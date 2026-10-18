"""M30-R8M24-RD.4: issuer-specific June 2026 Fitch BBB rating proof ONLY.

Licensed Fitch original research stays in ignored user-local files.
A verified BBB rating is NOT an observed INGR bond yield or WACC rate.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.external_source import (
    build_external_source_snapshot,materialize_external_source_snapshot,
    validate_external_source_snapshot,
)
from valuation_hub.ingr_wacc_damodaran_erp import _visible
from valuation_hub.ingr_r8_m23_execution import _git,_write

URL = "https://www.fitchratings.com/research/corporate-finance/fitch-affirms-ingredion-incorporated-idr-at-bbb-outlook-stable-08-06-2026"
SCHEMA = "ingr-fitch-20260608-bbb-issuer-rating-proof-v0.1"
RATED_ON = "2026-06-08"
AS_OF = "2026-09-14"


def _sha(obj:dict[str,Any],excluded:str)->str:
    v=copy.deepcopy(obj)
    v.pop(excluded,None)
    return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,
                      separators=(",",":"),allow_nan=False).encode()).hexdigest()


def extract_fitch_ingr_rating(raw:str)->dict[str,Any]:
    if not isinstance(raw,str) or len(raw.encode("utf-8"))>10_000_000:
        raise CaseServiceError("Fitch primary rating original HTML absent or oversized")
    t=_visible(raw)
    # Dated issuer rating action, not an unrelated BBB reference.
    source_patterns=(
        ("rating_heading",r"Fitch\s+Affirms\s+Ingredion\s+Incorporated['’]s\s+IDR\s+at\s+['‘’]BBB['‘’]\s*;\s*Outlook\s+Stable"),
        ("publication_date",r"Mon\s+08\s+Jun\s*,\s*2026"),
        ("announcement",r"Fitch\s+Ratings\s*-\s*Toronto\s*-\s*08\s+Jun\s+2026\s*:\s*Fitch\s+Ratings\s+has\s+affirmed\s+Ingredion\s+Incorporated['’]s\s+Long-Term\s+Issuer\s+Default\s+Rating\s*\(IDR\)\s+at\s+['‘’]BBB['‘’]"),
        ("short_rating",r"and\s+Short-Term\s+IDR\s+at\s+['‘’]F2['‘’]"),
        ("issuer_outlook",r"The\s+Rating\s+Outlook\s+is\s+Stable"),
        ("senior_unsecured",r"senior\s+unsecured\s+LT\s+BBB\s+Affirmed"),
        ("tate_lyle",r"Tate\s*(?:&|and)\s*Lyle"),
        ("acquisition_debt",r"(?:around|about)\s*\$?\s*4\s*\.\s*4\s+billion\s+of\s+incremental\s+debt"),
        ("future_closing",r"transaction\s+is\s+expected\s+to\s+close\s+in\s+the\s+second\s+half\s+of\s+2027"),
    )
    for name,pattern in source_patterns:
        if not re.search(pattern,t,re.I):
            raise CaseServiceError(f"Fitch 2026 Ingredion issuer rating {name} not source-proven")
    # Do not infer this 2026 issuer's current rating from the separate
    # planned 2027 combination's projected new financing.
    return {
        "entity_id":"SEC_CIK:0001046257",
        "issuer":"Ingredion Incorporated",
        "rating_agency":"Fitch Ratings",
        "rating_action_date":RATED_ON,
        "valuation_as_of":AS_OF,
        "issuer_long_term_idr":"BBB",
        "senior_unsecured_long_term":"BBB",
        "issuer_short_term_idr":"F2",
        "outlook":"Stable",
        "credit_grade_bbb_asof_dated_rating_action_observed":True,
        "rating_not_bond_ytm":True,
        "historical_intervening_rating_changes_excluded_by_this_source_alone":False,
        "planned_2027_tate_lyle_financing_is_future":True,
        "planned_incremental_debt_usd_billions_from_agency_case":4.4,
        "issued_refinancing_20260914_market_yield_observed":False,
        "credit_grade_compatible_with_bbb_index_but_tenor_not_proven":True,
        "wacc_debt_source_input_created":False,
        "reviewed_wacc_package":None,
        "human_review_completed":False,
        "status":"HOLD_FITCH_BBB_RATING_VERIFIED_INDEX_TO_ISSUER_COST_UNADJUDICATED",
    }


def _projection(snapshot:dict[str,Any])->dict[str,Any]:
    validate_external_source_snapshot(snapshot)
    if snapshot["source"]["locator"]!=URL or snapshot["source"]["tier"]!="A":
        raise CaseServiceError("Fitch original official rating source URL/tier mismatch")
    method=extract_fitch_ingr_rating(snapshot["raw_text"])
    p={"schema_version":SCHEMA,"canonical":False,
       "status":"SOURCE_BOUND_INGR_FITCH_BBB_RATING_NOT_ISSUER_BOND_YIELD",
       "method":method,
       "source_snapshot_sha256":snapshot["snapshot_sha256"],
       "source_body_sha256":snapshot["body"]["sha256"],
       "wacc_debt_source_input_created":False,
       "human_review_completed":False,
       "proof_sha256":""}
    p["proof_sha256"]=_sha(p,"proof_sha256")
    return p


def validate_fitch_rating(proof:dict[str,Any],snapshot:dict[str,Any])->dict[str,Any]:
    if not isinstance(proof,dict) or proof.get("schema_version")!=SCHEMA:
        raise CaseServiceError("Fitch 2026 rating proof absent or wrong schema")
    if proof!=_projection(snapshot):
        raise CaseServiceError("Fitch original BBB rating / date / method SHA invalid")
    return {"status":"PASS_REAL_FITCH_BBB_2026_RATING_INGR_RD_ASSUMPTION_HOLD",
            "proof_sha256":proof["proof_sha256"],
            "wacc_debt_source_input_created":False,
            "human_review_completed":False}


def materialize_fitch_rating(repo:Path,raw_path:Path)->dict[str,Any]:
    repo=repo.resolve()
    base=(repo/"workspace"/"source_snapshots").resolve()
    original=raw_path.resolve()
    if not original.is_relative_to(base) or not original.is_file():
        raise CaseServiceError("Fitch licensed original HTML must remain user-local ignored source_snapshots")
    raw=original.read_text(encoding="utf-8-sig")
    method=extract_fitch_ingr_rating(raw)
    snap=build_external_source_snapshot(
        raw,source_publisher="Fitch Ratings - rating action commentary",
        source_type="2026_06_08_ingr_bbb_issuer_and_senior_unsecured_rating",
        source_tier="A",source_locator=URL,
        captured_at=datetime.now(timezone.utc).isoformat())
    proof=_projection(snap)
    tag=snap["body"]["sha256"][:16]
    origin=base/f"INGR_Fitch_BBB_20260608_{tag}_snapshot.json"
    dest=base/f"INGR_Fitch_BBB_20260608_{tag}_proof.json"
    if origin.exists() or dest.exists():
        raise CaseServiceError("Fitch original rating already captured; refuse overwrite")
    materialize_external_source_snapshot(snap,origin,root=repo)
    _write(dest,proof)
    return {
        "status":"REAL_FITCH_INGR_BBB_ISSUER_SENIOR_UNSECURED_RATING_CAPTURED_RD_HOLD",
        "canonical":False,
        "issuer_long_term_idr":method["issuer_long_term_idr"],
        "senior_unsecured_long_term":method["senior_unsecured_long_term"],
        "rating_action_date":RATED_ON,
        "original_body_sha256":snap["body"]["sha256"],
        "snapshot_sha256":snap["snapshot_sha256"],
        "proof_sha256":proof["proof_sha256"],
        "snapshot_path":str(origin),"proof_path":str(dest),
        "wacc_debt_source_input_created":False,
        "human_review_completed":False,
        "next_action":"SOURCE_BIND_BBB_INDEX_TO_INGR_MATURITY_AND_2026_2027_REFINANCING_SCENARIO",
    }


def main(argv:list[str]|None=None)->int:
    p=argparse.ArgumentParser(description="Fitch 2026 original BBB rating, no borrower market yield")
    p.add_argument("--repo-root",type=Path,default=Path.cwd())
    p.add_argument("--raw",type=Path,required=True)
    p.add_argument("--json",action="store_true")
    a=p.parse_args(argv)
    try:
        repo=a.repo_root.resolve()
        _git(repo)
        path=a.raw if a.raw.is_absolute() else repo/a.raw
        out=materialize_fitch_rating(repo,path)
    except (CaseServiceError,OSError,ValueError,TypeError,KeyError) as exc:
        out={"status":"ERROR","error":str(exc)}
    print(json.dumps(out,sort_keys=True,indent=2,ensure_ascii=False))
    return int(out["status"]=="ERROR")


if __name__=="__main__":
    raise SystemExit(main())
