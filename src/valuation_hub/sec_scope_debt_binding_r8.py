"""M30-R8SCOPE: additive SEC aggregate-debt v0.2 binding with source-bound scopes.

This successor never mutates source cash AS_REPORTED, debt CFS, or R6
ASSUMPTION bytes. Its target identity inherits the reviewed cash observation,
and it exposes the original debt scope in both its projection and full proof.
"""
from __future__ import annotations

import copy
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub import debt_draft_binding_m30 as prior
from valuation_hub.draft_binding import (
    DIRECT_BIND, MATERIAL_FIELDS, STATUS, build_binding_proposal, validate_binding_proposal,
)
from valuation_hub.sec_scope_reconciliation_r8 import (
    BRIDGE_SCHEMA, build_scope_bridge, validate_scope_bridge,
)

SCHEMA = "draft-binding-proposal-v0.2-sec-debt-scoped-r8"
POLICY = "evidence-draft-binding-v0.2-sec-consolidated-scope-r8"


def _projection(bridge: dict[str, Any]) -> dict[str, Any]:
    context = bridge["debt_context"]
    projected = prior._projection(context)
    projected["source_financial_scope"] = "CFS"
    projected["binding_target_financial_scope"] = "AS_REPORTED"
    projected["scope_bridge_sha256"] = bridge["bridge_sha256"]
    projected["source_review_authority"] = "AI"
    return projected


def _decision(bridge: dict[str, Any]) -> dict[str, Any]:
    debt = bridge["debt_context"]
    if debt["freshness"]["status"] != "FRESH" or debt["binding_eligibility"]["eligible"] is not True:
        raise CaseServiceError("scope bridge does not waive debt freshness or review eligibility")
    return {
        "field": "equity.debt", "state": DIRECT_BIND,
        "rationale": "Tier-A issuer filing ties reviewed CFS debt to AS_REPORTED cash valuation scope; AI debt review retained",
        "source_metric": "interest_bearing_debt",
        "source_class": "DERIVED_FACT",
        "source_review_authority": "AI",
        "source_financial_scope": "CFS",
        "target_financial_scope": "AS_REPORTED",
        "source_route": "SOURCE_BOUND_SEC_CONSOLIDATED_SCOPE",
        "source_context_sha256": debt["context_sha256"],
        "source_debt_sha256": debt["source_debt_sha256"],
        "source_debt_profile_sha256": debt["source_debt_profile_sha256"],
        "source_freshness": copy.deepcopy(debt["freshness"]),
        "source_scope_bridge_sha256": bridge["bridge_sha256"],
        "review_assertion_sha256": debt["review_assertion_sha256"],
        "date_assertion_sha256": None,
    }


def _make(bridge: dict[str, Any]) -> dict[str, Any]:
    validate_scope_bridge(bridge)
    base = build_binding_proposal(
        [bridge["cash"]], as_of=bridge["as_of"], max_age_days=550
    )
    context = bridge["debt_context"]
    if (base["identity"] != {"entity_id":bridge["entity_id"],
                             "financial_scope":"AS_REPORTED","monetary_unit":"USD"}
        or context["unit"] != "USD"
        or context["policy"]["max_age_days"] != 550
        or context["policy"]["as_of"] != base["policy"]["as_of"]):
        raise CaseServiceError("scope bridge base cash identity or debt policy mismatch")
    matrix = [_decision(bridge) if row["field"] == "equity.debt"
              else copy.deepcopy(row) for row in base["draft_input_matrix"]]
    baseline = copy.deepcopy(base["baseline_context"])
    baseline["interest_bearing_debt"] = _projection(bridge)
    out = {
        "schema_version": SCHEMA, "status": STATUS, "canonical": False,
        "target": copy.deepcopy(base["target"]),
        "policy": {
            "version": POLICY, "as_of": base["policy"]["as_of"],
            "max_age_days": base["policy"]["max_age_days"],
            "direct_bind_requires": [
                "SOURCE_BOUND_2026Q2_SEC_CONSOLIDATED_SCOPE",
                "UNCHANGED_SOURCE_SCOPE_AND_SHA",
                "AI_REVIEWED_SEC_DEBT",
                "FRESH",
                "EXACT_ENTITY_AND_FILING",
            ],
        },
        "identity": copy.deepcopy(base["identity"]),
        "baseline_context": baseline,
        "conflicts": copy.deepcopy(base["conflicts"]),
        "draft_input_matrix": matrix,
        "completeness": prior._counts(matrix),
        "source_observation_sha256": copy.deepcopy(base["source_observation_sha256"]),
        "source_debt_context_sha256": context["context_sha256"],
        "source_scope_bridge_sha256": bridge["bridge_sha256"],
        "debt_binding_context": copy.deepcopy(context),
        "scope_bridge": copy.deepcopy(bridge),
        "base_v01_proposal": copy.deepcopy(base),
        "warning_en": "Noncanonical; independently source-reconciled CFS/AS_REPORTED scope, original source scopes unchanged.",
        "warning_ko": "비정식 제안. SEC 원문으로 범위 정합성만 입증하며 원본 범위를 변경하지 않습니다.",
        "proposal_sha256": "",
    }
    out["proposal_sha256"] = prior._sha(prior._without(out, "proposal_sha256"))
    return out


def build_scope_bridged_debt_proposal(bridge: dict[str, Any]) -> dict[str, Any]:
    out = _make(bridge)
    validate_scope_bridged_debt_proposal(out)
    return out


def validate_scope_bridged_debt_proposal(value: dict[str, Any]) -> dict[str, Any]:
    if (not isinstance(value, dict)
        or value.get("schema_version") != SCHEMA
        or not isinstance(value.get("scope_bridge"), dict)):
        raise CaseServiceError("M30-R8SCOPE v0.2 source-bridged proposal required")
    rebuilt = _make(value["scope_bridge"])
    if value != rebuilt:
        raise CaseServiceError("M30-R8SCOPE full v0.2 source/decision/policy/lineage/hash mismatch")
    return {"status": "PASS_R8_SCOPE_BRIDGED_SEC_DEBT_V02",
            "proposal_sha256": value["proposal_sha256"],
            "scope_bridge_sha256": value["source_scope_bridge_sha256"],
            "target_scope": "AS_REPORTED", "source_debt_scope": "CFS",
            "source_debt_class": "DERIVED_FACT", "canonical": False}
