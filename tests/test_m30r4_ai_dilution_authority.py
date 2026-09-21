from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from valuation_hub import cli_entry_m30r4
from valuation_hub.ai_dilution_authority import (
    ABSENT_SUPPORTED,
    ADJUDICATOR_ID,
    APPROVE,
    BLOCKED_DEPENDENCY,
    EXPLICIT_CONTINGENT_METHOD,
    EXPLICIT_COUNT_METHOD,
    EXPLICIT_OTHER_METHOD,
    HOLD,
    PRESENT,
    TSM_METHOD,
    TSM_TRANCHES_METHOD,
    build_ai_dilution_adjudication,
    build_ai_dilution_inventory,
    build_ai_reviewed_dilution_package,
    validate_ai_dilution_adjudication,
    validate_ai_dilution_inventory,
    validate_ai_reviewed_dilution_package,
)
from valuation_hub.case_service import CaseServiceError
from valuation_hub.market_price import build_market_price_candidate, build_market_price_review_assertion, finalize_reviewed_market_price
from valuation_hub.sec_live import TransportResponse, capture_companyfacts_snapshot
from valuation_hub.valuation_shares import (
    ADJUSTMENT_CATEGORIES,
    COMPLETE,
    build_valuation_share_base_context,
    extract_sec_current_common_shares_candidate,
    normalize_current_common_shares_candidate,
)


