"""M30-R8M24: source-conscious local Ingredion WACC readiness preflight.

This module never authors market rates, reviewer identity, reviewed WACC,
canonical Draft, or an M24 binding from an unreviewed source input.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.external_source import validate_external_source_snapshot
from valuation_hub.ingr_r8_m23_execution import (
    AS_OF, CASE_ID, _git, _read, _scan, _write,
)
from valuation_hub.r8_assumption_proposal import validate_r6_v3_proposal
from valuation_hub.sec_live import validate_source_snapshot
from valuation_hub.wacc_assumption import (
    FRESHNESS_MAX_AGE_DAYS, REQUIRED_METRICS, REVIEWABLE_TIERS,
    build_wacc_candidate, validate_wacc_source_input,
)

M23_V03_SHA = "5017a832d68f7a013829f4bc86679f0bcd8f40480f6954bd4443e6ae6400c472"
M23_V02_SHA = "42b8d691a3617235d52179bb56340ba0a7f2fca055a8b608f8eda5c44eb6d378"
M23_RUN = "r8_m23_20261014T141303035707Z"
SOURCE_INPUT_SCHEMA = "wacc-source-input-v0.1"
SOURCE_SNAPSHOT_SCHEMAS = {"external-source-snapshot-v0.1", "source-snapshot-v0.1"}
EQUITY_MARKET_VALUE_PROOF_SCHEMA = "ingr-market-cap-proxy-proof-v0.1"
ERP_PROOF_SCHEMA = "wacc-erp-method-source-proof-v0.1"
DEBT_MV_PROOF_SCHEMA = "ingr-debt-market-value-proxy-proof-v0.1"
BETA_PROOF_SCHEMA = "ingr-weekly-price-beta-method-proof-v0.1"
YAHOO_BETA_PROOF_SCHEMA = "ingr-yahoo-chart-weekly-price-beta-proof-v0.1"
BETA_LOW_R_SQUARED_REVIEW_THRESHOLD = 0.10  # QA advisory only; NOT an acceptance/failure rule


def _beta_regression_risk(r_squared: float) -> dict[str, Any]:
    # Provenance computation (upstream proof) supplies R². The 0.10
    # cutoff is a transparent reviewer triage policy, NOT a statistical
    # significance test or a universal cost-of-capital convention.
    if not isinstance(r_squared, (float, int)) or isinstance(r_squared, bool):
        raise CaseServiceError("beta regression R² must be finite numeric")
    if not 0 <= r_squared <= 1:
        raise CaseServiceError("beta regression R² outside [0,1]")
    return {
        "status": "LOW_EXPLANATORY_POWER_REVIEW_REQUIRED"
                  if r_squared < BETA_LOW_R_SQUARED_REVIEW_THRESHOLD
                  else "EXPLANATORY_POWER_REVIEW_PENDING",
        "r_squared": r_squared,
        "comparison_threshold": BETA_LOW_R_SQUARED_REVIEW_THRESHOLD,
        "threshold_semantics": "INTERNAL_NON_BLOCKING_REVIEW_TRIAGE_NOT_STATISTICAL_SIGNIFICANCE",
        "equity_return_variance_explained": r_squared,
        "price_only_total_return_adjustment_missing": True,
        "historical_source_availability_asof_proven": False,
        "beta_source_candidate_not_reviewed_wacc": True,
    }



def _m23(repo: Path, run_dir: Path) -> dict[str, Any]:
    path = run_dir / "m23_r6_assumption_v03.json"
    if not path.is_file():
        raise CaseServiceError(f"actual approved M23 v0.3 missing: {path}")
    proposal = _read(path)
    validate_r6_v3_proposal(proposal)
    if proposal.get("proposal_sha256") != M23_V03_SHA:
        raise CaseServiceError("local M23 proposal SHA is not the user-validated real INGR result")
    base = proposal["base_proposal"]
    if base.get("proposal_sha256") != M23_V02_SHA:
        raise CaseServiceError("M23 SEC debt scope-bridged v0.2 SHA mismatch")
    if (
        proposal["identity"].get("entity_id") != "SEC_CIK:0001046257"
        or proposal["identity"].get("financial_scope") != "AS_REPORTED"
        or proposal["identity"].get("monetary_unit") != "USD"
        or proposal["policy"].get("as_of") != AS_OF
    ):
        raise CaseServiceError("real M23 INGREDIENT entity/scope/currency/as-of mismatch")
    share = next((x for x in proposal["draft_input_matrix"] if x["field"] == "equity.diluted_shares"), None)
    if not share or share.get("source_class") != "ASSUMPTION":
        raise CaseServiceError("M23 shares must remain R6 ASSUMPTION")
    return proposal


def _validate_source_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    schema = payload.get("schema_version")
    if schema == "external-source-snapshot-v0.1":
        return validate_external_source_snapshot(payload)
    if schema == "source-snapshot-v0.1":
        return validate_source_snapshot(payload)
    raise CaseServiceError("WACC source reference does not point to a supported immutable snapshot")


def _origin_check(input_payload: dict[str, Any], snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    src = input_payload["source"]
    linked = [s for s in snapshots if s.get("snapshot_sha256") == src["source_sha256"]]
    if not linked:
        return {"status": "SOURCE_RAW_BYTES_NOT_LOCALLY_VERIFIED", "source_sha256": src["source_sha256"]}
    if any(x != linked[0] for x in linked[1:]):
        raise CaseServiceError("conflicting immutable snapshots with the same WACC source SHA")
    _validate_source_snapshot(linked[0])
    raw_source = linked[0].get("source", {})
    locator = raw_source.get("locator") or raw_source.get("final_locator")
    if locator != src["locator"]:
        raise CaseServiceError("WACC source locator differs from exact immutable snapshot locator")
    # A matching snapshot authenticates bytes/URL but does NOT prove that the
    # precise numerical WACC claim is present. Independent review is required.
    return {"status": "SNAPSHOT_VERIFIED_VALUE_REQUIRES_REVIEW",
            "source_sha256": src["source_sha256"]}


def _market_cap_proof(input_payload: dict[str, Any], snapshots: list[dict[str, Any]],
                      proofs: list[dict[str, Any]]) -> dict[str, Any]:
    from valuation_hub.ingr_wacc_equity_market_value import validate_market_cap_proxy
    matching = [x for x in proofs if x.get("wacc_input_sha256") == input_payload.get("input_sha256")]
    if not matching:
        return {"status": "EQUITY_MARKET_VALUE_TWO_SOURCE_PROOF_MISSING"}
    if len(matching) != 1:
        raise CaseServiceError("duplicate or conflicting market-cap proxy proofs")
    proof = matching[0]
    price = [x for x in snapshots if x.get("snapshot_sha256") == proof.get("source_price_snapshot_sha256")]
    sec = [x for x in snapshots if x.get("snapshot_sha256") == proof.get("source_sec_snapshot_sha256")]
    if len(price) != 1 or len(sec) != 1:
        return {"status": "EQUITY_MARKET_VALUE_SUPPORTING_SOURCE_MISSING"}
    validate_market_cap_proxy(proof, input_payload, price[0], sec[0])
    return {"status": "EQUITY_MARKET_VALUE_TWO_SOURCE_PROXY_VERIFIED_REVIEW_PENDING",
            "share_lag_days": proof["share_lag_days"],
            "shares_source_date": proof["reported_common_shares"]["observed_on"],
            "method_sha256": proof["proof_sha256"],
            "share_class": "ASSUMPTION"}


def _erp_method_proof(item: dict[str, Any], snapshots: list[dict[str, Any]],
                      proofs: list[dict[str, Any]]) -> dict[str, Any]:
    from valuation_hub.ingr_wacc_damodaran_erp import validate_erp_source_proof
    matches = [p for p in proofs if p.get("wacc_input_sha256") == item.get("input_sha256")]
    if not matches:
        return {"status": "ERP_EXPLICIT_MODEL_METHOD_PROOF_MISSING"}
    if len(matches) != 1:
        raise CaseServiceError("ERP model proof duplicated or conflicting")
    snapshot = [s for s in snapshots if s.get("snapshot_sha256") == matches[0].get("snapshot_sha256")]
    if len(snapshot) != 1:
        return {"status": "ERP_ORIGINAL_AUTHOR_SNAPSHOT_MISSING"}
    checked = validate_erp_source_proof(matches[0], item, snapshot[0])
    return {"status": "ERP_SOURCE_MODEL_PROOF_VERIFIED_REVIEW_PENDING",
            "proof_sha256": checked["method_proof_sha256"],
            "observed_on": checked["observed_on"],
            "source_class": "ASSUMPTION",
            "author_reference_rf": checked["author_model_reference_rf"],
            "valuation_rf": checked["valuation_reference_rf"],
            "rf_date_convention": "AUTHOR_SEP1_4.75_PERCENT_VERSUS_VALUATION_SEP14_4.97_PERCENT",
            "source_is_retrospective_asof": matches[0]["method"]["source_is_retrospective_asof"],
            "historical_availability_asof_proven": matches[0]["method"]["historical_availability_asof_proven"]}


def _debt_mv_method_proof(item: dict[str, Any], snapshots: list[dict[str, Any]],
                          proofs: list[dict[str, Any]]) -> dict[str, Any]:
    from valuation_hub.ingr_wacc_debt_market_value import validate_debt_mv_proof
    matches = [p for p in proofs if p.get("wacc_input_sha256") == item.get("input_sha256")]
    if not matches:
        return {"status": "DEBT_MV_EXPLICIT_METHOD_PROOF_MISSING"}
    if len(matches) != 1:
        raise CaseServiceError("debt MV method proof duplicated or conflicting")
    origin = [s for s in snapshots if s.get("snapshot_sha256") == matches[0].get("snapshot_sha256")]
    if len(origin) != 1:
        return {"status": "DEBT_MV_SEC_ORIGINAL_SNAPSHOT_MISSING"}
    checked = validate_debt_mv_proof(matches[0], item, origin[0])
    return {"status": "DEBT_MV_SOURCE_MODEL_PROOF_VERIFIED_REVIEW_PENDING",
            "proof_sha256": checked["method_proof_sha256"],
            "observed_on": checked["observed_on"],
            "source_class": "ASSUMPTION",
            "method": matches[0]["method"]["method"],
            "book_value_usd_millions": matches[0]["method"]["total_carrying_value_usd_millions"],
            "market_value_proxy_usd_millions": matches[0]["method"]["debt_mv_proxy_usd_millions"],
            "human_review_completed": False}


def _beta_method_proof(item: dict[str, Any], sources: list[dict[str, Any]],
                       stooq_proofs: list[dict[str, Any]],
                       yahoo_proofs: list[dict[str, Any]]) -> dict[str, Any]:
    from valuation_hub.ingr_wacc_levered_beta import validate_beta_method_proof
    from valuation_hub.ingr_wacc_yahoo_chart_beta import validate_yahoo_beta_proof

    stooq = [p for p in stooq_proofs if p.get("wacc_input_sha256") == item.get("input_sha256")]
    yahoo = [p for p in yahoo_proofs if p.get("wacc_input_sha256") == item.get("input_sha256")]
    if len(stooq) + len(yahoo) == 0:
        return {"status": "BETA_TWO_SOURCE_PRICE_REGRESSION_PROOF_MISSING"}
    if len(stooq) + len(yahoo) != 1:
        raise CaseServiceError("beta proofs duplicated/ambiguous across price providers")
    proof = (stooq or yahoo)[0]
    issuers = [s for s in sources if s.get("snapshot_sha256") == proof.get("issuer_snapshot_sha256")]
    markets = [s for s in sources if s.get("snapshot_sha256") == proof.get("market_snapshot_sha256")]
    if len(issuers) != 1 or len(markets) != 1:
        return {"status": "BETA_ORIGINAL_ISSUER_OR_MARKET_SNAPSHOT_MISSING"}
    if stooq:
        checked = validate_beta_method_proof(proof,item,issuers[0],markets[0])
        return {"status": "BETA_PRICE_ONLY_TWO_SOURCE_PROOF_VERIFIED_REVIEW_PENDING",
                "proof_sha256": checked["method_proof_sha256"],
                "beta": checked["beta"], "weekly_returns": checked["n_weekly_returns"],
                "r_squared": checked["r_squared"],
                "regression_quality": _beta_regression_risk(checked["r_squared"]),
                "return_basis": "PRICE_ONLY_NOT_TOTAL_RETURN",
                "provider": "Stooq original CSV",
                "historical_availability_asof_proven": False,
                "human_review_completed": False}
    checked = validate_yahoo_beta_proof(proof,item,issuers[0],markets[0])
    return {"status": "BETA_YAHOO_PRICE_ONLY_TWO_SOURCE_PROOF_VERIFIED_REVIEW_PENDING",
            "proof_sha256": checked["method_proof_sha256"],
            "beta": checked["beta"], "weekly_returns": checked["weekly_returns"],
            "r_squared": proof["method"]["r_squared"],
            "regression_quality": _beta_regression_risk(proof["method"]["r_squared"]),
            "return_basis": "PRICE_ONLY_NOT_TOTAL_RETURN",
            "provider": "Yahoo v8 chart original JSON",
            "historical_availability_asof_proven": False,
            "human_review_completed": False}

def _rows(items: list[dict[str, Any]], sources: list[dict[str, Any]],
          proofs: list[dict[str, Any]] | None = None,
          erp_proofs: list[dict[str, Any]] | None = None,
          debt_mv_proofs: list[dict[str, Any]] | None = None,
          beta_proofs: list[dict[str, Any]] | None = None,
          yahoo_beta_proofs: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    as_date = date.fromisoformat(AS_OF)
    for metric in REQUIRED_METRICS:
        matching = [x for x in items if x.get("metric") == metric]
        unique = {x.get("input_sha256") for x in matching}
        if not matching:
            out.append({"metric": metric, "status": "MISSING_SOURCE_INPUT",
                        "max_age_days": FRESHNESS_MAX_AGE_DAYS[metric]})
            continue
        if len(unique) != 1 or any(x != matching[0] for x in matching[1:]):
            out.append({"metric": metric, "status": "AMBIGUOUS_CONFLICTING_INPUTS",
                        "source_input_count": len(matching)})
            continue
        item = matching[0]
        validate_wacc_source_input(item)
        observed = date.fromisoformat(item["observed_on"])
        age = (as_date - observed).days
        tier = item["source"]["tier"]
        provenance = _origin_check(item, sources)
        status = ("FUTURE_DATED_BLOCKED" if age < 0
                  else "STALE_BLOCKED" if age > FRESHNESS_MAX_AGE_DAYS[metric]
                  else "UNREVIEWABLE_TIER_BLOCKED" if tier not in REVIEWABLE_TIERS
                  else "FRESH_SOURCE_INPUT_CANDIDATE")
        if status == "FRESH_SOURCE_INPUT_CANDIDATE" and provenance["status"] != "SNAPSHOT_VERIFIED_VALUE_REQUIRES_REVIEW":
            status = "SOURCE_BYTES_UNVERIFIED"
        if metric == "equity_risk_premium" and status == "FRESH_SOURCE_INPUT_CANDIDATE":
            # A standalone source-attested number does not justify choosing
            # any given US ERP estimator, date convention or cash payout method.
            method = _erp_method_proof(item, sources, erp_proofs or [])
            provenance["erp_method"] = method
            if method["status"] != "ERP_SOURCE_MODEL_PROOF_VERIFIED_REVIEW_PENDING":
                status = method["status"]
        if metric == "levered_beta" and status == "FRESH_SOURCE_INPUT_CANDIDATE":
            # A numeric beta in a vendor snapshot is not an independently
            # verified issuer-specific regression. Enforce original paired
            # price-series SHA, date alignment and price-only model caveats.
            method = _beta_method_proof(item,sources,beta_proofs or [],yahoo_beta_proofs or [])
            provenance["beta_method"] = method
            if method["status"] not in {"BETA_PRICE_ONLY_TWO_SOURCE_PROOF_VERIFIED_REVIEW_PENDING",
                                        "BETA_YAHOO_PRICE_ONLY_TWO_SOURCE_PROOF_VERIFIED_REVIEW_PENDING"}:
                status = method["status"]
        if metric == "debt_market_value" and status == "FRESH_SOURCE_INPUT_CANDIDATE":
            # A SEC snapshot with a debt number is not proof of total debt
            # market value. Enforce separately reconstructed Level-2 and short-
            # term fair-value approximation with undrawn facilities excluded.
            method = _debt_mv_method_proof(item, sources, debt_mv_proofs or [])
            provenance["debt_mv_method"] = method
            if method["status"] != "DEBT_MV_SOURCE_MODEL_PROOF_VERIFIED_REVIEW_PENDING":
                status = method["status"]
        if metric == "equity_market_value" and status == "FRESH_SOURCE_INPUT_CANDIDATE":
            # Price alone never proves current common-share count. Require
            # source-revalidated SEC dated count and explicitly 40-day lagged
            # proxy method, not the separate R6 diluted-share ASSUMPTION.
            method = _market_cap_proof(item, sources, proofs or [])
            provenance["market_cap_method"] = method
            if method["status"] != "EQUITY_MARKET_VALUE_TWO_SOURCE_PROXY_VERIFIED_REVIEW_PENDING":
                status = method["status"]
        out.append({"metric": metric, "status": status,
                    "observed_on": item["observed_on"], "age_days": age,
                    "max_age_days": FRESHNESS_MAX_AGE_DAYS[metric],
                    "claim_class": item["claim_class"], "tier": tier,
                    "input_sha256": item["input_sha256"],
                    "provenance": provenance})
    return out


def run_wacc_readiness(*, repo_root: Path, artifact_root: Path | None = None,
                       m23_run_dir: Path | None = None,
                       enforce_git: bool = True) -> dict[str, Any]:
    repo = repo_root.resolve()
    git_state = _git(repo) if enforce_git else {"branch": "test", "head": "git-disabled"}
    root = (artifact_root or (repo / "workspace")).resolve()
    if not root.is_relative_to((repo / "workspace").resolve()):
        raise CaseServiceError("WACC preflight must use gitignored workspace only")
    m23_dir = (m23_run_dir or (root / "execution_artifacts" / CASE_ID / M23_RUN))
    if not m23_dir.is_absolute():
        m23_dir = repo / m23_dir
    m23_dir = m23_dir.resolve()
    if not m23_dir.is_relative_to(root):
        raise CaseServiceError("M23 evidence path outside controlled workspace")
    m23 = _m23(repo, m23_dir)
    artifacts = _scan(root)
    inputs = [x.payload for x in artifacts if x.payload.get("schema_version") == SOURCE_INPUT_SCHEMA]
    snapshots = [x.payload for x in artifacts if x.payload.get("schema_version") in SOURCE_SNAPSHOT_SCHEMAS]
    proofs = [x.payload for x in artifacts if x.payload.get("schema_version") == EQUITY_MARKET_VALUE_PROOF_SCHEMA]
    erp_proofs = [x.payload for x in artifacts if x.payload.get("schema_version") == ERP_PROOF_SCHEMA]
    debt_mv_proofs = [x.payload for x in artifacts if x.payload.get("schema_version") == DEBT_MV_PROOF_SCHEMA]
    beta_proofs = [x.payload for x in artifacts if x.payload.get("schema_version") == BETA_PROOF_SCHEMA]
    yahoo_beta_proofs = [x.payload for x in artifacts if x.payload.get("schema_version") == YAHOO_BETA_PROOF_SCHEMA]
    rows = _rows(inputs, snapshots, proofs, erp_proofs, debt_mv_proofs, beta_proofs, yahoo_beta_proofs)
    complete = all(x["status"] == "FRESH_SOURCE_INPUT_CANDIDATE" for x in rows)
    result = {
        "status": "REAL_INGR_M24_WACC_SOURCE_CANDIDATES_READY_FOR_REVIEW" if complete
                  else "HOLD_REAL_INGR_M24_WACC_INPUT_GAPS",
        "canonical": False, "as_of": AS_OF, "entity_id": m23["identity"]["entity_id"],
        "financial_scope": m23["identity"]["financial_scope"], "currency": "USD",
        "git": git_state,
        "source_m23_v03_proposal_sha256": M23_V03_SHA,
        "source_m23_v02_proposal_sha256": M23_V02_SHA,
        "source_r6_shares_class": "ASSUMPTION",
        "metrics_required": list(REQUIRED_METRICS),
        "metrics_ready": sum(x["status"] == "FRESH_SOURCE_INPUT_CANDIDATE" for x in rows),
        "metrics": rows,
        "reviewed_wacc_package": None,
        "human_review_completed": False,
        "draft_v04_created": False,
        "next_action": "GATHER_DATE_ALIGNED_SOURCE_BOUND_WACC_INPUTS" if not complete
                       else "HUMAN_REVIEW_OF_INDEPENDENTLY_VERIFIED_WACC_CLAIMS",
        "warning": "Exact snapshot SHA/URL alone does not attest a numerical WACC claim. Real reviewer and exact scenario coverage still required.",
    }
    output_dir = root / "execution_artifacts" / CASE_ID / (
        "r8_m24_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    )
    output = output_dir / "wacc_source_readiness.json"
    _write(output, result)
    return {**result, "output": str(output)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Real INGR M24 WACC source readiness, no auto-review")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--m23-run-dir", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = run_wacc_readiness(repo_root=args.repo_root, artifact_root=args.artifact_root,
                                    m23_run_dir=args.m23_run_dir)
    except (CaseServiceError, ValueError, TypeError, KeyError, OSError) as exc:
        result = {"status": "ERROR", "error": str(exc)}
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 1 if result["status"] == "ERROR" else 0


if __name__ == "__main__":
    raise SystemExit(main())
