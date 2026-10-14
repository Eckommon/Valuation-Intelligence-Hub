"""M30-R8 route-aware share class and promotion regression tests (synthetic-only)."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

from valuation_hub.ai_dilution_authority import (
    ABSENT_SUPPORTED, BLOCKED_DEPENDENCY, PRESENT, EXPLICIT_COUNT_METHOD, build_ai_dilution_inventory,
)
from valuation_hub.case_service import CaseServiceError
from valuation_hub.dilution_envelope_source import build_source_bound_dilution_envelope_manifest
from valuation_hub.disclosure_limited_dilution import (
    ROLE_ANCHOR, ROLE_SUBSEQUENT, build_disclosure_limited_dilution_evidence,
    build_disclosure_limited_dilution_adjudication, finalize_disclosure_limited_dilution_assumption,
)
from valuation_hub.external_source import build_external_source_snapshot
from valuation_hub.share_dilution import derive_historical_dilution
from valuation_hub.valuation_shares import build_valuation_share_base_context
from valuation_hub.r8_assumption_proof import build_r6_binding_proof, validate_r6_binding_proof
from valuation_hub.r8_assumption_proposal import (
    build_r6_v3_proposal, build_assumption_proposal, validate_assumption_proposal,
)
from valuation_hub.r8_assumption_approval import build_assumption_approval
from valuation_hub.r8_draft_kernel import apply_approval, validate_bound_result
from valuation_hub.wacc_draft_binding import build_binding_proposal_with_wacc
from valuation_hub.terminal_growth_draft_binding import build_binding_proposal_with_terminal_growth
from valuation_hub.forecast_draft_binding import build_binding_proposal_with_forecast
from valuation_hub.market_price_draft_binding import build_binding_proposal_with_market_price
from valuation_hub.minority_interest_draft_binding import build_binding_proposal_with_minority_interest
from valuation_hub.promotion_m29 import (
    build_evidence_catalog_claim, build_complete_equity_candidate, validate_candidate_v2,
)
from valuation_hub.draft_binding import MATERIAL_FIELDS


def _test_module(name):
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location("_r8_" + name.replace(".py", ""), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(x, field):
    z = copy.deepcopy(x)
    z.pop(field, None)
    return hashlib.sha256(json.dumps(z, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _row(category, state, seed, **kw):
    x = dict(category=category, state=state,
             sources=[{"locator":f"https://www.sec.gov/example/{seed}", "snapshot_sha256":seed*64,
                       "source_type":"issuer_filing_snapshot"}],
             evidence_basis="TEST FIXTURE evidence only for " + category,
             contradiction_search={"performed":True,"summary":"Synthetic fixture contradiction search clean.",
                                   "material_contradictions":[]},
             dependencies=kw.get("dependencies", []), adjustment_id=kw.get("adjustment_id"),
             adjustment_shares=kw.get("adjustment_shares"), calculation_method=kw.get("calculation_method"),
             calculation_inputs=kw.get("calculation_inputs"))
    return x


def _observed(metric, value, entity):
    period = {"kind":"DURATION_QUARTER", "start":"2026-04-01", "end":"2026-06-30",
              "duration_days":91, "fiscal_year":2026, "fiscal_period":"Q2",
              "fiscal_quarter":2, "report_stage":"Q2", "date_precision":"EXACT"}
    result = {
        "schema_version":"share-dilution-observation-v0.1",
        "status":"SHARE_DILUTION_OBSERVATION_NORMALIZED", "canonical":False,
        "class":"NORMALIZED_FACT", "metric":metric,"value":value,"unit":"shares",
        "entity":copy.deepcopy(entity),"period":period,
        "lineage":{"normalization_rule":"SEC_WEIGHTED_AVERAGE_SHARE_DURATION_V01",
                   "source_candidate_sha256":"a"*64, "source_snapshot_sha256":"b"*64,
                   "source_body_sha256":"c"*64},
        "observation_sha256":"",
    }
    result["observation_sha256"] = _sha(result, "observation_sha256")
    return result


def _proof():
    base_tests = _test_module("test_m29_complete_equity_handoff.py")
    base = build_valuation_share_base_context(base_tests._share_observation(), as_of=base_tests.AS_OF)
    inventory = build_ai_dilution_inventory(base, [
        _row("options_treasury_stock_method", BLOCKED_DEPENDENCY, "a",
             dependencies=["complete_option_strike_distribution_for_valuation_date_tsm"]),
        _row("rsu_restricted_stock", PRESENT, "b", adjustment_id="R8-TEST-RSU",
             adjustment_shares=25, calculation_method=EXPLICIT_COUNT_METHOD,
             calculation_inputs={"explicit_share_count":25}),
        _row("warrants", ABSENT_SUPPORTED, "c"),
        _row("convertibles_if_converted", ABSENT_SUPPORTED, "d"),
        _row("contingent_shares", BLOCKED_DEPENDENCY, "e", dependencies=["no_complete_psu_payout_count"]),
        _row("other_explicit", BLOCKED_DEPENDENCY, "f", dependencies=["no_complete_deferred_equity_count"]),
    ])
    historical = derive_historical_dilution(
        _observed("weighted_average_basic_shares", 1000, base["entity"]),
        _observed("weighted_average_diluted_shares", 1030, base["entity"]),
    )
    anchor = build_external_source_snapshot(
        "<html><body><p>Total 35</p></body></html>",
        source_publisher="SEC", source_type="issuer_filing_snapshot", source_tier="A",
        source_locator="https://www.sec.gov/test/r8-anchor", captured_at="2026-09-12T09:00:00+09:00")
    grant = build_external_source_snapshot(
        "<html><body><p>Granted 4</p></body></html>",
        source_publisher="SEC", source_type="issuer_filing_snapshot", source_tier="A",
        source_locator="https://www.sec.gov/test/r8-grant", captured_at="2026-09-12T09:00:00+09:00")
    specs = [
        {"component_id":"TEST_ANCHOR", "role":ROLE_ANCHOR, "shares":35, "as_of":"2025-12-31",
         "evidence_basis":"Test source table exactly says Total 35", "calculation":None,
         "source_bindings":[{"snapshot_sha256":anchor["snapshot_sha256"],
                             "evidence_excerpt":"Total 35","observed_quantity":35,"unit_multiplier":1}]},
        {"component_id":"TEST_GRANTS", "role":ROLE_SUBSEQUENT, "shares":4, "as_of":"2026-06-30",
         "evidence_basis":"Test source explicitly says Granted 4", "calculation":None,
         "source_bindings":[{"snapshot_sha256":grant["snapshot_sha256"],
                             "evidence_excerpt":"Granted 4","observed_quantity":4,"unit_multiplier":1}]},
    ]
    manifest = build_source_bound_dilution_envelope_manifest(specs, [anchor, grant])
    evidence = build_disclosure_limited_dilution_evidence(base, inventory, historical, manifest["components"],
              as_of=base_tests.AS_OF, materiality_threshold=.05, max_historical_age_days=180)
    adjudication = build_disclosure_limited_dilution_adjudication(
        evidence, base, inventory, historical, manifest["components"],
        adjudicated_at="2026-09-12T10:00:00+09:00")
    package = finalize_disclosure_limited_dilution_assumption(
        evidence, adjudication, base, inventory, historical, manifest["components"])
    return build_r6_binding_proof(package, base, inventory, historical, manifest)


def _bound():
    m29 = _test_module("test_m29_complete_equity_handoff.py")
    m25, m26, m27, m28 = (m29._m25_fixtures(),m29._m26_fixtures(),
                           m29._m27_fixtures(),m29._m28_fixtures())
    from valuation_hub.debt_draft_binding import build_binding_proposal_with_debt
    v02 = build_binding_proposal_with_debt([m26._cash()], m29._debt_context(),
                                           as_of=m29.AS_OF, max_age_days=550)
    proof = _proof()
    v03 = build_r6_v3_proposal(v02, proof)
    v04 = build_binding_proposal_with_wacc(v03, m26._wacc_package(["BASE"]))
    v05 = build_binding_proposal_with_terminal_growth(v04, m25._terminal_package(
          scenarios=["BASE"],wacc_package=m26._wacc_package(["BASE"])))
    v06 = build_binding_proposal_with_forecast(v05, m26._forecast_package(["BASE"]))
    v07 = build_binding_proposal_with_market_price(v06, m27._package())
    v08 = build_binding_proposal_with_minority_interest(v07, m28._minority_package())
    v09 = build_assumption_proposal(v08, proof)
    draft = m26._draft(["BASE"])
    approval = build_assumption_approval(v09,draft,reviewer="R8 synthetic reviewer",
         target_entity_id=m29.ENTITY,target_financial_scope=m29.SCOPE,
         approved_fields=list(MATERIAL_FIELDS),approved_at="2026-09-12T18:30:00+09:00")
    result = apply_approval(v09,draft,approval)
    return proof,v03,v09,result


def test_r8_real_shape_source_proof_and_end_to_end_m29_assumption_authority():
    proof,v03,v09,result = _bound()
    assert validate_r6_binding_proof(proof)["status"]=="PASS_R8_R6_PROOF"
    assert v03["share_route"]=="R6_DISCLOSURE_LIMITED_ASSUMPTION"
    assert result["draft_after"]["equity"]["diluted_shares"] == 1030
    assert validate_bound_result(result)["share_class"]=="ASSUMPTION"
    observed = ("market_price","equity.cash","equity.minority_interest","equity.debt")
    catalog = [build_evidence_catalog_claim(result,field=field,claim_id="R8-"+field,
              metric=field,publisher="Test source",locator="https://www.sec.gov/r8-test",
              tier="A") for field in observed]
    candidate=build_complete_equity_candidate(result,catalog)
    checked=validate_candidate_v2(candidate)
    assert checked["evidence_count"]==4
    by={x["path"]:x for x in candidate["input_governance"]}
    assert by["equity.diluted_shares"]["class"]=="ASSUMPTION"
    assert by["equity.diluted_shares"]["claim_ids"]==[]
    assert by["equity.debt"]["class"]=="DERIVED"


def test_r8_rejects_exact_m22_relabeling_and_tampering():
    proof,v03,v09,result = _bound()
    tampered=copy.deepcopy(proof)
    tampered["package"]["class"]="DERIVED_FACT"
    with pytest.raises((CaseServiceError,KeyError,TypeError)):
        validate_r6_binding_proof(tampered)
    tampered=copy.deepcopy(v09)
    next(r for r in tampered["draft_input_matrix"] if r["field"]=="equity.diluted_shares")["source_class"]="DERIVED_FACT"
    with pytest.raises(CaseServiceError):
        validate_assumption_proposal(tampered)
    tampered=copy.deepcopy(result)
    tampered["draft_after"]["equity"]["diluted_shares"]=999
    with pytest.raises(CaseServiceError):
        validate_bound_result(tampered)
    m29=_test_module("test_m29_complete_equity_handoff.py")
    exact,_=m29._proposal_and_draft()
    with pytest.raises(CaseServiceError):
        build_assumption_proposal(exact,proof)
    with pytest.raises(CaseServiceError):
        build_evidence_catalog_claim(result,field="equity.diluted_shares",
          claim_id="R8-ILLEGAL",metric="fully_diluted_shares",
          publisher="Synthetic",locator="https://www.sec.gov/test",tier="A")
