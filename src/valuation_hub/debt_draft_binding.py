"""M20 debt-aware Draft binding proposal v0.2 / debt-aware Draft 바인딩 제안.

The original M16 v0.1 proposal builder is intentionally untouched. M20 wraps a
validated v0.1 proposal with one validated M20 debt-binding context and replaces
only the `equity.debt` classification.
"""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.debt_binding import FRESH, STALE_BLOCKED, validate_debt_binding_context
from valuation_hub.draft_binding import (
    DIRECT_BIND,
    MATERIAL_FIELDS,
    STATUS,
    build_binding_proposal,
    validate_binding_proposal,
)

SCHEMA_VERSION_V2 = "draft-binding-proposal-v0.2"
POLICY_VERSION_V2 = "evidence-draft-binding-v0.2-debt"


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    out = copy.deepcopy(value)
    out.pop(key, None)
    return out


def _counts(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    state_counts: dict[str, int] = {}
    for item in matrix:
        state_counts[item["state"]] = state_counts.get(item["state"], 0) + 1
    return {
        "material_field_count": len(MATERIAL_FIELDS),
        "classified_field_count": len(matrix),
        "state_counts": state_counts,
        "direct_bind_count": state_counts.get(DIRECT_BIND, 0),
        "unresolved_count": sum(count for state, count in state_counts.items() if state != DIRECT_BIND),
    }


def _debt_projection(context: dict[str, Any]) -> dict[str, Any]:
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
        "date_resolution": copy.deepcopy(context["date_resolution"]),
    }


def _debt_decision(context: dict[str, Any]) -> dict[str, Any]:
    fresh = context["freshness"]["status"]
    eligible = context["binding_eligibility"]["eligible"] is True and fresh == FRESH
    state = DIRECT_BIND if eligible else STALE_BLOCKED
    rationale = (
        "complete reviewed fresh M19 interest-bearing debt / 완전·검토완료·최신 M19 이자부채"
        if eligible
        else "complete reviewed debt exceeds freshness policy / 완전·검토완료 debt가 최신성 정책 초과"
    )
    return {
        "field": "equity.debt",
        "state": state,
        "rationale": rationale,
        "source_metric": "interest_bearing_debt",
        "source_class": "DERIVED_FACT",
        "source_freshness": copy.deepcopy(context["freshness"]),
        "source_context_sha256": context["context_sha256"],
        "source_debt_sha256": context["source_debt_sha256"],
        "date_assertion_sha256": context["date_resolution"].get("date_assertion_sha256"),
    }


