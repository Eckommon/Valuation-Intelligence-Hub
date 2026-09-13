"""M29 complete governed equity handoff regressions."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from valuation_hub import promotion as legacy_promotion
from valuation_hub.binding_apply_m28 import apply_binding_approval, build_binding_approval
from valuation_hub.case_service import CaseServiceError
from valuation_hub.debt_binding import build_debt_binding_context
from valuation_hub.debt_components import CORE_COMPONENTS, aggregate_interest_bearing_debt
from valuation_hub.debt_draft_binding import build_binding_proposal_with_debt
from valuation_hub.draft_binding import MATERIAL_FIELDS
from valuation_hub.draft_service import validate_draft
from valuation_hub.forecast_draft_binding import build_binding_proposal_with_forecast
from valuation_hub.market_price_draft_binding import build_binding_proposal_with_market_price
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
from valuation_hub.share_draft_binding import build_binding_proposal_with_diluted_shares
from valuation_hub.terminal_growth_draft_binding import build_binding_proposal_with_terminal_growth
from valuation_hub.valuation_shares import (
    ADJUSTMENT_CATEGORIES,
    build_diluted_share_bridge,
    build_dilution_adjustment,
    build_dilution_coverage_assertion,
    build_valuation_share_base_context,
    validate_dilution_adjustment,
)
from valuation_hub.wacc_draft_binding import build_binding_proposal_with_wacc

ENTITY = "DART_CORP:00126380"
SCOPE = "CFS"
AS_OF = "2026-09-12"


def _rehash(value: dict, field: str) -> str:
    copied = copy.deepcopy(value)
    copied.pop(field, None)
    return hashlib.sha256(
        json.dumps(copied, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _fixture(name: str):
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location("_m29_" + name.replace(".py", ""), path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _m25_fixtures():
    return _fixture("test_m25_terminal_growth_binding.py")


def _m26_fixtures():
    return _fixture("test_m26_integrated_forecast_binding.py")


def _m27_fixtures():
    return _fixture("test_m27_market_price_binding.py")


def _m28_fixtures():
    return _fixture("test_m28_minority_interest_binding.py")


def _debt_observation(metric: str, value: int) -> dict:
    result = {
        "schema_version": "debt-component-observation-v0.1",
        "status": "DEBT_COMPONENT_NORMALIZED",
        "canonical": False,
        "class": "NORMALIZED_FACT",
        "metric": metric,
        "value": value,
        "unit": "KRW",
        "entity": {"id": ENTITY, "source_system": "TEST", "financial_scope": SCOPE},
        "period": {
            "kind": "INSTANT",
            "start": None,
            "end": "2026-06-30",
            "duration_days": None,
            "fiscal_year": 2026,
            "fiscal_period": "H1",
            "fiscal_quarter": 2,
            "report_stage": "H1",
            "date_precision": "EXACT",
        },
        "lineage": {
            "normalization_rule": "TEST",
            "source_candidate_sha256": "a" * 64,
            "source_class": "FACT",
            "source_snapshot_sha256": "b" * 64,
            "source_body_sha256": "c" * 64,
            "filing_identity": {"id": "m29-test"},
            "source_detail": {"account_id": metric},
        },
        "observation_sha256": "",
    }
    result["observation_sha256"] = _rehash(result, "observation_sha256")
    return result


def _debt_context() -> dict:
    debt = aggregate_interest_bearing_debt(
        [_debt_observation(metric, (index + 1) * 100) for index, metric in enumerate(CORE_COMPONENTS)]
    )
    return build_debt_binding_context(debt, as_of=AS_OF, max_age_days=550)


def _share_observation() -> dict:
    result = {
        "schema_version": "current-common-shares-observation-v0.1",
        "status": "CURRENT_COMMON_SHARES_OBSERVATION_NORMALIZED",
        "canonical": False,
        "class": "NORMALIZED_FACT",
        "metric": "current_common_shares",
        "value": 1000,
        "unit": "shares",
        "entity": {"id": ENTITY, "source_system": "SEC", "financial_scope": SCOPE},
        "period": {"kind": "INSTANT", "start": None, "end": "2026-06-30", "date_precision": "EXACT"},
        "lineage": {
            "normalization_rule": "SEC_DEI_CURRENT_COMMON_SHARES_INSTANT_V01",
            "source_candidate_sha256": "d" * 64,
            "source_class": "FACT",
            "source_snapshot_sha256": "e" * 64,
            "source_body_sha256": "f" * 64,
            "filing_identity": {"accession": "m29-test", "form": "10-Q", "filed": "2026-08-05"},
            "source_detail": {"taxonomy": "dei", "concept": "EntityCommonStockSharesOutstanding"},
        },
        "semantic_boundary": {"current_common_shares_only": True, "fully_diluted_shares": False},
        "observation_sha256": "",
    }
    result["observation_sha256"] = _rehash(result, "observation_sha256")
    return result


def _eligible_share_bridge() -> dict:
    base = build_valuation_share_base_context(_share_observation(), as_of=AS_OF, max_age_days=180)
    adjustment = build_dilution_adjustment(
        adjustment_id="M29-OPT-1",
        category="options_treasury_stock_method",
        shares=25,
        source_sha256="1" * 64,
        source_description="Reviewed M29 treasury-stock-method dilution evidence",
    )
    adjustment["class"] = "NORMALIZED_FACT"
    adjustment["adjustment_sha256"] = _rehash(adjustment, "adjustment_sha256")
    validate_dilution_adjustment(adjustment)
    assertion = build_dilution_coverage_assertion(
        base,
        [adjustment],
        reviewer="M29 share reviewer",
        approved_at="2026-09-13T18:00:00+09:00",
        coverage_basis="All supported dilution categories explicitly reviewed for the M29 complete-chain fixture.",
        reviewed_categories=list(ADJUSTMENT_CATEGORIES),
    )
    return build_diluted_share_bridge(base, [adjustment], coverage_assertion=assertion)


def _proposal_and_draft():
    """Construct the complete M20→M23→M24→M25→M26→M27→M28 chain."""
    m25 = _m25_fixtures()
    m26 = _m26_fixtures()
    m27 = _m27_fixtures()
    m28 = _m28_fixtures()

    v02 = build_binding_proposal_with_debt([m26._cash()], _debt_context(), as_of=AS_OF, max_age_days=550)
    v03 = build_binding_proposal_with_diluted_shares(v02, _eligible_share_bridge())
    wacc = m26._wacc_package(["BASE"])
    v04 = build_binding_proposal_with_wacc(v03, wacc)
    terminal = m25._terminal_package(scenarios=["BASE"], wacc_package=wacc)
    v05 = build_binding_proposal_with_terminal_growth(v04, terminal)
    v06 = build_binding_proposal_with_forecast(v05, m26._forecast_package(["BASE"]))
    v07 = build_binding_proposal_with_market_price(v06, m27._package())
    v08 = build_binding_proposal_with_minority_interest(v07, m28._minority_package())
    assert v08["completeness"]["direct_bind_count"] == len(MATERIAL_FIELDS)
    assert v08["completeness"]["unresolved_count"] == 0
    return v08, m26._draft(["BASE"])


def _complete_result():
    proposal, draft = _proposal_and_draft()
    approval = build_binding_approval(
        proposal,
        draft,
        reviewer="M29 complete reviewer",
        target_entity_id=ENTITY,
        target_financial_scope=SCOPE,
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
        target_entity_id=ENTITY,
        target_financial_scope=SCOPE,
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
    return [
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
        for index, field in enumerate(OBSERVED_FIELD_CLASSES, start=1)
    ]


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
    assert all(
        row["rationale"] and row["lineage"]["proposal_decision"]["source_class"] == "ASSUMPTION"
        for row in assumption_rows
    )


def test_complete_candidate_reuses_human_review_scope_lock_and_becomes_promotion_ready() -> None:
    result, candidate = _approved_candidate()
    readiness = promotion_check(candidate)
    assert readiness["promotion_ready"] is True
    assert readiness["grounding"] == "COMPLETE_GOVERNED_BOUND_RESULT"
    assert readiness["source_bound_result_sha256"] == result["result_sha256"]


def test_partial_bound_result_is_rejected_before_catalog_projection() -> None:
    result = _partial_result()
    with pytest.raises(CaseServiceError, match="all 13|13개"):
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
    forged["review"] = {
        "decision": "APPROVE", "reviewer": "x", "reviewed_at": "2026-09-13T19:00:00+09:00",
        "rationale": "forged", "scope_sha256": review_scope_sha256(forged),
    }
    with pytest.raises(CaseServiceError, match="cannot alter|변경할 수 없음"):
        validate_candidate_v2(forged)

    forged = copy.deepcopy(candidate)
    claim = next(item for item in forged["evidence"] if item["binding_field"] == "equity.cash")
    claim["lineage"]["proposal_sha256"] = "0" * 64
    forged["review"] = {
        "decision": "APPROVE", "reviewer": "x", "reviewed_at": "2026-09-13T19:00:00+09:00",
        "rationale": "forged", "scope_sha256": review_scope_sha256(forged),
    }
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
