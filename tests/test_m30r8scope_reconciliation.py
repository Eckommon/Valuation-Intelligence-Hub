"""M30-R8SCOPE: synthetic source-bound Q2 reconciliation and M23 chain tests.

The fixture is synthetic, never treated as real Ingredion source authority. Exact
real snapshot SHA is patched ONLY in tests; production constants remain locked.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import pytest

from valuation_hub import ingr_r8_m23_execution as local
from valuation_hub import sec_scope_reconciliation_r8 as scope
from valuation_hub.case_service import CaseServiceError
from valuation_hub.external_source import build_external_source_snapshot
from valuation_hub.sec_scope_debt_binding_r8 import (
    build_scope_bridged_debt_proposal, validate_scope_bridged_debt_proposal,
)
from valuation_hub.r8_assumption_proposal import validate_r6_v3_proposal

SYNTHETIC_HTML = """
<html><body>
<h1>Ingredion Incorporated</h1>
<h2>Condensed Consolidated Balance Sheets</h2>
<p>June 30, 2026 December 31, 2025 (Unaudited)</p>
<table><tr><td>Cash and cash equivalents</td><td>$</td><td>948</td><td>$</td><td>1,030</td></tr></table>
<h2>Notes to the Condensed Consolidated Financial Statements</h2>
<h3>6. Financing Arrangements</h3>
<table>
<tr><td>Total long-term debt</td><td>1,742</td><td>1,742</td></tr>
<tr><td>Total short-term borrowings</td><td>41</td><td>48</td></tr>
<tr><td>Total debt</td><td>$</td><td>1,783</td><td>$</td><td>1,790</td></tr>
</table></body></html>
"""


def _fixture(name: str):
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location("_m30scope_"+name.replace(".py", ""), path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")


def _context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    r8l = _fixture("test_m30r8l_ingr_m23_execution.py")
    r3 = _fixture("test_m30r3_sec_observed_ai_authority.py")
    workspace, proof, _, _, _ = r8l._real_shape(tmp_path, monkeypatch)
    # Use real-shaped AI adjudicated current cash and debt, not fabricated human status.
    (workspace / "source_snapshots" / "synthetic_cash.json").unlink()
    _, debt = r8l._ai_debt_in_workspace(workspace, monkeypatch)
    candidate, raw_cash = r3._pair(r3.FIELD_CASH)
    evidence = r3._evidence(r3.FIELD_CASH, candidate, raw_cash)
    adjudication = r3._adjudication(r3.FIELD_CASH, candidate, raw_cash, evidence)
    cash = r3.build_ai_reviewed_cash_observation(candidate, raw_cash, adjudication, evidence)
    _write(workspace / "source_snapshots" / "ai_cash.json", cash)
    monkeypatch.setattr(local, "CASH_SHA", cash["observation_sha256"])
    monkeypatch.setattr(scope, "CASH_SHA", cash["observation_sha256"])
    monkeypatch.setattr(scope, "DEBT_SHA", debt["context_sha256"])
    monkeypatch.setattr(scope, "R8_SHA", proof["proof_sha256"])
    q2 = build_external_source_snapshot(
        SYNTHETIC_HTML, source_publisher="SEC",
        source_type="issuer_filing_snapshot", source_tier="A",
        source_locator=scope.LOCATOR, captured_at="2026-09-14T12:00:00+09:00",
    )
    _write(workspace / "source_snapshots" / "synthetic_q2_scope_snapshot.json", q2)
    monkeypatch.setattr(scope, "SOURCE_SHA", q2["snapshot_sha256"])
    monkeypatch.setattr(local, "SCOPE_SOURCE_SHA", q2["snapshot_sha256"])
    return workspace, proof, cash, debt, q2


def test_scope_reconciliation_preserves_original_classes_and_m23_real_shape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, proof, cash, debt, q2 = _context(tmp_path, monkeypatch)
    result = local.run_real_m23(repo_root=tmp_path, artifact_root=workspace, enforce_git=False)
    assert result["status"] == "REAL_INGR_M23_R6_ASSUMPTION_READY"
    assert result["source_financial_scopes"] == {
        "cash": "AS_REPORTED", "r6_shares": "AS_REPORTED", "sec_aggregate_debt": "CFS"
    }
    assert result["scope_bridge_sha256"]
    run_dir = Path(result["run_dir"])
    bridge = json.loads((run_dir / "r8_sec_scope_bridge.json").read_text(encoding="utf-8"))
    v02 = json.loads((run_dir / "m23_sec_debt_base_v02.json").read_text(encoding="utf-8"))
    v03 = json.loads((run_dir / "m23_r6_assumption_v03.json").read_text(encoding="utf-8"))
    assert scope.validate_scope_bridge(bridge)["status"] == "PASS_INGR_2026Q2_SCOPE_BRIDGE"
    assert validate_scope_bridged_debt_proposal(v02)["source_debt_scope"] == "CFS"
    assert validate_r6_v3_proposal(v03)["source_class"] == "ASSUMPTION"
    assert v02["identity"]["financial_scope"] == "AS_REPORTED"
    assert v02["debt_binding_context"] == debt
    assert v02["base_v01_proposal"]["baseline_context"]["cash"]["entity"]["financial_scope"] == "AS_REPORTED"
    assert v03["baseline_context"]["fully_diluted_shares"]["class"] == "ASSUMPTION"
    assert bridge["cash"] == cash and bridge["source_snapshot"] == q2
    assert bridge["r8_proof"] == proof


def test_exact_sealed_q2_issuer_metadata_alias_does_not_override_source_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, proof, cash, debt, _ = _context(tmp_path, monkeypatch)
    # SEC source identity derives from the immutable full snapshot SHA, Tier-A,
    # filing URL, the source body and the matching accession; a descriptive
    # publisher/source_type is not an extra signed SEC filing identifier.
    aliased = build_external_source_snapshot(
        SYNTHETIC_HTML, source_publisher="Ingredion Incorporated",
        source_type="inline_xbrl_document", source_tier="A",
        source_locator=scope.LOCATOR, captured_at="2026-09-14T12:00:00+09:00",
    )
    monkeypatch.setattr(scope, "SOURCE_SHA", aliased["snapshot_sha256"])
    checked = scope.build_scope_bridge(cash, debt, proof, aliased)
    assert scope.validate_scope_bridge(checked)["status"] == "PASS_INGR_2026Q2_SCOPE_BRIDGE"
    assert checked["source_snapshot"] == aliased
    assert checked["source_snapshot_sha256"] == aliased["snapshot_sha256"]


def test_even_sealed_snapshot_rejects_wrong_locator_or_untrusted_tier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, proof, cash, debt, _ = _context(tmp_path, monkeypatch)
    for tier, locator, failure in (
        ("B", scope.LOCATOR, "not Tier A"),
        ("A", "https://www.sec.gov/Archives/edgar/data/1046257/000162828026054722/other.htm", "locator"),
    ):
        wrong = build_external_source_snapshot(
            SYNTHETIC_HTML, source_publisher="Ingredion Incorporated",
            source_type="inline_xbrl_document", source_tier=tier,
            source_locator=locator, captured_at="2026-09-14T12:00:00+09:00",
        )
        monkeypatch.setattr(scope, "SOURCE_SHA", wrong["snapshot_sha256"])
        with pytest.raises(CaseServiceError, match=failure):
            scope.build_scope_bridge(cash, debt, proof, wrong)


def test_r8_source_snapshot_missing_is_need_not_fake_scope_approval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, *_ = _context(tmp_path, monkeypatch)
    (workspace / "source_snapshots" / "synthetic_q2_scope_snapshot.json").unlink()
    result = local.run_real_m23(repo_root=tmp_path, artifact_root=workspace, enforce_git=False)
    assert result["status"] == "NEED_SEC_SCOPE_SOURCE_SNAPSHOT"
    assert "m23_r6_v03_proposal_sha256" not in result


def test_scope_reconciliation_rejects_tampered_source_and_issuer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, proof, cash, debt, q2 = _context(tmp_path, monkeypatch)
    bad = copy.deepcopy(q2)
    bad["raw_text"] = bad["raw_text"].replace("1,783", "1,784")
    with pytest.raises(CaseServiceError):
        scope.build_scope_bridge(cash, debt, proof, bad)
    bad = copy.deepcopy(cash)
    bad["lineage"]["filing_identity"]["accession"] = "0001628280-26-000000"
    with pytest.raises(CaseServiceError):
        scope.build_scope_bridge(bad, debt, proof, q2)


def test_scope_bridged_proposal_rejects_scope_relabel_and_r6_class_upgrade(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, proof, cash, debt, q2 = _context(tmp_path, monkeypatch)
    bridge = scope.build_scope_bridge(cash, debt, proof, q2)
    proposal = build_scope_bridged_debt_proposal(bridge)
    altered = copy.deepcopy(proposal)
    altered["debt_binding_context"]["entity"]["financial_scope"] = "AS_REPORTED"
    with pytest.raises(CaseServiceError):
        validate_scope_bridged_debt_proposal(altered)
    altered = copy.deepcopy(bridge)
    altered["r8_proof"]["package"]["class"] = "DERIVED_FACT"
    with pytest.raises(CaseServiceError):
        scope.validate_scope_bridge(altered)


def test_scope_reconciliation_rejects_missing_cash_filing_ancestry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, proof, cash, debt, q2 = _context(tmp_path, monkeypatch)
    bad = copy.deepcopy(cash)
    bad["lineage"].pop("filing_identity")
    with pytest.raises(CaseServiceError):
        scope.build_scope_bridge(bad, debt, proof, q2)
