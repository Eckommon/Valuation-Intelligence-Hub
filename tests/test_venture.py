"""Venture valuation engine tests / 벤처 가치평가 엔진 테스트."""

from __future__ import annotations

import pytest

from valuation_hub.venture import (
    VentureScenario,
    probability_weighted_venture_value,
    required_probability_for_target_value,
    run_venture_scenario,
)


def test_probability_weighted_value_is_reproducible() -> None:
    scenarios = [
        VentureScenario("FAILURE", 0.6, 0, 0, 0, 15_000_000, 0.30),
        VentureScenario("SURVIVAL", 0.3, 50_000_000, 2.0, 10_000_000, 12_000_000, 0.30),
        VentureScenario("BREAKOUT", 0.1, 200_000_000, 4.0, 20_000_000, 10_000_000, 0.30),
    ]
    result = probability_weighted_venture_value(scenarios, 4.306639288158795)
    assert result.expected_present_value_per_share == pytest.approx(3.2467821083)


def test_probabilities_must_sum_to_one() -> None:
    scenarios = [
        VentureScenario("A", 0.4, 10, 2, 0, 1, 0.2),
        VentureScenario("B", 0.4, 20, 2, 0, 1, 0.2),
    ]
    with pytest.raises(ValueError, match="sum to 1.0"):
        probability_weighted_venture_value(scenarios, 5)


def test_dilution_reduces_per_share_value() -> None:
    concentrated = VentureScenario("X", 1.0, 100, 3, 0, 10, 0.2)
    diluted = VentureScenario("X", 1.0, 100, 3, 0, 20, 0.2)
    assert run_venture_scenario(diluted, 5).present_value_per_share < run_venture_scenario(concentrated, 5).present_value_per_share


def test_reverse_probability_diagnostic() -> None:
    probability = required_probability_for_target_value(
        target_value_per_share=1.28,
        fixed_weighted_value_per_share=0.3 * 2.4229717226484073,
        conditional_present_value_per_share=25.19890591554344,
    )
    assert probability == pytest.approx(0.0219497023)
