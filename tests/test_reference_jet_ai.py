"""Jet.AI venture reference regression / Jet.AI 벤처 기준 사례 회귀검증."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from valuation_hub.venture import (
    VentureScenario,
    probability_weighted_venture_value,
    required_probability_for_target_value,
)

ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = ROOT / "analyses" / "equities" / "US_JTAI_JET_AI"


def _load() -> dict:
    return json.loads((CASE_DIR / "case_inputs.json").read_text(encoding="utf-8"))


def _scenarios(case: dict) -> list[VentureScenario]:
    return [
        VentureScenario(
            name=item["name"],
            probability=item["probability"],
            terminal_revenue=item["terminal_revenue"],
            ev_to_sales=item["ev_to_sales"],
            terminal_net_debt=item["terminal_net_debt"],
            diluted_shares=item["diluted_shares"],
            discount_rate=item["discount_rate"],
            recovery_equity_value=item["recovery_equity_value"],
        )
        for item in case["scenarios"]
    ]


def test_jet_ai_probability_weighted_reference_value() -> None:
    case = _load()
    result = probability_weighted_venture_value(_scenarios(case), case["holding_period_years"])
    assert result.expected_present_value_per_share == pytest.approx(3.2467821083)


def test_jet_ai_result_file_matches_engine() -> None:
    case = _load()
    stored = json.loads((CASE_DIR / "valuation_result.json").read_text(encoding="utf-8"))
    result = probability_weighted_venture_value(_scenarios(case), case["holding_period_years"])
    assert result.expected_present_value_per_share == pytest.approx(stored["probability_weighted"]["expected_present_value_per_share"])
    by_name = {item.name: item for item in result.scenario_results}
    for name in ("FAILURE", "SURVIVAL", "BREAKOUT"):
        assert by_name[name].present_value_per_share == pytest.approx(stored["scenario_results"][name]["present_value_per_share"])


def test_jet_ai_reverse_breakout_probability() -> None:
    case = _load()
    result = probability_weighted_venture_value(_scenarios(case), case["holding_period_years"])
    by_name = {item.name: item for item in result.scenario_results}
    survival_weighted = 0.30 * by_name["SURVIVAL"].present_value_per_share
    required = required_probability_for_target_value(
        target_value_per_share=case["market"]["price"],
        fixed_weighted_value_per_share=survival_weighted,
        conditional_present_value_per_share=by_name["BREAKOUT"].present_value_per_share,
    )
    assert required == pytest.approx(0.0219497023)


def test_jet_ai_model_selection_rejects_reported_pe() -> None:
    manifest = json.loads((CASE_DIR / "evidence_manifest.json").read_text(encoding="utf-8"))
    assert manifest["model_selection"] == "PROBABILITY_WEIGHTED_VENTURE_OPTION_MODEL"
    assert manifest["model_rejection"]["standard_per_dcf"] == "REJECTED"
