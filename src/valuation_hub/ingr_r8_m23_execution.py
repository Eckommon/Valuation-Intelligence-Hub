"""Fail-closed user-local Ingredion M30-R8 → real M23 handoff.

Only audited, gitignored local files are consumed. No SEC fetch, synthetic
substitution, admission, Draft mutation, or authority upgrade is performed.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.debt_draft_binding_m30 import (
    build_binding_proposal_with_sec_aggregate_debt,
    validate_binding_proposal_sec_aggregate,
)
from valuation_hub.financial_normalization import validate_financial_observation
from valuation_hub.r8_assumption_proof import validate_r6_binding_proof
from valuation_hub.r8_assumption_proposal import (
    build_r6_v3_proposal,
    validate_r6_v3_proposal,
)
from valuation_hub.sec_aggregate_debt import (
    build_sec_aggregate_debt_binding_context,
    validate_reviewed_sec_aggregate_debt,
    validate_sec_aggregate_debt_binding_context,
)

CASE_ID = "US_INGR_INGREDION"
AS_OF = "2026-09-14"
ENTITY_ID = "SEC_CIK:0001046257"
R6_AND_CASH_SCOPE = "AS_REPORTED"
SEC_DEBT_SCOPE = "CFS"
CURRENCY = "USD"
EXPECTED_CASH_VALUE = 948_000_000
EXPECTED_DEBT_VALUE = 1_783_000_000
EXPECTED_SHARES = 63_900_000
R8_PROOF_SHA = "8abc7cf93fd3e2bf93422e915ab4fe5c6ebad2faef34a0a2f7596038eda55cc9"
R6_PACKAGE_SHA = "ae1e6612b67a56e568b9a9bcd6588c8765240a196ab395aa2dc86887b027e3af"
CASH_SHA = "c4c7cc9768835cd4ada7129f1ca33d6f7cf9b08a795e08d0085639f90d4551ec"
DEBT_CONTEXT_SHA = "1339821cb11c66482cfcbff66838ea6bdd42d32ebabcd32927e6839e6fa1286a"
DEBT_PROFILE_SHA = "b5fb0cbaa9758b2d772452ce00e3d3139af9aef7dd6e6b35a38db85b031d36e3"
MIN_R8_MAIN = "6a6409990c0f5612fb6489050cf26ab47263629d"
RUN_ID = "run_20261013T160243244215Z"


@dataclass(frozen=True)
class Source:
    path: Path
    payload: dict[str, Any]


def _read(path: Path) -> dict[str, Any]:
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise CaseServiceError(f"cannot load exact local JSON artifact: {path}") from exc
    if not isinstance(result, dict):
        raise CaseServiceError(f"artifact must be JSON object: {path}")
    return result


def _write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def _scan(root: Path) -> list[Source]:
    if not root.is_dir():
        return []
    found: list[Source] = []
    for path in sorted(root.rglob("*.json")):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            continue
        if isinstance(payload, dict):
            found.append(Source(path, payload))
    return found


def _exact(sources: list[Source], key: str, sha: str, label: str) -> Source | None:
    matches = [x for x in sources if x.payload.get(key) == sha]
    if not matches:
        return None
    first = matches[0]
    if any(x.payload != first.payload for x in matches[1:]):
        raise CaseServiceError(f"conflicting duplicate artifacts with {label} SHA")
    return first


def _git(repo: Path) -> dict[str, str]:
    def run(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)
    root = run("rev-parse", "--show-toplevel")
    if root.returncode or Path(root.stdout.strip()).resolve() != repo.resolve():
        raise CaseServiceError("real M23 runner requires its exact Git repository root")
    dirty = run("status", "--porcelain")
    if dirty.returncode or dirty.stdout.strip():
        raise CaseServiceError("tracked/unignored changes present; local Git worktree must be clean")
    head = run("rev-parse", "HEAD")
    ancestor = run("merge-base", "--is-ancestor", MIN_R8_MAIN, "HEAD")
    if head.returncode or ancestor.returncode:
        raise CaseServiceError("real M23 runner requires canonical M30-R8 main or a descendant")
    branch = run("branch", "--show-current").stdout.strip()
    return {"head": head.stdout.strip(), "branch": branch}


def _valid_cash(value: dict[str, Any]) -> None:
    validate_financial_observation(value)
    if (value.get("schema_version") != "financial-observation-v0.1"
        or value.get("observation_sha256") != CASH_SHA
        or value.get("metric") != "cash"
        or value.get("class") != "NORMALIZED_FACT"
        or value.get("value") != EXPECTED_CASH_VALUE
        or value.get("unit") != CURRENCY
        or value.get("entity", {}).get("id") != ENTITY_ID
        or value.get("entity", {}).get("financial_scope") != R6_AND_CASH_SCOPE
        or value.get("period", {}).get("kind") != "INSTANT"
        or value.get("period", {}).get("end") != "2026-06-30"):
        raise CaseServiceError("real reviewed INGR cash authority/period/identity/SHA mismatch")


def _valid_debt(value: dict[str, Any]) -> None:
    validate_sec_aggregate_debt_binding_context(value)
    if (value.get("context_sha256") != DEBT_CONTEXT_SHA
        or value.get("schema_version") != "debt-binding-context-v0.2-sec-aggregate"
        or value.get("value") != EXPECTED_DEBT_VALUE
        or value.get("unit") != CURRENCY
        or value.get("policy", {}).get("as_of") != AS_OF
        or value.get("policy", {}).get("max_age_days") != 550
        or value.get("entity") != {"id": ENTITY_ID, "financial_scope": SEC_DEBT_SCOPE}
        or value.get("freshness", {}).get("status") != "FRESH"
        or value.get("binding_eligibility", {}).get("eligible") is not True):
        raise CaseServiceError("real reviewed INGR aggregate-debt authority/period/identity/SHA mismatch")


def _locate_debt(sources: list[Source], run_dir: Path) -> Source | None:
    direct = _exact(sources, "context_sha256", DEBT_CONTEXT_SHA, "M30 aggregate debt context")
    if direct:
        _valid_debt(direct.payload)
        return direct
    profile = _exact(sources, "profile_sha256", DEBT_PROFILE_SHA, "reviewed SEC aggregate debt profile")
    if profile is None:
        return None
    validate_reviewed_sec_aggregate_debt(profile.payload)
    rebuilt = build_sec_aggregate_debt_binding_context(profile.payload, as_of=AS_OF, max_age_days=550)
    _valid_debt(rebuilt)
    path = run_dir / "rehydrated_sec_debt_context.json"
    _write(path, rebuilt)
    return Source(path, rebuilt)


def run_real_m23(*, repo_root: Path, artifact_root: Path | None = None,
                 proof_path: Path | None = None, enforce_git: bool = True) -> dict[str, Any]:
    repo = repo_root.resolve()
    git_state = _git(repo) if enforce_git else {"head": "git-check-disabled", "branch": "test"}
    root = (artifact_root or (repo / "workspace")).resolve()
    proof_file = (proof_path or (
        repo / "workspace" / "execution_artifacts" / CASE_ID / RUN_ID / "r8_binding_proof.json"
    ))
    proof_file = proof_file if proof_file.is_absolute() else repo / proof_file
    if not proof_file.is_file():
        return {"status": "NEED_R8_PROOF", "next_action": "RESTORE_EXACT_LOCAL_R8_PROOF",
                "required_proof_sha256": R8_PROOF_SHA, "required_path": str(proof_file)}
    proof = _read(proof_file)
    checked = validate_r6_binding_proof(proof)
    if (checked["proof_sha256"] != R8_PROOF_SHA
        or checked["package_sha256"] != R6_PACKAGE_SHA
        or proof["package"]["value"] != EXPECTED_SHARES
        or proof["package"]["class"] != "ASSUMPTION"
        or proof["package"]["as_of"] != AS_OF
        or proof["package"]["entity"].get("id") != ENTITY_ID
        or proof["package"]["entity"].get("financial_scope") != R6_AND_CASH_SCOPE):
        raise CaseServiceError("real R8 proof SHA/assumption/identity is not the exact approved case")
    sources = _scan(root)
    cash = _exact(sources, "observation_sha256", CASH_SHA, "AI-reviewed cash")
    debt = _exact(sources, "context_sha256", DEBT_CONTEXT_SHA, "AI-reviewed aggregate debt context")
    profile = _exact(sources, "profile_sha256", DEBT_PROFILE_SHA, "AI-reviewed aggregate debt profile")
    missing: list[dict[str, str]] = []
    if cash is None:
        missing.append({"artifact": "reviewed_cash_observation", "required_sha256": CASH_SHA})
    else:
        _valid_cash(cash.payload)
    if debt is None and profile is None:
        missing.append({"artifact": "reviewed_sec_aggregate_debt_context_or_profile",
                        "required_context_sha256": DEBT_CONTEXT_SHA,
                        "required_profile_sha256": DEBT_PROFILE_SHA})
    if missing:
        return {"status": "NEED_REAL_M23_SOURCE_ARTIFACTS",
                "next_action": "RESTORE_EXACT_GOVERNED_USER_LOCAL_CASH_DEBT",
                "missing": missing, "r8_proof_sha256": R8_PROOF_SHA,
                "scanned_json_files": len(sources), "git": git_state}
    run_dir = root / "execution_artifacts" / CASE_ID / (
        "r8_m23_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    )
    if not run_dir.parent.is_relative_to((repo / "workspace").resolve()):
        raise CaseServiceError("M23 materialization must remain under gitignored local workspace")
    if debt is None:
        debt = _locate_debt(sources, run_dir)
        if debt is None:
            raise CaseServiceError("reviewed debt profile vanished during deterministic rehydration")
    _valid_debt(debt.payload)
    cash_scope = cash.payload["entity"]["financial_scope"]
    debt_scope = debt.payload["entity"]["financial_scope"]
    r6_scope = proof["package"]["entity"]["financial_scope"]
    if cash_scope != debt_scope or r6_scope != debt_scope:
        # A filed consolidated-statement claim and an independently reviewed
        # scope-reconciliation assertion are required. Never silently relabel
        # signed SEC/NORMALIZED_FACT source objects or synthesize M19 components.
        return {
            "status": "HOLD_FINANCIAL_SCOPE_RECONCILIATION_REQUIRED",
            "next_action": "SOURCE_BOUND_AS_REPORTED_CFS_SCOPE_BRIDGE",
            "r8_proof_sha256": R8_PROOF_SHA,
            "cash_observation_sha256": CASH_SHA,
            "debt_context_sha256": DEBT_CONTEXT_SHA,
            "financial_scopes": {"r6_shares": r6_scope, "cash": cash_scope, "sec_aggregate_debt": debt_scope},
            "required_evidence": [
                "SAME_INGR_2026Q2_10Q_FILING_IDENTITY",
                "SOURCE_BOUND_CONSOLIDATED_STATEMENT_SCOPE",
                "INDEPENDENT_REVIEWED_SCOPE_RECONCILIATION",
            ],
            "git": git_state,
        }
    v02 = build_binding_proposal_with_sec_aggregate_debt(
        [cash.payload], debt.payload, as_of=AS_OF, max_age_days=550
    )
    validate_binding_proposal_sec_aggregate(v02)
    v03 = build_r6_v3_proposal(v02, proof)
    validate_r6_v3_proposal(v03)
    share = next(row for row in v03["draft_input_matrix"] if row["field"] == "equity.diluted_shares")
    if (share["source_class"] != "ASSUMPTION"
        or v03["baseline_context"]["fully_diluted_shares"]["value"] != EXPECTED_SHARES):
        raise CaseServiceError("R6 share authority would be improperly reclassified")
    _write(run_dir / "m23_sec_debt_base_v02.json", v02)
    _write(run_dir / "m23_r6_assumption_v03.json", v03)
    result = {
        "status": "REAL_INGR_M23_R6_ASSUMPTION_READY",
        "git": git_state, "run_dir": str(run_dir), "as_of": AS_OF,
        "cash_observation_sha256": CASH_SHA,
        "cash_source_path": str(cash.path),
        "debt_context_sha256": DEBT_CONTEXT_SHA,
        "debt_source_path": str(debt.path),
        "r6_package_sha256": R6_PACKAGE_SHA,
        "r8_proof_sha256": R8_PROOF_SHA,
        "m23_sec_debt_v02_proposal_sha256": v02["proposal_sha256"],
        "m23_r6_v03_proposal_sha256": v03["proposal_sha256"],
        "fully_diluted_shares_assumption": EXPECTED_SHARES,
        "fully_diluted_shares_source_class": "ASSUMPTION",
        "next_action": "BUILD_REAL_INGR_M24_WACC_PACKAGE",
    }
    _write(run_dir / "result.json", result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Real INGR R8 proof → M23 share ASSUMPTION")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--proof", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = run_real_m23(
            repo_root=args.repo_root, artifact_root=args.artifact_root,
            proof_path=args.proof,
        )
    except (CaseServiceError, OSError, ValueError, TypeError, KeyError) as exc:
        result = {"status": "ERROR", "error": str(exc)}
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 1 if result["status"] == "ERROR" else 0


if __name__ == "__main__":
    raise SystemExit(main())
