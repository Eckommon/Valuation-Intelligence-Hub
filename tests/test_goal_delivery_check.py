"""Plan must be truthful and link only to existing source-controlled files."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from valuation_hub.goal_delivery_check import GoalPlanError, check_goal_plan

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "governance" / "goal_delivery_plan.json").read_text(encoding="utf-8"))


def test_actual_repository_goal_plan_valid_and_non_promoting():
    result = check_goal_plan(ROOT)
    assert result["status"] == "PLAN_CONTRACT_VALID_REAL_CASE_NOT_YET_COMPLETE"
    assert result["case_admitted_to_registry"] is False
    assert result["current_wacc_candidates_user_reported"] == 5
    assert result["missing_inputs_user_reported"] == ["pre_tax_cost_of_debt", "tax_rate"]
    assert result["checkpoint_provenance"] == "USER_SUPPLIED_LOCAL_CLI_OUTPUT_NOT_REPLAYED_IN_GITHUB_CI"
    assert result["non_promoting"] is True
    assert result["next_priority"] == "P1"


@pytest.mark.parametrize("tamper", [
    lambda x: x.update(schema_version="unknown"),
    lambda x: x["priorities"].pop(),
    lambda x: x["priorities"][1].update(id="P0"),
    lambda x: x["priorities"][0].update(required_paths=["../outside.txt"]),
    lambda x: x["priorities"][0].update(required_paths=["src/valuation_hub/nonexistent_module.py"]),
    lambda x: x["priorities"][1].update(status="COMPLETE"),
    lambda x: x["user_reported_checkpoint"].update(wacc_candidates=7),
    lambda x: x["user_reported_checkpoint"].update(observation_type="CI_VERIFIED"),
    lambda x: x["user_reported_checkpoint"].update(reviewed_wacc=True),
    lambda x: x["case_target"].update(registry_admitted=True),
    lambda x: x["claims"].update(first_real_case_complete=True),
    lambda x: x["claims"].update(multi_asset_goal_complete=True),
    lambda x: x["claims"].update(reporting_not_approval=False),
    lambda x: x["current_iteration"].update(next_priority_id="P99"),
])
def test_plan_false_claim_or_missing_gate_is_rejected(tamper):
    plan = copy.deepcopy(DATA)
    tamper(plan)
    with pytest.raises(GoalPlanError):
        check_goal_plan(ROOT, plan)


def test_completed_stage_with_source_reference_still_not_final_valution():
    plan = copy.deepcopy(DATA)
    plan["priorities"][0]["status"] = "COMPLETE"
    plan["priorities"][0]["verified_evidence_refs"] = ["https://github.com/Eckommon/Valuation-Intelligence-Hub/pull/174"]
    result = check_goal_plan(ROOT, plan)
    assert result["status"] == "PLAN_CONTRACT_VALID_REAL_CASE_NOT_YET_COMPLETE"
    assert result["case_admitted_to_registry"] is False


def test_policy_docs_issuer_model_and_original_audit_are_present():
    for path in (
        ROOT / "AGENTS.md",
        ROOT / "docs" / "GOAL_DELIVERY_LOOP.md",
        ROOT / "src" / "valuation_hub" / "ingr_r8_m24_evidence_audit.py",
        ROOT / ".github" / "workflows" / "ci.yml",
    ):
        assert path.is_file()
