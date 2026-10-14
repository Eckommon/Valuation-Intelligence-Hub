"""M30-R8L real-shaped local Ingredion M23 execution regressions."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from valuation_hub import ingr_r8_m23_execution as local
from valuation_hub.case_service import CaseServiceError
from valuation_hub.debt_draft_binding_m30 import validate_binding_proposal_sec_aggregate
from valuation_hub.r8_assumption_proof import build_r6_binding_proof
from valuation_hub.r8_assumption_proposal import validate_r6_v3_proposal


def _fixture(name: str):
    source = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location("_r8l_" + name.replace(".py", ""), source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")


def _real_shape(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    r7 = _fixture("test_m30r7xl_local_ingr_execution.py")
    debt = _fixture("test_m30_sec_aggregate_debt_successor.py")
    workspace, raw = r7._prepare_workspace(tmp_path, monkeypatch)
    run = r7.runner.run_local_execution(
        repo_root=tmp_path, artifact_root=workspace, proxy_raw=raw, enforce_git=False
    )
    assert run["status"] == "REAL_INGR_R6_ASSUMPTION_APPROVED"
    result_dir = Path(run["run_dir"])
    package = json.loads((result_dir / "r6_package.json").read_text(encoding="utf-8"))
    base = json.loads((workspace / "inputs" / "base_context.json").read_text(encoding="utf-8"))
    inventory = json.loads((workspace / "inputs" / "r4_inventory.json").read_text(encoding="utf-8"))
    historical = json.loads((result_dir / "r7_package.json").read_text(encoding="utf-8"))
    manifest = json.loads((result_dir / "r7x_envelope_manifest.json").read_text(encoding="utf-8"))
    proof = build_r6_binding_proof(package, base, inventory, historical, manifest)
    _json(result_dir / "r8_binding_proof.json", proof)
    monkeypatch.setattr(local, "RUN_ID", result_dir.name)
    _, _, _, profile, context = debt._reviewed_debt()
    cash = debt._cash_observation()
    _json(workspace / "source_snapshots" / "synthetic_cash.json", cash)
    _json(workspace / "source_snapshots" / "synthetic_debt_context.json", context)
    _json(workspace / "source_snapshots" / "synthetic_debt_profile.json", profile)
    monkeypatch.setattr(local, "R8_PROOF_SHA", proof["proof_sha256"])
    monkeypatch.setattr(local, "R6_PACKAGE_SHA", package["package_sha256"])
    monkeypatch.setattr(local, "CASH_SHA", cash["observation_sha256"])
    monkeypatch.setattr(local, "DEBT_CONTEXT_SHA", context["context_sha256"])
    monkeypatch.setattr(local, "DEBT_PROFILE_SHA", profile["profile_sha256"])
    return workspace, proof, cash, profile, context


def test_real_shaped_m23_sec_debt_v02_and_r6_assumption_v03(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, proof, cash, profile, context = _real_shape(tmp_path, monkeypatch)
    result = local.run_real_m23(repo_root=tmp_path, artifact_root=workspace, enforce_git=False)
    assert result["status"] == "REAL_INGR_M23_R6_ASSUMPTION_READY"
    assert result["r8_proof_sha256"] == proof["proof_sha256"]
    assert result["fully_diluted_shares_assumption"] == 63_900_000
    assert result["fully_diluted_shares_source_class"] == "ASSUMPTION"
    assert result["cash_observation_sha256"] == cash["observation_sha256"]
    assert result["debt_context_sha256"] == context["context_sha256"]
    output = Path(result["run_dir"])
    v02 = json.loads((output / "m23_sec_debt_base_v02.json").read_text(encoding="utf-8"))
    v03 = json.loads((output / "m23_r6_assumption_v03.json").read_text(encoding="utf-8"))
    validate_binding_proposal_sec_aggregate(v02)
    validate_r6_v3_proposal(v03)
    assert v02["baseline_context"]["interest_bearing_debt"]["value"] == 1_783_000_000
    assert v03["baseline_context"]["fully_diluted_shares"]["value"] == 63_900_000
    assert v03["share_route"] == "R6_DISCLOSURE_LIMITED_ASSUMPTION"
    assert Path(result["run_dir"]).is_relative_to(tmp_path / "workspace")


def test_real_shaped_m23_rehydrates_only_from_reviewed_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, _, _, _, context = _real_shape(tmp_path, monkeypatch)
    (workspace / "source_snapshots" / "synthetic_debt_context.json").unlink()
    result = local.run_real_m23(repo_root=tmp_path, artifact_root=workspace, enforce_git=False)
    assert result["status"] == "REAL_INGR_M23_R6_ASSUMPTION_READY"
    assert result["debt_context_sha256"] == context["context_sha256"]
    assert (Path(result["run_dir"]) / "rehydrated_sec_debt_context.json").exists()


def test_real_shaped_m23_fails_closed_when_cash_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, _, _, _, _ = _real_shape(tmp_path, monkeypatch)
    (workspace / "source_snapshots" / "synthetic_cash.json").unlink()
    outcome = local.run_real_m23(repo_root=tmp_path, artifact_root=workspace, enforce_git=False)
    assert outcome["status"] == "NEED_REAL_M23_SOURCE_ARTIFACTS"
    assert outcome["missing"][0]["artifact"] == "reviewed_cash_observation"
    assert not list(workspace.glob("execution_artifacts/US_INGR_INGREDION/r8_m23_*/m23_r6_assumption_v03.json"))


def test_real_shaped_m23_fails_closed_when_debt_context_and_profile_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, _, _, _, _ = _real_shape(tmp_path, monkeypatch)
    for name in ("synthetic_debt_context.json", "synthetic_debt_profile.json"):
        (workspace / "source_snapshots" / name).unlink()
    outcome = local.run_real_m23(repo_root=tmp_path, artifact_root=workspace, enforce_git=False)
    assert outcome["status"] == "NEED_REAL_M23_SOURCE_ARTIFACTS"
    assert outcome["missing"][0]["artifact"] == "reviewed_sec_aggregate_debt_context_or_profile"


def test_real_shaped_m23_rejects_invalid_source_without_refabrication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, _, cash, _, _ = _real_shape(tmp_path, monkeypatch)
    altered = copy.deepcopy(cash)
    altered["value"] += 1
    _json(workspace / "source_snapshots" / "synthetic_cash.json", altered)
    with pytest.raises(CaseServiceError):
        local.run_real_m23(repo_root=tmp_path, artifact_root=workspace, enforce_git=False)
