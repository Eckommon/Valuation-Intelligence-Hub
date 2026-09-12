"""M26 additive CLI/Web interface regression tests."""
from __future__ import annotations

import json
from pathlib import Path

from valuation_hub import cli_entry_m26, cli_entry_m27
from valuation_hub.web_forecast import render_forecast_lab

ROOT = Path(__file__).resolve().parents[1]


def _scenarios() -> list[dict]:
    return [
        {
            "scenario_name": "BASE",
            "rationale": "Explicit integrated forecast for interface test.",
            "years": [
                {
                    "year": 2027,
                    "revenue": 2000.0,
                    "ebit_margin": 0.10,
                    "tax_rate": 0.25,
                    "depreciation_amortization": 80.0,
                    "capex": 100.0,
                    "delta_nwc": 50.0,
                }
            ],
        }
    ]


def test_m26_cli_builds_forecast_candidate(tmp_path: Path, capsys) -> None:
    path = tmp_path / "scenarios.json"
    path.write_text(json.dumps(_scenarios()), encoding="utf-8")
    rc = cli_entry_m26.main([
        "forecast-candidate-build",
        str(path),
        "--entity-id", "DART_CORP:00126380",
        "--financial-scope", "CFS",
        "--capital-currency", "KRW",
        "--as-of", "2026-09-12",
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == "forecast-scenario-assumption-candidate-v0.1"
    assert payload["class"] == "ASSUMPTION_CANDIDATE"
    assert payload["forecast_years"] == [2027]


def test_m26_cli_delegates_older_commands_unchanged(monkeypatch) -> None:
    seen: list[list[str]] = []

    def prior(argv: list[str]) -> int:
        seen.append(argv)
        return 73

    monkeypatch.setattr(cli_entry_m26.prior_cli, "main", prior)
    argv = ["draft-validate", "example.json"]
    assert cli_entry_m26.main(argv) == 73
    assert seen == [argv]


def test_forecast_web_lab_is_preparation_only() -> None:
    page = render_forecast_lab()
    assert "Integrated FCFF Forecast" in page
    assert "NO DRAFT APPLY" in page
    assert "NO FILE WRITE" in page
    assert "NO PROMOTION" in page
    assert "NO CANONICAL WRITE" in page
    assert "/api/forecast/" in page


def test_m26_wrapper_remains_in_successor_delegation_chain() -> None:
    assert cli_entry_m27.prior_cli is cli_entry_m26
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'vih = "valuation_hub.cli_entry_m27:main"' in pyproject
