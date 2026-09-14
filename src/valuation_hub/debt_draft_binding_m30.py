"""M30 backward-compatible debt-binding proposal successor.

Historical M16/M20 v0.1/v0.2 behavior remains delegated unchanged. The successor
accepts only the separately reviewed exact SEC aggregate-debt context and replaces
only `equity.debt`, without claiming historical five-component completeness.
"""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from valuation_hub import debt_draft_binding as legacy
from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_binding import DIRECT_BIND, MATERIAL_FIELDS, STATUS, build_binding_proposal, validate_binding_proposal
from valuation_hub.sec_aggregate_debt import (
    CONTEXT_POLICY,
    FRESH,
    STALE_BLOCKED,
    validate_sec_aggregate_debt_binding_context,
)

SCHEMA_VERSION = "draft-binding-proposal-v0.2-sec-aggregate-debt"
POLICY_VERSION = "evidence-draft-binding-v0.2-sec-aggregate-debt"


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    out = copy.deepcopy(value)
    out.pop(key, None)
    return out


def _counts(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for item in matrix:
        counts[item["state"]] = counts.get(item["state"], 0) + 1
    return {
        "material_field_count": len(MATERIAL_FIELDS),
        "classified_field_count": len(matrix),
        "state_counts": counts,
        "direct_bind_count": counts.get(DIRECT_BIND, 0),
        "unresolved_count": sum(count for state, count in counts.items() if state != DIRECT_BIND),
    }


def _projection(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "metric": "interest_bearing_debt",
        "value": context["value"],
        "unit": context["unit"],
        "class": "DERIVED_FACT",
        "entity": copy.deepcopy(context["entity"]),
        "source_period": copy.deepcopy(context["source_period"]),
        "resolved_period_end": context["resolved_period_end"],
        "freshness": copy.deepcopy(context["freshness"]),
        "context_sha256": context["context_sha256"],
        "source_debt_sha256": context["source_debt_sha256"],
        "source_debt_profile_sha256": context["source_debt_profile_sha256"],
        "review_assertion_sha256": context["review_assertion_sha256"],
        "date_resolution": copy.deepcopy(context["date_resolution"]),
        "semantic_boundary": copy.deepcopy(context["semantic_boundary"]),
    }


def _decision(context: dict[str, Any]) -> dict[str, Any]:
    fresh = context["freshness"]["status"]
    eligible = context["binding_eligibility"]["eligible"] is True and fresh == FRESH
    return {
        "field": "equity.debt",
        "state": DIRECT_BIND if eligible else STALE_BLOCKED,
        "rationale": (
            "human-reviewed exact SEC aggregate debt with explicit lease-liability boundary / "
            "인간검토완료 exact SEC aggregate debt 및 명시적 lease-liability 경계"
            if eligible
            else "reviewed SEC aggregate debt exceeds freshness policy / 검토 SEC aggregate debt가 최신성 정책 초과"
        ),
        "source_metric": "interest_bearing_debt",
        "source_class": "DERIVED_FACT",
        "source_freshness": copy.deepcopy(context["freshness"]),
        "source_context_sha256": context["context_sha256"],
        "source_debt_sha256": context["source_debt_sha256"],
        "source_debt_profile_sha256": context["source_debt_profile_sha256"],
        "review_assertion_sha256": context["review_assertion_sha256"],
        "date_assertion_sha256": None,
    }


def build_binding_proposal_with_sec_aggregate_debt(
    observations: list[dict[str, Any]], debt_context: dict[str, Any], *, as_of: str, max_age_days: int = 550
) -> dict[str, Any]:
    base = build_binding_proposal(observations, as_of=as_of, max_age_days=max_age_days)
    validate_sec_aggregate_debt_binding_context(debt_context)
    context_policy = debt_context.get("policy", {})
    if context_policy.get("version") != CONTEXT_POLICY or context_policy.get("as_of") != as_of or context_policy.get("max_age_days") != max_age_days:
        raise CaseServiceError("SEC aggregate debt context/proposal policy mismatch / SEC aggregate debt context·proposal 정책 불일치")
    identity = base["identity"]
    if debt_context["entity"] != {"id": identity["entity_id"], "financial_scope": identity["financial_scope"]}:
        raise CaseServiceError("SEC aggregate debt entity/scope mismatch / SEC aggregate debt entity·scope 불일치")
    monetary = identity.get("monetary_unit")
    if monetary is not None and debt_context["unit"] != monetary:
        raise CaseServiceError("SEC aggregate debt unit mismatch / SEC aggregate debt unit 불일치")
    matrix = [_decision(debt_context) if item["field"] == "equity.debt" else copy.deepcopy(item) for item in base["draft_input_matrix"]]
    baseline = copy.deepcopy(base["baseline_context"])
    baseline["interest_bearing_debt"] = _projection(debt_context)
    proposal = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "canonical": False,
        "target": copy.deepcopy(base["target"]),
        "policy": {
            "version": POLICY_VERSION,
            "as_of": as_of,
            "max_age_days": max_age_days,
            "direct_bind_requires": [
                "EXACT_SEC_AGGREGATE_DEBT_CONCEPT",
                "HUMAN_REVIEWED_NORMALIZED_FACT",
                "EXPLICIT_LEASE_LIABILITY_BOUNDARY",
                "DERIVED_FACT_PROJECTION",
                "FRESH",
                "PERIOD_COMPATIBLE",
            ],
        },
        "identity": copy.deepcopy(identity),
        "baseline_context": baseline,
        "conflicts": copy.deepcopy(base["conflicts"]),
        "draft_input_matrix": matrix,
        "completeness": _counts(matrix),
        "source_observation_sha256": copy.deepcopy(base["source_observation_sha256"]),
        "source_debt_context_sha256": debt_context["context_sha256"],
        "debt_binding_context": copy.deepcopy(debt_context),
        "base_v01_proposal": copy.deepcopy(base),
        "warning_en": "SEC aggregate-debt successor only. Historical M19 five-component completeness is not claimed or reconstructed.",
        "warning_ko": "SEC aggregate-debt successor 전용입니다. 역사적 M19 5개 구성요소 완전성을 주장하거나 재구성하지 않습니다.",
        "proposal_sha256": "",
    }
    proposal["proposal_sha256"] = _sha(_without(proposal, "proposal_sha256"))
    validate_binding_proposal_sec_aggregate(proposal)
    return proposal


