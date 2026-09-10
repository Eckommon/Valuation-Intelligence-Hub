"""Reverse valuation solvers / 역산 가치평가 솔버."""

from __future__ import annotations

from dataclasses import replace
from math import isfinite
from typing import Callable

from valuation_hub.scenario import ForecastYear, ScenarioDefinition, run_fcff_scenario


def solve_bisection(
    objective: Callable[[float], float],
    low: float,
    high: float,
    *,
    tolerance: float = 1e-8,
    max_iterations: int = 200,
) -> float:
    """Solve objective(x)=0 with a deterministic bracketed bisection solver."""
    if not all(isfinite(x) for x in (low, high, tolerance)):
        raise ValueError("bounds and tolerance must be finite.")
    if low >= high or tolerance <= 0:
        raise ValueError("require low < high and positive tolerance.")

    f_low = objective(low)
    f_high = objective(high)
    if f_low == 0:
        return low
    if f_high == 0:
        return high
    if f_low * f_high > 0:
        raise ValueError("objective must be bracketed by opposite signs.")

    for _ in range(max_iterations):
        mid = (low + high) / 2
        f_mid = objective(mid)
        if abs(f_mid) <= tolerance or (high - low) / 2 <= tolerance:
            return mid
        if f_low * f_mid <= 0:
            high = mid
            f_high = f_mid
        else:
            low = mid
            f_low = f_mid
    raise RuntimeError("bisection did not converge within max_iterations.")


def solve_required_terminal_growth(
    definition: ScenarioDefinition,
    forecast: list[ForecastYear],
    target_value_per_share: float,
    *,
    low: float = -0.05,
    high_buffer: float = 1e-6,
) -> float:
    """Solve terminal growth required to match target per-share value.

    현재 시장가격 등 목표 주당가치를 정당화하는 영구성장률을 역산한다.
    """
    if target_value_per_share <= 0:
        raise ValueError("target_value_per_share must be positive.")
    high = definition.wacc - high_buffer
    if low >= high:
        raise ValueError("invalid terminal-growth search interval.")

    def objective(growth: float) -> float:
        candidate = replace(definition, terminal_growth=growth)
        return run_fcff_scenario(candidate, forecast).value_per_share - target_value_per_share

    return solve_bisection(objective, low, high)


def scale_forecast_revenue(
    forecast: list[ForecastYear],
    factor: float,
) -> list[ForecastYear]:
    """Scale revenue and revenue-linked cash items for reverse experiments.

    매출과 매출 연동 현금항목을 동일 비율로 조정하여 시장 내재 경제성 실험에 사용한다.
    """
    if factor <= 0 or not isfinite(factor):
        raise ValueError("factor must be positive and finite.")
    return [
        replace(
            row,
            revenue=row.revenue * factor,
            depreciation_amortization=row.depreciation_amortization * factor,
            capex=row.capex * factor,
            delta_nwc=row.delta_nwc * factor,
        )
        for row in forecast
    ]


def solve_required_revenue_scale(
    definition: ScenarioDefinition,
    forecast: list[ForecastYear],
    target_value_per_share: float,
    *,
    low: float = 0.1,
    high: float = 20.0,
) -> float:
    """Solve proportional revenue/cash-economics scale required by market price."""
    if target_value_per_share <= 0:
        raise ValueError("target_value_per_share must be positive.")

    def objective(factor: float) -> float:
        scaled = scale_forecast_revenue(forecast, factor)
        return run_fcff_scenario(definition, scaled).value_per_share - target_value_per_share

    return solve_bisection(objective, low, high)
