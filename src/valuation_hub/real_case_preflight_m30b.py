"""M30-B real-equity source preflight successor.

This module preserves the complete M30-A v0.1 preflight as nested evidence and
resolves only the historical U.S. debt architectural blocker through the canonical
M30-P1 reviewed SEC aggregate-debt successor. It does not perform human semantic
review and never writes canonical state.
"""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.real_case_preflight import (
    HOLD_STATUS,
    PASS_STATUS,
    build_real_equity_source_preflight,
    validate_real_equity_source_preflight,
)
from valuation_hub.sec_aggregate_debt import (
    CANDIDATE_SCHEMA as SEC_DEBT_CANDIDATE_SCHEMA,
    SEC_CONCEPT,
    extract_sec_aggregate_debt_candidate,
    validate_sec_aggregate_debt_candidate,
)

SCHEMA_VERSION = "real-equity-source-preflight-v0.2"
STATUS_PASS = PASS_STATUS
STATUS_HOLD = HOLD_STATUS
LEGACY_DEBT_BLOCKER = "M19_SEC_COMPLETE_DEBT_PROFILE_UNAVAILABLE"
SUCCESSOR_DEBT_BLOCKER = "SEC_EXACT_AGGREGATE_DEBT_UNAVAILABLE"
NEXT_HOLD = "RESOLVE_BLOCKERS_THEN_CONTINUE_M20_M29"
NEXT_DEBT_REVIEW = "CONTINUE_TO_HUMAN_DEBT_SEMANTIC_REVIEW"


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    out = copy.deepcopy(value)
    out.pop(key, None)
    return out


def _block(code: str, detail: str) -> dict[str, str]:
    return {"code": code, "detail": detail}


def _successor_projection(candidate: dict[str, Any]) -> dict[str, Any]:
    validate_sec_aggregate_debt_candidate(candidate)
    return {
        "schema_version": candidate["schema_version"],
        "metric": candidate["metric"],
        "value": candidate["value"],
        "unit": candidate["unit"],
        "entity": copy.deepcopy(candidate["entity"]),
        "period": copy.deepcopy(candidate["period"]),
        "filing": copy.deepcopy(candidate["filing"]),
        "source_identity": copy.deepcopy(candidate["source_identity"]),
        "source_snapshot_sha256": candidate["source"]["snapshot_sha256"],
        "source_body_sha256": candidate["source"]["body_sha256"],
        "candidate_sha256": candidate["candidate_sha256"],
        "requires_human_semantic_review": True,
        "review_may_be_inferred": False,
    }


