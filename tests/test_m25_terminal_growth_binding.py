"""M25 governed terminal-growth assumption + Draft binding tests."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from valuation_hub.binding_apply import apply_binding_approval, build_binding_approval, validate_bound_draft_result
from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_binding import build_binding_proposal
from valuation_hub.terminal_growth_assumption import (
    LONG_RUN_INFLATION,
    LONG_RUN_REAL_GROWTH,
    build_terminal_growth_anchor_input,
    build_terminal_growth_candidate,
    build_terminal_growth_review_assertion,
    finalize_reviewed_terminal_growth,
    validate_reviewed_terminal_growth,
    validate_terminal_growth_candidate,
)
from valuation_hub.terminal_growth_draft_binding import (
    build_binding_proposal_with_terminal_growth,
    validate_binding_proposal_v5,
)
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

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "draft_equity_fcff.json"


def _hash(value: dict, field: str) -> str:
    copy_value = copy.deepcopy(value)
    copy_value.pop(field, None)
    return hashlib.sha256(
        json.dumps(copy_value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _cash() -> dict:
    value = {
        "schema_version": "financial-observation-v0.1",
        "status": "FINANCIAL_OBSERVATION_NORMALIZED",
        "canonical": False,
        "class": "NORMALIZED_FACT",
        "metric": "cash",
        "value": 777.0,
        "unit": "KRW",
        "entity": {"id": "DART_CORP:00126380", "source_system": "TEST", "financial_scope": "CFS"},
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
        "lineage": {"normalization_rule": "TEST", "source_candidate_sha256": "a" * 64},
        "observation_sha256": "",
    }
    value["observation_sha256"] = _hash(value, "observation_sha256")
    return value


def _wacc_source(metric: str, value: float, unit: str, observed_on: str, *, tier: str = "B", claim: str = "FACT") -> dict:
    return build_wacc_source_input(
        metric=metric,
        value=value,
        unit=unit,
        observed_on=observed_on,
        claim_class=claim,
        source_publisher=f"{metric} publisher",
        source_type="TEST_SOURCE",
        source_tier=tier,
        source_locator=f"test://{metric}",
        source_sha256=hashlib.sha256(metric.encode()).hexdigest(),
    )


def _wacc_inputs() -> list[dict]:
    return [
        _wacc_source(RISK_FREE_RATE, 0.0436, "decimal", "2026-09-01", tier="A"),
        _wacc_source(EQUITY_RISK_PREMIUM, 0.0418, "decimal", "2026-09-01", claim="ASSUMPTION"),
        _wacc_source(LEVERED_BETA, 1.2, "ratio", "2026-08-01", claim="ASSUMPTION"),
        _wacc_source(PRE_TAX_COST_OF_DEBT, 0.05, "decimal", "2026-08-01", claim="ASSUMPTION"),
        _wacc_source(EQUITY_MARKET_VALUE, 1000.0, "KRW", "2026-09-01"),
        _wacc_source(DEBT_MARKET_VALUE, 200.0, "KRW", "2026-06-30", tier="A"),
        _wacc_source(TAX_RATE, 0.25, "decimal", "2026-06-30", tier="A", claim="ASSUMPTION"),
    ]


def _wacc_package(*, scenarios: list[str] | None = None) -> dict:
    candidate = build_wacc_candidate(
        _wacc_inputs(),
        entity_id="DART_CORP:00126380",
        financial_scope="CFS",
        capital_currency="KRW",
        as_of="2026-09-12",
        scenario_names=scenarios or ["BASE"],
    )
    assertion = build_wacc_review_assertion(
        candidate,
        reviewer="human-wacc-reviewer",
        approved_at="2026-09-12T21:15:00+09:00",
        review_basis="Reviewed WACC sources and methodology.",
    )
    return finalize_reviewed_wacc(candidate, assertion)


def _anchor(metric: str, value: float, *, observed_on: str = "2026-06-01", tier: str = "B") -> dict:
    return build_terminal_growth_anchor_input(
        metric=metric,
        value=value,
        observed_on=observed_on,
        claim_class="ASSUMPTION",
        source_publisher=f"{metric} publisher",
        source_type="LONG_RUN_FORECAST",
        source_tier=tier,
        source_locator=f"test://{metric}",
        source_sha256=hashlib.sha256(("anchor-" + metric).encode()).hexdigest(),
    )


def _anchors(*, stale: bool = False, tier_d: bool = False) -> list[dict]:
    observed = "2025-01-01" if stale else "2026-06-01"
    return [
        _anchor(LONG_RUN_INFLATION, 0.02, observed_on=observed, tier="A"),
        _anchor(LONG_RUN_REAL_GROWTH, 0.015, observed_on=observed, tier="D" if tier_d else "B"),
    ]


def _scenario_assumptions(names: list[str] | None = None) -> list[dict]:
    names = names or ["BASE"]
    values = {"BASE": 0.025, "BULL": 0.03, "BEAR": 0.01}
    return [
        {"scenario_name": name, "terminal_growth": values.get(name, 0.02), "rationale": f"Reviewed perpetual growth for {name}."}
        for name in names
    ]


def _terminal_package(*, scenarios: list[str] | None = None, wacc_package: dict | None = None) -> dict:
    names = scenarios or ["BASE"]
    wacc = wacc_package or _wacc_package(scenarios=names)
    candidate = build_terminal_growth_candidate(_anchors(), wacc, scenario_assumptions=_scenario_assumptions(names))
    assertion = build_terminal_growth_review_assertion(
        candidate,
        reviewer="human-terminal-reviewer",
        approved_at="2026-09-12T21:25:00+09:00",
        review_basis="Reviewed macro anchors, WACC dependency, scenario values, and perpetual-growth constraints.",
    )
    return finalize_reviewed_terminal_growth(candidate, assertion)


def _v04(*, scenarios: list[str] | None = None, wacc_package: dict | None = None) -> tuple[dict, dict]:
    base = build_binding_proposal([_cash()], as_of="2026-09-12")
    wacc = wacc_package or _wacc_package(scenarios=scenarios or ["BASE"])
    return build_binding_proposal_with_wacc(base, wacc), wacc


def _draft(*, scenarios: list[str] | None = None) -> dict:
    draft = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    draft["currency"] = "KRW"
    draft["name"] = "M25 terminal-growth integration"
    names = scenarios or ["BASE"]
    base_row = copy.deepcopy(draft["equity"]["scenarios"]["BASE"])
    draft["equity"]["scenarios"] = {name: copy.deepcopy(base_row) for name in names}
    return draft


def _decision(proposal: dict, field: str) -> dict:
    return next(item for item in proposal["draft_input_matrix"] if item["field"] == field)


def test_candidate_recomputes_nominal_anchor_and_keeps_terminal_growth_as_assumption() -> None:
    wacc = _wacc_package()
    candidate = build_terminal_growth_candidate(_anchors(), wacc, scenario_assumptions=_scenario_assumptions())
    assert candidate["calculation"]["nominal_growth_anchor"] == pytest.approx((1.02 * 1.015) - 1)
    assert candidate["calculation"]["reviewed_wacc"] == pytest.approx(wacc["wacc"])
    assert candidate["class"] == "ASSUMPTION_CANDIDATE"
    assert validate_terminal_growth_candidate(candidate)["eligible_for_human_review"] is True


def test_stale_or_tier_d_anchor_cannot_be_human_reviewed() -> None:
    wacc = _wacc_package()
    stale = build_terminal_growth_candidate(_anchors(stale=True), wacc, scenario_assumptions=_scenario_assumptions())
    assert stale["review_readiness"]["eligible_for_human_review"] is False
    with pytest.raises(CaseServiceError, match="eligible|부적격"):
        build_terminal_growth_review_assertion(stale, reviewer="human", approved_at="2026-09-12T21:25:00+09:00", review_basis="review")
    tier_d = build_terminal_growth_candidate(_anchors(tier_d=True), wacc, scenario_assumptions=_scenario_assumptions())
    assert tier_d["review_readiness"]["all_source_tiers_reviewable"] is False
    with pytest.raises(CaseServiceError, match="eligible|부적격"):
        build_terminal_growth_review_assertion(tier_d, reviewer="human", approved_at="2026-09-12T21:25:00+09:00", review_basis="review")


def test_terminal_growth_above_macro_anchor_or_wacc_fails_closed() -> None:
    wacc = _wacc_package()
    above_anchor = [{"scenario_name": "BASE", "terminal_growth": 0.04, "rationale": "Too high."}]
    with pytest.raises(CaseServiceError, match="macro anchor|거시 anchor"):
        build_terminal_growth_candidate(_anchors(), wacc, scenario_assumptions=above_anchor)
    low_wacc = copy.deepcopy(wacc)
    low_wacc["wacc"] = 0.02
    low_wacc["candidate"]["calculation"]["wacc"] = 0.02
    # Nested WACC validation must reject hand-edited WACC before M25 can use it.
    with pytest.raises(CaseServiceError):
        build_terminal_growth_candidate(_anchors(), low_wacc, scenario_assumptions=_scenario_assumptions())


def test_negative_terminal_growth_above_minus_one_is_allowed_when_reviewed() -> None:
    wacc = _wacc_package()
    candidate = build_terminal_growth_candidate(
        _anchors(),
        wacc,
        scenario_assumptions=[{"scenario_name": "BASE", "terminal_growth": -0.02, "rationale": "Long-run contraction case."}],
    )
    assert candidate["scenario_assumptions"][0]["terminal_growth"] == -0.02


def test_reviewed_terminal_growth_is_assumption_and_nested_tamper_fails() -> None:
    package = _terminal_package()
    assert package["class"] == "ASSUMPTION"
    assert validate_reviewed_terminal_growth(package)["eligible"] is True
    tampered = copy.deepcopy(package)
    tampered["candidate"]["scenario_assumptions"][0]["terminal_growth"] += 0.001
    tampered["package_sha256"] = _hash(tampered, "package_sha256")
    with pytest.raises(CaseServiceError):
        validate_reviewed_terminal_growth(tampered)


def test_v05_requires_v04_and_replaces_only_terminal_growth() -> None:
    v04, wacc = _v04()
    package = _terminal_package(wacc_package=wacc)
    proposal = build_binding_proposal_with_terminal_growth(v04, package)
    checked = validate_binding_proposal_v5(proposal)
    assert proposal["schema_version"] == "draft-binding-proposal-v0.5"
    assert _decision(proposal, "scenario.wacc") == _decision(v04, "scenario.wacc")
    assert _decision(proposal, "scenario.terminal_growth")["state"] == "DIRECT_BIND"
    base_by = {item["field"]: item for item in v04["draft_input_matrix"]}
    by_field = {item["field"]: item for item in proposal["draft_input_matrix"]}
    for field in base_by:
        if field != "scenario.terminal_growth":
            assert by_field[field] == base_by[field]
    assert checked["direct_bind_count"] == v04["completeness"]["direct_bind_count"] + 1
    raw_base = build_binding_proposal([_cash()], as_of="2026-09-12")
    with pytest.raises(CaseServiceError, match="v0.4"):
        build_binding_proposal_with_terminal_growth(raw_base, package)


def test_v05_rejects_terminal_package_from_different_wacc_lineage() -> None:
    v04, wacc = _v04()
    other_inputs = _wacc_inputs()
    other_inputs[1] = _wacc_source(EQUITY_RISK_PREMIUM, 0.042, "decimal", "2026-09-01", claim="ASSUMPTION")
    other_candidate = build_wacc_candidate(
        other_inputs,
        entity_id="DART_CORP:00126380",
        financial_scope="CFS",
        capital_currency="KRW",
        as_of="2026-09-12",
        scenario_names=["BASE"],
    )
    other_assertion = build_wacc_review_assertion(other_candidate, reviewer="human", approved_at="2026-09-12T21:15:00+09:00", review_basis="review")
    other_wacc = finalize_reviewed_wacc(other_candidate, other_assertion)
    package = _terminal_package(wacc_package=other_wacc)
    assert package["source_wacc_package_sha256"] != wacc["package_sha256"]
    with pytest.raises(CaseServiceError, match="lineage"):
        build_binding_proposal_with_terminal_growth(v04, package)


def test_terminal_growth_apply_with_wacc_together_is_scenario_specific_and_immutable() -> None:
    names = ["BASE", "BULL"]
    v04, wacc = _v04(scenarios=names)
    package = _terminal_package(scenarios=names, wacc_package=wacc)
    proposal = build_binding_proposal_with_terminal_growth(v04, package)
    draft = _draft(scenarios=names)
    before = copy.deepcopy(draft)
    approval = build_binding_approval(
        proposal,
        draft,
        reviewer="human-approver",
        target_entity_id="DART_CORP:00126380",
        target_financial_scope="CFS",
        approved_fields=["scenario.wacc", "scenario.terminal_growth"],
        approved_at="2026-09-12T21:30:00+09:00",
    )
    result = apply_binding_approval(proposal, draft, approval)
    assert draft == before
    for name in names:
        assert result["draft_after"]["equity"]["scenarios"][name]["wacc"] == pytest.approx(wacc["wacc"])
        assert result["draft_after"]["equity"]["scenarios"][name]["terminal_growth"] == pytest.approx(package["terminal_growth"][name])
    terminal_diff = next(item for item in result["applied_diffs"] if item["field"] == "scenario.terminal_growth")
    assert terminal_diff["before"] == {"BASE": 0.025, "BULL": 0.025}
    assert terminal_diff["after"] == {"BASE": pytest.approx(0.025), "BULL": pytest.approx(0.03)}
    assert terminal_diff["source_terminal_growth_package_sha256"] == package["package_sha256"]
    assert terminal_diff["source_wacc_package_sha256"] == wacc["package_sha256"]
    assert terminal_diff["review_assertion_sha256"] == package["review_assertion"]["assertion_sha256"]
    assert terminal_diff["scenario_names"] == ["BASE", "BULL"]
    assert validate_bound_draft_result(result)["applied_field_count"] == 2


def test_terminal_growth_only_requires_reviewed_wacc_already_present_in_draft() -> None:
    v04, wacc = _v04()
    package = _terminal_package(wacc_package=wacc)
    proposal = build_binding_proposal_with_terminal_growth(v04, package)
    draft = _draft()
    with pytest.raises(CaseServiceError, match="already|함께 승인"):
        build_binding_approval(
            proposal,
            draft,
            reviewer="human",
            target_entity_id="DART_CORP:00126380",
            target_financial_scope="CFS",
            approved_fields=["scenario.terminal_growth"],
            approved_at="2026-09-12T21:30:00+09:00",
        )
    draft["equity"]["scenarios"]["BASE"]["wacc"] = wacc["wacc"]
    approval = build_binding_approval(
        proposal,
        draft,
        reviewer="human",
        target_entity_id="DART_CORP:00126380",
        target_financial_scope="CFS",
        approved_fields=["scenario.terminal_growth"],
        approved_at="2026-09-12T21:30:00+09:00",
    )
    result = apply_binding_approval(proposal, draft, approval)
    assert result["draft_after"]["equity"]["scenarios"]["BASE"]["terminal_growth"] == pytest.approx(0.025)


def test_terminal_growth_target_set_must_equal_draft_scenarios() -> None:
    v04, wacc = _v04(scenarios=["BASE"])
    package = _terminal_package(scenarios=["BASE"], wacc_package=wacc)
    proposal = build_binding_proposal_with_terminal_growth(v04, package)
    draft = _draft(scenarios=["BASE", "BULL"])
    with pytest.raises(CaseServiceError, match="scenario target set|시나리오"):
        build_binding_approval(
            proposal,
            draft,
            reviewer="human",
            target_entity_id="DART_CORP:00126380",
            target_financial_scope="CFS",
            approved_fields=["scenario.terminal_growth"],
            approved_at="2026-09-12T21:30:00+09:00",
        )
