"""M19 governed interest-bearing debt component tests."""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub import dart_live, sec_live
from valuation_hub.debt_components import (
    COMPLETE,
    CONFLICT,
    CORE_COMPONENTS,
    DART_COMPONENT_SPECS,
    PARTIAL,
    SEC_COMPONENT_SPECS,
    SEC_COMPONENT_SUPPORT,
    aggregate_interest_bearing_debt,
    normalize_debt_component_candidate,
    validate_debt_component_observation,
    validate_interest_bearing_debt_evidence,
)


def _sha(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _obs(metric: str, value: int | float, *, klass: str = "NORMALIZED_FACT", entity: str = "DART_CORP:00126380", scope: str = "CFS", unit: str = "KRW", end: str | None = None) -> dict:
    item = {
        "schema_version": "debt-component-observation-v0.1",
        "status": "DEBT_COMPONENT_NORMALIZED",
        "canonical": False,
        "class": klass,
        "metric": metric,
        "value": value,
        "unit": unit,
        "entity": {"id": entity, "source_system": "TEST", "financial_scope": scope},
        "period": {"kind": "INSTANT", "start": None, "end": end, "duration_days": None, "fiscal_year": 2026, "fiscal_period": "H1", "fiscal_quarter": 2, "report_stage": "H1", "date_precision": "REPORT_STAGE_ONLY" if end is None else "EXACT"},
        "lineage": {"normalization_rule": "TEST_DEBT_COMPONENT_V01", "source_candidate_sha256": "a" * 64, "source_class": "FACT" if klass == "NORMALIZED_FACT" else "FACT_CANDIDATE", "source_snapshot_sha256": "b" * 64, "source_body_sha256": "c" * 64, "filing_identity": {"test": True}, "source_detail": {"account_id": metric}},
        "observation_sha256": "",
    }
    payload = copy.deepcopy(item); payload.pop("observation_sha256")
    item["observation_sha256"] = _sha(payload)
    return item


def _all(*, klass: str = "NORMALIZED_FACT") -> list[dict]:
    return [_obs(metric, (index + 1) * 100, klass=klass) for index, metric in enumerate(CORE_COMPONENTS)]


def test_m19_mappings_do_not_mutate_m13_m14_registries() -> None:
    assert "short_term_borrowings" not in sec_live.METRIC_SPECS
    assert not set(CORE_COMPONENTS).intersection(dart_live.DART_METRIC_SPECS)
    assert SEC_COMPONENT_SUPPORT == {"short_term_borrowings"}
    assert SEC_COMPONENT_SPECS["short_term_borrowings"].concepts == (("us-gaap", "ShortTermBorrowings"),)
    assert set(DART_COMPONENT_SPECS) == set(CORE_COMPONENTS)
    assert DART_COMPONENT_SPECS["short_term_borrowings"].account_ids == ("ifrs-full_ShorttermBorrowings",)
    assert DART_COMPONENT_SPECS["current_portion_bonds"].account_ids == ("ifrs-full_CurrentPortionOfBondsIssued",)


def test_dart_debt_candidate_normalizes_in_isolated_pipeline() -> None:
    candidate = {
        "schema_version": "dart-debt-component-candidate-v0.1", "status": "DEBT_COMPONENT_EVIDENCE_CANDIDATE_UNREVIEWED", "canonical": False, "class": "FACT_CANDIDATE",
        "metric": "long_term_borrowings", "value": 300, "unit": "KRW",
        "request_identity": {"corp_code": "00126380", "bsns_year": "2026", "reprt_code": "11012", "fs_div": "CFS"},
        "statement_section": "BS", "account_selection": {"kind": "account_id", "fallback_index": 0, "fallback_used": False, "equal_precedence_count": 1},
        "row": {"rcept_no": "20260814000001", "account_id": "ifrs-full_LongtermBorrowings", "account_nm": "장기차입금", "thstrm_amount": "300"},
        "source": {"publisher": "FSS", "source_type": "official", "tier_proposal": "A", "locator": "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json?corp_code=00126380&bsns_year=2026&reprt_code=11012&fs_div=CFS", "snapshot_sha256": "b" * 64, "body_sha256": "c" * 64},
    }
    obs = normalize_debt_component_candidate(candidate)
    assert obs["schema_version"] == "debt-component-observation-v0.1"
    assert obs["class"] == "NORMALIZED_FACT_CANDIDATE"
    assert obs["period"]["kind"] == "INSTANT"
    assert obs["period"]["date_precision"] == "REPORT_STAGE_ONLY"
    assert obs["lineage"]["source_detail"]["account_id"] == "ifrs-full_LongtermBorrowings"
    assert validate_debt_component_observation(obs)["status"] == "PASS_DEBT_COMPONENT_OBSERVATION_VALIDATION"


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
    result = aggregate_interest_bearing_debt(_all()[:-1])
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


def test_equal_duplicate_keeps_candidate_authority_and_conflict_blocks_total() -> None:
    observations = _all()
    observations.append(_obs("short_term_borrowings", 100, klass="NORMALIZED_FACT_CANDIDATE"))
    result = aggregate_interest_bearing_debt(observations)
    assert result["coverage"]["status"] == COMPLETE
    component = next(item for item in result["components"] if item["metric"] == "short_term_borrowings")
    assert component["class"] == "NORMALIZED_FACT"
    assert result["class"] == "DERIVED_FACT_CANDIDATE"
    assert result["semantic_boundary"]["eligible_for_draft_direct_bind"] is False

    conflicting = _all()
    conflicting.append(_obs("short_term_borrowings", 999, klass="NORMALIZED_FACT_CANDIDATE"))
    blocked = aggregate_interest_bearing_debt(conflicting)
    assert blocked["coverage"]["status"] == CONFLICT
    assert blocked["coverage"]["conflict_components"] == ["short_term_borrowings"]
    assert blocked["class"] == "DERIVED_FACT_CANDIDATE"
    assert blocked["known_component_sum"] is None
    assert blocked["interest_bearing_debt_value"] is None
    assert blocked["semantic_boundary"]["eligible_for_draft_direct_bind"] is False


def test_noncomponent_and_identity_mismatches_fail_closed() -> None:
    bad = _obs("short_term_borrowings", 100)
    bad["metric"] = "liabilities"
    payload = copy.deepcopy(bad); payload.pop("observation_sha256")
    bad["observation_sha256"] = _sha(payload)
    with pytest.raises(CaseServiceError, match="explicit debt components|명시적 debt 구성요소"):
        aggregate_interest_bearing_debt([bad])
    base = _all()
    bad_set = copy.deepcopy(base); bad_set[-1] = _obs(CORE_COMPONENTS[-1], 500, scope="OFS")
    with pytest.raises(CaseServiceError, match="mismatch|불일치"):
        aggregate_interest_bearing_debt(bad_set)
    bad_set = copy.deepcopy(base); bad_set[-1] = _obs(CORE_COMPONENTS[-1], 500, unit="USD")
    with pytest.raises(CaseServiceError, match="mismatch|불일치"):
        aggregate_interest_bearing_debt(bad_set)
    bad_set = copy.deepcopy(base); bad_set[-1] = _obs(CORE_COMPONENTS[-1], 500, end="2026-03-31")
    with pytest.raises(CaseServiceError, match="mismatch|불일치"):
        aggregate_interest_bearing_debt(bad_set)


def test_hash_coverage_and_input_authority_tampering_are_detected() -> None:
    result = aggregate_interest_bearing_debt(_all())
    tampered = copy.deepcopy(result); tampered["interest_bearing_debt_value"] = 9999
    with pytest.raises(CaseServiceError):
        validate_interest_bearing_debt_evidence(tampered)
    tampered = copy.deepcopy(result); tampered["semantic_boundary"]["total_liabilities_used"] = True
    with pytest.raises(CaseServiceError, match="semantic boundary|의미경계"):
        validate_interest_bearing_debt_evidence(tampered)
    tampered = copy.deepcopy(result); tampered["class"] = "DERIVED_FACT_CANDIDATE"
    tampered["debt_sha256"] = _sha({k: v for k, v in tampered.items() if k != "debt_sha256"})
    with pytest.raises(CaseServiceError, match="authority propagation|권위전파"):
        validate_interest_bearing_debt_evidence(tampered)
