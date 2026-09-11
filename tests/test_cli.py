"""VIH CLI integration tests / VIH CLI 통합테스트."""

from __future__ import annotations

import json
from pathlib import Path

from valuation_hub.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_cli_list_json(capsys) -> None:
    code = main(["--root", str(ROOT), "--json", "list"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload) == 3
    assert payload[0]["case_id"] == "KR_010120_LS_ELECTRIC"


def test_cli_validate_json(capsys) -> None:
    code = main(["--root", str(ROOT), "--json", "validate", "US_JTAI_JET_AI"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is True
    assert payload["model"] == "venture_probability"


def test_cli_run_json(capsys) -> None:
    code = main(["--root", str(ROOT), "--json", "run", "KR_229640_LS_ECO_ENERGY"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["grounded"] is True
    assert round(payload["runtime"]["BASE"]["value_per_share"]) == 27326


def test_cli_report(capsys) -> None:
    code = main(["--root", str(ROOT), "report", "US_JTAI_JET_AI"])
    assert code == 0
    output = capsys.readouterr().out
    assert "Jet.AI Reference Valuation" in output
    assert "Jet.AI 기준 가치평가" in output


def test_cli_unknown_case_returns_nonzero(capsys) -> None:
    code = main(["--root", str(ROOT), "--json", "run", "DOES_NOT_EXIST"])
    assert code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert "unknown case" in payload["error"]
