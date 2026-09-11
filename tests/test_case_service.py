"""Executable case service integration tests / 실행형 사례 서비스 통합테스트."""

from __future__ import annotations

from pathlib import Path

import pytest

from valuation_hub.case_service import CaseServiceError, list_cases, read_report, run_case, validate_case

ROOT = Path(__file__).resolve().parents[1]


def test_registry_lists_three_reference_cases() -> None:
    cases = list_cases(ROOT)
    assert [case["case_id"] for case in cases] == [
        "KR_010120_LS_ELECTRIC",
        "KR_229640_LS_ECO_ENERGY",
        "US_JTAI_JET_AI",
    ]


@pytest.mark.parametrize(
    "case_id",
    ["KR_010120_LS_ELECTRIC", "KR_229640_LS_ECO_ENERGY", "US_JTAI_JET_AI"],
)
def test_all_registered_reference_cases_validate(case_id: str) -> None:
    result = validate_case(case_id, ROOT)
    assert result["valid"] is True
    assert result["promotion_gate"].startswith("PASS_")


def test_ls_electric_service_reproduces_reference() -> None:
    result = run_case("KR_010120_LS_ELECTRIC", ROOT)
    assert result["grounded"] is True
    assert result["runtime"]["BASE"]["value_per_share"] == pytest.approx(41475, abs=1.0)


def test_ls_eco_service_reproduces_reference() -> None:
    result = run_case("KR_229640_LS_ECO_ENERGY", ROOT)
    assert result["runtime"]["BASE"]["value_per_share"] == pytest.approx(27326, abs=1.0)
    assert result["runtime"]["BULL"]["value_per_share"] > result["market_price"]


def test_jet_ai_service_routes_to_venture_model() -> None:
    result = run_case("US_JTAI_JET_AI", ROOT)
    assert result["model"] == "venture_probability"
    assert result["runtime"]["expected_present_value_per_share"] == pytest.approx(3.2467821083)


def test_report_is_bilingual_artifact() -> None:
    report = read_report("KR_229640_LS_ECO_ENERGY", ROOT)
    assert "Reference Valuation" in report
    assert "기준 가치평가" in report


def test_unknown_case_fails_closed() -> None:
    with pytest.raises(CaseServiceError, match="unknown case"):
        run_case("UNKNOWN_CASE", ROOT)
