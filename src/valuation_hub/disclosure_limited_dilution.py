"""M30-R6 disclosure-limited diluted-share assumption.

R6 never weakens M22/M30-R4 exact dilution semantics. It is a separately typed
ASSUMPTION fallback for cases where R4 is HOLD because public issuer disclosure
cannot fully reconstruct valuation-date dilution, while contradiction search is
clean and a conservative source-bound materiality envelope is narrow enough.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import date, datetime
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
from valuation_hub.ai_historical_dilution_authority import (
    PACKAGE_SCHEMA as AI_HISTORICAL_PACKAGE_SCHEMA,
    validate_ai_reviewed_historical_dilution_package,
)
from valuation_hub.case_service import CaseServiceError
from valuation_hub.share_dilution import validate_historical_dilution
from valuation_hub.valuation_shares import FRESH, validate_valuation_share_base_context

EVIDENCE_SCHEMA = "disclosure-limited-dilution-evidence-v0.1"
EVIDENCE_STATUS = "DISCLOSURE_LIMITED_DILUTION_EVIDENCE_EVALUATED"
ADJUDICATION_SCHEMA = "disclosure-limited-dilution-adjudication-v0.1"
ADJUDICATION_STATUS = "DISCLOSURE_LIMITED_DILUTION_ADJUDICATED"
PACKAGE_SCHEMA = "disclosure-limited-diluted-share-assumption-v0.1"
PACKAGE_STATUS = "DISCLOSURE_LIMITED_DILUTED_SHARE_ASSUMPTION_READY"

POLICY_ID = "DISCLOSURE_LIMITED_DILUTION_ASSUMPTION_V01"
ADJUDICATOR_TYPE = "AI"
ADJUDICATOR_ID = "AI_DISCLOSURE_LIMITED_DILUTION_ADJUDICATOR_V01"

READY = "READY_FOR_DISCLOSURE_LIMITED_DILUTION_ADJUDICATION"
HOLD_MATERIALITY = "HOLD_DISCLOSURE_LIMITED_DILUTION_MATERIALITY"
APPROVE = "APPROVE_DISCLOSURE_LIMITED_DILUTION_ASSUMPTION"

ROLE_ANCHOR = "ANCHOR_OUTSTANDING_AWARDS"
ROLE_SUBSEQUENT = "SUBSEQUENT_GROSS_GRANT"
ROLE_PERFORMANCE_UPLIFT = "PERFORMANCE_MAX_UPLIFT"
ROLE_BUFFER = "DISCLOSURE_LAG_BUFFER"
ROLES = {ROLE_ANCHOR, ROLE_SUBSEQUENT, ROLE_PERFORMANCE_UPLIFT, ROLE_BUFFER}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


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


def _timestamp(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise CaseServiceError(f"{field} timezone-aware timestamp required / {field} 시간대 포함 시각 필요")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CaseServiceError(f"{field} ISO timestamp invalid / {field} 시각 오류") from exc
    if parsed.tzinfo is None:
        raise CaseServiceError(f"{field} timezone required / {field} 시간대 필요")
    return parsed.isoformat()


def _source_rows(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise CaseServiceError("envelope component requires source evidence / envelope component 출처근거 필요")
    result: list[dict[str, str]] = []
    for row in value:
        if not isinstance(row, dict):
            raise CaseServiceError("envelope source object required / envelope 출처 객체 필요")
        sha = row.get("snapshot_sha256")
        if not isinstance(sha, str) or not SHA256_RE.fullmatch(sha):
            raise CaseServiceError("envelope source SHA invalid / envelope 출처 SHA 오류")
        result.append({
            "locator": _text(row.get("locator"), "source.locator", 2000),
            "snapshot_sha256": sha,
            "source_type": _text(row.get("source_type"), "source.source_type", 160),
        })
    return result


def _normalize_components(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise CaseServiceError("upper-envelope components required / upper-envelope 구성요소 필요")
    ids: set[str] = set()
    rows: list[dict[str, Any]] = []
    for raw in value:
        if not isinstance(raw, dict):
            raise CaseServiceError("upper-envelope component object required / upper-envelope 구성요소 객체 필요")
        component_id = _text(raw.get("component_id"), "component_id", 120)
        if component_id in ids:
            raise CaseServiceError("duplicate upper-envelope component id / upper-envelope 구성요소 id 중복")
        ids.add(component_id)
        role = raw.get("role")
        if role not in ROLES:
            raise CaseServiceError("unsupported upper-envelope role / 미지원 upper-envelope 역할")
        shares = _num(raw.get("shares"), "component.shares")
        calculation = raw.get("calculation")
        if role == ROLE_BUFFER:
            if not isinstance(calculation, dict) or calculation.get("method") != "PRO_RATA_GROSS_GRANT_RUN_RATE_V01":
                raise CaseServiceError("disclosure-lag buffer requires reproducible pro-rata calculation / 공시시차 buffer는 재현 가능한 비례계산 필요")
            observed_grants = _num(calculation.get("observed_gross_grants"), "buffer.observed_gross_grants")
            observed_days = calculation.get("observed_days")
            lag_days = calculation.get("lag_days")
            if isinstance(observed_days, bool) or not isinstance(observed_days, int) or observed_days <= 0:
                raise CaseServiceError("buffer observed_days positive integer required / buffer observed_days 양의 정수 필요")
            if isinstance(lag_days, bool) or not isinstance(lag_days, int) or lag_days < 0:
                raise CaseServiceError("buffer lag_days nonnegative integer required / buffer lag_days 음이 아닌 정수 필요")
            expected_buffer = observed_grants * lag_days / observed_days
            if abs(shares - expected_buffer) > max(1e-6, abs(expected_buffer) * 1e-9):
                raise CaseServiceError("disclosure-lag buffer does not reproduce pro-rata inputs / 공시시차 buffer 재현 불일치")
            normalized_calculation = {
                "method": "PRO_RATA_GROSS_GRANT_RUN_RATE_V01",
                "observed_gross_grants": observed_grants,
                "observed_days": observed_days,
                "lag_days": lag_days,
            }
        elif calculation not in (None, {}):
            raise CaseServiceError("non-buffer envelope component cannot carry calculation / 비buffer envelope 구성요소 계산정보 불가")
        else:
            normalized_calculation = None
        rows.append({
            "component_id": component_id,
            "role": role,
            "shares": shares,
            "as_of": _iso(raw.get("as_of"), "component.as_of"),
            "sources": _source_rows(raw.get("sources")),
            "evidence_basis": _text(raw.get("evidence_basis"), "component.evidence_basis"),
            "calculation": normalized_calculation,
        })
    if sum(1 for row in rows if row["role"] == ROLE_ANCHOR) != 1:
        raise CaseServiceError("exactly one anchor outstanding-awards component required / anchor outstanding-awards 구성요소 정확히 1개 필요")
    return rows


def _historical_input(value: dict[str, Any]) -> tuple[dict[str, Any], str, str]:
    if isinstance(value, dict) and value.get("schema_version") == AI_HISTORICAL_PACKAGE_SCHEMA:
        checked = validate_ai_reviewed_historical_dilution_package(value)
        historical = value.get("historical_dilution")
        if not isinstance(historical, dict):
            raise CaseServiceError("R7 historical dilution payload missing / R7 역사적 희석 payload 누락")
        return historical, value["package_sha256"], checked["status"]
    if not isinstance(value, dict):
        raise CaseServiceError("historical dilution object required / 역사적 희석 객체 필요")
    derived_sha = value.get("derived_sha256")
    if not isinstance(derived_sha, str) or not SHA256_RE.fullmatch(derived_sha):
        raise CaseServiceError("historical dilution SHA invalid / 역사적 희석 SHA 오류")
    return value, derived_sha, "LEGACY_HISTORICAL_DILUTION_INPUT"


def _historical_diluted_shares(value: dict[str, Any], *, as_of: str, max_age_days: int) -> tuple[float, dict[str, Any]]:
    historical, _, authority_status = _historical_input(value)
    checked = validate_historical_dilution(historical)
    if historical.get("class") != "DERIVED_FACT":
        raise CaseServiceError("reviewed historical dilution FACT required / 검토된 역사적 희석 FACT 필요")
    boundary = historical.get("semantic_boundary", {})
    if boundary.get("historical_only") is not True or boundary.get("valuation_date_direct_bind") is not False:
        raise CaseServiceError("historical dilution semantic boundary invalid / 역사적 희석 의미경계 오류")
    period = historical.get("period", {})
    end = _iso(period.get("end"), "historical.period.end")
    as_of_date = date.fromisoformat(_iso(as_of, "as_of"))
    end_date = date.fromisoformat(end)
    age = (as_of_date - end_date).days
    if age < 0 or isinstance(max_age_days, bool) or not isinstance(max_age_days, int) or not 0 <= max_age_days <= 3650:
        raise CaseServiceError("historical dilution freshness policy invalid / 역사적 희석 최신성 정책 오류")
    if age > max_age_days:
        raise CaseServiceError("historical diluted-share anchor stale / 역사적 희석주식 anchor 오래됨")
    by = {item["metric"]: item for item in historical["sources"]}
    diluted = _num(by["weighted_average_diluted_shares"]["value"], "historical diluted shares", positive=True)
    return diluted, {
        "age_days": age,
        "max_age_days": max_age_days,
        "status": FRESH,
        "validation_status": checked["status"],
        "authority_status": authority_status,
    }


def _exact_present_adjustments(inventory: dict[str, Any]) -> float:
    return sum(_num(row["adjustment_shares"], f'{row["category"]}.adjustment_shares') for row in inventory["categories"] if row["state"] == PRESENT)


def build_disclosure_limited_dilution_evidence(
    base_context: dict[str, Any],
    hold_inventory: dict[str, Any],
    historical_dilution: dict[str, Any],
    upper_envelope_components: list[dict[str, Any]],
    *,
    as_of: str,
    materiality_threshold: float = 0.05,
    max_historical_age_days: int = 180,
) -> dict[str, Any]:
    base_checked = validate_valuation_share_base_context(base_context)
    if base_checked.get("freshness") != FRESH:
        raise CaseServiceError("fresh current-share base required / 최신 현재주식수 base 필요")
    inv_checked = validate_ai_dilution_inventory(hold_inventory, base_context)
    if inv_checked.get("decision") != HOLD or hold_inventory.get("decision") != HOLD:
        raise CaseServiceError("R6 requires an incomplete R4 HOLD; exact READY path outranks fallback / R6는 불완전 R4 HOLD 필요")
    if any(row["state"] == UNKNOWN_CONFLICT for row in hold_inventory["categories"]):
        raise CaseServiceError("R6 cannot override UNKNOWN_CONFLICT / R6는 UNKNOWN_CONFLICT 우회 불가")
    if not any(row["state"] == BLOCKED_DEPENDENCY for row in hold_inventory["categories"]):
        raise CaseServiceError("R6 requires disclosure-limited blockers / R6는 공시제약 blocker 필요")
    if hold_inventory.get("as_of") != as_of or base_context.get("policy", {}).get("as_of") != as_of:
        raise CaseServiceError("R6 as_of must equal R4/base valuation date / R6 as_of 불일치")

    threshold = _num(materiality_threshold, "materiality_threshold", positive=True)
    if threshold > 0.25:
        raise CaseServiceError("materiality threshold above 25% not permitted / materiality threshold 25% 초과 불가")

    historical_anchor, historical_freshness = _historical_diluted_shares(
        historical_dilution, as_of=as_of, max_age_days=max_historical_age_days
    )
    if historical_dilution.get("entity") != base_context.get("entity"):
        raise CaseServiceError("historical dilution/base entity mismatch / 역사적 희석·base entity 불일치")

    components = _normalize_components(upper_envelope_components)
    if any(date.fromisoformat(row["as_of"]) > date.fromisoformat(as_of) for row in components):
        raise CaseServiceError("upper-envelope evidence after valuation date not allowed / 가치평가일 이후 envelope 근거 불가")

    base_shares = _num(base_context.get("value"), "base current shares", positive=True)
    exact_present = _exact_present_adjustments(hold_inventory)
    exact_present_floor = base_shares + exact_present
    selected = max(historical_anchor, exact_present_floor)
    upper_increment = sum(row["shares"] for row in components)
    upper = base_shares + upper_increment
    lower = base_shares
    if upper < selected:
        raise CaseServiceError("upper envelope below selected assumption / upper envelope가 선택 가정보다 작음")
    spread = upper / selected - 1.0
    decision = READY if spread <= threshold else HOLD_MATERIALITY

    evidence = {
        "schema_version": EVIDENCE_SCHEMA,
        "status": EVIDENCE_STATUS,
        "canonical": False,
        "policy_id": POLICY_ID,
        "decision": decision,
        "as_of": as_of,
        "entity": copy.deepcopy(base_context["entity"]),
        "base_context_sha256": base_context["context_sha256"],
        "r4_inventory_sha256": hold_inventory["inventory_sha256"],
        "historical_dilution_sha256": _historical_input(historical_dilution)[1],
        "historical_freshness": historical_freshness,
        "selection": {
            "current_common_shares": base_shares,
            "exact_present_adjustments": exact_present,
            "exact_present_floor": exact_present_floor,
            "historical_diluted_anchor": historical_anchor,
            "selected_shares": selected,
            "rule": "MAX_LATEST_ISSUER_DILUTED_ANCHOR_AND_EXACT_PRESENT_FLOOR",
        },
        "upper_envelope": {
            "components": components,
            "incremental_shares": upper_increment,
            "lower_shares": lower,
            "upper_shares": upper,
            "relative_upper_spread": spread,
            "materiality_threshold": threshold,
            "conservative_no_netting": True,
        },
        "blockers": copy.deepcopy(inv_checked["blockers"]),
        "semantic_boundary": {
            "exact_r4_path_outranks_fallback": True,
            "historical_diluted_shares_remain_duration_reference": True,
            "selected_value_is_assumption_not_fact": True,
            "selected_value_is_assumption_not_derived_fact": True,
            "upper_envelope_is_conservative_not_exact": True,
            "unknown_conflict_never_fallback": True,
            "direct_bind_as_m22_derived_fact": False,
        },
        "evidence_sha256": "",
    }
    evidence["evidence_sha256"] = _sha(_without(evidence, "evidence_sha256"))
    validate_disclosure_limited_dilution_evidence(
        evidence, base_context, hold_inventory, historical_dilution, upper_envelope_components
    )
    return evidence


def validate_disclosure_limited_dilution_evidence(
    evidence: dict[str, Any],
    base_context: dict[str, Any],
    hold_inventory: dict[str, Any],
    historical_dilution: dict[str, Any],
    upper_envelope_components: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(evidence, dict) or evidence.get("schema_version") != EVIDENCE_SCHEMA or evidence.get("status") != EVIDENCE_STATUS or evidence.get("canonical") is not False or evidence.get("policy_id") != POLICY_ID:
        raise CaseServiceError("R6 evidence schema/status invalid / R6 evidence 스키마·상태 오류")

    base_checked = validate_valuation_share_base_context(base_context)
    if base_checked.get("freshness") != FRESH:
        raise CaseServiceError("R6 evidence base stale / R6 evidence base 오래됨")
    inv_checked = validate_ai_dilution_inventory(hold_inventory, base_context)
    if inv_checked.get("decision") != HOLD or hold_inventory.get("decision") != HOLD:
        raise CaseServiceError("R6 evidence requires R4 HOLD / R6 evidence는 R4 HOLD 필요")
    if any(row["state"] == UNKNOWN_CONFLICT for row in hold_inventory["categories"]):
        raise CaseServiceError("R6 evidence cannot contain UNKNOWN_CONFLICT / R6 evidence UNKNOWN_CONFLICT 불가")

    as_of = _iso(evidence.get("as_of"), "as_of")
    if hold_inventory.get("as_of") != as_of or base_context.get("policy", {}).get("as_of") != as_of:
        raise CaseServiceError("R6 evidence as_of lineage mismatch / R6 evidence as_of 계보 불일치")
    if historical_dilution.get("entity") != base_context.get("entity") or evidence.get("entity") != base_context.get("entity"):
        raise CaseServiceError("R6 evidence entity mismatch / R6 evidence entity 불일치")

    hist_policy = evidence.get("historical_freshness")
    if not isinstance(hist_policy, dict) or not isinstance(hist_policy.get("max_age_days"), int):
        raise CaseServiceError("R6 historical freshness projection invalid / R6 역사 최신성 투영 오류")
    historical_anchor, expected_hist_freshness = _historical_diluted_shares(
        historical_dilution, as_of=as_of, max_age_days=hist_policy["max_age_days"]
    )

    components = _normalize_components(upper_envelope_components)
    if any(date.fromisoformat(row["as_of"]) > date.fromisoformat(as_of) for row in components):
        raise CaseServiceError("upper-envelope evidence after valuation date not allowed / 가치평가일 이후 envelope 근거 불가")

    if evidence.get("base_context_sha256") != base_context.get("context_sha256") or evidence.get("r4_inventory_sha256") != hold_inventory.get("inventory_sha256") or evidence.get("historical_dilution_sha256") != _historical_input(historical_dilution)[1]:
        raise CaseServiceError("R6 evidence lineage mismatch / R6 evidence 계보 불일치")
    if evidence.get("historical_freshness") != expected_hist_freshness:
        raise CaseServiceError("R6 historical freshness mismatch / R6 역사 최신성 불일치")

    threshold = _num(evidence.get("upper_envelope", {}).get("materiality_threshold"), "materiality threshold", positive=True)
    if threshold > 0.25:
        raise CaseServiceError("materiality threshold above 25% not permitted / materiality threshold 25% 초과 불가")
    base_shares = _num(base_context.get("value"), "base current shares", positive=True)
    exact_present = _exact_present_adjustments(hold_inventory)
    exact_present_floor = base_shares + exact_present
    selected = max(historical_anchor, exact_present_floor)
    upper_increment = sum(row["shares"] for row in components)
    upper = base_shares + upper_increment
    lower = base_shares
    if upper < selected:
        raise CaseServiceError("upper envelope below selected assumption / upper envelope가 선택 가정보다 작음")
    spread = upper / selected - 1.0
    expected_decision = READY if spread <= threshold else HOLD_MATERIALITY

    expected_selection = {
        "current_common_shares": base_shares,
        "exact_present_adjustments": exact_present,
        "exact_present_floor": exact_present_floor,
        "historical_diluted_anchor": historical_anchor,
        "selected_shares": selected,
        "rule": "MAX_LATEST_ISSUER_DILUTED_ANCHOR_AND_EXACT_PRESENT_FLOOR",
    }
    expected_envelope = {
        "components": components,
        "incremental_shares": upper_increment,
        "lower_shares": lower,
        "upper_shares": upper,
        "relative_upper_spread": spread,
        "materiality_threshold": threshold,
        "conservative_no_netting": True,
    }
    if evidence.get("selection") != expected_selection or evidence.get("upper_envelope") != expected_envelope:
        raise CaseServiceError("R6 evidence independent projection mismatch / R6 evidence 독립 재계산 불일치")
    if evidence.get("blockers") != inv_checked.get("blockers") or evidence.get("decision") != expected_decision:
        raise CaseServiceError("R6 evidence blockers/materiality decision mismatch / R6 evidence blocker·materiality 판정 불일치")

    expected_boundary = {
        "exact_r4_path_outranks_fallback": True,
        "historical_diluted_shares_remain_duration_reference": True,
        "selected_value_is_assumption_not_fact": True,
        "selected_value_is_assumption_not_derived_fact": True,
        "upper_envelope_is_conservative_not_exact": True,
        "unknown_conflict_never_fallback": True,
        "direct_bind_as_m22_derived_fact": False,
    }
    if evidence.get("semantic_boundary") != expected_boundary:
        raise CaseServiceError("R6 semantic boundary invalid / R6 의미경계 오류")

    expected_sha = _sha(_without(evidence, "evidence_sha256"))
    if evidence.get("evidence_sha256") != expected_sha:
        raise CaseServiceError("R6 evidence SHA mismatch / R6 evidence SHA 불일치")
    return {
        "status": "PASS_DISCLOSURE_LIMITED_DILUTION_EVIDENCE_VALIDATION",
        "evidence_sha256": expected_sha,
        "decision": expected_decision,
        "selected_shares": selected,
        "upper_shares": upper,
        "relative_upper_spread": spread,
    }

def build_disclosure_limited_dilution_adjudication(
    evidence: dict[str, Any],
    base_context: dict[str, Any],
    hold_inventory: dict[str, Any],
    historical_dilution: dict[str, Any],
    upper_envelope_components: list[dict[str, Any]],
    *,
    adjudicated_at: str,
) -> dict[str, Any]:
    checked_evidence = validate_disclosure_limited_dilution_evidence(
        evidence, base_context, hold_inventory, historical_dilution, upper_envelope_components
    )
    when = _timestamp(adjudicated_at, "adjudicated_at")
    decision = APPROVE if checked_evidence["decision"] == READY else HOLD_MATERIALITY
    adjudication = {
        "schema_version": ADJUDICATION_SCHEMA,
        "status": ADJUDICATION_STATUS,
        "canonical": False,
        "policy_id": POLICY_ID,
        "adjudicator": {"type": ADJUDICATOR_TYPE, "id": ADJUDICATOR_ID},
        "decision": decision,
        "adjudicated_at": when,
        "evidence_sha256": evidence["evidence_sha256"],
        "base_context_sha256": base_context["context_sha256"],
        "r4_inventory_sha256": hold_inventory["inventory_sha256"],
        "historical_dilution_sha256": _historical_input(historical_dilution)[1],
        "selected_shares": checked_evidence["selected_shares"],
        "upper_shares": checked_evidence["upper_shares"],
        "relative_upper_spread": checked_evidence["relative_upper_spread"],
        "adjudication_sha256": "",
    }
    adjudication["adjudication_sha256"] = _sha(_without(adjudication, "adjudication_sha256"))
    validate_disclosure_limited_dilution_adjudication(
        adjudication, evidence, base_context, hold_inventory, historical_dilution, upper_envelope_components
    )
    return adjudication


def validate_disclosure_limited_dilution_adjudication(
    adjudication: dict[str, Any],
    evidence: dict[str, Any],
    base_context: dict[str, Any],
    hold_inventory: dict[str, Any],
    historical_dilution: dict[str, Any],
    upper_envelope_components: list[dict[str, Any]],
) -> dict[str, Any]:
    checked_evidence = validate_disclosure_limited_dilution_evidence(
        evidence, base_context, hold_inventory, historical_dilution, upper_envelope_components
    )
    if not isinstance(adjudication, dict) or adjudication.get("schema_version") != ADJUDICATION_SCHEMA or adjudication.get("status") != ADJUDICATION_STATUS or adjudication.get("canonical") is not False or adjudication.get("policy_id") != POLICY_ID or adjudication.get("adjudicator") != {"type": ADJUDICATOR_TYPE, "id": ADJUDICATOR_ID}:
        raise CaseServiceError("R6 adjudication schema/authority invalid / R6 adjudication 스키마·권위 오류")
    _timestamp(adjudication.get("adjudicated_at"), "adjudicated_at")
    expected_decision = APPROVE if checked_evidence["decision"] == READY else HOLD_MATERIALITY
    if (
        adjudication.get("decision") != expected_decision
        or adjudication.get("evidence_sha256") != evidence.get("evidence_sha256")
        or adjudication.get("base_context_sha256") != base_context.get("context_sha256")
        or adjudication.get("r4_inventory_sha256") != hold_inventory.get("inventory_sha256")
        or adjudication.get("historical_dilution_sha256") != _historical_input(historical_dilution)[1]
        or adjudication.get("selected_shares") != checked_evidence["selected_shares"]
        or adjudication.get("upper_shares") != checked_evidence["upper_shares"]
        or abs(adjudication.get("relative_upper_spread") - checked_evidence["relative_upper_spread"]) > 1e-12
    ):
        raise CaseServiceError("R6 adjudication projection mismatch / R6 adjudication 투영 불일치")
    expected_sha = _sha(_without(adjudication, "adjudication_sha256"))
    if adjudication.get("adjudication_sha256") != expected_sha:
        raise CaseServiceError("R6 adjudication SHA mismatch / R6 adjudication SHA 불일치")
    return {
        "status": "PASS_DISCLOSURE_LIMITED_DILUTION_ADJUDICATION_VALIDATION",
        "adjudication_sha256": expected_sha,
        "decision": expected_decision,
    }


def finalize_disclosure_limited_dilution_assumption(
    evidence: dict[str, Any],
    adjudication: dict[str, Any],
    base_context: dict[str, Any],
    hold_inventory: dict[str, Any],
    historical_dilution: dict[str, Any],
    upper_envelope_components: list[dict[str, Any]],
) -> dict[str, Any]:
    checked = validate_disclosure_limited_dilution_adjudication(
        adjudication, evidence, base_context, hold_inventory, historical_dilution, upper_envelope_components
    )
    if checked["decision"] != APPROVE:
        raise CaseServiceError("R6 assumption finalization requires approved materiality envelope / R6 가정 finalization은 materiality 승인 필요")
    package = {
        "schema_version": PACKAGE_SCHEMA,
        "status": PACKAGE_STATUS,
        "canonical": False,
        "class": "ASSUMPTION",
        "metric": "fully_diluted_shares",
        "unit": "shares",
        "policy_id": POLICY_ID,
        "as_of": evidence["as_of"],
        "entity": copy.deepcopy(evidence["entity"]),
        "value": evidence["selection"]["selected_shares"],
        "range": {
            "lower": evidence["upper_envelope"]["lower_shares"],
            "selected": evidence["selection"]["selected_shares"],
            "upper": evidence["upper_envelope"]["upper_shares"],
            "relative_upper_spread": evidence["upper_envelope"]["relative_upper_spread"],
        },
        "review_authority": {
            "type": ADJUDICATOR_TYPE,
            "id": ADJUDICATOR_ID,
            "decision": APPROVE,
            "adjudicated_at": adjudication["adjudicated_at"],
            "evidence_sha256": evidence["evidence_sha256"],
            "adjudication_sha256": adjudication["adjudication_sha256"],
        },
        "binding_eligibility": {
            "eligible_for_assumption_aware_successor": True,
            "eligible_for_m22_derived_fact_direct_bind": False,
            "reason": "DISCLOSURE_LIMITED_DILUTION_ASSUMPTION_MATERIALITY_PASS",
        },
        "semantic_boundary": copy.deepcopy(evidence["semantic_boundary"]),
        "evidence": copy.deepcopy(evidence),
        "adjudication": copy.deepcopy(adjudication),
        "package_sha256": "",
    }
    package["package_sha256"] = _sha(_without(package, "package_sha256"))
    validate_disclosure_limited_dilution_assumption(
        package, evidence, adjudication, base_context, hold_inventory, historical_dilution, upper_envelope_components
    )
    return package


def validate_disclosure_limited_dilution_assumption(
    package: dict[str, Any],
    evidence: dict[str, Any],
    adjudication: dict[str, Any],
    base_context: dict[str, Any],
    hold_inventory: dict[str, Any],
    historical_dilution: dict[str, Any],
    upper_envelope_components: list[dict[str, Any]],
) -> dict[str, Any]:
    checked = validate_disclosure_limited_dilution_adjudication(
        adjudication, evidence, base_context, hold_inventory, historical_dilution, upper_envelope_components
    )
    if checked["decision"] != APPROVE:
        raise CaseServiceError("approved R6 adjudication required / 승인된 R6 adjudication 필요")
    if not isinstance(package, dict) or package.get("schema_version") != PACKAGE_SCHEMA or package.get("status") != PACKAGE_STATUS or package.get("canonical") is not False or package.get("class") != "ASSUMPTION" or package.get("metric") != "fully_diluted_shares" or package.get("unit") != "shares" or package.get("policy_id") != POLICY_ID:
        raise CaseServiceError("R6 assumption package schema/status invalid / R6 가정 package 스키마·상태 오류")
    if package.get("value") != evidence.get("selection", {}).get("selected_shares") or package.get("evidence") != evidence or package.get("adjudication") != adjudication:
        raise CaseServiceError("R6 assumption package projection mismatch / R6 가정 package 투영 불일치")
    eligibility = package.get("binding_eligibility")
    if eligibility != {
        "eligible_for_assumption_aware_successor": True,
        "eligible_for_m22_derived_fact_direct_bind": False,
        "reason": "DISCLOSURE_LIMITED_DILUTION_ASSUMPTION_MATERIALITY_PASS",
    }:
        raise CaseServiceError("R6 assumption binding boundary invalid / R6 가정 binding 경계 오류")
    expected_sha = _sha(_without(package, "package_sha256"))
    if package.get("package_sha256") != expected_sha:
        raise CaseServiceError("R6 assumption package SHA mismatch / R6 가정 package SHA 불일치")
    return {
        "status": "PASS_DISCLOSURE_LIMITED_DILUTION_ASSUMPTION_VALIDATION",
        "package_sha256": expected_sha,
        "eligible_for_assumption_aware_successor": True,
        "fully_diluted_shares_assumption": package["value"],
        "relative_upper_spread": package["range"]["relative_upper_spread"],
    }

