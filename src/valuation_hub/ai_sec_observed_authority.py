"""Evidence-first AI authority for SEC cash, current shares, and minority interest.

M30-R3 extends the M30-R2 human-on-exception governance pattern without weakening
historical review paths.  AI approval is allowed only when exact source lineage,
field-specific semantic criteria, and contradiction search all validate.  The
result remains noncanonical and never writes a Draft or registry.
"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import date, datetime
from typing import Any
from urllib.parse import urlparse

from valuation_hub.case_service import CaseServiceError
from valuation_hub.financial_normalization import normalize_sec_candidate, validate_financial_observation
from valuation_hub.minority_interest import (
    build_minority_interest_review_assertion,
    finalize_reviewed_minority_interest,
    normalize_minority_interest_candidate,
    validate_minority_interest_candidate,
    validate_minority_interest_observation,
    validate_reviewed_minority_interest,
)
from valuation_hub.valuation_shares import (
    normalize_current_common_shares_candidate,
    validate_current_common_shares_candidate,
    validate_current_common_shares_observation,
)

EVIDENCE_SCHEMA = "ai-sec-observed-field-evidence-v0.1"
EVIDENCE_STATUS = "AI_SEC_OBSERVED_FIELD_EVIDENCE_READY"
ADJUDICATION_SCHEMA = "ai-sec-observed-field-adjudication-v0.1"
ADJUDICATION_STATUS = "AI_SEC_OBSERVED_FIELD_ADJUDICATED"
ADJUDICATOR_TYPE = "AI"
ADJUDICATOR_ID = "AI_EVIDENCE_ADJUDICATOR_V01"
DECISION_APPROVE = "APPROVE"

FIELD_CASH = "cash"
FIELD_SHARES = "current_common_shares"
FIELD_NCI = "minority_interest"
FIELDS = (FIELD_CASH, FIELD_SHARES, FIELD_NCI)

POLICIES = {
    FIELD_CASH: "AUTO_APPROVE_SEC_CASH_V01",
    FIELD_SHARES: "AUTO_APPROVE_SEC_CURRENT_COMMON_SHARES_V01",
    FIELD_NCI: "AUTO_APPROVE_SEC_MINORITY_INTEREST_V01",
}

REQUIRED_CRITERIA = {
    FIELD_CASH: (
        "q1_exact_cash_concept",
        "q2_exact_instant_period_and_currency",
        "q3_candidate_observation_lineage_reproduces",
        "q4_unique_nonfallback_tier_a_source",
    ),
    FIELD_SHARES: (
        "q1_exact_dei_current_common_shares",
        "q2_exact_instant_positive_share_count",
        "q3_current_common_not_fully_diluted_boundary_preserved",
        "q4_candidate_observation_lineage_reproduces",
    ),
    FIELD_NCI: (
        "q1_exact_nonredeemable_nci_concept",
        "q2_exact_instant_consolidated_scope",
        "q3_value_explicitly_reported_not_missing_imputed",
        "q4_nci_semantic_boundary_preserved",
    ),
}


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    out = copy.deepcopy(value)
    out.pop(key, None)
    return out


def _text(value: Any, field: str, limit: int = 8000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise CaseServiceError(f"{field} required/too long / {field} 필요·길이 오류")
    return value.strip()


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


def _official_filing_locator(value: Any) -> str:
    locator = _text(value, "primary_filing_locator", 2000)
    parsed = urlparse(locator)
    if parsed.scheme != "https" or parsed.hostname != "www.sec.gov" or not parsed.path.startswith("/Archives/edgar/"):
        raise CaseServiceError("first-party SEC filing locator required / SEC 공식 filing locator 필요")
    return locator


def _candidate_hash(field: str, candidate: dict[str, Any]) -> str:
    if field == FIELD_CASH:
        return _sha(candidate)
    value = candidate.get("candidate_sha256")
    if not isinstance(value, str) or len(value) != 64:
        raise CaseServiceError("candidate SHA missing / candidate SHA 누락")
    return value


def _validate_pair(field: str, candidate: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    if field not in FIELDS:
        raise CaseServiceError("unsupported SEC observed field / 미지원 SEC 관측필드")

    if field == FIELD_CASH:
        if (
            candidate.get("schema_version") != "sec-evidence-candidate-v0.1"
            or candidate.get("status") != "EVIDENCE_CANDIDATE_UNREVIEWED"
            or candidate.get("canonical") is not False
            or candidate.get("class") != "FACT_CANDIDATE"
            or candidate.get("metric") != "cash"
            or candidate.get("taxonomy") != "us-gaap"
            or candidate.get("concept") != "CashAndCashEquivalentsAtCarryingValue"
            or candidate.get("concept_fallback_used") is not False
            or candidate.get("concept_fallback_index") != 0
        ):
            raise CaseServiceError("cash candidate exact-source semantics invalid / cash candidate 정확 출처의미 오류")
        selection = candidate.get("selection", {})
        source = candidate.get("source", {})
        if selection.get("equal_precedence_count") != 1 or source.get("tier_proposal") != "A":
            raise CaseServiceError("cash candidate requires unique Tier-A exact source / cash candidate 고유 Tier-A 근거 필요")
        rebuilt = normalize_sec_candidate(candidate)
        validate_financial_observation(observation)
        if observation.get("class") != "NORMALIZED_FACT_CANDIDATE" or rebuilt != observation:
            raise CaseServiceError("cash candidate-observation lineage mismatch / cash candidate-observation lineage 불일치")
        period = observation["period"]
        if period.get("kind") != "INSTANT" or period.get("date_precision") != "EXACT" or observation.get("unit") != "USD":
            raise CaseServiceError("cash observation must be exact USD instant / cash observation 정확 USD 시점값 필요")
        filing = candidate.get("filing", {})
        source_snapshot_sha = observation.get("lineage", {}).get("source_snapshot_sha256")
        filing_accession = filing.get("accession")

    elif field == FIELD_SHARES:
        validate_current_common_shares_candidate(candidate)
        validate_current_common_shares_observation(observation)
        rebuilt = normalize_current_common_shares_candidate(candidate)
        if observation.get("class") != "NORMALIZED_FACT_CANDIDATE" or rebuilt != observation:
            raise CaseServiceError("share candidate-observation lineage mismatch / share candidate-observation lineage 불일치")
        if candidate.get("selection", {}).get("equal_precedence_count") != 1 or candidate.get("source", {}).get("tier_proposal") != "A":
            raise CaseServiceError("shares require unique Tier-A exact source / 주식수 고유 Tier-A 근거 필요")
        boundary = {"current_common_shares_only": True, "fully_diluted_shares": False}
        if candidate.get("semantic_boundary") != boundary or observation.get("semantic_boundary") != boundary:
            raise CaseServiceError("current-share semantic boundary invalid / 현재주식수 의미경계 오류")
        if observation.get("value", 0) <= 0 or observation.get("period", {}).get("date_precision") != "EXACT":
            raise CaseServiceError("current shares require positive exact instant / 현재주식수 양수 정확시점 필요")
        filing = candidate.get("filing", {})
        source_snapshot_sha = observation.get("lineage", {}).get("source_snapshot_sha256")
        filing_accession = filing.get("accession")

    else:
        validate_minority_interest_candidate(candidate)
        validate_minority_interest_observation(observation)
        rebuilt = normalize_minority_interest_candidate(candidate)
        if rebuilt != observation:
            raise CaseServiceError("NCI candidate-observation lineage mismatch / NCI candidate-observation lineage 불일치")
        if candidate.get("selection", {}).get("equal_precedence_count") != 1 or candidate.get("source", {}).get("tier") != "A":
            raise CaseServiceError("NCI requires unique Tier-A exact source / NCI 고유 Tier-A 근거 필요")
        if candidate.get("source_identity", {}).get("taxonomy") != "us-gaap" or candidate.get("source_identity", {}).get("concept") != "NonredeemableNoncontrollingInterest":
            raise CaseServiceError("NCI exact SEC concept required / NCI 정확 SEC concept 필요")
        boundary = {
            "missing_is_zero": False,
            "redeemable_noncontrolling_interest_included": False,
            "derived_from_equity_difference": False,
        }
        if candidate.get("semantic_boundary") != boundary or observation.get("semantic_boundary") != boundary:
            raise CaseServiceError("NCI semantic boundary invalid / NCI 의미경계 오류")
        if observation.get("period", {}).get("date_precision") != "EXACT" or observation.get("entity", {}).get("financial_scope") != "CFS":
            raise CaseServiceError("NCI requires exact consolidated fact / NCI 정확 연결 fact 필요")
        filing_accession = candidate.get("source_identity", {}).get("accession")
        source_snapshot_sha = observation.get("source", {}).get("snapshot_sha256")

    if not isinstance(source_snapshot_sha, str) or len(source_snapshot_sha) != 64:
        raise CaseServiceError("source snapshot SHA missing / source snapshot SHA 누락")
    if not isinstance(filing_accession, str) or not filing_accession:
        raise CaseServiceError("filing accession missing / filing accession 누락")
    period_end = observation.get("period", {}).get("end")
    if not isinstance(period_end, str):
        raise CaseServiceError("exact source period end required / 정확 source 기간말 필요")
    try:
        date.fromisoformat(period_end)
    except ValueError as exc:
        raise CaseServiceError("source period end invalid / source 기간말 오류") from exc

    return {
        "source_candidate_sha256": _candidate_hash(field, candidate),
        "source_observation_sha256": observation["observation_sha256"],
        "source_snapshot_sha256": source_snapshot_sha,
        "source_filing_accession": filing_accession,
        "source_period_end": period_end,
    }


def build_ai_sec_observed_evidence(
    field: str,
    candidate: dict[str, Any],
    observation: dict[str, Any],
    *,
    primary_filing_locator: str,
    evidence_basis: str,
    contradiction_search_summary: str,
    material_contradictions: list[str] | None = None,
    criteria: dict[str, bool],
) -> dict[str, Any]:
    lineage = _validate_pair(field, candidate, observation)
    required = REQUIRED_CRITERIA[field]
    if not isinstance(criteria, dict) or set(criteria) != set(required) or not all(isinstance(criteria[k], bool) for k in required):
        raise CaseServiceError("exact field-specific AI criteria set required / 정확한 필드별 AI 기준 집합 필요")
    contradictions = [] if material_contradictions is None else material_contradictions
    if not isinstance(contradictions, list) or not all(isinstance(v, str) and v.strip() for v in contradictions):
        raise CaseServiceError("material contradictions must be string list / material contradiction 문자열 목록 필요")
    packet = {
        "schema_version": EVIDENCE_SCHEMA,
        "status": EVIDENCE_STATUS,
        "canonical": False,
        "field": field,
        "policy_id": POLICIES[field],
        **lineage,
        "primary_filing_locator": _official_filing_locator(primary_filing_locator),
        "criteria": {key: criteria[key] for key in required},
        "contradiction_search": {
            "performed": True,
            "summary": _text(contradiction_search_summary, "contradiction_search_summary", 4000),
            "material_contradictions": [v.strip() for v in contradictions],
        },
        "evidence_basis": _text(evidence_basis, "evidence_basis", 8000),
        "evidence_sha256": "",
    }
    packet["evidence_sha256"] = _sha(_without(packet, "evidence_sha256"))
    validate_ai_sec_observed_evidence(packet, candidate, observation)
    return packet


def validate_ai_sec_observed_evidence(
    packet: dict[str, Any], candidate: dict[str, Any], observation: dict[str, Any]
) -> dict[str, Any]:
    if not isinstance(packet, dict) or packet.get("schema_version") != EVIDENCE_SCHEMA or packet.get("status") != EVIDENCE_STATUS or packet.get("canonical") is not False:
        raise CaseServiceError("AI observed evidence schema/status invalid / AI 관측근거 스키마·상태 오류")
    field = packet.get("field")
    if field not in FIELDS or packet.get("policy_id") != POLICIES[field]:
        raise CaseServiceError("AI observed evidence field/policy invalid / AI 관측근거 필드·정책 오류")
    lineage = _validate_pair(field, candidate, observation)
    for key, value in lineage.items():
        if packet.get(key) != value:
            raise CaseServiceError("AI observed evidence lineage mismatch / AI 관측근거 lineage 불일치")
    _official_filing_locator(packet.get("primary_filing_locator"))
    _text(packet.get("evidence_basis"), "evidence_basis", 8000)
    required = REQUIRED_CRITERIA[field]
    criteria = packet.get("criteria")
    if not isinstance(criteria, dict) or set(criteria) != set(required) or not all(criteria.get(k) is True for k in required):
        raise CaseServiceError("AI observed evidence criteria not all satisfied / AI 관측근거 기준 미충족")
    contradiction = packet.get("contradiction_search")
    if not isinstance(contradiction, dict) or contradiction.get("performed") is not True:
        raise CaseServiceError("AI contradiction search required / AI 반증검색 필요")
    _text(contradiction.get("summary"), "contradiction_search.summary", 4000)
    conflicts = contradiction.get("material_contradictions")
    if not isinstance(conflicts, list):
        raise CaseServiceError("AI contradiction list invalid / AI 반증목록 오류")
    if conflicts:
        raise CaseServiceError("material contradiction requires HOLD/escalation / 중대한 반증은 HOLD·상향 필요")
    expected = _sha(_without(packet, "evidence_sha256"))
    if packet.get("evidence_sha256") != expected:
        raise CaseServiceError("AI observed evidence SHA mismatch / AI 관측근거 SHA 불일치")
    return {"status": "PASS_AI_SEC_OBSERVED_EVIDENCE_VALIDATION", "field": field, "evidence_sha256": expected}


def build_ai_sec_observed_adjudication(
    candidate: dict[str, Any], observation: dict[str, Any], evidence: dict[str, Any], *, adjudicated_at: str
) -> dict[str, Any]:
    checked = validate_ai_sec_observed_evidence(evidence, candidate, observation)
    ts = _timestamp(adjudicated_at, "adjudicated_at")
    source_end = date.fromisoformat(evidence["source_period_end"])
    if source_end > ts.date():
        raise CaseServiceError("AI adjudication cannot precede source period end / AI 판단은 source 기간말 이전 불가")
    field = checked["field"]
    result = {
        "schema_version": ADJUDICATION_SCHEMA,
        "status": ADJUDICATION_STATUS,
        "canonical": False,
        "decision": DECISION_APPROVE,
        "field": field,
        "adjudicator": {"type": ADJUDICATOR_TYPE, "id": ADJUDICATOR_ID},
        "policy_id": POLICIES[field],
        "adjudicated_at": ts.isoformat(),
        "source_candidate_sha256": evidence["source_candidate_sha256"],
        "source_observation_sha256": evidence["source_observation_sha256"],
        "source_snapshot_sha256": evidence["source_snapshot_sha256"],
        "source_filing_accession": evidence["source_filing_accession"],
        "evidence_sha256": evidence["evidence_sha256"],
        "evidence": copy.deepcopy(evidence),
        "adjudication_sha256": "",
    }
    result["adjudication_sha256"] = _sha(_without(result, "adjudication_sha256"))
    validate_ai_sec_observed_adjudication(result, candidate, observation, evidence)
    return result


def validate_ai_sec_observed_adjudication(
    adjudication: dict[str, Any], candidate: dict[str, Any], observation: dict[str, Any], evidence: dict[str, Any]
) -> dict[str, Any]:
    checked = validate_ai_sec_observed_evidence(evidence, candidate, observation)
    field = checked["field"]
    if not isinstance(adjudication, dict) or adjudication.get("schema_version") != ADJUDICATION_SCHEMA or adjudication.get("status") != ADJUDICATION_STATUS:
        raise CaseServiceError("AI observed adjudication schema/status invalid / AI 관측판단 스키마·상태 오류")
    if adjudication.get("canonical") is not False or adjudication.get("decision") != DECISION_APPROVE or adjudication.get("field") != field:
        raise CaseServiceError("AI observed adjudication decision invalid / AI 관측판단 결정 오류")
    if adjudication.get("adjudicator") != {"type": ADJUDICATOR_TYPE, "id": ADJUDICATOR_ID} or adjudication.get("policy_id") != POLICIES[field]:
        raise CaseServiceError("AI observed adjudicator/policy invalid / AI 관측판단 adjudicator·정책 오류")
    _timestamp(adjudication.get("adjudicated_at"), "adjudicated_at")
    for key in ("source_candidate_sha256", "source_observation_sha256", "source_snapshot_sha256", "source_filing_accession", "evidence_sha256"):
        expected_value = evidence["evidence_sha256"] if key == "evidence_sha256" else evidence[key]
        if adjudication.get(key) != expected_value:
            raise CaseServiceError("AI observed adjudication lineage mismatch / AI 관측판단 lineage 불일치")
    if adjudication.get("evidence") != evidence:
        raise CaseServiceError("AI observed adjudication evidence mismatch / AI 관측판단 evidence 불일치")
    expected = _sha(_without(adjudication, "adjudication_sha256"))
    if adjudication.get("adjudication_sha256") != expected:
        raise CaseServiceError("AI observed adjudication SHA mismatch / AI 관측판단 SHA 불일치")
    return {"status": "PASS_AI_SEC_OBSERVED_ADJUDICATION_VALIDATION", "field": field, "adjudication_sha256": expected}


def _authority_review(field: str, source_observation: dict[str, Any], adjudication: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_authority": ADJUDICATOR_TYPE,
        "reviewer": ADJUDICATOR_ID,
        "review_mode": "AI_EVIDENCE_ADJUDICATION",
        "policy_id": POLICIES[field],
        "decision": DECISION_APPROVE,
        "adjudicated_at": adjudication["adjudicated_at"],
        "source_observation_sha256": source_observation["observation_sha256"],
        "evidence_sha256": evidence["evidence_sha256"],
        "adjudication_sha256": adjudication["adjudication_sha256"],
    }


def build_ai_reviewed_cash_observation(
    candidate: dict[str, Any], source_observation: dict[str, Any], adjudication: dict[str, Any], evidence: dict[str, Any]
) -> dict[str, Any]:
    checked = validate_ai_sec_observed_adjudication(adjudication, candidate, source_observation, evidence)
    if checked["field"] != FIELD_CASH:
        raise CaseServiceError("cash AI review requires cash adjudication / cash AI 검토는 cash 판단 필요")
    result = copy.deepcopy(source_observation)
    result["class"] = "NORMALIZED_FACT"
    result["authority_review"] = _authority_review(FIELD_CASH, source_observation, adjudication, evidence)
    result["observation_sha256"] = _sha(_without(result, "observation_sha256"))
    validate_financial_observation(result)
    validate_ai_reviewed_cash_observation(result, candidate, source_observation, adjudication, evidence)
    return result


def validate_ai_reviewed_cash_observation(
    reviewed: dict[str, Any], candidate: dict[str, Any], source_observation: dict[str, Any], adjudication: dict[str, Any], evidence: dict[str, Any]
) -> dict[str, Any]:
    validate_ai_sec_observed_adjudication(adjudication, candidate, source_observation, evidence)
    expected = copy.deepcopy(source_observation)
    expected["class"] = "NORMALIZED_FACT"
    expected["authority_review"] = _authority_review(FIELD_CASH, source_observation, adjudication, evidence)
    expected["observation_sha256"] = _sha(_without(expected, "observation_sha256"))
    if reviewed != expected:
        raise CaseServiceError("AI-reviewed cash projection mismatch / AI 검토 cash 투영 불일치")
    validate_financial_observation(reviewed)
    return {"status": "PASS_AI_REVIEWED_CASH_VALIDATION", "observation_sha256": reviewed["observation_sha256"], "review_authority": "AI"}


def build_ai_reviewed_current_share_observation(
    candidate: dict[str, Any], source_observation: dict[str, Any], adjudication: dict[str, Any], evidence: dict[str, Any]
) -> dict[str, Any]:
    checked = validate_ai_sec_observed_adjudication(adjudication, candidate, source_observation, evidence)
    if checked["field"] != FIELD_SHARES:
        raise CaseServiceError("share AI review requires share adjudication / share AI 검토는 share 판단 필요")
    result = copy.deepcopy(source_observation)
    result["class"] = "NORMALIZED_FACT"
    result["authority_review"] = _authority_review(FIELD_SHARES, source_observation, adjudication, evidence)
    result["observation_sha256"] = _sha(_without(result, "observation_sha256"))
    validate_current_common_shares_observation(result)
    validate_ai_reviewed_current_share_observation(result, candidate, source_observation, adjudication, evidence)
    return result


def validate_ai_reviewed_current_share_observation(
    reviewed: dict[str, Any], candidate: dict[str, Any], source_observation: dict[str, Any], adjudication: dict[str, Any], evidence: dict[str, Any]
) -> dict[str, Any]:
    validate_ai_sec_observed_adjudication(adjudication, candidate, source_observation, evidence)
    expected = copy.deepcopy(source_observation)
    expected["class"] = "NORMALIZED_FACT"
    expected["authority_review"] = _authority_review(FIELD_SHARES, source_observation, adjudication, evidence)
    expected["observation_sha256"] = _sha(_without(expected, "observation_sha256"))
    if reviewed != expected:
        raise CaseServiceError("AI-reviewed current-share projection mismatch / AI 검토 현재주식수 투영 불일치")
    validate_current_common_shares_observation(reviewed)
    if reviewed.get("semantic_boundary") != {"current_common_shares_only": True, "fully_diluted_shares": False}:
        raise CaseServiceError("AI share review cannot imply full dilution / AI share 검토는 완전희석을 의미할 수 없음")
    return {"status": "PASS_AI_REVIEWED_CURRENT_COMMON_SHARES_VALIDATION", "observation_sha256": reviewed["observation_sha256"], "review_authority": "AI"}


def _minority_review_basis(adjudication: dict[str, Any], evidence: dict[str, Any]) -> str:
    return json.dumps({
        "review_mode": "AI_EVIDENCE_ADJUDICATION",
        "policy_id": POLICIES[FIELD_NCI],
        "adjudicator_id": ADJUDICATOR_ID,
        "adjudication_sha256": adjudication["adjudication_sha256"],
        "evidence_sha256": evidence["evidence_sha256"],
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def build_ai_reviewed_minority_interest_package(
    candidate: dict[str, Any], source_observation: dict[str, Any], adjudication: dict[str, Any], evidence: dict[str, Any],
    *, as_of: str, max_age_days: int = 550,
) -> dict[str, Any]:
    checked = validate_ai_sec_observed_adjudication(adjudication, candidate, source_observation, evidence)
    if checked["field"] != FIELD_NCI:
        raise CaseServiceError("NCI AI review requires NCI adjudication / NCI AI 검토는 NCI 판단 필요")
    assertion = build_minority_interest_review_assertion(
        source_observation,
        as_of=as_of,
        reviewer=ADJUDICATOR_ID,
        approved_at=adjudication["adjudicated_at"],
        review_basis=_minority_review_basis(adjudication, evidence),
        asserted_period_end=None,
        max_age_days=max_age_days,
    )
    package = finalize_reviewed_minority_interest(source_observation, assertion)
    package["review_authority"] = _authority_review(FIELD_NCI, source_observation, adjudication, evidence)
    package["package_sha256"] = _sha(_without(package, "package_sha256"))
    validate_reviewed_minority_interest(package)
    validate_ai_reviewed_minority_interest_package(package, candidate, source_observation, adjudication, evidence)
    return package


def validate_ai_reviewed_minority_interest_package(
    package: dict[str, Any], candidate: dict[str, Any], source_observation: dict[str, Any], adjudication: dict[str, Any], evidence: dict[str, Any]
) -> dict[str, Any]:
    checked = validate_ai_sec_observed_adjudication(adjudication, candidate, source_observation, evidence)
    if checked["field"] != FIELD_NCI:
        raise CaseServiceError("NCI package authority mismatch / NCI package 권위 불일치")
    validate_reviewed_minority_interest(package)
    expected_authority = _authority_review(FIELD_NCI, source_observation, adjudication, evidence)
    if package.get("review_authority") != expected_authority:
        raise CaseServiceError("NCI AI review authority mismatch / NCI AI 검토권위 불일치")
    assertion = package.get("review_assertion", {})
    if assertion.get("reviewer") != ADJUDICATOR_ID or assertion.get("approved_at") != adjudication.get("adjudicated_at") or assertion.get("review_basis") != _minority_review_basis(adjudication, evidence):
        raise CaseServiceError("NCI AI review assertion mismatch / NCI AI 검토 assertion 불일치")
    if package.get("semantic_boundary", {}).get("missing_is_zero") is not False:
        raise CaseServiceError("NCI missing-as-zero prohibited / NCI missing-as-zero 금지")
    return {"status": "PASS_AI_REVIEWED_MINORITY_INTEREST_VALIDATION", "package_sha256": package["package_sha256"], "review_authority": "AI", "eligible": package["binding_eligibility"]["eligible"]}
