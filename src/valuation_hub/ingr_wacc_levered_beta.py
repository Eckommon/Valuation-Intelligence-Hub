"""M30-R8M24-BETA: offline two-source weekly price-return OLS for INGR.

This is an unreviewed price-only market beta ASSUMPTION. Stooq CSV
contains no total-return dividends; corporate-action adjustment and
historical publication are NOT attested by a retrospective download.
No prices, beta, approvals, or source records are generated synthetically.
"""
from __future__ import annotations

import argparse
import copy
import csv
from datetime import date, datetime, timedelta, timezone
import hashlib
import io
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

SCHEMA = "ingr-weekly-price-beta-method-proof-v0.1"
AS_OF = "2026-09-14"
START = "2023-09-14"
URL_INGR = "https://stooq.com/q/d/l/?s=ingr.us&i=d&d1=20230914&d2=20260914"
URL_SPX = "https://stooq.com/q/d/l/?s=%5Espx&i=d&d1=20230914&d2=20260914"
PERIOD = "CLOSE_ONLY_WEEKLY_LAST_COMMON_TRADING_DAY_3Y_OLS_V01"
MIN_DAILY = 500
MIN_WEEKLY_RETURNS = 125


def _sha(obj: dict[str, Any], key: str) -> str:
    value = copy.deepcopy(obj)
    value.pop(key, None)
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                        separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def _daily(raw: str, label: str) -> dict[date, float]:
    if not raw or len(raw.encode("utf-8")) > 4_000_000:
        raise CaseServiceError(f"{label}: original CSV body absent or oversized")
    try:
        reader = csv.DictReader(io.StringIO(raw.lstrip("\ufeff"), newline=""))
        if reader.fieldnames != ["Date", "Open", "High", "Low", "Close", "Volume"]:
            raise CaseServiceError(f"{label}: original daily OHLCV CSV header mismatch")
        result: dict[date, float] = {}
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise CaseServiceError(f"{label}: malformed/partial CSV row")
            if set(row) != set(reader.fieldnames):
                raise CaseServiceError(f"{label}: unexpected CSV fields")
            try:
                day = date.fromisoformat(row["Date"])
                o, h, l, c = (float(row[k]) for k in ("Open","High","Low","Close"))
                volume = float(row["Volume"])
            except (ValueError, TypeError) as exc:
                raise CaseServiceError(f"{label}: non-ISO date or nonnumeric daily bar") from exc
            if not START <= day.isoformat() <= AS_OF or day.weekday() >= 5:
                raise CaseServiceError(f"{label}: future/out-of-window/weekend daily bar")
            if any(not math.isfinite(v) or v <= 0 for v in (o,h,l,c)):
                raise CaseServiceError(f"{label}: missing/nonpositive close or OHLC")
            if not math.isfinite(volume) or volume < 0:
                raise CaseServiceError(f"{label}: missing/negative volume")
            if l > min(o,c,h) or h < max(o,c,l):
                raise CaseServiceError(f"{label}: OHLC price bounds inconsistent")
            if day in result:
                raise CaseServiceError(f"{label}: duplicated trading date")
            result[day] = c
    except (csv.Error, UnicodeError) as exc:
        raise CaseServiceError(f"{label}: malformed original CSV") from exc
    if len(result) < MIN_DAILY:
        raise CaseServiceError(f"{label}: insufficient original daily history")
    if max(result) != date.fromisoformat(AS_OF):
        raise CaseServiceError(f"{label}: last close is not exact valuation as-of day")
    if min(result) > date.fromisoformat(START) + timedelta(days=12):
        raise CaseServiceError(f"{label}: beginning of three-year lookback missing")
    return result


def _weekly_benchmark_pairs(issuer: dict[date, float],
                            market: dict[date, float]) -> list[tuple[str,float,float]]:
    # Use each ISO week's FINAL COMMON trading day; avoid mixing one
    # security's Thursday close with the index's Friday close.
    common = sorted(issuer.keys() & market.keys())
    weeks: dict[tuple[int,int], date] = {}
    for day in common:
        iso = day.isocalendar()
        weeks[(iso.year, iso.week)] = day
    dates = sorted(weeks.values())
    if len(dates) < MIN_WEEKLY_RETURNS + 1:
        raise CaseServiceError("INGR and SPX insufficient synchronized weeks")
    pairs: list[tuple[str,float,float]] = []
    for a,b in zip(dates, dates[1:]):
        if not 3 <= (b-a).days <= 10:
            raise CaseServiceError("INGR/SPX weekly gap inconsistent")
        ir = issuer[b]/issuer[a] - 1
        mr = market[b]/market[a] - 1
        if any(not math.isfinite(v) or abs(v) >= 0.40 for v in (ir,mr)):
            raise CaseServiceError("INGR/SPX extreme weekly close-price return requires review")
        pairs.append((b.isoformat(),ir,mr))
    if len(pairs) < MIN_WEEKLY_RETURNS or pairs[-1][0] != AS_OF:
        raise CaseServiceError("INGR/SPX weekly valuation-date alignment invalid")
    return pairs


