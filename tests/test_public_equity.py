import pytest

from valuation_hub.public_equity import (
    EquityBridgeInputs,
    OperatingWorkingCapital,
    continuing_operations_metric,
    delta_nwc,
    enterprise_value_from_market,
    market_cap,
    net_debt,
    normalize_per_share_for_split,
    normalize_shares_for_split,
    operating_nwc,
    require_same_currency,
)


def test_operating_nwc_identity() -> None:
    items = OperatingWorkingCapital(
        receivables=140.0,
        inventory=70.0,
        other_operating_current_assets=10.0,
        payables=60.0,
        other_operating_current_liabilities=20.0,
    )
    assert operating_nwc(items) == pytest.approx(140.0)


def test_delta_nwc_positive_is_cash_use_in_fcff_convention() -> None:
    assert delta_nwc(250.0, 200.0) == pytest.approx(50.0)


def test_five_for_one_split_restates_price_and_shares_consistently() -> None:
    price = normalize_per_share_for_split(500_000.0, 5.0, 1.0)
    shares = normalize_shares_for_split(30_000_000.0, 5.0, 1.0)
    assert price == pytest.approx(100_000.0)
    assert shares == pytest.approx(150_000_000.0)
    assert price * shares == pytest.approx(500_000.0 * 30_000_000.0)


def test_continuing_operations_removes_discontinued_component() -> None:
    assert continuing_operations_metric(100.0, 25.0) == pytest.approx(75.0)


def test_net_debt_identity() -> None:
    assert net_debt(500.0, 120.0) == pytest.approx(380.0)


def test_market_cap_requires_positive_share_count() -> None:
    with pytest.raises(ValueError):
        market_cap(10.0, 0.0)


def test_market_ev_bridge() -> None:
    bridge = EquityBridgeInputs(
        debt=100.0,
        cash=25.0,
        minority_interest=5.0,
        non_operating_assets=10.0,
        other_claims=2.0,
    )
    assert enterprise_value_from_market(1_000.0, bridge) == pytest.approx(1_072.0)


def test_currency_mismatch_fails_closed() -> None:
    with pytest.raises(ValueError):
        require_same_currency("KRW", "USD")


def test_same_currency_is_normalized() -> None:
    assert require_same_currency("krw", "KRW") == "KRW"
