"""M30-R8M24-RD.3: local-only licensed FRED/ICE BBB comparator proof.

The official BBB index yield is NOT an observed INGR bond yield and
must never create a WACC pre-tax cost of debt input or reviewed package.
ICE index material is licensed for internal use only; original stays
strictly user-local under gitignored source_snapshots.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.external_source import (
    build_external_source_snapshot, validate_external_source_snapshot,
    materialize_external_source_snapshot,
)
from valuation_hub.ingr_wacc_damodaran_erp import _visible
from valuation_hub.ingr_r8_m23_execution import _git, _write

URL = "https://fred.stlouisfed.org/data/BAMLC0A4CBBBEY"
SCHEMA = "ingr-fred-ice-bbb-market-benchmark-proof-v0.1"
SERIES = "BAMLC0A4CBBBEY"
OBSERVED_ON = "2026-09-14"
AS_OF = "2026-09-14"
INDEX_PERCENT = 5.90
PRIOR_DAY = "2026-09-11"
PRIOR_PERCENT = 5.89


def _sha(data: dict[str,Any], excluded: str) -> str:
    payload=copy.deepcopy(data)
    payload.pop(excluded,None)
    return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,
                         separators=(",",":"),allow_nan=False).encode()).hexdigest()


def extract_fred_bbb_comparator(raw: str)->dict[str,Any]:
    if not isinstance(raw,str) or len(raw.encode("utf-8"))>6_000_000:
        raise CaseServiceError("FRED original HTML body missing or oversized")
    visible=_visible(raw)
    # Require both provider and product identity, unlike a copied datum.
    for name,expr in (
        ("title",r"Table\s+Data\s*-\s*ICE\s+BofA\s+BBB\s+US\s+Corporate\s+Index\s+Effective\s+Yield"),
        ("series",r"Series\s+ID\s+BAMLC0A4CBBBEY\b"),
        ("publisher",r"Source\s+Ice\s+Data\s+Indices\s*,?\s*LLC\b"),
        ("unit",r"Units\s+Percent\b"),
        ("frequency",r"Frequency\s+Daily\s*,?\s*Close\b"),
        ("license",r"internal\s+use\s+only"),
    ):
        if not re.search(expr,visible,re.I):
            raise CaseServiceError(f"FRED/ICE BBB licensed series {name} unverified")
    matches=list(re.finditer(r"\bDATE\s+VALUE\b",visible,re.I))
    if len(matches)!=1:
        raise CaseServiceError("FRED/ICE dated observations table missing or duplicated")
    observations=visible[matches[0].end():]
    # Match all ISO day/value records from the actual FRED table, not page
    # navigation, metadata or content on another issuer/provider page.
    rows=list(re.finditer(
        r"(?<!\d)(20\d{2}-\d{2}-\d{2})\s+(\d+(?:\.\d+)?|\.)(?=\s|$)",
        observations))
    if len(rows)<200:
        raise CaseServiceError("FRED/ICE licensed daily table appears truncated")
    row_values:dict[str,float|None]={}
    for m in rows:
        day, value = m.group(1),m.group(2)
        if day in row_values:
            raise CaseServiceError("FRED/ICE dated observations duplicated")
        row_values[day]=None if value=="." else float(value)
    if row_values.get(OBSERVED_ON)!=INDEX_PERCENT:
        raise CaseServiceError("FRED 2026-09-14 BBB index original 5.90% missing or contradicted")
    if row_values.get(PRIOR_DAY)!=PRIOR_PERCENT:
        raise CaseServiceError("FRED 2026-09-11 BBB index prior day 5.89% missing or contradicted")
    if min(row_values)>"2025-09-14" or max(row_values)<OBSERVED_ON:
        raise CaseServiceError("FRED/ICE surrounding historical dates missing")
    return {
        "series_id":SERIES,
        "publisher":"ICE Data Indices LLC via FRED Federal Reserve Bank St. Louis",
        "metric":"BBB_US_CORPORATE_INDEX_EFFECTIVE_YIELD",
        "units":"percent_per_annum",
        "frequency":"daily_close",
        "valuation_as_of":AS_OF, "observed_on":OBSERVED_ON,
        "index_effective_yield_percent":INDEX_PERCENT,
        "previous_trading_day":PRIOR_DAY,
        "previous_trading_day_yield_percent":PRIOR_PERCENT,
        "source_is_licensed_ice_internal_use_only":True,
        "company_issuer_specific_bond_market_yield_observed":False,
        "ingr_credit_rating_asof_proven":False,
        "issuer_bond_tenor_and_duration_matched":False,
        "new_2026_10_note_refinancing_yield_observed":False,
        "asof_publication_time_verified":False,
        "input_class":"MARKET_COMPARATOR_NOT_WACC_SOURCE_INPUT",
        "pre_tax_cost_of_debt_wacc_input_created":False,
        "reviewed_wacc_package":None,
        "human_review_completed":False,
        "status":"HOLD_FRED_BBB_COMPARATOR_NOT_INGR_FORWARD_MARKET_DEBT_YIELD",
    }


def _projection(snapshot:dict[str,Any])->dict[str,Any]:
    validate_external_source_snapshot(snapshot)
    src=snapshot["source"]
    if src["locator"]!=URL or src["tier"]!="B":
        raise CaseServiceError("FRED/ICE BBB snapshot original issuer URL/tier mismatch")
    data=extract_fred_bbb_comparator(snapshot["raw_text"])
    proof={
        "schema_version":SCHEMA,"canonical":False,
        "status":"SOURCE_BOUND_ICE_BBB_MARKET_COMPARATOR_NO_INGR_WACC_COST_OF_DEBT",
        "method":data,
        "source_snapshot_sha256":snapshot["snapshot_sha256"],
        "source_body_sha256":snapshot["body"]["sha256"],
        "pre_tax_cost_of_debt_wacc_input_created":False,
        "human_review_completed":False,
        "proof_sha256":"",
    }
    proof["proof_sha256"]=_sha(proof,"proof_sha256")
    return proof


def validate_bbb_comparator(proof:dict[str,Any],snapshot:dict[str,Any])->dict[str,Any]:
    if not isinstance(proof,dict) or proof.get("schema_version")!=SCHEMA:
        raise CaseServiceError("FRED/ICE BBB comparator method proof absent")
    if proof!=_projection(snapshot):
        raise CaseServiceError("FRED/ICE original / index rate / authority SHA mismatch")
    return {"status":"PASS_FRED_BBB_MARKET_INDEX_CONTEXT_INGR_DEBT_YIELD_HOLD",
            "proof_sha256":proof["proof_sha256"],
            "pre_tax_cost_of_debt_wacc_input_created":False,
            "human_review_completed":False}


def materialize_bbb_comparator(repo:Path,raw_path:Path)->dict[str,Any]:
    root=(repo.resolve()/"workspace"/"source_snapshots").resolve()
    raw=raw_path.resolve()
    if not raw.is_relative_to(root) or not raw.is_file():
        raise CaseServiceError("FRED licensed original must stay in local ignored source_snapshots")
    text=raw.read_text(encoding="utf-8-sig")
    method=extract_fred_bbb_comparator(text)
    source=build_external_source_snapshot(
        text,source_publisher="FRED / ICE Data Indices LLC",
        source_type="licensed_bbb_us_corporate_effective_yield_market_comparator",
        source_tier="B",source_locator=URL,
        captured_at=datetime.now(timezone.utc).isoformat())
    proof=_projection(source)
    tag=source["body"]["sha256"][:16]
    target_source=root/f"INGR_FRED_BBB_index_comparator_{tag}_snapshot.json"
    target_proof=root/f"INGR_FRED_BBB_index_comparator_{tag}_proof.json"
    if target_source.exists() or target_proof.exists():
        raise CaseServiceError("same FRED licensed comparator body already captured; no overwrite")
    materialize_external_source_snapshot(source,target_source,root=repo)
    _write(target_proof,proof)
    return {
        "status":"REAL_20260914_BBB_INDEX_MARKET_COMPARATOR_CAPTURED_INGR_RD_HOLD",
        "canonical":False,
        "observed_on":OBSERVED_ON,
        "market_comparator_percent":method["index_effective_yield_percent"],
        "original_body_sha256":source["body"]["sha256"],
        "snapshot_sha256":source["snapshot_sha256"],
        "proof_sha256":proof["proof_sha256"],
        "snapshot_path":str(target_source),"proof_path":str(target_proof),
        "license":"INTERNAL_USE_ONLY_DO_NOT_PUBLISH_INDEX_DATA_SERIES",
        "company_rating_and_duration_match_proven":False,
        "pre_tax_cost_of_debt_wacc_input_created":False,
        "human_review_completed":False,
        "next_action":"SOURCE_ATTEST_INGR_CREDIT_GRADE_AND_DATED_ISSUER_YIELD_OR_GOVERNED_PROXY",
    }


def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description="FRED/ICE licensed BBB index original; issuer borrowing yield HOLD")
    parser.add_argument("--repo-root",type=Path,default=Path.cwd())
    parser.add_argument("--raw",type=Path,required=True)
    parser.add_argument("--json",action="store_true")
    args=parser.parse_args(argv)
    try:
        root=args.repo_root.resolve()
        _git(root)
        original=args.raw if args.raw.is_absolute() else root/args.raw
        result=materialize_bbb_comparator(root,original)
    except (CaseServiceError,OSError,ValueError,TypeError,KeyError) as exc:
        result={"status":"ERROR","error":str(exc)}
    print(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False))
    return int(result["status"]=="ERROR")


if __name__=="__main__":
    raise SystemExit(main())
