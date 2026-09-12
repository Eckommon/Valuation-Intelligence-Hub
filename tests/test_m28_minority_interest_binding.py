"""M28 governed minority-interest FACT + Draft binding tests."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from valuation_hub import dart_live, sec_live
from valuation_hub.binding_apply_m28 import apply_binding_approval, build_binding_approval, validate_bound_draft_result
from valuation_hub.case_service import CaseServiceError
from valuation_hub.market_price_draft_binding import build_binding_proposal_with_market_price
from valuation_hub.minority_interest import (
    build_minority_interest_review_assertion,
    extract_dart_minority_interest_candidate,
    extract_sec_minority_interest_candidate,
    finalize_reviewed_minority_interest,
    normalize_minority_interest_candidate,
    validate_minority_interest_candidate,
    validate_reviewed_minority_interest,
)
from valuation_hub.minority_interest_draft_binding import build_binding_proposal_with_minority_interest, validate_binding_proposal_v8


def _rehash(value: dict, field: str) -> str:
    copied = copy.deepcopy(value)
    copied.pop(field, None)
    return hashlib.sha256(json.dumps(copied, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _m27_fixtures():
    path = Path(__file__).with_name("test_m27_market_price_binding.py")
    spec = importlib.util.spec_from_file_location("_m27_minority_fixture", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def _v07() -> dict:
    f = _m27_fixtures()
    return build_binding_proposal_with_market_price(f._v06(["BASE"]), f._package())


def _draft() -> dict:
    return _m27_fixtures()._draft(["BASE"])


def _dart_snapshot(amount: str = "50,000,000", *, include: bool = True, fs_div: str = "CFS") -> dict:
    rows = []
    if include:
        rows.append({
            "rcept_no": "20260801000001", "reprt_code": "11012", "bsns_year": "2026", "corp_code": "00126380", "stock_code": "000000",
            "fs_div": fs_div, "fs_nm": "연결재무제표" if fs_div == "CFS" else "재무제표", "sj_div": "BS", "sj_nm": "재무상태표",
            "account_id": "ifrs-full_NoncontrollingInterests", "account_nm": "비지배지분", "account_detail": "-", "thstrm_nm": "제 2026 반기말",
            "thstrm_amount": amount, "frmtrm_nm": "전기말", "frmtrm_amount": "40,000,000", "ord": "20", "currency": "KRW",
        })
    body = json.dumps({"status": "000", "message": "정상", "list": rows}, ensure_ascii=False).encode()

    def transport(locator: str, *, api_key: str):
        return dart_live.DartTransportResponse(200, "application/json; charset=utf-8", body, locator)

    return dart_live.capture_dart_snapshot(
        "00126380", "2026", "11012", fs_div,
        api_key="x" * 24, transport=transport, fetched_at="2026-08-01T12:00:00+09:00",
    )


def _sec_snapshot(*, include: bool = True) -> dict:
    facts = {}
    if include:
        facts = {"us-gaap": {"NonredeemableNoncontrollingInterest": {"units": {"USD": [{
            "end": "2026-06-30", "val": 125000000, "accn": "0001234567-26-000001", "form": "10-Q", "filed": "2026-08-01", "fy": 2026, "fp": "Q2"
        }]}}}}
    body = json.dumps({"cik": 1234567, "facts": facts}).encode()

    def transport(locator: str, *, user_agent: str):
        return sec_live.TransportResponse(200, "application/json", body, locator)

    return sec_live.capture_companyfacts_snapshot(
        "1234567", user_agent="Research research@example.com", transport=transport, fetched_at="2026-08-01T12:00:00+00:00"
    )


def _minority_package(amount: str = "50,000,000") -> dict:
    candidate = extract_dart_minority_interest_candidate(_dart_snapshot(amount))
    observation = normalize_minority_interest_candidate(candidate)
    assertion = build_minority_interest_review_assertion(
        observation,
        as_of="2026-09-12",
        reviewer="minority reviewer",
        approved_at="2026-09-12T21:00:00+09:00",
        review_basis="Reviewed exact CFS noncontrolling-interest account and H1 period end.",
        asserted_period_end="2026-06-30",
        max_age_days=550,
    )
    return finalize_reviewed_minority_interest(observation, assertion)


def _decision(proposal: dict, field: str) -> dict:
    return next(item for item in proposal["draft_input_matrix"] if item["field"] == field)


def test_sec_exact_minority_interest_extracts_nonredeemable_nci_and_reviews_without_date_assertion() -> None:
    candidate = extract_sec_minority_interest_candidate(_sec_snapshot())
    assert candidate["source_identity"]["concept"] == "NonredeemableNoncontrollingInterest"
    assert candidate["period"]["date_precision"] == "EXACT"
    assert candidate["semantic_boundary"] == {
        "missing_is_zero": False,
        "redeemable_noncontrolling_interest_included": False,
        "derived_from_equity_difference": False,
    }
    observation = normalize_minority_interest_candidate(candidate)
    assertion = build_minority_interest_review_assertion(
        observation, as_of="2026-09-12", reviewer="human", approved_at="2026-09-12T12:00:00+00:00",
        review_basis="Reviewed exact SEC nonredeemable noncontrolling-interest fact.", max_age_days=550,
    )
    package = finalize_reviewed_minority_interest(observation, assertion)
    assert package["class"] == "NORMALIZED_FACT"
    assert package["date_resolution"] == "SOURCE_EXACT"
    assert validate_reviewed_minority_interest(package)["eligible"] is True


def test_opendart_report_stage_requires_human_exact_date_assertion() -> None:
    candidate = extract_dart_minority_interest_candidate(_dart_snapshot())
    assert candidate["source_identity"]["account_id"] == "ifrs-full_NoncontrollingInterests"
    assert candidate["period"]["date_precision"] == "REPORT_STAGE_ONLY"
    observation = normalize_minority_interest_candidate(candidate)
    with pytest.raises(CaseServiceError, match="requires human date assertion|인간 날짜승인"):
        build_minority_interest_review_assertion(
            observation, as_of="2026-09-12", reviewer="human", approved_at="2026-09-12T21:00:00+09:00", review_basis="Missing exact date."
        )
    package = _minority_package()
    assert package["resolved_period_end"] == "2026-06-30"
    assert package["date_resolution"] == "HUMAN_DATE_ASSERTION"
    assert package["value"] == 50000000


def test_missing_is_not_zero_but_explicit_zero_is_preserved() -> None:
    with pytest.raises(CaseServiceError, match="account unavailable|account 없음"):
        extract_dart_minority_interest_candidate(_dart_snapshot(include=False))
    with pytest.raises(CaseServiceError, match="concept unavailable|concept 없음"):
        extract_sec_minority_interest_candidate(_sec_snapshot(include=False))
    package = _minority_package("0")
    assert package["value"] == 0
    assert package["binding_eligibility"]["eligible"] is True


def test_resigned_candidate_cannot_change_exact_sec_or_dart_mapping() -> None:
    sec_candidate = extract_sec_minority_interest_candidate(_sec_snapshot())
    forged_sec = copy.deepcopy(sec_candidate)
    forged_sec["source_identity"]["concept"] = "RedeemableNoncontrollingInterestEquityCarryingAmount"
    forged_sec["candidate_sha256"] = _rehash(forged_sec, "candidate_sha256")
    with pytest.raises(CaseServiceError, match="exact concept identity|exact concept 식별"):
        validate_minority_interest_candidate(forged_sec)

    dart_candidate = extract_dart_minority_interest_candidate(_dart_snapshot())
    forged_dart = copy.deepcopy(dart_candidate)
    forged_dart["source_identity"]["account_id"] = "ifrs-full_Equity"
    forged_dart["candidate_sha256"] = _rehash(forged_dart, "candidate_sha256")
    with pytest.raises(CaseServiceError, match="exact account identity|exact account 식별"):
        validate_minority_interest_candidate(forged_dart)


def test_v08_replaces_only_minority_interest_and_requires_v07() -> None:
    base = _v07(); package = _minority_package()
    proposal = build_binding_proposal_with_minority_interest(base, package)
    checked = validate_binding_proposal_v8(proposal)
    assert proposal["schema_version"] == "draft-binding-proposal-v0.8"
    assert _decision(proposal, "equity.minority_interest")["state"] == "DIRECT_BIND"
    for item in base["draft_input_matrix"]:
        if item["field"] != "equity.minority_interest": assert _decision(proposal, item["field"]) == item
    assert checked["direct_bind_count"] == base["completeness"]["direct_bind_count"] + 1
    with pytest.raises(CaseServiceError, match="v0.7"):
        build_binding_proposal_with_minority_interest(base["base_proposal"], package)


def test_minority_interest_apply_changes_only_equity_field_and_preserves_lineage() -> None:
    package = _minority_package(); proposal = build_binding_proposal_with_minority_interest(_v07(), package); draft = _draft(); before = copy.deepcopy(draft)
    approval = build_binding_approval(
        proposal, draft, reviewer="human", target_entity_id="DART_CORP:00126380", target_financial_scope="CFS",
        approved_fields=["equity.minority_interest"], approved_at="2026-09-12T21:30:00+09:00",
    )
    result = apply_binding_approval(proposal, draft, approval)
    assert draft == before
    assert result["draft_after"]["equity"]["minority_interest"] == 50000000
    for key in ("cash", "debt", "diluted_shares", "scenarios"):
        assert result["draft_after"]["equity"][key] == before["equity"][key]
    assert result["draft_after"]["market_price"] == before["market_price"]
    assert validate_bound_draft_result(result)["applied_field_count"] == 1
    diff = result["applied_diffs"][0]
    assert diff["source_minority_interest_package_sha256"] == package["package_sha256"]
    assert diff["source_observation_sha256"] == package["observation"]["observation_sha256"]
    assert diff["source_snapshot_sha256"] == package["source"]["snapshot_sha256"]
    assert diff["review_assertion_sha256"] == package["review_assertion"]["assertion_sha256"]
