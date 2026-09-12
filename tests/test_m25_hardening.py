"""M25 terminal-growth validator hardening tests."""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_binding import build_binding_proposal
from valuation_hub.terminal_growth_assumption import (
    LONG_RUN_INFLATION,
    LONG_RUN_REAL_GROWTH,
    build_terminal_growth_anchor_input,
    build_terminal_growth_candidate,
    build_terminal_growth_review_assertion,
    finalize_reviewed_terminal_growth,
    validate_terminal_growth_candidate,
)
from valuation_hub.terminal_growth_draft_binding import build_binding_proposal_with_terminal_growth, validate_binding_proposal_v5
from valuation_hub.wacc_assumption import (
    DEBT_MARKET_VALUE,
    EQUITY_MARKET_VALUE,
    EQUITY_RISK_PREMIUM,
    LEVERED_BETA,
    PRE_TAX_COST_OF_DEBT,
    RISK_FREE_RATE,
    TAX_RATE,
    build_wacc_candidate,
    build_wacc_review_assertion,
    build_wacc_source_input,
    finalize_reviewed_wacc,
)
from valuation_hub.wacc_draft_binding import build_binding_proposal_with_wacc


def _rehash(value: dict, field: str) -> str:
    copied = copy.deepcopy(value)
    copied.pop(field, None)
    return hashlib.sha256(json.dumps(copied, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _cash() -> dict:
    value = {
        "schema_version": "financial-observation-v0.1",
        "status": "FINANCIAL_OBSERVATION_NORMALIZED",
        "canonical": False,
        "class": "NORMALIZED_FACT",
        "metric": "cash",
        "value": 100.0,
        "unit": "KRW",
        "entity": {"id": "DART_CORP:00126380", "source_system": "TEST", "financial_scope": "CFS"},
        "period": {"kind": "INSTANT", "start": None, "end": "2026-06-30", "duration_days": None, "fiscal_year": 2026, "fiscal_period": "H1", "fiscal_quarter": 2, "report_stage": "H1", "date_precision": "EXACT"},
        "lineage": {"normalization_rule": "TEST", "source_candidate_sha256": "a" * 64},
        "observation_sha256": "",
    }
    value["observation_sha256"] = _rehash(value, "observation_sha256")
    return value


def _wsrc(metric: str, value: float, unit: str, claim: str = "FACT") -> dict:
    return build_wacc_source_input(
        metric=metric,
        value=value,
        unit=unit,
        observed_on="2026-09-01",
        claim_class=claim,
        source_publisher="test",
        source_type="TEST",
        source_tier="A",
        source_locator=f"test://{metric}",
        source_sha256=hashlib.sha256(metric.encode()).hexdigest(),
    )


def _low_wacc_package() -> dict:
    inputs = [
        _wsrc(RISK_FREE_RATE, 0.01, "decimal"),
        _wsrc(EQUITY_RISK_PREMIUM, 0.015, "decimal", "ASSUMPTION"),
        _wsrc(LEVERED_BETA, 1.0, "ratio", "ASSUMPTION"),
        _wsrc(PRE_TAX_COST_OF_DEBT, 0.02, "decimal", "ASSUMPTION"),
        _wsrc(EQUITY_MARKET_VALUE, 1000.0, "KRW"),
        _wsrc(DEBT_MARKET_VALUE, 200.0, "KRW"),
        _wsrc(TAX_RATE, 0.25, "decimal", "ASSUMPTION"),
    ]
    candidate = build_wacc_candidate(inputs, entity_id="DART_CORP:00126380", financial_scope="CFS", capital_currency="KRW", as_of="2026-09-12", scenario_names=["BASE"])
    assertion = build_wacc_review_assertion(candidate, reviewer="human", approved_at="2026-09-12T21:00:00+09:00", review_basis="low WACC hardening fixture")
    return finalize_reviewed_wacc(candidate, assertion)


def _anchors() -> list[dict]:
    def build(metric: str, value: float) -> dict:
        return build_terminal_growth_anchor_input(
            metric=metric,
            value=value,
            observed_on="2026-06-01",
            claim_class="ASSUMPTION",
            source_publisher="macro source",
            source_type="FORECAST",
            source_tier="A",
            source_locator=f"test://{metric}",
            source_sha256=hashlib.sha256(("m25-" + metric).encode()).hexdigest(),
        )
    return [build(LONG_RUN_INFLATION, 0.02), build(LONG_RUN_REAL_GROWTH, 0.015)]


def _normal_wacc_package() -> dict:
    inputs = [
        _wsrc(RISK_FREE_RATE, 0.0436, "decimal"),
        _wsrc(EQUITY_RISK_PREMIUM, 0.0418, "decimal", "ASSUMPTION"),
        _wsrc(LEVERED_BETA, 1.2, "ratio", "ASSUMPTION"),
        _wsrc(PRE_TAX_COST_OF_DEBT, 0.05, "decimal", "ASSUMPTION"),
        _wsrc(EQUITY_MARKET_VALUE, 1000.0, "KRW"),
        _wsrc(DEBT_MARKET_VALUE, 200.0, "KRW"),
        _wsrc(TAX_RATE, 0.25, "decimal", "ASSUMPTION"),
    ]
    candidate = build_wacc_candidate(inputs, entity_id="DART_CORP:00126380", financial_scope="CFS", capital_currency="KRW", as_of="2026-09-12", scenario_names=["BASE"])
    assertion = build_wacc_review_assertion(candidate, reviewer="human", approved_at="2026-09-12T21:00:00+09:00", review_basis="normal WACC hardening fixture")
    return finalize_reviewed_wacc(candidate, assertion)


def _terminal_package(wacc: dict) -> dict:
    candidate = build_terminal_growth_candidate(
        _anchors(),
        wacc,
        scenario_assumptions=[{"scenario_name": "BASE", "terminal_growth": 0.025, "rationale": "Reviewed base perpetual growth."}],
    )
    assertion = build_terminal_growth_review_assertion(candidate, reviewer="human", approved_at="2026-09-12T21:10:00+09:00", review_basis="terminal growth hardening fixture")
    return finalize_reviewed_terminal_growth(candidate, assertion)


def test_valid_low_wacc_package_blocks_growth_at_or_above_wacc() -> None:
    wacc = _low_wacc_package()
    assert wacc["wacc"] < 0.025
    with pytest.raises(CaseServiceError, match="WACC|wacc"):
        build_terminal_growth_candidate(
            _anchors(),
            wacc,
            scenario_assumptions=[{"scenario_name": "BASE", "terminal_growth": 0.025, "rationale": "Below macro anchor but above WACC."}],
        )


def test_candidate_calculation_resigning_cannot_bypass_nominal_anchor_recomputation() -> None:
    wacc = _normal_wacc_package()
    candidate = build_terminal_growth_candidate(
        _anchors(),
        wacc,
        scenario_assumptions=[{"scenario_name": "BASE", "terminal_growth": 0.025, "rationale": "Reviewed."}],
    )
    tampered = copy.deepcopy(candidate)
    tampered["calculation"]["nominal_growth_anchor"] += 0.01
    tampered["candidate_sha256"] = _rehash(tampered, "candidate_sha256")
    with pytest.raises(CaseServiceError, match="calculation|계산"):
        validate_terminal_growth_candidate(tampered)


def test_v05_policy_resigning_cannot_weaken_direct_bind_requirements() -> None:
    wacc = _normal_wacc_package()
    base = build_binding_proposal([_cash()], as_of="2026-09-12")
    v04 = build_binding_proposal_with_wacc(base, wacc)
    proposal = build_binding_proposal_with_terminal_growth(v04, _terminal_package(wacc))
    tampered = copy.deepcopy(proposal)
    tampered["policy"]["direct_bind_requires"] = ["HUMAN_REVIEW_ASSERTION"]
    tampered["proposal_sha256"] = _rehash(tampered, "proposal_sha256")
    with pytest.raises(CaseServiceError, match="policy|정책"):
        validate_binding_proposal_v5(tampered)


def test_terminal_growth_projection_resigning_cannot_break_nested_package_lineage() -> None:
    wacc = _normal_wacc_package()
    base = build_binding_proposal([_cash()], as_of="2026-09-12")
    v04 = build_binding_proposal_with_wacc(base, wacc)
    proposal = build_binding_proposal_with_terminal_growth(v04, _terminal_package(wacc))
    tampered = copy.deepcopy(proposal)
    tampered["baseline_context"]["terminal_growth_assumption"]["value"]["BASE"] = 0.02
    tampered["proposal_sha256"] = _rehash(tampered, "proposal_sha256")
    with pytest.raises(CaseServiceError, match="baseline|투영"):
        validate_binding_proposal_v5(tampered)
