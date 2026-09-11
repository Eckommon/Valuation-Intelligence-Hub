"""Reviewed promotion protocol tests / 검토 기반 승격 프로토콜 테스트."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_service import template
from valuation_hub.promotion import (
    assess_candidate,
    build_candidate,
    promotion_check,
    validate_candidate,
)

ROOT = Path(__file__).resolve().parents[1]


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ready_candidate(model: str = "equity_fcff") -> dict:
    candidate = build_candidate(template(model, ROOT))
    draft = candidate["draft"]
    if model == "equity_fcff":
        observed = {
            "market_price": draft["market_price"],
            "equity.diluted_shares": draft["equity"]["diluted_shares"],
            "equity.debt": draft["equity"]["debt"],
            "equity.cash": draft["equity"]["cash"],
            "equity.minority_interest": draft["equity"]["minority_interest"],
        }
    else:
        observed = {"market_price": draft["market_price"]}

    evidence = []
    for binding in candidate["input_governance"]:
        path = binding["path"]
        if path in observed:
            claim_id = "claim_" + path.replace(".", "_").replace("[", "_").replace("]", "")
            binding["class"] = "FACT"
            binding["claim_ids"] = [claim_id]
            binding["rationale"] = "Observed input supported by linked evidence."
            evidence.append(
                {
                    "claim_id": claim_id,
                    "class": "FACT",
                    "metric": path,
                    "value": observed[path],
                    "unit": draft["currency"],
                    "as_of": "2026-09-11",
                    "status": "CURRENT",
                    "waiver": None,
                    "source": {
                        "publisher": "Test primary evidence",
                        "locator": f"https://example.invalid/{claim_id}",
                        "tier": "B",
                        "type": "test_fixture",
                        "published_at": "2026-09-11",
                    },
                }
            )
        else:
            binding["class"] = "ASSUMPTION"
            binding["claim_ids"] = []
            binding["rationale"] = "Explicit forward-model assumption for test review."
    candidate["evidence"] = evidence
    return candidate


def _approve(candidate: dict) -> dict:
    assessment = validate_candidate(candidate)
    candidate["review"] = {
        "decision": "APPROVE",
        "reviewer": "human-reviewer",
        "reviewed_at": "2026-09-11T14:20:00+09:00",
        "rationale": "Evidence and assumptions reviewed for repository PR preparation.",
        "scope_sha256": assessment["review_scope_sha256"],
    }
    return candidate


def test_candidate_build_is_deterministic_and_enumerates_material_inputs() -> None:
    draft = template("equity_fcff", ROOT)
    left = build_candidate(draft)
    right = build_candidate(draft)
    assert left == right
    paths = [item["path"] for item in left["input_governance"]]
    assert "market_price" in paths
    assert "equity.diluted_shares" in paths
    assert any(path.endswith(".wacc") for path in paths)
    assert not any(path.endswith(".year") for path in paths)
    assert all(item["class"] == "UNKNOWN" for item in left["input_governance"])


def test_candidate_skeleton_fails_closed_until_governance_is_completed() -> None:
    candidate = build_candidate(template("equity_fcff", ROOT))
    assessment = assess_candidate(candidate)
    assert assessment["ready_for_review"] is False
    assert any(item.startswith("INPUT_CLASS_INVALID") for item in assessment["blockers"])
    with pytest.raises(CaseServiceError, match="review gate blocked"):
        validate_candidate(candidate)


def test_ready_equity_candidate_requires_observed_facts_and_exact_evidence_values() -> None:
    candidate = _ready_candidate("equity_fcff")
    assessment = validate_candidate(candidate)
    assert assessment["ready_for_review"] is True
    assert assessment["required_observed_fact_count"] == 5
    assert len(assessment["review_scope_sha256"]) == 64

    evasion = copy.deepcopy(candidate)
    market_binding = next(item for item in evasion["input_governance"] if item["path"] == "market_price")
    market_binding["class"] = "ASSUMPTION"
    market_binding["claim_ids"] = []
    market_binding["rationale"] = "Try to evade evidence."
    blocked = assess_candidate(evasion)
    assert "OBSERVED_INPUT_MUST_BE_FACT:market_price" in blocked["blockers"]

    mismatch = copy.deepcopy(candidate)
    mismatch["evidence"][0]["value"] = float(mismatch["evidence"][0]["value"]) + 1
    blocked = assess_candidate(mismatch)
    assert any(item.startswith("EVIDENCE_VALUE_MISMATCH") for item in blocked["blockers"])


def test_stale_or_tier_d_fact_evidence_is_blocked_by_existing_evidence_gate() -> None:
    stale = _ready_candidate("venture_probability")
    stale["evidence"][0]["status"] = "STALE"
    assessment = assess_candidate(stale)
    assert any("EVIDENCE_GATE:STALE" in item for item in assessment["blockers"])

    tier_d = _ready_candidate("venture_probability")
    tier_d["evidence"][0]["source"]["tier"] = "D"
    assessment = assess_candidate(tier_d)
    assert any("TIER_D_CANNOT_CANONICALIZE_FACT" in item for item in assessment["blockers"])


def test_missing_or_duplicate_binding_fails_closed() -> None:
    candidate = _ready_candidate("venture_probability")
    candidate["input_governance"].pop()
    assessment = assess_candidate(candidate)
    assert any(item.startswith("MISSING_BINDING") for item in assessment["blockers"])

    duplicate = _ready_candidate("venture_probability")
    duplicate["input_governance"].append(copy.deepcopy(duplicate["input_governance"][0]))
    assessment = assess_candidate(duplicate)
    assert any(item.startswith("DUPLICATE_BINDING") for item in assessment["blockers"])


def test_explicit_human_review_hash_is_required_and_only_yields_pr_readiness() -> None:
    candidate = _ready_candidate("equity_fcff")
    with pytest.raises(CaseServiceError, match="APPROVE"):
        promotion_check(candidate)

    approved = _approve(candidate)
    result = promotion_check(approved)
    assert result["status"] == "REVIEW_APPROVED_READY_FOR_PR"
    assert result["promotion_ready"] is True
    assert result["canonical"] is False
    assert "PR" in result["next_action_en"]


def test_post_review_mutation_invalidates_approval_hash() -> None:
    candidate = _approve(_ready_candidate("equity_fcff"))
    assumption = next(item for item in candidate["input_governance"] if item["class"] == "ASSUMPTION")
    assumption["rationale"] += " Changed after approval."
    with pytest.raises(CaseServiceError, match="hash mismatch"):
        promotion_check(candidate)


def test_promotion_protocol_never_mutates_canonical_repository_state() -> None:
    protected = [
        ROOT / "registry" / "cases.json",
        ROOT / "analyses" / "equities" / "KR_010120_LS_ELECTRIC" / "case_inputs.json",
        ROOT / "analyses" / "equities" / "KR_010120_LS_ELECTRIC" / "valuation_result.json",
        ROOT / "analyses" / "equities" / "KR_010120_LS_ELECTRIC" / "evidence_manifest.json",
    ]
    before = {path: _digest(path) for path in protected}
    candidate = _approve(_ready_candidate("equity_fcff"))
    promotion_check(candidate)
    after = {path: _digest(path) for path in protected}
    assert before == after
