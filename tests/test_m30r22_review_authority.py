from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from valuation_hub import cli_entry_m30r2
from valuation_hub.ai_debt_adjudication import (
    REQUIRED_CRITERIA,
    build_ai_sec_aggregate_debt_adjudication,
    build_ai_sec_aggregate_debt_evidence,
    build_legacy_compatible_ai_review_assertion,
)
from valuation_hub.case_service import CaseServiceError
from valuation_hub.sec_aggregate_debt import (
    SEMANTIC_DECISION,
    build_sec_aggregate_debt_review_assertion,
    extract_sec_aggregate_debt_candidate,
    normalize_sec_aggregate_debt_candidate,
)
from valuation_hub.sec_aggregate_debt_authority import (
    AI_REASON,
    HUMAN_REASON,
    build_sec_aggregate_debt_binding_context,
    finalize_reviewed_sec_aggregate_debt,
    validate_reviewed_sec_aggregate_debt,
    validate_sec_aggregate_debt_binding_context,
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
        user_agent="M30R22 test-contact@example.com",
        transport=transport,
        fetched_at="2026-09-15T17:42:53+00:00",
    )
    candidate = extract_sec_aggregate_debt_candidate(snapshot, form="10-Q", period_end="2026-06-30")
    return normalize_sec_aggregate_debt_candidate(candidate)


def _ai_assertion(observation: dict) -> dict:
    evidence = build_ai_sec_aggregate_debt_evidence(
        observation,
        primary_filing_locator=PRIMARY,
        supporting_filing_locators=[SUPPORTING],
        evidence_basis="Issuer debt note reconciles 1.742B long-term plus 0.041B short-term to 1.783B total debt; operating leases are separate and finance leases are absent.",
        contradiction_search_summary="No material contrary issuer evidence found.",
        material_contradictions=[],
        criteria={key: True for key in REQUIRED_CRITERIA},
    )
    adjudication = build_ai_sec_aggregate_debt_adjudication(
        observation, evidence, adjudicated_at="2026-09-17T13:53:10+09:00"
    )
    return build_legacy_compatible_ai_review_assertion(observation, adjudication, evidence)


def _write(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def test_ai_profile_and_context_are_truthfully_labeled() -> None:
    observation = _observation()
    assertion = _ai_assertion(observation)
    profile = finalize_reviewed_sec_aggregate_debt(observation, assertion)
    assert profile["binding_eligibility"] == {"eligible": True, "reason": AI_REASON}
    checked = validate_reviewed_sec_aggregate_debt(profile)
    assert checked["review_authority"] == "AI"

    context = build_sec_aggregate_debt_binding_context(profile, as_of="2026-09-14")
    checked_context = validate_sec_aggregate_debt_binding_context(context)
    assert checked_context["review_authority"] == "AI"
    assert checked_context["eligible"] is True
    assert context["source_debt_profile_sha256"] == profile["profile_sha256"]


def test_mislabeled_ai_profile_fails_closed() -> None:
    observation = _observation()
    profile = finalize_reviewed_sec_aggregate_debt(observation, _ai_assertion(observation))
    bad = copy.deepcopy(profile)
    bad["binding_eligibility"] = {"eligible": True, "reason": HUMAN_REASON}
    with pytest.raises(CaseServiceError, match="reviewer-type"):
        validate_reviewed_sec_aggregate_debt(bad)


def test_explicit_human_path_preserves_historical_reason() -> None:
    observation = _observation()
    assertion = build_sec_aggregate_debt_review_assertion(
        observation,
        reviewer="Explicit Human Reviewer",
        reviewed_at="2026-09-17T13:00:00+09:00",
        review_basis="Human reviewed issuer financing and lease-liability boundary.",
        source_basis_locator=PRIMARY,
        semantic_scope_decision=SEMANTIC_DECISION,
    )
    profile = finalize_reviewed_sec_aggregate_debt(observation, assertion)
    assert profile["binding_eligibility"] == {"eligible": True, "reason": HUMAN_REASON}
    checked = validate_reviewed_sec_aggregate_debt(profile)
    assert checked["review_authority"] == "HUMAN"


def test_top_level_cli_uses_authority_aware_finalize_and_context(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    observation = _observation()
    assertion = _ai_assertion(observation)
    observation_path = _write(tmp_path / "observation.json", observation)
    assertion_path = _write(tmp_path / "assertion.json", assertion)

    assert cli_entry_m30r2.main([
        "--json", "sec-aggregate-debt-finalize", str(observation_path), str(assertion_path)
    ]) == 0
    profile = json.loads(capsys.readouterr().out)
    assert profile["binding_eligibility"]["reason"] == AI_REASON
    profile_path = _write(tmp_path / "profile.json", profile)

    assert cli_entry_m30r2.main([
        "--json", "sec-aggregate-debt-profile-validate", str(profile_path)
    ]) == 0
    checked = json.loads(capsys.readouterr().out)
    assert checked["review_authority"] == "AI"

    assert cli_entry_m30r2.main([
        "--json", "sec-aggregate-debt-context-build", str(profile_path), "--as-of", "2026-09-14"
    ]) == 0
    context = json.loads(capsys.readouterr().out)
    context_path = _write(tmp_path / "context.json", context)

    assert cli_entry_m30r2.main([
        "--json", "sec-aggregate-debt-context-validate", str(context_path)
    ]) == 0
    checked_context = json.loads(capsys.readouterr().out)
    assert checked_context["review_authority"] == "AI"
