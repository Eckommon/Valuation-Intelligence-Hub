"""LS Eco Energy reference-case regression / LS에코에너지 기준 사례 회귀검증."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from valuation_hub.scenario import ForecastYear, ScenarioDefinition, run_fcff_scenario

ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = ROOT / "analyses" / "equities" / "KR_229640_LS_ECO_ENERGY"


def _load() -> dict:
    return json.loads((CASE_DIR / "case_inputs.json").read_text(encoding="utf-8"))


def _build_forecast(case: dict, scenario_name: str) -> list[ForecastYear]:
    scenario = case["scenarios"][scenario_name]
    prior_nwc = case["opening_core_nwc"]["value"]
    rows: list[ForecastYear] = []
    for item in scenario["years"]:
        revenue = item["revenue"]
        current_nwc = revenue * item["nwc_to_sales"]
        rows.append(ForecastYear(year=item["year"], revenue=revenue, ebit_margin=item["ebit_margin"], tax_rate=item["tax_rate"], depreciation_amortization=revenue * item["da_to_sales"], capex=revenue * item["capex_to_sales"], delta_nwc=current_nwc - prior_nwc))
        prior_nwc = current_nwc
    return rows


def _run(case: dict, scenario_name: str):
    scenario = case["scenarios"][scenario_name]
    definition = ScenarioDefinition(name=scenario_name, wacc=scenario["wacc"], terminal_growth=scenario["terminal_growth"], diluted_shares=case["market"]["diluted_shares"], debt=scenario["future_net_debt"], cash=0.0, minority_interest=scenario["future_minority_interest"])
    return run_fcff_scenario(definition, _build_forecast(case, scenario_name))


@pytest.mark.parametrize(("scenario", "expected_per_share"), [("BEAR", 4445), ("BASE", 27326), ("BULL", 57748)])
def test_ls_eco_reference_value_per_share(scenario: str, expected_per_share: int) -> None:
    assert _run(_load(), scenario).value_per_share == pytest.approx(expected_per_share, abs=1.0)


def test_ls_eco_market_price_sits_between_base_and_bull() -> None:
    case = _load()
    base = _run(case, "BASE").value_per_share
    bull = _run(case, "BULL").value_per_share
    assert base < case["market"]["price"] < bull


def test_ls_eco_result_file_matches_engine() -> None:
    case = _load()
    stored = json.loads((CASE_DIR / "valuation_result.json").read_text(encoding="utf-8"))
    for scenario in ("BEAR", "BASE", "BULL"):
        assert _run(case, scenario).value_per_share == pytest.approx(stored["scenario_results"][scenario]["current_intrinsic_value_per_share"], abs=1.0)
