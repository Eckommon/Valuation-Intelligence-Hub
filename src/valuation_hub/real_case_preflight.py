"""M30 real public-equity source-contract preflight / M30 실기업 source-contract 사전검증.

This module does not acquire credentials, approve evidence, mutate Drafts, or write
canonical case state. It validates a captured M13 SEC CompanyFacts snapshot against
one proposed real-case identity and probes source availability through existing
M13/M28 extractors. Unsupported prerequisites become explicit HOLD blockers.
"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from valuation_hub.case_service import CaseServiceError, find_repo_root, load_registry
from valuation_hub.debt_components import CORE_COMPONENTS, SEC_COMPONENT_SUPPORT
from valuation_hub.minority_interest import (
    extract_sec_minority_interest_candidate,
    validate_minority_interest_candidate,
)
from valuation_hub.sec_live import (
    extract_sec_evidence_candidate,
    normalize_cik,
    validate_source_snapshot,
)

SCHEMA_VERSION = "real-equity-source-preflight-v0.1"
PASS_STATUS = "PASS_REAL_EQUITY_SOURCE_PREFLIGHT"
HOLD_STATUS = "HOLD_REAL_CASE_PREREQUISITE"


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _date(value: Any, label: str) -> date:
    if not isinstance(value, str):
        raise CaseServiceError(f"{label} date required / {label} 날짜 필요")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise CaseServiceError(f"{label} date invalid / {label} 날짜 오류") from exc


def _text(value: Any, label: str, limit: int = 240) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise CaseServiceError(f"{label} required/too long / {label} 필요·길이 오류")
    return value.strip()


def _block(code: str, detail: str) -> dict[str, str]:
    return {"code": code, "detail": detail}


def _safe_extract(
    blockers: list[dict[str, str]],
    code: str,
    fn,
) -> dict[str, Any] | None:
    try:
        value = fn()
    except (CaseServiceError, KeyError, TypeError, ValueError) as exc:
        blockers.append(_block(code, str(exc)))
        return None
    if not isinstance(value, dict):
        blockers.append(_block(code, "extractor returned non-object / extractor가 객체를 반환하지 않음"))
        return None
    return value


def _registry_collision(case_id: str, repo: Path) -> dict[str, Any] | None:
    registry = load_registry(repo)
    for item in registry["cases"]:
        if isinstance(item, dict) and item.get("case_id") == case_id:
            return copy.deepcopy(item)
    return None


def build_real_equity_source_preflight(
    *,
    case_id: str,
    legal_name: str,
    ticker: str,
    exchange: str,
    cik: str | int,
    financial_period_end: str,
    valuation_as_of: str,
    sec_snapshot: dict[str, Any] | None,
    root: Path | None = None,
    form: str = "10-Q",
    shares_period_end: str | None = None,
) -> dict[str, Any]:
    """Probe one real U.S. equity target without promoting any authority.

    PASS means only that the currently implemented source prerequisites tested here
    are available. It does not mean the case is reviewed, bound, or canonical.
    """
    repo = root.resolve() if root else find_repo_root()
    case = _text(case_id, "case_id", 160)
    name = _text(legal_name, "legal_name", 240)
    symbol = _text(ticker, "ticker", 32).upper()
    venue = _text(exchange, "exchange", 80).upper()
    normalized_cik = normalize_cik(cik)
    period_end = _date(financial_period_end, "financial_period_end").isoformat()
    as_of = _date(valuation_as_of, "valuation_as_of").isoformat()
    if period_end > as_of:
        raise CaseServiceError("financial period end cannot be after valuation as_of / 재무기간말은 valuation as_of 이후일 수 없음")
    requested_form = _text(form, "form", 20).upper()
    share_end = _date(shares_period_end, "shares_period_end").isoformat() if shares_period_end else None
    if share_end is not None and share_end > as_of:
        raise CaseServiceError("shares period end cannot be after valuation as_of / 주식수 기준일은 valuation as_of 이후일 수 없음")

    blockers: list[dict[str, str]] = []
    collision = _registry_collision(case, repo)
    if collision is not None:
        blockers.append(_block("REGISTRY_CASE_ID_COLLISION", f"case_id already canonical / case_id가 이미 정식 등록됨: {case}"))

    checks: dict[str, Any] = {
        "registry_non_collision": collision is None,
        "sec_snapshot": None,
        "cash_candidate": None,
        "shares_candidate": None,
        "minority_interest_candidate": None,
        "us_sec_debt_profile": None,
    }

    if sec_snapshot is None:
        blockers.append(_block(
            "SEC_SOURCE_SNAPSHOT_REQUIRED",
            "captured M13 CompanyFacts snapshot required; runtime identifying User-Agent must be supplied outside repository / M13 CompanyFacts snapshot 필요; 식별 User-Agent는 저장소 밖 runtime에서 제공",
        ))
    else:
        validation = _safe_extract(
            blockers,
            "SEC_SNAPSHOT_INVALID",
            lambda: validate_source_snapshot(sec_snapshot),
        )
        if validation is not None:
            checks["sec_snapshot"] = validation
            if validation.get("cik") != normalized_cik:
                blockers.append(_block("SEC_CIK_MISMATCH", f"expected {normalized_cik}, got {validation.get('cik')}"))
            else:
                try:
                    payload = json.loads(sec_snapshot["raw_text"])
                except (KeyError, json.JSONDecodeError, TypeError) as exc:
                    blockers.append(_block("SEC_PAYLOAD_INVALID", str(exc)))
                    payload = None
                if isinstance(payload, dict):
                    source_name = str(payload.get("entityName") or "").strip()
                    checks["sec_snapshot"]["entity_name"] = source_name
                    if not source_name or source_name.casefold() != name.casefold():
                        blockers.append(_block("SEC_LEGAL_NAME_MISMATCH", f"expected {name!r}, got {source_name!r}"))

                cash = _safe_extract(
                    blockers,
                    "SEC_CASH_UNAVAILABLE",
                    lambda: extract_sec_evidence_candidate(sec_snapshot, "cash", form=requested_form, period_end=period_end),
                )
                if cash is not None:
                    checks["cash_candidate"] = {
                        "metric": cash.get("metric"),
                        "value": cash.get("value"),
                        "unit": cash.get("unit"),
                        "period": copy.deepcopy(cash.get("period")),
                        "filing": copy.deepcopy(cash.get("filing")),
                        "taxonomy": cash.get("taxonomy"),
                        "concept": cash.get("concept"),
                        "source_snapshot_sha256": cash.get("source", {}).get("snapshot_sha256"),
                    }

                shares = _safe_extract(
                    blockers,
                    "SEC_SHARES_OUTSTANDING_UNAVAILABLE",
                    lambda: extract_sec_evidence_candidate(sec_snapshot, "shares_outstanding", form=requested_form, period_end=share_end),
                )
                if shares is not None:
                    selected_end = shares.get("period", {}).get("end")
                    if not isinstance(selected_end, str) or selected_end > as_of:
                        blockers.append(_block("SEC_SHARES_AFTER_AS_OF", f"shares end {selected_end!r} exceeds valuation as_of {as_of}"))
                    checks["shares_candidate"] = {
                        "metric": shares.get("metric"),
                        "value": shares.get("value"),
                        "unit": shares.get("unit"),
                        "period": copy.deepcopy(shares.get("period")),
                        "filing": copy.deepcopy(shares.get("filing")),
                        "taxonomy": shares.get("taxonomy"),
                        "concept": shares.get("concept"),
                        "source_snapshot_sha256": shares.get("source", {}).get("snapshot_sha256"),
                    }

                minority = _safe_extract(
                    blockers,
                    "SEC_EXACT_MINORITY_INTEREST_UNAVAILABLE",
                    lambda: extract_sec_minority_interest_candidate(sec_snapshot, form=requested_form, period_end=period_end),
                )
                if minority is not None:
                    _safe_extract(blockers, "SEC_EXACT_MINORITY_INTEREST_INVALID", lambda: validate_minority_interest_candidate(minority))
                    checks["minority_interest_candidate"] = {
                        "metric": minority.get("metric"),
                        "value": minority.get("value"),
                        "unit": minority.get("unit"),
                        "period": copy.deepcopy(minority.get("period")),
                        "source_identity": copy.deepcopy(minority.get("source_identity")),
                        "candidate_sha256": minority.get("candidate_sha256"),
                        "explicit_zero": minority.get("value") == 0,
                    }

    legacy_supported = sorted(SEC_COMPONENT_SUPPORT)
    legacy_required = list(CORE_COMPONENTS)
    missing = [component for component in legacy_required if component not in SEC_COMPONENT_SUPPORT]
    checks["us_sec_debt_profile"] = {
        "legacy_required_components": legacy_required,
        "legacy_sec_supported_components": legacy_supported,
        "legacy_missing_components": missing,
        "complete_profile_supported": not missing,
    }
    if missing:
        blockers.append(_block(
            "M19_SEC_COMPLETE_DEBT_PROFILE_UNAVAILABLE",
            "historical M19 SEC v0.1 cannot produce COMPLETE_CORE_COMPONENTS without fabricating missing debt components; missing=" + ",".join(missing),
        ))

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": PASS_STATUS if not blockers else HOLD_STATUS,
        "canonical": False,
        "target": {
            "case_id": case,
            "legal_name": name,
            "ticker": symbol,
            "exchange": venue,
            "cik": normalized_cik,
            "entity_id": f"SEC_CIK:{normalized_cik}",
            "financial_scope": "CFS",
            "financial_period_end": period_end,
            "valuation_as_of": as_of,
            "form": requested_form,
        },
        "checks": checks,
        "blockers": blockers,
        "human_review_boundary": {
            "automatic_approval_forbidden": True,
            "reviewer_must_be_explicit": True,
            "runtime_sec_user_agent_must_not_be_committed": True,
            "canonical_write": False,
        },
        "next_action": "RESOLVE_BLOCKERS_THEN_CONTINUE_M20_M29" if blockers else "CONTINUE_REAL_SOURCE_GOVERNANCE",
        "preflight_sha256": "",
    }
    unsigned = copy.deepcopy(result)
    unsigned.pop("preflight_sha256", None)
    result["preflight_sha256"] = _sha(unsigned)
    validate_real_equity_source_preflight(result)
    return result


def validate_real_equity_source_preflight(preflight: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(preflight, dict) or preflight.get("schema_version") != SCHEMA_VERSION:
        raise CaseServiceError("M30 preflight schema invalid / M30 preflight 스키마 오류")
    if preflight.get("status") not in {PASS_STATUS, HOLD_STATUS} or preflight.get("canonical") is not False:
        raise CaseServiceError("M30 preflight status/canonical invalid / M30 preflight 상태·정식여부 오류")
    target, checks, blockers, boundary = (
        preflight.get("target"), preflight.get("checks"), preflight.get("blockers"), preflight.get("human_review_boundary")
    )
    if not isinstance(target, dict) or not isinstance(checks, dict) or not isinstance(blockers, list) or not isinstance(boundary, dict):
        raise CaseServiceError("M30 preflight structure incomplete / M30 preflight 구조 불완전")
    normalize_cik(target.get("cik"))
    if target.get("entity_id") != f"SEC_CIK:{target.get('cik')}" or target.get("financial_scope") != "CFS":
        raise CaseServiceError("M30 target identity invalid / M30 대상 식별 오류")
    if any(not isinstance(item, dict) or not isinstance(item.get("code"), str) or not item.get("code") for item in blockers):
        raise CaseServiceError("M30 blocker format invalid / M30 blocker 형식 오류")
    if len({item["code"] for item in blockers}) != len(blockers):
        raise CaseServiceError("M30 blocker codes must be unique / M30 blocker code 중복")
    expected_status = HOLD_STATUS if blockers else PASS_STATUS
    if preflight.get("status") != expected_status:
        raise CaseServiceError("M30 preflight status/blocker mismatch / M30 preflight 상태·blocker 불일치")
    if boundary != {
        "automatic_approval_forbidden": True,
        "reviewer_must_be_explicit": True,
        "runtime_sec_user_agent_must_not_be_committed": True,
        "canonical_write": False,
    }:
        raise CaseServiceError("M30 human-review boundary invalid / M30 인간검토 경계 오류")
    expected_next = "RESOLVE_BLOCKERS_THEN_CONTINUE_M20_M29" if blockers else "CONTINUE_REAL_SOURCE_GOVERNANCE"
    if preflight.get("next_action") != expected_next:
        raise CaseServiceError("M30 next-action mismatch / M30 next-action 불일치")
    unsigned = copy.deepcopy(preflight)
    unsigned.pop("preflight_sha256", None)
    expected = _sha(unsigned)
    if preflight.get("preflight_sha256") != expected:
        raise CaseServiceError("M30 preflight SHA mismatch / M30 preflight SHA 불일치")
    return {
        "status": "PASS_M30_PREFLIGHT_ARTIFACT_VALIDATION",
        "canonical": False,
        "decision": preflight["status"],
        "blocker_count": len(blockers),
        "preflight_sha256": expected,
    }
