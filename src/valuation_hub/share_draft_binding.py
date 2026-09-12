"""M23 complete M22 share bridge → Draft binding proposal v0.3.

M23 never rebuilds historical M16/M20 decisions. It wraps an already validated
v0.1 or v0.2 proposal and replaces only `equity.diluted_shares` when the embedded
M22 bridge is complete, reviewed, fresh, and future-bind eligible.
"""
from __future__ import annotations

import copy
import hashlib
import json
from math import isfinite
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.debt_draft_binding import validate_binding_proposal_any as validate_binding_proposal_any_v2
from valuation_hub.draft_binding import DIRECT_BIND, MATERIAL_FIELDS, STATUS
from valuation_hub.valuation_shares import COMPLETE, validate_diluted_share_bridge

SCHEMA_VERSION_V3 = "draft-binding-proposal-v0.3"
POLICY_VERSION_V3 = "evidence-draft-binding-v0.3-diluted-shares"


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


def _eligible_bridge(bridge: dict[str, Any]) -> None:
    validation = validate_diluted_share_bridge(bridge)
    value = bridge.get("candidate_fully_diluted_shares")
    if (
        validation.get("coverage_status") != COMPLETE
        or validation.get("eligible_for_future_direct_bind") is not True
        or bridge.get("class") != "DERIVED_FACT"
        or bridge.get("coverage", {}).get("status") != COMPLETE
        or bridge.get("binding_eligibility", {}).get("eligible_for_future_direct_bind") is not True
    ):
        raise CaseServiceError("only complete reviewed fresh M22 share bridge can bind / 완전·검토완료·최신 M22 share bridge만 바인딩 가능")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)) or value <= 0:
        raise CaseServiceError("eligible diluted-share bridge value invalid / 적격 희석주식 bridge 값 오류")
    assertion = bridge.get("coverage_assertion")
    if not isinstance(assertion, dict) or not isinstance(assertion.get("assertion_sha256"), str):
        raise CaseServiceError("eligible diluted-share bridge coverage assertion missing / 적격 희석주식 bridge coverage 승인 누락")


def _share_projection(bridge: dict[str, Any]) -> dict[str, Any]:
    return {
        "metric": "fully_diluted_shares",
        "value": bridge["candidate_fully_diluted_shares"],
        "unit": "shares",
        "class": "DERIVED_FACT",
        "entity": copy.deepcopy(bridge["entity"]),
        "as_of": bridge["as_of"],
        "coverage_status": bridge["coverage"]["status"],
        "freshness": copy.deepcopy(bridge["base_context"]["freshness"]),
        "context_sha256": bridge["bridge_sha256"],
        "source_bridge_sha256": bridge["bridge_sha256"],
        "base_context_sha256": bridge["base_context"]["context_sha256"],
        "coverage_assertion_sha256": bridge["coverage_assertion"]["assertion_sha256"],
    }


def _share_decision(bridge: dict[str, Any]) -> dict[str, Any]:
    projection = _share_projection(bridge)
    return {
        "field": "equity.diluted_shares",
        "state": DIRECT_BIND,
        "rationale": "complete reviewed fresh M22 diluted-share bridge / 완전·검토완료·최신 M22 희석주식 bridge",
        "source_metric": "fully_diluted_shares",
        "source_class": "DERIVED_FACT",
        "source_freshness": copy.deepcopy(projection["freshness"]),
        "source_context_sha256": bridge["bridge_sha256"],
        "source_bridge_sha256": bridge["bridge_sha256"],
        "base_context_sha256": projection["base_context_sha256"],
        "coverage_assertion_sha256": projection["coverage_assertion_sha256"],
    }


def build_binding_proposal_with_diluted_shares(base_proposal: dict[str, Any], share_bridge: dict[str, Any]) -> dict[str, Any]:
    """Enrich validated M16/M20 proposal with one eligible M22 share bridge."""
    validate_binding_proposal_any_v2(base_proposal)
    _eligible_bridge(share_bridge)

    identity = base_proposal["identity"]
    bridge_entity = share_bridge.get("entity", {})
    if bridge_entity.get("id") != identity.get("entity_id") or bridge_entity.get("financial_scope") != identity.get("financial_scope"):
        raise CaseServiceError("share bridge entity/scope mismatch with base proposal / share bridge entity·scope가 base proposal과 불일치")
    base_as_of = base_proposal.get("policy", {}).get("as_of")
    if not isinstance(base_as_of, str) or share_bridge.get("as_of") != base_as_of:
        raise CaseServiceError("share bridge as_of must equal base proposal as_of / share bridge as_of와 base proposal as_of 불일치")

    matrix = [
        _share_decision(share_bridge) if item["field"] == "equity.diluted_shares" else copy.deepcopy(item)
        for item in base_proposal["draft_input_matrix"]
    ]
    baseline = copy.deepcopy(base_proposal["baseline_context"])
    baseline["fully_diluted_shares"] = _share_projection(share_bridge)
    proposal = {
        "schema_version": SCHEMA_VERSION_V3,
        "status": STATUS,
        "canonical": False,
        "target": copy.deepcopy(base_proposal["target"]),
        "policy": {
            "version": POLICY_VERSION_V3,
            "as_of": base_as_of,
            "base_policy_version": base_proposal["policy"]["version"],
            "direct_bind_requires": [
                "SEMANTIC_EXACT",
                "REVIEWED_DERIVED_FACT",
                "FRESH",
                "COMPLETE_REVIEWED_DILUTION_COVERAGE",
                "HUMAN_COVERAGE_ASSERTION",
            ],
        },
        "identity": copy.deepcopy(identity),
        "baseline_context": baseline,
        "conflicts": copy.deepcopy(base_proposal["conflicts"]),
        "draft_input_matrix": matrix,
        "completeness": _counts(matrix),
        "source_observation_sha256": copy.deepcopy(base_proposal["source_observation_sha256"]),
        "source_share_bridge_sha256": share_bridge["bridge_sha256"],
        "share_bridge": copy.deepcopy(share_bridge),
        "base_proposal": copy.deepcopy(base_proposal),
        "base_proposal_sha256": base_proposal["proposal_sha256"],
        "warning_en": "Share-aware proposal only. It does not mutate a Draft or promote evidence authority.",
        "warning_ko": "Share-aware 제안 전용입니다. Draft를 변경하거나 근거 권위를 승격하지 않습니다.",
        "proposal_sha256": "",
    }
    proposal["proposal_sha256"] = _sha(_without(proposal, "proposal_sha256"))
    validate_binding_proposal_v3(proposal)
    return proposal


