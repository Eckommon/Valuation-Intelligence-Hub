"""M22 valuation-date share-base and diluted-share bridge tests."""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub.sec_live import METRIC_SPECS, TransportResponse, capture_companyfacts_snapshot
from valuation_hub.share_dilution import METRICS as M21_METRICS, validate_historical_dilution
from valuation_hub.valuation_shares import (
    ADJUSTMENT_CATEGORIES,
    BASE_ONLY,
    COMPLETE,
    CONFLICT,
    PARTIAL,
    build_diluted_share_bridge,
    build_dilution_adjustment,
    build_dilution_coverage_assertion,
    build_valuation_share_base_context,
    extract_sec_current_common_shares_candidate,
    normalize_current_common_shares_candidate,
    validate_current_common_shares_candidate,
    validate_diluted_share_bridge,
    validate_dilution_adjustment,
    validate_valuation_share_base_context,
)

FETCHED_AT = "2026-09-12T11:30:00+00:00"


def _digest(value: dict, field: str) -> str:
    payload = copy.deepcopy(value)
    payload.pop(field, None)
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _payload() -> dict:
    return {
        "cik": 1234567,
        "entityName": "Share Bridge Fixture Inc.",
        "facts": {
            "dei": {
                "EntityCommonStockSharesOutstanding": {
                    "units": {
                        "shares": [
                            {"end": "2026-08-01", "val": 1000, "accn": "0001234567-26-000040", "form": "10-Q", "filed": "2026-08-05", "frame": "CY2026Q2I"},
                            {"end": "2026-05-01", "val": 980, "accn": "0001234567-26-000020", "form": "10-Q", "filed": "2026-05-05", "frame": "CY2026Q1I"}
                        ]
                    }
                }
            }
        }
    }


def _snapshot(payload: dict | None = None) -> dict:
    body = json.dumps(payload or _payload(), separators=(",", ":")).encode()
    def transport(locator: str, *, user_agent: str) -> TransportResponse:
        return TransportResponse(status=200, content_type="application/json", body=body, final_locator=locator)
    return capture_companyfacts_snapshot(
        "1234567",
        user_agent="Valuation-Intelligence-Hub test@example.com",
        transport=transport,
        fetched_at=FETCHED_AT,
    )


def _reviewed_candidate(candidate: dict) -> dict:
    out = copy.deepcopy(candidate)
    out["class"] = "FACT"
    out["candidate_sha256"] = _digest(out, "candidate_sha256")
    validate_current_common_shares_candidate(out)
    return out


def _reviewed_adjustment(candidate: dict) -> dict:
    out = copy.deepcopy(candidate)
    out["class"] = "NORMALIZED_FACT"
    out["adjustment_sha256"] = _digest(out, "adjustment_sha256")
    validate_dilution_adjustment(out)
    return out


def _base_context(*, as_of: str = "2026-09-12", max_age_days: int = 180) -> dict:
    candidate = extract_sec_current_common_shares_candidate(_snapshot(), period_end="2026-08-01", form="10-Q")
    observation = normalize_current_common_shares_candidate(_reviewed_candidate(candidate))
    return build_valuation_share_base_context(observation, as_of=as_of, max_age_days=max_age_days)


