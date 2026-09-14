from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_binding import MATERIAL_FIELDS
from valuation_hub.forecast_draft_binding import FORECAST_FIELDS
from valuation_hub.real_case_readiness import (
    AWAITING_DEPENDENCY,
    AWAITING_HUMAN_REVIEW,
    AWAITING_REAL_SOURCE,
    BLOCKED,
    READY,
    build_real_equity_readiness_manifest,
    validate_real_equity_readiness_manifest,
)
from valuation_hub.terminal_growth_assumption import REQUIRED_ANCHORS
from valuation_hub.wacc_assumption import REQUIRED_METRICS


def _fixture_module():
    path = Path(__file__).with_name("test_m30b_real_case_preflight_v2.py")
    spec = importlib.util.spec_from_file_location("_m30b_readiness_fixture", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _manifest(preflight=None):
    return build_real_equity_readiness_manifest(
        case_id="US_INGR_INGREDION",
        legal_name="Ingredion Incorporated",
        ticker="INGR",
        exchange="NYSE",
        cik="0001046257",
        financial_period_end="2026-06-30",
        valuation_as_of="2026-09-14",
        form="10-Q",
        preflight=preflight,
    )


def _reseal(value: dict) -> None:
    unsigned = copy.deepcopy(value)
    unsigned.pop("manifest_sha256", None)
    value["manifest_sha256"] = hashlib.sha256(
        json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def test_no_preflight_produces_exact_13_field_fail_closed_plan() -> None:
    manifest = _manifest()
    checked = validate_real_equity_readiness_manifest(manifest)
    assert checked["material_field_count"] == 13
    assert [item["field"] for item in manifest["fields"]] == list(MATERIAL_FIELDS)
    assert manifest["source_preflight"] is None
    assert {item["code"] for item in manifest["blockers"]} == {"REAL_SEC_PREFLIGHT_NOT_SUPPLIED"}
    by_field = {item["field"]: item for item in manifest["fields"]}
    assert by_field["market_price"]["state"] == AWAITING_REAL_SOURCE
    assert by_field["equity.cash"]["state"] == AWAITING_REAL_SOURCE
    assert by_field["equity.debt"]["state"] == AWAITING_REAL_SOURCE
    assert by_field["scenario.wacc"]["state"] == AWAITING_REAL_SOURCE
    assert by_field["scenario.terminal_growth"]["state"] == AWAITING_DEPENDENCY
    assert all(by_field[field]["state"] == AWAITING_DEPENDENCY for field in FORECAST_FIELDS)
    assert "CAPTURE_REAL_M13_SEC_COMPANYFACTS" in manifest["next_actions"]
    assert manifest["human_review_boundary"]["automatic_approval_forbidden"] is True
    assert manifest["human_review_boundary"]["canonical_write"] is False


def test_dag_explicitly_models_m24_m25_m26_prerequisites() -> None:
    manifest = _manifest()
    nodes = {item["node_id"]: item for item in manifest["prerequisite_dag"]}
    wacc_source_ids = {f"m24.wacc.source.{metric}" for metric in REQUIRED_METRICS}
    assert wacc_source_ids.issubset(nodes)
    assert set(nodes["m24.wacc.candidate"]["dependencies"]) == wacc_source_ids
    anchor_ids = {f"m25.terminal_growth.anchor.{anchor}" for anchor in REQUIRED_ANCHORS}
    assert anchor_ids.issubset(nodes)
    assert set(nodes["m25.terminal_growth.candidate"]["dependencies"]) == anchor_ids | {"m24.wacc.reviewed_package"}
    assert nodes["m26.forecast.candidate"]["state"] == AWAITING_HUMAN_REVIEW
    forecast_fields = [item for item in manifest["fields"] if item["field"] in FORECAST_FIELDS]
    assert len(forecast_fields) == 6
    assert {item["prerequisite_node"] for item in forecast_fields} == {"m26.forecast.reviewed_package"}


def test_valid_m30b_preflight_projects_candidates_only_to_human_review(tmp_path: Path) -> None:
    f = _fixture_module()
    preflight = f._build(f._repo(tmp_path), f._snapshot())
    manifest = _manifest(preflight)
    checked = validate_real_equity_readiness_manifest(manifest)
    assert checked["material_field_count"] == 13
    nodes = {item["node_id"]: item for item in manifest["prerequisite_dag"]}
    assert nodes["m13.sec.companyfacts_snapshot"]["state"] == READY
    assert nodes["m30b.real_source_preflight"]["state"] == READY
    by_field = {item["field"]: item for item in manifest["fields"]}
    for field in ("equity.cash", "equity.diluted_shares", "equity.debt", "equity.minority_interest"):
        assert by_field[field]["state"] == AWAITING_HUMAN_REVIEW
    assert by_field["market_price"]["state"] == AWAITING_REAL_SOURCE
    assert "PERFORM_M30P1_DEBT_SEMANTIC_REVIEW" in manifest["next_actions"]
    assert manifest["source_preflight_projection"]["successor_debt_candidate_available"] is True


def test_missing_exact_debt_propagates_source_blocker_without_fake_review_readiness(tmp_path: Path) -> None:
    f = _fixture_module()
    preflight = f._build(f._repo(tmp_path), f._snapshot(include_debt=False))
    manifest = _manifest(preflight)
    by_field = {item["field"]: item for item in manifest["fields"]}
    assert by_field["equity.debt"]["state"] == AWAITING_REAL_SOURCE
    assert "SEC_EXACT_AGGREGATE_DEBT_UNAVAILABLE" in {item["code"] for item in manifest["blockers"]}
    assert "PERFORM_M30P1_DEBT_SEMANTIC_REVIEW" not in manifest["next_actions"]
    validate_real_equity_readiness_manifest(manifest)


def test_registry_collision_blocks_every_material_field(tmp_path: Path) -> None:
    f = _fixture_module()
    preflight = f._build(f._repo(tmp_path, collision=True), f._snapshot())
    manifest = _manifest(preflight)
    assert {item["state"] for item in manifest["fields"]} == {BLOCKED}
    assert manifest["next_actions"] == ["RESOLVE_REGISTRY_CASE_ID_COLLISION"]
    validate_real_equity_readiness_manifest(manifest)


def test_unknown_dag_dependency_is_rejected_even_after_outer_reseal() -> None:
    manifest = _manifest()
    tampered = copy.deepcopy(manifest)
    tampered["prerequisite_dag"][0]["dependencies"] = ["unknown.node"]
    _reseal(tampered)
    with pytest.raises(CaseServiceError, match="unknown dependency|미등록 dependency"):
        validate_real_equity_readiness_manifest(tampered)


def test_dag_cycle_is_rejected_even_after_outer_reseal() -> None:
    manifest = _manifest()
    tampered = copy.deepcopy(manifest)
    by_id = {item["node_id"]: item for item in tampered["prerequisite_dag"]}
    by_id["m13.sec.companyfacts_snapshot"]["dependencies"] = ["m30b.real_source_preflight"]
    _reseal(tampered)
    with pytest.raises(CaseServiceError, match="cycle|순환"):
        validate_real_equity_readiness_manifest(tampered)


def test_field_state_tamper_is_rejected_after_outer_reseal() -> None:
    manifest = _manifest()
    tampered = copy.deepcopy(manifest)
    tampered["fields"][0]["state"] = READY
    _reseal(tampered)
    with pytest.raises(CaseServiceError, match="deterministic reconstruction|결정론적 재구성"):
        validate_real_equity_readiness_manifest(tampered)
