"""Evidence-first autonomous semantic adjudication for SEC aggregate debt.

This module is additive to the legacy explicit-human review path. It does not
fabricate a human reviewer. Instead it creates a typed AI adjudication artifact
from a structured evidence packet, fails closed on missing/contradictory
criteria, and then produces a legacy-compatible review assertion whose reviewer
identifier is explicitly the model-neutral AI adjudicator constant.

The compatibility assertion exists only so the already-canonical downstream
profile/context machinery can be reused without weakening historical validators.
"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.sec_aggregate_debt import (
    SEMANTIC_DECISION,
    build_sec_aggregate_debt_review_assertion,
    review_scope_sha256,
    validate_sec_aggregate_debt_observation,
)

EVIDENCE_SCHEMA = "ai-sec-aggregate-debt-evidence-v0.1"
EVIDENCE_STATUS = "AI_SEC_AGGREGATE_DEBT_EVIDENCE_READY"
ADJUDICATION_SCHEMA = "ai-sec-aggregate-debt-adjudication-v0.1"
ADJUDICATION_STATUS = "AI_SEC_AGGREGATE_DEBT_ADJUDICATED"
ADJUDICATOR_TYPE = "AI"
ADJUDICATOR_ID = "AI_EVIDENCE_ADJUDICATOR_V01"
POLICY_ID = "AUTO_APPROVE_SEC_AGGREGATE_DEBT_V01"
DECISION_APPROVE = "APPROVE"
DECISION_HOLD = "HOLD"

REQUIRED_CRITERIA = (
    "q1_financing_components_are_interest_bearing",
    "q2_issuer_total_debt_reconciles_to_observation",
    "q3_operating_lease_liabilities_separately_classified",
    "q4_lease_exclusion_supported",
)


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    out = copy.deepcopy(value)
    out.pop(key, None)
    return out


def _text(value: Any, field: str, limit: int = 4000) -> str:
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


def build_ai_sec_aggregate_debt_evidence(
    observation: dict[str, Any], *, primary_filing_locator: str,
    supporting_filing_locators: list[str], evidence_basis: str,
    contradiction_search_summary: str, material_contradictions: list[str] | None = None,
    criteria: dict[str, bool],
) -> dict[str, Any]:
    validate_sec_aggregate_debt_observation(observation)
    primary = _text(primary_filing_locator, "primary_filing_locator", 2000)
    if not isinstance(supporting_filing_locators, list) or not all(isinstance(v, str) and v.strip() for v in supporting_filing_locators):
        raise CaseServiceError("supporting filing locators must be string list / supporting filing locator 문자열 목록 필요")
    supporting = [v.strip() for v in supporting_filing_locators]
    basis = _text(evidence_basis, "evidence_basis", 8000)
    contradiction_summary = _text(contradiction_search_summary, "contradiction_search_summary", 4000)
    contradictions = [] if material_contradictions is None else material_contradictions
    if not isinstance(contradictions, list) or not all(isinstance(v, str) and v.strip() for v in contradictions):
        raise CaseServiceError("material contradictions must be string list / material contradiction 문자열 목록 필요")
    if not isinstance(criteria, dict) or set(criteria) != set(REQUIRED_CRITERIA):
        raise CaseServiceError("exact AI debt criteria set required / 정확한 AI debt 기준 집합 필요")
    if not all(isinstance(criteria[key], bool) for key in REQUIRED_CRITERIA):
        raise CaseServiceError("AI debt criteria must be boolean / AI debt 기준은 boolean 필요")

    packet = {
        "schema_version": EVIDENCE_SCHEMA,
        "status": EVIDENCE_STATUS,
        "canonical": False,
        "policy_id": POLICY_ID,
        "source_observation_sha256": observation["observation_sha256"],
        "scope_sha256": review_scope_sha256(observation),
        "source_filing_accession": observation["filing"]["accession"],
        "primary_filing_locator": primary,
        "supporting_filing_locators": supporting,
        "criteria": {key: criteria[key] for key in REQUIRED_CRITERIA},
        "contradiction_search": {
            "performed": True,
            "summary": contradiction_summary,
            "material_contradictions": [v.strip() for v in contradictions],
        },
        "evidence_basis": basis,
        "evidence_sha256": "",
    }
    packet["evidence_sha256"] = _sha(_without(packet, "evidence_sha256"))
    validate_ai_sec_aggregate_debt_evidence(packet, observation)
    return packet


def validate_ai_sec_aggregate_debt_evidence(packet: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    validate_sec_aggregate_debt_observation(observation)
    if not isinstance(packet, dict) or packet.get("schema_version") != EVIDENCE_SCHEMA or packet.get("status") != EVIDENCE_STATUS:
        raise CaseServiceError("AI debt evidence schema/status invalid / AI debt evidence 스키마·상태 오류")
    if packet.get("canonical") is not False or packet.get("policy_id") != POLICY_ID:
        raise CaseServiceError("AI debt evidence authority/policy invalid / AI debt evidence 권위·정책 오류")
    if packet.get("source_observation_sha256") != observation.get("observation_sha256"):
        raise CaseServiceError("AI debt evidence observation mismatch / AI debt evidence observation 불일치")
    if packet.get("scope_sha256") != review_scope_sha256(observation):
        raise CaseServiceError("AI debt evidence scope mismatch / AI debt evidence scope 불일치")
    if packet.get("source_filing_accession") != observation.get("filing", {}).get("accession"):
        raise CaseServiceError("AI debt evidence filing mismatch / AI debt evidence filing 불일치")
    _text(packet.get("primary_filing_locator"), "primary_filing_locator", 2000)
    supporting = packet.get("supporting_filing_locators")
    if not isinstance(supporting, list) or not all(isinstance(v, str) and v.strip() for v in supporting):
        raise CaseServiceError("AI debt supporting locators invalid / AI debt supporting locator 오류")
    _text(packet.get("evidence_basis"), "evidence_basis", 8000)
    criteria = packet.get("criteria")
    if not isinstance(criteria, dict) or set(criteria) != set(REQUIRED_CRITERIA):
        raise CaseServiceError("AI debt evidence criteria invalid / AI debt evidence 기준 오류")
    if not all(criteria.get(key) is True for key in REQUIRED_CRITERIA):
        raise CaseServiceError("AI debt evidence criteria not all satisfied / AI debt evidence 기준 미충족")
    contradiction = packet.get("contradiction_search")
    if not isinstance(contradiction, dict) or contradiction.get("performed") is not True:
        raise CaseServiceError("AI debt contradiction search required / AI debt 반증검색 필요")
    _text(contradiction.get("summary"), "contradiction_search.summary", 4000)
    conflicts = contradiction.get("material_contradictions")
    if not isinstance(conflicts, list):
        raise CaseServiceError("AI debt contradiction list invalid / AI debt 반증목록 오류")
    if conflicts:
        raise CaseServiceError("AI debt material contradiction requires HOLD/escalation / AI debt 중대한 반증은 HOLD·상향 필요")
    expected = _sha(_without(packet, "evidence_sha256"))
    if packet.get("evidence_sha256") != expected:
        raise CaseServiceError("AI debt evidence SHA mismatch / AI debt evidence SHA 불일치")
    return {"status": "PASS_AI_SEC_AGGREGATE_DEBT_EVIDENCE_VALIDATION", "evidence_sha256": expected}


def build_ai_sec_aggregate_debt_adjudication(
    observation: dict[str, Any], evidence: dict[str, Any], *, adjudicated_at: str
) -> dict[str, Any]:
    validate_sec_aggregate_debt_observation(observation)
    validate_ai_sec_aggregate_debt_evidence(evidence, observation)
    ts = _timestamp(adjudicated_at, "adjudicated_at")
    if datetime.fromisoformat(observation["period"]["end"] + "T00:00:00+00:00").date() > ts.date():
        raise CaseServiceError("AI adjudication cannot precede source period end / AI 판단은 source 기간말 이전 불가")
    adjudication = {
        "schema_version": ADJUDICATION_SCHEMA,
        "status": ADJUDICATION_STATUS,
        "canonical": False,
        "decision": DECISION_APPROVE,
        "adjudicator": {"type": ADJUDICATOR_TYPE, "id": ADJUDICATOR_ID},
        "policy_id": POLICY_ID,
        "adjudicated_at": ts.isoformat(),
        "semantic_scope_decision": SEMANTIC_DECISION,
        "source_observation_sha256": observation["observation_sha256"],
        "scope_sha256": review_scope_sha256(observation),
        "source_filing_accession": observation["filing"]["accession"],
        "evidence_sha256": evidence["evidence_sha256"],
        "evidence": copy.deepcopy(evidence),
        "adjudication_sha256": "",
    }
    adjudication["adjudication_sha256"] = _sha(_without(adjudication, "adjudication_sha256"))
    validate_ai_sec_aggregate_debt_adjudication(adjudication, observation, evidence)
    return adjudication


def validate_ai_sec_aggregate_debt_adjudication(
    adjudication: dict[str, Any], observation: dict[str, Any], evidence: dict[str, Any]
) -> dict[str, Any]:
    validate_sec_aggregate_debt_observation(observation)
    validate_ai_sec_aggregate_debt_evidence(evidence, observation)
    if not isinstance(adjudication, dict) or adjudication.get("schema_version") != ADJUDICATION_SCHEMA or adjudication.get("status") != ADJUDICATION_STATUS:
        raise CaseServiceError("AI debt adjudication schema/status invalid / AI debt 판단 스키마·상태 오류")
    if adjudication.get("canonical") is not False or adjudication.get("decision") != DECISION_APPROVE:
        raise CaseServiceError("AI debt adjudication decision invalid / AI debt 판단 결정 오류")
    if adjudication.get("adjudicator") != {"type": ADJUDICATOR_TYPE, "id": ADJUDICATOR_ID}:
        raise CaseServiceError("AI debt adjudicator identity invalid / AI debt adjudicator 식별 오류")
    if adjudication.get("policy_id") != POLICY_ID or adjudication.get("semantic_scope_decision") != SEMANTIC_DECISION:
        raise CaseServiceError("AI debt adjudication policy/semantic decision invalid / AI debt 판단 정책·의미결정 오류")
    _timestamp(adjudication.get("adjudicated_at"), "adjudicated_at")
    if adjudication.get("source_observation_sha256") != observation.get("observation_sha256") or adjudication.get("scope_sha256") != review_scope_sha256(observation):
        raise CaseServiceError("AI debt adjudication scope mismatch / AI debt 판단 scope 불일치")
    if adjudication.get("source_filing_accession") != observation.get("filing", {}).get("accession"):
        raise CaseServiceError("AI debt adjudication filing mismatch / AI debt 판단 filing 불일치")
    if adjudication.get("evidence_sha256") != evidence.get("evidence_sha256") or adjudication.get("evidence") != evidence:
        raise CaseServiceError("AI debt adjudication evidence lineage mismatch / AI debt 판단 evidence lineage 불일치")
    expected = _sha(_without(adjudication, "adjudication_sha256"))
    if adjudication.get("adjudication_sha256") != expected:
        raise CaseServiceError("AI debt adjudication SHA mismatch / AI debt 판단 SHA 불일치")
    return {"status": "PASS_AI_SEC_AGGREGATE_DEBT_ADJUDICATION_VALIDATION", "adjudication_sha256": expected}


def build_legacy_compatible_ai_review_assertion(
    observation: dict[str, Any], adjudication: dict[str, Any], evidence: dict[str, Any]
) -> dict[str, Any]:
    validate_ai_sec_aggregate_debt_adjudication(adjudication, observation, evidence)
    review_basis = json.dumps(
        {
            "review_mode": "AI_EVIDENCE_ADJUDICATION",
            "policy_id": POLICY_ID,
            "adjudicator_id": ADJUDICATOR_ID,
            "adjudication_sha256": adjudication["adjudication_sha256"],
            "evidence_sha256": evidence["evidence_sha256"],
            "evidence_basis": evidence["evidence_basis"],
            "contradiction_search": evidence["contradiction_search"],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    if len(review_basis) > 2000:
        compact = {
            "review_mode": "AI_EVIDENCE_ADJUDICATION",
            "policy_id": POLICY_ID,
            "adjudicator_id": ADJUDICATOR_ID,
            "adjudication_sha256": adjudication["adjudication_sha256"],
            "evidence_sha256": evidence["evidence_sha256"],
        }
        review_basis = json.dumps(compact, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return build_sec_aggregate_debt_review_assertion(
        observation,
        reviewer=ADJUDICATOR_ID,
        reviewed_at=adjudication["adjudicated_at"],
        review_basis=review_basis,
        source_basis_locator=evidence["primary_filing_locator"],
        semantic_scope_decision=SEMANTIC_DECISION,
    )
