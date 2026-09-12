"""M27 governed market-price FACT + Draft binding tests."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from valuation_hub.binding_apply_m27 import (
    apply_binding_approval,
    build_binding_approval,
    validate_bound_draft_result,
)
from valuation_hub.case_service import CaseServiceError
from valuation_hub.forecast_draft_binding import build_binding_proposal_with_forecast
from valuation_hub.market_price import (
    build_market_price_candidate,
    build_market_price_review_assertion,
    finalize_reviewed_market_price,
    validate_market_price_candidate,
    validate_reviewed_market_price,
)
from valuation_hub.market_price_draft_binding import (
    build_binding_proposal_with_market_price,
    validate_binding_proposal_v7,
)


def _rehash(value: dict, field: str) -> str:
    copied = copy.deepcopy(value)
    copied.pop(field, None)
    return hashlib.sha256(
        json.dumps(copied, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _m26_fixtures():
    path = Path(__file__).with_name("test_m26_integrated_forecast_binding.py")
    spec = importlib.util.spec_from_file_location("_m26_market_fixture", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _v06(names: list[str] | None = None) -> dict:
    fixtures = _m26_fixtures()
    names = names or ["BASE"]
    return build_binding_proposal_with_forecast(fixtures._v05(names), fixtures._forecast_package(names))


def _draft(names: list[str] | None = None) -> dict:
    return _m26_fixtures()._draft(names or ["BASE"])


def _package(
    *,
    currency: str = "KRW",
    entity_id: str = "DART_CORP:00126380",
    financial_scope: str = "CFS",
    source_tier: str = "A",
    trading_date: str = "2026-09-11",
    observed_at: str = "2026-09-11T15:30:00+09:00",
    as_of: str = "2026-09-12",
    max_age_days: int = 7,
) -> dict:
    candidate = build_market_price_candidate(
        price=123.45,
        currency=currency,
        entity_id=entity_id,
        financial_scope=financial_scope,
        instrument_id="KR7000000000",
        symbol="TEST",
        venue="KRX",
        quote_type="OFFICIAL_CLOSE",
        trading_date=trading_date,
        observed_at=observed_at,
        as_of=as_of,
        source_publisher="Korea Exchange",
        source_type="official_exchange_close",
        source_tier=source_tier,
        source_locator="repo://market/quote",
        source_snapshot_sha256="a" * 64,
        max_age_days=max_age_days,
    )
    assertion = build_market_price_review_assertion(
        candidate,
        reviewer="market reviewer",
        approved_at="2026-09-12T21:00:00+09:00",
        review_basis="Reviewed exact exchange quote identity and freshness.",
    )
    return finalize_reviewed_market_price(candidate, assertion)


def _decision(proposal: dict, field: str) -> dict:
    return next(item for item in proposal["draft_input_matrix"] if item["field"] == field)


def test_market_price_candidate_is_fact_candidate_and_reviewed_package_is_fact() -> None:
    candidate = build_market_price_candidate(
        price=123.45,
        currency="KRW",
        entity_id="DART_CORP:00126380",
        financial_scope="CFS",
        instrument_id="KR7000000000",
        symbol="TEST",
        venue="KRX",
        quote_type="OFFICIAL_CLOSE",
        trading_date="2026-09-11",
        observed_at="2026-09-11T15:30:00+09:00",
        as_of="2026-09-12",
        source_publisher="Korea Exchange",
        source_type="official_exchange_close",
        source_tier="A",
        source_locator="repo://market/quote",
        source_snapshot_sha256="a" * 64,
    )
    checked = validate_market_price_candidate(candidate)
    assert candidate["class"] == "FACT_CANDIDATE"
    assert checked["eligible_for_human_review"] is True
    assertion = build_market_price_review_assertion(
        candidate,
        reviewer="human",
        approved_at="2026-09-12T10:00:00+09:00",
        review_basis="Exact quote reviewed.",
    )
    package = finalize_reviewed_market_price(candidate, assertion)
    assert package["class"] == "FACT"
    assert validate_reviewed_market_price(package)["eligible"] is True


def test_market_price_stale_or_lower_tier_cannot_be_reviewed() -> None:
    candidate = build_market_price_candidate(
        price=123.45,
        currency="KRW",
        entity_id="DART_CORP:00126380",
        financial_scope="CFS",
        instrument_id="KR7000000000",
        symbol="TEST",
        venue="KRX",
        quote_type="OFFICIAL_CLOSE",
        trading_date="2026-09-01",
        observed_at="2026-09-01T15:30:00+09:00",
        as_of="2026-09-12",
        source_publisher="secondary",
        source_type="reference_price",
        source_tier="C",
        source_locator="repo://market/reference",
        source_snapshot_sha256="b" * 64,
        max_age_days=7,
    )
    checked = validate_market_price_candidate(candidate)
    assert checked["freshness"] == "STALE_BLOCKED"
    assert checked["eligible_for_human_review"] is False
    with pytest.raises(CaseServiceError, match="not eligible for review|인간검토 부적격"):
        build_market_price_review_assertion(
            candidate,
            reviewer="human",
            approved_at="2026-09-12T10:00:00+09:00",
            review_basis="Should fail.",
        )


def test_market_price_quote_chronology_is_exact() -> None:
    with pytest.raises(CaseServiceError, match="local date|현지 날짜"):
        build_market_price_candidate(
            price=123.45,
            currency="KRW",
            entity_id="DART_CORP:00126380",
            financial_scope="CFS",
            instrument_id="KR7000000000",
            symbol="TEST",
            venue="KRX",
            quote_type="OFFICIAL_CLOSE",
            trading_date="2026-09-11",
            observed_at="2026-09-12T00:30:00+09:00",
            as_of="2026-09-12",
            source_publisher="Korea Exchange",
            source_type="official_exchange_close",
            source_tier="A",
            source_locator="repo://market/quote",
            source_snapshot_sha256="a" * 64,
        )
    with pytest.raises(CaseServiceError, match="after valuation as_of|가치평가일 이후"):
        build_market_price_candidate(
            price=123.45,
            currency="KRW",
            entity_id="DART_CORP:00126380",
            financial_scope="CFS",
            instrument_id="KR7000000000",
            symbol="TEST",
            venue="KRX",
            quote_type="LAST_TRADE",
            trading_date="2026-09-13",
            observed_at="2026-09-13T10:00:00+09:00",
            as_of="2026-09-12",
            source_publisher="Korea Exchange",
            source_type="official_exchange_trade",
            source_tier="A",
            source_locator="repo://market/trade",
            source_snapshot_sha256="a" * 64,
        )


def test_v07_replaces_only_market_price_and_requires_v06() -> None:
    base = _v06(["BASE"])
    package = _package()
    proposal = build_binding_proposal_with_market_price(base, package)
    checked = validate_binding_proposal_v7(proposal)
    assert proposal["schema_version"] == "draft-binding-proposal-v0.7"
    assert _decision(proposal, "market_price")["state"] == "DIRECT_BIND"
    for item in base["draft_input_matrix"]:
        if item["field"] != "market_price":
            assert _decision(proposal, item["field"]) == item
    assert checked["direct_bind_count"] == base["completeness"]["direct_bind_count"] + 1
    with pytest.raises(CaseServiceError, match="v0.6"):
        build_binding_proposal_with_market_price(base["base_proposal"], package)


def test_v07_compatibility_mismatch_fails_closed() -> None:
    base = _v06(["BASE"])
    with pytest.raises(CaseServiceError, match="currency mismatch|통화 불일치"):
        build_binding_proposal_with_market_price(base, _package(currency="USD"))
    with pytest.raises(CaseServiceError, match="entity/scope mismatch|entity·scope 불일치"):
        build_binding_proposal_with_market_price(base, _package(entity_id="DART_CORP:OTHER"))
    package = _package(as_of="2026-09-11", trading_date="2026-09-11")
    with pytest.raises(CaseServiceError, match="as_of"):
        build_binding_proposal_with_market_price(base, package)


def test_nested_market_price_tamper_fails_even_after_outer_resign() -> None:
    package = _package()
    tampered = copy.deepcopy(package)
    tampered["candidate"]["price"] += 1.0
    tampered["package_sha256"] = _rehash(tampered, "package_sha256")
    with pytest.raises(CaseServiceError):
        validate_reviewed_market_price(tampered)


def test_v07_policy_tamper_fails_after_outer_resign() -> None:
    proposal = build_binding_proposal_with_market_price(_v06(["BASE"]), _package())
    tampered = copy.deepcopy(proposal)
    tampered["policy"]["direct_bind_requires"].remove("AS_TRADED_PER_SHARE")
    tampered["proposal_sha256"] = _rehash(tampered, "proposal_sha256")
    with pytest.raises(CaseServiceError, match="policy/base mismatch|정책·base 불일치"):
        validate_binding_proposal_v7(tampered)


def test_market_price_apply_updates_only_top_level_and_preserves_lineage() -> None:
    package = _package()
    proposal = build_binding_proposal_with_market_price(_v06(["BASE"]), package)
    draft = _draft(["BASE"])
    before = copy.deepcopy(draft)
    approval = build_binding_approval(
        proposal,
        draft,
        reviewer="human",
        target_entity_id="DART_CORP:00126380",
        target_financial_scope="CFS",
        approved_fields=["market_price"],
        approved_at="2026-09-12T21:30:00+09:00",
    )
    result = apply_binding_approval(proposal, draft, approval)
    assert draft == before
    assert result["draft_after"]["market_price"] == pytest.approx(123.45)
    assert result["draft_after"]["equity"] == before["equity"]
    assert validate_bound_draft_result(result)["applied_field_count"] == 1
    diff = result["applied_diffs"][0]
    assert diff["field"] == "market_price"
    assert diff["source_market_price_package_sha256"] == package["package_sha256"]
    assert diff["source_snapshot_sha256"] == package["source"]["snapshot_sha256"]
    assert diff["review_assertion_sha256"] == package["review_assertion"]["assertion_sha256"]
    assert diff["trading_date"] == "2026-09-11"
    assert diff["venue"] == "KRX"
    assert diff["quote_type"] == "OFFICIAL_CLOSE"
