"""M29 complete governed equity handoff regressions."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

from valuation_hub import promotion as legacy_promotion
from valuation_hub.binding_apply_m28 import apply_binding_approval, build_binding_approval
from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_binding import MATERIAL_FIELDS
from valuation_hub.draft_service import validate_draft
from valuation_hub.minority_interest_draft_binding import build_binding_proposal_with_minority_interest
from valuation_hub.promotion_m29 import (
    CANDIDATE_SCHEMA_VERSION_V2,
    OBSERVED_FIELD_CLASSES,
    assess_candidate,
    build_complete_equity_candidate,
    build_evidence_catalog_claim,
    promotion_check,
    review_scope_sha256,
    validate_candidate_v2,
)


def _m28_fixtures():
    path = Path(__file__).with_name("test_m28_minority_interest_binding.py")
    spec = importlib.util.spec_from_file_location("_m29_m28_fixture", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _proposal_and_draft():
    f = _m28_fixtures()
    proposal = build_binding_proposal_with_minority_interest(f._v07(), f._minority_package())
    return proposal, f._draft()


def _complete_result():
    proposal, draft = _proposal_and_draft()
    approval = build_binding_approval(
        proposal,
        draft,
        reviewer="M29 complete reviewer",
        target_entity_id="DART_CORP:00126380",
        target_financial_scope="CFS",
        approved_fields=list(MATERIAL_FIELDS),
        approved_at="2026-09-13T18:30:00+09:00",
    )
    return apply_binding_approval(proposal, draft, approval)


def _partial_result():
    proposal, draft = _proposal_and_draft()
    approval = build_binding_approval(
        proposal,
        draft,
        reviewer="M29 partial reviewer",
        target_entity_id="DART_CORP:00126380",
        target_financial_scope="CFS",
        approved_fields=["equity.minority_interest"],
        approved_at="2026-09-13T18:31:00+09:00",
    )
    return apply_binding_approval(proposal, draft, approval)


def _catalog(result):
    metrics = {
        "market_price": "market_price",
        "equity.cash": "cash",
        "equity.minority_interest": "minority_interest",
        "equity.debt": "interest_bearing_debt",
        "equity.diluted_shares": "fully_diluted_shares",
    }
    claims = []
    for index, field in enumerate(OBSERVED_FIELD_CLASSES, start=1):
        claims.append(
            build_evidence_catalog_claim(
                result,
                field=field,
                claim_id=f"M29-OBS-{index:02d}",
                metric=metrics[field],
                publisher="M29 test evidence publisher",
                locator=f"repo://m29/{field}",
                tier="A",
                source_type="TEST_FIXTURE",
                source_date="2026-09-13",
            )
        )
    return claims


def _approved_candidate():
    result = _complete_result()
    candidate = build_complete_equity_candidate(result, _catalog(result))
    candidate["review"] = {
        "decision": "APPROVE",
        "reviewer": "promotion reviewer",
        "reviewed_at": "2026-09-13T19:00:00+09:00",
        "rationale": "Reviewed complete governed M28 handoff and exact five-claim evidence catalog.",
        "scope_sha256": review_scope_sha256(candidate),
    }
    return result, candidate


def test_complete_v08_result_projects_all_material_numeric_paths_without_unknown() -> None:
    result = _complete_result()
    candidate = build_complete_equity_candidate(result, _catalog(result))
    checked = validate_candidate_v2(candidate)
    assert candidate["schema_version"] == CANDIDATE_SCHEMA_VERSION_V2
    assert candidate["draft"] == result["draft_after"]
    assert candidate["source_bound_result_sha256"] == result["result_sha256"]
    expected_paths = legacy_promotion._material_numeric_paths(validate_draft(result["draft_after"]))
    assert checked["material_input_count"] == len(expected_paths)
    assert {row["path"] for row in candidate["input_governance"]} == set(expected_paths)
    assert all(row["class"] != "UNKNOWN" for row in candidate["input_governance"])
    by_path = {row["path"]: row for row in candidate["input_governance"]}
    assert by_path["market_price"]["class"] == "FACT"
    assert by_path["equity.cash"]["class"] == "NORMALIZED_FACT"
    assert by_path["equity.minority_interest"]["class"] == "NORMALIZED_FACT"
    assert by_path["equity.debt"]["class"] == "DERIVED"
    assert by_path["equity.diluted_shares"]["class"] == "DERIVED"
    assumption_rows = [row for row in candidate["input_governance"] if row["class"] == "ASSUMPTION"]
    assert assumption_rows
    assert all(row["rationale"] and row["lineage"]["proposal_decision"]["source_class"] == "ASSUMPTION" for row in assumption_rows)


def test_complete_candidate_reuses_human_review_scope_lock_and_becomes_promotion_ready() -> None:
    result, candidate = _approved_candidate()
    readiness = promotion_check(candidate)
    assert readiness["promotion_ready"] is True
    assert readiness["grounding"] == "COMPLETE_GOVERNED_BOUND_RESULT"
    assert readiness["source_bound_result_sha256"] == result["result_sha256"]


def test_partial_bound_result_is_rejected_before_catalog_projection() -> None:
    result = _partial_result()
    with pytest.raises(CaseServiceError, match="exactly all 13|정확히 13개"):
        build_evidence_catalog_claim(
            result,
            field="market_price",
            claim_id="M29-PARTIAL",
            metric="market_price",
            publisher="source",
            locator="repo://partial",
            tier="A",
        )


def test_catalog_cannot_relabel_derived_fields_or_use_tier_d() -> None:
    result = _complete_result()
    catalog = _catalog(result)
    debt = next(item for item in catalog if item["binding_field"] == "equity.debt")
    debt["class"] = "FACT"
    with pytest.raises(CaseServiceError, match="class/status mismatch|class·status"):
        build_complete_equity_candidate(result, catalog)

    with pytest.raises(CaseServiceError, match="Tier D|tier"):
        build_evidence_catalog_claim(
            result,
            field="market_price",
            claim_id="M29-TIER-D",
            metric="market_price",
            publisher="untrusted",
            locator="repo://tier-d",
            tier="D",
        )


def test_catalog_value_and_lineage_tampering_fail_closed_even_if_candidate_is_reviewed_again() -> None:
    result = _complete_result()
    candidate = build_complete_equity_candidate(result, _catalog(result))
    forged = copy.deepcopy(candidate)
    claim = next(item for item in forged["evidence"] if item["binding_field"] == "market_price")
    claim["value"] += 1
    forged["review"] = {"decision": "APPROVE", "reviewer": "x", "reviewed_at": "2026-09-13T19:00:00+09:00", "rationale": "forged", "scope_sha256": review_scope_sha256(forged)}
    with pytest.raises(CaseServiceError, match="cannot alter|변경할 수 없음"):
        validate_candidate_v2(forged)

    forged = copy.deepcopy(candidate)
    claim = next(item for item in forged["evidence"] if item["binding_field"] == "equity.cash")
    claim["lineage"]["proposal_sha256"] = "0" * 64
    forged["review"] = {"decision": "APPROVE", "reviewer": "x", "reviewed_at": "2026-09-13T19:00:00+09:00", "rationale": "forged", "scope_sha256": review_scope_sha256(forged)}
    with pytest.raises(CaseServiceError, match="lineage mismatch|lineage 불일치"):
        validate_candidate_v2(forged)


def test_nested_bound_result_tamper_cannot_be_legitimized_by_new_review_scope_hash() -> None:
    _, candidate = _approved_candidate()
    forged = copy.deepcopy(candidate)
    forged["source_bound_result"]["draft_after"]["market_price"] += 10
    forged["review"]["scope_sha256"] = review_scope_sha256(forged)
    with pytest.raises(CaseServiceError):
        validate_candidate_v2(forged)


def test_v01_assessment_delegates_without_semantic_change() -> None:
    _, draft = _proposal_and_draft()
    legacy_candidate = legacy_promotion.build_candidate(draft)
    assert assess_candidate(legacy_candidate) == legacy_promotion.assess_candidate(legacy_candidate)
