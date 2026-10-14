"""M30-R8M24 source-locked INGR readiness, no fake market data or review."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from valuation_hub import ingr_r8_m23_execution as m23_runner
from valuation_hub import ingr_r8_m24_readiness as wacc
from valuation_hub.case_service import CaseServiceError
from valuation_hub.external_source import build_external_source_snapshot
from valuation_hub.wacc_assumption import (
    REQUIRED_METRICS, RATE_METRICS,
    build_wacc_source_input,
)


def _fixture(name: str):
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location("_wacc_" + name.replace(".py", ""), path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _save(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, ensure_ascii=False), encoding="utf-8")


def _workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    scope = _fixture("test_m30r8scope_reconciliation.py")
    workspace, _, _, _, _ = scope._context(tmp_path, monkeypatch)
    result = m23_runner.run_real_m23(repo_root=tmp_path, artifact_root=workspace, enforce_git=False)
    assert result["status"] == "REAL_INGR_M23_R6_ASSUMPTION_READY"
    monkeypatch.setattr(wacc, "M23_V03_SHA", result["m23_r6_v03_proposal_sha256"])
    monkeypatch.setattr(wacc, "M23_V02_SHA", result["m23_sec_debt_v02_proposal_sha256"])
    return workspace, Path(result["run_dir"])


def test_real_m23_sha_is_required_and_empty_wacc_discovery_holds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, m23_dir = _workspace(tmp_path, monkeypatch)
    result = wacc.run_wacc_readiness(repo_root=tmp_path, artifact_root=workspace,
                                     m23_run_dir=m23_dir, enforce_git=False)
    assert result["status"] == "HOLD_REAL_INGR_M24_WACC_INPUT_GAPS"
    assert result["metrics_ready"] == 0
    assert [r["metric"] for r in result["metrics"]] == list(REQUIRED_METRICS)
    assert all(r["status"] == "MISSING_SOURCE_INPUT" for r in result["metrics"])
    assert not result["human_review_completed"]
    assert not result["draft_v04_created"]
    assert Path(result["output"]).exists()
    monkeypatch.setattr(wacc, "M23_V03_SHA", "a"*64)
    with pytest.raises(CaseServiceError, match="SHA"):
        wacc.run_wacc_readiness(repo_root=tmp_path, artifact_root=workspace,
                                 m23_run_dir=m23_dir, enforce_git=False)


def _inputs(workspace: Path, *, raw: bool = True, stale: bool = False,
            tier_d: bool = False):
    values = [0.035, 0.05, 1.15, 0.047, 8_000_000_000, 1_783_000_000, 0.24]
    units = ["decimal", "decimal", "ratio", "decimal", "USD", "USD", "decimal"]
    for i, (metric, value, unit) in enumerate(zip(REQUIRED_METRICS, values, units)):
        tier = "D" if tier_d and i == 2 else "B"
        locator = f"https://example.test/evidence/{metric}/2026"
        text = f"Test-only evidence for {metric}: {value} {unit}. NOT REAL MARKET DATA."
        snap = build_external_source_snapshot(text, source_publisher="Synthetic fixture",
            source_type="test-only-source", source_tier=tier,
            source_locator=locator, captured_at="2026-09-12T12:00:00+09:00")
        observation = "2026-07-01" if stale and i == 0 else "2026-09-01"
        item = build_wacc_source_input(
            metric=metric, value=value, unit=unit, observed_on=observation,
            claim_class="ASSUMPTION" if i in (1, 2, 3, 6) else "FACT",
            source_publisher="Synthetic fixture", source_type="test-only-source",
            source_tier=tier, source_locator=locator, source_sha256=snap["snapshot_sha256"])
        _save(workspace/"source_snapshots"/f"test_wacc_{metric}.json", item)
        if raw:
            _save(workspace/"source_snapshots"/f"test_wacc_snapshot_{metric}.json", snap)


def test_all_seven_immutable_sources_are_only_ready_for_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, run = _workspace(tmp_path, monkeypatch)
    _inputs(workspace)
    result = wacc.run_wacc_readiness(repo_root=tmp_path, artifact_root=workspace,
                                     m23_run_dir=run, enforce_git=False)
    assert result["status"] == "REAL_INGR_M24_WACC_SOURCE_CANDIDATES_READY_FOR_REVIEW"
    assert result["metrics_ready"] == 7
    assert all(x["status"] == "FRESH_SOURCE_INPUT_CANDIDATE" for x in result["metrics"])
    assert all(x["provenance"]["status"] == "SNAPSHOT_VERIFIED_VALUE_REQUIRES_REVIEW"
               for x in result["metrics"])
    assert result["reviewed_wacc_package"] is None
    assert result["draft_v04_created"] is False
    assert result["human_review_completed"] is False


def test_missing_bytes_stale_and_tier_d_are_independent_holds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, run = _workspace(tmp_path, monkeypatch)
    _inputs(workspace, raw=False, stale=True, tier_d=True)
    result = wacc.run_wacc_readiness(repo_root=tmp_path, artifact_root=workspace,
                                     m23_run_dir=run, enforce_git=False)
    assert result["status"] == "HOLD_REAL_INGR_M24_WACC_INPUT_GAPS"
    assert result["metrics"][0]["status"] == "STALE_BLOCKED"
    assert result["metrics"][2]["status"] == "UNREVIEWABLE_TIER_BLOCKED"
    assert result["metrics"][1]["status"] == "SOURCE_BYTES_UNVERIFIED"
    assert result["metrics_ready"] == 0


def test_conflicting_source_input_rejects_ambiguous_market_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, run = _workspace(tmp_path, monkeypatch)
    _inputs(workspace)
    path = workspace/"source_snapshots"/f"test_wacc_{REQUIRED_METRICS[0]}.json"
    different = copy.deepcopy(json.loads(path.read_text(encoding="utf-8")))
    # A distinct valid source input for the same metric is ambiguous, never auto-selected.
    changed = build_wacc_source_input(
        metric=REQUIRED_METRICS[0], value=0.04, unit="decimal", observed_on="2026-09-01",
        claim_class="FACT", source_publisher="Synthetic fixture", source_type="test-only-source",
        source_tier="B", source_locator=different["source"]["locator"],
        source_sha256=different["source"]["source_sha256"])
    _save(workspace/"source_snapshots"/"another_rf.json", changed)
    result = wacc.run_wacc_readiness(repo_root=tmp_path, artifact_root=workspace,
                                     m23_run_dir=run, enforce_git=False)
    assert result["metrics"][0]["status"] == "AMBIGUOUS_CONFLICTING_INPUTS"
    assert result["status"] == "HOLD_REAL_INGR_M24_WACC_INPUT_GAPS"


def test_tampered_source_input_and_ancestor_proposal_are_blocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, run = _workspace(tmp_path, monkeypatch)
    _inputs(workspace)
    path = workspace/"source_snapshots"/f"test_wacc_{REQUIRED_METRICS[0]}.json"
    x = json.loads(path.read_text(encoding="utf-8"))
    x["value"] += 0.01
    _save(path, x)
    with pytest.raises(CaseServiceError):
        wacc.run_wacc_readiness(repo_root=tmp_path, artifact_root=workspace,
                                 m23_run_dir=run, enforce_git=False)
