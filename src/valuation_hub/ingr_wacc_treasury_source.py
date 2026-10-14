"""M30-R8M24-RF: offline, source-locked nominal US Treasury 10-year intake.

As-of 2026-09-14. The original U.S. Treasury HTML or CSV is acquired
separately and never altered. This is one FACT source input candidate,
not a reviewed WACC assumption or a canonical Draft mutation.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.external_source import (
    build_external_source_snapshot,
    build_wacc_source_input_from_snapshot,
    materialize_external_source_snapshot,
    validate_wacc_source_input_against_snapshot,
)
from valuation_hub.ingr_r8_m23_execution import _git, _write

URL = ("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
       "TextView?field_tdr_date_value_month=202609&type=daily_treasury_yield_curve")
DATE = "2026-09-14"
DATE_CELL = "09/14/2026"
METRIC = "risk_free_rate"
TEN_YEAR_HEADER = "10 YR"
EXPECTED_PERCENT = 4.97
POLICY = "US_TREASURY_20260914_NOMINAL_10Y_PAR_YIELD_V01"


class _TreasuryRows(HTMLParser):
    """Preserve physical table rows/cells, not text from unrelated tables."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table" and self._table is None:
            self._table = []
        elif tag == "tr" and self._table is not None and self._row is None:
            self._row = []
        elif tag in ("td", "th") and self._row is not None and self._cell is None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(" ".join(" ".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            self.tables.append(self._table)
            self._table = None


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("\xa0", " ")).strip().upper()


def _extract_from_rows(tables: list[list[list[str]]]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for table in tables:
        for idx, row in enumerate(table):
            names = [_normalize(cell) for cell in row]
            if names.count("DATE") != 1 or names.count(TEN_YEAR_HEADER) != 1:
                continue
            date_col, ten_col = names.index("DATE"), names.index(TEN_YEAR_HEADER)
            if date_col == ten_col:
                raise CaseServiceError("10-year and date column colliding")
            for value_row in table[idx + 1:]:
                if date_col >= len(value_row) or ten_col >= len(value_row):
                    continue
                if _normalize(value_row[date_col]) != DATE_CELL:
                    continue
                candidates.append({"date": value_row[date_col],
                                   "ten_year": value_row[ten_col],
                                   "header": row,
                                   "data_row": value_row})
    if len(candidates) != 1:
        raise CaseServiceError("Treasury exact 09/14/2026 10 YR row must appear exactly once")
    return candidates[0]


def extract_treasury_ten_year(raw: str) -> dict[str, Any]:
    if not isinstance(raw, str) or not raw:
        raise CaseServiceError("exact Treasury source raw UTF-8 body required")
    if "<table" in raw.lower():
        p = _TreasuryRows()
        try:
            p.feed(raw)
            p.close()
        except Exception as exc:
            raise CaseServiceError("Treasury HTML table parser failed") from exc
        row = _extract_from_rows(p.tables)
    else:
        # Treasury Download CSV may use a BOM and a conventional Date, 10 YR header.
        parsed = list(csv.reader(io.StringIO(raw.lstrip("\ufeff"))))
        row = _extract_from_rows([parsed])
    raw_yield = row["ten_year"].replace("%", "").strip()
    if not re.fullmatch(r"\d{1,2}(?:\.\d{1,4})?", raw_yield):
        raise CaseServiceError("10-year Treasury rate cell is missing or nonnumeric")
    actual_percent = float(raw_yield)
    if actual_percent != EXPECTED_PERCENT:
        raise CaseServiceError("2026-09-14 Treasury 10 YR rate contradicts official 4.97%")
    return {"date": DATE, "maturity": TEN_YEAR_HEADER, "yield_percent": actual_percent,
            "rate_decimal": round(actual_percent / 100, 8),
            "header": row["header"], "source_table_row": row["data_row"],
            "policy": POLICY, "source_locator": URL}


def create_treasury_fact_from_raw(raw: str, *, captured_at: str) -> dict[str, Any]:
    evidence = extract_treasury_ten_year(raw)
    snapshot = build_external_source_snapshot(
        raw, source_publisher="U.S. Department of the Treasury",
        source_type="daily_treasury_nominal_par_yield_curve",
        source_tier="A", source_locator=URL, captured_at=captured_at)
    item = build_wacc_source_input_from_snapshot(
        snapshot, metric=METRIC, value=evidence["rate_decimal"],
        unit="decimal", observed_on=DATE, claim_class="FACT")
    validate_wacc_source_input_against_snapshot(item, snapshot)
    proof = {
        "schema_version": "treasury-date-column-cell-proof-v0.1",
        "canonical": False, "status": "EXACT_10Y_TREASURY_CELL_CAPTURED",
        "as_of": DATE, "value_percent": evidence["yield_percent"],
        "value_decimal": evidence["rate_decimal"], "cell": evidence["source_table_row"],
        "header": evidence["header"], "policy": POLICY,
        "source_snapshot_sha256": snapshot["snapshot_sha256"],
        "source_body_sha256": snapshot["body"]["sha256"],
        "wacc_source_input_sha256": item["input_sha256"],
        "reviewed_wacc": False, "human_reviewed": False
    }
    return {"snapshot": snapshot, "wacc_source_input": item, "cell_proof": proof}


def materialize_treasury_fact(repo: Path, raw_file: Path) -> dict[str, Any]:
    repo = repo.resolve()
    source_root = (repo / "workspace" / "source_snapshots").resolve()
    path = raw_file.resolve()
    if not path.is_relative_to(source_root) or not path.is_file():
        raise CaseServiceError("raw Treasury file must be under workspace/source_snapshots")
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise CaseServiceError("Treasury file must contain readable original UTF-8 HTML/CSV") from exc
    artifact = create_treasury_fact_from_raw(
        raw, captured_at=datetime.now(timezone.utc).isoformat())
    snapshot = artifact["snapshot"]
    item = artifact["wacc_source_input"]
    tag = snapshot["snapshot_sha256"][:16]
    target_snapshot = source_root / f"UST_nominal_10yr_20260914_{tag}_snapshot.json"
    target_input = source_root / f"INGR_wacc_risk_free_rate_20260914_{tag}.json"
    target_proof = (repo / "workspace" / "execution_artifacts" /
                    "US_INGR_INGREDION" / f"UST_10y_20260914_{tag}_cell_proof.json")
    if any(p.exists() for p in (target_snapshot, target_input, target_proof)):
        raise CaseServiceError("same source-tag Treasury artifact already exists; refusing overwrite")
    materialize_external_source_snapshot(snapshot, target_snapshot, root=repo)
    _write(target_input, item)
    _write(target_proof, artifact["cell_proof"])
    return {
        "status": "REAL_INGR_RISK_FREE_RATE_SOURCE_CANDIDATE_READY_FOR_REVIEW",
        "canonical": False, "as_of": DATE, "risk_free_rate": item["value"],
        "source_claim_class": "FACT", "source_tier": "A",
        "source_snapshot_sha256": snapshot["snapshot_sha256"],
        "source_body_sha256": snapshot["body"]["sha256"],
        "wacc_input_sha256": item["input_sha256"],
        "source_snapshot_path": str(target_snapshot),
        "wacc_input_path": str(target_input), "cell_proof_path": str(target_proof),
        "human_review_completed": False, "reviewed_wacc_package": None,
        "next_action": "REVALIDATE_SEVEN_METRIC_INGR_M24_READINESS"
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline UST 2026-09-14 10y WACC fact candidate")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        repo = args.repo_root.resolve()
        _git(repo)
        raw = args.raw if args.raw.is_absolute() else repo / args.raw
        result = materialize_treasury_fact(repo, raw)
    except (CaseServiceError, OSError, ValueError, TypeError, KeyError) as exc:
        result = {"status": "ERROR", "error": str(exc)}
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 1 if result["status"] == "ERROR" else 0


if __name__ == "__main__":
    raise SystemExit(main())
