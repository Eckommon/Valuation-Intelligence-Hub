"""M30-R8M24-ERP: exact-dated NYU Damodaran implied ERP model/source intake.

Evidence candidate only. Method selection (adjusted TTM payout), dated risk-free
reference (4.75% on Sep 1 versus 4.97% Sep 14), and independently validated
body/URL are carried through an unreviewed source-embedded method proof.
No human reviewer, WACC calculation approval or Draft mutation.
"""
from __future__ import annotations

import argparse
import copy
from datetime import date, datetime, timezone
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.external_source import (
    build_external_source_snapshot,
    build_wacc_source_input_from_snapshot,
    materialize_external_source_snapshot,
    validate_external_source_snapshot,
    validate_wacc_source_input_against_snapshot,
)
from valuation_hub.ingr_r8_m23_execution import _git, _read, _write

URL = "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/home.htm"
OBSERVED_ON = "2026-09-01"
AS_OF = "2026-09-14"
ERP = 0.0414
PUBLISHED_US_TREASURY_RATE = 0.0475
VALUATION_RF_RATE = 0.0497
POLICY = "NYU_DAMODARAN_SEP1_2026_IMPLIED_ERP_TTM_ADJUSTED_PAYOUT_V01"
SCHEMA = "wacc-erp-method-source-proof-v0.1"
HEADER = "Implied ERP on September 1, 2026"
METHOD = "Trailing 12 month, with adjusted payout"


class _Visible(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data)


def _visible(raw: str) -> str:
    if not raw.strip() or "<" not in raw:
        raise CaseServiceError("NYU original webpage HTML body required")
    parser = _Visible()
    try:
        parser.feed(raw)
        parser.close()
    except Exception as exc:
        raise CaseServiceError("NYU HTML parsing failed") from exc
    return " ".join(" ".join(parser.parts).split())


def _exact_pct(section: str, label: str) -> float:
    pattern = rf"(\d+(?:\.\d+)?)%\s*\(\s*{re.escape(label)}\s*\)"
    matches = re.findall(pattern, section, flags=re.I)
    if len(matches) != 1:
        raise CaseServiceError(f"NYU ERP {label} value missing or ambiguous")
    return float(matches[0])


def extract_dated_adjusted_erp(raw: str) -> dict[str, Any]:
    visible = _visible(raw)
    headline = re.findall(
        rf"{re.escape(HEADER)}\s*=\s*(\d+(?:\.\d+)?)%\s*\(\s*{re.escape(METHOD)}\s*\)",
        visible, flags=re.I)
    if len(headline) != 1:
        raise CaseServiceError("NYU Sep 1 2026 adjusted-payout ERP headline missing/ambiguous")
    if float(headline[0]) != 4.14:
        raise CaseServiceError("NYU Sep 1 adjusted-payout ERP contradicted 4.14%")
    start = re.search(re.escape(HEADER), visible, flags=re.I)
    assert start is not None
    # Anchor alternatives and model's own risk-free reference in the SAME
    # dated author section, excluding any previous-month/next-month update.
    end = re.search(r"(?:Implied ERP in previous month|Downloadable datasets|Day-to-day ERP)",
                    visible[start.end():], flags=re.I)
    segment = visible[start.start(): start.end() + (end.start() if end else 1400)]
    # Real site may include an adjacent Day-to-day ERP link before "previous
    # month", but this section precedes that link.
    if len(segment) > 1900:
        raise CaseServiceError("NYU ERP dated section exceeds isolated boundary")
    alternatives = {
        "trailing_cash_yield": ("Trailing 12 month cash yield", 4.09),
        "average_10yr_cash_flow": ("Average CF yield last 10 years", 6.05),
        "net_cash_yield": ("Net cash yield", 3.80),
        "normalized_earnings_payout": ("Normalized Earnings & Payout", 3.56),
    }
    for key, (label, value) in alternatives.items():
        actual = _exact_pct(segment, label)
        if actual != value:
            raise CaseServiceError(f"NYU ERP alternative model {key} mismatch")
    rf = re.findall(r"US\s+treasury\s+rate\s+of\s+(\d+(?:\.\d+)?)%\s+used\s+as\s+the\s+riskfree",
                    segment, flags=re.I)
    if len(rf) != 1 or float(rf[0]) != 4.75:
        raise CaseServiceError("NYU ERP Sep1 4.75% risk-free reference not source-bound")
    if (date.fromisoformat(AS_OF) - date.fromisoformat(OBSERVED_ON)).days != 13:
        raise CaseServiceError("ERP observation date lag does not match 13 days")
    return {
        "as_of": AS_OF, "observed_on": OBSERVED_ON,
        "model": "IMPLIED_ERP_US_TTM_ADJUSTED_PAYOUT",
        "market": "US", "author": "Aswath Damodaran, NYU Stern",
        "date_header": HEADER, "model_label": METHOD,
        "erp_decimal": ERP, "erp_percent": 4.14,
        "author_model_risk_free_decimal": PUBLISHED_US_TREASURY_RATE,
        "valuation_asof_risk_free_decimal": VALUATION_RF_RATE,
        "model_rf_valuation_rf_difference_basis_points": 22,
        "alternatives_percent": {k: v for k, (_,v) in alternatives.items()},
        "dated_section_exact": segment,
        "methodology_selection": "ASSUMPTION_PENDING_REVIEW",
        "policy": POLICY,
    }


