"""M29 additive CLI/Web interface contract tests."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from valuation_hub import cli_entry_m28, cli_entry_m29, cli_entry_m30, cli_entry_m30r1, cli_entry_m30r2
from valuation_hub.web_complete_equity_handoff import render_complete_handoff_lab


def _fixtures():
    path = Path(__file__).with_name("test_m29_complete_equity_handoff.py")
    spec = importlib.util.spec_from_file_location("_m29_interface_fixture", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_console_entrypoint_targets_latest_m30r2_and_preserves_m29_delegation() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    assert 'vih = "valuation_hub.cli_entry_m30r2:main"' in pyproject
    assert cli_entry_m30r2.prior_cli is cli_entry_m30r1
    assert cli_entry_m30r1.prior_cli is cli_entry_m30
    assert cli_entry_m30.prior_cli is cli_entry_m29
    assert cli_entry_m29.prior_cli is cli_entry_m28


def test_m29_cli_intercepts_only_complete_handoff_and_version_aware_promotion_admission_surface() -> None:
    assert cli_entry_m29._command(["complete-handoff-build"]) == "complete-handoff-build"
    assert cli_entry_m29._command(["candidate-validate"]) == "candidate-validate"
    assert cli_entry_m29._command(["promotion-check"]) == "promotion-check"
    assert cli_entry_m29._command(["admission-build"]) == "admission-build"
    assert cli_entry_m29._command(["minority-sec-extract"]) is None
    assert cli_entry_m29._command(["market-price-candidate-build"]) is None


def test_complete_handoff_cli_build_and_validate_v02_without_writing_files(tmp_path, capsys) -> None:
    f = _fixtures()
    result = f._complete_result()
    catalog = f._catalog(result)
    result_path = tmp_path / "result.json"
    catalog_path = tmp_path / "catalog.json"
    candidate_path = tmp_path / "candidate.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")

    before = {item.name for item in tmp_path.iterdir()}
    assert cli_entry_m29.main(["--json", "complete-handoff-build", str(result_path), str(catalog_path)]) == 0
    candidate = json.loads(capsys.readouterr().out)
    assert candidate["schema_version"] == "promotion-candidate-v0.2"
    assert candidate["source_bound_result_sha256"] == result["result_sha256"]
    assert {item.name for item in tmp_path.iterdir()} == before

    candidate_path.write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")
    assert cli_entry_m29.main(["--json", "candidate-validate", str(candidate_path)]) == 0
    checked = json.loads(capsys.readouterr().out)
    assert checked["ready_for_review"] is True
    assert checked["blockers"] == []


def test_complete_handoff_web_lab_is_preparation_only() -> None:
    page = render_complete_handoff_lab()
    assert "/api/equity-handoff/" in page
    assert "13/13 DIRECT_BIND" in page
    assert "NO UNKNOWN" in page
    assert "NO AUTO APPROVAL" in page
    assert "NO FILE WRITE" in page
    assert "NO ADMISSION APPLY" in page
    assert "NO CANONICAL WRITE" in page
