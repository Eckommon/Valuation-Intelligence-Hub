from __future__ import annotations

import json

import pytest

from valuation_hub.ai_debt_adjudication import (
    ADJUDICATOR_ID,
    POLICY_ID,
    REQUIRED_CRITERIA,
    build_ai_sec_aggregate_debt_adjudication,
    build_ai_sec_aggregate_debt_evidence,
    build_legacy_compatible_ai_review_assertion,
    validate_ai_sec_aggregate_debt_adjudication,
    validate_ai_sec_aggregate_debt_evidence,
)
from valuation_hub.case_service import CaseServiceError
from valuation_hub.sec_aggregate_debt import (
    extract_sec_aggregate_debt_candidate,
    finalize_reviewed_sec_aggregate_debt,
    normalize_sec_aggregate_debt_candidate,
    validate_reviewed_sec_aggregate_debt,
)
from valuation_hub.sec_live import TransportResponse, capture_companyfacts_snapshot, companyfacts_locator

CIK = "0001046257"
ACCN = "0001628280-26-054722"
PRIMARY = "https://www.sec.gov/Archives/edgar/data/1046257/000162828026054722/ingr-20260630.htm"
SUPPORTING = "https://www.sec.gov/Archives/edgar/data/1046257/000162828026008603/ingr-20251231.htm"


def _observation() -> dict:
    payload = {
        "cik": 1046257,
        "entityName": "Ingredion Incorporated",
        "facts": {"us-gaap": {"DebtLongtermAndShorttermCombinedAmount": {"units": {"USD": [{
            "val": 1_783_000_000,
            "end": "2026-06-30",
            "form": "10-Q",
            "filed": "2026-08-07",
            "accn": ACCN,
        }]}}}},
    }
    body = json.dumps(payload, separators=(",", ":")).encode()

    def transport(locator: str, *, user_agent: str):
        assert locator == companyfacts_locator(CIK)
        return TransportResponse(200, "application/json", body, locator)

    snapshot = capture_companyfacts_snapshot(
        CIK,
        user_agent="M30R2 test-contact@example.com",
        transport=transport,
        fetched_at="2026-09-15T17:42:53+00:00",
    )
    candidate = extract_sec_aggregate_debt_candidate(snapshot, form="10-Q", period_end="2026-06-30")
    return normalize_sec_aggregate_debt_candidate(candidate)


def _criteria() -> dict[str, bool]:
    return {key: True for key in REQUIRED_CRITERIA}


def _evidence(observation: dict, *, contradictions: list[str] | None = None, criteria: dict[str, bool] | None = None) -> dict:
    return build_ai_sec_aggregate_debt_evidence(
        observation,
        primary_filing_locator=PRIMARY,
        supporting_filing_locators=[SUPPORTING],
        evidence_basis=(
            "Issuer 2026 Q2 filing reconciles long-term debt 1.742B plus short-term borrowings 0.041B "
            "to total debt 1.783B; prior audited filing separately classifies operating lease liabilities "
            "and reports no finance leases."
        ),
        contradiction_search_summary="Searched financing and lease disclosures; no material contrary evidence found.",
        material_contradictions=[] if contradictions is None else contradictions,
        criteria=_criteria() if criteria is None else criteria,
    )


def test_ai_adjudication_can_approve_and_reuse_downstream_profile() -> None:
    observation = _observation()
    evidence = _evidence(observation)
    checked = validate_ai_sec_aggregate_debt_evidence(evidence, observation)
    assert checked["status"] == "PASS_AI_SEC_AGGREGATE_DEBT_EVIDENCE_VALIDATION"

    adjudication = build_ai_sec_aggregate_debt_adjudication(
        observation, evidence, adjudicated_at="2026-09-17T13:00:00+09:00"
    )
    assert adjudication["decision"] == "APPROVE"
    assert adjudication["adjudicator"] == {"type": "AI", "id": ADJUDICATOR_ID}
    assert adjudication["policy_id"] == POLICY_ID
    assert validate_ai_sec_aggregate_debt_adjudication(adjudication, observation, evidence)["status"] == (
        "PASS_AI_SEC_AGGREGATE_DEBT_ADJUDICATION_VALIDATION"
    )

    assertion = build_legacy_compatible_ai_review_assertion(observation, adjudication, evidence)
    assert assertion["reviewer"] == ADJUDICATOR_ID
    assert "AI_EVIDENCE_ADJUDICATION" in assertion["review_basis"]

    profile = finalize_reviewed_sec_aggregate_debt(observation, assertion)
    checked_profile = validate_reviewed_sec_aggregate_debt(profile)
    assert checked_profile["eligible"] is True
    assert profile["value"] == 1_783_000_000
    assert profile["semantic_boundary"]["lease_liabilities_included"] is False


def test_ai_evidence_fails_closed_when_any_semantic_criterion_is_false() -> None:
    observation = _observation()
    criteria = _criteria()
    criteria["q4_lease_exclusion_supported"] = False
    with pytest.raises(CaseServiceError, match="criteria"):
        _evidence(observation, criteria=criteria)


def test_ai_evidence_fails_closed_on_material_contradiction() -> None:
    observation = _observation()
    with pytest.raises(CaseServiceError, match="contradiction"):
        _evidence(observation, contradictions=["Lease liability appears inside issuer debt reconciliation."])


def test_ai_adjudication_requires_timezone_aware_timestamp() -> None:
    observation = _observation()
    evidence = _evidence(observation)
    with pytest.raises(CaseServiceError, match="timezone"):
        build_ai_sec_aggregate_debt_adjudication(observation, evidence, adjudicated_at="2026-09-17T13:00:00")