def _sha(obj: dict[str, Any], without: str) -> str:
    value = copy.deepcopy(obj)
    value.pop(without, None)
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _projection(snapshot: dict[str, Any], wacc_input: dict[str, Any]) -> dict[str, Any]:
    validate_external_source_snapshot(snapshot)
    if snapshot["source"]["locator"] != URL or snapshot["source"]["tier"] != "B":
        raise CaseServiceError("untrusted or mismatched NYU ERP original source")
    method = extract_dated_adjusted_erp(snapshot["raw_text"])
    validate_wacc_source_input_against_snapshot(wacc_input, snapshot)
    if (wacc_input.get("metric") != "equity_risk_premium"
        or wacc_input.get("value") != ERP
        or wacc_input.get("unit") != "decimal"
        or wacc_input.get("observed_on") != OBSERVED_ON
        or wacc_input.get("claim_class") != "ASSUMPTION"):
        raise CaseServiceError("NYU implied ERP must remain dated ASSUMPTION")
    proof = {
        "schema_version": SCHEMA, "canonical": False,
        "status": "UNREVIEWED_SOURCE_BOUND_IMPLIED_ERP",
        "method": method,
        "snapshot_sha256": snapshot["snapshot_sha256"],
        "source_body_sha256": snapshot["body"]["sha256"],
        "wacc_input_sha256": wacc_input["input_sha256"],
        "human_review_completed": False, "wacc_package_created": False,
        "methodology_warning": "Damodaran's 4.14% Sep1 adjusted-payout ERP assumes the original 4.75% riskfree rate; Sep14 independent UST nominal 10y rate is 4.97%. Combining those dates/models requires explicit review.",
        "proof_sha256": "",
    }
    proof["proof_sha256"] = _sha(proof, "proof_sha256")
    return proof


def build_erp_source(raw: str, *, captured_at: str) -> dict[str, Any]:
    method = extract_dated_adjusted_erp(raw)
    snapshot = build_external_source_snapshot(
        raw, source_publisher="Aswath Damodaran, NYU Stern",
        source_type="monthly_us_implied_equity_risk_premium",
        source_tier="B", source_locator=URL, captured_at=captured_at)
    inp = build_wacc_source_input_from_snapshot(
        snapshot, metric="equity_risk_premium", value=method["erp_decimal"],
        unit="decimal", observed_on=OBSERVED_ON, claim_class="ASSUMPTION")
    proof = _projection(snapshot, inp)
    return {"snapshot": snapshot, "wacc_input": inp, "proof": proof}


