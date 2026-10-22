"""M30-R8M24-AUDIT.1: fail-closed offline original-context proof and 5/7 gates.

No artificial user production market prices, WACC rate, or review.
"""
from __future__ import annotations
import copy
import json
from pathlib import Path

import pytest

from valuation_hub import ingr_r8_m24_evidence_audit as audit
from valuation_hub.case_service import CaseServiceError


def _context():
    return {"status":"VERIFIED_SEC_TWO_CONTEXT_PROOFS_NO_RATE_INPUT",
            "bond_2026_q2":{"notes_verified":4},
            "tax_2025_10k":{"us_federal_2025_statutory_percent":21.0}}


def _readiness():
    metrics=[]
    for name in ("risk_free_rate","equity_risk_premium",
                 "levered_beta","pre_tax_cost_of_debt",
                 "equity_market_value","debt_market_value","tax_rate"):
        x={"metric":name,
           "status": ("MISSING_SOURCE_INPUT" if name in ("pre_tax_cost_of_debt","tax_rate")
                      else "FRESH_SOURCE_INPUT_CANDIDATE")}
        if x["status"]=="FRESH_SOURCE_INPUT_CANDIDATE":
            x["input_sha256"]="test-only-"+name
        if name=="equity_risk_premium":
            x["provenance"]={"erp_method":{
                "historical_availability_asof_proven":False,
                "author_reference_rf":.0475,"valuation_rf":.0497}}
        elif name=="levered_beta":
            x["provenance"]={"beta_method":{
                "historical_availability_asof_proven":False,
                "return_basis":"PRICE_ONLY_NOT_TOTAL_RETURN",
                "provider":"Yahoo v8 chart original JSON",
                "weekly_returns":157,"regression_beta":0.342231910459605,
                "beta":0.342231910459605,
                "r_squared":0.07067663798658909,
                "proof_sha256":"1f53a9bb6758c4d7718e5f650a62bb2b0e459ce4dde4df85a16a999b03fbbf91"}}
        elif name=="equity_market_value":
            x["provenance"]={"market_cap_method":{"share_class":"ASSUMPTION"}}
        elif name=="debt_market_value":
            x["provenance"]={"debt_mv_method":{"source_class":"ASSUMPTION"}}
        metrics.append(x)
    return {
        "as_of":"2026-09-14","entity_id":"SEC_CIK:0001046257",
        "financial_scope":"AS_REPORTED","currency":"USD",
        "canonical":False,"human_review_completed":False,
        "reviewed_wacc_package":None,"draft_v04_created":False,
        "metrics_ready":5,"metrics":metrics,
        "status":"HOLD_REAL_INGR_M24_WACC_INPUT_GAPS",
        "git":{"branch":"main","head":"test-only-main"},
        "output":"test-only-output",
    }


def test_five_of_seven_exact_gate_and_scenario_firewall():
    r=audit.assess_nonpromoting_gates(_readiness(),_context())
    assert r["status"]=="PASS_ORIGINAL_CONTEXT_AUDIT_AND_HOLD_TWO_WACC_RATE_INPUTS"
    assert r["current_source_candidates"]==5
    assert r["unresolved_rate_inputs"]==["pre_tax_cost_of_debt","tax_rate"]
    assert r["candidate_quality_warnings"]["erp_author_vs_valuation_rf_difference_basis_points"]==22
    assert r["candidate_quality_warnings"]["beta_weak_r_squared"]<.1
    assert r["blocking_evidence_gates"][0]["tate_lyle_2027_future_debt_not_as_reported_debt"] is True
    assert r["scenario_boundaries"][0]["issuer_yield_selected"] is None
    assert r["scenario_boundaries"][1]["financing_terms_and_valuation_scenario_verified"] is False
    assert r["wacc_pre_tax_rate_selected"] is None
    assert r["wacc_marginal_tax_rate_selected"] is None
    assert r["reviewed_wacc_package"] is None
    assert r["human_review_completed"] is False
    assert r["draft_v04_created"] is False
    assert r["real_case_admitted"] is False