def build_real_equity_source_preflight_v2(
    *,
    case_id: str,
    legal_name: str,
    ticker: str,
    exchange: str,
    cik: str | int,
    financial_period_end: str,
    valuation_as_of: str,
    sec_snapshot: dict[str, Any] | None,
    root=None,
    form: str = "10-Q",
    shares_period_end: str | None = None,
) -> dict[str, Any]:
    """Build M30-B v0.2 while preserving exact M30-A v0.1 output."""
    base = build_real_equity_source_preflight(
        case_id=case_id,
        legal_name=legal_name,
        ticker=ticker,
        exchange=exchange,
        cik=cik,
        financial_period_end=financial_period_end,
        valuation_as_of=valuation_as_of,
        sec_snapshot=sec_snapshot,
        root=root,
        form=form,
        shares_period_end=shares_period_end,
    )
    validate_real_equity_source_preflight(base)

    blockers = [copy.deepcopy(item) for item in base["blockers"] if item.get("code") != LEGACY_DEBT_BLOCKER]
    checks = copy.deepcopy(base["checks"])
    debt_candidate: dict[str, Any] | None = None

    if sec_snapshot is not None and checks.get("sec_snapshot") is not None:
        try:
            debt_candidate = extract_sec_aggregate_debt_candidate(
                sec_snapshot,
                form=base["target"]["form"],
                period_end=base["target"]["financial_period_end"],
            )
        except (CaseServiceError, KeyError, TypeError, ValueError) as exc:
            blockers.append(_block(SUCCESSOR_DEBT_BLOCKER, str(exc)))

    projection = _successor_projection(debt_candidate) if debt_candidate is not None else None
    legacy = checks.get("us_sec_debt_profile")
    checks["us_sec_debt_profile"] = {
        "legacy_v01": copy.deepcopy(legacy),
        "legacy_blocker_resolved_by": "M30-P1_REVIEWED_SEC_AGGREGATE_DEBT_SUCCESSOR",
        "successor_candidate_schema": SEC_DEBT_CANDIDATE_SCHEMA,
        "successor_exact_concept": {"taxonomy": SEC_CONCEPT[0], "concept": SEC_CONCEPT[1]},
        "successor_candidate_available": projection is not None,
        "successor_requires_human_semantic_review": True,
        "successor_review_may_be_inferred": False,
    }
    checks["sec_aggregate_debt_candidate"] = projection

    boundary = copy.deepcopy(base["human_review_boundary"])
    boundary["debt_semantic_review_required"] = True
    boundary["debt_semantic_review_may_be_inferred"] = False

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_PASS if not blockers else STATUS_HOLD,
        "canonical": False,
        "target": copy.deepcopy(base["target"]),
        "checks": checks,
        "blockers": blockers,
        "resolved_prerequisites": [
            {
                "code": LEGACY_DEBT_BLOCKER,
                "resolution": "M30-P1 reviewed exact SEC aggregate-debt successor",
                "canonical_main": "11182eeab7e60a90e6ddc140ca05f45e93af7e40",
            }
        ],
        "human_review_boundary": boundary,
        "next_action": NEXT_HOLD if blockers else NEXT_DEBT_REVIEW,
        "base_v01_preflight": copy.deepcopy(base),
        "base_v01_preflight_sha256": base["preflight_sha256"],
        "preflight_sha256": "",
    }
    result["preflight_sha256"] = _sha(_without(result, "preflight_sha256"))
    validate_real_equity_source_preflight_v2(result)
    return result


