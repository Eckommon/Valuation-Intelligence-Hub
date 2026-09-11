import pytest

from valuation_hub.public_equity import EquityBridgeInputs
from valuation_hub.reference_case import (
    RatioForecastYear,
    build_ratio_forecast,
    exit_irr,
    relative_valuation_lenses,
    simple_operating_nwc,
    terminal_exit_price,
)


def test_ratio_forecast_derives_delta_nwc_from_modeled_balance():
    opening = 100.0
    rows = [
        RatioForecastYear(2027, 1000.0, 0.10, 0.25, 0.02, 0.03, 0.12),
        RatioForecastYear(2028, 1100.0, 0.11, 0.25, 0.02, 0.03, 0.11),
    ]
    forecast = build_ratio_forecast(rows, opening)
    assert forecast[0].delta_nwc == 20.0
    assert forecast[1].delta_nwc == 1.0
    assert forecast[1].capex == 33.0
    assert forecast[1].depreciation_amortization == 22.0


def test_simple_operating_nwc():
    assert simple_operating_nwc(140.0, 70.0, 60.0) == 150.0


def test_relative_lenses_keep_market_and_enterprise_bridges_distinct():
    bridge = EquityBridgeInputs(debt=30.0, cash=10.0, minority_interest=5.0)
    out = relative_valuation_lenses(
        price=10.0,
        diluted_shares=100.0,
        revenue=500.0,
        ebit=100.0,
        net_income=50.0,
        free_cash_flow=-10.0,
        bridge=bridge,
    )
    assert out["market_cap"] == 1000.0
    assert out["enterprise_value"] == 1025.0
    assert out["price_to_sales"] == 2.0
    assert out["market_cap_to_ebit"] == 10.0
    assert out["price_to_earnings"] == 20.0
    assert out["price_to_fcf"] is None
    assert out["ev_to_ebit"] == 10.25


def test_terminal_exit_price_and_irr():
    price = terminal_exit_price(
        terminal_enterprise_value=1200.0,
        diluted_shares=100.0,
        future_net_debt=100.0,
    )
    assert price == 11.0
    assert exit_irr(10.0, 11.0, 1.0) == pytest.approx(0.1)
