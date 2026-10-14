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


def _label_pattern(label: str) -> str:
    """Preserve full method words while tolerating spacing around punctuation.

    HTMLParser intentionally separates adjacent inline text nodes. For
    instance, <b>4.20</b>% (<i>Trailing 12 month</i>, with adjusted payout)
    becomes "4.20 % ( Trailing 12 month , with adjusted payout )".
    """
    return (re.escape(label)
            .replace(r"\ ", r"\s+")
            .replace(",", r"\s*,\s*")
            .replace("&", r"\s*&\s*"))


def _percent_method_pattern(label: str) -> str:
    return rf"(?P<value>\d+(?:\.\d+)?)\s*%\s*\(\s*{_label_pattern(label)}\s*\)"


def _exact_pct(section: str, label: str) -> float:
    matches = re.findall(_percent_method_pattern(label), section, flags=re.I)
    if len(matches) != 1:
        raise CaseServiceError(f"NYU ERP {label} value missing or ambiguous")
    return float(matches[0])


def inspect_erp_html(raw: str) -> dict[str, Any]:
    """Non-promoting diagnostics; never claims original data were approved."""
    visible = _visible(raw)
    headings = re.findall(
        r"Implied ERP on\s+([A-Za-z]+\s+\d{1,2},?\s+20\d{2})\s*=",
        visible, flags=re.I)
    return {
        "status": "ERP_AUTHOR_HTML_DIAGNOSTIC_ONLY",
        "html_bytes": len(raw.encode("utf-8")),
        "raw_body_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "dated_current_headings": headings[:12],
        "dated_headings_total": len(headings),
        "explicit_previous_month_sections": len(re.findall(
            r"Implied ERP in previous month\s*=", visible, flags=re.I)),
        "has_exact_sep_1_heading": any(re.fullmatch(
            r"September\s+1,?\s+2026", h, flags=re.I) for h in headings),
        "has_exact_oct_1_heading": any(re.fullmatch(
            r"October\s+1,?\s+2026", h, flags=re.I) for h in headings),
        "current_adjusted_payout_model_count": len(re.findall(
            rf"Implied\s+ERP\s+on\s+[A-Za-z]+\s+\d{1,2},?\s+20\d{2}\s*="
            rf"\s*{_percent_method_pattern(METHOD)}", visible, flags=re.I)),
        "previous_month_adjusted_payout_model_count": len(re.findall(
            rf"Implied\s+ERP\s+in\s+previous\s+month\s*="
            rf"\s*{_percent_method_pattern(METHOD)}", visible, flags=re.I)),
        "eligible_erp_source_assumed": False,
        "human_review_completed": False,
    }


def _isolated_method_segment(visible: str) -> tuple[str, str, str]:
    """Isolate exactly dated September or October's explicit prior-month panel.

    Date labels must be unique *before* a method match. Otherwise a duplicate
    current heading with a different model could be silently ignored.
    """
    dated_headings = list(re.finditer(
        r"Implied\s+ERP\s+on\s+(?P<date>[A-Za-z]+\s+\d{1,2},?\s+20\d{2})\s*=",
        visible, flags=re.I))
    if len(dated_headings) != 1:
        raise CaseServiceError("NYU exactly one dated current ERP heading required")
    h = dated_headings[0]
    date_header = " ".join(h.group("date").split())
    current = re.match(
        rf"\s*{_percent_method_pattern(METHOD)}", visible[h.end():], flags=re.I)
    if current is None:
        raise CaseServiceError("NYU dated current adjusted-payout model missing/ambiguous")

    if re.fullmatch(r"September\s+1,?\s+2026", date_header, re.I):
        if float(current.group("value")) != 4.14:
            raise CaseServiceError("Sep1 adjusted-payout ERP contradicts 4.14%")
        # A past-month recap can coexist with the September headline; it is
        # not evidence for September's selected adjusted-payout current model.
        tail = visible[h.end() + current.end():]
        cut = re.search(
            r"Implied ERP in previous month|Day-to-day ERP|Downloadable datasets",
            tail, flags=re.I)
        section = visible[h.start(): h.end() + current.end()
                          + (cut.start() if cut else 1400)]
        route = "SEP1_DATED_CURRENT_AUTHOR_HEADLINE"
        cited = date_header
    elif re.fullmatch(r"October\s+1,?\s+2026", date_header, re.I):
        # Exactly one Oct 1 dated author headline identifies the earlier
        # month. Only the explicit previous-month panel attests Sep1's values.
        prev_headings = list(re.finditer(
            r"Implied\s+ERP\s+in\s+previous\s+month\s*=", visible, flags=re.I))
        if len(prev_headings) != 1 or prev_headings[0].start() < h.end():
            raise CaseServiceError(
                "October headline requires exactly one explicit prior-month ERP panel")
        p = prev_headings[0]
        previous = re.match(
            rf"\s*{_percent_method_pattern(METHOD)}", visible[p.end():], flags=re.I)
        if previous is None:
            raise CaseServiceError("October prior-month adjusted-payout method missing")
        if float(previous.group("value")) != 4.14:
            raise CaseServiceError("October previous-month panel is not Sep1 ERP 4.14%")
        tail = visible[p.end() + previous.end():]
        cut = re.search(
            r"Downloadable datasets|Downloadable spreadsheets|Papers:|Other Updates",
            tail, flags=re.I)
        section = visible[p.start(): p.end() + previous.end()
                          + (cut.start() if cut else 1400)]
        route = "OCT1_CURRENT_EXPLICIT_SEP1_PREVIOUS_MONTH_RECAP"
        cited = date_header
    else:
        raise CaseServiceError(
            "current NYU ERP page neither September 1 nor October 1 2026; "
            "previous-month cannot prove Sept 1 date")
    if not 100 <= len(section) <= 1900:
        raise CaseServiceError("dated NYU ERP model panel missing or boundary ambiguous")
    return section, route, cited