def validate_erp_source_proof(proof: dict[str, Any], inp: dict[str, Any],
                              snapshot: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(proof, dict) or proof.get("schema_version") != SCHEMA:
        raise CaseServiceError("NYU ERP source proof missing or schema mismatch")
    if proof != _projection(snapshot, inp):
        raise CaseServiceError("NYU ERP dated model proof/source SHA mismatch")
    return {"status": "PASS_SOURCE_BOUND_NYU_IMPLIED_ERP_CANDIDATE",
            "method_proof_sha256": proof["proof_sha256"],
            "wacc_input_sha256": inp["input_sha256"],
            "observed_on": OBSERVED_ON, "source_class": "ASSUMPTION",
            "author_model_reference_rf": PUBLISHED_US_TREASURY_RATE,
            "valuation_reference_rf": VALUATION_RF_RATE,
            "human_review_completed": False}


def materialize_erp_source(repo: Path, raw_path: Path) -> dict[str, Any]:
    repo = repo.resolve()
    source_root = (repo / "workspace" / "source_snapshots").resolve()
    path = raw_path.resolve()
    if not path.is_relative_to(source_root) or not path.is_file():
        raise CaseServiceError("NYU ERP raw file must be under local workspace/source_snapshots")
    raw = path.read_text(encoding="utf-8-sig")
    result = build_erp_source(raw, captured_at=datetime.now(timezone.utc).isoformat())
    snapshot, item, proof = result["snapshot"], result["wacc_input"], result["proof"]
    tag = snapshot["snapshot_sha256"][:16]
    out_snapshot = source_root / f"NYU_Damodaran_implied_ERP_20260901_{tag}_snapshot.json"
    out_input = source_root / f"INGR_wacc_equity_risk_premium_20260901_{tag}.json"
    out_proof = source_root / f"INGR_wacc_equity_risk_premium_20260901_{tag}_proof.json"
    if any(p.exists() for p in (out_snapshot, out_input, out_proof)):
        raise CaseServiceError("NYU ERP source capture already exists; no overwrite")
    materialize_external_source_snapshot(snapshot, out_snapshot, root=repo)
    _write(out_input, item)
    _write(out_proof, proof)
    return {
        "status": "REAL_INGR_ERP_METHOD_SOURCE_CANDIDATE_READY_FOR_REVIEW",
        "canonical": False, "as_of": AS_OF, "observed_on": OBSERVED_ON,
        "implied_erp": ERP, "source_class": "ASSUMPTION",
        "source_tier": "B", "method": "IMPLIED_ERP_US_TTM_ADJUSTED_PAYOUT",
        "model_reference_rf": PUBLISHED_US_TREASURY_RATE,
        "valuation_asof_reference_rf": VALUATION_RF_RATE,
        "model_rf_mismatch_basis_points": 22,
        "source_snapshot_sha256": snapshot["snapshot_sha256"],
        "source_body_sha256": snapshot["body"]["sha256"],
        "erp_input_sha256": item["input_sha256"],
        "erp_method_proof_sha256": proof["proof_sha256"],
        "source_snapshot_path": str(out_snapshot),
        "erp_input_path": str(out_input), "method_proof_path": str(out_proof),
        "human_review_completed": False,
        "reviewed_wacc_package": None,
        "next_action": "REVALIDATE_SEVEN_METRIC_INGR_M24_READINESS",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Offline NYU September 1 2026 implied ERP capture")
    p.add_argument("--repo-root", type=Path, default=Path.cwd())
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    try:
        repo = args.repo_root.resolve()
        _git(repo)
        path = args.raw if args.raw.is_absolute() else repo / args.raw
        result = materialize_erp_source(repo, path)
    except (CaseServiceError, ValueError, TypeError, KeyError, OSError) as exc:
        result = {"status": "ERROR", "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 1 if result["status"] == "ERROR" else 0


if __name__ == "__main__":
    raise SystemExit(main())
