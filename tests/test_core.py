"""Valuation kernel invariants / 가치평가 커널 불변조건 테스트."""

import pytest

from valuation_hub.core import (
    FcFFInputs,
    annualized_return,
    enterprise_to_equity,
    fcff,
    probability_weighted_value,
    terminal_value_gordon,
    value_per_share,
)


def test_fcff_identity() -> None:
    inputs = FcFFInputs(
        ebit=100.0,
        tax_rate=0.25,
        depreciation_amortization=10.0,
        capex=20.0,
        delta_nwc=5.0,
    )
    assert fcff(inputs) == pytest.approx(60.0)


def test_terminal_growth_must_be_below_wacc() -> None:
    with pytest.raises(ValueError):
        terminal_value_gordon(final_fcff=100.0, wacc=0.08, growth=0.08)


def test_equity_bridge() -> None:
    value = enterprise_to_equity(
        enterprise_value=1000.0,
        debt=200.0,
        cash=50.0,
        non_operating_assets=20.0,
        minority_interest=10.0,
        other_claims=5.0,
    )
    assert value == pytest.approx(855.0)


def test_value_per_share_requires_positive_share_count() -> None:
    with pytest.raises(ValueError):
        value_per_share(100.0, 0.0)


def test_annualized_return_round_trip() -> None:
    assert annualized_return(100.0, 121.0, 2.0) == pytest.approx(0.10)


def test_probability_weighted_value() -> None:
    values = {"bear": 50.0, "base": 100.0, "bull": 200.0}
    probabilities = {"bear": 0.2, "base": 0.5, "bull": 0.3}
    assert probability_weighted_value(values, probabilities) == pytest.approx(120.0)


def test_probabilities_must_sum_to_one() -> None:
    with pytest.raises(ValueError):
        probability_weighted_value(
            {"bear": 1.0, "base": 2.0, "bull": 3.0},
            {"bear": 0.2, "base": 0.5, "bull": 0.2},
        )
