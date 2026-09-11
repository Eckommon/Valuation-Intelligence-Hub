"""Interactive evidence/preview tests / 인터랙티브 근거·미리보기 테스트."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from valuation_hub.case_service import CaseServiceError, run_case
from valuation_hub.interactive import evidence_view, preview_case


ROOT = Path(__file__).resolve().parents[1]


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_evidence_view_exposes_classification_and_provenance() -> None:
    view = evidence_view("KR_010120_LS_ELECTRIC", ROOT)
    assert view["read_only"] is True
    assert view["promotion_gate"] == "PASS_MATERIAL_INPUTS_RECONCILED"
    assert view["classification_counts"]["FACT"] > 0
    normalized = [c for c in view["claims"] if c.get("class") == "NORMALIZED_FACT"]
    assert normalized
    assert normalized[0]["source"]["publisher"]
    assert normalized[0]["depends_on"]


def test_equity_preview_is_noncanonical_and_changes_value() -> None:
    canonical = run_case("KR_229640_LS_ECO_ENERGY", ROOT)
    base = canonical["runtime"]["BASE"]["value_per_share"]
    preview = preview_case(
        "KR_229640_LS_ECO_ENERGY",
        {"scenario": "BASE", "revenue_scale": 1.10, "ebit_margin_delta": 0.01},
        ROOT,
    )
    assert preview["canonical"] is False
    assert preview["status"] == "PREVIEW_NOT_CANONICAL"
    assert preview["preview"]["value_per_share"] != pytest.approx(base)


def test_equity_preview_fails_closed_on_terminal_growth_gte_wacc() -> None:
    with pytest.raises(CaseServiceError, match="terminal growth"):
        preview_case(
            "KR_010120_LS_ELECTRIC",
            {"scenario": "BASE", "wacc": 0.05, "terminal_growth": 0.05},
            ROOT,
        )


def test_venture_preview_requires_probabilities_sum_to_one() -> None:
    with pytest.raises(CaseServiceError, match="probabilities must sum"):
        preview_case(
            "US_JTAI_JET_AI",
            {"probabilities": {"FAILURE": 0.5, "SURVIVAL": 0.5, "BREAKOUT": 0.5}},
            ROOT,
        )


def test_preview_does_not_mutate_canonical_files() -> None:
    case_dir = ROOT / "analyses" / "equities" / "KR_010120_LS_ELECTRIC"
    paths = [case_dir / "case_inputs.json", case_dir / "valuation_result.json", case_dir / "evidence_manifest.json"]
    before = {path: _digest(path) for path in paths}
    preview_case("KR_010120_LS_ELECTRIC", {"scenario": "BULL", "wacc": 0.10}, ROOT)
    after = {path: _digest(path) for path in paths}
    assert before == after
    assert run_case("KR_010120_LS_ELECTRIC", ROOT)["runtime"]["BASE"]["value_per_share"] == pytest.approx(41475, abs=1)