@pytest.mark.parametrize("mutation",[
    lambda r:r.update(metrics_ready=6),
    lambda r:r.update(canonical=True),
    lambda r:r.update(human_review_completed=True),
    lambda r:r.update(reviewed_wacc_package={"fake":True}),
    lambda r:r.update(draft_v04_created=True),
    lambda r:r.update(as_of="2026-09-15"),
    lambda r:r["metrics"][3].update(status="FRESH_SOURCE_INPUT_CANDIDATE"),
    lambda r:r["metrics"][1]["provenance"]["erp_method"].update(historical_availability_asof_proven=True),
    lambda r:r["metrics"][2]["provenance"]["beta_method"].update(r_squared=0.31),
    lambda r:r["metrics"][2]["provenance"]["beta_method"].update(provider="Stooq original CSV"),
    lambda r:r["metrics"][4]["provenance"]["market_cap_method"].update(share_class="FACT"),
])
def test_method_input_quality_fails_closed_on_changed_stage_or_fake_authority(mutation):
    r=_readiness()
    mutation(r)
    with pytest.raises(CaseServiceError):
        audit.assess_nonpromoting_gates(r,_context())


def test_untrusted_original_context_rejected():
    r=_readiness()
    with pytest.raises(CaseServiceError):
        audit.assess_nonpromoting_gates(r,{"status":"MISSING"})
    r["metrics"].append(copy.deepcopy(r["metrics"][-1]))
    with pytest.raises(CaseServiceError):
        audit.assess_nonpromoting_gates(r,_context())


def test_locked_sec_originals_and_sha_proof_validation(tmp_path:Path,monkeypatch):
    base=tmp_path/"workspace"/"source_snapshots"
    base.mkdir(parents=True)
    for name in (audit.BOND_SNAPSHOT,audit.BOND_PROOF,
                 audit.TAX_SNAPSHOT,audit.TAX_PROOF):
        (base/name).write_text("{}",encoding="utf-8")
    (base/audit.BOND_PROOF).write_text(json.dumps({"proof_sha256":audit.BOND_PROOF_SHA}),encoding="utf-8")
    (base/audit.TAX_PROOF).write_text(json.dumps({"proof_sha256":audit.TAX_PROOF_SHA}),encoding="utf-8")
    def fake_load(path):
        if path.name==audit.BOND_SNAPSHOT:
            return {"body":{"sha256":audit.BOND_BODY_SHA},
                    "snapshot_sha256":"original-bond-snapshot-test"}
        return {"body":{"sha256":audit.TAX_BODY_SHA},
                "snapshot_sha256":"original-tax-snapshot-test"}
    def fake_bond(p,s):
        assert p["proof_sha256"]==audit.BOND_PROOF_SHA
        assert s["body"]["sha256"]==audit.BOND_BODY_SHA
        return {"wacc_debt_input_created":False,"bond_count":4}
    def fake_tax(p,s):
        assert p["proof_sha256"]==audit.TAX_PROOF_SHA
        assert s["body"]["sha256"]==audit.TAX_BODY_SHA
        return {"wacc_tax_source_input_created":False}
    monkeypatch.setattr(audit,"load_external_source_snapshot",fake_load)
    monkeypatch.setattr(audit,"validate_sec_debt_inventory_proof",fake_bond)
    monkeypatch.setattr(audit,"validate_2025_tax_bridge",fake_tax)
    result=audit.validate_local_context(tmp_path)
    assert result["status"]=="VERIFIED_SEC_TWO_CONTEXT_PROOFS_NO_RATE_INPUT"
    assert result["bond_2026_q2"]["pre_tax_cost_of_debt_input_created"] is False
    assert result["tax_2025_10k"]["wacc_marginal_cash_tax_input_created"] is False
    (base/audit.TAX_PROOF).write_text(json.dumps({"proof_sha256":"tampered"}),encoding="utf-8")
    with pytest.raises(CaseServiceError):
        audit.validate_local_context(tmp_path)


def test_offline_audit_no_external_fetch_and_local_only_artifact(tmp_path:Path,monkeypatch):
    rd=_readiness()
    monkeypatch.setattr(audit,"run_wacc_readiness",lambda **kwargs:rd)
    monkeypatch.setattr(audit,"validate_local_context",lambda repo:_context())
    result=audit.run_offline_context_audit(tmp_path,enforce_git=False)
    path=Path(result["output"])
    assert path.is_file()
    assert path.is_relative_to(tmp_path/"workspace"/"execution_artifacts")
    saved=json.loads(path.read_text(encoding="utf-8"))
    assert saved["canonical"] is False
    assert saved["reviewed_wacc_package"] is None
    assert saved["source_readiness_path"]=="test-only-output"
