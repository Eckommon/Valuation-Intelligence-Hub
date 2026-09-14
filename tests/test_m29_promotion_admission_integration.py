"""M29 promotion-package → admission → guarded-plan integration."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from valuation_hub.admission_apply_m29 import build_repository_change_plan, validate_repository_change_plan
from valuation_hub.admission_m29 import build_admission_bundle, validate_admission_bundle
from valuation_hub.binding_apply_m28 import apply_binding_approval, build_binding_approval
from valuation_hub.debt_draft_binding import build_binding_proposal_with_debt
from valuation_hub.draft_binding import MATERIAL_FIELDS
from valuation_hub.draft_service import validate_draft
from valuation_hub.forecast_draft_binding import build_binding_proposal_with_forecast
from valuation_hub.market_price_draft_binding import build_binding_proposal_with_market_price
from valuation_hub.minority_interest_draft_binding import build_binding_proposal_with_minority_interest
from valuation_hub.promotion_m29 import build_complete_equity_candidate, review_scope_sha256
from valuation_hub.promotion_package import build_promotion_package, validate_promotion_package
from valuation_hub.share_draft_binding import build_binding_proposal_with_diluted_shares
from valuation_hub.terminal_growth_draft_binding import build_binding_proposal_with_terminal_growth
from valuation_hub.wacc_draft_binding import build_binding_proposal_with_wacc

ROOT = Path(__file__).resolve().parents[1]
CASE_ID = "M29_GOVERNED_EQUITY_HANDOFF_TEST"
SCENARIOS = ["BEAR", "BASE", "BULL"]


def _m29_fixtures():
    path = Path(__file__).with_name("test_m29_complete_equity_handoff.py")
    spec = importlib.util.spec_from_file_location("_m29_package_fixture", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_profile_candidate():
    f = _m29_fixtures()
    m25 = f._m25_fixtures()
    m26 = f._m26_fixtures()
    m27 = f._m27_fixtures()
    m28 = f._m28_fixtures()

    v02 = build_binding_proposal_with_debt([m26._cash()], f._debt_context(), as_of=f.AS_OF, max_age_days=550)
    v03 = build_binding_proposal_with_diluted_shares(v02, f._eligible_share_bridge())
    wacc = m26._wacc_package(SCENARIOS)
    v04 = build_binding_proposal_with_wacc(v03, wacc)
    terminal = m25._terminal_package(scenarios=SCENARIOS, wacc_package=wacc)
    v05 = build_binding_proposal_with_terminal_growth(v04, terminal)
    v06 = build_binding_proposal_with_forecast(v05, m26._forecast_package(SCENARIOS))
    v07 = build_binding_proposal_with_market_price(v06, m27._package())
    v08 = build_binding_proposal_with_minority_interest(v07, m28._minority_package())
    assert v08["completeness"]["direct_bind_count"] == len(MATERIAL_FIELDS)
    assert v08["completeness"]["unresolved_count"] == 0

    draft = m26._draft(SCENARIOS)
    approval = build_binding_approval(
        v08,
        draft,
        reviewer="M29 canonical-profile reviewer",
        target_entity_id=f.ENTITY,
        target_financial_scope=f.SCOPE,
        approved_fields=list(MATERIAL_FIELDS),
        approved_at="2026-09-13T19:10:00+09:00",
    )
    result = apply_binding_approval(v08, draft, approval)
    candidate = build_complete_equity_candidate(result, f._catalog(result))
    candidate["review"] = {
        "decision": "APPROVE",
        "reviewer": "M29 promotion reviewer",
        "reviewed_at": "2026-09-13T19:20:00+09:00",
        "rationale": "Reviewed complete BEAR/BASE/BULL governed handoff for canonical-admission compatibility.",
        "scope_sha256": review_scope_sha256(candidate),
    }
    return candidate


def _package():
    return build_promotion_package(
        _canonical_profile_candidate(),
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
    assert set(reviewed["draft"]["equity"]["scenarios"]) == set(SCENARIOS)
    assert package["artifacts"]["evidence_bundle.json"]["evidence"] == reviewed["evidence"]


def test_v02_package_builds_and_validates_existing_m11_admission_bundle() -> None:
    package = _package()
    source_candidate = package["artifacts"]["reviewed_candidate.json"]
    bundle = build_admission_bundle(package, ROOT)
    checked = validate_admission_bundle(bundle, ROOT)
    assert checked["valid"] is True
    assert checked["case_id"] == CASE_ID
    assert bundle["target_path"] == f"analyses/equities/{CASE_ID}"
    assert bundle["artifacts"]["SOURCE_PACKAGE.json"] == package
    assert bundle["artifacts"]["SOURCE_PACKAGE.json"]["artifacts"]["reviewed_candidate.json"]["draft"] == source_candidate["draft"]
    assert bundle["artifacts"]["case_inputs.json"]["reviewed_draft"] == validate_draft(source_candidate["draft"])
    assert bundle["artifacts"]["evidence_reviewed.json"]["claims"] == source_candidate["evidence"]
    assert bundle["artifacts"]["evidence_reviewed.json"]["input_governance"] == source_candidate["input_governance"]


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
