"""Core valuation primitives / 핵심 가치평가 원시 함수.

This module intentionally contains pure, dependency-light functions so that
all asset adapters can share one auditable valuation kernel.

본 모듈은 모든 자산 어댑터가 하나의 감사 가능한 가치평가 커널을 공유하도록
의존성이 낮은 순수 함수를 제공한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class FcFFInputs:
    """Inputs for FCFF / FCFF 입력값."""

    ebit: float
    tax_rate: float
    depreciation_amortization: float
    capex: float
    delta_nwc: float


def _require_rate(name: str, value: float) -> None:
    if not isfinite(value) or not 0 <= value < 1:
        raise ValueError(f"{name} must be finite and in [0, 1).")


def nopat(ebit: float, tax_rate: float) -> float:
    """Return NOPAT = EBIT * (1-tax). / 세후영업이익 계산."""
    _require_rate("tax_rate", tax_rate)
    return ebit * (1 - tax_rate)


def fcff(inputs: FcFFInputs) -> float:
    """Return FCFF = NOPAT + D&A - CAPEX - ΔNWC. / FCFF 계산."""
    return (
        nopat(inputs.ebit, inputs.tax_rate)
        + inputs.depreciation_amortization
        - inputs.capex
        - inputs.delta_nwc
    )


def present_value(cash_flow: float, discount_rate: float, period: float) -> float:
    """Discount one cash flow. / 단일 현금흐름 현재가치 계산."""
    if not isfinite(discount_rate) or discount_rate <= -1:
        raise ValueError("discount_rate must be finite and greater than -1.")
    if not isfinite(period) or period < 0:
        raise ValueError("period must be finite and non-negative.")
    return cash_flow / ((1 + discount_rate) ** period)


def terminal_value_gordon(final_fcff: float, wacc: float, growth: float) -> float:
    """Gordon-growth terminal value. / 고든 성장모형 계속가치."""
    _require_rate("wacc", wacc)
    if not isfinite(growth):
        raise ValueError("growth must be finite.")
    if growth >= wacc:
        raise ValueError("terminal growth must be lower than WACC.")
    return final_fcff * (1 + growth) / (wacc - growth)


def enterprise_to_equity(
    enterprise_value: float,
    debt: float = 0.0,
    cash: float = 0.0,
    non_operating_assets: float = 0.0,
    minority_interest: float = 0.0,
    other_claims: float = 0.0,
) -> float:
    """Bridge enterprise value to equity value. / EV를 자기자본가치로 변환."""
    return (
        enterprise_value
        - debt
        + cash
        + non_operating_assets
        - minority_interest
        - other_claims
    )


def value_per_share(equity_value: float, diluted_shares: float) -> float:
    """Return equity value per diluted share. / 희석주식수 기준 주당가치."""
    if not isfinite(diluted_shares) or diluted_shares <= 0:
        raise ValueError("diluted_shares must be positive and finite.")
    return equity_value / diluted_shares


def annualized_return(current_price: float, future_value: float, years: float) -> float:
    """Simple annualized holding-period return. / 단순 연환산 보유수익률."""
    if current_price <= 0 or years <= 0:
        raise ValueError("current_price and years must be positive.")
    if future_value < 0:
        raise ValueError("future_value cannot be negative for this simple formula.")
    if future_value == 0:
        return -1.0
    return (future_value / current_price) ** (1 / years) - 1


def probability_weighted_value(values: dict[str, float], probabilities: dict[str, float]) -> float:
    """Return Σ p_i*V_i with strict probability checks. / 확률가중 가치 계산."""
    if set(values) != set(probabilities):
        raise ValueError("values and probabilities must have identical scenario keys.")
    total_probability = sum(probabilities.values())
    if abs(total_probability - 1.0) > 1e-9:
        raise ValueError("scenario probabilities must sum to 1.0.")
    if any(p < 0 or p > 1 for p in probabilities.values()):
        raise ValueError("each probability must be in [0, 1].")
    return sum(values[key] * probabilities[key] for key in values)
