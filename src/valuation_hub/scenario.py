"""Scenario valuation engine / 시나리오 가치평가 엔진."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from valuation_hub.core import (
    FcFFInputs,
    enterprise_to_equity,
    fcff,
    present_value,
    terminal_value_gordon,
    value_per_share,
)


@dataclass(frozen=True)
class ForecastYear:
    year: int
    revenue: float
    ebit_margin: float
    tax_rate: float
    depreciation_amortization: float
    capex: float
    delta_nwc: float


@dataclass(frozen=True)
class ScenarioDefinition:
    name: str
    wacc: float
    terminal_growth: float
    diluted_shares: float
    debt: float = 0.0
    cash: float = 0.0
    non_operating_assets: float = 0.0
    minority_interest: float = 0.0
    other_claims: float = 0.0


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    forecast_fcff: tuple[float, ...]
    explicit_pv: float
    terminal_value: float
    terminal_pv: float
    enterprise_value: float
    equity_value: float
    value_per_share: float


def _validate_forecast(rows: list[ForecastYear]) -> None:
    if not rows:
        raise ValueError("forecast must contain at least one year.")
    years = [row.year for row in rows]
    if years != sorted(years) or len(years) != len(set(years)):
        raise ValueError("forecast years must be unique and ascending.")
    for row in rows:
        if row.revenue < 0 or not isfinite(row.revenue):
            raise ValueError("revenue must be finite and non-negative.")
        if not isfinite(row.ebit_margin):
            raise ValueError("ebit_margin must be finite.")
        for name, value in (
            ("depreciation_amortization", row.depreciation_amortization),
            ("capex", row.capex),
            ("delta_nwc", row.delta_nwc),
        ):
            if not isfinite(value):
                raise ValueError(f"{name} must be finite.")


def run_fcff_scenario(definition: ScenarioDefinition, forecast: list[ForecastYear]) -> ScenarioResult:
    """Run an explicit FCFF DCF scenario / 명시기간 FCFF DCF 시나리오 실행."""
    _validate_forecast(forecast)
    fcffs: list[float] = []
    explicit_pv = 0.0

    for period, row in enumerate(forecast, start=1):
        ebit = row.revenue * row.ebit_margin
        cash_flow = fcff(
            FcFFInputs(
                ebit=ebit,
                tax_rate=row.tax_rate,
                depreciation_amortization=row.depreciation_amortization,
                capex=row.capex,
                delta_nwc=row.delta_nwc,
            )
        )
        fcffs.append(cash_flow)
        explicit_pv += present_value(cash_flow, definition.wacc, period)

    terminal = terminal_value_gordon(
        final_fcff=fcffs[-1],
        wacc=definition.wacc,
        growth=definition.terminal_growth,
    )
    terminal_pv = present_value(terminal, definition.wacc, len(forecast))
    enterprise_value = explicit_pv + terminal_pv
    equity_value = enterprise_to_equity(
        enterprise_value,
        debt=definition.debt,
        cash=definition.cash,
        non_operating_assets=definition.non_operating_assets,
        minority_interest=definition.minority_interest,
        other_claims=definition.other_claims,
    )
    per_share = value_per_share(equity_value, definition.diluted_shares)

    return ScenarioResult(
        name=definition.name,
        forecast_fcff=tuple(fcffs),
        explicit_pv=explicit_pv,
        terminal_value=terminal,
        terminal_pv=terminal_pv,
        enterprise_value=enterprise_value,
        equity_value=equity_value,
        value_per_share=per_share,
    )


def sensitivity_grid(
    base_definition: ScenarioDefinition,
    forecast: list[ForecastYear],
    wacc_values: list[float],
    terminal_growth_values: list[float],
) -> dict[tuple[float, float], float | None]:
    """Return per-share sensitivity values; invalid cells are None / 주당가치 민감도 표."""
    result: dict[tuple[float, float], float | None] = {}
    for wacc in wacc_values:
        for growth in terminal_growth_values:
            if growth >= wacc:
                result[(wacc, growth)] = None
                continue
            definition = ScenarioDefinition(
                name=base_definition.name,
                wacc=wacc,
                terminal_growth=growth,
                diluted_shares=base_definition.diluted_shares,
                debt=base_definition.debt,
                cash=base_definition.cash,
                non_operating_assets=base_definition.non_operating_assets,
                minority_interest=base_definition.minority_interest,
                other_claims=base_definition.other_claims,
            )
            result[(wacc, growth)] = run_fcff_scenario(definition, forecast).value_per_share
    return result
