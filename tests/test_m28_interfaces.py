"""M28 additive CLI/Web interface contract tests."""
from __future__ import annotations

from pathlib import Path

from valuation_hub import cli_entry_m27, cli_entry_m28, cli_entry_m29, cli_entry_m30, cli_entry_m30r1
from valuation_hub.web_minority_interest import render_minority_interest_lab


def test_console_entrypoint_targets_latest_successor_and_preserves_m28_chain() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    assert 'vih = "valuation_hub.cli_entry_m30r1:main"' in pyproject
    assert cli_entry_m28.prior_cli is cli_entry_m27
    assert cli_entry_m29.prior_cli is cli_entry_m28
    assert cli_entry_m30.prior_cli is cli_entry_m29
    assert cli_entry_m30r1.prior_cli is cli_entry_m30


def test_m28_cli_intercepts_only_successor_surface() -> None:
    assert cli_entry_m28._command(["minority-sec-extract"]) == "minority-sec-extract"
    assert cli_entry_m28._command(["binding-build-with-minority-interest"]) == "binding-build-with-minority-interest"
    assert cli_entry_m28._command(["market-price-candidate-build"]) is None
    assert cli_entry_m28._command(["forecast-candidate-build"]) is None


def test_minority_interest_web_lab_is_preparation_only() -> None:
    page = render_minority_interest_lab()
    assert "/api/minority-interest/" in page
    assert "MISSING ≠ ZERO" in page
    assert "nonredeemable" in page.lower()
    assert "NO DRAFT APPLY" in page
    assert "NO FILE WRITE" in page
    assert "NO PROMOTION" in page
    assert "NO CANONICAL WRITE" in page
