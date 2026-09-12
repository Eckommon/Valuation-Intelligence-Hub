"""M23 complete M22 share bridge → M16/M20/M17 binding integration tests."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from valuation_hub.binding_apply import apply_binding_approval, build_binding_approval, validate_bound_draft_result
from valuation_hub.case_service import CaseServiceError
from valuation_hub.debt_binding import build_debt_binding_context
from valuation_hub.debt_components import CORE_COMPONENTS, aggregate_interest_bearing_debt
from valuation_hub.debt_draft_binding import build_binding_proposal_with_debt
from valuation_hub.draft_binding import build_binding_proposal
from valuation_hub.share_draft_binding import build_binding_proposal_with_diluted_shares, validate_binding_proposal_v3
from valuation_hub.valuation_shares import (
    ADJUSTMENT_CATEGORIES,
    build_diluted_share_bridge,
    build_dilution_adjustment,
    build_dilution_coverage_assertion,
    build_valuation_share_base_context,
    validate_dilution_adjustment,
)

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "draft_equity_fcff.json"
ENTITY = "SEC_CIK:0001234567"
SCOPE = "AS_REPORTED"
AS_OF = "2026-09-12"


def _hash(value: dict, field: str) -> str:
    payload = copy.deepcopy(value)
    payload.pop(field, None)
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _cash() -> dict:
    result = {
        "schema_version": "financial-observation-v0.1",
        "status": "FINANCIAL_OBSERVATION_NORMALIZED",
        "canonical": False,
        "class": "NORMALIZED_FACT",
        "metric": "cash",
        "value": 777,
        "unit": "USD",
        "entity": {"id": ENTITY, "source_system": "TEST", "financial_scope": SCOPE},
        "period": {"kind": "INSTANT", "start": None, "end": "2026-08-01", "duration_days": None, "fiscal_year": 2026, "fiscal_period": "Q2", "fiscal_quarter": 2, "report_stage": "Q2", "date_precision": "EXACT"},
        "lineage": {"normalization_rule": "TEST", "source_candidate_sha256": "a" * 64},
        "observation_sha256": "",
    }
    result["observation_sha256"] = _hash(result, "observation_sha256")
    return result


def _debt_obs(metric: str, value: int) -> dict:
    result = {
        "schema_version": "debt-component-observation-v0.1",
        "status": "DEBT_COMPONENT_NORMALIZED",
        "canonical": False,
        "class": "NORMALIZED_FACT",
        "metric": metric,
        "value": value,
        "unit": "USD",
        "entity": {"id": ENTITY, "source_system": "TEST", "financial_scope": SCOPE},
        "period": {"kind": "INSTANT", "start": None, "end": "2026-08-01", "duration_days": None, "fiscal_year": 2026, "fiscal_period": "Q2", "fiscal_quarter": 2, "report_stage": "Q2", "date_precision": "EXACT"},
        "lineage": {"normalization_rule": "TEST", "source_candidate_sha256": "a" * 64, "source_class": "FACT", "source_snapshot_sha256": "b" * 64, "source_body_sha256": "c" * 64, "filing_identity": {"id": "test"}, "source_detail": {"account_id": metric}},
        "observation_sha256": "",
    }
    result["observation_sha256"] = _hash(result, "observation_sha256")
    return result


def _debt_context() -> dict:
    debt = aggregate_interest_bearing_debt([_debt_obs(metric, (index + 1) * 100) for index, metric in enumerate(CORE_COMPONENTS)])
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
        "period": {"kind": "INSTANT", "start": None, "end": "2026-08-01", "date_precision": "EXACT"},
        "lineage": {"normalization_rule": "SEC_DEI_CURRENT_COMMON_SHARES_INSTANT_V01", "source_candidate_sha256": "d" * 64, "source_class": "FACT", "source_snapshot_sha256": "e" * 64, "source_body_sha256": "f" * 64, "filing_identity": {"accession": "0001234567-26-000040", "form": "10-Q", "filed": "2026-08-05"}, "source_detail": {"taxonomy": "dei", "concept": "EntityCommonStockSharesOutstanding"}},
        "semantic_boundary": {"current_common_shares_only": True, "fully_diluted_shares": False},
        "observation_sha256": "",
    }
    result["observation_sha256"] = _hash(result, "observation_sha256")
    return result


def _reviewed_adjustment() -> dict:
    adjustment = build_dilution_adjustment(
        adjustment_id="OPT-1",
        category="options_treasury_stock_method",
        shares=25,
        source_sha256="1" * 64,
        source_description="Reviewed treasury-stock-method option dilution evidence",
    )
    adjustment["class"] = "NORMALIZED_FACT"
    adjustment["adjustment_sha256"] = _hash(adjustment, "adjustment_sha256")
    validate_dilution_adjustment(adjustment)
    return adjustment


def _eligible_bridge(*, entity: str = ENTITY, as_of: str = AS_OF) -> dict:
    observation = _share_observation()
    observation["entity"]["id"] = entity
    observation["observation_sha256"] = _hash(observation, "observation_sha256")
    base = build_valuation_share_base_context(observation, as_of=as_of, max_age_days=180)
    adjustment = _reviewed_adjustment()
    assertion = build_dilution_coverage_assertion(
        base,
        [adjustment],
        reviewer="human-share-reviewer",
        approved_at="2026-09-12T20:00:00+09:00",
        coverage_basis="All supported dilution categories explicitly reviewed against issuer evidence.",
        reviewed_categories=list(ADJUSTMENT_CATEGORIES),
    )
    return build_diluted_share_bridge(base, [adjustment], coverage_assertion=assertion)


def _partial_bridge() -> dict:
    base = build_valuation_share_base_context(_share_observation(), as_of=AS_OF, max_age_days=180)
    candidate = build_dilution_adjustment(
        adjustment_id="RSU-1",
        category="rsu_restricted_stock",
        shares=50,
        source_sha256="2" * 64,
        source_description="Unreviewed RSU candidate evidence",
    )
    return build_diluted_share_bridge(base, [candidate])


def _draft() -> dict:
    draft = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    draft["currency"] = "USD"
    draft["name"] = "M23 share binding integration"
    return draft


def _decision(proposal: dict, field: str) -> dict:
    return next(item for item in proposal["draft_input_matrix"] if item["field"] == field)


def test_v03_wraps_v01_and_replaces_only_diluted_shares() -> None:
    base = build_binding_proposal([_cash()], as_of=AS_OF)
    before = copy.deepcopy(base)
    proposal = build_binding_proposal_with_diluted_shares(base, _eligible_bridge())
    assert base == before
    assert proposal["schema_version"] == "draft-binding-proposal-v0.3"
    assert proposal["base_proposal"] == base
    assert _decision(proposal, "equity.diluted_shares")["state"] == "DIRECT_BIND"
    assert _decision(proposal, "equity.cash") == _decision(base, "equity.cash")
    for item in base["draft_input_matrix"]:
        if item["field"] != "equity.diluted_shares":
            assert _decision(proposal, item["field"]) == item
    assert proposal["baseline_context"]["fully_diluted_shares"]["value"] == 1025
    assert validate_binding_proposal_v3(proposal)["direct_bind_count"] == 2


def test_v03_wraps_v02_and_preserves_debt_lineage() -> None:
    debt_base = build_binding_proposal_with_debt([_cash()], _debt_context(), as_of=AS_OF, max_age_days=550)
    before = copy.deepcopy(debt_base)
    proposal = build_binding_proposal_with_diluted_shares(debt_base, _eligible_bridge())
    assert debt_base == before
    assert proposal["base_proposal"]["schema_version"] == "draft-binding-proposal-v0.2"
    assert _decision(proposal, "equity.cash")["state"] == "DIRECT_BIND"
    assert _decision(proposal, "equity.debt") == _decision(debt_base, "equity.debt")
    assert _decision(proposal, "equity.diluted_shares")["state"] == "DIRECT_BIND"
    assert proposal["debt_binding_context"] if "debt_binding_context" in proposal else True
    assert validate_binding_proposal_v3(proposal)["direct_bind_count"] == 3


def test_ineligible_or_mismatched_share_bridges_fail_before_v03_creation() -> None:
    base = build_binding_proposal([_cash()], as_of=AS_OF)
    with pytest.raises(CaseServiceError, match="complete reviewed fresh"):
        build_binding_proposal_with_diluted_shares(base, _partial_bridge())
    with pytest.raises(CaseServiceError, match="entity/scope"):
        build_binding_proposal_with_diluted_shares(base, _eligible_bridge(entity="SEC_CIK:0009999999"))
    with pytest.raises(CaseServiceError, match="as_of"):
        build_binding_proposal_with_diluted_shares(base, _eligible_bridge(as_of="2026-09-11"))


def test_nested_share_bridge_tamper_fails_even_if_outer_proposal_is_resealed() -> None:
    proposal = build_binding_proposal_with_diluted_shares(build_binding_proposal([_cash()], as_of=AS_OF), _eligible_bridge())
    tampered = copy.deepcopy(proposal)
    tampered["share_bridge"]["coverage_assertion"]["coverage_basis"] = "forged"
    tampered["proposal_sha256"] = _hash(tampered, "proposal_sha256")
    with pytest.raises(CaseServiceError):
        validate_binding_proposal_v3(tampered)


def test_human_approval_can_apply_cash_debt_and_diluted_shares_together() -> None:
    debt_base = build_binding_proposal_with_debt([_cash()], _debt_context(), as_of=AS_OF, max_age_days=550)
    bridge = _eligible_bridge()
    proposal = build_binding_proposal_with_diluted_shares(debt_base, bridge)
    draft = _draft()
    before = copy.deepcopy(draft)
    approval = build_binding_approval(
        proposal,
        draft,
        reviewer="human-final-reviewer",
        target_entity_id=ENTITY,
        target_financial_scope=SCOPE,
        approved_fields=["equity.cash", "equity.debt", "equity.diluted_shares"],
        approved_at="2026-09-12T20:10:00+09:00",
    )
    result = apply_binding_approval(proposal, draft, approval)
    assert draft == before
    after = result["draft_after"]["equity"]
    assert after["cash"] == 777
    assert after["debt"] == 1500
    assert after["diluted_shares"] == 1025
    by_field = {item["field"]: item for item in result["applied_diffs"]}
    share_diff = by_field["equity.diluted_shares"]
    assert share_diff["source_context_sha256"] == bridge["bridge_sha256"]
    assert share_diff["source_bridge_sha256"] == bridge["bridge_sha256"]
    assert share_diff["base_context_sha256"] == bridge["base_context"]["context_sha256"]
    assert share_diff["coverage_assertion_sha256"] == bridge["coverage_assertion"]["assertion_sha256"]
    assert "source_debt_sha256" in by_field["equity.debt"]
    assert "source_observation_sha256" in by_field["equity.cash"]
    assert validate_bound_draft_result(result)["applied_field_count"] == 3


def test_v03_does_not_allow_approval_of_unresolved_non_direct_field() -> None:
    proposal = build_binding_proposal_with_diluted_shares(build_binding_proposal([_cash()], as_of=AS_OF), _eligible_bridge())
    with pytest.raises(CaseServiceError, match="DIRECT_BIND"):
        build_binding_approval(
            proposal,
            _draft(),
            reviewer="human",
            target_entity_id=ENTITY,
            target_financial_scope=SCOPE,
            approved_fields=["equity.debt"],
            approved_at="2026-09-12T20:10:00+09:00",
        )
