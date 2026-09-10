import pytest

from valuation_hub.reverse import (
    scale_forecast_revenue,
    solve_bisection,
    solve_required_revenue_scale,
    solve_required_terminal_growth,
)
from valuation_hub.scenario import (
    ForecastYear,
    ScenarioDefinition,
    run_fcff_scenario,
    sensitivity_grid,
)


def sample_forecast() -> list[ForecastYear]:
    return [
        ForecastYear(2027, 100.0, 0.10, 0.25, 5.0, 6.0, 2.0),
        ForecastYear(2028, 110.0, 0.11, 0.25, 5.5, 6.5, 2.0),
        ForecastYear(2029, 120.0, 0.12, 0.25, 6.0, 7.0, 2.0),
    ]


def sample_definition() -> ScenarioDefinition:
    return ScenarioDefinition(
        name="base",
        wacc=0.10,
        terminal_growth=0.03,
        diluted_shares=10.0,
        debt=20.0,
        cash=5.0,
    )


def test_scenario_is_deterministic() -> None:
    definition = sample_definition()
    forecast = sample_forecast()
    first = run_fcff_scenario(definition, forecast)
    second = run_fcff_scenario(definition, forecast)
    assert first == second


def test_scenario_fcff_is_constructed_from_economics() -> None:
    result = run_fcff_scenario(sample_definition(), sample_forecast())
    # 2027 EBIT=10, NOPAT=7.5, +D&A 5 - capex 6 - dNWC 2 = 4.5
    assert result.forecast_fcff[0] == pytest.approx(4.5)


def test_invalid_forecast_order_fails_closed() -> None:
    forecast = sample_forecast()[::-1]
    with pytest.raises(ValueError):
        run_fcff_scenario(sample_definition(), forecast)


def test_sensitivity_invalid_terminal_cell_is_none() -> None:
    grid = sensitivity_grid(
        sample_definition(),
        sample_forecast(),
        wacc_values=[0.03, 0.10],
        terminal_growth_values=[0.03],
    )
    assert grid[(0.03, 0.03)] is None
    assert grid[(0.10, 0.03)] is not None


def test_bisection_solves_simple_root() -> None:
    root = solve_bisection(lambda x: x * x - 4.0, 0.0, 3.0)
    assert root == pytest.approx(2.0, abs=1e-7)


def test_reverse_terminal_growth_reproduces_known_value() -> None:
    definition = sample_definition()
    forecast = sample_forecast()
    target = run_fcff_scenario(definition, forecast).value_per_share
    solved = solve_required_terminal_growth(
        definition,
        forecast,
        target,
        low=-0.02,
    )
    assert solved == pytest.approx(definition.terminal_growth, abs=1e-7)


def test_revenue_scaling_preserves_margin_but_scales_linked_cash_items() -> None:
    scaled = scale_forecast_revenue(sample_forecast(), 2.0)
    assert scaled[0].revenue == pytest.approx(200.0)
    assert scaled[0].ebit_margin == pytest.approx(0.10)
    assert scaled[0].capex == pytest.approx(12.0)
    assert scaled[0].delta_nwc == pytest.approx(4.0)


def test_reverse_revenue_scale_reproduces_factor_one() -> None:
    definition = sample_definition()
    forecast = sample_forecast()
    target = run_fcff_scenario(definition, forecast).value_per_share
    solved = solve_required_revenue_scale(definition, forecast, target)
    assert solved == pytest.approx(1.0, abs=1e-7)
