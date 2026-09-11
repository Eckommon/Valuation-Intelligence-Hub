"""Draft CLI workflow tests / Draft CLI 흐름 테스트."""

from __future__ import annotations

import json
from pathlib import Path

from valuation_hub import cli
from valuation_hub.draft_service import template

ROOT = Path(__file__).resolve().parents[1]


def test_cli_draft_template_outputs_valid_json(capsys) -> None:
    rc = cli.main(["--root", str(ROOT), "draft-template", "equity_fcff"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "DRAFT_USER_SUPPLIED"
    assert payload["model"] == "equity_fcff"


def test_cli_draft_validate_and_run_file(tmp_path: Path, capsys) -> None:
    path = tmp_path / "draft.json"
    path.write_text(json.dumps(template("venture_probability", ROOT)), encoding="utf-8")
    rc = cli.main(["--root", str(ROOT), "draft-validate", str(path)])
    assert rc == 0
    assert "PASS DRAFT" in capsys.readouterr().out

    rc = cli.main(["--root", str(ROOT), "--json", "draft-run", str(path)])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["canonical"] is False
    assert payload["status"] == "DRAFT_USER_SUPPLIED"
    assert payload["runtime"]["expected_present_value_per_share"] > 0


def test_cli_draft_rejects_bad_json(tmp_path: Path, capsys) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    rc = cli.main(["draft-run", str(path)])
    assert rc == 2
    assert "Draft JSON" in capsys.readouterr().err
