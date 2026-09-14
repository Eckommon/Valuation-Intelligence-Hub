"""M30-P1 reviewed SEC aggregate-debt successor regressions."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from valuation_hub.binding_apply_m28 import apply_binding_approval, build_binding_approval
from valuation_hub.case_service import CaseServiceError
from valuation_hub.debt_draft_binding_m30 import (
    build_binding_proposal_with_sec_aggregate_debt,
    validate_binding_proposal_sec_aggregate,
)
from valuation_hub.draft_binding import MATERIAL_FIELDS
from valuation_hub.forecast_assumption import (
    build_forecast_candidate,
    build_forecast_review_assertion,
    finalize_reviewed_forecast,
)
from valuation_hub.forecast_draft_binding import (
    build_binding_proposal_with_forecast,
    validate_binding_proposal_any as validate_latest_proposal,
)
from valuation_hub.market_price import (
    build_market_price_candidate,
    build_market_price_review_assertion,
    finalize_reviewed_market_price,
)
from valuation_hub.market_price_draft_binding import build_binding_proposal_with_market_price
from valuation_hub.minority_interest import (
    build_minority_interest_review_assertion,
    extract_sec_minority_interest_candidate,
    finalize_reviewed_minority_interest,
    normalize_minority_interest_candidate,
)
from valuation_hub.minority_interest_draft_binding import build_binding_proposal_with_minority_interest
from valuation_hub.promotion_m29 import (
    OBSERVED_FIELD_CLASSES,
    build_complete_equity_candidate,
    build_evidence_catalog_claim,
    promotion_check,
    review_scope_sha256 as promotion_review_scope_sha256,
)
from valuation_hub.sec_aggregate_debt import (
    SEMANTIC_DECISION,
    build_sec_aggregate_debt_binding_context,
    build_sec_aggregate_debt_review_assertion,
    extract_sec_aggregate_debt_candidate,
    finalize_reviewed_sec_aggregate_debt,
    normalize_sec_aggregate_debt_candidate,
    validate_reviewed_sec_aggregate_debt,
    validate_sec_aggregate_debt_candidate,
)
from valuation_hub.sec_live import TransportResponse, capture_companyfacts_snapshot, companyfacts_locator
from valuation_hub.share_draft_binding import build_binding_proposal_with_diluted_shares
from valuation_hub.terminal_growth_assumption import (
    LONG_RUN_INFLATION,
    LONG_RUN_REAL_GROWTH,
    build_terminal_growth_anchor_input,
    build_terminal_growth_candidate,
    build_terminal_growth_review_assertion,
    finalize_reviewed_terminal_growth,
)
from valuation_hub.terminal_growth_draft_binding import build_binding_proposal_with_terminal_growth
from valuation_hub.valuation_shares import (
    ADJUSTMENT_CATEGORIES,
    build_diluted_share_bridge,
    build_dilution_adjustment,
    build_dilution_coverage_assertion,
    build_valuation_share_base_context,
    validate_dilution_adjustment,
)
from valuation_hub.wacc_assumption import (
    DEBT_MARKET_VALUE,
    EQUITY_MARKET_VALUE,
    EQUITY_RISK_PREMIUM,
    LEVERED_BETA,
    PRE_TAX_COST_OF_DEBT,
    RISK_FREE_RATE,
    TAX_RATE,
    build_wacc_candidate,
    build_wacc_review_assertion,
    build_wacc_source_input,
    finalize_reviewed_wacc,
)
from valuation_hub.wacc_draft_binding import build_binding_proposal_with_wacc

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "draft_equity_fcff.json"
CIK = "0001046257"
ENTITY = f"SEC_CIK:{CIK}"
SCOPE = "CFS"
AS_OF = "2026-09-14"
ACCN = "0001628280-26-054722"
DEBT_VALUE = 1_783_000_000


def _rehash(value: dict, field: str) -> str:
    copied = copy.deepcopy(value)
    copied.pop(field, None)
    return hashlib.sha256(
        json.dumps(copied, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _payload(*, debt_values: list[int] | None = None, include_debt: bool = True) -> dict:
    debt_values = debt_values or [DEBT_VALUE]
    us_gaap: dict[str, dict] = {
        "NonredeemableNoncontrollingInterest": {
            "units": {"USD": [{"val": 0, "end": "2026-06-30", "fy": 2026, "fp": "Q2", "form": "10-Q", "filed": "2026-08-07", "accn": ACCN}]}
        }
    }
    if include_debt:
        us_gaap["DebtLongtermAndShorttermCombinedAmount"] = {
            "units": {
                "USD": [
                    {"val": value, "end": "2026-06-30", "fy": 2026, "fp": "Q2", "form": "10-Q", "filed": "2026-08-07", "accn": ACCN}
                    for value in debt_values
                ]
            }
        }
    return {"cik": 1046257, "entityName": "Ingredion Incorporated", "facts": {"us-gaap": us_gaap}}


def _snapshot(*, debt_values: list[int] | None = None, include_debt: bool = True) -> dict:
    body = json.dumps(_payload(debt_values=debt_values, include_debt=include_debt), separators=(",", ":")).encode()

    def transport(locator: str, *, user_agent: str):
        assert locator == companyfacts_locator(CIK)
        assert user_agent == "M30-P1-test test@example.com"
        return TransportResponse(200, "application/json; charset=utf-8", body, locator)

    return capture_companyfacts_snapshot(
        CIK,
        user_agent="M30-P1-test test@example.com",
        transport=transport,
        fetched_at="2026-09-14T00:00:00+00:00",
    )


def _reviewed_debt(snapshot: dict | None = None):
    candidate = extract_sec_aggregate_debt_candidate(snapshot or _snapshot(), form="10-Q", period_end="2026-06-30")
    observation = normalize_sec_aggregate_debt_candidate(candidate)
    assertion = build_sec_aggregate_debt_review_assertion(
        observation,
        reviewer="M30 debt reviewer",
        reviewed_at="2026-09-14T09:15:00+09:00",
        review_basis="Reviewed issuer filing reconciliation: total debt equals reported short-term borrowings plus reported long-term debt, excluding lease liabilities from this project boundary.",
        source_basis_locator="repo://m30-p1/ingredion-2026-q2-debt-note",
        semantic_scope_decision=SEMANTIC_DECISION,
    )
    profile = finalize_reviewed_sec_aggregate_debt(observation, assertion)
    context = build_sec_aggregate_debt_binding_context(profile, as_of=AS_OF, max_age_days=550)
    return candidate, observation, assertion, profile, context


def _cash_observation() -> dict:
    value = {
        "schema_version": "financial-observation-v0.1",
        "status": "FINANCIAL_OBSERVATION_NORMALIZED",
        "canonical": False,
        "class": "NORMALIZED_FACT",
        "metric": "cash",
        "value": 948_000_000,
        "unit": "USD",
        "entity": {"id": ENTITY, "source_system": "SEC", "financial_scope": SCOPE},
        "period": {"kind": "INSTANT", "start": None, "end": "2026-06-30", "duration_days": None, "fiscal_year": 2026, "fiscal_period": "Q2", "fiscal_quarter": 2, "report_stage": "Q2", "date_precision": "EXACT"},
        "lineage": {"normalization_rule": "TEST_SEC_CASH", "source_candidate_sha256": "a" * 64},
        "observation_sha256": "",
    }
    value["observation_sha256"] = _rehash(value, "observation_sha256")
    return value


def _share_observation() -> dict:
    value = {
        "schema_version": "current-common-shares-observation-v0.1",
        "status": "CURRENT_COMMON_SHARES_OBSERVATION_NORMALIZED",
        "canonical": False,
        "class": "NORMALIZED_FACT",
        "metric": "current_common_shares",
        "value": 63_063_979,
        "unit": "shares",
        "entity": {"id": ENTITY, "source_system": "SEC", "financial_scope": SCOPE},
        "period": {"kind": "INSTANT", "start": None, "end": "2026-08-05", "date_precision": "EXACT"},
        "lineage": {
            "normalization_rule": "SEC_DEI_CURRENT_COMMON_SHARES_INSTANT_V01",
            "source_candidate_sha256": "b" * 64,
            "source_class": "FACT",
            "source_snapshot_sha256": "c" * 64,
            "source_body_sha256": "d" * 64,
            "filing_identity": {"accession": ACCN, "form": "10-Q", "filed": "2026-08-07"},
            "source_detail": {"taxonomy": "dei", "concept": "EntityCommonStockSharesOutstanding"},
        },
        "semantic_boundary": {"current_common_shares_only": True, "fully_diluted_shares": False},
        "observation_sha256": "",
    }
    value["observation_sha256"] = _rehash(value, "observation_sha256")
    return value


def _share_bridge() -> dict:
    base = build_valuation_share_base_context(_share_observation(), as_of=AS_OF, max_age_days=180)
    adjustment = build_dilution_adjustment(
        adjustment_id="M30-P1-OPT-1",
        category="options_treasury_stock_method",
        shares=250_000,
        source_sha256="e" * 64,
        source_description="Reviewed M30-P1 treasury-stock-method dilution fixture.",
    )
    adjustment["class"] = "NORMALIZED_FACT"
    adjustment["adjustment_sha256"] = _rehash(adjustment, "adjustment_sha256")
    validate_dilution_adjustment(adjustment)
    assertion = build_dilution_coverage_assertion(
        base,
        [adjustment],
        reviewer="M30 share reviewer",
        approved_at="2026-09-14T09:20:00+09:00",
        coverage_basis="All supported dilution categories explicitly reviewed for successor integration.",
        reviewed_categories=list(ADJUSTMENT_CATEGORIES),
    )
    return build_diluted_share_bridge(base, [adjustment], coverage_assertion=assertion)


def _wsrc(metric: str, value: float, unit: str, claim: str = "FACT") -> dict:
    return build_wacc_source_input(
        metric=metric,
        value=value,
        unit=unit,
        observed_on="2026-09-01",
        claim_class=claim,
        source_publisher="M30 test",
        source_type="TEST",
        source_tier="A",
        source_locator=f"repo://m30/wacc/{metric}",
        source_sha256=hashlib.sha256(("m30-" + metric).encode()).hexdigest(),
    )


def _wacc_package() -> dict:
    inputs = [
        _wsrc(RISK_FREE_RATE, 0.0436, "decimal"),
        _wsrc(EQUITY_RISK_PREMIUM, 0.0418, "decimal", "ASSUMPTION"),
        _wsrc(LEVERED_BETA, 0.85, "ratio", "ASSUMPTION"),
        _wsrc(PRE_TAX_COST_OF_DEBT, 0.05, "decimal", "ASSUMPTION"),
        _wsrc(EQUITY_MARKET_VALUE, 8_000_000_000.0, "USD"),
        _wsrc(DEBT_MARKET_VALUE, float(DEBT_VALUE), "USD"),
        _wsrc(TAX_RATE, 0.25, "decimal", "ASSUMPTION"),
    ]
    candidate = build_wacc_candidate(inputs, entity_id=ENTITY, financial_scope=SCOPE, capital_currency="USD", as_of=AS_OF, scenario_names=["BASE"])
    assertion = build_wacc_review_assertion(candidate, reviewer="M30 WACC reviewer", approved_at="2026-09-14T09:25:00+09:00", review_basis="Reviewed M30-P1 WACC fixture.")
    return finalize_reviewed_wacc(candidate, assertion)


def _terminal_package(wacc: dict) -> dict:
    anchors = [
        build_terminal_growth_anchor_input(metric=LONG_RUN_INFLATION, value=0.02, observed_on="2026-06-01", claim_class="ASSUMPTION", source_publisher="M30 macro", source_type="FORECAST", source_tier="A", source_locator="repo://m30/inflation", source_sha256="f" * 64),
        build_terminal_growth_anchor_input(metric=LONG_RUN_REAL_GROWTH, value=0.015, observed_on="2026-06-01", claim_class="ASSUMPTION", source_publisher="M30 macro", source_type="FORECAST", source_tier="A", source_locator="repo://m30/real-growth", source_sha256="1" * 64),
    ]
    candidate = build_terminal_growth_candidate(anchors, wacc, scenario_assumptions=[{"scenario_name": "BASE", "terminal_growth": 0.025, "rationale": "Reviewed long-run BASE growth."}])
    assertion = build_terminal_growth_review_assertion(candidate, reviewer="M30 terminal reviewer", approved_at="2026-09-14T09:30:00+09:00", review_basis="Reviewed M30-P1 terminal growth fixture.")
    return finalize_reviewed_terminal_growth(candidate, assertion)


def _forecast_package() -> dict:
    rows = [
        {"year": year, "revenue": revenue, "ebit_margin": margin, "tax_rate": 0.25, "depreciation_amortization": da, "capex": capex, "delta_nwc": nwc}
        for year, revenue, margin, da, capex, nwc in [
            (2027, 8_500_000_000.0, 0.10, 350_000_000.0, 420_000_000.0, 120_000_000.0),
            (2028, 8_900_000_000.0, 0.105, 365_000_000.0, 430_000_000.0, 110_000_000.0),
            (2029, 9_300_000_000.0, 0.11, 380_000_000.0, 440_000_000.0, 100_000_000.0),
            (2030, 9_700_000_000.0, 0.115, 395_000_000.0, 450_000_000.0, 90_000_000.0),
        ]
    ]
    candidate = build_forecast_candidate([{"scenario_name": "BASE", "rationale": "Reviewed BASE operating forecast.", "years": rows}], entity_id=ENTITY, financial_scope=SCOPE, capital_currency="USD", as_of=AS_OF)
    assertion = build_forecast_review_assertion(candidate, reviewer="M30 forecast reviewer", approved_at="2026-09-14T09:35:00+09:00", review_basis="Reviewed all M30-P1 forecast rows and FCFF diagnostics.")
    return finalize_reviewed_forecast(candidate, assertion)


def _market_price_package() -> dict:
    candidate = build_market_price_candidate(
        price=126.50,
        currency="USD",
        entity_id=ENTITY,
        financial_scope=SCOPE,
        instrument_id="TEST-INGR",
        symbol="INGR",
        venue="NYSE",
        quote_type="OFFICIAL_CLOSE",
        trading_date="2026-09-11",
        observed_at="2026-09-11T16:00:00-04:00",
        as_of=AS_OF,
        source_publisher="NYSE test fixture",
        source_type="official_exchange_close",
        source_tier="A",
        source_locator="repo://m30/market/ingr",
        source_snapshot_sha256="2" * 64,
        max_age_days=7,
    )
    assertion = build_market_price_review_assertion(candidate, reviewer="M30 market reviewer", approved_at="2026-09-14T09:40:00+09:00", review_basis="Reviewed exact exchange quote identity and freshness.")
    return finalize_reviewed_market_price(candidate, assertion)


def _minority_package() -> dict:
    candidate = extract_sec_minority_interest_candidate(_snapshot(), form="10-Q", period_end="2026-06-30")
    observation = normalize_minority_interest_candidate(candidate)
    assertion = build_minority_interest_review_assertion(
        observation,
        as_of=AS_OF,
        reviewer="M30 NCI reviewer",
        approved_at="2026-09-14T09:45:00+09:00",
        review_basis="Reviewed exact SEC nonredeemable noncontrolling-interest fact; explicit zero preserved.",
        max_age_days=550,
    )
    return finalize_reviewed_minority_interest(observation, assertion)


def _complete_chain():
    _, _, _, profile, debt_context = _reviewed_debt()
    v02 = build_binding_proposal_with_sec_aggregate_debt([_cash_observation()], debt_context, as_of=AS_OF, max_age_days=550)
    v03 = build_binding_proposal_with_diluted_shares(v02, _share_bridge())
    wacc = _wacc_package()
    v04 = build_binding_proposal_with_wacc(v03, wacc)
    v05 = build_binding_proposal_with_terminal_growth(v04, _terminal_package(wacc))
    v06 = build_binding_proposal_with_forecast(v05, _forecast_package())
    v07 = build_binding_proposal_with_market_price(v06, _market_price_package())
    v08 = build_binding_proposal_with_minority_interest(v07, _minority_package())
    assert validate_latest_proposal(v08)["direct_bind_count"] == len(MATERIAL_FIELDS)
    assert v08["completeness"]["unresolved_count"] == 0
    draft = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    draft["name"] = "M30 SEC aggregate debt successor"
    approval = build_binding_approval(
        v08,
        draft,
        reviewer="M30 complete binding reviewer",
        target_entity_id=ENTITY,
        target_financial_scope=SCOPE,
        approved_fields=list(MATERIAL_FIELDS),
        approved_at="2026-09-14T10:00:00+09:00",
    )
    result = apply_binding_approval(v08, draft, approval)
    return profile, v08, result


def _catalog(result: dict) -> list[dict]:
    metrics = {"market_price": "market_price", "equity.cash": "cash", "equity.minority_interest": "minority_interest", "equity.debt": "interest_bearing_debt", "equity.diluted_shares": "fully_diluted_shares"}
    return [
        build_evidence_catalog_claim(result, field=field, claim_id=f"M30-OBS-{index:02d}", metric=metrics[field], publisher="M30 integration evidence", locator=f"repo://m30/{field}", tier="A", source_type="TEST_FIXTURE", source_date=AS_OF)
        for index, field in enumerate(OBSERVED_FIELD_CLASSES, start=1)
    ]


def test_exact_sec_aggregate_debt_lifecycle_and_m20_apply() -> None:
    candidate, observation, assertion, profile, context = _reviewed_debt()
    assert candidate["value"] == DEBT_VALUE
    assert candidate["source_identity"] == {"taxonomy": "us-gaap", "concept": "DebtLongtermAndShorttermCombinedAmount"}
    assert observation["class"] == "NORMALIZED_FACT_CANDIDATE"
    assert assertion["semantic_scope_decision"] == SEMANTIC_DECISION
    assert profile["class"] == "NORMALIZED_FACT"
    assert validate_reviewed_sec_aggregate_debt(profile)["eligible"] is True
    proposal = build_binding_proposal_with_sec_aggregate_debt([_cash_observation()], context, as_of=AS_OF)
    checked = validate_binding_proposal_sec_aggregate(proposal)
    assert checked["direct_bind_count"] == 2
    assert "COMPLETE_CORE_COMPONENTS" not in json.dumps(proposal, sort_keys=True)


def test_missing_conflicting_and_resigned_semantic_tamper_fail_closed() -> None:
    with pytest.raises(CaseServiceError, match="concept unavailable|concept 없음"):
        extract_sec_aggregate_debt_candidate(_snapshot(include_debt=False), form="10-Q", period_end="2026-06-30")
    with pytest.raises(CaseServiceError, match="conflict|충돌"):
        extract_sec_aggregate_debt_candidate(_snapshot(debt_values=[DEBT_VALUE, DEBT_VALUE + 1]), form="10-Q", period_end="2026-06-30")

    candidate, _, _, profile, _ = _reviewed_debt()
    forged_candidate = copy.deepcopy(candidate)
    forged_candidate["source_identity"]["concept"] = "Liabilities"
    forged_candidate["candidate_sha256"] = _rehash(forged_candidate, "candidate_sha256")
    with pytest.raises(CaseServiceError, match="exact concept identity|exact concept 식별"):
        validate_sec_aggregate_debt_candidate(forged_candidate)

    forged_profile = copy.deepcopy(profile)
    forged_profile["semantic_boundary"]["lease_liabilities_included"] = True
    forged_profile["profile_sha256"] = _rehash(forged_profile, "profile_sha256")
    with pytest.raises(CaseServiceError, match="semantic boundary|의미경계"):
        validate_reviewed_sec_aggregate_debt(forged_profile)


def test_sec_aggregate_successor_reaches_complete_m28_apply_and_m29_promotion_ready() -> None:
    profile, proposal, result = _complete_chain()
    assert result["unresolved_binding_matrix"] == []
    assert len(result["applied_diffs"]) == len(MATERIAL_FIELDS)
    assert result["draft_after"]["equity"]["debt"] == DEBT_VALUE
    debt_decision = next(row for row in proposal["draft_input_matrix"] if row["field"] == "equity.debt")
    assert debt_decision["source_debt_profile_sha256"] == profile["profile_sha256"]
    debt_diff = next(row for row in result["applied_diffs"] if row["field"] == "equity.debt")
    assert debt_diff["source_debt_sha256"] == profile["profile_sha256"]

    candidate = build_complete_equity_candidate(result, _catalog(result))
    candidate["review"] = {
        "decision": "APPROVE",
        "reviewer": "M30 promotion reviewer",
        "reviewed_at": "2026-09-14T10:05:00+09:00",
        "rationale": "Reviewed complete SEC aggregate-debt successor handoff through M28.",
        "scope_sha256": promotion_review_scope_sha256(candidate),
    }
    readiness = promotion_check(candidate)
    assert readiness["promotion_ready"] is True
    assert readiness["grounding"] == "COMPLETE_GOVERNED_BOUND_RESULT"
