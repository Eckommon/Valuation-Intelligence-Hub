"""M26 integrated forecast assumption + atomic Draft binding tests."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from valuation_hub.binding_apply import apply_binding_approval, build_binding_approval, validate_bound_draft_result
from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_binding import build_binding_proposal
from valuation_hub.forecast_assumption import (
    FORECAST_COMPONENTS,
    build_forecast_candidate,
    build_forecast_review_assertion,
    finalize_reviewed_forecast,
    validate_forecast_candidate,
    validate_reviewed_forecast,
)
from valuation_hub.forecast_draft_binding import FORECAST_FIELDS, build_binding_proposal_with_forecast, validate_binding_proposal_v6
from valuation_hub.terminal_growth_assumption import (
    LONG_RUN_INFLATION,
    LONG_RUN_REAL_GROWTH,
    build_terminal_growth_anchor_input,
    build_terminal_growth_candidate,
    build_terminal_growth_review_assertion,
    finalize_reviewed_terminal_growth,
)
from valuation_hub.terminal_growth_draft_binding import build_binding_proposal_with_terminal_growth
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
        "value": 777.0,
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
        source_sha256=hashlib.sha256(("m26-" + metric).encode()).hexdigest(),
    )


def _wacc_package(names: list[str]) -> dict:
    inputs = [
        _wsrc(RISK_FREE_RATE, 0.0436, "decimal"),
        _wsrc(EQUITY_RISK_PREMIUM, 0.0418, "decimal", "ASSUMPTION"),
        _wsrc(LEVERED_BETA, 1.2, "ratio", "ASSUMPTION"),
        _wsrc(PRE_TAX_COST_OF_DEBT, 0.05, "decimal", "ASSUMPTION"),
        _wsrc(EQUITY_MARKET_VALUE, 1000.0, "KRW"),
        _wsrc(DEBT_MARKET_VALUE, 200.0, "KRW"),
        _wsrc(TAX_RATE, 0.25, "decimal", "ASSUMPTION"),
    ]
    candidate = build_wacc_candidate(inputs, entity_id="DART_CORP:00126380", financial_scope="CFS", capital_currency="KRW", as_of="2026-09-12", scenario_names=names)
    assertion = build_wacc_review_assertion(candidate, reviewer="wacc reviewer", approved_at="2026-09-12T21:00:00+09:00", review_basis="M26 WACC fixture")
    return finalize_reviewed_wacc(candidate, assertion)


def _tg_anchor(metric: str, value: float) -> dict:
    return build_terminal_growth_anchor_input(
        metric=metric,
        value=value,
        observed_on="2026-06-01",
        claim_class="ASSUMPTION",
        source_publisher="macro",
        source_type="FORECAST",
        source_tier="A",
        source_locator=f"test://{metric}",
        source_sha256=hashlib.sha256(("m26-tg-" + metric).encode()).hexdigest(),
    )


def _v05(names: list[str]) -> dict:
    base = build_binding_proposal([_cash()], as_of="2026-09-12")
    wacc = _wacc_package(names)
    v04 = build_binding_proposal_with_wacc(base, wacc)
    assumptions = [
        {"scenario_name": name, "terminal_growth": 0.025 if name == "BASE" else 0.03, "rationale": f"Reviewed {name} terminal growth."}
        for name in names
    ]
    candidate = build_terminal_growth_candidate(
        [_tg_anchor(LONG_RUN_INFLATION, 0.02), _tg_anchor(LONG_RUN_REAL_GROWTH, 0.015)],
        wacc,
        scenario_assumptions=assumptions,
    )
    assertion = build_terminal_growth_review_assertion(candidate, reviewer="terminal reviewer", approved_at="2026-09-12T21:10:00+09:00", review_basis="M26 terminal fixture")
    return build_binding_proposal_with_terminal_growth(v04, finalize_reviewed_terminal_growth(candidate, assertion))


def _forecast_scenarios(names: list[str] | None = None, years: list[int] | None = None) -> list[dict]:
    names = names or ["BASE"]
    years = years or [2027, 2028]
    result = []
    for name in names:
        bull = name == "BULL"
        rows = []
        for index, year in enumerate(years):
            rows.append({
                "year": year,
                "revenue": (2000.0 + 200.0 * index) * (1.1 if bull else 1.0),
                "ebit_margin": 0.10 + 0.01 * index + (0.02 if bull else 0.0),
                "tax_rate": 0.25,
                "depreciation_amortization": 80.0 + 8.0 * index,
                "capex": 100.0 + 5.0 * index,
                "delta_nwc": 50.0 - 10.0 * index,
            })
        result.append({"scenario_name": name, "rationale": f"Explicit reviewed {name} operating forecast.", "years": rows})
    return result


def _forecast_package(names: list[str] | None = None, years: list[int] | None = None) -> dict:
    names = names or ["BASE"]
    candidate = build_forecast_candidate(_forecast_scenarios(names, years), entity_id="DART_CORP:00126380", financial_scope="CFS", capital_currency="KRW", as_of="2026-09-12")
    assertion = build_forecast_review_assertion(candidate, reviewer="forecast reviewer", approved_at="2026-09-12T21:20:00+09:00", review_basis="Reviewed all scenario rows and FCFF diagnostics.")
    return finalize_reviewed_forecast(candidate, assertion)


def _draft(names: list[str] | None = None, years: list[int] | None = None) -> dict:
    names = names or ["BASE"]
    years = years or [2027, 2028]
    draft = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    draft["currency"] = "KRW"
    draft["name"] = "M26 integrated forecast"
    source = copy.deepcopy(draft["equity"]["scenarios"]["BASE"])
    template_row = copy.deepcopy(source["years"][0])
    scenarios = {}
    for name in names:
        scenario = copy.deepcopy(source)
        scenario["years"] = []
        for year in years:
            row = copy.deepcopy(template_row)
            row["year"] = year
            scenario["years"].append(row)
        scenarios[name] = scenario
    draft["equity"]["scenarios"] = scenarios
    return draft


def _decision(proposal: dict, field: str) -> dict:
    return next(item for item in proposal["draft_input_matrix"] if item["field"] == field)


def test_candidate_recomputes_fcff_diagnostics_and_remains_assumption_candidate() -> None:
    candidate = build_forecast_candidate(_forecast_scenarios(), entity_id="DART_CORP:00126380", financial_scope="CFS", capital_currency="KRW", as_of="2026-09-12")
    first = candidate["diagnostics"]["BASE"][0]
    assert first["ebit"] == pytest.approx(200.0)
    assert first["nopat"] == pytest.approx(150.0)
    assert first["fcff"] == pytest.approx(80.0)
    assert first["revenue_growth"] is None
    assert candidate["class"] == "ASSUMPTION_CANDIDATE"
    assert validate_forecast_candidate(candidate)["eligible_for_human_review"] is True


def test_forecast_years_must_be_common_future_and_rows_complete() -> None:
    bad_year = _forecast_scenarios(years=[2026, 2027])
    with pytest.raises(CaseServiceError, match="after valuation year|가치평가 연도"):
        build_forecast_candidate(bad_year, entity_id="DART_CORP:00126380", financial_scope="CFS", capital_currency="KRW", as_of="2026-09-12")
    mismatch = _forecast_scenarios(["BASE", "BULL"])
    mismatch[1]["years"] = mismatch[1]["years"][:1]
    with pytest.raises(CaseServiceError, match="identical forecast-year set|동일 Forecast 연도집합"):
        build_forecast_candidate(mismatch, entity_id="DART_CORP:00126380", financial_scope="CFS", capital_currency="KRW", as_of="2026-09-12")
    missing = _forecast_scenarios()
    missing[0]["years"][0].pop("capex")
    with pytest.raises(CaseServiceError):
        build_forecast_candidate(missing, entity_id="DART_CORP:00126380", financial_scope="CFS", capital_currency="KRW", as_of="2026-09-12")


def test_forecast_numeric_guards_fail_closed() -> None:
    bad = _forecast_scenarios()
    bad[0]["years"][0]["revenue"] = -1
    with pytest.raises(CaseServiceError, match="revenue|매출"):
        build_forecast_candidate(bad, entity_id="DART_CORP:00126380", financial_scope="CFS", capital_currency="KRW", as_of="2026-09-12")
    bad = _forecast_scenarios()
    bad[0]["years"][0]["tax_rate"] = 1
    with pytest.raises(CaseServiceError, match="tax rate|세율"):
        build_forecast_candidate(bad, entity_id="DART_CORP:00126380", financial_scope="CFS", capital_currency="KRW", as_of="2026-09-12")
    bad = _forecast_scenarios()
    bad[0]["years"][0]["capex"] = -1
    with pytest.raises(CaseServiceError, match="CAPEX|D&A"):
        build_forecast_candidate(bad, entity_id="DART_CORP:00126380", financial_scope="CFS", capital_currency="KRW", as_of="2026-09-12")


def test_reviewed_forecast_is_assumption_and_nested_tamper_fails() -> None:
    package = _forecast_package()
    assert package["class"] == "ASSUMPTION"
    assert validate_reviewed_forecast(package)["eligible"] is True
    tampered = copy.deepcopy(package)
    tampered["candidate"]["scenarios"][0]["years"][0]["revenue"] += 1
    tampered["package_sha256"] = _rehash(tampered, "package_sha256")
    with pytest.raises(CaseServiceError):
        validate_reviewed_forecast(tampered)


def test_v06_requires_v05_and_replaces_exactly_six_forecast_decisions() -> None:
    names = ["BASE", "BULL"]
    v05 = _v05(names)
    package = _forecast_package(names)
    proposal = build_binding_proposal_with_forecast(v05, package)
    checked = validate_binding_proposal_v6(proposal)
    assert proposal["schema_version"] == "draft-binding-proposal-v0.6"
    assert checked["atomic_forecast_fields"] == list(FORECAST_FIELDS)
    for field in FORECAST_FIELDS:
        assert _decision(proposal, field)["state"] == "DIRECT_BIND"
    for field in ("scenario.wacc", "scenario.terminal_growth", "equity.cash", "equity.debt", "equity.diluted_shares"):
        assert _decision(proposal, field) == _decision(v05, field)
    assert proposal["completeness"]["direct_bind_count"] == v05["completeness"]["direct_bind_count"] + len(FORECAST_FIELDS)
    with pytest.raises(CaseServiceError, match="v0.5"):
        build_binding_proposal_with_forecast(v05["base_proposal"], package)


def test_forecast_approval_is_all_six_or_none() -> None:
    proposal = build_binding_proposal_with_forecast(_v05(["BASE"]), _forecast_package(["BASE"]))
    draft = _draft(["BASE"])
    with pytest.raises(CaseServiceError, match="all-six-or-none|6개 전부"):
        build_binding_approval(
            proposal,
            draft,
            reviewer="human",
            target_entity_id="DART_CORP:00126380",
            target_financial_scope="CFS",
            approved_fields=[FORECAST_FIELDS[0]],
            approved_at="2026-09-12T21:30:00+09:00",
        )


def test_atomic_forecast_apply_updates_all_components_and_preserves_input_draft() -> None:
    names = ["BASE", "BULL"]
    package = _forecast_package(names)
    proposal = build_binding_proposal_with_forecast(_v05(names), package)
    draft = _draft(names)
    before = copy.deepcopy(draft)
    approval = build_binding_approval(
        proposal,
        draft,
        reviewer="human",
        target_entity_id="DART_CORP:00126380",
        target_financial_scope="CFS",
        approved_fields=list(FORECAST_FIELDS),
        approved_at="2026-09-12T21:30:00+09:00",
    )
    result = apply_binding_approval(proposal, draft, approval)
    assert draft == before
    assert validate_bound_draft_result(result)["applied_field_count"] == 6
    by_name = {item["scenario_name"]: item for item in package["scenarios"]}
    for name in names:
        assert result["draft_after"]["equity"]["scenarios"][name]["years"] == by_name[name]["years"]
    revenue_diff = next(item for item in result["applied_diffs"] if item["field"] == "scenario.years.revenue")
    assert revenue_diff["forecast_component"] == "revenue"
    assert revenue_diff["source_forecast_package_sha256"] == package["package_sha256"]
    assert revenue_diff["forecast_block_sha256"] == package["forecast_block_sha256"]
    assert revenue_diff["review_assertion_sha256"] == package["review_assertion"]["assertion_sha256"]
    assert revenue_diff["scenario_names"] == ["BASE", "BULL"]
    assert revenue_diff["forecast_years"] == [2027, 2028]


def test_forecast_apply_requires_exact_draft_scenario_and_year_sets() -> None:
    proposal = build_binding_proposal_with_forecast(_v05(["BASE"]), _forecast_package(["BASE"], [2027, 2028]))
    wrong_years = _draft(["BASE"], [2027, 2029])
    with pytest.raises(CaseServiceError, match="year set|연도집합"):
        build_binding_approval(
            proposal,
            wrong_years,
            reviewer="human",
            target_entity_id="DART_CORP:00126380",
            target_financial_scope="CFS",
            approved_fields=list(FORECAST_FIELDS),
            approved_at="2026-09-12T21:30:00+09:00",
        )
    wrong_scenarios = _draft(["BASE", "BULL"], [2027, 2028])
    with pytest.raises(CaseServiceError, match="scenario target set|시나리오"):
        build_binding_approval(
            proposal,
            wrong_scenarios,
            reviewer="human",
            target_entity_id="DART_CORP:00126380",
            target_financial_scope="CFS",
            approved_fields=list(FORECAST_FIELDS),
            approved_at="2026-09-12T21:30:00+09:00",
        )


def test_all_six_forecast_component_names_match_material_fields() -> None:
    assert set(FORECAST_FIELDS) == {f"scenario.years.{component}" for component in FORECAST_COMPONENTS}
