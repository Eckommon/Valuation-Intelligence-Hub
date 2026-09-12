"""M22 CLI/Web calculate-only interface contracts."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from valuation_hub import cli_entry
from valuation_hub.sec_live import TransportResponse, capture_companyfacts_snapshot
from valuation_hub.valuation_shares import extract_sec_current_common_shares_candidate, normalize_current_common_shares_candidate
from valuation_hub.web_valuation_shares import render_share_bridge_lab


def _digest(value: dict, field: str) -> str:
    payload = copy.deepcopy(value); payload.pop(field, None)
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _snapshot() -> dict:
    payload = {"cik":1234567,"entityName":"CLI Share Fixture","facts":{"dei":{"EntityCommonStockSharesOutstanding":{"units":{"shares":[{"end":"2026-08-01","val":1000,"accn":"0001234567-26-000040","form":"10-Q","filed":"2026-08-05","frame":"CY2026Q2I"}]}}}}}
    body = json.dumps(payload,separators=(",", ":")).encode()
    def transport(locator:str,*,user_agent:str)->TransportResponse:
        return TransportResponse(status=200,content_type="application/json",body=body,final_locator=locator)
    return capture_companyfacts_snapshot("1234567",user_agent="Valuation-Intelligence-Hub test@example.com",transport=transport,fetched_at="2026-09-12T11:30:00+00:00")


def _reviewed_observation() -> dict:
    candidate = extract_sec_current_common_shares_candidate(_snapshot(),period_end="2026-08-01",form="10-Q")
    candidate["class"] = "FACT"
    candidate["candidate_sha256"] = _digest(candidate,"candidate_sha256")
    return normalize_current_common_shares_candidate(candidate)


def test_cli_dispatch_exposes_m22_commands() -> None:
    commands = (
        "share-sec-extract","share-normalize","share-observation-validate",
        "share-base-context-build","share-base-context-validate",
        "share-adjustment-build","share-adjustment-validate",
        "share-coverage-assertion-build","share-coverage-assertion-validate",
        "share-bridge-build","share-bridge-validate",
    )
    for command in commands:
        assert cli_entry._command([command]) == command


def test_cli_base_only_bridge_round_trip(tmp_path:Path,capsys) -> None:
    observation = _reviewed_observation(); op = tmp_path/"observation.json"; op.write_text(json.dumps(observation))
    assert cli_entry.main(["share-base-context-build",str(op),"--as-of","2026-09-12","--max-age-days","180"]) == 0
    context = json.loads(capsys.readouterr().out); cp = tmp_path/"context.json"; cp.write_text(json.dumps(context))
    assert context["freshness"]["status"] == "FRESH"
    assert context["semantic_boundary"]["direct_bind_to_diluted_shares"] is False
    assert cli_entry.main(["share-base-context-validate",str(cp)]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "PASS_VALUATION_SHARE_BASE_CONTEXT_VALIDATION"

    ap = tmp_path/"adjustments.json"; ap.write_text("[]")
    assert cli_entry.main(["share-bridge-build",str(cp),str(ap)]) == 0
    bridge = json.loads(capsys.readouterr().out); bp = tmp_path/"bridge.json"; bp.write_text(json.dumps(bridge))
    assert bridge["coverage"]["status"] == "BASE_ONLY"
    assert bridge["candidate_fully_diluted_shares"] == 1000
    assert bridge["binding_eligibility"]["eligible_for_future_direct_bind"] is False
    assert cli_entry.main(["share-bridge-validate",str(bp)]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "PASS_DILUTED_SHARE_BRIDGE_VALIDATION"


def test_cli_adjustment_build_is_candidate_not_reviewed_fact(tmp_path:Path,capsys) -> None:
    assert cli_entry.main([
        "share-adjustment-build","--adjustment-id","RSU-1","--category","rsu_restricted_stock",
        "--shares","50","--source-sha256","a"*64,"--source-description","Explicit RSU candidate evidence",
    ]) == 0
    adjustment = json.loads(capsys.readouterr().out); path = tmp_path/"adjustment.json"; path.write_text(json.dumps(adjustment))
    assert adjustment["class"] == "NORMALIZED_FACT_CANDIDATE"
    assert adjustment["semantic_boundary"]["historical_factor_generated"] is False
    assert cli_entry.main(["share-adjustment-validate",str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "PASS_DILUTION_ADJUSTMENT_VALIDATION"


def test_web_share_bridge_lab_is_calculate_only() -> None:
    page = render_share_bridge_lab()
    assert "CURRENT SHARES ≠ FULLY DILUTED · NO MISSING-AS-ZERO · CALCULATE ONLY" in page
    assert "BASE_ONLY" in page and "PARTIAL_DILUTION_COVERAGE" in page
    assert "/api/shares/bridge-build" in page
    assert "/api/shares/file-write" not in page
    assert "/api/shares/canonical" not in page
    assert "NO DRAFT WRITE · NO CANONICAL WRITE" in page
