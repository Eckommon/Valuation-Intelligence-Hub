"""M30-R8M24-BETA.Y: alternate original Yahoo Finance v8 chart JSON route.

The legacy Stooq CSV endpoint served a JavaScript verification page
on the user's actual Windows execution. This adapter never bypasses
that challenge, uses no credentials and does not relabel HTML as CSV.

Yahoo v8 chart is an unofficial and availability-unproven provider API.
Any derived INGR CAPM beta is a price-only, noncanonical ASSUMPTION.
"""
from __future__ import annotations

import argparse
import copy
from datetime import date, datetime, timezone, timedelta
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.external_source import (
    build_external_source_snapshot, build_wacc_source_input_from_snapshot,
    materialize_external_source_snapshot, validate_external_source_snapshot,
    validate_wacc_source_input_against_snapshot,
)
from valuation_hub.ingr_r8_m23_execution import _git, _write
from valuation_hub.ingr_wacc_levered_beta import (
    START, AS_OF, MIN_DAILY, MIN_WEEKLY_RETURNS, _weekly_benchmark_pairs,
)

URL_INGR = ("https://query1.finance.yahoo.com/v8/finance/chart/INGR"
            "?period1=1694649600&period2=1789430400&interval=1d")
URL_INDEX = ("https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC"
             "?period1=1694649600&period2=1789430400&interval=1d")
SCHEMA = "ingr-yahoo-chart-weekly-price-beta-proof-v0.1"
METHOD = "YAHOO_V8_CLOSE_ONLY_ALIGNED_WEEKLY_3Y_OLS_V01"


def _sha(v:dict[str,Any], excluded:str)->str:
    copy_obj=copy.deepcopy(v)
    copy_obj.pop(excluded,None)
    return hashlib.sha256(json.dumps(copy_obj,sort_keys=True,ensure_ascii=False,
                         separators=(",",":"),allow_nan=False).encode()).hexdigest()


def _source_series(raw:str, expected_symbol:str)->dict[date,float]:
    if not isinstance(raw,str) or not raw.strip() or len(raw.encode("utf-8"))>5_000_000:
        raise CaseServiceError("Yahoo original JSON missing or oversized")
    if raw.lstrip().startswith("<"):
        raise CaseServiceError("Yahoo original received HTML / JS challenge, not JSON")
    try:
        value=json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CaseServiceError("Yahoo original v8 chart body not valid JSON") from exc
    if not isinstance(value,dict) or set(value)!={"chart"}:
        raise CaseServiceError("Yahoo original chart envelope malformed")
    chart=value["chart"]
    if not isinstance(chart,dict) or chart.get("error") is not None:
        raise CaseServiceError("Yahoo original chart provider error/auth/rate limit")
    result=chart.get("result")
    if not isinstance(result,list) or len(result)!=1 or not isinstance(result[0],dict):
        raise CaseServiceError("Yahoo original chart result absent/ambiguous")
    record=result[0]
    meta=record.get("meta")
    if not isinstance(meta,dict) or meta.get("symbol")!=expected_symbol:
        raise CaseServiceError("Yahoo original ticker identity mismatch")
    if meta.get("currency")!="USD":
        raise CaseServiceError("Yahoo original ticker currency not USD")
    if record.get("events") is not None and not isinstance(record["events"],dict):
        raise CaseServiceError("Yahoo chart corporate-action events structure malformed")
    timestamps=record.get("timestamp")
    ind=record.get("indicators")
    if (not isinstance(timestamps,list) or not isinstance(ind,dict)
        or not isinstance(ind.get("quote"),list) or len(ind["quote"])!=1
        or not isinstance(ind["quote"][0],dict)):
        raise CaseServiceError("Yahoo original timestamps/daily quote structure missing")
    raw_close=ind["quote"][0].get("close")
    if not isinstance(raw_close,list) or len(raw_close)!=len(timestamps):
        raise CaseServiceError("Yahoo daily close and timestamp arrays misaligned")
    if len(timestamps)<MIN_DAILY:
        raise CaseServiceError("Yahoo daily time series too short")
    if len(set(timestamps))!=len(timestamps):
        raise CaseServiceError("Yahoo duplicated raw timestamp")
    series:dict[date,float]={}
    prev=None
    for stamp,closing in zip(timestamps,raw_close):
        if isinstance(stamp,bool) or not isinstance(stamp,int) or stamp<=0:
            raise CaseServiceError("Yahoo daily timestamp must be integer UTC epoch seconds")
        if prev is not None and stamp<=prev:
            raise CaseServiceError("Yahoo daily timestamps not strictly increasing")
        prev=stamp
        # All US daily chart UTC stamps fall on the stated US trading
        # calendar day. No timezone-rebaselining or future values allowed.
        d=datetime.fromtimestamp(stamp,tz=timezone.utc).date()
        if not (START<=d.isoformat()<=AS_OF) or d.weekday()>4:
            raise CaseServiceError("Yahoo daily source date outside valuation lookback")
        if isinstance(closing,bool) or not isinstance(closing,(float,int)):
            raise CaseServiceError("Yahoo raw close missing/partial/non-numeric")
        p=float(closing)
        if not math.isfinite(p) or p<=0:
            raise CaseServiceError("Yahoo close nonfinite or nonpositive")
        if d in series:
            raise CaseServiceError("Yahoo multiple UTC timestamps for same date")
        series[d]=p
    if len(series)<MIN_DAILY or max(series)!=date.fromisoformat(AS_OF):
        raise CaseServiceError("Yahoo exact as-of last trading close missing")
    if min(series)>date.fromisoformat(START)+timedelta(days=12):
        raise CaseServiceError("Yahoo three-year lookback origin missing")
    return series