def _sha(value: dict, field: str) -> str:
    copied = copy.deepcopy(value)
    copied.pop(field, None)
    return hashlib.sha256(json.dumps(copied, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _snapshot() -> dict:
    payload = {"cik": 1046257, "entityName": "Ingredion Incorporated", "facts": {"dei": {"EntityCommonStockSharesOutstanding": {"units": {"shares": [{"end": "2026-08-05", "val": 63_063_979, "accn": "0001628280-26-054722", "form": "10-Q", "filed": "2026-08-07"}]}}}}}
    body = json.dumps(payload, separators=(",", ":")).encode()
    def transport(locator: str, *, user_agent: str) -> TransportResponse:
        return TransportResponse(200, "application/json", body, locator)
    return capture_companyfacts_snapshot("1046257", user_agent="M30R4 test@example.com", transport=transport, fetched_at="2026-09-15T17:42:53+00:00")


def _base() -> dict:
    candidate = extract_sec_current_common_shares_candidate(_snapshot(), period_end="2026-08-05", form="10-Q")
    candidate["class"] = "FACT"
    candidate["candidate_sha256"] = _sha(candidate, "candidate_sha256")
    observation = normalize_current_common_shares_candidate(candidate)
    return build_valuation_share_base_context(observation, as_of="2026-09-14")


def _market() -> dict:
    candidate = build_market_price_candidate(
        price=120.0,
        currency="USD",
        entity_id="SEC_CIK:0001046257",
        financial_scope="AS_REPORTED",
        instrument_id="US4571871023",
        symbol="INGR",
        venue="NYSE",
        quote_type="OFFICIAL_CLOSE",
        trading_date="2026-09-14",
        observed_at="2026-09-14T16:00:00-04:00",
        as_of="2026-09-14",
        source_publisher="NYSE",
        source_type="official_exchange_close",
        source_tier="A",
        source_locator="repo://market/INGR/2026-09-14",
        source_snapshot_sha256="9" * 64,
    )
    assertion = build_market_price_review_assertion(
        candidate,
        reviewer="fixture reviewer",
        approved_at="2026-09-15T09:00:00+09:00",
        review_basis="Fixture review of exact exchange quote.",
    )
    return finalize_reviewed_market_price(candidate, assertion)


def _sources(seed: str) -> list[dict]:
    return [{"locator": f"repo://evidence/{seed}", "snapshot_sha256": seed * 64, "source_type": "issuer_filing_snapshot"}]


def _row(category: str, state: str, seed: str, **kwargs) -> dict:
    result = {
        "category": category,
        "state": state,
        "sources": _sources(seed),
        "evidence_basis": kwargs.pop("evidence_basis", f"Explicit issuer evidence for {category}."),
        "contradiction_search": {
            "performed": True,
            "summary": kwargs.pop("summary", "No material contrary issuer evidence identified."),
            "material_contradictions": kwargs.pop("contradictions", []),
        },
        "dependencies": kwargs.pop("dependencies", []),
        "adjustment_id": kwargs.pop("adjustment_id", None),
        "adjustment_shares": kwargs.pop("adjustment_shares", None),
        "calculation_method": kwargs.pop("calculation_method", None),
        "calculation_inputs": kwargs.pop("calculation_inputs", None),
    }
    assert not kwargs
    return result


def _incomplete_rows() -> list[dict]:
    return [
        _row("options_treasury_stock_method", BLOCKED_DEPENDENCY, "a", dependencies=["source_bound_valuation_date_market_price"]),
        _row("rsu_restricted_stock", PRESENT, "b", adjustment_id="INGR-RSU-20260630", adjustment_shares=534_000, calculation_method=EXPLICIT_COUNT_METHOD, calculation_inputs={"explicit_share_count": 534_000}),
        _row("warrants", ABSENT_SUPPORTED, "c"),
        _row("convertibles_if_converted", ABSENT_SUPPORTED, "d"),
        _row("contingent_shares", BLOCKED_DEPENDENCY, "e", dependencies=["complete_point_in_time_performance_award_count"]),
        _row("other_explicit", BLOCKED_DEPENDENCY, "f", dependencies=["current_director_and_deferred_equity_unit_count"]),
    ]


def _complete_rows() -> list[dict]:
    # At $120 market price, 100 options at $60 strike produce 50 incremental TSM shares.
    return [
        _row("options_treasury_stock_method", PRESENT, "a", adjustment_id="OPT", adjustment_shares=50.0, calculation_method=TSM_METHOD, calculation_inputs={"outstanding_instruments": 100, "weighted_average_exercise_price": 60.0, "homogeneous_exercise_price": True}),
        _row("rsu_restricted_stock", PRESENT, "b", adjustment_id="RSU", adjustment_shares=20, calculation_method=EXPLICIT_COUNT_METHOD, calculation_inputs={"explicit_share_count": 20}),
        _row("warrants", ABSENT_SUPPORTED, "c"),
        _row("convertibles_if_converted", ABSENT_SUPPORTED, "d"),
        _row("contingent_shares", PRESENT, "e", adjustment_id="PSU", adjustment_shares=10, calculation_method=EXPLICIT_CONTINGENT_METHOD, calculation_inputs={"explicit_share_count": 10}),
        _row("other_explicit", PRESENT, "f", adjustment_id="OTHER", adjustment_shares=5, calculation_method=EXPLICIT_OTHER_METHOD, calculation_inputs={"explicit_share_count": 5}),
    ]


def test_real_shaped_incomplete_inventory_is_durable_hold_not_zero_fill() -> None:
    base = _base()
    inventory = build_ai_dilution_inventory(base, _incomplete_rows())
    checked = validate_ai_dilution_inventory(inventory, base)
    assert checked["decision"] == HOLD
    assert len(checked["blockers"]) == 3
    states = {row["category"]: row["state"] for row in inventory["categories"]}
    assert states["options_treasury_stock_method"] == BLOCKED_DEPENDENCY
    assert states["contingent_shares"] == BLOCKED_DEPENDENCY
    assert states["other_explicit"] == BLOCKED_DEPENDENCY
    assert inventory["semantic_boundary"]["missing_category_never_zero_or_absent"] is True

    adjudication = build_ai_dilution_adjudication(inventory, base, adjudicated_at="2026-09-18T03:00:00+09:00")
    assert adjudication["decision"] != APPROVE
    with pytest.raises(CaseServiceError, match="incomplete dilution coverage"):
        build_ai_reviewed_dilution_package(base, inventory, adjudication)


def test_options_present_requires_source_bound_market_price() -> None:
    rows = _complete_rows()
    with pytest.raises(CaseServiceError, match="market price"):
        build_ai_dilution_inventory(_base(), rows)


def test_historical_weighted_average_eps_method_cannot_be_valuation_date_adjustment() -> None:
    rows = _complete_rows()
    rows[0]["calculation_method"] = "HISTORICAL_WEIGHTED_AVERAGE_EPS"
    with pytest.raises(CaseServiceError, match="calculation method"):
        build_ai_dilution_inventory(_base(), rows, market_price_package=_market())


def test_material_contradiction_cannot_be_resolved_present() -> None:
    rows = _complete_rows()
    rows[1]["contradiction_search"]["material_contradictions"] = ["Issuer disclosure conflicts with supplied RSU count."]
    with pytest.raises(CaseServiceError, match="material contradiction"):
        build_ai_dilution_inventory(_base(), rows, market_price_package=_market())


def test_complete_ai_coverage_reuses_m22_and_produces_eligible_bridge() -> None:
    base = _base()
    inventory = build_ai_dilution_inventory(base, _complete_rows(), market_price_package=_market())
    assert inventory["decision"] != HOLD
    adjudication = build_ai_dilution_adjudication(inventory, base, adjudicated_at="2026-09-18T03:00:00+09:00")
    assert adjudication["decision"] == APPROVE
    assert adjudication["adjudicator"] == {"type": "AI", "id": ADJUDICATOR_ID}
    assert validate_ai_dilution_adjudication(adjudication, inventory, base)["decision"] == APPROVE

    package = build_ai_reviewed_dilution_package(base, inventory, adjudication)
    checked = validate_ai_reviewed_dilution_package(package, base, inventory, adjudication)
    assert checked["eligible"] is True
    assert package["bridge"]["coverage"]["status"] == COMPLETE
    assert package["bridge"]["binding_eligibility"]["eligible_for_future_direct_bind"] is True
    assert package["value"] == 63_063_979 + 50 + 20 + 10 + 5
    assert all(item["class"] == "NORMALIZED_FACT" for item in package["adjustments"])
    assert package["coverage_assertion"]["reviewer"] == ADJUDICATOR_ID


def test_cli_builds_hold_inventory_and_delegates_prior_commands(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    base = _base()
    bp = tmp_path / "base.json"
    rp = tmp_path / "rows.json"
    bp.write_text(json.dumps(base), encoding="utf-8")
    rp.write_text(json.dumps(_incomplete_rows()), encoding="utf-8")

    rc = cli_entry_m30r4.main(["--json", "dilution-ai-inventory-build", str(bp), str(rp)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["decision"] == HOLD
    assert len(out["blockers"]) == 3

    seen: list[list[str]] = []
    monkeypatch.setattr(cli_entry_m30r4.prior_cli, "main", lambda argv: seen.append(list(argv)) or 31)
    old = ["share-base-context-validate", "base.json"]
    assert cli_entry_m30r4.main(old) == 31
    assert seen == [old]


def test_inventory_requires_exactly_all_m22_categories() -> None:
    rows = _incomplete_rows()[:-1]
    with pytest.raises(CaseServiceError, match="exactly six"):
        build_ai_dilution_inventory(_base(), rows)
    assert tuple(row["category"] for row in _incomplete_rows()) == ADJUSTMENT_CATEGORIES


def test_aggregate_weighted_average_strike_fails_closed_without_homogeneous_proof() -> None:
    rows = _complete_rows()
    rows[0]["calculation_inputs"].pop("homogeneous_exercise_price")
    with pytest.raises(CaseServiceError, match="weighted-average strike"):
        build_ai_dilution_inventory(_base(), rows, market_price_package=_market())


def test_tranche_tsm_catches_dilution_hidden_by_weighted_average_strike() -> None:
    rows = _complete_rows()
    # 50 options at 60 and 50 options at 180 have weighted-average strike 120.
    # At market 120 an aggregate-average shortcut incorrectly returns zero,
    # while tranche-safe TSM preserves dilution from the lower-strike tranche.
    expected = 50 * (120 - 60) / 120 + 50 * max(0, 120 - 180) / 120
    rows[0]["calculation_method"] = TSM_TRANCHES_METHOD
    rows[0]["adjustment_shares"] = expected
    rows[0]["calculation_inputs"] = {
        "total_outstanding_instruments": 100,
        "tranches": [
            {"outstanding_instruments": 50, "exercise_price": 60.0},
            {"outstanding_instruments": 50, "exercise_price": 180.0},
        ],
    }
    inventory = build_ai_dilution_inventory(_base(), rows, market_price_package=_market())
    option_row = inventory["categories"][0]
    assert option_row["adjustment_shares"] == expected


def test_tranche_tsm_requires_complete_outstanding_reconciliation() -> None:
    rows = _complete_rows()
    rows[0]["calculation_method"] = TSM_TRANCHES_METHOD
    rows[0]["adjustment_shares"] = 25.0
    rows[0]["calculation_inputs"] = {
        "total_outstanding_instruments": 100,
        "tranches": [{"outstanding_instruments": 50, "exercise_price": 60.0}],
    }
    with pytest.raises(CaseServiceError, match="total mismatch"):
        build_ai_dilution_inventory(_base(), rows, market_price_package=_market())