def validate_real_equity_source_preflight_v2(preflight: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(preflight, dict) or preflight.get("schema_version") != SCHEMA_VERSION:
        raise CaseServiceError("M30-B preflight schema invalid / M30-B preflight 스키마 오류")
    if preflight.get("canonical") is not False or preflight.get("status") not in {STATUS_PASS, STATUS_HOLD}:
        raise CaseServiceError("M30-B preflight status/canonical invalid / M30-B preflight 상태·정식여부 오류")

    base = preflight.get("base_v01_preflight")
    if not isinstance(base, dict):
        raise CaseServiceError("M30-B base v0.1 preflight missing / M30-B base v0.1 preflight 누락")
    validate_real_equity_source_preflight(base)
    if preflight.get("base_v01_preflight_sha256") != base.get("preflight_sha256"):
        raise CaseServiceError("M30-B base v0.1 SHA mismatch / M30-B base v0.1 SHA 불일치")
    if preflight.get("target") != base.get("target"):
        raise CaseServiceError("M30-B target drift from base v0.1 / M30-B 대상이 base v0.1에서 변경됨")

    blockers = preflight.get("blockers")
    checks = preflight.get("checks")
    boundary = preflight.get("human_review_boundary")
    resolved = preflight.get("resolved_prerequisites")
    if not isinstance(blockers, list) or not isinstance(checks, dict) or not isinstance(boundary, dict) or not isinstance(resolved, list):
        raise CaseServiceError("M30-B structure incomplete / M30-B 구조 불완전")
    if any(not isinstance(item, dict) or not isinstance(item.get("code"), str) or not item["code"] for item in blockers):
        raise CaseServiceError("M30-B blocker format invalid / M30-B blocker 형식 오류")
    if len({item["code"] for item in blockers}) != len(blockers):
        raise CaseServiceError("M30-B blocker codes must be unique / M30-B blocker code 중복")
    if any(item.get("code") == LEGACY_DEBT_BLOCKER for item in blockers):
        raise CaseServiceError("M30-B must not retain resolved legacy debt blocker / M30-B는 해결된 legacy debt blocker를 유지할 수 없음")

    base_expected = [copy.deepcopy(item) for item in base["blockers"] if item.get("code") != LEGACY_DEBT_BLOCKER]
    candidate = checks.get("sec_aggregate_debt_candidate")
    successor_available = candidate is not None
    expected_blockers = base_expected
    if successor_available:
        if not isinstance(candidate, dict):
            raise CaseServiceError("M30-B debt candidate projection invalid / M30-B debt candidate projection 오류")
        if candidate.get("schema_version") != SEC_DEBT_CANDIDATE_SCHEMA:
            raise CaseServiceError("M30-B debt candidate schema drift / M30-B debt candidate 스키마 drift")
        identity = candidate.get("source_identity")
        if identity != {"taxonomy": SEC_CONCEPT[0], "concept": SEC_CONCEPT[1]}:
            raise CaseServiceError("M30-B exact aggregate debt identity drift / M30-B exact aggregate debt 식별 drift")
        if candidate.get("entity") != {"id": base["target"]["entity_id"], "financial_scope": "CFS"}:
            raise CaseServiceError("M30-B debt entity mismatch / M30-B debt entity 불일치")
        if candidate.get("period", {}).get("end") != base["target"]["financial_period_end"]:
            raise CaseServiceError("M30-B debt period mismatch / M30-B debt period 불일치")
        if candidate.get("requires_human_semantic_review") is not True or candidate.get("review_may_be_inferred") is not False:
            raise CaseServiceError("M30-B debt human-review boundary invalid / M30-B debt 인간검토 경계 오류")
    else:
        if base.get("checks", {}).get("sec_snapshot") is not None:
            matches = [item for item in blockers if item.get("code") == SUCCESSOR_DEBT_BLOCKER]
            if len(matches) != 1:
                raise CaseServiceError("M30-B missing exact-debt blocker / M30-B exact-debt blocker 누락")
        expected_blockers = [item for item in blockers]

    debt_profile = checks.get("us_sec_debt_profile")
    if not isinstance(debt_profile, dict):
        raise CaseServiceError("M30-B debt-profile check missing / M30-B debt-profile check 누락")
    if debt_profile.get("legacy_v01") != base.get("checks", {}).get("us_sec_debt_profile"):
        raise CaseServiceError("M30-B legacy debt check drift / M30-B legacy debt check drift")
    if debt_profile.get("successor_candidate_available") is not successor_available:
        raise CaseServiceError("M30-B successor availability mismatch / M30-B successor availability 불일치")
    if debt_profile.get("successor_requires_human_semantic_review") is not True or debt_profile.get("successor_review_may_be_inferred") is not False:
        raise CaseServiceError("M30-B successor review policy invalid / M30-B successor 검토정책 오류")

    if boundary.get("automatic_approval_forbidden") is not True or boundary.get("canonical_write") is not False:
        raise CaseServiceError("M30-B inherited human-review boundary invalid / M30-B 상속 인간검토 경계 오류")
    if boundary.get("debt_semantic_review_required") is not True or boundary.get("debt_semantic_review_may_be_inferred") is not False:
        raise CaseServiceError("M30-B debt review boundary invalid / M30-B debt 검토경계 오류")

    expected_status = STATUS_HOLD if blockers else STATUS_PASS
    if preflight.get("status") != expected_status:
        raise CaseServiceError("M30-B status/blocker mismatch / M30-B 상태·blocker 불일치")
    expected_next = NEXT_HOLD if blockers else NEXT_DEBT_REVIEW
    if preflight.get("next_action") != expected_next:
        raise CaseServiceError("M30-B next-action mismatch / M30-B next-action 불일치")

    if resolved != [{
        "code": LEGACY_DEBT_BLOCKER,
        "resolution": "M30-P1 reviewed exact SEC aggregate-debt successor",
        "canonical_main": "11182eeab7e60a90e6ddc140ca05f45e93af7e40",
    }]:
        raise CaseServiceError("M30-B resolved-prerequisite lineage invalid / M30-B 해결 prerequisite lineage 오류")

    expected = _sha(_without(preflight, "preflight_sha256"))
    if preflight.get("preflight_sha256") != expected:
        raise CaseServiceError("M30-B preflight SHA mismatch / M30-B preflight SHA 불일치")
    return {
        "status": "PASS_M30B_PREFLIGHT_ARTIFACT_VALIDATION",
        "canonical": False,
        "decision": preflight["status"],
        "blocker_count": len(blockers),
        "successor_debt_candidate_available": successor_available,
        "preflight_sha256": expected,
    }
