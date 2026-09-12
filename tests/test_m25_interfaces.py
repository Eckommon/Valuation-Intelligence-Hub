"""M25 additive CLI/Web interface contracts."""
from __future__ import annotations

from pathlib import Path

from valuation_hub import cli_entry_m25
from valuation_hub.web_terminal_growth import render_terminal_growth_lab


def test_m25_cli_intercepts_only_terminal_growth_surface_and_v05_validation() -> None:
    for command in (
        "terminal-growth-anchor-build",
        "terminal-growth-anchor-validate",
        "terminal-growth-candidate-build",
        "terminal-growth-candidate-validate",
        "terminal-growth-review-build",
        "terminal-growth-review-validate",
        "terminal-growth-finalize",
        "terminal-growth-validate",
        "binding-build-with-terminal-growth",
        "binding-validate",
        "web",
    ):
        assert cli_entry_m25._command([command]) == command
    assert cli_entry_m25._command(["wacc-candidate-validate"]) is None
    assert cli_entry_m25._command(["share-bridge-validate"]) is None
    assert cli_entry_m25._command(["debt-validate"]) is None


def test_terminal_growth_candidate_parser_requires_all_three_input_artifacts() -> None:
    args = cli_entry_m25._parser().parse_args([
        "terminal-growth-candidate-build",
        "anchors.json",
        "wacc.json",
        "scenario-assumptions.json",
    ])
    assert args.command == "terminal-growth-candidate-build"
    assert args.anchors == Path("anchors.json")
    assert args.wacc_package == Path("wacc.json")
    assert args.scenario_assumptions == Path("scenario-assumptions.json")


def test_terminal_growth_web_lab_is_assumption_only_and_no_write() -> None:
    page = render_terminal_growth_lab()
    assert "ASSUMPTION · WACC-DEPENDENT · HUMAN REVIEW" in page
    assert "Macro anchor ≠ terminal-growth fact." in page
    assert "g &lt; reviewed WACC" in page
    assert "/api/terminal-growth/" in page
    assert "NO DRAFT APPLY · NO FILE WRITE · NO PROMOTION · NO CANONICAL WRITE" in page
    assert "/api/terminal-growth/apply" not in page
    assert "/api/terminal-growth/file-write" not in page
    assert "/api/terminal-growth/canonical" not in page
