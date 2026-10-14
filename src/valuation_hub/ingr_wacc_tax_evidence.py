"""M30-R8M24-TAX.1: exact SEC 2026 Q2 tax observations, NOT WACC tax-rate.

GAAP/adjusted effective income-tax rates and management guidance are not
automatically the marginal cash tax rate for WACC. This module creates
source-locked unreviewed context ONLY, never a WACC source input.
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
    build_external_source_snapshot, materialize_external_source_snapshot,
    validate_external_source_snapshot,
)
from valuation_hub.ingr_r8_m23_execution import _git, _write
from valuation_hub.ingr_wacc_damodaran_erp import _visible

URL = "https://www.sec.gov/Archives/edgar/data/1046257/000162828026052104/ingr-20260630xexx99.htm"
AS_OF = "2026-09-14"
PUBLISHED_ON = "2026-08-04"
QUARTER_END = "2026-06-30"
SCHEMA = "ingr-effective-tax-observation-proof-v0.1"

Q2 = (
    r"The\s+reported\s+and\s+adjusted\s+effective\s+tax\s+rates\s+for\s+the"
    r"\s+second\s+quarter\s+were\s+(?P<gaap>\d+(?:\.\d+)?)\s*%\s+and"
    r"\s+(?P<adjusted>\d+(?:\.\d+)?)\s*%\s*,\s*compared\s+to"
    r"\s+(?P<prior_gaap>\d+(?:\.\d+)?)\s*%\s+and"
    r"\s+(?P<prior_adjusted>\d+(?:\.\d+)?)\s*%"
)
YEAR = (
    r"For\s+full-year\s+2026\s*,?\s*the\s+Company\s+expects\s+a"
    r"\s+reported\s+effective\s+tax\s+rate\s+of"
    r"\s+(?P<gaap_low>\d+(?:\.\d+)?)\s*%\s+to"
    r"\s+(?P<gaap_high>\d+(?:\.\d+)?)\s*%\s+and\s+still\s+expects\s+an"
    r"\s+adjusted\s+effective\s+tax\s+rate\s+of"
    r"\s+(?P<adjusted_low>\d+(?:\.\d+)?)\s*%\s+to"
    r"\s+(?P<adjusted_high>\d+(?:\.\d+)?)\s*%"
)


def _one(text: str, pattern: str, name: str) -> re.Match[str]:
    matches = list(re.finditer(pattern, text, re.I))
    if len(matches) != 1:
        raise CaseServiceError(f"SEC tax {name} passage absent/duplicated")
    return matches[0]


def extract_tax_observations(raw: str) -> dict[str, Any]:
    text = _visible(raw)
    if not re.search(r"Ingredion\s+Incorporated\s+reports\s+second\s+quarter\s+2026\s+results", text, re.I):
        raise CaseServiceError("SEC release issuer/quarter identity missing")
    if not re.search(r"Other\s+Financial\s+Items", text, re.I):
        raise CaseServiceError("SEC tax summary section missing")
    if not re.search(r"Full-Year\s+2026\s+Outlook", text, re.I):
        raise CaseServiceError("SEC tax annual guidance heading missing")
    q2 = _one(text, Q2, "Q2 2026 observed")
    year = _one(text, YEAR, "2026 guidance")
    observed = {k: float(v) for k, v in q2.groupdict().items()}
    guidance = {k: float(v) for k, v in year.groupdict().items()}
    if observed != {"gaap": 33.7, "adjusted": 27.2,
                    "prior_gaap": 23.6, "prior_adjusted": 27.2}:
        raise CaseServiceError("SEC tax reported/adjusted observed values contradicted")
    if guidance != {"gaap_low": 27.4, "gaap_high": 28.9,
                    "adjusted_low": 26.0, "adjusted_high": 27.5}:
        raise CaseServiceError("SEC tax GAAP/adjusted guidance values contradicted")
    if not re.search(r"Pakistan\s+business\s+and\s+the\s+change\s+in\s+value\s+of\s+the\s+Mexican\s+peso", text[q2.end():q2.end()+600], re.I):
        raise CaseServiceError("SEC tax special-item/FX context absent")
    if not re.search(r"excludes\s+acquisition-related\s+integration\s+and\s+restructuring\s+costs", text[year.end():year.end()+800], re.I):
        raise CaseServiceError("SEC annual guidance exclusion context absent")
    return {
        "entity_id": "SEC_CIK:0001046257", "as_of": AS_OF,
        "filing_on": PUBLISHED_ON, "quarter_end": QUARTER_END,
        "quarter_2026_effective_rates_percent": {
            "gaap": observed["gaap"], "adjusted_non_gaap": observed["adjusted"]},
        "quarter_2025_comparator_percent": {
            "gaap": observed["prior_gaap"], "adjusted_non_gaap": observed["prior_adjusted"]},
        "full_year_2026_guidance_percent": {
            "gaap": [guidance["gaap_low"], guidance["gaap_high"]],
            "adjusted_non_gaap": [guidance["adjusted_low"], guidance["adjusted_high"]]},
        "difference_semantics": "HISTORICAL_ETR_VERSUS_EXPECTED_ADJUSTED_ETR_NOT_WACC_MARGINAL_CASH_TAX",
        "special_items": "Pakistan divestiture / Mexican peso FX / acquisition integration exclusions",
        "tax_rate_wacc_numeric_selected": None,
        "wacc_tax_source_input_created": False,
        "human_review_completed": False,
        "status": "HOLD_WACC_MARGINAL_TAX_METHODOLOGY_NOT_EVIDENCED",
    }


def _sha(payload: dict[str, Any], excluded: str) -> str:
    obj = copy.deepcopy(payload)
    obj.pop(excluded, None)
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _projection(snapshot: dict[str, Any]) -> dict[str, Any]:
    validate_external_source_snapshot(snapshot)
    if snapshot["source"]["locator"] != URL or snapshot["source"]["tier"] != "A":
        raise CaseServiceError("SEC 8-K tax original URL/tier mismatch")
    extracted = extract_tax_observations(snapshot["raw_text"])
    out = {
        "schema_version": SCHEMA, "canonical": False,
        "status": "SOURCE_BOUND_TAX_OBSERVATIONS_METHOD_HOLD",
        "source_snapshot_sha256": snapshot["snapshot_sha256"],
        "source_body_sha256": snapshot["body"]["sha256"],
        "method": extracted,
        "wacc_tax_source_input_created": False,
        "reviewed_wacc_package": None,
        "human_review_completed": False,
        "proof_sha256": "",
    }
    out["proof_sha256"] = _sha(out, "proof_sha256")
    return out


def build_tax_evidence(raw: str, *, captured_at: str) -> dict[str, Any]:
    extract_tax_observations(raw)
    snapshot = build_external_source_snapshot(
        raw, source_publisher="US SEC / Ingredion Incorporated",
        source_type="2026q2_8k_ex99_effective_tax_guidance_context",
        source_tier="A", source_locator=URL, captured_at=captured_at)
    return {"snapshot": snapshot, "proof": _projection(snapshot)}


def validate_tax_evidence(proof: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(proof, dict) or proof.get("schema_version") != SCHEMA:
        raise CaseServiceError("SEC tax observation proof schema missing")
    if proof != _projection(snapshot):
        raise CaseServiceError("SEC tax observation/source SHA or semantic claims mismatch")
    return {
        "status": "PASS_SOURCE_BOUND_TAX_OBSERVATIONS_MARGINAL_METHOD_HOLD",
        "source_snapshot_sha256": snapshot["snapshot_sha256"],
        "proof_sha256": proof["proof_sha256"],
        "wacc_tax_source_input_created": False,
        "human_review_completed": False,
    }


def materialize_tax_evidence(repo: Path, raw_path: Path) -> dict[str, Any]:
    repo = repo.resolve()
    root = (repo / "workspace" / "source_snapshots").resolve()
    path = raw_path.resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise CaseServiceError("SEC tax original HTML must be user-local workspace/source_snapshots")
    data = build_tax_evidence(path.read_text(encoding="utf-8-sig"),
                              captured_at=datetime.now(timezone.utc).isoformat())
    snapshot, proof = data["snapshot"], data["proof"]
    tag = snapshot["body"]["sha256"][:16]
    originals = root / f"INGR_2026Q2_tax_ex99_{tag}_snapshot.json"
    method = root / f"INGR_2026Q2_tax_ex99_{tag}_proof.json"
    if originals.exists() or method.exists():
        raise CaseServiceError("SEC tax observation source already captured; no overwrite")
    materialize_external_source_snapshot(snapshot, originals, root=repo)
    _write(method, proof)
    return {
        "status": "REAL_INGR_TAX_OBSERVATIONS_CAPTURED_METHOD_HOLD",
        "canonical": False, "source_snapshot_path": str(originals),
        "method_proof_path": str(method),
        "source_body_sha256": snapshot["body"]["sha256"],
        "source_snapshot_sha256": snapshot["snapshot_sha256"],
        "proof_sha256": proof["proof_sha256"],
        "wacc_tax_source_input_created": False,
        "human_review_completed": False,
        "next_action": "SOURCE_BIND_WACC_MARGINAL_CASH_TAX_POLICY_BEFORE_TAX_RATE_INPUT",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Offline SEC 8-K effective tax observations, no WACC input")
    p.add_argument("--repo-root", type=Path, default=Path.cwd())
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    try:
        root = args.repo_root.resolve()
        _git(root)
        path = args.raw if args.raw.is_absolute() else root / args.raw
        result = materialize_tax_evidence(root, path)
    except (CaseServiceError, TypeError, ValueError, KeyError, OSError) as exc:
        result = {"status": "ERROR", "error": str(exc)}
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 1 if result["status"] == "ERROR" else 0


if __name__ == "__main__":
    raise SystemExit(main())
