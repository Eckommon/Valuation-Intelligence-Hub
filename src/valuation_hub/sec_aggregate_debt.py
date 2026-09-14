"""Reviewed exact SEC aggregate-debt profile for real U.S. equity cases.

Historical M19 component semantics remain untouched. This successor path accepts
only the exact SEC CompanyFacts concept `us-gaap:DebtLongtermAndShorttermCombinedAmount`,
preserves the captured M13 snapshot lineage, and requires an explicit human semantic
review before the as-reported amount may feed a DERIVED_FACT debt binding context.

The human review is intentionally stronger than a numeric approval: because the
historical project debt boundary excludes lease liabilities, the reviewer must
explicitly establish from the issuer filing that the selected aggregate is suitable
for that boundary. The AI must never infer this approval.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import date, datetime
from math import isfinite
from typing import Any

from valuation_hub import sec_live
from valuation_hub.case_service import CaseServiceError

CANDIDATE_SCHEMA = "sec-aggregate-debt-candidate-v0.1"
OBSERVATION_SCHEMA = "sec-aggregate-debt-observation-v0.1"
REVIEW_ASSERTION_SCHEMA = "sec-aggregate-debt-review-assertion-v0.1"
REVIEWED_PROFILE_SCHEMA = "reviewed-sec-aggregate-debt-profile-v0.1"
CONTEXT_SCHEMA = "debt-binding-context-v0.2-sec-aggregate"
CANDIDATE_STATUS = "SEC_AGGREGATE_DEBT_CANDIDATE"
OBSERVATION_STATUS = "SEC_AGGREGATE_DEBT_NORMALIZED"
REVIEW_STATUS = "SEC_AGGREGATE_DEBT_REVIEW_APPROVED"
PROFILE_STATUS = "SEC_AGGREGATE_DEBT_REVIEWED"
CONTEXT_STATUS = "DEBT_BINDING_CONTEXT_EVALUATED"
METRIC = "interest_bearing_debt_as_reported"
TARGET_METRIC = "interest_bearing_debt"
SEC_CONCEPT = ("us-gaap", "DebtLongtermAndShorttermCombinedAmount")
SEC_FORMS = frozenset({"10-Q", "10-Q/A", "10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A"})
SEMANTIC_DECISION = "EXPLICIT_FILING_RECONCILIATION_EXCLUDES_LEASE_LIABILITIES"
CONTEXT_POLICY = "DEBT_BINDING_CONTEXT_V02_SEC_AGGREGATE"
FRESH = "FRESH"
STALE_BLOCKED = "STALE_BLOCKED"
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    out = copy.deepcopy(value)
    out.pop(key, None)
    return out


def _number(value: Any, field: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)) or value < 0:
        raise CaseServiceError(f"{field} must be finite nonnegative numeric / {field} 유한 비음수 숫자 필요")
    return value


def _date(value: Any, field: str) -> date:
    if not isinstance(value, str):
        raise CaseServiceError(f"{field} YYYY-MM-DD required / {field} 날짜 필요")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise CaseServiceError(f"{field} invalid / {field} 날짜 오류") from exc
    if parsed.isoformat() != value:
        raise CaseServiceError(f"{field} canonical YYYY-MM-DD required / {field} 정규 날짜 형식 필요")
    return parsed


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise CaseServiceError(f"{field} timezone-aware timestamp required / {field} 시간대 포함 시각 필요")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CaseServiceError(f"{field} ISO timestamp invalid / {field} ISO 시각 오류") from exc
    if parsed.tzinfo is None:
        raise CaseServiceError(f"{field} timezone required / {field} 시간대 필요")
    return parsed


def _text(value: Any, field: str, limit: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise CaseServiceError(f"{field} required/too long / {field} 필요·길이 오류")
    return value.strip()


def _scope_payload(observation: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": observation.get("schema_version"),
        "status": observation.get("status"),
        "canonical": observation.get("canonical"),
        "class": observation.get("class"),
        "metric": observation.get("metric"),
        "value": observation.get("value"),
        "unit": observation.get("unit"),
        "entity": observation.get("entity"),
        "period": observation.get("period"),
        "filing": observation.get("filing"),
        "source_identity": observation.get("source_identity"),
        "source": observation.get("source"),
        "source_candidate_sha256": observation.get("source_candidate_sha256"),
        "observation_sha256": observation.get("observation_sha256"),
    }


def review_scope_sha256(observation: dict[str, Any]) -> str:
    validate_sec_aggregate_debt_observation(observation)
    return _sha(_scope_payload(observation))


def extract_sec_aggregate_debt_candidate(
    snapshot: dict[str, Any], *, form: str | None = None, period_end: str | None = None
) -> dict[str, Any]:
    """Extract the exact aggregate-debt SEC instant fact; no fallback concepts."""
    checked = sec_live.validate_source_snapshot(snapshot)
    requested_form = form.upper() if form else None
    if requested_form is not None and requested_form not in SEC_FORMS:
        raise CaseServiceError("SEC form not allowed for aggregate debt / aggregate debt SEC form 오류")
    requested_end = _date(period_end, "period_end").isoformat() if period_end else None
    try:
        payload = json.loads(snapshot["raw_text"])
    except (KeyError, json.JSONDecodeError, TypeError) as exc:
        raise CaseServiceError("SEC aggregate-debt snapshot payload invalid / SEC aggregate debt snapshot 오류") from exc
    facts = payload.get("facts")
    taxonomy, concept = SEC_CONCEPT
    taxonomy_obj = facts.get(taxonomy) if isinstance(facts, dict) else None
    concept_obj = taxonomy_obj.get(concept) if isinstance(taxonomy_obj, dict) else None
    units = concept_obj.get("units") if isinstance(concept_obj, dict) else None
    series = units.get("USD") if isinstance(units, dict) else None
    if not isinstance(series, list):
        raise CaseServiceError("exact SEC aggregate-debt concept unavailable / 정확한 SEC aggregate debt concept 없음")
    candidates: list[dict[str, Any]] = []
    for raw in series:
        if not isinstance(raw, dict) or raw.get("form") not in SEC_FORMS:
            continue
        if requested_form and raw.get("form") != requested_form:
            continue
        if raw.get("start") not in (None, ""):
            continue
        try:
            end = _date(raw.get("end"), "SEC aggregate debt end").isoformat()
            filed = _date(raw.get("filed"), "SEC aggregate debt filed").isoformat()
        except CaseServiceError:
            continue
        if requested_end and end != requested_end:
            continue
        accn = raw.get("accn")
        if not isinstance(accn, str) or not sec_live.ACCESSION_RE.fullmatch(accn) or "val" not in raw:
            continue
        _number(raw["val"], "SEC aggregate debt")
        item = copy.deepcopy(raw)
        item["end"], item["filed"] = end, filed
        candidates.append(item)
    if not candidates:
        raise CaseServiceError("no exact SEC aggregate-debt fact matches filters / 정확한 SEC aggregate debt fact 없음")
    latest_filed = max(item["filed"] for item in candidates)
    top = [item for item in candidates if item["filed"] == latest_filed]
    latest_end = max(item["end"] for item in top)
    top = [item for item in top if item["end"] == latest_end]
    distinct = {json.dumps(item["val"], sort_keys=True, allow_nan=False) for item in top}
    if len(distinct) != 1:
        raise CaseServiceError("equal-precedence SEC aggregate-debt facts conflict / 동일 우선순위 SEC aggregate debt fact 충돌")
    chosen = sorted(top, key=lambda item: (str(item.get("accn", "")), str(item.get("form", "")), str(item.get("frame", ""))), reverse=True)[0]
    candidate = {
        "schema_version": CANDIDATE_SCHEMA,
        "status": CANDIDATE_STATUS,
        "canonical": False,
        "class": "FACT_CANDIDATE",
        "metric": METRIC,
        "value": chosen["val"],
        "unit": "USD",
        "entity": {"id": f"SEC_CIK:{checked['cik']}", "financial_scope": "CFS"},
        "period": {"kind": "INSTANT", "start": None, "end": chosen["end"], "date_precision": "EXACT"},
        "filing": {"accession": chosen["accn"], "form": chosen["form"], "filed": chosen["filed"]},
        "source_identity": {"taxonomy": taxonomy, "concept": concept},
        "source": {
            "publisher": sec_live.SEC_PUBLISHER,
            "source_type": sec_live.SEC_SOURCE_TYPE,
            "tier": sec_live.SEC_TIER,
            "locator": snapshot["source"]["final_locator"],
            "snapshot_sha256": snapshot["snapshot_sha256"],
            "body_sha256": snapshot["response"]["body_sha256"],
        },
        "selection": {"rule": "EXACT_SEC_AGGREGATE_DEBT_THEN_LATEST_FILED_THEN_LATEST_END", "equal_precedence_count": len(top)},
        "candidate_sha256": "",
    }
    candidate["candidate_sha256"] = _sha(_without(candidate, "candidate_sha256"))
    validate_sec_aggregate_debt_candidate(candidate)
    return candidate


def validate_sec_aggregate_debt_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(candidate, dict) or candidate.get("schema_version") != CANDIDATE_SCHEMA or candidate.get("status") != CANDIDATE_STATUS:
        raise CaseServiceError("SEC aggregate-debt candidate schema/status invalid / SEC aggregate debt candidate 스키마·상태 오류")
    if candidate.get("canonical") is not False or candidate.get("class") != "FACT_CANDIDATE" or candidate.get("metric") != METRIC:
        raise CaseServiceError("SEC aggregate-debt candidate authority invalid / SEC aggregate debt candidate 권위 오류")
    _number(candidate.get("value"), "aggregate debt value")
    if candidate.get("unit") != "USD":
        raise CaseServiceError("SEC aggregate debt unit must be USD / SEC aggregate debt 단위는 USD 필요")
    entity, period, filing, identity, source = (candidate.get("entity"), candidate.get("period"), candidate.get("filing"), candidate.get("source_identity"), candidate.get("source"))
    if not all(isinstance(item, dict) for item in (entity, period, filing, identity, source)):
        raise CaseServiceError("SEC aggregate-debt candidate structure incomplete / SEC aggregate debt candidate 구조 불완전")
    if not str(entity.get("id", "")).startswith("SEC_CIK:") or entity.get("financial_scope") != "CFS":
        raise CaseServiceError("SEC aggregate-debt entity/scope invalid / SEC aggregate debt entity·scope 오류")
    if period != {"kind": "INSTANT", "start": None, "end": period.get("end"), "date_precision": "EXACT"}:
        raise CaseServiceError("SEC aggregate debt must be exact instant / SEC aggregate debt는 exact instant 필요")
    _date(period.get("end"), "period.end")
    if identity != {"taxonomy": SEC_CONCEPT[0], "concept": SEC_CONCEPT[1]}:
        raise CaseServiceError("SEC aggregate-debt exact concept identity invalid / SEC aggregate debt exact concept 식별 오류")
    if filing.get("form") not in SEC_FORMS or not isinstance(filing.get("accession"), str) or not sec_live.ACCESSION_RE.fullmatch(filing["accession"]):
        raise CaseServiceError("SEC aggregate-debt filing identity invalid / SEC aggregate debt filing 식별 오류")
    _date(filing.get("filed"), "filing.filed")
    if source.get("tier") != "A":
        raise CaseServiceError("SEC aggregate debt source must be Tier A / SEC aggregate debt는 Tier A 출처 필요")
    for key in ("snapshot_sha256", "body_sha256"):
        if not isinstance(source.get(key), str) or not SHA_RE.fullmatch(source[key]):
            raise CaseServiceError("SEC aggregate-debt source SHA invalid / SEC aggregate debt source SHA 오류")
    expected = _sha(_without(candidate, "candidate_sha256"))
    if candidate.get("candidate_sha256") != expected:
        raise CaseServiceError("SEC aggregate-debt candidate SHA mismatch / SEC aggregate debt candidate SHA 불일치")
    return {"status": "PASS_SEC_AGGREGATE_DEBT_CANDIDATE_VALIDATION", "candidate_sha256": expected}


def normalize_sec_aggregate_debt_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    validate_sec_aggregate_debt_candidate(candidate)
    observation = {
        "schema_version": OBSERVATION_SCHEMA,
        "status": OBSERVATION_STATUS,
        "canonical": False,
        "class": "NORMALIZED_FACT_CANDIDATE",
        "metric": METRIC,
        "value": candidate["value"],
        "unit": candidate["unit"],
        "entity": copy.deepcopy(candidate["entity"]),
        "period": copy.deepcopy(candidate["period"]),
        "filing": copy.deepcopy(candidate["filing"]),
        "source_identity": copy.deepcopy(candidate["source_identity"]),
        "source": copy.deepcopy(candidate["source"]),
        "source_candidate_sha256": candidate["candidate_sha256"],
        "candidate": copy.deepcopy(candidate),
        "observation_sha256": "",
    }
    observation["observation_sha256"] = _sha(_without(observation, "observation_sha256"))
    validate_sec_aggregate_debt_observation(observation)
    return observation


def validate_sec_aggregate_debt_observation(observation: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(observation, dict) or observation.get("schema_version") != OBSERVATION_SCHEMA or observation.get("status") != OBSERVATION_STATUS:
        raise CaseServiceError("SEC aggregate-debt observation schema/status invalid / SEC aggregate debt observation 스키마·상태 오류")
    if observation.get("canonical") is not False or observation.get("class") != "NORMALIZED_FACT_CANDIDATE" or observation.get("metric") != METRIC:
        raise CaseServiceError("SEC aggregate-debt observation authority invalid / SEC aggregate debt observation 권위 오류")
    candidate = observation.get("candidate")
    if not isinstance(candidate, dict):
        raise CaseServiceError("SEC aggregate-debt source candidate missing / SEC aggregate debt source candidate 누락")
    validate_sec_aggregate_debt_candidate(candidate)
    for key in ("value", "unit", "entity", "period", "filing", "source_identity", "source"):
        if observation.get(key) != candidate.get(key):
            raise CaseServiceError("SEC aggregate-debt normalization drift / SEC aggregate debt 정규화 drift")
    if observation.get("source_candidate_sha256") != candidate.get("candidate_sha256"):
        raise CaseServiceError("SEC aggregate-debt candidate lineage mismatch / SEC aggregate debt candidate lineage 불일치")
    expected = _sha(_without(observation, "observation_sha256"))
    if observation.get("observation_sha256") != expected:
        raise CaseServiceError("SEC aggregate-debt observation SHA mismatch / SEC aggregate debt observation SHA 불일치")
    return {"status": "PASS_SEC_AGGREGATE_DEBT_OBSERVATION_VALIDATION", "observation_sha256": expected}


def build_sec_aggregate_debt_review_assertion(
    observation: dict[str, Any], *, reviewer: str, reviewed_at: str, review_basis: str, source_basis_locator: str,
    semantic_scope_decision: str
) -> dict[str, Any]:
    validate_sec_aggregate_debt_observation(observation)
    reviewer_value = _text(reviewer, "reviewer", 160)
    basis = _text(review_basis, "review_basis", 2000)
    locator = _text(source_basis_locator, "source_basis_locator", 2000)
    reviewed = _timestamp(reviewed_at, "reviewed_at")
    if semantic_scope_decision != SEMANTIC_DECISION:
        raise CaseServiceError("explicit filing reconciliation excluding lease liabilities required / lease liabilities 제외를 확인한 명시적 filing 조정 검토 필요")
    if _date(observation["period"]["end"], "period.end") > reviewed.date():
        raise CaseServiceError("review cannot precede source period end / source 기간말 이전 검토 불가")
    assertion = {
        "schema_version": REVIEW_ASSERTION_SCHEMA,
        "status": REVIEW_STATUS,
        "canonical": False,
        "decision": "APPROVE",
        "reviewer": reviewer_value,
        "reviewed_at": reviewed.isoformat(),
        "review_basis": basis,
        "source_basis_locator": locator,
        "semantic_scope_decision": semantic_scope_decision,
        "scope_sha256": review_scope_sha256(observation),
        "source_observation_sha256": observation["observation_sha256"],
        "source_filing_accession": observation["filing"]["accession"],
        "assertion_sha256": "",
    }
    assertion["assertion_sha256"] = _sha(_without(assertion, "assertion_sha256"))
    validate_sec_aggregate_debt_review_assertion(assertion, observation)
    return assertion


def validate_sec_aggregate_debt_review_assertion(assertion: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    validate_sec_aggregate_debt_observation(observation)
    if not isinstance(assertion, dict) or assertion.get("schema_version") != REVIEW_ASSERTION_SCHEMA or assertion.get("status") != REVIEW_STATUS:
        raise CaseServiceError("SEC aggregate-debt review schema/status invalid / SEC aggregate debt review 스키마·상태 오류")
    if assertion.get("canonical") is not False or assertion.get("decision") != "APPROVE":
        raise CaseServiceError("SEC aggregate-debt review authority/decision invalid / SEC aggregate debt review 권위·결정 오류")
    _text(assertion.get("reviewer"), "reviewer", 160)
    _text(assertion.get("review_basis"), "review_basis", 2000)
    _text(assertion.get("source_basis_locator"), "source_basis_locator", 2000)
    _timestamp(assertion.get("reviewed_at"), "reviewed_at")
    if assertion.get("semantic_scope_decision") != SEMANTIC_DECISION:
        raise CaseServiceError("SEC aggregate-debt semantic scope not approved / SEC aggregate debt 의미범위 미승인")
    if assertion.get("scope_sha256") != review_scope_sha256(observation) or assertion.get("source_observation_sha256") != observation.get("observation_sha256"):
        raise CaseServiceError("SEC aggregate-debt review scope/observation SHA mismatch / SEC aggregate debt 검토 scope·observation SHA 불일치")
    if assertion.get("source_filing_accession") != observation.get("filing", {}).get("accession"):
        raise CaseServiceError("SEC aggregate-debt review filing mismatch / SEC aggregate debt 검토 filing 불일치")
    expected = _sha(_without(assertion, "assertion_sha256"))
    if assertion.get("assertion_sha256") != expected:
        raise CaseServiceError("SEC aggregate-debt review assertion SHA mismatch / SEC aggregate debt 검토 assertion SHA 불일치")
    return {"status": "PASS_SEC_AGGREGATE_DEBT_REVIEW_VALIDATION", "assertion_sha256": expected}


def finalize_reviewed_sec_aggregate_debt(
    observation: dict[str, Any], assertion: dict[str, Any]
) -> dict[str, Any]:
    validate_sec_aggregate_debt_observation(observation)
    validate_sec_aggregate_debt_review_assertion(assertion, observation)
    profile = {
        "schema_version": REVIEWED_PROFILE_SCHEMA,
        "status": PROFILE_STATUS,
        "canonical": False,
        "class": "NORMALIZED_FACT",
        "metric": METRIC,
        "value": observation["value"],
        "unit": observation["unit"],
        "entity": copy.deepcopy(observation["entity"]),
        "period": copy.deepcopy(observation["period"]),
        "filing": copy.deepcopy(observation["filing"]),
        "source_identity": copy.deepcopy(observation["source_identity"]),
        "source": copy.deepcopy(observation["source"]),
        "semantic_boundary": {
            "total_liabilities_used": False,
            "missing_as_zero": False,
            "lease_liabilities_included": False,
            "basis": SEMANTIC_DECISION,
        },
        "observation": copy.deepcopy(observation),
        "review_assertion": copy.deepcopy(assertion),
        "source_observation_sha256": observation["observation_sha256"],
        "review_assertion_sha256": assertion["assertion_sha256"],
        "binding_eligibility": {"eligible": True, "reason": "HUMAN_REVIEWED_EXACT_SEC_AGGREGATE_DEBT"},
        "profile_sha256": "",
    }
    profile["profile_sha256"] = _sha(_without(profile, "profile_sha256"))
    validate_reviewed_sec_aggregate_debt(profile)
    return profile


def validate_reviewed_sec_aggregate_debt(profile: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(profile, dict) or profile.get("schema_version") != REVIEWED_PROFILE_SCHEMA or profile.get("status") != PROFILE_STATUS:
        raise CaseServiceError("reviewed SEC aggregate-debt profile schema/status invalid / 검토 SEC aggregate debt profile 스키마·상태 오류")
    if profile.get("canonical") is not False or profile.get("class") != "NORMALIZED_FACT" or profile.get("metric") != METRIC:
        raise CaseServiceError("reviewed SEC aggregate-debt authority invalid / 검토 SEC aggregate debt 권위 오류")
    observation, assertion = profile.get("observation"), profile.get("review_assertion")
    if not isinstance(observation, dict) or not isinstance(assertion, dict):
        raise CaseServiceError("reviewed SEC aggregate-debt lineage missing / 검토 SEC aggregate debt lineage 누락")
    validate_sec_aggregate_debt_observation(observation)
    validate_sec_aggregate_debt_review_assertion(assertion, observation)
    for key in ("value", "unit", "entity", "period", "filing", "source_identity", "source"):
        if profile.get(key) != observation.get(key):
            raise CaseServiceError("reviewed SEC aggregate-debt projection drift / 검토 SEC aggregate debt 투영 drift")
    if profile.get("source_observation_sha256") != observation.get("observation_sha256") or profile.get("review_assertion_sha256") != assertion.get("assertion_sha256"):
        raise CaseServiceError("reviewed SEC aggregate-debt lineage SHA mismatch / 검토 SEC aggregate debt lineage SHA 불일치")
    boundary = profile.get("semantic_boundary")
    if boundary != {"total_liabilities_used": False, "missing_as_zero": False, "lease_liabilities_included": False, "basis": SEMANTIC_DECISION}:
        raise CaseServiceError("reviewed SEC aggregate-debt semantic boundary invalid / 검토 SEC aggregate debt 의미경계 오류")
    if profile.get("binding_eligibility") != {"eligible": True, "reason": "HUMAN_REVIEWED_EXACT_SEC_AGGREGATE_DEBT"}:
        raise CaseServiceError("reviewed SEC aggregate-debt eligibility invalid / 검토 SEC aggregate debt 적격성 오류")
    expected = _sha(_without(profile, "profile_sha256"))
    if profile.get("profile_sha256") != expected:
        raise CaseServiceError("reviewed SEC aggregate-debt profile SHA mismatch / 검토 SEC aggregate debt profile SHA 불일치")
    return {"status": "PASS_REVIEWED_SEC_AGGREGATE_DEBT_VALIDATION", "eligible": True, "profile_sha256": expected}


def _freshness(period_end: str, as_of: str, max_age_days: int) -> dict[str, Any]:
    if isinstance(max_age_days, bool) or not isinstance(max_age_days, int) or not 0 <= max_age_days <= 3650:
        raise CaseServiceError("aggregate-debt max_age_days out of range / aggregate debt max_age_days 범위 오류")
    age = (_date(as_of, "as_of") - _date(period_end, "period_end")).days
    if age < 0:
        raise CaseServiceError("aggregate-debt period end after as_of / aggregate debt 기간말이 as_of 이후")
    return {"status": FRESH if age <= max_age_days else STALE_BLOCKED, "age_days": age, "max_age_days": max_age_days}


def build_sec_aggregate_debt_binding_context(
    profile: dict[str, Any], *, as_of: str, max_age_days: int = 550
) -> dict[str, Any]:
    validate_reviewed_sec_aggregate_debt(profile)
    period_end = profile["period"]["end"]
    freshness = _freshness(period_end, as_of, max_age_days)
    eligible = freshness["status"] == FRESH
    context = {
        "schema_version": CONTEXT_SCHEMA,
        "status": CONTEXT_STATUS,
        "canonical": False,
        "class": "DERIVED_FACT",
        "metric": TARGET_METRIC,
        "value": profile["value"],
        "unit": profile["unit"],
        "entity": copy.deepcopy(profile["entity"]),
        "source_period": copy.deepcopy(profile["period"]),
        "resolved_period_end": period_end,
        "date_resolution": {"method": "SOURCE_EXACT", "date_assertion_sha256": None},
        "policy": {"version": CONTEXT_POLICY, "as_of": as_of, "max_age_days": max_age_days},
        "freshness": freshness,
        "binding_eligibility": {"eligible": eligible, "reason": "REVIEWED_SEC_AGGREGATE_PROFILE_FRESH" if eligible else "STALE_DEBT"},
        "source_debt_sha256": profile["profile_sha256"],
        "source_debt_profile_sha256": profile["profile_sha256"],
        "review_assertion_sha256": profile["review_assertion_sha256"],
        "semantic_boundary": copy.deepcopy(profile["semantic_boundary"]),
        "reviewed_profile": copy.deepcopy(profile),
        "context_sha256": "",
    }
    context["context_sha256"] = _sha(_without(context, "context_sha256"))
    validate_sec_aggregate_debt_binding_context(context)
    return context


def validate_sec_aggregate_debt_binding_context(context: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(context, dict) or context.get("schema_version") != CONTEXT_SCHEMA or context.get("status") != CONTEXT_STATUS:
        raise CaseServiceError("SEC aggregate debt context schema/status invalid / SEC aggregate debt context 스키마·상태 오류")
    if context.get("canonical") is not False or context.get("class") != "DERIVED_FACT" or context.get("metric") != TARGET_METRIC:
        raise CaseServiceError("SEC aggregate debt context authority/metric invalid / SEC aggregate debt context 권위·metric 오류")
    profile = context.get("reviewed_profile")
    if not isinstance(profile, dict):
        raise CaseServiceError("SEC aggregate debt reviewed profile missing / SEC aggregate debt reviewed profile 누락")
    validate_reviewed_sec_aggregate_debt(profile)
    if context.get("value") != profile.get("value") or context.get("unit") != profile.get("unit") or context.get("entity") != profile.get("entity") or context.get("source_period") != profile.get("period"):
        raise CaseServiceError("SEC aggregate debt context/profile projection mismatch / SEC aggregate debt context·profile 투영 불일치")
    if context.get("source_debt_sha256") != profile.get("profile_sha256") or context.get("source_debt_profile_sha256") != profile.get("profile_sha256") or context.get("review_assertion_sha256") != profile.get("review_assertion_sha256"):
        raise CaseServiceError("SEC aggregate debt context/profile lineage mismatch / SEC aggregate debt context·profile lineage 불일치")
    period_end = profile["period"]["end"]
    if context.get("resolved_period_end") != period_end or context.get("date_resolution") != {"method": "SOURCE_EXACT", "date_assertion_sha256": None}:
        raise CaseServiceError("SEC aggregate debt date projection invalid / SEC aggregate debt 날짜 투영 오류")
    policy = context.get("policy")
    if not isinstance(policy, dict) or policy.get("version") != CONTEXT_POLICY:
        raise CaseServiceError("SEC aggregate debt context policy invalid / SEC aggregate debt context 정책 오류")
    expected_freshness = _freshness(period_end, policy.get("as_of"), policy.get("max_age_days"))
    if context.get("freshness") != expected_freshness:
        raise CaseServiceError("SEC aggregate debt freshness mismatch / SEC aggregate debt 최신성 불일치")
    eligible = expected_freshness["status"] == FRESH
    expected_eligibility = {"eligible": eligible, "reason": "REVIEWED_SEC_AGGREGATE_PROFILE_FRESH" if eligible else "STALE_DEBT"}
    if context.get("binding_eligibility") != expected_eligibility:
        raise CaseServiceError("SEC aggregate debt eligibility mismatch / SEC aggregate debt 적격성 불일치")
    if context.get("semantic_boundary") != profile.get("semantic_boundary"):
        raise CaseServiceError("SEC aggregate debt semantic boundary drift / SEC aggregate debt 의미경계 drift")
    expected = _sha(_without(context, "context_sha256"))
    if context.get("context_sha256") != expected:
        raise CaseServiceError("SEC aggregate debt context SHA mismatch / SEC aggregate debt context SHA 불일치")
    return {"status": "PASS_SEC_AGGREGATE_DEBT_CONTEXT_VALIDATION", "eligible": eligible, "context_sha256": expected}
