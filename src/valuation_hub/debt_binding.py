"""M20 debt date assertion + binding-ready context / 이자부채 날짜승인 + 바인딩 context.

M20 never invents an exact date for REPORT_STAGE_ONLY debt. A human assertion may
resolve that date, but it is SHA-locked to the exact M19 debt evidence and remains
noncanonical. Only complete reviewed fresh debt becomes binding-eligible.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import date, datetime
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.debt_components import COMPLETE, DEBT_SCHEMA_VERSION, validate_interest_bearing_debt_evidence

DATE_ASSERTION_SCHEMA = "debt-date-assertion-v0.1"
DATE_ASSERTION_STATUS = "DEBT_DATE_ASSERTED"
CONTEXT_SCHEMA = "debt-binding-context-v0.1"
CONTEXT_STATUS = "DEBT_BINDING_CONTEXT_EVALUATED"
CONTEXT_POLICY = "DEBT_BINDING_CONTEXT_V01"
FRESH = "FRESH"
STALE_BLOCKED = "STALE_BLOCKED"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    out = copy.deepcopy(value); out.pop(key, None); return out


def _parse_date(value: Any, field: str) -> date:
    if not isinstance(value, str):
        raise CaseServiceError(f"{field} YYYY-MM-DD required / {field} 날짜 필요")
    try: parsed = date.fromisoformat(value)
    except ValueError as exc: raise CaseServiceError(f"{field} invalid / {field} 날짜 오류") from exc
    if parsed.isoformat() != value:
        raise CaseServiceError(f"{field} canonical YYYY-MM-DD required / {field} 정규 날짜 형식 필요")
    return parsed


def _parse_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise CaseServiceError(f"{field} timezone-aware timestamp required / {field} 시간대 포함 시각 필요")
    try: parsed = datetime.fromisoformat(value)
    except ValueError as exc: raise CaseServiceError(f"{field} ISO timestamp invalid / {field} ISO 시각 오류") from exc
    if parsed.tzinfo is None:
        raise CaseServiceError(f"{field} timezone required / {field} 시간대 필요")
    return parsed


def _max_age(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 3650:
        raise CaseServiceError("max_age_days out of range / max_age_days 범위 오류")
    return value


def _period_identity(debt: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(debt["period"])


def build_debt_date_assertion(debt: dict[str, Any], *, reviewer: str, approved_at: str, asserted_period_end: str, review_basis: str) -> dict[str, Any]:
    validate_interest_bearing_debt_evidence(debt)
    period = debt["period"]
    if period.get("date_precision") != "REPORT_STAGE_ONLY" or period.get("end") is not None:
        raise CaseServiceError("date assertion is only for unresolved REPORT_STAGE_ONLY debt / 날짜승인은 미해결 REPORT_STAGE_ONLY debt 전용")
    if not isinstance(reviewer, str) or not reviewer.strip() or len(reviewer.strip()) > 160:
        raise CaseServiceError("reviewer required / reviewer 필요")
    if not isinstance(review_basis, str) or not review_basis.strip() or len(review_basis.strip()) > 1000:
        raise CaseServiceError("review_basis required / 날짜승인 근거 필요")
    approved = _parse_timestamp(approved_at, "approved_at")
    asserted = _parse_date(asserted_period_end, "asserted_period_end")
    if asserted > approved.date():
        raise CaseServiceError("asserted period end cannot be after approval date / 승인일 이후 기간말 주장 불가")
    assertion = {
        "schema_version": DATE_ASSERTION_SCHEMA, "status": DATE_ASSERTION_STATUS, "canonical": False,
        "reviewer": reviewer.strip(), "approved_at": approved.isoformat(), "source_debt_sha256": debt["debt_sha256"],
        "target_identity": copy.deepcopy(debt["entity"]), "source_period_identity": _period_identity(debt),
        "asserted_period_end": asserted.isoformat(), "review_basis": review_basis.strip(), "assertion_sha256": "",
    }
    assertion["assertion_sha256"] = _sha(_without(assertion, "assertion_sha256"))
    validate_debt_date_assertion(assertion, debt)
    return assertion


def validate_debt_date_assertion(assertion: dict[str, Any], debt: dict[str, Any]) -> dict[str, Any]:
    validate_interest_bearing_debt_evidence(debt)
    if not isinstance(assertion, dict) or assertion.get("schema_version") != DATE_ASSERTION_SCHEMA or assertion.get("status") != DATE_ASSERTION_STATUS:
        raise CaseServiceError("debt date assertion schema/status invalid / debt 날짜승인 스키마·상태 오류")
    if assertion.get("canonical") is not False:
        raise CaseServiceError("debt date assertion must remain noncanonical / debt 날짜승인은 비정식이어야 함")
    period = debt["period"]
    if period.get("date_precision") != "REPORT_STAGE_ONLY" or period.get("end") is not None:
        raise CaseServiceError("source debt does not require date assertion / source debt는 날짜승인 대상이 아님")
    if assertion.get("source_debt_sha256") != debt.get("debt_sha256"):
        raise CaseServiceError("date assertion debt SHA mismatch / 날짜승인 debt SHA 불일치")
    if assertion.get("target_identity") != debt.get("entity") or assertion.get("source_period_identity") != period:
        raise CaseServiceError("date assertion identity/period mismatch / 날짜승인 식별·기간 불일치")
    reviewer, basis = assertion.get("reviewer"), assertion.get("review_basis")
    if not isinstance(reviewer, str) or not reviewer.strip() or len(reviewer) > 160:
        raise CaseServiceError("date assertion reviewer invalid / 날짜승인 reviewer 오류")
    if not isinstance(basis, str) or not basis.strip() or len(basis) > 1000:
        raise CaseServiceError("date assertion review basis invalid / 날짜승인 근거 오류")
    approved = _parse_timestamp(assertion.get("approved_at"), "approved_at")
    asserted = _parse_date(assertion.get("asserted_period_end"), "asserted_period_end")
    if asserted > approved.date():
        raise CaseServiceError("asserted period end after approval date / 승인일 이후 기간말 주장")
    expected = _sha(_without(assertion, "assertion_sha256"))
    if assertion.get("assertion_sha256") != expected:
        raise CaseServiceError("debt date assertion SHA-256 mismatch / debt 날짜승인 SHA-256 불일치")
    return {"status": "PASS_DEBT_DATE_ASSERTION_VALIDATION", "canonical": False, "assertion_sha256": expected, "asserted_period_end": asserted.isoformat()}


def _resolve_period_end(debt: dict[str, Any], assertion: dict[str, Any] | None) -> tuple[str, dict[str, Any]]:
    period = debt["period"]; precision, end = period.get("date_precision"), period.get("end")
    if precision == "EXACT" and isinstance(end, str):
        _parse_date(end, "debt period.end")
        if assertion is not None:
            raise CaseServiceError("EXACT debt must not be overridden by date assertion / EXACT debt 날짜는 승인으로 덮어쓸 수 없음")
        return end, {"method": "SOURCE_EXACT", "date_assertion_sha256": None}
    if precision == "REPORT_STAGE_ONLY" and end is None:
        if assertion is None:
            raise CaseServiceError("REPORT_STAGE_ONLY debt requires human date assertion / REPORT_STAGE_ONLY debt는 인간 날짜승인 필요")
        validate_debt_date_assertion(assertion, debt)
        return assertion["asserted_period_end"], {"method": "HUMAN_DATE_ASSERTION", "date_assertion_sha256": assertion["assertion_sha256"]}
    raise CaseServiceError("unsupported debt date precision / 미지원 debt 날짜정밀도")


def _freshness(resolved_end: str, as_of: str, max_age_days: int) -> dict[str, Any]:
    end_date = _parse_date(resolved_end, "resolved_period_end")
    as_of_date = _parse_date(as_of, "as_of")
    max_age = _max_age(max_age_days)
    age = (as_of_date - end_date).days
    if age < 0:
        raise CaseServiceError("debt period end is after as_of / debt 기간말이 as_of 이후")
    return {"status": FRESH if age <= max_age else STALE_BLOCKED, "age_days": age, "max_age_days": max_age}


def build_debt_binding_context(debt: dict[str, Any], *, as_of: str, max_age_days: int = 550, date_assertion: dict[str, Any] | None = None) -> dict[str, Any]:
    validation = validate_interest_bearing_debt_evidence(debt)
    if debt.get("schema_version") != DEBT_SCHEMA_VERSION:
        raise CaseServiceError("M19 debt evidence required / M19 debt 근거 필요")
    if validation["coverage_status"] != COMPLETE or debt.get("class") != "DERIVED_FACT" or debt.get("semantic_boundary", {}).get("eligible_for_draft_direct_bind") is not True:
        raise CaseServiceError("only complete reviewed M19 debt can enter binding context / 완전·검토완료 M19 debt만 바인딩 context 가능")
    value = debt.get("interest_bearing_debt_value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise CaseServiceError("complete debt value invalid / 완전 debt 값 오류")
    _parse_date(as_of, "as_of"); _max_age(max_age_days)
    resolved_end, resolution = _resolve_period_end(debt, date_assertion)
    freshness = _freshness(resolved_end, as_of, max_age_days)
    eligible = freshness["status"] == FRESH
    context = {
        "schema_version": CONTEXT_SCHEMA, "status": CONTEXT_STATUS, "canonical": False, "class": "DERIVED_FACT",
        "metric": "interest_bearing_debt", "value": value, "unit": debt["unit"], "entity": copy.deepcopy(debt["entity"]),
        "source_period": copy.deepcopy(debt["period"]), "resolved_period_end": resolved_end, "date_resolution": resolution,
        "policy": {"version": CONTEXT_POLICY, "as_of": as_of, "max_age_days": max_age_days},
        "freshness": freshness,
        "binding_eligibility": {"eligible": eligible, "reason": "COMPLETE_REVIEWED_FRESH" if eligible else "STALE_DEBT"},
        "source_debt_sha256": debt["debt_sha256"], "context_sha256": "",
    }
    context["context_sha256"] = _sha(_without(context, "context_sha256"))
    validate_debt_binding_context(context, debt=debt, date_assertion=date_assertion)
    return context


def validate_debt_binding_context(context: dict[str, Any], *, debt: dict[str, Any] | None = None, date_assertion: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(context, dict) or context.get("schema_version") != CONTEXT_SCHEMA or context.get("status") != CONTEXT_STATUS:
        raise CaseServiceError("debt binding context schema/status invalid / debt 바인딩 context 스키마·상태 오류")
    if context.get("canonical") is not False or context.get("class") != "DERIVED_FACT" or context.get("metric") != "interest_bearing_debt":
        raise CaseServiceError("debt binding context authority/metric invalid / debt 바인딩 context 권위·metric 오류")
    if not isinstance(context.get("entity"), dict) or not isinstance(context.get("unit"), str) or not context["unit"]:
        raise CaseServiceError("debt binding context identity/unit invalid / debt 바인딩 context 식별·unit 오류")
    resolved_end = context.get("resolved_period_end"); _parse_date(resolved_end, "resolved_period_end")
    resolution, freshness, eligibility, policy = context.get("date_resolution"), context.get("freshness"), context.get("binding_eligibility"), context.get("policy")
    if not isinstance(resolution, dict) or resolution.get("method") not in {"SOURCE_EXACT", "HUMAN_DATE_ASSERTION"}:
        raise CaseServiceError("debt date resolution invalid / debt 날짜해결 방식 오류")
    if not isinstance(policy, dict) or policy.get("version") != CONTEXT_POLICY:
        raise CaseServiceError("debt binding context policy invalid / debt 바인딩 context 정책 오류")
    as_of = policy.get("as_of"); max_age = policy.get("max_age_days")
    _parse_date(as_of, "policy.as_of"); _max_age(max_age)
    expected_freshness = _freshness(resolved_end, as_of, max_age)
    if freshness != expected_freshness:
        raise CaseServiceError("debt freshness recomputation mismatch / debt 최신성 재계산 불일치")
    expected_eligible = expected_freshness["status"] == FRESH
    expected_reason = "COMPLETE_REVIEWED_FRESH" if expected_eligible else "STALE_DEBT"
    if eligibility != {"eligible": expected_eligible, "reason": expected_reason}:
        raise CaseServiceError("debt binding eligibility mismatch / debt 바인딩 적격성 불일치")
    source_sha = context.get("source_debt_sha256")
    if not isinstance(source_sha, str) or not SHA256_RE.fullmatch(source_sha):
        raise CaseServiceError("debt binding source SHA invalid / debt 바인딩 source SHA 오류")
    assertion_sha = resolution.get("date_assertion_sha256")
    if resolution["method"] == "SOURCE_EXACT":
        if assertion_sha is not None:
            raise CaseServiceError("SOURCE_EXACT cannot carry assertion SHA / SOURCE_EXACT assertion SHA 불가")
    elif not isinstance(assertion_sha, str) or not SHA256_RE.fullmatch(assertion_sha):
        raise CaseServiceError("HUMAN_DATE_ASSERTION requires assertion SHA / 인간 날짜승인 SHA 필요")
    if debt is not None:
        validation = validate_interest_bearing_debt_evidence(debt)
        if validation["coverage_status"] != COMPLETE or debt.get("class") != "DERIVED_FACT" or debt.get("semantic_boundary", {}).get("eligible_for_draft_direct_bind") is not True:
            raise CaseServiceError("context source debt no longer eligible / context source debt 적격성 상실")
        if source_sha != debt.get("debt_sha256") or context.get("entity") != debt.get("entity") or context.get("unit") != debt.get("unit") or context.get("source_period") != debt.get("period") or context.get("value") != debt.get("interest_bearing_debt_value"):
            raise CaseServiceError("debt binding context/source mismatch / debt 바인딩 context·source 불일치")
        expected_end, expected_resolution = _resolve_period_end(debt, date_assertion)
        if resolved_end != expected_end or resolution != expected_resolution:
            raise CaseServiceError("debt binding date resolution/source mismatch / debt 바인딩 날짜해결·source 불일치")
    expected = _sha(_without(context, "context_sha256"))
    if context.get("context_sha256") != expected:
        raise CaseServiceError("debt binding context SHA-256 mismatch / debt 바인딩 context SHA-256 불일치")
    return {"status": "PASS_DEBT_BINDING_CONTEXT_VALIDATION", "canonical": False, "context_sha256": expected, "eligible": expected_eligible, "freshness_status": expected_freshness["status"]}
