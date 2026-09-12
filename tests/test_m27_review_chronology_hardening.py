"""M27 quote-review chronology hardening regression tests."""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub.market_price import (
    build_market_price_candidate,
    build_market_price_review_assertion,
    validate_market_price_review_assertion,
)


def _rehash(value: dict, field: str) -> str:
    copied = copy.deepcopy(value)
    copied.pop(field, None)
    return hashlib.sha256(
        json.dumps(copied, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _candidate() -> dict:
    return build_market_price_candidate(
        price=123.45,
        currency="KRW",
        entity_id="DART_CORP:00126380",
        financial_scope="CFS",
        instrument_id="KR7000000000",
        symbol="TEST",
        venue="KRX",
        quote_type="OFFICIAL_CLOSE",
        trading_date="2026-09-12",
        observed_at="2026-09-12T15:30:00+09:00",
        as_of="2026-09-12",
        source_publisher="Korea Exchange",
        source_type="official_exchange_close",
        source_tier="A",
        source_locator="repo://market/quote",
        source_snapshot_sha256="a" * 64,
        max_age_days=7,
    )


def test_review_cannot_predate_quote_observation_on_same_valuation_day() -> None:
    with pytest.raises(CaseServiceError, match="predate quote observation|quote 관측시각"):
        build_market_price_review_assertion(
            _candidate(),
            reviewer="human",
            approved_at="2026-09-12T10:00:00+09:00",
            review_basis="Impossible pre-observation approval.",
        )


def test_resigned_assertion_cannot_bypass_quote_review_chronology() -> None:
    candidate = _candidate()
    assertion = build_market_price_review_assertion(
        candidate,
        reviewer="human",
        approved_at="2026-09-12T16:00:00+09:00",
        review_basis="Observed and reviewed after the close.",
    )
    forged = copy.deepcopy(assertion)
    forged["approved_at"] = "2026-09-12T10:00:00+09:00"
    forged["assertion_sha256"] = _rehash(forged, "assertion_sha256")
    with pytest.raises(CaseServiceError, match="predate quote observation|quote 관측시각"):
        validate_market_price_review_assertion(forged, candidate)