def validate_binding_proposal_sec_aggregate(proposal: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(proposal, dict) or proposal.get("schema_version") != SCHEMA_VERSION or proposal.get("status") != STATUS or proposal.get("canonical") is not False:
        raise CaseServiceError("SEC aggregate debt proposal schema/status invalid / SEC aggregate debt proposal 스키마·상태 오류")
    if proposal.get("target") != {"draft_schema_version": "draft-case-v0.1", "model": "equity_fcff"}:
        raise CaseServiceError("SEC aggregate debt proposal target invalid / SEC aggregate debt proposal 대상 오류")
    base = proposal.get("base_v01_proposal")
    if not isinstance(base, dict):
        raise CaseServiceError("SEC aggregate debt base v0.1 proposal missing / SEC aggregate debt base v0.1 proposal 누락")
    validate_binding_proposal(base)
    if proposal.get("identity") != base.get("identity") or proposal.get("conflicts") != base.get("conflicts") or proposal.get("source_observation_sha256") != base.get("source_observation_sha256"):
        raise CaseServiceError("SEC aggregate debt proposal/base lineage mismatch / SEC aggregate debt proposal·base lineage 불일치")
    policy = proposal.get("policy")
    if not isinstance(policy, dict) or policy.get("version") != POLICY_VERSION or policy.get("as_of") != base.get("policy", {}).get("as_of") or policy.get("max_age_days") != base.get("policy", {}).get("max_age_days"):
        raise CaseServiceError("SEC aggregate debt proposal policy/base mismatch / SEC aggregate debt proposal 정책·base 불일치")
    context = proposal.get("debt_binding_context")
    if not isinstance(context, dict):
        raise CaseServiceError("SEC aggregate debt full context missing / SEC aggregate debt 전체 context 누락")
    validate_sec_aggregate_debt_binding_context(context)
    context_policy = context.get("policy", {})
    if context_policy.get("as_of") != policy.get("as_of") or context_policy.get("max_age_days") != policy.get("max_age_days"):
        raise CaseServiceError("SEC aggregate debt context/proposal freshness mismatch / SEC aggregate debt context·proposal 최신성 불일치")
    if proposal.get("source_debt_context_sha256") != context.get("context_sha256"):
        raise CaseServiceError("SEC aggregate debt context SHA lineage mismatch / SEC aggregate debt context SHA lineage 불일치")
    baseline = proposal.get("baseline_context")
    if not isinstance(baseline, dict) or baseline.get("interest_bearing_debt") != _projection(context):
        raise CaseServiceError("SEC aggregate debt baseline projection mismatch / SEC aggregate debt baseline 투영 불일치")
    identity = proposal["identity"]
    if context.get("entity") != {"id": identity.get("entity_id"), "financial_scope": identity.get("financial_scope")} or context.get("unit") != identity.get("monetary_unit"):
        raise CaseServiceError("SEC aggregate debt context identity/unit mismatch / SEC aggregate debt context 식별·unit 불일치")
    matrix = proposal.get("draft_input_matrix")
    if not isinstance(matrix, list) or {item.get("field") for item in matrix if isinstance(item, dict)} != set(MATERIAL_FIELDS):
        raise CaseServiceError("SEC aggregate debt binding matrix incomplete / SEC aggregate debt 바인딩 matrix 불완전")
    base_by = {item["field"]: item for item in base["draft_input_matrix"]}
    by = {item["field"]: item for item in matrix}
    for field in MATERIAL_FIELDS:
        if field != "equity.debt" and by[field] != base_by[field]:
            raise CaseServiceError("SEC aggregate debt successor may replace only equity.debt / SEC aggregate debt successor는 equity.debt만 변경 가능")
    if by["equity.debt"] != _decision(context):
        raise CaseServiceError("SEC aggregate debt decision lineage mismatch / SEC aggregate debt 판정 lineage 불일치")
    if proposal.get("completeness") != _counts(matrix):
        raise CaseServiceError("SEC aggregate debt completeness mismatch / SEC aggregate debt completeness 불일치")
    expected = _sha(_without(proposal, "proposal_sha256"))
    if proposal.get("proposal_sha256") != expected:
        raise CaseServiceError("SEC aggregate debt proposal SHA mismatch / SEC aggregate debt proposal SHA 불일치")
    return {
        "status": "PASS_SEC_AGGREGATE_DEBT_BINDING_PROPOSAL_VALIDATION",
        "canonical": False,
        "proposal_sha256": expected,
        "direct_bind_count": proposal["completeness"]["direct_bind_count"],
        "unresolved_count": proposal["completeness"]["unresolved_count"],
    }


def validate_binding_proposal_any(proposal: dict[str, Any]) -> dict[str, Any]:
    if isinstance(proposal, dict) and proposal.get("schema_version") == SCHEMA_VERSION:
        return validate_binding_proposal_sec_aggregate(proposal)
    return legacy.validate_binding_proposal_any(proposal)
