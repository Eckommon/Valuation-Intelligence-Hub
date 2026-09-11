"""Valuation visualization tests / 가치평가 시각화 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest

from valuation_hub.case_service import run_case
from valuation_hub.interactive import evidence_view
from valuation_hub.visualization import (
    equity_market_scenario_chart,
    evidence_classification_summary,
    fcff_trend_chart,
    horizontal_value_chart,
    venture_outcome_chart,
)

ROOT = Path(__file__).resolve().parents[1]


def test_equity_charts_use_runtime_values() -> None:
    result = run_case("KR_010120_LS_ELECTRIC", ROOT)
    runtime = result["runtime"]
    bars = equity_market_scenario_chart(runtime, result["market_price"], "KRW")
    trend = fcff_trend_chart(runtime, currency="KRW")
    assert "Market / 시장" in bars
    assert "Bear" in bars and "Base" in bars and "Bull" in bars
    assert "₩206,000" in bars
    assert "polyline" in trend
    assert "BEAR" in trend and "BASE" in trend and "BULL" in trend


def test_venture_chart_exposes_probabilities_and_expected_value() -> None:
    result = run_case("US_JTAI_JET_AI", ROOT)
    chart = venture_outcome_chart(result["runtime"], result["market_price"], "USD")
    assert "Expected / 기대가치" in chart
    assert "Failure (60%)" in chart
    assert "Breakout (10%)" in chart


def test_evidence_summary_contains_real_class_counts() -> None:
    evidence = evidence_view("KR_229640_LS_ECO_ENERGY", ROOT)
    summary = evidence_classification_summary(evidence["classification_counts"])
    assert "FACT" in summary
    assert "data-class=\"ALL\"" in summary


def test_value_chart_rejects_bad_values() -> None:
    with pytest.raises(ValueError):
        horizontal_value_chart([])
    with pytest.raises(ValueError):
        horizontal_value_chart([("bad", -1)])
