"""Static, non-promoting goal-delivery plan validation.

This validator checks the plan's structural consistency with the repository,
not user-local original evidence, issuer rates, approval or economic value.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class GoalPlanError(ValueError):
    """A governance-plan assertion is unsupported or inconsistent."""


PLAN_PATH = "governance/goal_delivery_plan.json"
SCHEMA = "vih-goal-delivery-plan-v0.1"
PRIORITIES = tuple(f"P{i}" for i in range(6))
ALLOWED_STATES = {
    "CODE_MERGED_LOCAL_RUN_PENDING",
    "BLOCKED_REAL_EVIDENCE",
    "WAITING_DEPENDENCY",
    "NOT_YET_VALIDATED",
    "VERIFIED",
    "COMPLETE",
}


def _relative_existing_file(root: Path, raw: str) -> Path:
    if not isinstance(raw, str) or not raw or raw.startswith(("/", "\\")):
        raise GoalPlanError("invalid referenced file path")
    candidate = (root / raw).resolve()
    if not candidate.is_relative_to(root.resolve()) or not candidate.is_file():
        raise GoalPlanError(f"missing/unsafe plan reference: {raw}")
    return candidate


def check_goal_plan(repo_root: Path, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fail closed on inconsistent claims, missing files and priority drift."""
    repo = repo_root.resolve()
    if payload is None:
        try:
            payload = json.loads(_relative_existing_file(repo, PLAN_PATH).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise GoalPlanError("goal delivery plan cannot be read") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA:
        raise GoalPlanError("goal plan schema mismatch")

    for raw in payload.get("canonical_policy_paths", []):
        _relative_existing_file(repo, raw)
    if len(payload.get("canonical_policy_paths", [])) < 4:
        raise GoalPlanError("goal plan misses canonical policy documents")

    stages = payload.get("priorities")
    if not isinstance(stages, list) or [x.get("id") for x in stages if isinstance(x, dict)] != list(PRIORITIES):
        raise GoalPlanError("exact ordered P0..P5 goal stages required")
    if len(stages) != len(PRIORITIES):
        raise GoalPlanError("missing/duplicate goal stage")
    for stage in stages:
        if stage.get("status") not in ALLOWED_STATES or not stage.get("exit_gate") or not stage.get("next_action"):
            raise GoalPlanError("stage status/action/proof gate missing")
        paths = stage.get("required_paths")
        if not isinstance(paths, list) or not paths:
            raise GoalPlanError("each stage requires repository evidence paths")
        for raw in paths:
            _relative_existing_file(repo, raw)
        if stage["status"] == "COMPLETE" and not stage.get("verified_evidence_refs"):
            raise GoalPlanError("completed stage has no independent evidence reference")

    target = payload.get("case_target", {})
    if (target.get("case_id") != "US_INGR_INGREDION"
        or target.get("entity_id") != "SEC_CIK:0001046257"
        or target.get("valuation_as_of") != "2026-09-14"
        or target.get("scope") != "AS_REPORTED"
        or target.get("required_material_fields") != 13):
        raise GoalPlanError("first real-case identity/scope contract changed")

    try:
        registry = json.loads(_relative_existing_file(repo, "registry/cases.json").read_text(encoding="utf-8"))
        admitted = any(x.get("case_id") == "US_INGR_INGREDION" for x in registry["cases"])
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise GoalPlanError("canonical case registry unreadable") from exc
    if target.get("registry_admitted") is not admitted:
        raise GoalPlanError("registry admission claim differs from real repository")

    checkpoint = payload.get("user_reported_checkpoint", {})
    ready, required, missing = (
        checkpoint.get("wacc_candidates"),
        checkpoint.get("wacc_required"),
        checkpoint.get("missing"),
    )
    if (not isinstance(ready, int) or isinstance(ready, bool)
        or not isinstance(required, int) or isinstance(required, bool)
        or required != 7 or ready < 0 or ready > required
        or not isinstance(missing, list)
        or len(missing) != required - ready
        or len(set(missing)) != len(missing)
        or not set(missing).issubset({
            "risk_free_rate", "equity_risk_premium", "levered_beta",
            "pre_tax_cost_of_debt", "equity_market_value", "debt_market_value",
            "tax_rate",
        })):
        raise GoalPlanError("source readiness inventory is internally inconsistent")
    if checkpoint.get("observation_type") != "USER_SUPPLIED_LOCAL_CLI_OUTPUT_NOT_REPLAYED_IN_GITHUB_CI":
        raise GoalPlanError("source evidence cannot silently be called CI-verified")
    if checkpoint.get("completed_valuation") is not False or checkpoint.get("reviewed_wacc") is not False:
        raise GoalPlanError("unreviewed source checkpoint cannot claim a reviewed valuation")
    if checkpoint.get("status") != "HOLD_REAL_INGR_M24_WACC_INPUT_GAPS":
        raise GoalPlanError("historical checkpoint HOLD status changed without new contract")

    claims = payload.get("claims", {})
    if claims.get("reporting_not_approval") is not True:
        raise GoalPlanError("goal-check must remain non-promoting")
    if claims.get("first_real_case_complete") is True and (not admitted or stages[2]["status"] != "COMPLETE"):
        raise GoalPlanError("unsupported first real-case completion claim")
    if claims.get("multi_asset_goal_complete") is True and stages[5]["status"] != "COMPLETE":
        raise GoalPlanError("unsupported multi-asset completion claim")

    iteration = payload.get("current_iteration", {})
    if iteration.get("next_priority_id") not in PRIORITIES:
        raise GoalPlanError("next iteration must target a known priority")

    return {
        "status": "PLAN_CONTRACT_VALID_REAL_CASE_NOT_YET_COMPLETE",
        "non_promoting": True,
        "case_admitted_to_registry": admitted,
        "current_wacc_candidates_user_reported": ready,
        "wacc_required": required,
        "missing_inputs_user_reported": missing,
        "checkpoint_provenance": checkpoint["observation_type"],
        "next_priority": iteration["next_priority_id"],
        "remaining_priority_ids": [x["id"] for x in stages if x["status"] != "COMPLETE"],
        "warning": "Repository plan checks do not verify source bytes, approvals, model quality, or any real valuation.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Non-promoting goal delivery contract validation")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = check_goal_plan(args.repo_root)
    except (GoalPlanError, OSError, TypeError, KeyError) as exc:
        result = {"status": "ERROR", "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return int(result["status"] == "ERROR")


if __name__ == "__main__":
    raise SystemExit(main())
