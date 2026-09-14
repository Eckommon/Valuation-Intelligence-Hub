from __future__ import annotations

import json
from pathlib import Path

from valuation_hub import cli_entry_m30


def _target_args() -> list[str]:
    return [
        "--case-id", "US_INGR_INGREDION",
        "--legal-name", "Ingredion Incorporated",
        "--ticker", "INGR",
        "--exchange", "NYSE",
        "--cik", "0001046257",
        "--financial-period-end", "2026-06-30",
        "--valuation-as-of", "2026-09-14",
        "--form", "10-Q",
    ]


def test_m30_readiness_cli_builds_without_sec_runtime_credential(monkeypatch, capsys) -> None:
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    rc = cli_entry_m30.main(["--json", "real-equity-readiness-build", *_target_args()])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == "real-equity-readiness-manifest-v0.1"
    assert payload["canonical"] is False
    assert len(payload["fields"]) == 13
    assert {item["code"] for item in payload["blockers"]} == {"REAL_SEC_PREFLIGHT_NOT_SUPPLIED"}


def test_m30_readiness_cli_validate_is_read_only(tmp_path: Path, capsys) -> None:
    rc = cli_entry_m30.main(["--json", "real-equity-readiness-build", *_target_args()])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    before = path.read_bytes()
    assert cli_entry_m30.main(["--json", "real-equity-readiness-validate", str(path)]) == 0
    checked = json.loads(capsys.readouterr().out)
    assert checked["status"] == "PASS_REAL_EQUITY_READINESS_MANIFEST_VALIDATION"
    assert checked["material_field_count"] == 13
    assert path.read_bytes() == before


def test_m30_readiness_commands_are_intercepted_and_prior_command_still_delegates() -> None:
    assert cli_entry_m30._command(["real-equity-readiness-build"]) == "real-equity-readiness-build"
    assert cli_entry_m30._command(["real-equity-readiness-validate"]) == "real-equity-readiness-validate"
    assert cli_entry_m30._command(["complete-handoff-build"]) is None