def calculate_beta(issuer_csv: str, market_csv: str) -> dict[str, Any]:
    issuer = _daily(issuer_csv, "INGR.US")
    market = _daily(market_csv, "^SPX")
    paired = _weekly_benchmark_pairs(issuer,market)
    x = [p[2] for p in paired]
    y = [p[1] for p in paired]
    mx = sum(x)/len(x)
    my = sum(y)/len(y)
    sxx = sum((u-mx)**2 for u in x)
    syy = sum((v-my)**2 for v in y)
    sxy = sum((u-mx)*(v-my) for u,v in zip(x,y))
    if sxx <= 1e-8 or syy <= 1e-8:
        raise CaseServiceError("INGR/SPX degenerate market return variance")
    beta = sxy/sxx
    if not math.isfinite(beta) or not -5 < beta < 10:
        raise CaseServiceError("INGR/SPX model beta outside WACC contract")
    correlation = sxy/math.sqrt(sxx*syy)
    r2 = correlation*correlation
    if not 0 <= r2 <= 1+1e-10:
        raise CaseServiceError("INGR/SPX model R2 invalid")
    trace_hash = hashlib.sha256(json.dumps(paired,separators=(",",":"),
                             ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    return {
        "method": PERIOD,
        "issuer_symbol": "INGR.US", "benchmark_symbol": "^SPX",
        "return_basis": "PRICE_ONLY_CLOSE_TO_CLOSE_NOT_TOTAL_RETURN",
        "dividends_included": False, "historical_adjustment_basis_verified": False,
        "historical_source_availability_asof_proven": False,
        "valuation_date": AS_OF, "lookback_start": START,
        "aligned_daily_days": len(issuer.keys() & market.keys()),
        "issuer_daily_rows": len(issuer), "index_daily_rows": len(market),
        "weekly_returns": len(paired),
        "weekly_first_return": paired[0][0], "weekly_last_return": paired[-1][0],
        "regression_beta": beta, "alpha_weekly": my-beta*mx,
        "regression_r_squared": min(1.0,r2), "return_pairs_sha256": trace_hash,
        "industry_jan2026_levered_beta_comparator": 0.61,
        "industry_comparator_not_company_beta": True,
        "claim_class": "ASSUMPTION", "human_review_completed": False,
    }


def _projection(issuer_snapshot: dict[str,Any], market_snapshot: dict[str,Any],
                source_input: dict[str,Any]) -> dict[str,Any]:
    for src, expected in ((issuer_snapshot,URL_INGR),(market_snapshot,URL_SPX)):
        validate_external_source_snapshot(src)
        if src["source"]["locator"] != expected or src["source"]["tier"] != "B":
            raise CaseServiceError("INGR beta original CSV locator/tier mismatch")
    model = calculate_beta(issuer_snapshot["raw_text"], market_snapshot["raw_text"])
    validate_wacc_source_input_against_snapshot(source_input, issuer_snapshot)
    if (source_input.get("metric") != "levered_beta" or
        source_input.get("value") != model["regression_beta"] or
        source_input.get("unit") != "ratio" or
        source_input.get("observed_on") != AS_OF or
        source_input.get("claim_class") != "ASSUMPTION"):
        raise CaseServiceError("INGR source beta not exact market-price OLS ASSUMPTION")
    out = {
        "schema_version": SCHEMA, "canonical": False,
        "status": "UNREVIEWED_TWO_SOURCE_PRICE_ONLY_INGR_BETA",
        "method": model,
        "issuer_snapshot_sha256": issuer_snapshot["snapshot_sha256"],
        "market_snapshot_sha256": market_snapshot["snapshot_sha256"],
        "issuer_body_sha256": issuer_snapshot["body"]["sha256"],
        "market_body_sha256": market_snapshot["body"]["sha256"],
        "wacc_input_sha256": source_input["input_sha256"],
        "human_review_completed": False, "wacc_package_created": False,
        "proof_sha256": "",
    }
    out["proof_sha256"] = _sha(out,"proof_sha256")
    return out


def build_beta_source(issuer_csv: str, market_csv: str,
                      *, captured_at: str) -> dict[str,Any]:
    result = calculate_beta(issuer_csv, market_csv)
    issuer = build_external_source_snapshot(
        issuer_csv, source_publisher="Stooq historical INGR.US daily prices",
        source_type="daily_unadjusted_or_adjustment_unverified_ohlcv_close",
        source_tier="B", source_locator=URL_INGR, captured_at=captured_at)
    market = build_external_source_snapshot(
        market_csv, source_publisher="Stooq historical ^SPX daily index level",
        source_type="daily_sp500_price_index_close",
        source_tier="B", source_locator=URL_SPX, captured_at=captured_at)
    source_input = build_wacc_source_input_from_snapshot(
        issuer,metric="levered_beta",value=result["regression_beta"],
        unit="ratio",observed_on=AS_OF,claim_class="ASSUMPTION")
    return {
        "issuer_snapshot": issuer, "market_snapshot": market,
        "wacc_input": source_input,
        "proof": _projection(issuer, market, source_input),
    }


def validate_beta_method_proof(proof: dict[str,Any], inp: dict[str,Any],
                               issuer: dict[str,Any], market: dict[str,Any]) -> dict[str,Any]:
    if not isinstance(proof,dict) or proof.get("schema_version") != SCHEMA:
        raise CaseServiceError("INGR beta original two-source OLS proof missing")
    if proof != _projection(issuer,market,inp):
        raise CaseServiceError("INGR beta model/source/input SHA mismatch")
    return {
        "status": "PASS_TWO_SOURCE_INGR_BETA_PRICE_ONLY_CANDIDATE",
        "method_proof_sha256": proof["proof_sha256"],
        "beta": proof["method"]["regression_beta"],
        "n_weekly_returns": proof["method"]["weekly_returns"],
        "r_squared": proof["method"]["regression_r_squared"],
        "historical_availability_asof_proven": False,
        "human_review_completed": False,
    }


def materialize_beta_source(repo: Path, issuer_path: Path, market_path: Path) -> dict[str,Any]:
    repo = repo.resolve()
    root = (repo/"workspace"/"source_snapshots").resolve()
    paths = [x.resolve() for x in (issuer_path,market_path)]
    if any(not p.is_relative_to(root) or not p.is_file() for p in paths):
        raise CaseServiceError("beta original CSVs must be in user-local workspace/source_snapshots")
    result = build_beta_source(*(x.read_text(encoding="utf-8-sig") for x in paths),
                               captured_at=datetime.now(timezone.utc).isoformat())
    issuer,market,inp,proof = (result[k] for k in
        ("issuer_snapshot","market_snapshot","wacc_input","proof"))
    key = issuer["body"]["sha256"][:12]+"_"+market["body"]["sha256"][:12]
    targets = [
        root/f"INGR_beta_issuer_{key}_snapshot.json",
        root/f"INGR_beta_market_{key}_snapshot.json",
        root/f"INGR_wacc_levered_beta_{key}.json",
        root/f"INGR_wacc_levered_beta_{key}_proof.json",
    ]
    if any(p.exists() for p in targets):
        raise CaseServiceError("beta original source pair already captured; no overwrite")
    materialize_external_source_snapshot(issuer,targets[0],root=repo)
    materialize_external_source_snapshot(market,targets[1],root=repo)
    _write(targets[2],inp)
    _write(targets[3],proof)
    return {
        "status": "REAL_INGR_PRICE_ONLY_BETA_SOURCE_CANDIDATE_READY_FOR_REVIEW",
        "canonical": False, "metric": "levered_beta",
        "value": inp["value"], "claim_class": "ASSUMPTION",
        "weekly_sample_count": proof["method"]["weekly_returns"],
        "r_squared": proof["method"]["regression_r_squared"],
        "issuer_raw_sha256": issuer["body"]["sha256"],
        "market_raw_sha256": market["body"]["sha256"],
        "source_input_sha256": inp["input_sha256"],
        "proof_sha256": proof["proof_sha256"],
        "issuer_snapshot_path": str(targets[0]),
        "market_snapshot_path": str(targets[1]),
        "wacc_input_path": str(targets[2]),
        "method_proof_path": str(targets[3]),
        "price_only_not_total_return": True,
        "historical_availability_asof_proven": False,
        "human_review_completed": False, "reviewed_wacc_package": None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline INGR/^SPX weekly price-only OLS source")
    parser.add_argument("--repo-root",type=Path,default=Path.cwd())
    parser.add_argument("--issuer",type=Path,required=True)
    parser.add_argument("--market",type=Path,required=True)
    parser.add_argument("--json",action="store_true")
    opts = parser.parse_args(argv)
    try:
        repo = opts.repo_root.resolve()
        _git(repo)
        issuer = opts.issuer if opts.issuer.is_absolute() else repo/opts.issuer
        market = opts.market if opts.market.is_absolute() else repo/opts.market
        value = materialize_beta_source(repo,issuer,market)
    except (CaseServiceError,OSError,TypeError,ValueError,KeyError) as exc:
        value = {"status":"ERROR","error":str(exc)}
    print(json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False))
    return int(value["status"] == "ERROR")


if __name__ == "__main__":
    raise SystemExit(main())
