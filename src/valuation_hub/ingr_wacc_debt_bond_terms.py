"""M30-R8M24-RD.1: exact SEC debt inventory, NOT forward debt cost.

Reuse the user's validated existing original Q2 2026 SEC snapshot; extract
four contractual bond coupons/maturities/carrying amounts. No new 10-Q
download, no WACC pre-tax cost of debt, no yield invention or review.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.external_source import (
    load_external_source_snapshot, validate_external_source_snapshot,
)
from valuation_hub.ingr_wacc_damodaran_erp import _visible
from valuation_hub.ingr_wacc_debt_market_value import URL, _section, _row, _numbers
from valuation_hub.ingr_r8_m23_execution import _git, _write

SCHEMA = "ingr-sec-bond-maturity-inventory-proof-v0.1"
REQUIRED_ORIGINAL_SHA256 = "bb03a79c2ab289873e5cfe6cc299ba52d9659dda5594d224b6dce844a6bbf167"
OBSERVED_ON = "2026-06-30"
AS_OF = "2026-09-14"
NOTE_ROWS = (
    ("2.900", "June 1, 2030", "2030-06-01", (597,597)),
    ("3.200", "October 1, 2026", "2026-10-01", (500,499)),
    ("3.900", "June 1, 2050", "2050-06-01", (392,392)),
    ("6.625", "April 15, 2037", "2037-04-15", (253,253)),
)


def _sha(obj: dict[str,Any], key: str) -> str:
    payload = copy.deepcopy(obj)
    payload.pop(key,None)
    return hashlib.sha256(json.dumps(payload,sort_keys=True,
           ensure_ascii=False,separators=(",",":"),allow_nan=False).encode()).hexdigest()


def extract_sec_debt_inventory(raw: str) -> dict[str,Any]:
    text = _visible(raw)
    if not re.search(r"Ingredion\s+Incorporated",text,re.I):
        raise CaseServiceError("SEC issuer for bond inventory unverified")
    if not re.search(r"quarterly\s+period\s+ended\s+June\s+30,?\s+2026",text,re.I):
        raise CaseServiceError("SEC debt inventory Q2 period mismatch")
    if not re.search(r"dollars\s+in\s+millions",text,re.I):
        raise CaseServiceError("SEC debt inventory scale missing")
    note = _section(text,r"6\s*\.\s*Financing\s+Arrangements",
        r"7\s*\.\s*Pension\s+and\s+Other\s+Postretirement\s+Benefits","debt schedule")
    if not re.search(r"As\s+of\s+June\s+30,?\s+2026\s+As\s+of\s+December\s+31,?\s+2025",note,re.I):
        raise CaseServiceError("debt maturity schedule dated column heads missing")
    tranches: list[dict[str,Any]] = []
    locations = []
    for coupon,label,maturity,expected in NOTE_ROWS:
        # SEC Inline-XBRL markup can split percentage and date punctuation
        # into adjacent visible text nodes. Allow only node whitespace:
        # exact coupon digits and exact maturity remain mandatory.
        coupon_integer, decimals = coupon.split(".")
        coupon_text = rf"{coupon_integer}\s*\.\s*{decimals}\s*%"
        month_day, year = label.split(", ")
        month, day = month_day.rsplit(" ", 1)
        maturity_label = rf"{re.escape(month)}\s+{re.escape(day)}\s*,\s*{re.escape(year)}"
        pattern = rf"{coupon_text}\s+senior\s+notes\s+due\s+{maturity_label}"
        rows = list(re.finditer(pattern,note,re.I))
        if len(rows) != 1:
            raise CaseServiceError(f"INGR {coupon}% note/maturity missing or duplicate")
        locations.append(rows[0])
    for i,(coupon,label,maturity,expected) in enumerate(NOTE_ROWS):
        start=locations[i].end()
        end=locations[i+1].start() if i+1<len(locations) else note.find("Revolving credit agreement",start)
        if end <= start:
            raise CaseServiceError("SEC four senior-note term rows not contiguous")
        bounded = note[start:end].strip()
        if coupon == "3.200":
            # SEC explicitly marks the Oct-2026 refinancing note (i).
            # Accept only the documented footnote marker at this row,
            # not arbitrary narrative text mixed into numeric columns.
            if not re.match(r"^\(i\)\s+",bounded,re.I):
                raise CaseServiceError("2026 senior-note refinancing footnote marker absent")
            bounded = re.sub(r"^\(i\)\s+","",bounded, count=1, flags=re.I)
        amounts = _numbers(bounded,name=f"senior note {coupon}%")
        if amounts != list(expected):
            raise CaseServiceError(f"SEC note {coupon}% dated carrying amounts contradicted: {amounts}")
        tranches.append({
            "coupon_percent": float(coupon), "maturity": maturity,
            "carrying_june2026_usd_millions": expected[0],
            "carrying_dec2025_usd_millions": expected[1],
            "carrying_is_not_face_principal": True,
        })
    # Independently reconcile constituent non-note debt rows, not only
    # summary totals. This prevents a falsified short-term component from
    # passing while an unrelated printed total remains unchanged.
    table_end = note.find("_________________")
    if table_end < 0:
        raise CaseServiceError("SEC maturity table accounting footnote boundary absent")
    table = note[:table_end]
    for label, start, stop, expected in (
        ("other_long_term", r"Other\s+long-term\s+borrowings",
         r"Total\s+long-term\s+debt", [0,1]),
        ("other_short_term", r"Other\s+short-term\s+borrowings",
         r"Delayed\s+draw\s+term\s+loan\s+facility", [41,48]),
    ):
        component = _numbers(_row(table,start,stop,label),name=label)
        if component != expected:
            raise CaseServiceError(f"SEC {label} financing component contradicted")
    expected_sum = sum(x["carrying_june2026_usd_millions"] for x in tranches)
    if expected_sum != 1742:
        raise CaseServiceError("senior note sum not equal long-term debt carry")
    for name,pattern,next_label,values in (
        ("long_term",r"Total\s+long-term\s+debt",r"Other\s+short-term\s+borrowings",[1742,1742]),
        ("short_term",r"Total\s+short-term\s+borrowings",r"Total\s+debt",[41,48]),
        ("all_debt",r"Total\s+debt(?!\s+carrying)",r"_{3,}|\(i\)\s*The\s+senior",[1783,1790]),
    ):
        amounts = _numbers(_row(note,pattern,next_label,name),name=name)
        if amounts != values:
            raise CaseServiceError(f"SEC total {name} maturity reconciliation failed")
    for facility in ("Bridge","DDTL"):
        if not re.search(rf"No\s+amounts\s+were\s+outstanding\s+under\s+the\s+{facility}\s+Facility\s+as\s+of\s+June\s+30,?\s+2026",note,re.I):
            raise CaseServiceError(f"{facility} facility not proven undrawn")
    if not re.search(r"senior\s+notes\s+due\s+October\s+1,?\s+2026\s+are\s+classified\s+as\s+long-term\s+debt\s+as\s+we\s+have\s+the\s+intent\s+and\s+ability\s+to\s+refinance",note,re.I):
        raise CaseServiceError("2026 maturity's long-term reclassification unproven")
    return {
        "issuer":"Ingredion Incorporated", "entity_id":"SEC_CIK:0001046257",
        "period_end":OBSERVED_ON, "valuation_as_of":AS_OF,
        "fixed_note_carrying_total_usd_millions":1742,
        "short_term_carrying_usd_millions":41,
        "total_reported_debt_carrying_usd_millions":1783,
        "tranches":tranches,
        "short_term_2026_note_refinancing_classification":True,
        "pending_acquisition_bridge_and_ddtl_undrawn_at_period_end":True,
        "company_specific_bond_ytm_observed":False,
        "maturity_specific_market_bond_prices_observed":False,
        "aggregate_fair_value_not_individual_bond_fair_values":True,
        "historical_coupon_not_forward_cost_of_debt":True,
        "face_values_verified":False,
        "pretax_debt_rate_selected":None,
        "wacc_debt_input_created":False,
        "human_review_completed":False,
        "status":"HOLD_FORWARD_YIELD_CREDIT_CURVE_NOT_OBSERVED",
    }


def inspect_sec_bond_html(raw: str) -> dict[str, Any]:
    """Inspect actual bounded SEC text without creating any WACC artifact."""
    visible = _visible(raw)
    try:
        note = _section(visible,r"6\s*\.\s*Financing\s+Arrangements",
            r"7\s*\.\s*Pension\s+and\s+Other\s+Postretirement\s+Benefits","debt schedule")
    except CaseServiceError:
        note = ""
    matches = list(re.finditer(r"senior\s+notes\s+due",note,re.I))
    return {
        "status": "SEC_NOTE6_ORIGINAL_VISIBLE_DIAGNOSTIC_ONLY",
        "original_body_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "note6_bounded": bool(note),
        "senior_note_label_excerpts": [
            note[max(0,m.start()-35):m.end()+45] for m in matches[:8]
        ],
        "pretax_debt_rate_selected": None,
        "human_review_completed": False,
    }


def _projection(snapshot: dict[str,Any]) -> dict[str,Any]:
    validate_external_source_snapshot(snapshot)
    if (snapshot["source"]["locator"] != URL
        or snapshot["source"]["tier"] != "A"
        or snapshot["body"]["sha256"] != REQUIRED_ORIGINAL_SHA256):
        raise CaseServiceError("SEC exact user-verified 2026Q2 10-Q original SHA/URL mismatch")
    data = extract_sec_debt_inventory(snapshot["raw_text"])
    obj={
        "schema_version":SCHEMA,
        "canonical":False,
        "status":"SOURCE_BOUND_INGR_BOND_INVENTORY_NOT_FORWARD_YIELD",
        "method":data,
        "source_snapshot_sha256":snapshot["snapshot_sha256"],
        "source_body_sha256":snapshot["body"]["sha256"],
        "wacc_debt_input_created":False,
        "human_review_completed":False,
        "proof_sha256":"",
    }
    obj["proof_sha256"]=_sha(obj,"proof_sha256")
    return obj


def validate_sec_debt_inventory_proof(proof:dict[str,Any],snapshot:dict[str,Any])->dict[str,Any]:
    if not isinstance(proof,dict) or proof.get("schema_version")!=SCHEMA:
        raise CaseServiceError("SEC company-specific note inventory proof wrong schema")
    if proof!=_projection(snapshot):
        raise CaseServiceError("SEC note schedule/SHA or authority proof mismatch")
    return {"status":"PASS_BOND_INVENTORY_SOURCE_RECORDED_FORWARD_COST_HOLD",
            "proof_sha256":proof["proof_sha256"],"bond_count":len(proof["method"]["tranches"]),
            "wacc_debt_input_created":False,"human_review_completed":False}


def materialize_sec_debt_inventory(repo:Path,snapshot_path:Path)->dict[str,Any]:
    root=(repo.resolve()/"workspace"/"source_snapshots").resolve()
    path=snapshot_path.resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise CaseServiceError("SEC Q2 bond inventory requires prior immutable local snapshot")
    original=load_external_source_snapshot(path)
    proof=_projection(original)
    target=root/f"INGR_Q2_bond_terms_{REQUIRED_ORIGINAL_SHA256[:16]}_proof.json"
    if target.exists():
        raise CaseServiceError("SEC senior note inventory proof already exists; no overwrite")
    _write(target,proof)
    return {
        "status":"REAL_INGR_SEC_BOND_TERMS_CAPTURED_FORWARD_YIELD_HOLD",
        "canonical":False,
        "source_body_sha256":REQUIRED_ORIGINAL_SHA256,
        "source_snapshot_sha256":original["snapshot_sha256"],
        "proof_sha256":proof["proof_sha256"],
        "proof_path":str(target),
        "senior_note_count":len(proof["method"]["tranches"]),
        "total_long_term_debt_carry_usd_millions":1742,
        "pretax_debt_rate_selected":None,
        "wacc_debt_input_created":False,
        "human_review_completed":False,
        "next_action":"GATHER_2026_09_14_ISSUER_BOND_YTM_OR_TERM_MATCHED_CREDIT_SPREAD",
    }


def main(argv:list[str]|None=None)->int:
    p=argparse.ArgumentParser(description="SEC original immutable 2026Q2 bond terms; NOT WACC debt yield")
    p.add_argument("--repo-root",type=Path,default=Path.cwd())
    p.add_argument("--snapshot",required=True,type=Path)
    p.add_argument("--diagnose",action="store_true")
    p.add_argument("--json",action="store_true")
    args=p.parse_args(argv)
    try:
        repo=args.repo_root.resolve()
        _git(repo)
        raw=args.snapshot if args.snapshot.is_absolute() else repo/args.snapshot
        if args.diagnose:
            allowed = (repo/"workspace"/"source_snapshots").resolve()
            if not raw.resolve().is_relative_to(allowed):
                raise CaseServiceError("SEC debt diagnostic requires local original snapshot")
            snapshot = load_external_source_snapshot(raw)
            validate_external_source_snapshot(snapshot)
            if snapshot["body"]["sha256"] != REQUIRED_ORIGINAL_SHA256:
                raise CaseServiceError("SEC original body SHA mismatch")
            value = inspect_sec_bond_html(snapshot["raw_text"])
        else:
            value = materialize_sec_debt_inventory(repo,raw)
    except (CaseServiceError,OSError,KeyError,ValueError,TypeError) as exc:
        value={"status":"ERROR","error":str(exc)}
    print(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False))
    return int(value["status"]=="ERROR")


if __name__=="__main__":
    raise SystemExit(main())
