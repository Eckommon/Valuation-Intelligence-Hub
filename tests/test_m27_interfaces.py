"""M27 additive CLI/Web interface contract tests."""
from __future__ import annotations

from pathlib import Path

from valuation_hub import cli_entry_m27
from valuation_hub.web_market_price import render_market_price_lab


def test_console_entrypoint_targets_m27_wrapper() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    assert 'vih = "valuation_hub.cli_entry_m27:main"' in pyproject


def test_m27_cli_intercepts_market_price_and_delegates_older_commands() -> None:
    assert cli_entry_m27._command(["market-price-candidate-build"]) == "market-price-candidate-build"
    assert cli_entry_m27._command(["forecast-candidate-build"]) is None
    assert cli_entry_m27._command(["debt-aggregate"]) is None


def test_market_price_web_lab_is_preparation_only() -> None:
    page = render_market_price_lab()
    assert "/api/market-price/" in page
    assert "NO DRAFT APPLY" in page
    assert "NO FILE WRITE" in page
    assert "NO PROMOTION" in page
    assert "NO CANONICAL WRITE" in page
    assert "Historical adjusted price ≠ valuation-date market price" in page
