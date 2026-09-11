"""Venture and option-like valuation primitives / 벤처·옵션형 가치평가 원시함수.

Use this module when conventional FCFF DCF creates false precision because
business perimeter, financing, dilution, or survival probability dominate value.

사업범위 변경, 자금조달, 희석, 생존확률이 가치를 지배하여 전통적 FCFF DCF가
거짓 정밀도를 만들 수 있는 경우 본 모듈을 사용한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class VentureScenario:
    """Conditional terminal venture outcome / 조건부 벤처 종착 시나리오."""

    name: str
    probability: float
    terminal_revenue: float
    ev_to_sales: float
    terminal_net_debt: float
    diluted_shares: float
    discount_rate: float
    recovery_equity_value: float = 0.0


@dataclass(frozen=True)
class VentureScenarioResult:
    name: str
    probability: float
    terminal_enterprise_value: float
    terminal_equity_value: float
    terminal_value_per_share: float
    present_value_per_share: float
    probability_weighted_present_value_per_share: float


@dataclass(frozen=True)
class VentureExpectedValueResult:
    scenario_results: tuple[VentureScenarioResult, ...]
    expected_present_value_per_share: float


def _validate_scenario(scenario: VentureScenario) -> None:
    values = (
        scenario.probability,
        scenario.terminal_revenue,
        scenario.ev_to_sales,
        scenario.terminal_net_debt,
        scenario.diluted_shares,
        scenario.discount_rate,
        scenario.recovery_equity_value,
    )
    if not all(isfinite(v) for v in values):
        raise ValueError("all venture scenario inputs must be finite.")
    if not 0 <= scenario.probability <= 1:
        raise ValueError("probability must be in [0, 1].")
    if scenario.terminal_revenue < 0 or scenario.ev_to_sales < 0:
        raise ValueError("terminal revenue and EV/sales must be non-negative.")
    if scenario.diluted_shares <= 0:
        raise ValueError("diluted_shares must be positive.")
    if scenario.discount_rate <= -1:
        raise ValueError("discount_rate must be greater than -1.")
    if scenario.recovery_equity_value < 0:
        raise ValueError("recovery_equity_value cannot be negative.")


def run_venture_scenario(scenario: VentureScenario, years: float) -> VentureScenarioResult:
    """Value one conditional venture outcome / 단일 조건부 벤처 시나리오 가치평가."""
    _validate_scenario(scenario)
    if not isfinite(years) or years <= 0:
        raise ValueError("years must be positive and finite.")

    terminal_enterprise_value = scenario.terminal_revenue * scenario.ev_to_sales
    operating_equity_value = max(terminal_enterprise_value - scenario.terminal_net_debt, 0.0)
    terminal_equity_value = max(operating_equity_value, scenario.recovery_equity_value)
    terminal_value_per_share = terminal_equity_value / scenario.diluted_shares
    present_value_per_share = terminal_value_per_share / ((1 + scenario.discount_rate) ** years)
    weighted = scenario.probability * present_value_per_share

    return VentureScenarioResult(
        name=scenario.name,
        probability=scenario.probability,
        terminal_enterprise_value=terminal_enterprise_value,
        terminal_equity_value=terminal_equity_value,
        terminal_value_per_share=terminal_value_per_share,
        present_value_per_share=present_value_per_share,
        probability_weighted_present_value_per_share=weighted,
    )


def probability_weighted_venture_value(
    scenarios: list[VentureScenario],
    years: float,
    *,
    probability_tolerance: float = 1e-9,
) -> VentureExpectedValueResult:
    """Return probability-weighted present value/share / 확률가중 현재 주당가치."""
    if not scenarios:
        raise ValueError("at least one venture scenario is required.")
    total_probability = sum(s.probability for s in scenarios)
    if abs(total_probability - 1.0) > probability_tolerance:
        raise ValueError("venture scenario probabilities must sum to 1.0.")
    results = tuple(run_venture_scenario(s, years) for s in scenarios)
    expected = sum(r.probability_weighted_present_value_per_share for r in results)
    return VentureExpectedValueResult(results, expected)


def required_probability_for_target_value(
    *,
    target_value_per_share: float,
    fixed_weighted_value_per_share: float,
    conditional_present_value_per_share: float,
) -> float:
    """Solve probability required for one conditional outcome to meet a target.

    Other scenario weighted contributions are held fixed. This is a reverse
    probability diagnostic, not a probability forecast.

    다른 시나리오의 확률가중 기여값을 고정하고 특정 조건부 결과가 목표가치를
    맞추기 위해 필요한 확률을 역산한다. 확률 전망이 아니라 역산 진단이다.
    """
    if target_value_per_share < 0 or fixed_weighted_value_per_share < 0:
        raise ValueError("target and fixed weighted value must be non-negative.")
    if conditional_present_value_per_share <= 0:
        raise ValueError("conditional present value must be positive.")
    probability = (
        target_value_per_share - fixed_weighted_value_per_share
    ) / conditional_present_value_per_share
    if probability < 0 or probability > 1:
        raise ValueError("target implies a probability outside [0, 1].")
    return probability