def build_binding_proposal_with_debt(
    observations: list[dict[str, Any]],
    debt_context: dict[str, Any],
    *,
    as_of: str,
    max_age_days: int = 550,
) -> dict[str, Any]:
    base = build_binding_proposal(observations, as_of=as_of, max_age_days=max_age_days)
    validate_debt_binding_context(debt_context)
    identity = base["identity"]
    if debt_context["entity"] != {"id": identity["entity_id"], "financial_scope": identity["financial_scope"]}:
        raise CaseServiceError("debt context entity/scope mismatch with base proposal / debt context entity·scope가 base proposal과 불일치")
    monetary = identity.get("monetary_unit")
    if monetary is not None and debt_context["unit"] != monetary:
        raise CaseServiceError("debt context unit mismatch with base proposal / debt context unit이 base proposal과 불일치")

    matrix = [
        _debt_decision(debt_context) if item["field"] == "equity.debt" else copy.deepcopy(item)
        for item in base["draft_input_matrix"]
    ]
    baseline = copy.deepcopy(base["baseline_context"])
    baseline["interest_bearing_debt"] = _debt_projection(debt_context)
    proposal = {
        "schema_version": SCHEMA_VERSION_V2,
        "status": STATUS,
        "canonical": False,
        "target": copy.deepcopy(base["target"]),
        "policy": {
            "version": POLICY_VERSION_V2,
            "as_of": as_of,
            "max_age_days": max_age_days,
            "direct_bind_requires": [
                "SEMANTIC_EXACT",
                "REVIEWED_DERIVED_FACT",
                "FRESH",
                "PERIOD_COMPATIBLE",
                "DEBT_COMPLETE_CORE_COMPONENTS",
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
        "warning_en": "Debt-aware proposal only. It does not mutate a Draft or promote evidence authority.",
        "warning_ko": "Debt-aware 제안 전용입니다. Draft를 변경하거나 근거 권위를 승격하지 않습니다.",
        "proposal_sha256": "",
    }
    proposal["proposal_sha256"] = _sha(_without(proposal, "proposal_sha256"))
    validate_binding_proposal_v2(proposal)
    return proposal


def validate_binding_proposal_v2(proposal: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(proposal, dict) or proposal.get("schema_version") != SCHEMA_VERSION_V2 or proposal.get("status") != STATUS or proposal.get("canonical") is not False:
        raise CaseServiceError("debt-aware binding proposal schema/status invalid / debt-aware 바인딩 제안 스키마·상태 오류")
    if proposal.get("target") != {"draft_schema_version": "draft-case-v0.1", "model": "equity_fcff"}:
        raise CaseServiceError("debt-aware binding target invalid / debt-aware 바인딩 대상 오류")

    base = proposal.get("base_v01_proposal")
    if not isinstance(base, dict):
        raise CaseServiceError("base v0.1 proposal missing / base v0.1 proposal 누락")
    validate_binding_proposal(base)
    if proposal.get("identity") != base.get("identity") or proposal.get("conflicts") != base.get("conflicts") or proposal.get("source_observation_sha256") != base.get("source_observation_sha256"):
        raise CaseServiceError("debt-aware proposal/base identity lineage mismatch / debt-aware proposal·base lineage 불일치")

    policy = proposal.get("policy")
    if not isinstance(policy, dict) or policy.get("version") != POLICY_VERSION_V2 or policy.get("as_of") != base.get("policy", {}).get("as_of") or policy.get("max_age_days") != base.get("policy", {}).get("max_age_days"):
        raise CaseServiceError("debt-aware policy/base mismatch / debt-aware policy·base 불일치")

    full_context = proposal.get("debt_binding_context")
    if not isinstance(full_context, dict):
        raise CaseServiceError("full debt binding context missing / 전체 debt 바인딩 context 누락")
    validate_debt_binding_context(full_context)
    context_sha = full_context["context_sha256"]
    if proposal.get("source_debt_context_sha256") != context_sha:
        raise CaseServiceError("debt context SHA lineage mismatch / debt context SHA lineage 불일치")

    baseline = proposal.get("baseline_context")
    if not isinstance(baseline, dict):
        raise CaseServiceError("debt-aware baseline context invalid / debt-aware baseline context 오류")
    debt = baseline.get("interest_bearing_debt")
    if debt != _debt_projection(full_context):
        raise CaseServiceError("debt baseline projection mismatch / debt baseline projection 불일치")

    identity = proposal["identity"]
    if full_context.get("entity") != {"id": identity.get("entity_id"), "financial_scope": identity.get("financial_scope")} or full_context.get("unit") != identity.get("monetary_unit"):
        raise CaseServiceError("debt context identity/unit mismatch / debt context 식별·unit 불일치")

    matrix = proposal.get("draft_input_matrix")
    if not isinstance(matrix, list) or {item.get("field") for item in matrix if isinstance(item, dict)} != set(MATERIAL_FIELDS):
        raise CaseServiceError("debt-aware binding matrix incomplete / debt-aware 바인딩 matrix 불완전")
    base_by = {item["field"]: item for item in base["draft_input_matrix"]}
    by = {item["field"]: item for item in matrix}
    for field in MATERIAL_FIELDS:
        if field != "equity.debt" and by[field] != base_by[field]:
            raise CaseServiceError("M20 may replace only equity.debt classification / M20은 equity.debt 판정만 변경 가능")

    decision = by["equity.debt"]
    expected_decision = _debt_decision(full_context)
    if decision != expected_decision:
        raise CaseServiceError("debt DIRECT_BIND lineage/classification mismatch / debt DIRECT_BIND lineage·판정 불일치")
    if proposal.get("completeness") != _counts(matrix):
        raise CaseServiceError("debt-aware completeness mismatch / debt-aware completeness 불일치")

    expected = _sha(_without(proposal, "proposal_sha256"))
    if proposal.get("proposal_sha256") != expected:
        raise CaseServiceError("debt-aware binding proposal SHA-256 mismatch / debt-aware 바인딩 제안 SHA-256 불일치")
    return {
        "status": "PASS_DEBT_AWARE_BINDING_PROPOSAL_VALIDATION",
        "canonical": False,
        "proposal_sha256": expected,
        "direct_bind_count": proposal["completeness"]["direct_bind_count"],
        "unresolved_count": proposal["completeness"]["unresolved_count"],
    }


def validate_binding_proposal_any(proposal: dict[str, Any]) -> dict[str, Any]:
    if isinstance(proposal, dict) and proposal.get("schema_version") == SCHEMA_VERSION_V2:
        return validate_binding_proposal_v2(proposal)
    return validate_binding_proposal(proposal)