def _historical_reference() -> dict:
    boundary = {
        "historical_only": True,
        "valuation_date_direct_bind": False,
        "forecast_direct_bind": False,
        "shares_outstanding_substitution": False,
        "warning_en": "Weighted-average diluted EPS shares are historical duration evidence, not valuation-date fully diluted shares.",
        "warning_ko": "기간평균 diluted EPS 주식수는 역사적 기간근거이며 valuation-date 완전희석주식수가 아닙니다.",
    }
    result = {
        "schema_version": "historical-dilution-evidence-v0.1",
        "status": "HISTORICAL_DILUTION_EVIDENCE",
        "canonical": False,
        "class": "DERIVED_FACT",
        "entity": {"id": "SEC_CIK:0001234567", "source_system": "SEC", "financial_scope": "AS_REPORTED"},
        "period": {"kind": "DURATION_QUARTER", "start": "2026-04-01", "end": "2026-06-30"},
        "historical_dilution_factor": 1.1,
        "historical_incremental_diluted_shares": 10,
        "unit": "ratio+shares",
        "sources": [
            {"metric": "weighted_average_basic_shares", "value": 100, "class": "NORMALIZED_FACT", "observation_sha256": "a" * 64},
            {"metric": "weighted_average_diluted_shares", "value": 110, "class": "NORMALIZED_FACT", "observation_sha256": "b" * 64},
        ],
        "semantic_boundary": boundary,
        "derived_sha256": "",
    }
    result["derived_sha256"] = _digest(result, "derived_sha256")
    validate_historical_dilution(result)
    return result


def test_m22_source_registry_isolation_and_exact_dei_mapping() -> None:
    assert set(METRIC_SPECS) == {"revenue", "operating_income", "net_income", "assets", "cash", "shares_outstanding"}
    assert set(M21_METRICS) == {"weighted_average_basic_shares", "weighted_average_diluted_shares"}
    candidate = extract_sec_current_common_shares_candidate(_snapshot(), period_end="2026-08-01", form="10-Q")
    assert candidate["taxonomy"] == "dei"
    assert candidate["concept"] == "EntityCommonStockSharesOutstanding"
    assert candidate["value"] == 1000
    assert candidate["period"]["kind"] == "INSTANT"
    assert candidate["semantic_boundary"]["fully_diluted_shares"] is False


def test_equal_precedence_ambiguous_current_share_values_fail_closed() -> None:
    payload = _payload()
    payload["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"].append(
        {"end": "2026-08-01", "val": 1200, "accn": "0001234567-26-000041", "form": "10-Q", "filed": "2026-08-05"}
    )
    with pytest.raises(CaseServiceError, match="ambiguous equal-precedence"):
        extract_sec_current_common_shares_candidate(_snapshot(payload), period_end="2026-08-01", form="10-Q")


def test_reviewed_instant_builds_recomputable_freshness_context() -> None:
    candidate = extract_sec_current_common_shares_candidate(_snapshot(), period_end="2026-08-01")
    candidate_obs = normalize_current_common_shares_candidate(candidate)
    with pytest.raises(CaseServiceError, match="reviewed fact"):
        build_valuation_share_base_context(candidate_obs, as_of="2026-09-12")

    reviewed = normalize_current_common_shares_candidate(_reviewed_candidate(candidate))
    context = build_valuation_share_base_context(reviewed, as_of="2026-09-12", max_age_days=60)
    assert context["freshness"] == {"status": "FRESH", "age_days": 42, "max_age_days": 60}
    assert context["semantic_boundary"]["direct_bind_to_diluted_shares"] is False

    tampered = copy.deepcopy(context)
    tampered["freshness"]["age_days"] = 1
    tampered["context_sha256"] = _digest(tampered, "context_sha256")
    with pytest.raises(CaseServiceError, match="freshness mismatch"):
        validate_valuation_share_base_context(tampered)


def test_stale_base_remains_base_but_cannot_be_complete_coverage() -> None:
    context = _base_context(as_of="2026-09-12", max_age_days=10)
    assert context["freshness"]["status"] == "STALE_BLOCKED"
    bridge = build_diluted_share_bridge(context, [])
    assert bridge["coverage"]["status"] == BASE_ONLY
    assert bridge["binding_eligibility"]["eligible_for_future_direct_bind"] is False
    with pytest.raises(CaseServiceError, match="fresh base"):
        build_dilution_coverage_assertion(
            context,
            [],
            reviewer="human",
            approved_at="2026-09-12T20:00:00+09:00",
            coverage_basis="All categories reviewed; no dilution instruments found.",
            reviewed_categories=list(ADJUSTMENT_CATEGORIES),
        )


