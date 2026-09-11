"""User Draft service tests / 사용자 Draft 서비스 테스트."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_service import run_draft, template, validate_draft

ROOT = Path(__file__).resolve().parents[1]


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_equity_template_validates_and_runs_through_shared_kernel() -> None:
    payload = template("equity_fcff", ROOT)
    normalized = validate_draft(payload)
    result = run_draft(payload)
    assert normalized["canonical"] is False
    assert normalized["status"] == "DRAFT_USER_SUPPLIED"
    assert result["canonical"] is False
    assert result["grounding"] == "USER_SUPPLIED_UNVERIFIED"
    assert result["runtime"]["scenarios"]["BASE"]["value_per_share"] > 0


def test_venture_template_validates_and_runs() -> None:
    payload = template("venture_probability", ROOT)
    result = run_draft(payload)
    assert result["status"] == "DRAFT_USER_SUPPLIED"
    assert result["runtime"]["expected_present_value_per_share"] > 0
    assert set(result["runtime"]["scenarios"]) == {"FAILURE", "SURVIVAL", "BREAKOUT"}


def test_equity_draft_fails_closed_when_terminal_growth_reaches_wacc() -> None:
    payload = template("equity_fcff", ROOT)
    payload["equity"]["scenarios"]["BASE"]["terminal_growth"] = payload["equity"]["scenarios"]["BASE"]["wacc"]
    with pytest.raises(CaseServiceError, match="terminal growth"):
        validate_draft(payload)


def test_venture_draft_fails_closed_on_probability_sum() -> None:
    payload = template("venture_probability", ROOT)
    payload["venture"]["scenarios"][0]["probability"] = 0.9
    with pytest.raises(CaseServiceError, match="probabilities must sum"):
        run_draft(payload)


def test_draft_rejects_nonfinite_and_unsorted_years() -> None:
    payload = template("equity_fcff", ROOT)
    bad = copy.deepcopy(payload)
    bad["market_price"] = float("nan")
    with pytest.raises(CaseServiceError, match="finite"):
        validate_draft(bad)

    bad = copy.deepcopy(payload)
    years = bad["equity"]["scenarios"]["BASE"]["years"]
    years[0]["year"], years[1]["year"] = years[1]["year"], years[0]["year"]
    with pytest.raises(CaseServiceError, match="ascending"):
        validate_draft(bad)


def test_draft_execution_never_mutates_canonical_repository_state() -> None:
    protected = [
        ROOT / "registry" / "cases.json",
        ROOT / "analyses" / "equities" / "KR_010120_LS_ELECTRIC" / "case_inputs.json",
        ROOT / "analyses" / "equities" / "KR_010120_LS_ELECTRIC" / "valuation_result.json",
        ROOT / "analyses" / "equities" / "KR_010120_LS_ELECTRIC" / "evidence_manifest.json",
    ]
    before = {path: _digest(path) for path in protected}
    run_draft(template("equity_fcff", ROOT))
    run_draft(template("venture_probability", ROOT))
    after = {path: _digest(path) for path in protected}
    assert before == after
