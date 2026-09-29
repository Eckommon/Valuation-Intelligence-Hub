"""M30-R7 evidence-first AI authority for M21 historical dilution.

This successor reviews the exact SEC weighted-average basic/diluted share
candidate→observation pair and emits a self-contained authority package.
The nested historical dilution remains duration evidence only and can never
represent valuation-date fully diluted shares.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import date, datetime
from typing import Any
from urllib.parse import urlparse

from valuation_hub.case_service import CaseServiceError
from valuation_hub.share_dilution import (
    derive_historical_dilution,
    normalize_share_dilution_candidate,
    validate_historical_dilution,
    validate_share_dilution_candidate,
    validate_share_dilution_observation,
)

EVIDENCE_SCHEMA = "ai-historical-dilution-evidence-v0.1"
EVIDENCE_STATUS = "AI_HISTORICAL_DILUTION_EVIDENCE_READY"
ADJUDICATION_SCHEMA = "ai-historical-dilution-adjudication-v0.1"
ADJUDICATION_STATUS = "AI_HISTORICAL_DILUTION_ADJUDICATED"
PACKAGE_SCHEMA = "ai-reviewed-historical-dilution-package-v0.1"
PACKAGE_STATUS = "AI_REVIEWED_HISTORICAL_DILUTION_READY"

POLICY_ID = "AUTO_APPROVE_SEC_HISTORICAL_DILUTION_V01"
ADJUDICATOR_TYPE = "AI"
ADJUDICATOR_ID = "AI_HISTORICAL_DILUTION_ADJUDICATOR_V01"
DECISION_APPROVE = "APPROVE"

BASIC = "weighted_average_basic_shares"
DILUTED = "weighted_average_diluted_shares"
REQUIRED_CRITERIA = (
    "q1_exact_sec_weighted_average_share_concepts",
    "q2_candidate_observation_lineage_reproduces",
    "q3_same_entity_period_filing_and_source",
    "q4_basic_positive_and_diluted_not_below_basic",
    "q5_historical_only_semantic_boundary_preserved",
)
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
    if (
        parsed.scheme != "https"
        or parsed.hostname != "www.sec.gov"
        or not parsed.path.startswith("/Archives/edgar/")
    ):
        raise CaseServiceError("first-party SEC filing locator required / SEC 공식 filing locator 필요")
    return locator


def _validate_one(
    metric: str,
    candidate: dict[str, Any],
    observation: dict[str, Any],
) -> dict[str, Any]:
    validate_share_dilution_candidate(candidate)
    validate_share_dilution_observation(observation)
    if candidate.get("metric") != metric or observation.get("metric") != metric:
        raise CaseServiceError("historical dilution metric mismatch / 역사적 희석 metric 불일치")
    if candidate.get("class") != "FACT_CANDIDATE" or observation.get("class") != "NORMALIZED_FACT_CANDIDATE":
        raise CaseServiceError("R7 requires unreviewed candidate authority / R7은 미검토 candidate 권위 필요")
    rebuilt = normalize_share_dilution_candidate(candidate)
    if rebuilt != observation:
        raise CaseServiceError("historical candidate-observation lineage mismatch / 역사적 candidate-observation 계보 불일치")
    selection = candidate.get("selection", {})
    source = candidate.get("source", {})
    if selection.get("equal_precedence_count") != 1:
        raise CaseServiceError("historical dilution requires unique SEC fact / 역사적 희석은 고유 SEC fact 필요")
    if source.get("tier_proposal") != "A":
        raise CaseServiceError("historical dilution requires Tier-A SEC source / 역사적 희석 Tier-A SEC source 필요")
    if source.get("publisher") != "U.S. Securities and Exchange Commission":
        raise CaseServiceError("historical dilution SEC publisher mismatch / 역사적 희석 SEC publisher 불일치")
    snapshot_sha = source.get("snapshot_sha256")
    body_sha = source.get("body_sha256")
    if not isinstance(snapshot_sha, str) or not SHA256_RE.fullmatch(snapshot_sha):
        raise CaseServiceError("historical dilution snapshot SHA invalid / 역사적 희석 snapshot SHA 오류")
    if not isinstance(body_sha, str) or not SHA256_RE.fullmatch(body_sha):
        raise CaseServiceError("historical dilution body SHA invalid / 역사적 희석 body SHA 오류")
    return {
        "metric": metric,
        "candidate_sha256": candidate["candidate_sha256"],
        "observation_sha256": observation["observation_sha256"],
        "snapshot_sha256": snapshot_sha,
        "body_sha256": body_sha,
        "filing": copy.deepcopy(candidate["filing"]),
        "period": copy.deepcopy(observation["period"]),
        "entity": copy.deepcopy(observation["entity"]),
        "value": observation["value"],
    }


def _validate_pair(
    basic_candidate: dict[str, Any],
    basic_observation: dict[str, Any],
    diluted_candidate: dict[str, Any],
    diluted_observation: dict[str, Any],
) -> dict[str, Any]:
    basic = _validate_one(BASIC, basic_candidate, basic_observation)
    diluted = _validate_one(DILUTED, diluted_candidate, diluted_observation)
    if basic["entity"] != diluted["entity"]:
        raise CaseServiceError("historical dilution entity mismatch / 역사적 희석 entity 불일치")
    if basic["period"] != diluted["period"]:
        raise CaseServiceError("historical dilution period mismatch / 역사적 희석 기간 불일치")
    if basic["filing"] != diluted["filing"]:
        raise CaseServiceError("historical dilution filing mismatch / 역사적 희석 filing 불일치")
    if basic["snapshot_sha256"] != diluted["snapshot_sha256"] or basic["body_sha256"] != diluted["body_sha256"]:
        raise CaseServiceError("historical dilution source snapshot mismatch / 역사적 희석 source snapshot 불일치")
    b = basic["value"]
    d = diluted["value"]
    if isinstance(b, bool) or isinstance(d, bool) or not isinstance(b, (int, float)) or not isinstance(d, (int, float)):
        raise CaseServiceError("historical dilution numeric values required / 역사적 희석 숫자값 필요")
    if b <= 0 or d < b:
        raise CaseServiceError("historical dilution arithmetic invalid / 역사적 희석 산술 오류")
    return {"basic": basic, "diluted": diluted}


def build_ai_historical_dilution_evidence(
    basic_candidate: dict[str, Any],
    basic_observation: dict[str, Any],
    diluted_candidate: dict[str, Any],
    diluted_observation: dict[str, Any],
    *,
    primary_filing_locator: str,
    evidence_basis: str,
    contradiction_search_summary: str,
    material_contradictions: list[str] | None = None,
    criteria: dict[str, bool],
) -> dict[str, Any]:
    pair = _validate_pair(
        basic_candidate, basic_observation, diluted_candidate, diluted_observation
    )
    if not isinstance(criteria, dict) or set(criteria) != set(REQUIRED_CRITERIA):
        raise CaseServiceError("exact R7 AI criteria set required / 정확한 R7 AI 기준 집합 필요")
    if not all(isinstance(criteria[key], bool) for key in REQUIRED_CRITERIA):
        raise CaseServiceError("R7 criteria booleans required / R7 기준 boolean 필요")
    contradictions = [] if material_contradictions is None else material_contradictions
    if not isinstance(contradictions, list) or not all(
        isinstance(item, str) and item.strip() for item in contradictions
    ):
        raise CaseServiceError("material contradictions string list required / material contradiction 문자열 목록 필요")

    evidence = {
        "schema_version": EVIDENCE_SCHEMA,
        "status": EVIDENCE_STATUS,
        "canonical": False,
        "policy_id": POLICY_ID,
        "pair": {
            "basic_candidate_sha256": pair["basic"]["candidate_sha256"],
            "basic_observation_sha256": pair["basic"]["observation_sha256"],
            "diluted_candidate_sha256": pair["diluted"]["candidate_sha256"],
            "diluted_observation_sha256": pair["diluted"]["observation_sha256"],
            "source_snapshot_sha256": pair["basic"]["snapshot_sha256"],
            "source_body_sha256": pair["basic"]["body_sha256"],
            "filing": copy.deepcopy(pair["basic"]["filing"]),
            "period": copy.deepcopy(pair["basic"]["period"]),
            "entity": copy.deepcopy(pair["basic"]["entity"]),
            "basic_shares": pair["basic"]["value"],
            "diluted_shares": pair["diluted"]["value"],
        },
        "primary_filing_locator": _official_filing_locator(primary_filing_locator),
        "criteria": {key: criteria[key] for key in REQUIRED_CRITERIA},
        "contradiction_search": {
            "performed": True,
            "summary": _text(
                contradiction_search_summary, "contradiction_search_summary", 4000
            ),
            "material_contradictions": [item.strip() for item in contradictions],
        },
        "evidence_basis": _text(evidence_basis, "evidence_basis"),
        "semantic_boundary": {
            "historical_duration_evidence_only": True,
            "valuation_date_direct_bind": False,
            "fully_diluted_shares_substitution": False,
        },
        "evidence_sha256": "",
    }
    evidence["evidence_sha256"] = _sha(_without(evidence, "evidence_sha256"))
    validate_ai_historical_dilution_evidence(
        evidence,
        basic_candidate,
        basic_observation,
        diluted_candidate,
        diluted_observation,
    )
    return evidence


def validate_ai_historical_dilution_evidence(
    evidence: dict[str, Any],
    basic_candidate: dict[str, Any],
    basic_observation: dict[str, Any],
    diluted_candidate: dict[str, Any],
    diluted_observation: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(evidence, dict)
        or evidence.get("schema_version") != EVIDENCE_SCHEMA
        or evidence.get("status") != EVIDENCE_STATUS
        or evidence.get("canonical") is not False
        or evidence.get("policy_id") != POLICY_ID
    ):
        raise CaseServiceError("R7 evidence schema/status invalid / R7 근거 스키마·상태 오류")
    pair = _validate_pair(
        basic_candidate, basic_observation, diluted_candidate, diluted_observation
    )
    expected_pair = {
        "basic_candidate_sha256": pair["basic"]["candidate_sha256"],
        "basic_observation_sha256": pair["basic"]["observation_sha256"],
        "diluted_candidate_sha256": pair["diluted"]["candidate_sha256"],
        "diluted_observation_sha256": pair["diluted"]["observation_sha256"],
        "source_snapshot_sha256": pair["basic"]["snapshot_sha256"],
        "source_body_sha256": pair["basic"]["body_sha256"],
        "filing": copy.deepcopy(pair["basic"]["filing"]),
        "period": copy.deepcopy(pair["basic"]["period"]),
        "entity": copy.deepcopy(pair["basic"]["entity"]),
        "basic_shares": pair["basic"]["value"],
        "diluted_shares": pair["diluted"]["value"],
    }
    if evidence.get("pair") != expected_pair:
        raise CaseServiceError("R7 evidence lineage mismatch / R7 근거 계보 불일치")
    _official_filing_locator(evidence.get("primary_filing_locator"))
    _text(evidence.get("evidence_basis"), "evidence_basis")
    criteria = evidence.get("criteria")
    if (
        not isinstance(criteria, dict)
        or set(criteria) != set(REQUIRED_CRITERIA)
        or not all(criteria.get(key) is True for key in REQUIRED_CRITERIA)
    ):
        raise CaseServiceError("R7 evidence criteria not all satisfied / R7 근거 기준 미충족")
    contradiction = evidence.get("contradiction_search")
    if not isinstance(contradiction, dict) or contradiction.get("performed") is not True:
        raise CaseServiceError("R7 contradiction search required / R7 반증검색 필요")
    _text(contradiction.get("summary"), "contradiction_search.summary", 4000)
    conflicts = contradiction.get("material_contradictions")
    if not isinstance(conflicts, list):
        raise CaseServiceError("R7 contradiction list invalid / R7 반증목록 오류")
    if conflicts:
        raise CaseServiceError("material contradiction requires HOLD/escalation / 중대한 반증은 HOLD·상향 필요")
    expected_boundary = {
        "historical_duration_evidence_only": True,
        "valuation_date_direct_bind": False,
        "fully_diluted_shares_substitution": False,
    }
    if evidence.get("semantic_boundary") != expected_boundary:
        raise CaseServiceError("R7 semantic boundary invalid / R7 의미경계 오류")
    expected_sha = _sha(_without(evidence, "evidence_sha256"))
    if evidence.get("evidence_sha256") != expected_sha:
        raise CaseServiceError("R7 evidence SHA mismatch / R7 근거 SHA 불일치")
    return {
        "status": "PASS_AI_HISTORICAL_DILUTION_EVIDENCE_VALIDATION",
        "evidence_sha256": expected_sha,
    }


def build_ai_historical_dilution_adjudication(
    evidence: dict[str, Any],
    basic_candidate: dict[str, Any],
    basic_observation: dict[str, Any],
    diluted_candidate: dict[str, Any],
    diluted_observation: dict[str, Any],
    *,
    adjudicated_at: str,
) -> dict[str, Any]:
    validate_ai_historical_dilution_evidence(
        evidence,
        basic_candidate,
        basic_observation,
        diluted_candidate,
        diluted_observation,
    )
    when = _timestamp(adjudicated_at, "adjudicated_at")
    filed = date.fromisoformat(evidence["pair"]["filing"]["filed"])
    if when.date() < filed:
        raise CaseServiceError("R7 adjudication cannot precede filing / R7 판단은 filing 이전 불가")
    adjudication = {
        "schema_version": ADJUDICATION_SCHEMA,
        "status": ADJUDICATION_STATUS,
        "canonical": False,
        "decision": DECISION_APPROVE,
        "policy_id": POLICY_ID,
        "adjudicator": {"type": ADJUDICATOR_TYPE, "id": ADJUDICATOR_ID},
        "adjudicated_at": when.isoformat(),
        "evidence_sha256": evidence["evidence_sha256"],
        "source_snapshot_sha256": evidence["pair"]["source_snapshot_sha256"],
        "source_filing_accession": evidence["pair"]["filing"]["accession"],
        "adjudication_sha256": "",
    }
    adjudication["adjudication_sha256"] = _sha(
        _without(adjudication, "adjudication_sha256")
    )
    validate_ai_historical_dilution_adjudication(
        adjudication,
        evidence,
        basic_candidate,
        basic_observation,
        diluted_candidate,
        diluted_observation,
    )
    return adjudication


def validate_ai_historical_dilution_adjudication(
    adjudication: dict[str, Any],
    evidence: dict[str, Any],
    basic_candidate: dict[str, Any],
    basic_observation: dict[str, Any],
    diluted_candidate: dict[str, Any],
    diluted_observation: dict[str, Any],
) -> dict[str, Any]:
    validate_ai_historical_dilution_evidence(
        evidence,
        basic_candidate,
        basic_observation,
        diluted_candidate,
        diluted_observation,
    )
    if (
        not isinstance(adjudication, dict)
        or adjudication.get("schema_version") != ADJUDICATION_SCHEMA
        or adjudication.get("status") != ADJUDICATION_STATUS
        or adjudication.get("canonical") is not False
        or adjudication.get("decision") != DECISION_APPROVE
        or adjudication.get("policy_id") != POLICY_ID
        or adjudication.get("adjudicator")
        != {"type": ADJUDICATOR_TYPE, "id": ADJUDICATOR_ID}
    ):
        raise CaseServiceError("R7 adjudication schema/authority invalid / R7 판단 스키마·권위 오류")
    when = _timestamp(adjudication.get("adjudicated_at"), "adjudicated_at")
    if when.date() < date.fromisoformat(evidence["pair"]["filing"]["filed"]):
        raise CaseServiceError("R7 adjudication cannot precede filing / R7 판단은 filing 이전 불가")
    if (
        adjudication.get("evidence_sha256") != evidence.get("evidence_sha256")
        or adjudication.get("source_snapshot_sha256")
        != evidence["pair"]["source_snapshot_sha256"]
        or adjudication.get("source_filing_accession")
        != evidence["pair"]["filing"]["accession"]
    ):
        raise CaseServiceError("R7 adjudication lineage mismatch / R7 판단 계보 불일치")
    expected_sha = _sha(_without(adjudication, "adjudication_sha256"))
    if adjudication.get("adjudication_sha256") != expected_sha:
        raise CaseServiceError("R7 adjudication SHA mismatch / R7 판단 SHA 불일치")
    return {
        "status": "PASS_AI_HISTORICAL_DILUTION_ADJUDICATION_VALIDATION",
        "adjudication_sha256": expected_sha,
    }


def _promote_observation(
    observation: dict[str, Any],
    evidence: dict[str, Any],
    adjudication: dict[str, Any],
) -> dict[str, Any]:
    reviewed = copy.deepcopy(observation)
    reviewed["class"] = "NORMALIZED_FACT"
    reviewed["authority_review"] = {
        "review_authority": ADJUDICATOR_TYPE,
        "reviewer": ADJUDICATOR_ID,
        "review_mode": "AI_EVIDENCE_ADJUDICATION",
        "policy_id": POLICY_ID,
        "decision": DECISION_APPROVE,
        "adjudicated_at": adjudication["adjudicated_at"],
        "source_observation_sha256": observation["observation_sha256"],
        "evidence_sha256": evidence["evidence_sha256"],
        "adjudication_sha256": adjudication["adjudication_sha256"],
    }
    reviewed["observation_sha256"] = ""
    reviewed["observation_sha256"] = _sha(
        _without(reviewed, "observation_sha256")
    )
    validate_share_dilution_observation(reviewed)
    return reviewed


def build_ai_reviewed_historical_dilution_package(
    basic_candidate: dict[str, Any],
    basic_observation: dict[str, Any],
    diluted_candidate: dict[str, Any],
    diluted_observation: dict[str, Any],
    evidence: dict[str, Any],
    adjudication: dict[str, Any],
) -> dict[str, Any]:
    validate_ai_historical_dilution_adjudication(
        adjudication,
        evidence,
        basic_candidate,
        basic_observation,
        diluted_candidate,
        diluted_observation,
    )
    reviewed_basic = _promote_observation(
        basic_observation, evidence, adjudication
    )
    reviewed_diluted = _promote_observation(
        diluted_observation, evidence, adjudication
    )
    historical = derive_historical_dilution(reviewed_basic, reviewed_diluted)
    if historical.get("class") != "DERIVED_FACT":
        raise CaseServiceError("R7 reviewed historical dilution must derive FACT / R7 검토 역사희석 FACT 필요")
    package = {
        "schema_version": PACKAGE_SCHEMA,
        "status": PACKAGE_STATUS,
        "canonical": False,
        "class": "DERIVED_FACT",
        "metric": "historical_dilution",
        "unit": "ratio+shares",
        "policy_id": POLICY_ID,
        "entity": copy.deepcopy(historical["entity"]),
        "period": copy.deepcopy(historical["period"]),
        "derived_sha256": historical["derived_sha256"],
        "source_candidates": {
            "basic": copy.deepcopy(basic_candidate),
            "diluted": copy.deepcopy(diluted_candidate),
        },
        "source_observations": {
            "basic": copy.deepcopy(basic_observation),
            "diluted": copy.deepcopy(diluted_observation),
        },
        "evidence": copy.deepcopy(evidence),
        "adjudication": copy.deepcopy(adjudication),
        "reviewed_observations": {
            "basic": reviewed_basic,
            "diluted": reviewed_diluted,
        },
        "historical_dilution": historical,
        "semantic_boundary": {
            "historical_only": True,
            "valuation_date_direct_bind": False,
            "fully_diluted_shares_substitution": False,
            "r6_anchor_eligible": True,
        },
        "package_sha256": "",
    }
    package["package_sha256"] = _sha(_without(package, "package_sha256"))
    validate_ai_reviewed_historical_dilution_package(package)
    return package


def validate_ai_reviewed_historical_dilution_package(
    package: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(package, dict)
        or package.get("schema_version") != PACKAGE_SCHEMA
        or package.get("status") != PACKAGE_STATUS
        or package.get("canonical") is not False
        or package.get("class") != "DERIVED_FACT"
        or package.get("metric") != "historical_dilution"
        or package.get("unit") != "ratio+shares"
        or package.get("policy_id") != POLICY_ID
    ):
        raise CaseServiceError("R7 package schema/status invalid / R7 package 스키마·상태 오류")
    candidates = package.get("source_candidates")
    observations = package.get("source_observations")
    reviewed = package.get("reviewed_observations")
    evidence = package.get("evidence")
    adjudication = package.get("adjudication")
    historical = package.get("historical_dilution")
    if not all(
        isinstance(value, dict)
        for value in (
            candidates,
            observations,
            reviewed,
            evidence,
            adjudication,
            historical,
        )
    ):
        raise CaseServiceError("R7 package embedded lineage incomplete / R7 package 내장 계보 불완전")
    basic_candidate = candidates.get("basic")
    diluted_candidate = candidates.get("diluted")
    basic_observation = observations.get("basic")
    diluted_observation = observations.get("diluted")
    if not all(
        isinstance(value, dict)
        for value in (
            basic_candidate,
            diluted_candidate,
            basic_observation,
            diluted_observation,
        )
    ):
        raise CaseServiceError("R7 package source pair incomplete / R7 package source pair 불완전")
    validate_ai_historical_dilution_adjudication(
        adjudication,
        evidence,
        basic_candidate,
        basic_observation,
        diluted_candidate,
        diluted_observation,
    )
    expected_basic = _promote_observation(
        basic_observation, evidence, adjudication
    )
    expected_diluted = _promote_observation(
        diluted_observation, evidence, adjudication
    )
    if reviewed.get("basic") != expected_basic or reviewed.get("diluted") != expected_diluted:
        raise CaseServiceError("R7 reviewed observation projection mismatch / R7 검토 observation 투영 불일치")
    expected_historical = derive_historical_dilution(
        expected_basic, expected_diluted
    )
    validate_historical_dilution(historical)
    if historical != expected_historical:
        raise CaseServiceError("R7 historical dilution projection mismatch / R7 역사희석 투영 불일치")
    if (
        package.get("entity") != historical.get("entity")
        or package.get("period") != historical.get("period")
        or package.get("derived_sha256") != historical.get("derived_sha256")
    ):
        raise CaseServiceError("R7 package historical lineage mismatch / R7 package 역사 계보 불일치")
    expected_boundary = {
        "historical_only": True,
        "valuation_date_direct_bind": False,
        "fully_diluted_shares_substitution": False,
        "r6_anchor_eligible": True,
    }
    if package.get("semantic_boundary") != expected_boundary:
        raise CaseServiceError("R7 package semantic boundary invalid / R7 package 의미경계 오류")
    expected_sha = _sha(_without(package, "package_sha256"))
    if package.get("package_sha256") != expected_sha:
        raise CaseServiceError("R7 package SHA mismatch / R7 package SHA 불일치")
    return {
        "status": "PASS_AI_REVIEWED_HISTORICAL_DILUTION_VALIDATION",
        "package_sha256": expected_sha,
        "derived_sha256": historical["derived_sha256"],
        "basic_shares": evidence["pair"]["basic_shares"],
        "diluted_shares": evidence["pair"]["diluted_shares"],
        "historical_incremental_diluted_shares": historical[
            "historical_incremental_diluted_shares"
        ],
        "review_authority": ADJUDICATOR_TYPE,
        "r6_anchor_eligible": True,
    }
