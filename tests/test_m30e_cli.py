from __future__ import annotations

import json
from pathlib import Path

from valuation_hub import cli_entry_m30


def _repo(tmp_path: Path) -> Path:
    (tmp_path / "workspace" / "source_snapshots").mkdir(parents=True)
    return tmp_path


def _build_snapshot(root: Path, capsys) -> Path:
    source = root / "market_source.txt"
    source.write_text("official quote INGR 132.50\n", encoding="utf-8")
    output = Path("workspace/source_snapshots/ingr_market.json")
    rc = cli_entry_m30.main([
        "--root", str(root), "--json", "external-source-snapshot-build", str(source),
        "--publisher", "Example Official Publisher",
        "--source-type", "official_market_quote",
        "--source-tier", "A",
        "--source-locator", "https://example.org/market/ingr",
        "--captured-at", "2026-09-14T10:00:00+09:00",
        "--output", str(output),
    ])
    assert rc == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "EXTERNAL_SOURCE_SNAPSHOT_MATERIALIZED"
    return output


def test_external_snapshot_cli_build_validate_and_bound_market_candidate(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    snapshot = _build_snapshot(root, capsys)
    rc = cli_entry_m30.main(["--root", str(root), "--json", "external-source-snapshot-validate", str(snapshot)])
    assert rc == 0
    checked = json.loads(capsys.readouterr().out)
    assert checked["status"] == "PASS_EXTERNAL_SOURCE_SNAPSHOT_VALIDATION"

    rc = cli_entry_m30.main([
        "--root", str(root), "--json", "market-price-candidate-build-from-snapshot", str(snapshot),
        "--price", "132.50", "--currency", "USD", "--entity-id", "SEC_CIK:0001046257",
        "--financial-scope", "CFS", "--instrument-id", "NYSE:INGR", "--symbol", "INGR",
        "--venue", "NYSE", "--quote-type", "OFFICIAL_CLOSE", "--trading-date", "2026-09-14",
        "--observed-at", "2026-09-14T16:00:00-04:00", "--as-of", "2026-09-14",
    ])
    assert rc == 0
    candidate = json.loads(capsys.readouterr().out)
    stored = json.loads((root / snapshot).read_text(encoding="utf-8"))
    assert candidate["source"]["snapshot_sha256"] == stored["snapshot_sha256"]
    assert candidate["source"]["locator"] == "https://example.org/market/ingr"


def test_snapshot_bound_wacc_and_terminal_cli(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    snapshot = _build_snapshot(root, capsys)
    rc = cli_entry_m30.main([
        "--root", str(root), "--json", "wacc-source-build-from-snapshot", str(snapshot),
        "--metric", "risk_free_rate", "--value", "0.041", "--unit", "decimal",
        "--observed-on", "2026-09-14", "--claim-class", "FACT",
    ])
    assert rc == 0
    wacc = json.loads(capsys.readouterr().out)
    rc = cli_entry_m30.main([
        "--root", str(root), "--json", "terminal-growth-anchor-build-from-snapshot", str(snapshot),
        "--metric", "long_run_inflation", "--value", "0.02", "--observed-on", "2026-09-14",
        "--claim-class", "ASSUMPTION",
    ])
    assert rc == 0
    anchor = json.loads(capsys.readouterr().out)
    stored = json.loads((root / snapshot).read_text(encoding="utf-8"))
    assert wacc["source"]["source_sha256"] == stored["snapshot_sha256"]
    assert anchor["source"]["source_sha256"] == stored["snapshot_sha256"]


def test_external_output_escape_fails_closed(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path)
    source = root / "source.txt"
    source.write_text("x", encoding="utf-8")
    rc = cli_entry_m30.main([
        "--root", str(root), "--json", "external-source-snapshot-build", str(source),
        "--publisher", "Publisher", "--source-type", "release", "--source-tier", "A",
        "--source-locator", "https://example.org/source", "--captured-at", "2026-09-14T10:00:00+09:00",
        "--output", "outside.json",
    ])
    assert rc == 2
    assert "workspace/source_snapshots" in json.loads(capsys.readouterr().out)["error"]


def test_external_commands_are_additive() -> None:
    assert cli_entry_m30._command(["external-source-snapshot-build"]) == "external-source-snapshot-build"
    assert cli_entry_m30._command(["wacc-source-build-from-snapshot"]) == "wacc-source-build-from-snapshot"
    assert cli_entry_m30._command(["complete-handoff-build"]) is None
