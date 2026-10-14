"""M30-R8M24-EQV: offline two-source, explicitly lagged equity market value.

Do not confuse SEC common shares outstanding as of 2026-08-05 with
2026-09-14 common shares FACT or with 63.9m R6 diluted ASSUMPTION.
The numerical proxy is an unapproved WACC ASSUMPTION source candidate.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
from datetime import date, datetime, timezone
from decimal import Decimal
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.external_source import (
    build_external_source_snapshot,
    build_wacc_source_input_from_snapshot,
    validate_external_source_snapshot,
    validate_wacc_source_input_against_snapshot,
    materialize_external_source_snapshot,
)
from valuation_hub.ingr_r8_m23_execution import _git, _read, _write
from valuation_hub.sec_scope_reconciliation_r8 import (
    SOURCE_SHA as SEC_SHA, LOCATOR as SEC_LOCATOR, _source_checks,
)

SCHEMA = "ingr-market-cap-proxy-proof-v0.1"
POLICY = "MARKET_CAP_UNADJUSTED_CLOSE_LAGGED_REPORTED_COMMON_SHARES_V01"
PRICE_URL = "https://stockanalysis.com/stocks/ingr/history/"
VALUATION_DATE = "2026-09-14"
PRICE_DATE_TEXT = "SEP 14, 2026"
SHARE_DATE = "2026-08-05"
SHARES = 63_063_979
CLOSE = Decimal("98.63")
WACC_METRIC = "equity_market_value"


class _VisibleTables(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self.parts: list[str] = []
        self._current: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table" and self._current is None:
            self._current = []
        elif tag == "tr" and self._current is not None and self._row is None:
            self._row = []
        elif tag in ("th", "td") and self._row is not None and self._cell is None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)
        self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in ("th", "td") and self._cell is not None and self._row is not None:
            self._row.append(" ".join(" ".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None and self._current is not None:
            self._current.append(self._row)
            self._row = None
        elif tag == "table" and self._current is not None:
            self.tables.append(self._current)
            self._current = None


def _normalize(text: str) -> str:
    return " ".join(text.replace("\xa0", " ").upper().split())


def _parse_html(raw: str) -> _VisibleTables:
    p = _VisibleTables()
    try:
        p.feed(raw)
        p.close()
    except Exception as exc:
        raise CaseServiceError("market price/SEC HTML parsing failed") from exc
    return p


def extract_unadjusted_close(raw: str) -> dict[str, Any]:
    if not isinstance(raw, str) or "<table" not in raw.lower():
        raise CaseServiceError("daily market quote must contain a readable historical HTML table")
    parser = _parse_html(raw)
    hits = []
    for table in parser.tables:
        for i, row in enumerate(table):
            headers = [_normalize(x).replace(".", "") for x in row]
            if "DATE" not in headers or "CLOSE" not in headers:
                continue
            date_col = headers.index("DATE")
            close_col = headers.index("CLOSE")
            for data in table[i+1:]:
                if max(date_col, close_col) >= len(data):
                    continue
                day = _normalize(data[date_col])
                if day not in ("SEP 14, 2026", "SEPTEMBER 14, 2026"):
                    continue
                hits.append((row, data, data[close_col]))
    if len(hits) != 1:
        raise CaseServiceError("exactly one 2026-09-14 INGR daily unadjusted Close row is required")
    header, row, raw_close = hits[0]
    if not re.fullmatch(r"\$?\s*\d+(?:\.\d{1,2})?", raw_close.strip()):
        raise CaseServiceError("unadjusted daily close cell not numeric USD")
    found = Decimal(raw_close.replace("$", "").strip())
    if found != CLOSE:
        raise CaseServiceError("2026-09-14 INGR unadjusted close differs from cross-verified $98.63")
    return {"date": VALUATION_DATE, "ticker": "INGR", "exchange": "NYSE",
            "currency": "USD", "price": float(found),
            "market_close_convention": "UNADJUSTED_CLOSE",
            "header": header, "row": row}


def extract_sec_reported_common_shares(sec_snapshot: dict[str, Any]) -> dict[str, Any]:
    validate_external_source_snapshot(sec_snapshot)
    _source_checks(sec_snapshot)
    if (sec_snapshot["snapshot_sha256"] != SEC_SHA
        or sec_snapshot["source"]["locator"] != SEC_LOCATOR):
        raise CaseServiceError("not the exact Tier-A original Ingredion 2026 Q2 filing")
    parser = _parse_html(sec_snapshot["raw_text"])
    visible = _normalize(" ".join(parser.parts))
    match = re.search(
        r"OUTSTANDING AS OF AUGUST\s+5,\s+2026.{0,500}?"
        r"63,063,979\s+SHARES", visible,
        flags=re.DOTALL,
    )
    if not match:
        raise CaseServiceError("Q2 filed shares and August 5 instant cannot be jointly attested")
    return {"shares": SHARES, "observed_on": SHARE_DATE,
            "class": "NORMALIZED_FACT", "share_count_type": "COMMON_OUTSTANDING",
            "filing_source_sha256": SEC_SHA,
            "source_excerpt": match.group(0)}


def _hash(obj: dict[str, Any], exclude: str) -> str:
    o = copy.deepcopy(obj)
    o.pop(exclude, None)
    return hashlib.sha256(json.dumps(o, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _reconstruct(price_snapshot: dict[str, Any], sec_snapshot: dict[str, Any],
                 wacc_input: dict[str, Any]) -> dict[str, Any]:
    validate_external_source_snapshot(price_snapshot)
    if (price_snapshot["source"]["locator"] != PRICE_URL
        or price_snapshot["source"]["tier"] not in ("A","B","C")):
        raise CaseServiceError("untrusted price source URL or tier")
    price = extract_unadjusted_close(price_snapshot["raw_text"])
    shares = extract_sec_reported_common_shares(sec_snapshot)
    expected_value = Decimal(str(price["price"])) * Decimal(shares["shares"])
    date_lag = (date.fromisoformat(VALUATION_DATE) - date.fromisoformat(SHARE_DATE)).days
    if date_lag != 40:
        raise CaseServiceError("stale share-count lag must be exactly visible")
    if (wacc_input.get("metric") != WACC_METRIC
        or wacc_input.get("claim_class") != "ASSUMPTION"
        or wacc_input.get("value") != float(expected_value)
        or wacc_input.get("unit") != "USD"
        or wacc_input.get("observed_on") != VALUATION_DATE):
        raise CaseServiceError("market cap value/class/as-of inconsistent with source-bound proxy")
    validate_wacc_source_input_against_snapshot(wacc_input, price_snapshot)
    proof = {
        "schema_version": SCHEMA, "status": "UNREVIEWED_LAGGED_COMMON_SHARES_MARKETCAP_PROXY",
        "canonical": False, "policy": POLICY, "entity_id": "SEC_CIK:0001046257",
        "as_of": VALUATION_DATE, "currency": "USD",
        "price": price, "reported_common_shares": shares, "share_lag_days": date_lag,
        "share_count_carryforward": "ASSUMPTION_NOT_ASOF_FACT",
        "value_usd": float(expected_value),
        "source_price_snapshot_sha256": price_snapshot["snapshot_sha256"],
        "source_sec_snapshot_sha256": SEC_SHA,
        "wacc_input_sha256": wacc_input["input_sha256"],
        "reviewed_by_human": False, "eligible_for_auto_review": False,
        "warning": "No proven 2026-09-14 outstanding-share count. Use August 5 reported common shares only as explicit 40-day lagged proxy. Do not use R6 63.9m diluted shares.",
        "proof_sha256": "",
    }
    proof["proof_sha256"] = _hash(proof, "proof_sha256")
    return proof


def build_market_cap_proxy(price_raw: str, sec_snapshot: dict[str, Any],
                           *, captured_at: str) -> dict[str, Any]:
    price_data = extract_unadjusted_close(price_raw)
    snap = build_external_source_snapshot(
        price_raw, source_publisher="Stock Analysis / S&P Global Market Intelligence",
        source_type="historical_stock_prices_unadjusted_daily",
        source_tier="B", source_locator=PRICE_URL, captured_at=captured_at)
    sec = extract_sec_reported_common_shares(sec_snapshot)
    value = float(Decimal(str(price_data["price"])) * Decimal(sec["shares"]))
    inp = build_wacc_source_input_from_snapshot(
        snap, metric=WACC_METRIC, value=value, unit="USD",
        observed_on=VALUATION_DATE, claim_class="ASSUMPTION")
    proof = _reconstruct(snap, sec_snapshot, inp)
    return {"price_snapshot": snap, "wacc_input": inp, "proof": proof}


def validate_market_cap_proxy(proof: dict[str, Any], inp: dict[str, Any],
                              price_snapshot: dict[str, Any],
                              sec_snapshot: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(proof, dict) or proof.get("schema_version") != SCHEMA:
        raise CaseServiceError("equity market value lagged source proof missing")
    expected = _reconstruct(price_snapshot, sec_snapshot, inp)
    if proof != expected:
        raise CaseServiceError("equity market value two-source proof/sha/method differs")
    return {"status": "PASS_UNREVIEWED_INGR_EQUITY_MARKET_VALUE_PROXY",
            "proof_sha256": proof["proof_sha256"],
            "wacc_input_sha256": inp["input_sha256"],
            "market_value_usd": proof["value_usd"],
            "share_count_reference_date": SHARE_DATE,
            "lag_days": 40, "source_class": "ASSUMPTION", "human_reviewed": False}


def materialize_market_cap_proxy(repo: Path, price_path: Path, sec_path: Path) -> dict[str, Any]:
    repo = repo.resolve()
    src_dir = (repo / "workspace" / "source_snapshots").resolve()
    if not price_path.resolve().is_relative_to(src_dir) or not price_path.is_file():
        raise CaseServiceError("original price HTML must be inside user-local workspace/source_snapshots")
    if not sec_path.resolve().is_relative_to(src_dir) or not sec_path.is_file():
        raise CaseServiceError("SEC Tier-A Q2 snapshot must be inside user-local workspace/source_snapshots")
    price = price_path.read_text(encoding="utf-8-sig")
    sec = _read(sec_path)
    artifacts = build_market_cap_proxy(price, sec, captured_at=datetime.now(timezone.utc).isoformat())
    snapshot = artifacts["price_snapshot"]
    inp, proof = artifacts["wacc_input"], artifacts["proof"]
    prefix = snapshot["snapshot_sha256"][:16]
    price_dest = src_dir / f"INGR_equity_price_20260914_{prefix}_snapshot.json"
    inp_dest = src_dir / f"INGR_wacc_equity_market_value_20260914_{prefix}.json"
    proof_dest = src_dir / f"INGR_wacc_equity_market_value_20260914_{prefix}_proof.json"
    if any(x.exists() for x in (price_dest, inp_dest, proof_dest)):
        raise CaseServiceError("identical price capture already materialized; refuse overwrite")
    materialize_external_source_snapshot(snapshot, price_dest, root=repo)
    _write(inp_dest, inp)
    _write(proof_dest, proof)
    return {"status": "REAL_INGR_EQUITY_MARKET_VALUE_PROXY_READY_FOR_REVIEW",
            "as_of": VALUATION_DATE, "canonical": False,
            "price_usd": float(CLOSE), "reported_common_shares": SHARES,
            "share_reported_at": SHARE_DATE, "lag_days": 40,
            "equity_market_value_usd": inp["value"], "source_class": "ASSUMPTION",
            "price_snapshot_sha256": snapshot["snapshot_sha256"],
            "sec_snapshot_sha256": SEC_SHA,
            "market_value_input_sha256": inp["input_sha256"],
            "market_value_proof_sha256": proof["proof_sha256"],
            "price_snapshot_path": str(price_dest),
            "wacc_input_path": str(inp_dest), "proof_path": str(proof_dest),
            "human_review_completed": False, "reviewed_wacc_package": None,
            "next_action": "REVALIDATE_SEVEN_METRIC_INGR_M24_READINESS"}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Source-bound INGR equity market-cap lagged-share proxy")
    p.add_argument("--repo-root", type=Path, default=Path.cwd())
    p.add_argument("--price-raw", required=True, type=Path)
    p.add_argument("--sec-snapshot", type=Path,
                   default=Path("workspace/source_snapshots/INGR_2026Q2_10Q_dilution_snapshot_20260914.json"))
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    try:
        repo = a.repo_root.resolve()
        _git(repo)
        raw = a.price_raw if a.price_raw.is_absolute() else repo / a.price_raw
        sec = a.sec_snapshot if a.sec_snapshot.is_absolute() else repo / a.sec_snapshot
        result = materialize_market_cap_proxy(repo, raw, sec)
    except (CaseServiceError, ValueError, TypeError, KeyError, OSError) as exc:
        result = {"status":"ERROR", "error":str(exc)}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 1 if result["status"] == "ERROR" else 0

if __name__ == "__main__":
    raise SystemExit(main())