def test_candidate_adjustment_is_partial_and_cannot_be_promoted_by_assertion() -> None:
    context = _base_context()
    adjustment = build_dilution_adjustment(
        adjustment_id="RSU-1",
        category="rsu_restricted_stock",
        shares=50,
        source_sha256="c" * 64,
        source_description="Explicit RSU candidate evidence",
    )
    bridge = build_diluted_share_bridge(context, [adjustment])
    assert bridge["coverage"]["status"] == PARTIAL
    assert bridge["candidate_fully_diluted_shares"] == 1050
    assert bridge["class"] == "DERIVED_FACT_CANDIDATE"
    with pytest.raises(CaseServiceError, match="reviewed adjustment"):
        build_dilution_coverage_assertion(
            context,
            [adjustment],
            reviewer="human",
            approved_at="2026-09-12T20:00:00+09:00",
            coverage_basis="Reviewed all categories.",
            reviewed_categories=list(ADJUSTMENT_CATEGORIES),
        )


def test_reviewed_adjustment_plus_full_human_coverage_can_be_future_bind_eligible() -> None:
    context = _base_context()
    adjustment = _reviewed_adjustment(build_dilution_adjustment(
        adjustment_id="OPT-1",
        category="options_treasury_stock_method",
        shares=25,
        source_sha256="d" * 64,
        source_description="Reviewed option treasury-stock-method evidence",
    ))
    assertion = build_dilution_coverage_assertion(
        context,
        [adjustment],
        reviewer="human-reviewer",
        approved_at="2026-09-12T20:00:00+09:00",
        coverage_basis="All supported dilution categories explicitly reviewed against issuer evidence.",
        reviewed_categories=list(ADJUSTMENT_CATEGORIES),
    )
    bridge = build_diluted_share_bridge(context, [adjustment], coverage_assertion=assertion)
    assert bridge["coverage"]["status"] == COMPLETE
    assert bridge["candidate_fully_diluted_shares"] == 1025
    assert bridge["class"] == "DERIVED_FACT"
    assert bridge["binding_eligibility"]["eligible_for_future_direct_bind"] is True
    assert validate_diluted_share_bridge(bridge)["coverage_status"] == COMPLETE

    tampered = copy.deepcopy(bridge)
    tampered["coverage_assertion"]["coverage_basis"] = "forged"
    tampered["bridge_sha256"] = _digest(tampered, "bridge_sha256")
    with pytest.raises(CaseServiceError, match="assertion SHA"):
        validate_diluted_share_bridge(tampered)


def test_duplicate_adjustment_id_conflict_hides_candidate_total() -> None:
    context = _base_context()
    a = build_dilution_adjustment(adjustment_id="W-1", category="warrants", shares=10, source_sha256="e" * 64, source_description="candidate A")
    b = build_dilution_adjustment(adjustment_id="W-1", category="warrants", shares=20, source_sha256="f" * 64, source_description="candidate B")
    bridge = build_diluted_share_bridge(context, [a, b])
    assert bridge["coverage"]["status"] == CONFLICT
    assert bridge["candidate_fully_diluted_shares"] is None
    assert bridge["binding_eligibility"]["eligible_for_future_direct_bind"] is False


def test_m21_historical_reference_never_auto_creates_current_adjustment() -> None:
    context = _base_context()
    historical = _historical_reference()
    bridge = build_diluted_share_bridge(context, [], historical_reference=historical)
    assert bridge["coverage"]["status"] == BASE_ONLY
    assert bridge["candidate_fully_diluted_shares"] == 1000
    assert bridge["input_adjustments"] == []
    assert bridge["historical_reference"]["reference_only"] is True
    assert bridge["historical_reference"]["auto_adjustment_created"] is False
    assert bridge["semantic_boundary"]["historical_factor_auto_adjustment"] is False
    assert validate_diluted_share_bridge(bridge)["eligible_for_future_direct_bind"] is False