def extract_dated_adjusted_erp(raw: str) -> dict[str, Any]:
    visible = _visible(raw)
    segment, route, cited_header = _isolated_method_segment(visible)
    alternatives = {
        "trailing_cash_yield": ("Trailing 12 month cash yield", 4.09),
        "average_10yr_cash_flow": ("Average CF yield last 10 years", 6.05),
        "net_cash_yield": ("Net cash yield", 3.80),
        "normalized_earnings_payout": ("Normalized Earnings & Payout", 3.56),
    }
    for key, (label, expected) in alternatives.items():
        if _exact_pct(segment, label) != expected:
            raise CaseServiceError(f"NYU ERP alternative model {key} mismatch")
    rf = re.findall(
        r"US\s+treasury\s+rate\s+of\s+(\d+(?:\.\d+)?)\s*%"
        r"\s+used\s+as\s+the\s+riskfree", segment, re.I)
    if len(rf) != 1 or float(rf[0]) != 4.75:
        raise CaseServiceError("NYU Sep1 4.75% author risk-free reference missing")
    if (date.fromisoformat(AS_OF) - date.fromisoformat(OBSERVED_ON)).days != 13:
        raise CaseServiceError("ERP date lag not 13 days")
    retrospective = route.startswith("OCT1")
    return {
        "as_of": AS_OF,
        "observed_on": OBSERVED_ON,
        "model": "IMPLIED_ERP_US_TTM_ADJUSTED_PAYOUT",
        "market": "US",
        "author": "Aswath Damodaran, NYU Stern",
        "date_header": HEADER,
        "author_page_current_date_header": cited_header,
        "source_extraction_route": route,
        "source_is_retrospective_asof": retrospective,
        "historical_availability_asof_proven": False,  # download/capture timestamp cannot attest first publication
        "model_label": METHOD,
        "erp_decimal": ERP,
        "erp_percent": 4.14,
        "author_model_risk_free_decimal": PUBLISHED_US_TREASURY_RATE,
        "valuation_asof_risk_free_decimal": VALUATION_RF_RATE,
        "model_rf_valuation_rf_difference_basis_points": 22,
        "alternatives_percent": {k: v for k, (_, v) in alternatives.items()},
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
        "source_extraction_route": proof["method"]["source_extraction_route"],
        "source_is_retrospective_asof": proof["method"]["source_is_retrospective_asof"],
        "historical_availability_asof_proven": proof["method"]["historical_availability_asof_proven"],
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
    p.add_argument("--diagnose", action="store_true", help="Report actual author page dates and hash; never create WACC inputs")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    try:
        repo = args.repo_root.resolve()
        _git(repo)
        path = args.raw if args.raw.is_absolute() else repo / args.raw
        if args.diagnose:
            path = path.resolve()
            if not path.is_relative_to((repo / "workspace" / "source_snapshots").resolve()):
                raise CaseServiceError("ERP diagnostic raw must be user-local workspace source")
            result = inspect_erp_html(path.read_text(encoding="utf-8-sig"))
        else:
            result = materialize_erp_source(repo, path)
    except (CaseServiceError, ValueError, TypeError, KeyError, OSError) as exc:
        result = {"status": "ERROR", "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 1 if result["status"] == "ERROR" else 0


if __name__ == "__main__":
    raise SystemExit(main())
