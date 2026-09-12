"""M19 governed interest-bearing debt component tests."""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub import dart_live, financial_normalization, sec_live
from valuation_hub.debt_components import (
    COMPLETE,
    CONFLICT,
    CORE_COMPONENTS,
    PARTIAL,
    SEC_COMPONENT_SUPPORT,
    aggregate_interest_bearing_debt,
    validate_interest_bearing_debt_evidence,
)


def _sha(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _obs(metric: str, value: int | float, *, klass: str = "NORMALIZED_FACT", entity: str = "DART_CORP:00126380", scope: str = "CFS", unit: str = "KRW", end: str = "2026-06-30") -> dict:
    item = {
        "schema_version": "financial-observation-v0.1",
        "status": "FINANCIAL_OBSERVATION_NORMALIZED",
        "canonical": False,
        "class": klass,
        "metric": metric,
        "value": value,
        "unit": unit,
        "entity": {"id": entity, "source_system": "TEST", "financial_scope": scope},
        "period": {"kind": "INSTANT", "start": None, "end": end, "duration_days": None, "fiscal_year": 2026, "fiscal_period": "H1", "fiscal_quarter": 2, "report_stage": "H1", "date_precision": "EXACT"},
        "lineage": {"normalization_rule": "TEST_DEBT_COMPONENT_V01", "source_detail": {"account_id": metric}},
        "observation_sha256": "",
    }
    payload = copy.deepcopy(item); payload.pop("observation_sha256")
    item["observation_sha256"] = _sha(payload)
    return item


def _all(*, klass: str = "NORMALIZED_FACT") -> list[dict]:
    return [_obs(metric, (index + 1) * 100, klass=klass) for index, metric in enumerate(CORE_COMPONENTS)]


def test_source_mappings_are_conservative_and_exact() -> None:
    assert SEC_COMPONENT_SUPPORT == {"short_term_borrowings"}
    assert sec_live.METRIC_SPECS["short_term_borrowings"].concepts == (("us-gaap", "ShortTermBorrowings"),)
    assert set(CORE_COMPONENTS).issubset(dart_live.DART_METRIC_SPECS)
    assert dart_live.DART_METRIC_SPECS["short_term_borrowings"].account_ids == ("ifrs-full_ShorttermBorrowings",)
    assert dart_live.DART_METRIC_SPECS["current_portion_bonds"].account_ids == ("ifrs-full_CurrentPortionOfBondsIssued",)
    assert set(CORE_COMPONENTS).issubset(financial_normalization.INSTANT_METRICS)


def test_complete_reviewed_components_produce_eligible_debt_value() -> None:
    result = aggregate_interest_bearing_debt(_all())
    assert result["coverage"]["status"] == COMPLETE
    assert result["known_component_sum"] == 1500
    assert result["interest_bearing_debt_value"] == 1500
    assert result["class"] == "DERIVED_FACT"
    assert result["semantic_boundary"]["eligible_for_draft_direct_bind"] is True
    assert result["semantic_boundary"]["total_liabilities_used"] is False
    assert result["semantic_boundary"]["lease_liabilities_included"] is False
    assert validate_interest_bearing_debt_evidence(result)["status"] == "PASS_INTEREST_BEARING_DEBT_VALIDATION"


def test_partial_components_expose_known_sum_but_not_debt_total() -> None:
    observations = _all()[:-1]
    result = aggregate_interest_bearing_debt(observations)
    assert result["coverage"]["status"] == PARTIAL
    assert result["coverage"]["missing_components"] == ["bonds_noncurrent"]
    assert result["known_component_sum"] == 1000
    assert result["interest_bearing_debt_value"] is None
    assert result["semantic_boundary"]["missing_as_zero"] is False
    assert result["semantic_boundary"]["eligible_for_draft_direct_bind"] is False


def test_complete_candidate_components_never_become_reviewed_or_bindable() -> None:
    observations = _all()
    observations[2] = _obs(CORE_COMPONENTS[2], 300, klass="NORMALIZED_FACT_CANDIDATE")
    result = aggregate_interest_bearing_debt(observations)
    assert result["coverage"]["status"] == COMPLETE
    assert result["class"] == "DERIVED_FACT_CANDIDATE"
    assert result["interest_bearing_debt_value"] == 1500
    assert result["semantic_boundary"]["eligible_for_draft_direct_bind"] is False


def test_equal_duplicate_reconciles_to_reviewed_but_conflict_blocks_total() -> None:
    observations = _all()
    observations.append(_obs("short_term_borrowings", 100, klass="NORMALIZED_FACT_CANDIDATE"))
    result = aggregate_interest_bearing_debt(observations)
    assert result["coverage"]["status"] == COMPLETE
    component = next(item for item in result["components"] if item["metric"] == "short_term_borrowings")
    assert component["class"] == "NORMALIZED_FACT"

    conflicting = _all()
    conflicting.append(_obs("short_term_borrowings", 999))
    blocked = aggregate_interest_bearing_debt(conflicting)
    assert blocked["coverage"]["status"] == CONFLICT
    assert blocked["coverage"]["conflict_components"] == ["short_term_borrowings"]
    assert blocked["known_component_sum"] is None
    assert blocked["interest_bearing_debt_value"] is None
    assert blocked["semantic_boundary"]["eligible_for_draft_direct_bind"] is False


def test_liabilities_and_identity_mismatches_fail_closed() -> None:
    with pytest.raises(CaseServiceError, match="explicit debt components|명시적 debt 구성요소"):
        aggregate_interest_bearing_debt([_obs("liabilities", 5000)])
    base = _all()
    bad = copy.deepcopy(base); bad[-1] = _obs(CORE_COMPONENTS[-1], 500, scope="OFS")
    with pytest.raises(CaseServiceError, match="mismatch|불일치"):
        aggregate_interest_bearing_debt(bad)
    bad = copy.deepcopy(base); bad[-1] = _obs(CORE_COMPONENTS[-1], 500, unit="USD")
    with pytest.raises(CaseServiceError, match="mismatch|불일치"):
        aggregate_interest_bearing_debt(bad)
    bad = copy.deepcopy(base); bad[-1] = _obs(CORE_COMPONENTS[-1], 500, end="2026-03-31")
    with pytest.raises(CaseServiceError, match="mismatch|불일치"):
        aggregate_interest_bearing_debt(bad)


def test_hash_and_coverage_tampering_are_detected() -> None:
    result = aggregate_interest_bearing_debt(_all())
    tampered = copy.deepcopy(result); tampered["interest_bearing_debt_value"] = 9999
    with pytest.raises(CaseServiceError):
        validate_interest_bearing_debt_evidence(tampered)
    tampered = copy.deepcopy(result); tampered["semantic_boundary"]["total_liabilities_used"] = True
    with pytest.raises(CaseServiceError, match="semantic boundary|의미경계"):
        validate_interest_bearing_debt_evidence(tampered)
