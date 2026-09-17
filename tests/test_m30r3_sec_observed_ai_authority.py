from __future__ import annotations

import json
from pathlib import Path

import pytest

from valuation_hub import cli_entry_m30r3
from valuation_hub.ai_sec_observed_authority import (
    ADJUDICATOR_ID,
    FIELD_CASH,
    FIELD_NCI,
    FIELD_SHARES,
    REQUIRED_CRITERIA,
    build_ai_reviewed_cash_observation,
    build_ai_reviewed_current_share_observation,
    build_ai_reviewed_minority_interest_package,
    build_ai_sec_observed_adjudication,
    build_ai_sec_observed_evidence,
    validate_ai_reviewed_cash_observation,
    validate_ai_reviewed_current_share_observation,
    validate_ai_reviewed_minority_interest_package,
)
from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_binding import build_binding_proposal
from valuation_hub.financial_normalization import normalize_sec_candidate
from valuation_hub.minority_interest import extract_sec_minority_interest_candidate, normalize_minority_interest_candidate
from valuation_hub.sec_live import TransportResponse, capture_companyfacts_snapshot, companyfacts_locator, extract_sec_evidence_candidate
from valuation_hub.valuation_shares import (
    build_valuation_share_base_context,
    extract_sec_current_common_shares_candidate,
    normalize_current_common_shares_candidate,
)

CIK = "0001046257"
ACCN = "0001628280-26-054722"
PRIMARY = "https://www.sec.gov/Archives/edgar/data/1046257/000162828026054722/ingr-20260630.htm"


def _snapshot() -> dict:
    payload = {
        "cik": 1046257,
        "entityName": "Ingredion Incorporated",
        "facts": {
            "us-gaap": {
                "CashAndCashEquivalentsAtCarryingValue": {"units": {"USD": [{
                    "val": 948_000_000, "end": "2026-06-30", "fy": 2026, "fp": "Q2",
                    "frame": "CY2026Q2I", "form": "10-Q", "filed": "2026-08-07", "accn": ACCN,
                }]}},
                "NonredeemableNoncontrollingInterest": {"units": {"USD": [{
                    "val": 0, "end": "2026-06-30", "form": "10-Q", "filed": "2026-08-07", "accn": ACCN,
                }]}},
            },
            "dei": {
                "EntityCommonStockSharesOutstanding": {"units": {"shares": [{
                    "val": 63_063_979, "end": "2026-08-05", "form": "10-Q", "filed": "2026-08-07", "accn": ACCN,
                }]}}
            },
        },
    }
    body = json.dumps(payload, separators=(",", ":")).encode()

    def transport(locator: str, *, user_agent: str):
        assert locator == companyfacts_locator(CIK)
        return TransportResponse(200, "application/json", body, locator)

    return capture_companyfacts_snapshot(
        CIK,
        user_agent="M30R3 test-contact@example.com",
        transport=transport,
        fetched_at="2026-09-15T17:42:53+00:00",
    )


def _pair(field: str) -> tuple[dict, dict]:
    snapshot = _snapshot()
    if field == FIELD_CASH:
        candidate = extract_sec_evidence_candidate(snapshot, "cash", form="10-Q", period_end="2026-06-30")
        return candidate, normalize_sec_candidate(candidate)
    if field == FIELD_SHARES:
        candidate = extract_sec_current_common_shares_candidate(snapshot, form="10-Q", period_end="2026-08-05")
        return candidate, normalize_current_common_shares_candidate(candidate)
    candidate = extract_sec_minority_interest_candidate(snapshot, form="10-Q", period_end="2026-06-30")
    return candidate, normalize_minority_interest_candidate(candidate)


def _evidence(field: str, candidate: dict, observation: dict, *, contradictions: list[str] | None = None) -> dict:
    return build_ai_sec_observed_evidence(
        field,
        candidate,
        observation,
        primary_filing_locator=PRIMARY,
        evidence_basis=f"Exact issuer SEC filing evidence supports {field} source semantics and lineage.",
        contradiction_search_summary="Issuer filing/source identity checked for material contrary evidence; none identified.",
        material_contradictions=[] if contradictions is None else contradictions,
        criteria={key: True for key in REQUIRED_CRITERIA[field]},
    )


def _adjudication(field: str, candidate: dict, observation: dict, evidence: dict) -> dict:
    return build_ai_sec_observed_adjudication(
        candidate, observation, evidence, adjudicated_at="2026-09-18T01:30:00+09:00"
    )


