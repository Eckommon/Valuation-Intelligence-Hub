"""M30-R8M24-DMV: offline, source-bound Ingredion Q2 2026 debt-MV proxy.

The reported long-term debt Level-2 fair value plus short-term borrowing
carrying-as-fair-value approximation is an unreviewed ASSUMPTION, never
a disclosed total-debt-market-value FACT, WACC approval, or Draft mutation.
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
    build_external_source_snapshot, build_wacc_source_input_from_snapshot,
    materialize_external_source_snapshot, validate_external_source_snapshot,
    validate_wacc_source_input_against_snapshot,
)
from valuation_hub.ingr_wacc_damodaran_erp import _visible
from valuation_hub.ingr_r8_m23_execution import _git, _write

URL = "https://www.sec.gov/Archives/edgar/data/1046257/000162828026054722/ingr-20260630.htm"
OBSERVED_ON = "2026-06-30"
AS_OF = "2026-09-14"
FILED_ON = "2026-08-07"
VALUE_USD = 1_681_000_000.0
SCHEMA = "ingr-debt-market-value-proxy-proof-v0.1"
METHOD = "LONG_TERM_LEVEL2_FAIR_VALUE_PLUS_SHORT_TERM_CARRYING_AS_FAIR_VALUE_PROXY"


def _section(text: str, start: str, end: str, name: str) -> str:
    starts = list(re.finditer(start, text, flags=re.I))
    if len(starts) != 1:
        raise CaseServiceError(f"SEC {name} note heading absent or ambiguous")
    tail = text[starts[0].end():]
    bound = re.search(end, tail, flags=re.I)
    if bound is None:
        raise CaseServiceError(f"SEC {name} note boundary absent")
    return tail[:bound.start()]


def _row(text: str, label: str, next_label: str, name: str) -> str:
    starts = list(re.finditer(label, text, flags=re.I))
    if len(starts) != 1:
        raise CaseServiceError(f"SEC {name} row absent or duplicate")
    tail = text[starts[0].end():]
    end = re.search(next_label, tail, flags=re.I)
    if end is None:
        raise CaseServiceError(f"SEC {name} row boundary absent")
    return tail[:end.start()]


def _numbers(row: str, *, name: str) -> list[int]:
    # Dash is explicitly reported zero within the Level 1/3 hierarchy; never
    # use this conversion for an absent field or a missing source row.
    text = re.sub(r"(?<!\w)[—–-](?!\w)", " 0 ", row).replace("$", " ")
    if re.search(r"[^\d\s,.]", text):
        raise CaseServiceError(f"SEC {name} contains unexpected characters")
    return [int(x.replace(",", "")) for x in re.findall(r"\d[\d,]*", text)]


def extract_debt_mv(raw: str) -> dict[str, Any]:
    text = _visible(raw)
    if not re.search(r"Ingredion\s+Incorporated", text, re.I):
        raise CaseServiceError("SEC issuer mismatch")
    if not re.search(r"quarterly\s+period\s+ended\s+June\s+30,?\s+2026", text, re.I):
        raise CaseServiceError("SEC quarter mismatch")
    if not re.search(r"dollars\s+in\s+millions", text, re.I):
        raise CaseServiceError("SEC currency scale not evidenced")
    fair = _section(text, r"5\s*\.\s*Fair\s+Value\s+Measurements",
                    r"6\s*\.\s*Financing\s+Arrangements", "fair value")
    debt = _section(text, r"6\s*\.\s*Financing\s+Arrangements",
                    r"7\s*\.\s*Pension\s+and\s+Other\s+Postretirement\s+Benefits", "financing")
    period = r"As\s+of\s+June\s+30,?\s+2026\s+As\s+of\s+December\s+31,?\s+2025"
    if not re.search(period, fair, re.I) or not re.search(period, debt, re.I):
        raise CaseServiceError("SEC Q2 vs prior-year comparison columns missing")
    if not re.search(r"Level\s+1\s+Level\s+2\s+Level\s+3\s+Total\s+Level\s+1\s+Level\s+2\s+Level\s+3\s+Total", fair, re.I):
        raise CaseServiceError("SEC Level 2 fair value position not demonstrated")
    fv_row = _row(fair, r"(?<!Total\s)Long-term\s+debt",
                  r"The\s+carrying\s+values\s+of", "long-term fair value")
    fv = _numbers(fv_row, name="long-term fair value")
    if fv != [0, 1640, 0, 1640, 0, 1649, 0, 1649]:
        raise CaseServiceError("SEC long-term Level-2 fair value or year columns contradicted")
    if not re.search(r"short-term\s+borrowings\s+and\s+accounts\s+payable\s+approximate\s+fair\s+values", fair, re.I):
        raise CaseServiceError("SEC short-term debt FV proxy policy unverified")
    if not re.search(r"fair\s+value\s+of\s+our\s+long-term\s+debt\s+is\s+estimated\s+based\s+on\s+quotations", fair, re.I):
        raise CaseServiceError("SEC fair-value quotation policy unverified")
    pairs = (
        ("long_term_book", r"Total\s+long-term\s+debt", r"Other\s+short-term\s+borrowings", [1742, 1742]),
        ("short_term_book", r"Total\s+short-term\s+borrowings", r"Total\s+debt", [41, 48]),
        ("total_book", r"Total\s+debt(?!\s+carrying)", r"_{3,}|\(i\)\s*The\s+senior", [1783, 1790]),
    )
    for label, start, stop, expected in pairs:
        found = _numbers(_row(debt, start, stop, label), name=label)
        if found != expected:
            raise CaseServiceError(f"SEC {label} amounts/period wrong: {found}")
    for facility in ("Bridge", "DDTL"):
        if not re.search(rf"No\s+amounts\s+were\s+outstanding\s+under\s+the\s+{facility}\s+Facility\s+as\s+of\s+June\s+30,?\s+2026", debt, re.I):
            raise CaseServiceError(f"SEC {facility} undrawn facility exclusion unproven")
    if fv[1] + 41 != 1681 or 1783 - (fv[1] + 41) != 102:
        raise CaseServiceError("SEC debt MV/book value independent cross-check failed")
    return {
        "issuer": "Ingredion Incorporated", "entity_id": "SEC_CIK:0001046257",
        "period_end": OBSERVED_ON, "filed_on": FILED_ON,
        "valuation_as_of": AS_OF, "method": METHOD,
        "long_term_level2_fair_value_usd_millions": fv[1],
        "short_term_carrying_as_fair_value_usd_millions": 41,
        "debt_mv_proxy_usd_millions": 1681,
        "total_carrying_value_usd_millions": 1783,
        "book_less_proxy_usd_millions": 102,
        "debt_market_value_usd": VALUE_USD,
        "undrawn_acquisition_facilities_excluded": True,
        "claim_class": "ASSUMPTION",
        "methodology_selection": "ASSUMPTION_PENDING_REVIEW",
        "human_review_completed": False,
    }


def _sha(obj: dict[str, Any], field: str) -> str:
    value = copy.deepcopy(obj)
    value.pop(field, None)
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _projection(snapshot: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    validate_external_source_snapshot(snapshot)
    if snapshot["source"]["locator"] != URL or snapshot["source"]["tier"] != "A":
        raise CaseServiceError("SEC original debt-MV URL or source tier mismatch")
    method = extract_debt_mv(snapshot["raw_text"])
    validate_wacc_source_input_against_snapshot(item, snapshot)
    if (item.get("metric") != "debt_market_value" or item.get("value") != VALUE_USD
        or item.get("unit") != "USD" or item.get("observed_on") != OBSERVED_ON
        or item.get("claim_class") != "ASSUMPTION"):
        raise CaseServiceError("SEC debt market value requires exact dated ASSUMPTION")
    proof = {
        "schema_version": SCHEMA, "status": "UNREVIEWED_SEC_DEBT_MV_PROXY",
        "canonical": False, "method": method,
        "snapshot_sha256": snapshot["snapshot_sha256"],
        "source_body_sha256": snapshot["body"]["sha256"],
        "wacc_input_sha256": item["input_sha256"],
        "human_review_completed": False,
        "wacc_package_created": False, "proof_sha256": "",
    }
    proof["proof_sha256"] = _sha(proof, "proof_sha256")
    return proof


def build_debt_mv_source(raw: str, *, captured_at: str) -> dict[str, Any]:
    data = extract_debt_mv(raw)
    snapshot = build_external_source_snapshot(
        raw, source_publisher="US SEC / Ingredion Incorporated",
        source_type="2026q2_form10q_fair_value_financing",
        source_tier="A", source_locator=URL, captured_at=captured_at)
    item = build_wacc_source_input_from_snapshot(
        snapshot, metric="debt_market_value", value=data["debt_market_value_usd"],
        unit="USD", observed_on=OBSERVED_ON, claim_class="ASSUMPTION")
    return {"snapshot": snapshot, "wacc_input": item,
            "proof": _projection(snapshot, item)}


def validate_debt_mv_proof(proof: dict[str, Any], item: dict[str, Any],
                           snapshot: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(proof, dict) or proof.get("schema_version") != SCHEMA:
        raise CaseServiceError("SEC debt market value proof absent or wrong schema")
    if proof != _projection(snapshot, item):
        raise CaseServiceError("SEC debt market value method/input/source SHA mismatch")
    return {"status": "PASS_SOURCE_BOUND_DEBT_MV_PROXY_CANDIDATE",
            "method_proof_sha256": proof["proof_sha256"],
            "input_sha256": item["input_sha256"],
            "source_class": "ASSUMPTION", "observed_on": OBSERVED_ON,
            "human_review_completed": False}


def inspect_debt_mv_html(raw: str) -> dict[str, Any]:
    visible = _visible(raw)
    return {
        "status": "SEC_Q2_DEBT_DIAGNOSTIC_ONLY",
        "raw_body_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "html_bytes": len(raw.encode("utf-8")),
        "has_note5": bool(re.search(r"5\s*\.\s*Fair\s+Value\s+Measurements", visible, re.I)),
        "has_note6": bool(re.search(r"6\s*\.\s*Financing\s+Arrangements", visible, re.I)),
        "has_note7": bool(re.search(r"7\s*\.\s*Pension\s+and\s+Other\s+Postretirement\s+Benefits", visible, re.I)),
        "eligible_assumed": False, "human_review_completed": False,
    }


def materialize_debt_mv_source(repo: Path, raw_path: Path) -> dict[str, Any]:
    repo = repo.resolve()
    root = (repo / "workspace" / "source_snapshots").resolve()
    path = raw_path.resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise CaseServiceError("SEC debt original HTML must be in local workspace/source_snapshots")
    data = build_debt_mv_source(
        path.read_text(encoding="utf-8-sig"),
        captured_at=datetime.now(timezone.utc).isoformat())
    snapshot, item, proof = data["snapshot"], data["wacc_input"], data["proof"]
    tag = snapshot["snapshot_sha256"][:16]
    targets = [
        root / f"INGR_Q2_debt_market_value_{tag}_snapshot.json",
        root / f"INGR_wacc_debt_market_value_20260630_{tag}.json",
        root / f"INGR_wacc_debt_market_value_20260630_{tag}_proof.json",
    ]
    if any(p.exists() for p in targets):
        raise CaseServiceError("SEC debt market value immutable output already exists")
    materialize_external_source_snapshot(snapshot, targets[0], root=repo)
    _write(targets[1], item)
    _write(targets[2], proof)
    return {
        "status": "REAL_INGR_DEBT_MV_SOURCE_CANDIDATE_READY_FOR_REVIEW",
        "canonical": False, "claim_class": "ASSUMPTION",
        "debt_market_value_usd": VALUE_USD,
        "source_body_sha256": snapshot["body"]["sha256"],
        "source_snapshot_sha256": snapshot["snapshot_sha256"],
        "wacc_input_sha256": item["input_sha256"],
        "method_proof_sha256": proof["proof_sha256"],
        "source_snapshot_path": str(targets[0]),
        "wacc_input_path": str(targets[1]), "method_proof_path": str(targets[2]),
        "human_review_completed": False, "reviewed_wacc_package": None,
        "next_action": "REVALIDATE_SEVEN_METRIC_INGR_M24_READINESS",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Offline INGR SEC original-debt-MV source")
    p.add_argument("--repo-root", type=Path, default=Path.cwd())
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--diagnose", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    try:
        repo = args.repo_root.resolve()
        _git(repo)
        path = args.raw if args.raw.is_absolute() else repo / args.raw
        if args.diagnose:
            path = path.resolve()
            if not path.is_relative_to((repo / "workspace" / "source_snapshots").resolve()):
                raise CaseServiceError("SEC debt diagnostic outside local source root")
            result = inspect_debt_mv_html(path.read_text(encoding="utf-8-sig"))
        else:
            result = materialize_debt_mv_source(repo, path)
    except (CaseServiceError, TypeError, ValueError, KeyError, OSError) as exc:
        result = {"status": "ERROR", "error": str(exc)}
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 1 if result["status"] == "ERROR" else 0


if __name__ == "__main__":
    raise SystemExit(main())
