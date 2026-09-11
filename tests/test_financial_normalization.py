"""M15 financial normalization and TTM invariants / 재무정규화·TTM 불변조건."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub.dart_live import DartTransportResponse, capture_dart_snapshot, extract_dart_evidence_candidate
from valuation_hub.financial_normalization import (
    DURATION_ANNUAL,
    DURATION_QUARTER,
    DURATION_TTM,
    DURATION_YTD,
    INSTANT,
    normalize_dart_candidate,
    normalize_sec_candidate,
    reconcile_same_period,
    ttm_annual_bridge,
    ttm_four_quarters,
    validate_financial_observation,
    validate_ttm_result,
)
from valuation_hub.sec_live import TransportResponse, capture_companyfacts_snapshot, extract_sec_evidence_candidate

ROOT = Path(__file__).resolve().parents[1]
SEC_FIXTURE = ROOT / "tests" / "fixtures" / "sec_companyfacts_sample.json"
DART_FIXTURE = ROOT / "tests" / "fixtures" / "opendart_financials_sample.json"
SEC_AGENT = "Valuation-Intelligence-Hub test@example.com"
DART_KEY = "K" * 40


def _sec_snapshot() -> dict:
    body = SEC_FIXTURE.read_bytes()
    def transport(locator: str, *, user_agent: str) -> TransportResponse:
        assert user_agent == SEC_AGENT
        return TransportResponse(200, "application/json", body, locator)
    return capture_companyfacts_snapshot(1234567, user_agent=SEC_AGENT, transport=transport, fetched_at="2026-09-11T06:30:00+00:00")


def _dart_snapshot() -> dict:
    body = DART_FIXTURE.read_bytes()
    def transport(locator: str, *, api_key: str) -> DartTransportResponse:
        assert api_key == DART_KEY
        return DartTransportResponse(200, "application/json", body, locator)
    return capture_dart_snapshot("00126380", 2026, "11012", "CFS", api_key=DART_KEY, transport=transport, fetched_at="2026-09-11T07:40:00+00:00")


def _quarter(value: int, fy: int, fq: int, *, entity: str = "DART_CORP:00126380", scope: str = "CFS", unit: str = "KRW", klass: str = "NORMALIZED_FACT_CANDIDATE") -> dict:
    obs = {
        "schema_version": "financial-observation-v0.1",
        "status": "FINANCIAL_OBSERVATION_NORMALIZED",
        "canonical": False,
        "class": klass,
        "metric": "revenue",
        "value": value,
        "unit": unit,
        "entity": {"id": entity, "source_system": "TEST", "financial_scope": scope},
        "period": {"kind": DURATION_QUARTER, "start": None, "end": None, "duration_days": None, "fiscal_year": fy, "fiscal_period": f"Q{fq}", "fiscal_quarter": fq, "report_stage": f"Q{fq}", "date_precision": "TEST"},
        "lineage": {"normalization_rule": "TEST_FIXTURE", "source_candidate_sha256": "a" * 64},
        "observation_sha256": "",
    }
    import hashlib, json
    payload = copy.deepcopy(obs); payload.pop("observation_sha256", None)
    obs["observation_sha256"] = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return obs


def _with_period(base: dict, *, value: int, kind: str, fy: int, fq: int, stage: str) -> dict:
    obs = copy.deepcopy(base)
    obs["value"] = value
    obs["period"].update({"kind": kind, "fiscal_year": fy, "fiscal_quarter": fq, "report_stage": stage})
    import hashlib, json
    payload = copy.deepcopy(obs); payload.pop("observation_sha256", None)
    obs["observation_sha256"] = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return obs


def test_sec_instant_normalizes_and_preserves_candidate_authority() -> None:
    candidate = extract_sec_evidence_candidate(_sec_snapshot(), "assets")
    obs = normalize_sec_candidate(candidate)
    assert obs["period"]["kind"] == INSTANT
    assert obs["class"] == "NORMALIZED_FACT_CANDIDATE"
    assert obs["entity"]["id"] == "SEC_CIK:0001234567"
    assert validate_financial_observation(obs)["period_kind"] == INSTANT


def test_sec_10q_requires_explicit_quarter_or_ytd_semantics() -> None:
    candidate = extract_sec_evidence_candidate(_sec_snapshot(), "revenue", form="10-Q")
    with pytest.raises(CaseServiceError, match="requires explicit|명시"):
        normalize_sec_candidate(candidate)
    start = candidate["period"]["start"]
    end = candidate["period"]["end"]
    days = (__import__("datetime").date.fromisoformat(end) - __import__("datetime").date.fromisoformat(start)).days + 1
    declared = DURATION_QUARTER if days <= 120 else DURATION_YTD
    obs = normalize_sec_candidate(candidate, declared_period_kind=declared)
    assert obs["period"]["kind"] == declared


def test_reviewed_fact_input_propagates_to_normalized_fact_without_becoming_canonical() -> None:
    candidate = extract_dart_evidence_candidate(_dart_snapshot(), "assets")
    candidate["class"] = "FACT"
    obs = normalize_dart_candidate(candidate)
    assert obs["class"] == "NORMALIZED_FACT"
    assert obs["canonical"] is False


def test_dart_current_and_cumulative_period_semantics_are_distinct() -> None:
    candidate = extract_dart_evidence_candidate(_dart_snapshot(), "revenue")
    quarter = normalize_dart_candidate(candidate, amount_basis="CURRENT")
    ytd = normalize_dart_candidate(candidate, amount_basis="CUMULATIVE")
    assert quarter["period"]["kind"] == DURATION_QUARTER
    assert quarter["value"] == 165_000_000_000
    assert ytd["period"]["kind"] == DURATION_YTD
    assert ytd["value"] == 330_000_000_000
    assert quarter["period"]["date_precision"] == "REPORT_STAGE_ONLY"
    assert ytd["lineage"]["source_detail"]["raw_cumulative"] == "330,000,000,000"


def test_observation_hash_tamper_is_detected() -> None:
    obs = normalize_dart_candidate(extract_dart_evidence_candidate(_dart_snapshot(), "assets"))
    obs["value"] += 1
    with pytest.raises(CaseServiceError, match="SHA-256"):
        validate_financial_observation(obs)


def test_four_quarter_ttm_requires_contiguous_compatible_quarters() -> None:
    quarters = [_quarter(10, 2025, 3), _quarter(20, 2025, 4), _quarter(30, 2026, 1), _quarter(40, 2026, 2)]
    result = ttm_four_quarters(quarters)
    assert result["value"] == 100
    assert result["period"]["kind"] == DURATION_TTM
    assert result["transform"]["components"] == [10, 20, 30, 40]
    assert validate_ttm_result(result)["status"] == "PASS_TTM_VALIDATION"

    gap = [quarters[0], quarters[1], quarters[2], _quarter(50, 2026, 3)]
    with pytest.raises(CaseServiceError, match="duplicate|gap|중복|공백"):
        ttm_four_quarters(gap)
    mixed = copy.deepcopy(quarters)
    mixed[-1] = _quarter(40, 2026, 2, unit="USD")
    with pytest.raises(CaseServiceError, match="compatibility|호환성"):
        ttm_four_quarters(mixed)


def test_annual_bridge_exact_formula_and_stage_guard() -> None:
    base = _quarter(1, 2025, 1)
    annual = _with_period(base, value=1000, kind=DURATION_ANNUAL, fy=2025, fq=4, stage="FY")
    current_ytd = _with_period(base, value=600, kind=DURATION_YTD, fy=2026, fq=2, stage="H1")
    prior_ytd = _with_period(base, value=450, kind=DURATION_YTD, fy=2025, fq=2, stage="H1")
    result = ttm_annual_bridge(annual, current_ytd, prior_ytd)
    assert result["value"] == 1150
    assert result["transform"]["components"] == {"prior_fy": 1000, "current_ytd": 600, "prior_comparable_ytd": 450}

    wrong_stage = _with_period(prior_ytd, value=450, kind=DURATION_YTD, fy=2025, fq=3, stage="Q3")
    with pytest.raises(CaseServiceError, match="stages|단계"):
        ttm_annual_bridge(annual, current_ytd, wrong_stage)


def test_same_period_reconciliation_never_averages_conflicts() -> None:
    left = _quarter(25, 2026, 1)
    right = copy.deepcopy(left)
    right["class"] = "NORMALIZED_FACT"
    import hashlib, json
    payload = copy.deepcopy(right); payload.pop("observation_sha256", None)
    right["observation_sha256"] = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    chosen = reconcile_same_period([left, right])
    assert chosen["class"] == "NORMALIZED_FACT"

    conflict = copy.deepcopy(right)
    conflict["value"] = 26
    payload = copy.deepcopy(conflict); payload.pop("observation_sha256", None)
    conflict["observation_sha256"] = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    with pytest.raises(CaseServiceError, match="UNKNOWN_CONFLICT"):
        reconcile_same_period([left, conflict])
