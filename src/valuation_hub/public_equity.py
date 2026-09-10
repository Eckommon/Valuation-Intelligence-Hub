"""Public-equity normalization primitives / 상장기업 정규화 원시 함수.

The adapter layer converts accounting observations into normalized economic
inputs while keeping the transformations explicit and reproducible.

어댑터 레이어는 회계 관측치를 정규화된 경제 입력으로 변환하되,
변환 규칙을 명시적이고 재현 가능하게 유지한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class OperatingWorkingCapital:
    """Core operating working-capital components / 핵심 영업 운전자본 구성."""

    receivables: float
    inventory: float
    other_operating_current_assets: float = 0.0
    payables: float = 0.0
    other_operating_current_liabilities: float = 0.0


@dataclass(frozen=True)
class EquityBridgeInputs:
    """Balance-sheet bridge items / 자기자본가치 연결 항목."""

    debt: float
    cash: float
    minority_interest: float = 0.0
    non_operating_assets: float = 0.0
    other_claims: float = 0.0


def _finite(name: str, value: float) -> float:
    if not isfinite(value):
        raise ValueError(f"{name} must be finite.")
    return value


def operating_nwc(items: OperatingWorkingCapital) -> float:
    """Return operating NWC / 영업 운전자본 계산.

    operating NWC = receivables + inventory + other operating current assets
                    - payables - other operating current liabilities
    """
    values = {
        "receivables": items.receivables,
        "inventory": items.inventory,
        "other_operating_current_assets": items.other_operating_current_assets,
        "payables": items.payables,
        "other_operating_current_liabilities": items.other_operating_current_liabilities,
    }
    for name, value in values.items():
        _finite(name, value)
    return (
        items.receivables
        + items.inventory
        + items.other_operating_current_assets
        - items.payables
        - items.other_operating_current_liabilities
    )


def delta_nwc(current_nwc: float, prior_nwc: float) -> float:
    """Return change in operating NWC / 영업 운전자본 증감 계산."""
    return _finite("current_nwc", current_nwc) - _finite("prior_nwc", prior_nwc)


def normalize_per_share_for_split(
    historical_per_share: float,
    split_numerator: float,
    split_denominator: float,
) -> float:
    """Restate historical per-share data for a stock split / 과거 주당수치 분할조정.

    For a 5-for-1 split, numerator=5 and denominator=1; historical price/EPS
    is divided by five.
    """
    _finite("historical_per_share", historical_per_share)
    if split_numerator <= 0 or split_denominator <= 0:
        raise ValueError("split ratio components must be positive.")
    return historical_per_share * split_denominator / split_numerator


def normalize_shares_for_split(
    historical_shares: float,
    split_numerator: float,
    split_denominator: float,
) -> float:
    """Restate historical share count for a split / 과거 주식수 분할조정."""
    if historical_shares < 0 or not isfinite(historical_shares):
        raise ValueError("historical_shares must be finite and non-negative.")
    if split_numerator <= 0 or split_denominator <= 0:
        raise ValueError("split ratio components must be positive.")
    return historical_shares * split_numerator / split_denominator


def continuing_operations_metric(
    consolidated_metric: float,
    discontinued_operations_metric: float,
) -> float:
    """Remove discontinued operations when signs are presented consistently.

    중단사업이 연결 수치에 포함되어 있고 동일 부호체계로 제시된 경우 제거한다.
    """
    return _finite("consolidated_metric", consolidated_metric) - _finite(
        "discontinued_operations_metric", discontinued_operations_metric
    )


def net_debt(debt: float, cash: float) -> float:
    """Return net debt = debt - cash / 순부채 계산."""
    return _finite("debt", debt) - _finite("cash", cash)


def market_cap(price: float, diluted_shares: float) -> float:
    """Return equity market capitalization / 시가총액 계산."""
    if price < 0 or not isfinite(price):
        raise ValueError("price must be finite and non-negative.")
    if diluted_shares <= 0 or not isfinite(diluted_shares):
        raise ValueError("diluted_shares must be positive and finite.")
    return price * diluted_shares


def enterprise_value_from_market(
    market_capitalization: float,
    bridge: EquityBridgeInputs,
) -> float:
    """Convert market equity value to operating enterprise value.

    EV = market cap + debt - cash - non-operating assets
         + minority interest + other claims.
    """
    return (
        _finite("market_capitalization", market_capitalization)
        + _finite("debt", bridge.debt)
        - _finite("cash", bridge.cash)
        - _finite("non_operating_assets", bridge.non_operating_assets)
        + _finite("minority_interest", bridge.minority_interest)
        + _finite("other_claims", bridge.other_claims)
    )


def require_same_currency(*currency_codes: str) -> str:
    """Fail closed when monetary inputs use different currencies / 통화 불일치 차단."""
    normalized = {code.strip().upper() for code in currency_codes if code.strip()}
    if len(normalized) != 1:
        raise ValueError("all monetary inputs must use the same currency before aggregation.")
    return next(iter(normalized))
