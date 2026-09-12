"""M18 governed derived financial evidence tests / 거버넌스 파생재무근거 테스트."""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub.derived_financial import (
    derive_historical_net_income_margin,
    derive_historical_operating_margin,
    validate_derived_financial_evidence,
)
from valuation_hub.draft_binding import build_binding_proposal
from valuation_hub.financial_normalization import DURATION_ANNUAL


def _sha(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _obs(metric: str, value: int | float, *, klass: str = "NORMALIZED_FACT", entity: str = "DART_CORP:00126380", scope: str = "CFS", unit: str = "KRW", fiscal_year: int = 2025) -> dict:
    result = {
        "schema_version": "financial-observation-v0.1",
        "status": "FINANCIAL_OBSERVATION_NORMALIZED",
        "canonical": False,
        "class": klass,
        "metric": metric,
        "value": value,
        "unit": unit,
        "entity": {"id": entity, "source_system": "TEST", "financial_scope": scope},
        "period": {
            "kind": DURATION_ANNUAL,
            "start": "2025-01-01",
            "end": "2025-12-31",
            "duration_days": 365,
            "fiscal_year": fiscal_year,
            "fiscal_period": "FY",
            "fiscal_quarter": 4,
            "report_stage": "FY",
            "date_precision": "EXACT",
        },
        "lineage": {"normalization_rule": "TEST_NORMALIZATION_V01"},
        "observation_sha256": "",
    }
    payload = copy.deepcopy(result)
    payload.pop("observation_sha256")
    result["observation_sha256"] = _sha(payload)
    return result


def _rehash(obs: dict) -> dict:
    payload = copy.deepcopy(obs)
    payload.pop("observation_sha256", None)
    obs["observation_sha256"] = _sha(payload)
    return obs


def test_operating_margin_is_deterministic_historical_derived_fact() -> None:
    result = derive_historical_operating_margin(_obs("operating_income", 120), _obs("revenue", 1000))
    assert result["value"] == 0.12
    assert result["class"] == "DERIVED_FACT"
    assert result["unit"] == "ratio"
    assert result["semantic_boundary"] ["historical_only"] is True
    assert result["semantic_boundary"] ["forecast_direct_bind"] is False
    assert validate_derived_financial_evidence(result)["status"] == "PASS_DERIVED_FINANCIAL_EVIDENCE_VALIDATION"


def test_candidate_input_propagates_candidate_authority() -> None:
    result = derive_historical_net_income_margin(
        _obs("net_income", 70, klass="NORMALIZED_FACT_CANDIDATE"),
        _obs("revenue", 1000),
    )
    assert result["value"] == 0.07
    assert result["class"] == "DERIVED_FACT_CANDIDATE"


def test_entity_scope_unit_and_period_mismatch_fail_closed() -> None:
    numerator = _obs("operating_income", 100)
    with pytest.raises(CaseServiceError, match="entity mismatch|entity 불일치"):
        derive_historical_operating_margin(numerator, _obs("revenue", 1000, entity="DART_CORP:OTHER"))
    with pytest.raises(CaseServiceError, match="scope mismatch|재무범위 불일치"):
        derive_historical_operating_margin(numerator, _obs("revenue", 1000, scope="OFS"))
    with pytest.raises(CaseServiceError, match="unit mismatch|unit 불일치"):
        derive_historical_operating_margin(numerator, _obs("revenue", 1000, unit="USD"))
    with pytest.raises(CaseServiceError, match="period identity mismatch|기간식별 불일치"):
        derive_historical_operating_margin(numerator, _obs("revenue", 1000, fiscal_year=2024))


def test_zero_revenue_and_wrong_metric_fail_closed() -> None:
    with pytest.raises(CaseServiceError, match="nonzero|0일 수 없음"):
        derive_historical_operating_margin(_obs("operating_income", 10), _obs("revenue", 0))
    with pytest.raises(CaseServiceError, match="operating_income|분자 지표 오류"):
        derive_historical_operating_margin(_obs("net_income", 10), _obs("revenue", 100))


def test_derived_hash_and_arithmetic_tampering_are_detected() -> None:
    result = derive_historical_operating_margin(_obs("operating_income", 120), _obs("revenue", 1000))
    tampered = copy.deepcopy(result)
    tampered["value"] = 0.13
    with pytest.raises(CaseServiceError, match="arithmetic mismatch|산술 불일치"):
        validate_derived_financial_evidence(tampered)

    tampered = copy.deepcopy(result)
    tampered["semantic_boundary"]["forecast_direct_bind"] = True
    with pytest.raises(CaseServiceError, match="semantic boundary|의미경계"):
        validate_derived_financial_evidence(tampered)


def test_historical_ratio_cannot_enter_m16_direct_binding_pipeline() -> None:
    derived = derive_historical_operating_margin(_obs("operating_income", 120), _obs("revenue", 1000))
    with pytest.raises(CaseServiceError):
        build_binding_proposal([derived], as_of="2026-09-11", max_age_days=550)