def calculate_yahoo_beta(issuer_json:str, benchmark_json:str)->dict[str,Any]:
    issuer=_source_series(issuer_json,"INGR")
    market=_source_series(benchmark_json,"^GSPC")
    pairs=_weekly_benchmark_pairs(issuer,market)
    ir=[x[1] for x in pairs]
    mr=[x[2] for x in pairs]
    mu_i=sum(ir)/len(ir)
    mu_m=sum(mr)/len(mr)
    variance=sum((r-mu_m)**2 for r in mr)
    covariance=sum((r-mu_m)*(i-mu_i) for r,i in zip(mr,ir))
    response_var=sum((i-mu_i)**2 for i in ir)
    if variance<=1e-8 or response_var<=1e-8:
        raise CaseServiceError("Yahoo INGR/index market or issuer return variance too small")
    beta=covariance/variance
    if not -5<beta<10 or not math.isfinite(beta):
        raise CaseServiceError("Yahoo derived CAPM beta outside WACC range")
    r2=min(1.0,(covariance*covariance)/(variance*response_var))
    trace_sha=hashlib.sha256(json.dumps(pairs,separators=(",",":"),
                 ensure_ascii=False,allow_nan=False).encode()).hexdigest()
    return {
        "method":METHOD,"issuer_symbol":"INGR","benchmark_symbol":"^GSPC",
        "currency":"USD","valuation_date":AS_OF,"lookback_start":START,
        "date_normalization":"UTC_CALENDAR_DATE_OF_VENDOR_DAILY_CHART",
        "return_basis":"PRICE_ONLY_CLOSE_TO_CLOSE_NOT_DIVIDEND_ADJUSTED_TOTAL_RETURN",
        "dividends_included":False,"historical_adjustment_basis_verified":False,
        "historical_source_availability_asof_proven":False,
        "vendor_api_official_or_supported":False,
        "issuer_daily_rows":len(issuer),"benchmark_daily_rows":len(market),
        "aligned_days":len(issuer.keys()&market.keys()),
        "weekly_returns":len(pairs),"first_return":pairs[0][0],
        "last_return":pairs[-1][0],"regression_beta":beta,
        "alpha_weekly":mu_i-beta*mu_m,
        "r_squared":r2,"return_pairs_sha256":trace_sha,
        "claim_class":"ASSUMPTION","human_review_completed":False,
    }


def _projection(issuer:dict[str,Any], benchmark:dict[str,Any],
                wacc:dict[str,Any])->dict[str,Any]:
    for snapshot,url in ((issuer,URL_INGR),(benchmark,URL_INDEX)):
        validate_external_source_snapshot(snapshot)
        if snapshot["source"]["locator"]!=url or snapshot["source"]["tier"]!="B":
            raise CaseServiceError("Yahoo original query/source provenance mismatch")
    method=calculate_yahoo_beta(issuer["raw_text"],benchmark["raw_text"])
    validate_wacc_source_input_against_snapshot(wacc,issuer)
    if (wacc.get("metric")!="levered_beta"
        or wacc.get("value")!=method["regression_beta"]
        or wacc.get("unit")!="ratio"
        or wacc.get("observed_on")!=AS_OF
        or wacc.get("claim_class")!="ASSUMPTION"):
        raise CaseServiceError("Yahoo derived WACC beta input mismatch")
    obj={
        "schema_version":SCHEMA,"canonical":False,
        "status":"UNREVIEWED_ORIGINAL_YAHOO_PRICE_ONLY_INGR_BETA",
        "method":method,
        "issuer_snapshot_sha256":issuer["snapshot_sha256"],
        "market_snapshot_sha256":benchmark["snapshot_sha256"],
        "issuer_body_sha256":issuer["body"]["sha256"],
        "market_body_sha256":benchmark["body"]["sha256"],
        "wacc_input_sha256":wacc["input_sha256"],
        "human_review_completed":False,"wacc_package_created":False,
        "proof_sha256":"",
    }
    obj["proof_sha256"]=_sha(obj,"proof_sha256")
    return obj