def test_cash_ai_authority_becomes_m16_direct_bind_eligible() -> None:
    candidate, observation = _pair(FIELD_CASH)
    evidence = _evidence(FIELD_CASH, candidate, observation)
    adjudication = _adjudication(FIELD_CASH, candidate, observation, evidence)
    reviewed = build_ai_reviewed_cash_observation(candidate, observation, adjudication, evidence)

    checked = validate_ai_reviewed_cash_observation(reviewed, candidate, observation, adjudication, evidence)
    assert checked["review_authority"] == "AI"
    assert reviewed["class"] == "NORMALIZED_FACT"
    assert reviewed["value"] == 948_000_000
    assert reviewed["authority_review"]["reviewer"] == ADJUDICATOR_ID

    proposal = build_binding_proposal([reviewed], as_of="2026-09-14")
    cash = next(item for item in proposal["draft_input_matrix"] if item["field"] == "equity.cash")
    assert cash["state"] == "DIRECT_BIND"


def test_current_share_ai_authority_unlocks_base_context_without_diluted_equivalence() -> None:
    candidate, observation = _pair(FIELD_SHARES)
    evidence = _evidence(FIELD_SHARES, candidate, observation)
    adjudication = _adjudication(FIELD_SHARES, candidate, observation, evidence)
    reviewed = build_ai_reviewed_current_share_observation(candidate, observation, adjudication, evidence)

    checked = validate_ai_reviewed_current_share_observation(reviewed, candidate, observation, adjudication, evidence)
    assert checked["review_authority"] == "AI"
    assert reviewed["class"] == "NORMALIZED_FACT"
    assert reviewed["value"] == 63_063_979
    assert reviewed["semantic_boundary"] == {"current_common_shares_only": True, "fully_diluted_shares": False}

    context = build_valuation_share_base_context(reviewed, as_of="2026-09-14")
    assert context["binding_eligibility"]["eligible_as_current_common_share_base"] is True
    assert context["semantic_boundary"]["fully_diluted_shares"] is False


def test_explicit_zero_nci_ai_authority_preserves_missing_not_zero_boundary() -> None:
    candidate, observation = _pair(FIELD_NCI)
    assert candidate["value"] == 0
    assert candidate["semantic_boundary"]["missing_is_zero"] is False

    evidence = _evidence(FIELD_NCI, candidate, observation)
    adjudication = _adjudication(FIELD_NCI, candidate, observation, evidence)
    package = build_ai_reviewed_minority_interest_package(
        candidate, observation, adjudication, evidence, as_of="2026-09-14"
    )
    checked = validate_ai_reviewed_minority_interest_package(package, candidate, observation, adjudication, evidence)

    assert checked["review_authority"] == "AI"
    assert checked["eligible"] is True
    assert package["value"] == 0
    assert package["class"] == "NORMALIZED_FACT"
    assert package["semantic_boundary"]["missing_is_zero"] is False
    assert package["review_assertion"]["reviewer"] == ADJUDICATOR_ID


def test_material_contradiction_fails_closed() -> None:
    candidate, observation = _pair(FIELD_CASH)
    with pytest.raises(CaseServiceError, match="contradiction"):
        _evidence(FIELD_CASH, candidate, observation, contradictions=["Conflicting issuer cash disclosure identified."])


def test_field_mismatch_and_missing_criterion_fail_closed() -> None:
    candidate, observation = _pair(FIELD_SHARES)
    criteria = {key: True for key in REQUIRED_CRITERIA[FIELD_SHARES]}
    criteria["q3_current_common_not_fully_diluted_boundary_preserved"] = False
    with pytest.raises(CaseServiceError, match="criteria"):
        build_ai_sec_observed_evidence(
            FIELD_SHARES, candidate, observation,
            primary_filing_locator=PRIMARY,
            evidence_basis="Evidence basis.",
            contradiction_search_summary="No contradiction.",
            material_contradictions=[],
            criteria=criteria,
        )

    cash_candidate, cash_observation = _pair(FIELD_CASH)
    with pytest.raises(CaseServiceError):
        _evidence(FIELD_SHARES, cash_candidate, cash_observation)


def test_cli_new_surface_and_prior_delegation(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    candidate, observation = _pair(FIELD_CASH)
    candidate_path = tmp_path / "candidate.json"
    observation_path = tmp_path / "observation.json"
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    observation_path.write_text(json.dumps(observation), encoding="utf-8")

    argv = [
        "--json", "sec-observed-ai-evidence-build", FIELD_CASH,
        str(candidate_path), str(observation_path),
        "--primary-filing-locator", PRIMARY,
        "--evidence-basis", "Exact issuer SEC filing cash evidence.",
        "--contradiction-search-summary", "No material contrary evidence identified.",
    ]
    for criterion in REQUIRED_CRITERIA[FIELD_CASH]:
        argv.extend(["--criterion", criterion])
    assert cli_entry_m30r3.main(argv) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["field"] == FIELD_CASH
    assert all(out["criteria"].values())

    seen: list[list[str]] = []
    monkeypatch.setattr(cli_entry_m30r3.prior_cli, "main", lambda values: seen.append(list(values)) or 27)
    old = ["sec-aggregate-debt-profile-validate", "profile.json"]
    assert cli_entry_m30r3.main(old) == 27
    assert seen == [old]
