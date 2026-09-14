"""M30-E immutable non-SEC source intake / 비SEC 불변 원문 intake.

The module accepts already-acquired UTF-8 source bytes, seals them into a
noncanonical immutable snapshot, and binds existing M27/M24/M25 source builders to
that snapshot's provenance. It deliberately performs no network fetch and no human
review or authority promotion.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.market_price import build_market_price_candidate, validate_market_price_candidate
from valuation_hub.terminal_growth_assumption import (
    build_terminal_growth_anchor_input,
    validate_terminal_growth_anchor_input,
)
from valuation_hub.wacc_assumption import build_wacc_source_input, validate_wacc_source_input

SCHEMA_VERSION = "external-source-snapshot-v0.1"
STATUS = "EXTERNAL_SOURCE_SNAPSHOT_CAPTURED"
ADAPTER = "local-utf8-external-source-v0.1"
SOURCE_TIERS = ("A", "B", "C", "D")
MAX_BODY_BYTES = 32 * 1024 * 1024


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    out = copy.deepcopy(value)
    out.pop(key, None)
    return out


def _text(value: Any, field: str, *, maximum: int = 500) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
        raise CaseServiceError(f"{field} required / {field} 필요")
    return value.strip()


def _timestamp(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise CaseServiceError(f"{field} timezone-aware timestamp required / {field} 시간대 포함 시각 필요")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CaseServiceError(f"{field} ISO timestamp invalid / {field} ISO 시각 오류") from exc
    if parsed.tzinfo is None:
        raise CaseServiceError(f"{field} timezone required / {field} 시간대 필요")
    return parsed.isoformat()


def _locator(value: Any) -> str:
    locator = _text(value, "source_locator", maximum=4000)
    parsed = urlparse(locator)
    if parsed.scheme != "https" or not parsed.hostname:
        raise CaseServiceError("external source locator must be absolute HTTPS / 외부 원문 locator는 절대 HTTPS URL이어야 함")
    try:
        port = parsed.port
    except ValueError as exc:
        raise CaseServiceError("external source locator port invalid / 외부 원문 locator port 오류") from exc
    if parsed.username or parsed.password or port not in (None, 443):
        raise CaseServiceError("external source locator authority unsafe / 외부 원문 locator authority 오류")
    return locator


def build_external_source_snapshot(
    raw_text: str,
    *,
    source_publisher: str,
    source_type: str,
    source_tier: str,
    source_locator: str,
    captured_at: str,
) -> dict[str, Any]:
    if not isinstance(raw_text, str) or not raw_text:
        raise CaseServiceError("external source raw_text required / 외부 원문 raw_text 필요")
    raw = raw_text.encode("utf-8", errors="strict")
    if not raw or len(raw) > MAX_BODY_BYTES:
        raise CaseServiceError("external source body size invalid / 외부 원문 크기 오류")
    if source_tier not in SOURCE_TIERS:
        raise CaseServiceError("external source tier invalid / 외부 원문 tier 오류")
    publisher = _text(source_publisher, "source_publisher", maximum=300)
    source_kind = _text(source_type, "source_type", maximum=160)
    locator = _locator(source_locator)
    captured = _timestamp(captured_at, "captured_at")
    snapshot: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "canonical": False,
        "adapter": ADAPTER,
        "source": {
            "publisher": publisher,
            "source_type": source_kind,
            "tier": source_tier,
            "locator": locator,
        },
        "capture": {
            "method": "LOCAL_UTF8_INTAKE",
            "captured_at": captured,
            "network_fetch_performed": False,
            "credentials_persisted": False,
        },
        "body": {"bytes": len(raw), "sha256": _sha(raw)},
        "raw_text": raw_text,
        "snapshot_sha256": "",
    }
    snapshot["snapshot_sha256"] = _sha(_canonical_bytes(_without(snapshot, "snapshot_sha256")))
    validate_external_source_snapshot(snapshot)
    return snapshot


def validate_external_source_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(snapshot, dict) or snapshot.get("schema_version") != SCHEMA_VERSION or snapshot.get("status") != STATUS:
        raise CaseServiceError("external source snapshot schema/status invalid / 외부 원문 snapshot 스키마·상태 오류")
    if snapshot.get("canonical") is not False or snapshot.get("adapter") != ADAPTER:
        raise CaseServiceError("external source snapshot authority/adapter invalid / 외부 원문 snapshot 권위·adapter 오류")
    if set(snapshot) != {"schema_version", "status", "canonical", "adapter", "source", "capture", "body", "raw_text", "snapshot_sha256"}:
        raise CaseServiceError("external source snapshot top-level contract invalid / 외부 원문 snapshot 최상위 계약 오류")
    source, capture, body = snapshot.get("source"), snapshot.get("capture"), snapshot.get("body")
    raw_text = snapshot.get("raw_text")
    if not isinstance(source, dict) or set(source) != {"publisher", "source_type", "tier", "locator"}:
        raise CaseServiceError("external source provenance contract invalid / 외부 원문 provenance 계약 오류")
    if not isinstance(capture, dict) or set(capture) != {"method", "captured_at", "network_fetch_performed", "credentials_persisted"}:
        raise CaseServiceError("external source capture contract invalid / 외부 원문 capture 계약 오류")
    if not isinstance(body, dict) or set(body) != {"bytes", "sha256"} or not isinstance(raw_text, str) or not raw_text:
        raise CaseServiceError("external source body contract invalid / 외부 원문 body 계약 오류")
    _text(source.get("publisher"), "source.publisher", maximum=300)
    _text(source.get("source_type"), "source.source_type", maximum=160)
    if source.get("tier") not in SOURCE_TIERS:
        raise CaseServiceError("external source snapshot tier invalid / 외부 원문 snapshot tier 오류")
    if source.get("locator") != _locator(source.get("locator")):
        raise CaseServiceError("external source locator normalization mismatch / 외부 원문 locator 정규화 불일치")
    if capture != {
        "method": "LOCAL_UTF8_INTAKE",
        "captured_at": _timestamp(capture.get("captured_at"), "capture.captured_at"),
        "network_fetch_performed": False,
        "credentials_persisted": False,
    }:
        raise CaseServiceError("external source capture safety boundary invalid / 외부 원문 capture 안전경계 오류")
    raw = raw_text.encode("utf-8", errors="strict")
    if len(raw) > MAX_BODY_BYTES or body.get("bytes") != len(raw) or body.get("sha256") != _sha(raw):
        raise CaseServiceError("external source raw body hash/size mismatch / 외부 원문 해시·크기 불일치")
    expected = _sha(_canonical_bytes(_without(snapshot, "snapshot_sha256")))
    if snapshot.get("snapshot_sha256") != expected:
        raise CaseServiceError("external source snapshot SHA-256 mismatch / 외부 원문 snapshot SHA-256 불일치")
    return {
        "status": "PASS_EXTERNAL_SOURCE_SNAPSHOT_VALIDATION",
        "canonical": False,
        "snapshot_sha256": expected,
        "body_sha256": body["sha256"],
        "source_tier": source["tier"],
        "captured_at": capture["captured_at"],
    }


def materialize_external_source_snapshot(snapshot: dict[str, Any], output: Path, root: Path | None = None) -> dict[str, Any]:
    repo = root.resolve() if root else find_repo_root()
    validate_external_source_snapshot(snapshot)
    target = output.resolve()
    allowed = (repo / "workspace" / "source_snapshots").resolve()
    try:
        target.relative_to(allowed)
    except ValueError as exc:
        raise CaseServiceError("external source snapshots may only be written under workspace/source_snapshots / 외부 원문 snapshot은 workspace/source_snapshots 아래에만 기록 가능") from exc
    if target.exists():
        raise CaseServiceError("external source snapshot output already exists / 외부 원문 snapshot 출력파일이 이미 존재함")
    target.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(target, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            target.unlink(missing_ok=True)
        finally:
            raise
    return {
        "status": "EXTERNAL_SOURCE_SNAPSHOT_MATERIALIZED",
        "canonical": False,
        "path": str(target),
        "snapshot_sha256": snapshot["snapshot_sha256"],
        "body_sha256": snapshot["body"]["sha256"],
        "file_sha256": _sha(data),
    }


def load_external_source_snapshot(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CaseServiceError(f"external source snapshot file not found / 외부 원문 snapshot 파일 없음: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise CaseServiceError(f"external source snapshot read failed / 외부 원문 snapshot 읽기 실패: {path}") from exc
    if not isinstance(value, dict):
        raise CaseServiceError("external source snapshot JSON object required / 외부 원문 snapshot JSON 객체 필요")
    return value


def _provenance(snapshot: dict[str, Any]) -> dict[str, str]:
    validate_external_source_snapshot(snapshot)
    source = snapshot["source"]
    return {
        "publisher": source["publisher"],
        "source_type": source["source_type"],
        "tier": source["tier"],
        "locator": source["locator"],
        "snapshot_sha256": snapshot["snapshot_sha256"],
    }


def _market_source(snapshot: dict[str, Any]) -> dict[str, str]:
    source = _provenance(snapshot)
    return {
        "publisher": source["publisher"],
        "source_type": source["source_type"],
        "tier": source["tier"],
        "locator": source["locator"],
        "snapshot_sha256": source["snapshot_sha256"],
    }


def _assumption_source(snapshot: dict[str, Any]) -> dict[str, str]:
    source = _provenance(snapshot)
    return {
        "publisher": source["publisher"],
        "type": source["source_type"],
        "tier": source["tier"],
        "locator": source["locator"],
        "source_sha256": source["snapshot_sha256"],
    }


def validate_market_price_candidate_against_snapshot(candidate: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    checked = validate_market_price_candidate(candidate)
    if candidate.get("source") != _market_source(snapshot):
        raise CaseServiceError("market-price candidate/snapshot provenance mismatch / 시장가격 candidate·snapshot provenance 불일치")
    return {**checked, "snapshot_sha256": snapshot["snapshot_sha256"]}


def validate_wacc_source_input_against_snapshot(value: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    checked = validate_wacc_source_input(value)
    if value.get("source") != _assumption_source(snapshot):
        raise CaseServiceError("WACC input/snapshot provenance mismatch / WACC 입력·snapshot provenance 불일치")
    return {**checked, "snapshot_sha256": snapshot["snapshot_sha256"]}


def validate_terminal_growth_anchor_against_snapshot(value: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    checked = validate_terminal_growth_anchor_input(value)
    if value.get("source") != _assumption_source(snapshot):
        raise CaseServiceError("terminal-growth anchor/snapshot provenance mismatch / 영구성장률 anchor·snapshot provenance 불일치")
    return {**checked, "snapshot_sha256": snapshot["snapshot_sha256"]}


def build_market_price_candidate_from_snapshot(snapshot: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    source = _provenance(snapshot)
    forbidden = {"source_publisher", "source_type", "source_tier", "source_locator", "source_snapshot_sha256"} & set(kwargs)
    if forbidden:
        raise CaseServiceError("source provenance must come only from snapshot / source provenance는 snapshot에서만 파생되어야 함")
    candidate = build_market_price_candidate(
        **kwargs,
        source_publisher=source["publisher"],
        source_type=source["source_type"],
        source_tier=source["tier"],
        source_locator=source["locator"],
        source_snapshot_sha256=source["snapshot_sha256"],
    )
    validate_market_price_candidate_against_snapshot(candidate, snapshot)
    return candidate


def build_wacc_source_input_from_snapshot(snapshot: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    source = _provenance(snapshot)
    forbidden = {"source_publisher", "source_type", "source_tier", "source_locator", "source_sha256"} & set(kwargs)
    if forbidden:
        raise CaseServiceError("WACC source provenance must come only from snapshot / WACC provenance는 snapshot에서만 파생되어야 함")
    value = build_wacc_source_input(
        **kwargs,
        source_publisher=source["publisher"],
        source_type=source["source_type"],
        source_tier=source["tier"],
        source_locator=source["locator"],
        source_sha256=source["snapshot_sha256"],
    )
    validate_wacc_source_input_against_snapshot(value, snapshot)
    return value


def build_terminal_growth_anchor_from_snapshot(snapshot: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    source = _provenance(snapshot)
    forbidden = {"source_publisher", "source_type", "source_tier", "source_locator", "source_sha256"} & set(kwargs)
    if forbidden:
        raise CaseServiceError("terminal-growth provenance must come only from snapshot / 영구성장률 provenance는 snapshot에서만 파생되어야 함")
    value = build_terminal_growth_anchor_input(
        **kwargs,
        source_publisher=source["publisher"],
        source_type=source["source_type"],
        source_tier=source["tier"],
        source_locator=source["locator"],
        source_sha256=source["snapshot_sha256"],
    )
    validate_terminal_growth_anchor_against_snapshot(value, snapshot)
    return value