def build_yahoo_beta_source(issuer_json:str, benchmark_json:str,
                            *, captured_at:str)->dict[str,Any]:
    method=calculate_yahoo_beta(issuer_json,benchmark_json)
    issuer=build_external_source_snapshot(issuer_json,source_publisher="Yahoo Finance v8 chart INGR",
        source_type="daily_chart_unverified_price_only",source_tier="B",
        source_locator=URL_INGR,captured_at=captured_at)
    market=build_external_source_snapshot(benchmark_json,source_publisher="Yahoo Finance v8 chart ^GSPC",
        source_type="daily_chart_price_index_only",source_tier="B",
        source_locator=URL_INDEX,captured_at=captured_at)
    wacc=build_wacc_source_input_from_snapshot(issuer,metric="levered_beta",
        value=method["regression_beta"],unit="ratio",observed_on=AS_OF,
        claim_class="ASSUMPTION")
    return {"issuer_snapshot":issuer,"market_snapshot":market,
            "wacc_input":wacc,"proof":_projection(issuer,market,wacc)}


def validate_yahoo_beta_proof(proof:dict[str,Any],wacc:dict[str,Any],
                              issuer:dict[str,Any],market:dict[str,Any])->dict[str,Any]:
    if not isinstance(proof,dict) or proof.get("schema_version")!=SCHEMA:
        raise CaseServiceError("Yahoo original beta proof absent/wrong schema")
    if proof!=_projection(issuer,market,wacc):
        raise CaseServiceError("Yahoo two-source original-price model proof mismatch")
    return {"status":"PASS_YAHOO_ORIGINAL_TWO_SOURCE_PRICE_ONLY_BETA",
            "beta":proof["method"]["regression_beta"],
            "method_proof_sha256":proof["proof_sha256"],
            "weekly_returns":proof["method"]["weekly_returns"],
            "historical_availability_asof_proven":False,
            "human_review_completed":False}


def materialize_yahoo_beta(repo:Path,issuer_path:Path,market_path:Path)->dict[str,Any]:
    repo=repo.resolve()
    base=(repo/"workspace"/"source_snapshots").resolve()
    paths=[x.resolve() for x in (issuer_path,market_path)]
    if any(not p.is_file() or not p.is_relative_to(base) for p in paths):
        raise CaseServiceError("Yahoo beta original JSON must stay user-local")
    result=build_yahoo_beta_source(*(p.read_text(encoding="utf-8-sig") for p in paths),
                                   captured_at=datetime.now(timezone.utc).isoformat())
    a,b,c,d=(result[key] for key in
             ("issuer_snapshot","market_snapshot","wacc_input","proof"))
    token=a["body"]["sha256"][:12]+"_"+b["body"]["sha256"][:12]
    targets=[
        base/f"INGR_beta_yahoo_issuer_{token}_snapshot.json",
        base/f"INGR_beta_yahoo_index_{token}_snapshot.json",
        base/f"INGR_wacc_levered_beta_yahoo_{token}.json",
        base/f"INGR_wacc_levered_beta_yahoo_{token}_proof.json",
    ]
    if any(p.exists() for p in targets):
        raise CaseServiceError("Yahoo identical original pair already materialized")
    materialize_external_source_snapshot(a,targets[0],root=repo)
    materialize_external_source_snapshot(b,targets[1],root=repo)
    _write(targets[2],c)
    _write(targets[3],d)
    return {
        "status":"REAL_INGR_YAHOO_PRICE_ONLY_BETA_CANDIDATE_READY_FOR_REVIEW",
        "canonical":False,"metric":"levered_beta","value":c["value"],
        "claim_class":"ASSUMPTION","weekly_returns":d["method"]["weekly_returns"],
        "r_squared":d["method"]["r_squared"],
        "issuer_body_sha256":a["body"]["sha256"],
        "market_body_sha256":b["body"]["sha256"],
        "source_input_sha256":c["input_sha256"],
        "proof_sha256":d["proof_sha256"],
        "issuer_snapshot_path":str(targets[0]),
        "market_snapshot_path":str(targets[1]),
        "wacc_input_path":str(targets[2]),
        "method_proof_path":str(targets[3]),
        "historical_source_availability_asof_proven":False,
        "human_review_completed":False,"reviewed_wacc_package":None,
    }


def main(argv:list[str]|None=None)->int:
    p=argparse.ArgumentParser(description="Offline source-locked Yahoo price-only INGR beta")
    p.add_argument("--repo-root",type=Path,default=Path.cwd())
    p.add_argument("--issuer",type=Path,required=True)
    p.add_argument("--market",type=Path,required=True)
    p.add_argument("--json",action="store_true")
    args=p.parse_args(argv)
    try:
        repo=args.repo_root.resolve()
        _git(repo)
        issuer=args.issuer if args.issuer.is_absolute() else repo/args.issuer
        market=args.market if args.market.is_absolute() else repo/args.market
        result=materialize_yahoo_beta(repo,issuer,market)
    except (CaseServiceError,OSError,ValueError,TypeError,KeyError) as exc:
        result={"status":"ERROR","error":str(exc)}
    print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))
    return int(result["status"]=="ERROR")


if __name__=="__main__":
    raise SystemExit(main())