def validate_binding_proposal_v3(proposal: dict[str, Any]) -> dict[str, Any]:
    if (
        not isinstance(proposal, dict)
        or proposal.get("schema_version") != SCHEMA_VERSION_V3
        or proposal.get("status") != STATUS
        or proposal.get("canonical") is not False
    ):
        raise CaseServiceError("share-aware binding proposal schema/status invalid / share-aware 바인딩 제안 스키마·상태 오류")
    if proposal.get("target") != {"draft_schema_version": "draft-case-v0.1", "model": "equity_fcff"}:
        raise CaseServiceError("share-aware binding target invalid / share-aware 바인딩 대상 오류")

    base = proposal.get("base_proposal")
    bridge = proposal.get("share_bridge")
    if not isinstance(base, dict) or not isinstance(bridge, dict):
        raise CaseServiceError("share-aware base proposal/bridge missing / share-aware base proposal·bridge 누락")
    validate_binding_proposal_any_v2(base)
    _eligible_bridge(bridge)
    if proposal.get("base_proposal_sha256") != base.get("proposal_sha256"):
        raise CaseServiceError("share-aware base proposal SHA mismatch / share-aware base proposal SHA 불일치")
    if proposal.get("source_share_bridge_sha256") != bridge.get("bridge_sha256"):
        raise CaseServiceError("share bridge SHA lineage mismatch / share bridge SHA lineage 불일치")

    policy = proposal.get("policy")
    if (
        not isinstance(policy, dict)
        or policy.get("version") != POLICY_VERSION_V3
        or policy.get("as_of") != base.get("policy", {}).get("as_of")
        or policy.get("base_policy_version") != base.get("policy", {}).get("version")
    ):
        raise CaseServiceError("share-aware policy/base mismatch / share-aware 정책·base 불일치")
    identity = proposal.get("identity")
    if identity != base.get("identity") or proposal.get("conflicts") != base.get("conflicts") or proposal.get("source_observation_sha256") != base.get("source_observation_sha256"):
        raise CaseServiceError("share-aware proposal/base lineage mismatch / share-aware proposal·base lineage 불일치")
    bridge_entity = bridge.get("entity", {})
    if bridge_entity.get("id") != identity.get("entity_id") or bridge_entity.get("financial_scope") != identity.get("financial_scope"):
        raise CaseServiceError("share bridge identity mismatch / share bridge 식별 불일치")
    if bridge.get("as_of") != policy.get("as_of"):
        raise CaseServiceError("share bridge/proposal as_of mismatch / share bridge·proposal as_of 불일치")

    baseline = proposal.get("baseline_context")
    if not isinstance(baseline, dict):
        raise CaseServiceError("share-aware baseline context invalid / share-aware baseline context 오류")
    expected_baseline = copy.deepcopy(base["baseline_context"])
    expected_baseline["fully_diluted_shares"] = _share_projection(bridge)
    if baseline != expected_baseline:
        raise CaseServiceError("fully diluted share baseline projection mismatch / 완전희석주식 baseline projection 불일치")

    matrix = proposal.get("draft_input_matrix")
    if not isinstance(matrix, list) or {item.get("field") for item in matrix if isinstance(item, dict)} != set(MATERIAL_FIELDS):
        raise CaseServiceError("share-aware binding matrix incomplete / share-aware 바인딩 matrix 불완전")
    base_by = {item["field"]: item for item in base["draft_input_matrix"]}
    by = {item["field"]: item for item in matrix}
    for field in MATERIAL_FIELDS:
        if field != "equity.diluted_shares" and by[field] != base_by[field]:
            raise CaseServiceError("M23 may replace only equity.diluted_shares classification / M23은 equity.diluted_shares 판정만 변경 가능")
    if by["equity.diluted_shares"] != _share_decision(bridge):
        raise CaseServiceError("diluted-share DIRECT_BIND lineage/classification mismatch / 희석주식 DIRECT_BIND lineage·판정 불일치")
    if proposal.get("completeness") != _counts(matrix):
        raise CaseServiceError("share-aware completeness mismatch / share-aware completeness 불일치")

    expected = _sha(_without(proposal, "proposal_sha256"))
    if proposal.get("proposal_sha256") != expected:
        raise CaseServiceError("share-aware binding proposal SHA-256 mismatch / share-aware 바인딩 제안 SHA-256 불일치")
    return {
        "status": "PASS_SHARE_AWARE_BINDING_PROPOSAL_VALIDATION",
        "canonical": False,
        "proposal_sha256": expected,
        "direct_bind_count": proposal["completeness"]["direct_bind_count"],
        "unresolved_count": proposal["completeness"]["unresolved_count"],
    }


def validate_binding_proposal_any(proposal: dict[str, Any]) -> dict[str, Any]:
    if isinstance(proposal, dict) and proposal.get("schema_version") == SCHEMA_VERSION_V3:
        return validate_binding_proposal_v3(proposal)
    return validate_binding_proposal_any_v2(proposal)
