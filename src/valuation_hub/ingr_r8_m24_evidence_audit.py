"""M30-R8M24-AUDIT.1 — real source-provenance audit without network access.

Cross-validate immutable user-local SEC 2026 bond inventory and 2025
tax bridge against original snapshots, then consume the existing M24
readiness preflight. Report nonpromoting blockers and case scenarios.

Never convert historical bond coupon/ETR or unlicensed market index
comparison into an issuer yield, WACC marginal rate, reviewed package,
draft, real-case admission or a human approval.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timezone
from pathlib import Path
import json
import math
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.external_source import load_external_source_snapshot
from valuation_hub.ingr_r8_m23_execution import CASE_ID,AS_OF,_write
from valuation_hub.ingr_r8_m24_readiness import run_wacc_readiness
from valuation_hub.ingr_wacc_debt_bond_terms import (
    REQUIRED_ORIGINAL_SHA256 as BOND_BODY_SHA,
    validate_sec_debt_inventory_proof,
)
from valuation_hub.ingr_wacc_tax_bridge_10k import validate_2025_tax_bridge

SCHEMA="ingr-r8m24-offline-evidence-boundary-audit-v0.1"
TAX_BODY_SHA="f932b04e0bf99ad80ea19326b724d553368cac6c6dad2ab64c1512154cd1aa1b"
BOND_PROOF_SHA="6158a891e2cc91d1466672c92a24c9141af2fe180a8735869b3cbe97b6f48997"
TAX_PROOF_SHA="c3d83e6a3c59236b1a18c1fc5cd3fa513605d6de0cf0c81c6131c291593a5594"
BOND_SNAPSHOT="INGR_Q2_debt_market_value_bb03a79c2ab28987_snapshot.json"
BOND_PROOF="INGR_Q2_bond_terms_bb03a79c2ab28987_proof.json"
TAX_SNAPSHOT="INGR_2025_tax_reconcile_f932b04e0bf99ad8_snapshot.json"
TAX_PROOF="INGR_2025_tax_reconcile_f932b04e0bf99ad8_proof.json"


def _locked_json(path:Path,base:Path)->dict[str,Any]:
    p=path.resolve()
    if path.is_symlink() or not p.is_relative_to(base.resolve()) or not p.is_file():
        raise CaseServiceError("original method context path is missing or outside ignored workspace")
    try:
        value=json.loads(p.read_text(encoding="utf-8"))
    except (ValueError,OSError,UnicodeError) as exc:
        raise CaseServiceError("original method context JSON invalid") from exc
    if not isinstance(value,dict):
        raise CaseServiceError("original method proof is not an object")
    return value


def validate_local_context(repo:Path)->dict[str,Any]:
    base=(repo.resolve()/"workspace"/"source_snapshots").resolve()
    if not base.is_dir():
        raise CaseServiceError("real user-local source_snapshots missing")
    source_bond=base/BOND_SNAPSHOT
    source_tax=base/TAX_SNAPSHOT
    if any(p.is_symlink() or not p.is_file() for p in (source_bond,source_tax)):
        raise CaseServiceError("real original SEC bond or tax source snapshot absent")
    bond=load_external_source_snapshot(source_bond)
    tax=load_external_source_snapshot(source_tax)
    if bond["body"]["sha256"]!=BOND_BODY_SHA or tax["body"]["sha256"]!=TAX_BODY_SHA:
        raise CaseServiceError("original SEC body differs from exact real local source")
    bond_proof=_locked_json(base/BOND_PROOF,base)
    tax_proof=_locked_json(base/TAX_PROOF,base)
    if bond_proof.get("proof_sha256")!=BOND_PROOF_SHA:
        raise CaseServiceError("real 2026 Q2 SEC bond inventory proof SHA changed")
    if tax_proof.get("proof_sha256")!=TAX_PROOF_SHA:
        raise CaseServiceError("real 2025 SEC tax bridge proof SHA changed")
    bond_checked=validate_sec_debt_inventory_proof(bond_proof,bond)
    tax_checked=validate_2025_tax_bridge(tax_proof,tax)
    if bond_checked["wacc_debt_input_created"] or tax_checked["wacc_tax_source_input_created"]:
        raise CaseServiceError("non-promoting contexts falsely claim a WACC rate")
    return {
        "status":"VERIFIED_SEC_TWO_CONTEXT_PROOFS_NO_RATE_INPUT",
        "bond_2026_q2":{
            "original_body_sha256":bond["body"]["sha256"],
            "snapshot_sha256":bond["snapshot_sha256"],
            "inventory_proof_sha256":bond_proof["proof_sha256"],
            "notes_verified":bond_checked["bond_count"],
            "long_term_debt_carrying_usd_millions":1742,
            "pre_tax_cost_of_debt_input_created":False,
        },
        "tax_2025_10k":{
            "original_body_sha256":tax["body"]["sha256"],
            "snapshot_sha256":tax["snapshot_sha256"],
            "tax_method_proof_sha256":tax_proof["proof_sha256"],
            "us_federal_2025_statutory_percent":21.0,
            "worldwide_2025_accounting_etr_percent":24.4,
            "wacc_marginal_cash_tax_input_created":False,
        },
    }


def assess_nonpromoting_gates(readiness:dict[str,Any],
                             context:dict[str,Any])->dict[str,Any]:
    if (readiness.get("as_of")!=AS_OF
        or readiness.get("entity_id")!="SEC_CIK:0001046257"
        or readiness.get("financial_scope")!="AS_REPORTED"
        or readiness.get("currency")!="USD"
        or readiness.get("canonical") is not False
        or readiness.get("human_review_completed") is not False
        or readiness.get("draft_v04_created") is not False
        or readiness.get("reviewed_wacc_package") is not None
        or context.get("status")!="VERIFIED_SEC_TWO_CONTEXT_PROOFS_NO_RATE_INPUT"):
        raise CaseServiceError("WACC audit authority/as-of/original-context mismatch")
    metrics=readiness.get("metrics")
    if not isinstance(metrics,list) or len(metrics)!=7:
        raise CaseServiceError("WACC audit metrics expected exactly seven")
    if any(not isinstance(x,dict) for x in metrics):
        raise CaseServiceError("invalid WACC metric record")
    m={x.get("metric"):x for x in metrics}
    if len(m)!=7:
        raise CaseServiceError("duplicate or invalid WACC metrics")
    if sum(x.get("status")=="FRESH_SOURCE_INPUT_CANDIDATE" for x in metrics)!=readiness.get("metrics_ready"):
        raise CaseServiceError("WACC readiness source count contradicted")
    debt=m.get("pre_tax_cost_of_debt",{})
    tax=m.get("tax_rate",{})
    # This *particular* audit is tailored to the user-verified 5/7
    # source stage; a genuinely new 6/7 or 7/7 stage requires a
    # new governed run, not a hidden continuation of this audit.
    if (readiness.get("metrics_ready")!=5
        or debt.get("status")!="MISSING_SOURCE_INPUT"
        or tax.get("status")!="MISSING_SOURCE_INPUT"
        or any(m.get(key,{}).get("status")!="FRESH_SOURCE_INPUT_CANDIDATE"
               for key in ("risk_free_rate","equity_risk_premium",
                           "levered_beta","equity_market_value","debt_market_value"))):
        raise CaseServiceError("audit source-stage contract changed; rerun governed readiness")
    erp=m["equity_risk_premium"]["provenance"]["erp_method"]
    beta=m["levered_beta"]["provenance"]["beta_method"]
    market_cap=m["equity_market_value"]["provenance"]["market_cap_method"]
    debt_mv=m["debt_market_value"]["provenance"]["debt_mv_method"]
    if (erp.get("historical_availability_asof_proven") is not False
        or erp.get("author_reference_rf")!=0.0475
        or erp.get("valuation_rf")!=0.0497
        or beta.get("historical_availability_asof_proven") is not False
        or beta.get("return_basis")!="PRICE_ONLY_NOT_TOTAL_RETURN"
        or beta.get("provider")!="Yahoo v8 chart original JSON"
        or beta.get("weekly_returns")!=157
        or beta.get("proof_sha256")!="1f53a9bb6758c4d7718e5f650a62bb2b0e459ce4dde4df85a16a999b03fbbf91"
        or not math.isclose(beta.get("beta",float("nan")),0.342231910459605,rel_tol=0,abs_tol=1e-12)
        or not math.isclose(beta.get("r_squared",float("nan")),0.07067663798658909,rel_tol=0,abs_tol=1e-12)
        or market_cap.get("share_class")!="ASSUMPTION"
        or debt_mv.get("source_class")!="ASSUMPTION"):
        raise CaseServiceError("real 5/7 beta, ERP or capital-source risk profile changed")
    return {
        "schema_version":SCHEMA,
        "status":"PASS_ORIGINAL_CONTEXT_AUDIT_AND_HOLD_TWO_WACC_RATE_INPUTS",
        "canonical":False,
        "as_of":AS_OF,
        "entity_id":"SEC_CIK:0001046257",
        "basis":"AS_REPORTED",
        "current_source_candidates":5,
        "required_source_candidates":7,
        "verified_context":context,
        "candidate_sha256":{k:m[k]["input_sha256"]
                            for k in ("risk_free_rate","equity_risk_premium",
                                      "levered_beta","equity_market_value","debt_market_value")},
        "unresolved_rate_inputs":["pre_tax_cost_of_debt","tax_rate"],
        "blocking_evidence_gates":[
            {"metric":"pre_tax_cost_of_debt",
             "status":"HOLD_NO_DATED_INGR_MARKET_YIELD_OR_GOVERNED_TERM_MATCHED_PROXY",
             "verified_bond_terms_not_bond_yield":True,
             "due_october_2026_refinancing_requires_separate_treatment":True,
             "tate_lyle_2027_future_debt_not_as_reported_debt":True,
             "original_fred_ice_index_not_attested_by_this_audit":True,
             "original_fitch_rating_not_attested_by_this_audit":True},
            {"metric":"tax_rate",
             "status":"HOLD_INCREMENTAL_JURISDICTIONAL_CASH_INTEREST_SHIELD_UNPROVEN",
             "historical_us_statutory_not_global_marginal_rate":True,
             "historical_global_etr_not_cash_marginal_rate":True,
             "deductibility_163j_and_foreign_limits_not_attested":True},
        ],
        "candidate_quality_warnings":{
            "beta_weak_r_squared":beta["r_squared"],
            "beta_price_only_not_total_return":True,
            "beta_asof_data_availability_unproven":True,
            "erp_october_retrospective_asof_unproven":True,
            "erp_author_vs_valuation_rf_difference_basis_points":22,
            "equity_market_value_lagged_shares_unreviewed":True,
            "debt_market_value_long_term_level2_plus_short_term_proxy_unreviewed":True,
        },
        "scenario_boundaries":[
            {"scenario":"2026_09_14_STANDALONE_AS_REPORTED",
             "funded_debt_source":"SEC_2026_Q2_CARRYING_AND_LEVEL2_UNREVIEWED_PROXY",
             "bond_2030_2037_2050_and_oct_2026_refinancing":True,
             "issuer_yield_selected":None,"marginal_tax_selected":None},
            {"scenario":"FUTURE_2027_TATE_LYLE_COMBINATION",
             "state":"SEPARATE_FORECAST_NOT_2026_AS_REPORTED_FACT",
             "financing_terms_and_valuation_scenario_verified":False,
             "issuer_yield_selected":None,"marginal_tax_selected":None},
        ],
        "wacc_pre_tax_rate_selected":None,
        "wacc_marginal_tax_rate_selected":None,
        "reviewed_wacc_package":None,
        "human_review_completed":False,
        "draft_v04_created":False,
        "real_case_admitted":False,
        "next_action":"SECURE_DATE_ALIGNED_COMPANY_DEBT_TERM_YIELD_AND_INCREMENTAL_CASH_TAX_POLICY",
    }


def run_offline_context_audit(repo_root:Path,*,enforce_git:bool=True)->dict[str,Any]:
    repo=repo_root.resolve()
    readiness=run_wacc_readiness(repo_root=repo,enforce_git=enforce_git)
    if readiness["status"]!="HOLD_REAL_INGR_M24_WACC_INPUT_GAPS":
        raise CaseServiceError("context audit requires original missing-rate WACC HOLD")
    context=validate_local_context(repo)
    report=assess_nonpromoting_gates(readiness,context)
    report["git"]=readiness["git"]
    report["source_readiness_path"]=readiness["output"]
    target=(repo/"workspace"/"execution_artifacts"/CASE_ID/
            ("r8_m24_offline_audit_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))/
            "evidence_boundary_audit.json")
    _write(target,report)
    return {**report,"output":str(target)}


def main(argv:list[str]|None=None)->int:
    p=argparse.ArgumentParser(description="Offline immutable SEC+M24 evidence boundary audit; no rate approval")
    p.add_argument("--repo-root",type=Path,default=Path.cwd())
    p.add_argument("--json",action="store_true")
    a=p.parse_args(argv)
    try:
        result=run_offline_context_audit(a.repo_root)
    except (CaseServiceError,OSError,ValueError,KeyError,TypeError) as exc:
        result={"status":"ERROR","error":str(exc)}
    print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))
    return int(result["status"]=="ERROR")


if __name__=="__main__":
    raise SystemExit(main())
