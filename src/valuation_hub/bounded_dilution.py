"""M30-R6 category-level bounded dilution envelope.

This module is deliberately narrower than the disclosure-limited point-assumption
path. It preserves each M22 dilution category as EXACT, BOUNDED, or
UNBOUNDED_DEPENDENCY and evaluates only an analytical interval. The interval is
noncanonical and can never impersonate an exact equity.diluted_shares fact.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from math import isfinite
from typing import Any

from valuation_hub.ai_dilution_authority import (
    ABSENT_SUPPORTED,
    BLOCKED_DEPENDENCY,
    HOLD,
    PRESENT,
    UNKNOWN_CONFLICT,
    validate_ai_dilution_inventory,
)
from valuation_hub.case_service import CaseServiceError
from valuation_hub.valuation_shares import (
    ADJUSTMENT_CATEGORIES,
    FRESH,
    validate_valuation_share_base_context,
)

SCHEMA = "bounded-dilution-envelope-v0.1"
STATUS = "BOUNDED_DILUTION_ENVELOPE_EVALUATED"
POLICY_ID = "BOUNDED_DILUTION_PUBLIC_DATA_V01"

RANGE_READY = "RANGE_READY_FOR_VALUATION_SCENARIOS"
HOLD_MATERIAL = "HOLD_MATERIAL_DILUTION_UNCERTAINTY"
HOLD_UNBOUNDED = "HOLD_UNBOUNDED_DILUTION_DEPENDENCY"

EXACT = "EXACT"
BOUNDED = "BOUNDED"
UNBOUNDED_DEPENDENCY = "UNBOUNDED_DEPENDENCY"
RANGE_STATES = {EXACT, BOUNDED, UNBOUNDED_DEPENDENCY}

EXACT_REPRODUCED = "EXACT_REPRODUCED"
EVIDENCE_IMPLIED = "EVIDENCE_IMPLIED"
ASSUMPTION_CONDITIONAL = "ASSUMPTION_CONDITIONAL"
UNBOUNDED_DISCLOSURE = "UNBOUNDED_DISCLOSURE"
BOUND_KINDS = {
    EXACT_REPRODUCED,
    EVIDENCE_IMPLIED,
    ASSUMPTION_CONDITIONAL,
    UNBOUNDED_DISCLOSURE,
}

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


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


def _num(value: Any, field: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
        raise CaseServiceError(f"{field} finite numeric required / {field} 유한 숫자 필요")
    number = float(value)
    if positive and number <= 0:
        raise CaseServiceError(f"{field} must be > 0 / {field} 0 초과 필요")
    if not positive and number < 0:
        raise CaseServiceError(f"{field} must be nonnegative / {field} 음수 불가")
    return number


def _text(value: Any, field: str, maximum: int = 8000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
        raise CaseServiceError(f"{field} required/too long / {field} 필요·길이 오류")
    return value.strip()


def _str_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise CaseServiceError(f"{field} string array required / {field} 문자열 배열 필요")
    return [item.strip() for item in value]


def _source_rows(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise CaseServiceError("bounded dilution row requires source evidence / bounded dilution row 출처근거 필요")
    rows: list[dict[str, str]] = []
    for raw in value:
        if not isinstance(raw, dict):
            raise CaseServiceError("bounded dilution source object required / bounded dilution 출처 객체 필요")
        snapshot_sha = raw.get("snapshot_sha256")
        if not isinstance(snapshot_sha, str) or not SHA256_RE.fullmatch(snapshot_sha):
            raise CaseServiceError("bounded dilution source SHA invalid / bounded dilution 출처 SHA 오류")
        rows.append(
            {
                "locator": _text(raw.get("locator"), "source.locator", 2000),
                "snapshot_sha256": snapshot_sha,
                "source_type": _text(raw.get("source_type"), "source.source_type", 160),
            }
        )
    return rows


def _normalize_range_row(raw: dict[str, Any], inventory_row: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise CaseServiceError("bounded dilution category object required / bounded dilution category 객체 필요")

    category = raw.get("category")
    state = raw.get("state")
    bound_kind = raw.get("bound_kind")
    if category != inventory_row.get("category") or category not in ADJUSTMENT_CATEGORIES:
        raise CaseServiceError("bounded dilution category/inventory mismatch / bounded dilution category·inventory 불일치")
    if state not in RANGE_STATES or bound_kind not in BOUND_KINDS:
        raise CaseServiceError("bounded dilution state/bound kind invalid / bounded dilution 상태·bound kind 오류")

    sources = _source_rows(raw.get("sources"))
    evidence_basis = _text(raw.get("evidence_basis"), "evidence_basis")
    assumptions = _str_list(raw.get("assumptions"), "assumptions")
    inv_state = inventory_row.get("state")

    if inv_state == UNKNOWN_CONFLICT:
        raise CaseServiceError("bounded dilution cannot override UNKNOWN_CONFLICT / bounded dilution은 UNKNOWN_CONFLICT 우회 불가")

    if inv_state == PRESENT:
        if state != EXACT or bound_kind != EXACT_REPRODUCED:
            raise CaseServiceError("R4 PRESENT category must remain EXACT / R4 PRESENT category는 EXACT 유지 필요")
        expected = _num(inventory_row.get("adjustment_shares"), f"{category}.adjustment_shares")
        lower = _num(raw.get("lower_shares"), f"{category}.lower_shares")
        upper = _num(raw.get("upper_shares"), f"{category}.upper_shares")
        if abs(lower - expected) > max(1e-6, abs(expected) * 1e-9) or abs(upper - expected) > max(1e-6, abs(expected) * 1e-9):
            raise CaseServiceError("EXACT range must reproduce R4 PRESENT adjustment / EXACT 범위는 R4 PRESENT 조정 재현 필요")
        if assumptions:
            raise CaseServiceError("EXACT reproduced category cannot add assumptions / EXACT 재현 category 가정 추가 불가")
    elif inv_state == ABSENT_SUPPORTED:
        if state != EXACT or bound_kind != EXACT_REPRODUCED:
            raise CaseServiceError("R4 ABSENT_SUPPORTED category must remain exact zero / R4 ABSENT_SUPPORTED category는 정확한 0 유지 필요")
        lower = _num(raw.get("lower_shares"), f"{category}.lower_shares")
        upper = _num(raw.get("upper_shares"), f"{category}.upper_shares")
        if lower != 0 or upper != 0:
            raise CaseServiceError("ABSENT_SUPPORTED range must be zero / ABSENT_SUPPORTED 범위는 0 필요")
        if assumptions:
            raise CaseServiceError("ABSENT_SUPPORTED exact zero cannot add assumptions / ABSENT_SUPPORTED 정확 0 가정 추가 불가")
    elif inv_state == BLOCKED_DEPENDENCY:
        if state == EXACT:
            raise CaseServiceError("R4 blocked category cannot become exact inside R6; rebuild R4 instead / R4 blocker를 R6에서 exact로 승격 불가")
        lower = _num(raw.get("lower_shares"), f"{category}.lower_shares")
        if state == BOUNDED:
            upper = _num(raw.get("upper_shares"), f"{category}.upper_shares")
            if upper < lower:
                raise CaseServiceError("bounded dilution upper below lower / bounded dilution 상단이 하단보다 작음")
            if bound_kind not in {EVIDENCE_IMPLIED, ASSUMPTION_CONDITIONAL}:
                raise CaseServiceError("BOUNDED category requires evidence-implied or assumption-conditional kind / BOUNDED category bound kind 오류")
            if bound_kind == EVIDENCE_IMPLIED and assumptions:
                raise CaseServiceError("evidence-implied bound cannot carry assumptions / evidence-implied bound 가정 불가")
            if bound_kind == ASSUMPTION_CONDITIONAL and not assumptions:
                raise CaseServiceError("assumption-conditional bound requires explicit assumptions / 조건부 bound는 명시적 가정 필요")
        else:
            upper = None
            if bound_kind != UNBOUNDED_DISCLOSURE:
                raise CaseServiceError("UNBOUNDED_DEPENDENCY requires unbounded-disclosure kind / UNBOUNDED_DEPENDENCY bound kind 오류")
    else:
        raise CaseServiceError("unsupported R4 state for bounded dilution / bounded dilution 미지원 R4 상태")

    row = {
        "category": category,
        "r4_state": inv_state,
        "state": state,
        "bound_kind": bound_kind,
        "lower_shares": lower,
        "upper_shares": upper,
        "sources": sources,
        "evidence_basis": evidence_basis,
        "assumptions": assumptions,
        "range_sha256": "",
    }
    row["range_sha256"] = _sha(_without(row, "range_sha256"))
    return row


def _normalize_ranges(
    category_ranges: list[dict[str, Any]],
    hold_inventory: dict[str, Any],
) -> list[dict[str, Any]]:
    if not isinstance(category_ranges, list) or len(category_ranges) != len(ADJUSTMENT_CATEGORIES):
        raise CaseServiceError("bounded dilution requires exactly six category ranges / bounded dilution은 정확히 6개 category 범위 필요")
    by_category: dict[str, dict[str, Any]] = {}
    for raw in category_ranges:
        if not isinstance(raw, dict) or raw.get("category") not in ADJUSTMENT_CATEGORIES:
            raise CaseServiceError("bounded dilution category invalid / bounded dilution category 오류")
        category = raw["category"]
        if category in by_category:
            raise CaseServiceError("duplicate bounded dilution category / bounded dilution category 중복")
        by_category[category] = raw
    if set(by_category) != set(ADJUSTMENT_CATEGORIES):
        raise CaseServiceError("bounded dilution category coverage incomplete / bounded dilution category 범위 누락")

    inventory_by_category = {row["category"]: row for row in hold_inventory["categories"]}
    return [
        _normalize_range_row(by_category[category], inventory_by_category[category])
        for category in ADJUSTMENT_CATEGORIES
    ]


def _validate_upstream(
    base_context: dict[str, Any],
    hold_inventory: dict[str, Any],
) -> dict[str, Any]:
    base_checked = validate_valuation_share_base_context(base_context)
    if base_checked.get("freshness") != FRESH:
        raise CaseServiceError("bounded dilution requires fresh current-share base / bounded dilution은 최신 현재주식수 base 필요")
    inventory_checked = validate_ai_dilution_inventory(hold_inventory, base_context)
    if inventory_checked.get("decision") != HOLD or hold_inventory.get("decision") != HOLD:
        raise CaseServiceError("exact R4 path outranks bounded dilution; R6 requires HOLD / exact R4 경로가 우선하며 R6는 HOLD 필요")
    if any(row.get("state") == UNKNOWN_CONFLICT for row in hold_inventory.get("categories", [])):
        raise CaseServiceError("bounded dilution cannot override UNKNOWN_CONFLICT / bounded dilution은 UNKNOWN_CONFLICT 우회 불가")
    if not any(row.get("state") == BLOCKED_DEPENDENCY for row in hold_inventory.get("categories", [])):
        raise CaseServiceError("bounded dilution requires at least one disclosure blocker / bounded dilution은 공시 blocker 필요")
    return inventory_checked


def _project(
    base_context: dict[str, Any],
    rows: list[dict[str, Any]],
    *,
    materiality_threshold: float,
) -> dict[str, Any]:
    threshold = _num(materiality_threshold, "materiality_threshold", positive=True)
    if threshold > 0.25:
        raise CaseServiceError("materiality threshold above 25% not permitted / materiality threshold 25% 초과 불가")

    base_shares = _num(base_context.get("value"), "base current shares", positive=True)
    lower_adjustment = sum(row["lower_shares"] for row in rows)
    lower = base_shares + lower_adjustment
    unbounded = [row["category"] for row in rows if row["state"] == UNBOUNDED_DEPENDENCY]

    if unbounded:
        return {
            "decision": HOLD_UNBOUNDED,
            "base_current_shares": base_shares,
            "lower_adjustment_shares": lower_adjustment,
            "upper_adjustment_shares": None,
            "lower_fully_diluted_shares": lower,
            "upper_fully_diluted_shares": None,
            "range_width_shares": None,
            "relative_share_uncertainty": None,
            "max_per_share_value_reduction": None,
            "lower_to_upper_per_share_value_multiplier": None,
            "materiality_threshold": threshold,
            "unbounded_categories": unbounded,
        }

    upper_adjustment = sum(_num(row["upper_shares"], f'{row["category"]}.upper_shares') for row in rows)
    upper = base_shares + upper_adjustment
    if upper < lower:
        raise CaseServiceError("aggregate bounded dilution upper below lower / 총 bounded dilution 상단이 하단보다 작음")
    width = upper - lower
    relative = upper / lower - 1.0
    per_share_reduction = 1.0 - lower / upper
    decision = RANGE_READY if relative <= threshold else HOLD_MATERIAL
    return {
        "decision": decision,
        "base_current_shares": base_shares,
        "lower_adjustment_shares": lower_adjustment,
        "upper_adjustment_shares": upper_adjustment,
        "lower_fully_diluted_shares": lower,
        "upper_fully_diluted_shares": upper,
        "range_width_shares": width,
        "relative_share_uncertainty": relative,
        "max_per_share_value_reduction": per_share_reduction,
        "lower_to_upper_per_share_value_multiplier": lower / upper,
        "materiality_threshold": threshold,
        "unbounded_categories": [],
    }


def build_bounded_dilution_envelope(
    base_context: dict[str, Any],
    hold_inventory: dict[str, Any],
    category_ranges: list[dict[str, Any]],
    *,
    materiality_threshold: float = 0.05,
) -> dict[str, Any]:
    _validate_upstream(base_context, hold_inventory)
    rows = _normalize_ranges(category_ranges, hold_inventory)
    projection = _project(base_context, rows, materiality_threshold=materiality_threshold)

    envelope = {
        "schema_version": SCHEMA,
        "status": STATUS,
        "canonical": False,
        "class": "ANALYTICAL_RANGE",
        "metric": "fully_diluted_shares_interval",
        "unit": "shares",
        "policy_id": POLICY_ID,
        "as_of": base_context["policy"]["as_of"],
        "entity": copy.deepcopy(base_context["entity"]),
        "base_context_sha256": base_context["context_sha256"],
        "r4_inventory_sha256": hold_inventory["inventory_sha256"],
        "category_ranges": rows,
        "decision": projection["decision"],
        "envelope": {key: value for key, value in projection.items() if key != "decision"},
        "semantic_boundary": {
            "interval_not_exact_fact": True,
            "interval_not_derived_fact": True,
            "direct_bind_as_equity_diluted_shares": False,
            "exact_r4_path_outranks_interval": True,
            "blocked_category_exact_resolution_requires_r4_rebuild": True,
            "conditional_bounds_preserve_assumptions": True,
            "per_share_impact_is_denominator_sensitivity_only": True,
        },
        "envelope_sha256": "",
    }
    envelope["envelope_sha256"] = _sha(_without(envelope, "envelope_sha256"))
    validate_bounded_dilution_envelope(envelope, base_context, hold_inventory, category_ranges)
    return envelope


def validate_bounded_dilution_envelope(
    envelope: dict[str, Any],
    base_context: dict[str, Any],
    hold_inventory: dict[str, Any],
    category_ranges: list[dict[str, Any]],
) -> dict[str, Any]:
    _validate_upstream(base_context, hold_inventory)
    if (
        not isinstance(envelope, dict)
        or envelope.get("schema_version") != SCHEMA
        or envelope.get("status") != STATUS
        or envelope.get("canonical") is not False
        or envelope.get("class") != "ANALYTICAL_RANGE"
        or envelope.get("metric") != "fully_diluted_shares_interval"
        or envelope.get("unit") != "shares"
        or envelope.get("policy_id") != POLICY_ID
    ):
        raise CaseServiceError("bounded dilution envelope schema/status invalid / bounded dilution envelope 스키마·상태 오류")
    if (
        envelope.get("as_of") != base_context.get("policy", {}).get("as_of")
        or envelope.get("entity") != base_context.get("entity")
        or envelope.get("base_context_sha256") != base_context.get("context_sha256")
        or envelope.get("r4_inventory_sha256") != hold_inventory.get("inventory_sha256")
    ):
        raise CaseServiceError("bounded dilution envelope lineage mismatch / bounded dilution envelope 계보 불일치")

    rows = _normalize_ranges(category_ranges, hold_inventory)
    if envelope.get("category_ranges") != rows:
        raise CaseServiceError("bounded dilution category projection mismatch / bounded dilution category 투영 불일치")

    raw_projection = envelope.get("envelope")
    if not isinstance(raw_projection, dict):
        raise CaseServiceError("bounded dilution projection missing / bounded dilution 투영 누락")
    threshold = _num(raw_projection.get("materiality_threshold"), "materiality_threshold", positive=True)
    expected = _project(base_context, rows, materiality_threshold=threshold)
    expected_decision = expected.pop("decision")
    if envelope.get("decision") != expected_decision or raw_projection != expected:
        raise CaseServiceError("bounded dilution independent projection mismatch / bounded dilution 독립 투영 불일치")

    expected_boundary = {
        "interval_not_exact_fact": True,
        "interval_not_derived_fact": True,
        "direct_bind_as_equity_diluted_shares": False,
        "exact_r4_path_outranks_interval": True,
        "blocked_category_exact_resolution_requires_r4_rebuild": True,
        "conditional_bounds_preserve_assumptions": True,
        "per_share_impact_is_denominator_sensitivity_only": True,
    }
    if envelope.get("semantic_boundary") != expected_boundary:
        raise CaseServiceError("bounded dilution semantic boundary invalid / bounded dilution 의미경계 오류")

    expected_sha = _sha(_without(envelope, "envelope_sha256"))
    if envelope.get("envelope_sha256") != expected_sha:
        raise CaseServiceError("bounded dilution envelope SHA mismatch / bounded dilution envelope SHA 불일치")
    return {
        "status": "PASS_BOUNDED_DILUTION_ENVELOPE_VALIDATION",
        "envelope_sha256": expected_sha,
        "decision": expected_decision,
        "relative_share_uncertainty": expected["relative_share_uncertainty"],
        "max_per_share_value_reduction": expected["max_per_share_value_reduction"],
    }
