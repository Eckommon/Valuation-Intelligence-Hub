"""M30-R7X source-bound ingress for the R6 dilution upper envelope.

This module does not estimate diluted shares. It binds caller-supplied envelope
claims to validated immutable Tier-A source snapshots, verifies that the cited
source excerpts and observed quantities are present, and projects the exact
component shape already consumed by M30-R6.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import date
from html.parser import HTMLParser
from math import isfinite
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.disclosure_limited_dilution import (
    ROLE_ANCHOR,
    ROLE_BUFFER,
    ROLE_PERFORMANCE_UPLIFT,
    ROLE_SUBSEQUENT,
    ROLES,
    _normalize_components,
)
from valuation_hub.external_source import validate_external_source_snapshot

MANIFEST_SCHEMA = "source-bound-dilution-envelope-manifest-v0.1"
MANIFEST_STATUS = "SOURCE_BOUND_DILUTION_ENVELOPE_READY"
SOURCE_POLICY = {
    "required_tier": "A",
    "excerpt_match": "WHITESPACE_NORMALIZED_VISIBLE_OR_RAW_EXACT_SUBSTRING",
    "claim_binding": "OBSERVED_QUANTITY_X_UNIT_MULTIPLIER",
}
BUFFER_METHOD = "PRO_RATA_GROSS_GRANT_RUN_RATE_V01"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data:
            self.parts.append(data)


def _bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    out = copy.deepcopy(value)
    out.pop(key, None)
    return out


def _text(value: Any, field: str, maximum: int = 8000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
        raise CaseServiceError(f"{field} required/too long / {field} 필요·길이 오류")
    return value.strip()


def _iso(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise CaseServiceError(f"{field} date required / {field} 날짜 필요")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise CaseServiceError(f"{field} invalid / {field} 날짜 오류") from exc
    if parsed.isoformat() != value:
        raise CaseServiceError(f"{field} canonical YYYY-MM-DD required / {field} 정규날짜 필요")
    return value


def _number(value: Any, field: str, *, nonnegative: bool = True) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
        raise CaseServiceError(f"{field} finite numeric required / {field} 유한 숫자 필요")
    number = float(value)
    if nonnegative and number < 0:
        raise CaseServiceError(f"{field} nonnegative required / {field} 음수 불가")
    return number


def _integer(value: Any, field: str, *, positive: bool = False) -> int:
    number = _number(value, field)
    if not float(number).is_integer():
        raise CaseServiceError(f"{field} integer required / {field} 정수 필요")
    integer = int(number)
    if positive and integer <= 0:
        raise CaseServiceError(f"{field} positive integer required / {field} 양의 정수 필요")
    return integer


def _norm(value: str) -> str:
    return " ".join(value.split())


def _visible_text(value: str) -> str:
    parser = _VisibleTextParser()
    try:
        parser.feed(value)
        parser.close()
    except Exception:
        return _norm(value)
    return _norm(" ".join(parser.parts))


def _excerpt_matches(raw_text: str, excerpt: str) -> bool:
    target = _norm(excerpt)
    if not target:
        return False
    return target in _norm(raw_text) or target in _visible_text(raw_text)


def _quantity_token_present(excerpt: str, observed_quantity: int) -> bool:
    plain = str(observed_quantity)
    comma = f"{observed_quantity:,}"
    pattern = re.compile(rf"(?<!\d)(?:{re.escape(comma)}|{re.escape(plain)})(?!\d)")
    return bool(pattern.search(excerpt))


def _snapshot_map(source_snapshots: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if not isinstance(source_snapshots, list) or not source_snapshots:
        raise CaseServiceError("source snapshots required / source snapshot 필요")
    if len(source_snapshots) > 16:
        raise CaseServiceError("too many source snapshots / source snapshot 과다")
    result: dict[str, dict[str, Any]] = {}
    for snapshot in source_snapshots:
        checked = validate_external_source_snapshot(snapshot)
        sha = checked["snapshot_sha256"]
        if sha in result:
            raise CaseServiceError("duplicate source snapshot SHA / source snapshot SHA 중복")
        if snapshot["source"]["tier"] != "A":
            raise CaseServiceError("R7X real envelope requires Tier-A source / R7X 실 envelope는 Tier-A 출처 필요")
        result[sha] = snapshot
    return result


def _binding(
    raw: Any,
    snapshots: dict[str, dict[str, Any]],
    *,
    field: str,
) -> tuple[dict[str, Any], int]:
    if not isinstance(raw, dict):
        raise CaseServiceError(f"{field} object required / {field} 객체 필요")
    if set(raw) != {"snapshot_sha256", "evidence_excerpt", "observed_quantity", "unit_multiplier"}:
        raise CaseServiceError(f"{field} contract invalid / {field} 계약 오류")
    sha = raw.get("snapshot_sha256")
    if not isinstance(sha, str) or not SHA256_RE.fullmatch(sha) or sha not in snapshots:
        raise CaseServiceError(f"{field} snapshot lineage missing / {field} snapshot 계보 누락")
    excerpt = _text(raw.get("evidence_excerpt"), f"{field}.evidence_excerpt", 6000)
    observed = _integer(raw.get("observed_quantity"), f"{field}.observed_quantity")
    multiplier = _integer(raw.get("unit_multiplier"), f"{field}.unit_multiplier", positive=True)
    snapshot = snapshots[sha]
    if not _excerpt_matches(snapshot["raw_text"], excerpt):
        raise CaseServiceError(f"{field} excerpt not found in source snapshot / {field} excerpt 원문 불일치")
    if not _quantity_token_present(excerpt, observed):
        raise CaseServiceError(f"{field} observed quantity absent from excerpt / {field} 관측수량 excerpt 누락")
    normalized = {
        "snapshot_sha256": sha,
        "evidence_excerpt": excerpt,
        "observed_quantity": observed,
        "unit_multiplier": multiplier,
    }
    return normalized, observed * multiplier


def _normalize_spec(
    raw: Any,
    snapshots: dict[str, dict[str, Any]],
    *,
    index: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(raw, dict):
        raise CaseServiceError("envelope component spec object required / envelope 구성 spec 객체 필요")
    allowed = {
        "component_id",
        "role",
        "shares",
        "as_of",
        "evidence_basis",
        "source_bindings",
        "calculation",
    }
    if set(raw) - allowed:
        raise CaseServiceError("envelope component spec unknown field / envelope 구성 spec 알 수 없는 필드")
    component_id = _text(raw.get("component_id"), "component_id", 120)
    role = raw.get("role")
    if role not in ROLES:
        raise CaseServiceError("unsupported upper-envelope role / 미지원 upper-envelope 역할")
    shares = _number(raw.get("shares"), "component.shares")
    as_of = _iso(raw.get("as_of"), "component.as_of")
    evidence_basis = _text(raw.get("evidence_basis"), "component.evidence_basis")
    bindings_raw = raw.get("source_bindings")
    if not isinstance(bindings_raw, list) or not bindings_raw:
        raise CaseServiceError("component source_bindings required / 구성요소 source_bindings 필요")
    normalized_bindings: list[dict[str, Any]] = []
    claim_values: list[int] = []
    for binding_index, binding_raw in enumerate(bindings_raw):
        normalized_binding, claim_value = _binding(
            binding_raw,
            snapshots,
            field=f"component_specs[{index}].source_bindings[{binding_index}]",
        )
        normalized_bindings.append(normalized_binding)
        claim_values.append(claim_value)

    calculation = raw.get("calculation")
    if role in {ROLE_ANCHOR, ROLE_SUBSEQUENT}:
        if calculation not in (None, {}):
            raise CaseServiceError("direct envelope claim cannot carry calculation / 직접 envelope 주장 계산정보 불가")
        if len(claim_values) != 1 or abs(shares - claim_values[0]) > 1e-9:
            raise CaseServiceError("direct envelope claim must equal one source-bound quantity / 직접 envelope 주장은 단일 출처수량과 일치 필요")
        normalized_calculation = None
    elif role == ROLE_PERFORMANCE_UPLIFT:
        if calculation not in (None, {}):
            raise CaseServiceError("performance uplift cannot carry calculation / 성과 uplift 계산정보 불가")
        if len(claim_values) < 1 or abs(shares - sum(claim_values)) > 1e-9:
            raise CaseServiceError("performance uplift must equal source-bound claim sum / 성과 uplift는 출처수량 합계와 일치 필요")
        normalized_calculation = None
    elif role == ROLE_BUFFER:
        if not isinstance(calculation, dict) or set(calculation) != {
            "method",
            "observed_gross_grants",
            "observed_days",
            "lag_days",
        }:
            raise CaseServiceError("buffer calculation contract invalid / buffer 계산 계약 오류")
        if calculation.get("method") != BUFFER_METHOD:
            raise CaseServiceError("buffer calculation method invalid / buffer 계산방식 오류")
        observed_gross = _number(calculation.get("observed_gross_grants"), "buffer.observed_gross_grants")
        observed_days = _integer(calculation.get("observed_days"), "buffer.observed_days", positive=True)
        lag_days = _integer(calculation.get("lag_days"), "buffer.lag_days")
        if abs(observed_gross - sum(claim_values)) > 1e-9:
            raise CaseServiceError("buffer observed gross grants must equal bound source claims / buffer 관측총부여량은 출처수량 합계와 일치 필요")
        expected = observed_gross * lag_days / observed_days
        if abs(shares - expected) > max(1e-6, abs(expected) * 1e-9):
            raise CaseServiceError("buffer shares do not reproduce pro-rata calculation / buffer 주식수 비례계산 불일치")
        normalized_calculation = {
            "method": BUFFER_METHOD,
            "observed_gross_grants": observed_gross,
            "observed_days": observed_days,
            "lag_days": lag_days,
        }
    else:
        raise CaseServiceError("unsupported envelope role / 미지원 envelope 역할")

    unique_sources: dict[str, dict[str, str]] = {}
    for binding in normalized_bindings:
        snapshot = snapshots[binding["snapshot_sha256"]]
        sha = snapshot["snapshot_sha256"]
        unique_sources[sha] = {
            "locator": snapshot["source"]["locator"],
            "snapshot_sha256": sha,
            "source_type": snapshot["source"]["source_type"],
        }

    spec = {
        "component_id": component_id,
        "role": role,
        "shares": shares,
        "as_of": as_of,
        "evidence_basis": evidence_basis,
        "source_bindings": normalized_bindings,
        "calculation": normalized_calculation,
    }
    projected = {
        "component_id": component_id,
        "role": role,
        "shares": shares,
        "as_of": as_of,
        "sources": [unique_sources[key] for key in sorted(unique_sources)],
        "evidence_basis": evidence_basis,
        "calculation": normalized_calculation,
    }
    return spec, projected


def _assemble_manifest(
    component_specs: list[dict[str, Any]],
    source_snapshots: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(component_specs, list) or not component_specs:
        raise CaseServiceError("component_specs array required / component_specs 배열 필요")
    if len(component_specs) > 32:
        raise CaseServiceError("too many envelope components / envelope 구성요소 과다")
    snapshots = _snapshot_map(source_snapshots)
    normalized_specs: list[dict[str, Any]] = []
    projected: list[dict[str, Any]] = []
    ids: set[str] = set()
    referenced: set[str] = set()
    for index, raw in enumerate(component_specs):
        spec, component = _normalize_spec(raw, snapshots, index=index)
        if spec["component_id"] in ids:
            raise CaseServiceError("duplicate envelope component id / envelope 구성요소 id 중복")
        ids.add(spec["component_id"])
        normalized_specs.append(spec)
        projected.append(component)
        referenced.update(binding["snapshot_sha256"] for binding in spec["source_bindings"])

    normalized_components = _normalize_components(projected)
    used_snapshots = [copy.deepcopy(snapshots[key]) for key in sorted(referenced)]
    manifest: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA,
        "status": MANIFEST_STATUS,
        "canonical": False,
        "source_policy": copy.deepcopy(SOURCE_POLICY),
        "component_specs": normalized_specs,
        "components": normalized_components,
        "source_snapshots": used_snapshots,
        "manifest_sha256": "",
    }
    manifest["manifest_sha256"] = _sha(_without(manifest, "manifest_sha256"))
    return manifest


def build_source_bound_dilution_envelope_manifest(
    component_specs: list[dict[str, Any]],
    source_snapshots: list[dict[str, Any]],
) -> dict[str, Any]:
    manifest = _assemble_manifest(component_specs, source_snapshots)
    validate_source_bound_dilution_envelope_manifest(manifest)
    return manifest


def validate_source_bound_dilution_envelope_manifest(
    manifest: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        raise CaseServiceError("source-bound envelope manifest object required / source-bound envelope manifest 객체 필요")
    expected_keys = {
        "schema_version",
        "status",
        "canonical",
        "source_policy",
        "component_specs",
        "components",
        "source_snapshots",
        "manifest_sha256",
    }
    if set(manifest) != expected_keys:
        raise CaseServiceError("source-bound envelope manifest top-level contract invalid / source-bound envelope manifest 최상위 계약 오류")
    if (
        manifest.get("schema_version") != MANIFEST_SCHEMA
        or manifest.get("status") != MANIFEST_STATUS
        or manifest.get("canonical") is not False
        or manifest.get("source_policy") != SOURCE_POLICY
    ):
        raise CaseServiceError("source-bound envelope manifest schema/policy invalid / source-bound envelope manifest 스키마·정책 오류")
    rebuilt = _assemble_manifest(
        manifest.get("component_specs"),
        manifest.get("source_snapshots"),
    )
    if manifest.get("component_specs") != rebuilt["component_specs"]:
        raise CaseServiceError("source-bound envelope component spec projection mismatch / source-bound envelope 구성 spec 투영 불일치")
    if manifest.get("components") != rebuilt["components"]:
        raise CaseServiceError("source-bound envelope component projection mismatch / source-bound envelope 구성 투영 불일치")
    if manifest.get("source_snapshots") != rebuilt["source_snapshots"]:
        raise CaseServiceError("source-bound envelope snapshot projection mismatch / source-bound envelope snapshot 투영 불일치")
    expected_sha = _sha(_without(manifest, "manifest_sha256"))
    if manifest.get("manifest_sha256") != expected_sha or expected_sha != rebuilt["manifest_sha256"]:
        raise CaseServiceError("source-bound envelope manifest SHA mismatch / source-bound envelope manifest SHA 불일치")
    return {
        "status": "PASS_SOURCE_BOUND_DILUTION_ENVELOPE_VALIDATION",
        "manifest_sha256": expected_sha,
        "component_count": len(manifest["components"]),
        "source_snapshot_count": len(manifest["source_snapshots"]),
        "components": copy.deepcopy(manifest["components"]),
    }
