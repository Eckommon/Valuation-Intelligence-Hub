"""M29 promotion-package → admission → guarded-plan integration."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from valuation_hub.admission import build_admission_bundle, validate_admission_bundle
from valuation_hub.admission_apply import build_repository_change_plan, validate_repository_change_plan
from valuation_hub.promotion_package import build_promotion_package, validate_promotion_package

ROOT = Path(__file__).resolve().parents[1]
CASE_ID = "M29_GOVERNED_EQUITY_HANDOFF_TEST"


def _m29_fixtures():
    path = Path(__file__).with_name("test_m29_complete_equity_handoff.py")
    spec = importlib.util.spec_from_file_location("_m29_package_fixture", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _package():
    _, candidate = _m29_fixtures()._approved_candidate()
    return build_promotion_package(
        candidate,
        case_id=CASE_ID,
        display_name_en="M29 Governed Equity Handoff Test",
        display_name_ko="M29 거버넌스 Equity 인계 테스트",
        asset_class="public_equity",
        root=ROOT,
    )


def test_v02_candidate_stages_through_existing_m10_package_contract() -> None:
    package = _package()
    checked = validate_promotion_package(package, ROOT)
    assert checked["valid"] is True
    assert checked["case_id"] == CASE_ID
    assert checked["source_model"] == "equity_fcff"
    reviewed = package["artifacts"]["reviewed_candidate.json"]
    assert reviewed["schema_version"] == "promotion-candidate-v0.2"
    assert package["artifacts"]["evidence_bundle.json"]["evidence"] == reviewed["evidence"]


def test_v02_package_builds_and_validates_existing_m11_admission_bundle() -> None:
    package = _package()
    bundle = build_admission_bundle(package, ROOT)
    checked = validate_admission_bundle(bundle, ROOT)
    assert checked["valid"] is True
    assert checked["case_id"] == CASE_ID
    assert bundle["target_path"] == f"analyses/equities/{CASE_ID}"
    assert bundle["artifacts"]["SOURCE_PACKAGE.json"] == package
    assert bundle["artifacts"]["evidence_reviewed.json"]["evidence"] == package["artifacts"]["reviewed_candidate.json"]["evidence"]


def test_v02_admission_bundle_reaches_existing_m12_deterministic_change_plan() -> None:
    package = _package()
    bundle = build_admission_bundle(package, ROOT)
    plan = build_repository_change_plan(bundle, ROOT)
    checked = validate_repository_change_plan(plan, bundle, ROOT)
    assert checked["valid"] is True
    assert checked["case_id"] == CASE_ID
    assert plan["source_admission_bundle_sha256"] == bundle["bundle_sha256"]
    assert plan["target_path"] == f"analyses/equities/{CASE_ID}"
    assert len(plan["artifact_writes"]) == 6
