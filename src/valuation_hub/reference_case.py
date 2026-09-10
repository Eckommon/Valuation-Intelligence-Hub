"""Reference-case orchestration helpers / 기준 사례 오케스트레이션 헬퍼.

These functions keep case-specific assumptions outside the valuation kernel while
making common transformations deterministic and testable.

본 모듈은 사례별 가정을 가치평가 커널 밖에 유지하면서 공통 변환을 결정론적이고
테스트 가능하게 만든다.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from valuation_hub.core import annualized_return
from valuation_hub.public_equity import EquityBridgeInputs, enterprise_value_from_market, market_cap
from valuation_hub.scenario import ForecastYear


@dataclass(frozen=True)
class RatioForecastYear:
    """Revenue and cash-economics ratios for one forecast year / 연도별 비율 가정."""

    year: int
    revenue: float
    ebit_margin: float
    tax_rate: float
    da_to_sales: float
    capex_to_sales: float
    nwc_to_sales: float


def build_ratio_forecast(rows: list[RatioForecastYear], opening_nwc: float) -> list[ForecastYear]:
    """Convert ratio assumptions into explicit FCFF forecast inputs.

    ΔNWC is calculated from the change in modeled operating NWC, rather than
    entered as an unexplained plug.

    비율 가정을 명시 FCFF 입력으로 변환한다. ΔNWC는 설명 없는 조정값이 아니라
    모델링된 영업 운전자본의 증감으로 계산한다.
    """
    if not rows:
        raise ValueError("rows must contain at least one forecast year.")
    if not isfinite(opening_nwc):
        raise ValueError("opening_nwc must be finite.")

    forecast: list[ForecastYear] = []
    prior_nwc = opening_nwc
    prior_year: int | None = None

    for row in rows:
        if prior_year is not None and row.year <= prior_year:
            raise ValueError("forecast years must be strictly ascending.")
        if row.revenue < 0 or not isfinite(row.revenue):
            raise ValueError("revenue must be finite and non-negative.")
        for name, value in (
            ("ebit_margin", row.ebit_margin),
            ("tax_rate", row.tax_rate),
            ("da_to_sales", row.da_to_sales),
            ("capex_to_sales", row.capex_to_sales),
            ("nwc_to_sales", row.nwc_to_sales),
        ):
            if not isfinite(value):
                raise ValueError(f"{name} must be finite.")
        if not 0 <= row.tax_rate < 1:
            raise ValueError("tax_rate must be in [0, 1).")
        if row.da_to_sales < 0 or row.capex_to_sales < 0 or row.nwc_to_sales < 0:
            raise ValueError("D&A, CAPEX and NWC ratios must be non-negative.")

        modeled_nwc = row.revenue * row.nwc_to_sales
        forecast.append(
            ForecastYear(
                year=row.year,
                revenue=row.revenue,
                ebit_margin=row.ebit_margin,
                tax_rate=row.tax_rate,
                depreciation_amortization=row.revenue * row.da_to_sales,
                capex=row.revenue * row.capex_to_sales,
                delta_nwc=modeled_nwc - prior_nwc,
            )
        )
        prior_nwc = modeled_nwc
        prior_year = row.year

    return forecast


def simple_operating_nwc(receivables: float, inventory: float, payables: float) -> float:
    """Core NWC = receivables + inventory - payables / 핵심 영업운전자본."""
    for name, value in (("receivables", receivables), ("inventory", inventory), ("payables", payables)):
        if not isfinite(value) or value < 0:
            raise ValueError(f"{name} must be finite and non-negative.")
    return receivables + inventory - payables


def relative_valuation_lenses(
    *,
    price: float,
    diluted_shares: float,
    revenue: float,
    ebit: float,
    net_income: float,
    free_cash_flow: float,
    bridge: EquityBridgeInputs,
) -> dict[str, float | None]:
    """Return reproducible market-value lenses / 재현 가능한 시장가치 렌즈."""
    if revenue <= 0 or ebit <= 0 or net_income <= 0:
        raise ValueError("revenue, EBIT and net income must be positive for these lenses.")
    equity_market_value = market_cap(price, diluted_shares)
    enterprise_market_value = enterprise_value_from_market(equity_market_value, bridge)
    return {
        "market_cap": equity_market_value,
        "enterprise_value": enterprise_market_value,
        "price_to_sales": equity_market_value / revenue,
        "market_cap_to_ebit": equity_market_value / ebit,
        "price_to_earnings": equity_market_value / net_income,
        "price_to_fcf": None if free_cash_flow <= 0 else equity_market_value / free_cash_flow,
        "ev_to_ebit": enterprise_market_value / ebit,
    }


def terminal_exit_price(
    *,
    terminal_enterprise_value: float,
    diluted_shares: float,
    future_net_debt: float,
    future_minority_interest: float = 0.0,
    future_other_claims: float = 0.0,
) -> float:
    """Translate terminal EV into a future equity value per share / 미래 주당가치 변환."""
    if diluted_shares <= 0 or not isfinite(diluted_shares):
        raise ValueError("diluted_shares must be positive and finite.")
    equity = terminal_enterprise_value - future_net_debt - future_minority_interest - future_other_claims
    return equity / diluted_shares


def exit_irr(current_price: float, exit_price: float, years: float) -> float:
    """Annualized price-only IRR / 배당 제외 가격 기준 연환산 IRR."""
    return annualized_return(current_price, exit_price, years)
