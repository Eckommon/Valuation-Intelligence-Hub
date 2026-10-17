"""M30-R8M24-TAX.2: offline FY2025 SEC tax bridge evidence, NOT WACC rate.

The source reports an historical U.S. 21% statutory base and a 24.4%
consolidated 2025 effective rate, across foreign/state tax effects.
Neither rate proves a 2026-09-14 consolidated marginal interest shield.
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

URL = "https://www.sec.gov/Archives/edgar/data/1046257/000162828026008603/ingr-20251231.htm"
PERIOD_END = "2025-12-31"
FILED_ON = "2026-02-17"
AS_OF = "2026-09-14"
SCHEMA = "ingr-fy2025-tax-statutory-effective-bridge-proof-v0.1"
IRS_INTEREST_LIMIT_URL = "https://www.irs.gov/instructions/i8990"
EXPECTED_RECONCILIATION = (
    ("federal", r"Federal\s+statutory\s+tax\s+rate",
     r"U\.?S\.?\s+tax\s+effects", 21.0),
    ("effective", r"Effective\s+income\s+tax\s+rate",
     r"$", 24.4),
)


def _hash(v: dict[str, Any], field: str) -> str:
    data = copy.deepcopy(v)
    data.pop(field, None)
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _block(raw: str) -> str:
    visible = _visible(raw)
    if not re.search(r"INGREDION\s+INCORPORATED", visible, re.I):
        raise CaseServiceError("SEC FY2025 10-K issuer missing or contradicted")
    if not re.search(r"fiscal\s+year\s+ended\s+December\s+31\s*,?\s*2025", visible, re.I):
        raise CaseServiceError("SEC FY2025 annual period missing")
    needle = (
        r"The\s+following\s+table\s+reconciles\s+the\s+U\.?S\.?\s+federal"
        r"\s+statutory\s+income\s+tax\s+rate\s+to\s+the\s+Company[’']s"
        r"\s+effective\s+tax\s+rate\s+for\s+2025\s*\.?"
    )
    starts = list(re.finditer(needle, visible, re.I))
    if len(starts) != 1:
        raise CaseServiceError("SEC 2025 statutory/effective reconciliation heading ambiguous")
    tail = visible[starts[0].end():]
    end = re.search(r"\(i\)\s*Illinois\s+and\s+New\s+York", tail, re.I)
    if not end:
        raise CaseServiceError("SEC tax reconciliation 2025 table/footnote boundary missing")
    block = tail[:end.start()]
    if len(block) > 8000 or not re.search(r"2025\s+Amount\s+Percent", block, re.I):
        raise CaseServiceError("SEC tax 2025 year/columns ambiguous")
    return block


def _single_row(block: str, label: str, end_label: str, name: str) -> str:
    found = list(re.finditer(label, block, re.I))
    if len(found) != 1:
        raise CaseServiceError(f"SEC FY2025 tax {name} row missing or repeated")
    start = found[0].end()
    if end_label == "$":
        return block[start:]
    boundary = re.search(end_label, block[start:], re.I)
    if boundary is None:
        raise CaseServiceError(f"SEC FY2025 tax {name} row stop missing")
    return block[start:start+boundary.start()]


def _numbers(text: str, expected: tuple[int, float], name: str) -> None:
    # The SEC Inline-XBRL visible text may insert spaces around periods
    # and percentage punctuation. Require the *exact* USD million
    # numerator and one-decimal rate from the intended dated table row.
    million, pct = expected
    integer, tenth = f"{pct:.1f}".split(".")
    pattern = rf"^\s*\$?\s*{million}\s+{integer}\s*\.\s*{tenth}\s*%?\s*$"
    if not re.fullmatch(pattern, text, re.I):
        raise CaseServiceError(f"SEC tax {name} numeric amount/rate mismatch")


def extract_2025_tax_bridge(raw: str) -> dict[str, Any]:
    table = _block(raw)
    statutory = _single_row(table, EXPECTED_RECONCILIATION[0][1],
                            EXPECTED_RECONCILIATION[0][2], "federal")
    effective = _single_row(table, EXPECTED_RECONCILIATION[1][1],
                            EXPECTED_RECONCILIATION[1][2], "effective")
    _numbers(statutory, (204, 21.0), "federal statutory")
    _numbers(effective, (238, 24.4), "consolidated ETR")
    # This section, not unrelated 2024 comparison pages, must contain
    # evidence of distinct state/foreign effects and tax credits.
    row_anchors = (
        r"State\s+and\s+local\s+income\s+taxes\s*,?\s*net\s+of\s+federal\s+benefit",
        r"Foreign\s+tax\s+credit",
        r"Mexico\s*:",
        r"Germany\s*:",
        r"Colombia",
        r"Other\s+foreign\s+jurisdictions",
        r"Foreign\s+tax\s+effects\s*:",
    )
    for name in row_anchors:
        if len(list(re.finditer(name, table, re.I))) != 1:
            raise CaseServiceError("SEC 2025 tax statutory bridge country/credit rows missing or duplicate")
    state = _single_row(table,
        r"State\s+and\s+local\s+income\s+taxes\s*,?\s*net\s+of\s+federal\s+benefit\s*\(i\)",
        r"Effect\s+of\s+cross-border\s+tax\s+laws",
        "state/local")
    if not re.fullmatch(r"\s*7\s+0\s*\.\s*7\s*", state):
        raise CaseServiceError("SEC 2025 state/local +0.7pp reconciliation contradicted")
    if re.search(r"Tax\s+rate\s+difference\s+on\s+foreign\s+income", table, re.I):
        raise CaseServiceError("SEC 2025 tax bridge confusing pre-2025 comparator year")
    return {
        "entity_id": "SEC_CIK:0001046257",
        "period_end": PERIOD_END, "filing_on": FILED_ON,
        "valuation_as_of": AS_OF,
        "historical_us_federal_statutory_percent": 21.0,
        "historical_us_federal_imputed_provision_usd_millions": 204,
        "historical_consolidated_effective_percent": 24.4,
        "historical_consolidated_tax_provision_usd_millions": 238,
        "historical_etr_minus_us_base_percentage_points": 3.4,
        "historical_state_and_local_effect_percentage_points": 0.7,
        "foreign_country_effects_present": ["Mexico", "Germany", "Colombia", "other"],
        "foreign_tax_credit_effect_present": True,
        "issuer_tax_geography_weights_verified": False,
        "us_section_163j_deductibility_verified": False,
        "other_jurisdictions_interest_deductibility_verified": False,
        "incremental_cash_tax_shield_verified": False,
        "irs_163j_guidance_locator_unverified_original": IRS_INTEREST_LIMIT_URL,
        "selected_2026_wacc_marginal_cash_tax_rate": None,
        "wacc_tax_source_input_created": False,
        "reviewed_wacc_package": None,
        "human_review_completed": False,
        "status": "HOLD_COMPANY_MARGINAL_INTEREST_SHIELD_JURISDICTION_DEDUCTIBILITY_UNPROVEN",
    }


def _projection(snapshot: dict[str, Any]) -> dict[str, Any]:
    validate_external_source_snapshot(snapshot)
    if snapshot["source"]["locator"] != URL or snapshot["source"]["tier"] != "A":
        raise CaseServiceError("SEC FY2025 10-K original locator/tier mismatch")
    method = extract_2025_tax_bridge(snapshot["raw_text"])
    p = {
        "schema_version": SCHEMA,
        "canonical": False,
        "status": "SOURCE_BOUND_2025_TAX_STATUTORY_ETR_BRIDGE_NOT_WACC_RATE",
        "method": method,
        "source_snapshot_sha256": snapshot["snapshot_sha256"],
        "source_body_sha256": snapshot["body"]["sha256"],
        "wacc_tax_source_input_created": False,
        "human_review_completed": False,
        "proof_sha256": "",
    }
    p["proof_sha256"] = _hash(p, "proof_sha256")
    return p


def build_2025_tax_bridge(raw: str, *, captured_at: str) -> dict[str, Any]:
    extract_2025_tax_bridge(raw)
    snapshot = build_external_source_snapshot(
        raw, source_publisher="US SEC / Ingredion Incorporated",
        source_type="2025_form10k_tax_statutory_effective_reconciliation",
        source_tier="A", source_locator=URL, captured_at=captured_at,
    )
    return {"snapshot": snapshot, "proof": _projection(snapshot)}


def validate_2025_tax_bridge(proof: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(proof, dict) or proof.get("schema_version") != SCHEMA:
        raise CaseServiceError("SEC 2025 tax bridge schema missing")
    if proof != _projection(snapshot):
        raise CaseServiceError("SEC tax historic 2025 statutory/ETR original SHA or proof mismatch")
    return {
        "status": "PASS_FY2025_TAX_CONTEXT_MARGINAL_INTEREST_SHIELD_HOLD",
        "proof_sha256": proof["proof_sha256"],
        "wacc_tax_source_input_created": False,
        "human_review_completed": False,
    }


def materialize_2025_tax_bridge(repo: Path, path: Path) -> dict[str, Any]:
    repo = repo.resolve()
    base = (repo / "workspace" / "source_snapshots").resolve()
    raw = path.resolve()
    if not raw.is_relative_to(base) or not raw.is_file():
        raise CaseServiceError("2025 SEC 10-K original must be inside user-local source_snapshots")
    data = build_2025_tax_bridge(
        raw.read_text(encoding="utf-8-sig"),
        captured_at=datetime.now(timezone.utc).isoformat(),
    )
    snapshot, proof = data["snapshot"], data["proof"]
    token = snapshot["body"]["sha256"][:16]
    target_source = base / f"INGR_2025_tax_reconcile_{token}_snapshot.json"
    target_proof = base / f"INGR_2025_tax_reconcile_{token}_proof.json"
    if target_source.exists() or target_proof.exists():
        raise CaseServiceError("SEC 2025 tax original already captured; no overwrite")
    materialize_external_source_snapshot(snapshot, target_source, root=repo)
    _write(target_proof, proof)
    return {
        "status": "REAL_INGR_2025_TAX_STATUTORY_EFFECTIVE_BRIDGE_CAPTURED_METHOD_HOLD",
        "canonical": False,
        "source_original_body_sha256": snapshot["body"]["sha256"],
        "snapshot_sha256": snapshot["snapshot_sha256"],
        "proof_sha256": proof["proof_sha256"],
        "snapshot_path": str(target_source), "proof_path": str(target_proof),
        "federal_2025_statutory_percent": 21.0,
        "global_2025_effective_percent": 24.4,
        "2026_wacc_marginal_rate_selected": None,
        "wacc_tax_source_input_created": False,
        "human_review_completed": False,
        "next_action": "GATHER_2026_MARGINAL_TAX_JURISDICTION_AND_163J_INTEREST_SHIELD",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="2025 SEC tax bridge; no WACC tax rate")
    p.add_argument("--repo-root", type=Path, default=Path.cwd())
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    try:
        repo = args.repo_root.resolve()
        _git(repo)
        file = args.raw if args.raw.is_absolute() else repo / args.raw
        result = materialize_2025_tax_bridge(repo, file)
    except (CaseServiceError, OSError, ValueError, TypeError, KeyError) as exc:
        result = {"status": "ERROR", "error": str(exc)}
    print(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False))
    return int(result["status"] == "ERROR")


if __name__ == "__main__":
    raise SystemExit(main())
