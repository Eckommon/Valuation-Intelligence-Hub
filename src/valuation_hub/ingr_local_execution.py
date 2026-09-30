"""Case-specific local execution orchestration for M30 Ingredion R7 -> R7X -> R6.

This module intentionally adds no valuation formula and performs no generic network
fetch. It only discovers user-local governed artifacts, validates them through the
existing kernels, optionally seals explicitly supplied local DEF 14A bytes, and runs
the already-canonical R7/R7X/R6 sequence.

Run from an installed editable checkout:

    python -m valuation_hub.ingr_local_execution --sync-main
    python -m valuation_hub.ingr_local_execution --sync-main --proxy-raw path/to/ingr-20260402.htm

The runner writes only below workspace/execution_artifacts and
workspace/source_snapshots. Drafts, registry, admission state, and GitHub issues are
never mutated.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from valuation_hub.ai_historical_dilution_authority import (
    REQUIRED_CRITERIA,
    build_ai_historical_dilution_adjudication,
    build_ai_historical_dilution_evidence,
    build_ai_reviewed_historical_dilution_package,
    validate_ai_reviewed_historical_dilution_package,
)
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.dilution_envelope_source import (
    build_source_bound_dilution_envelope_manifest,
    validate_source_bound_dilution_envelope_manifest,
)
from valuation_hub.disclosure_limited_dilution import (
    APPROVE,
    ROLE_ANCHOR,
    ROLE_BUFFER,
    ROLE_PERFORMANCE_UPLIFT,
    ROLE_SUBSEQUENT,
    build_disclosure_limited_dilution_adjudication,
    build_disclosure_limited_dilution_evidence,
    finalize_disclosure_limited_dilution_assumption,
    validate_disclosure_limited_dilution_adjudication,
    validate_disclosure_limited_dilution_assumption,
)
from valuation_hub.external_source import (
    build_external_source_snapshot,
    materialize_external_source_snapshot,
    validate_external_source_snapshot,
)

CASE_ID = "US_INGR_INGREDION"
MINIMUM_STATE_SYNC_SHA = "05ff4d79924f0767ce6ca8fc6dd429f07a416a64"
BASE_CONTEXT_SHA = "12ac21026b1a06756d0474e0ad2aec10bdd9391caf2ff03ca512c2cb3d8a0adc"
R4_INVENTORY_SHA = "bb8242c126fcd0c91c0a3aedd8aac26640c8b3ad829a59823eb861762270a4b2"
Q2_EXTERNAL_SNAPSHOT_SHA = "f61f33b0e27403ab56882d8cc1daa3a66571e9452fc5d8012268f39ab098b0f9"

Q2_PRIMARY_FILING = "https://www.sec.gov/Archives/edgar/data/1046257/000162828026054722/ingr-20260630.htm"
PROXY_FILING = "https://www.sec.gov/Archives/edgar/data/1046257/000104625726000151/ingr-20260402.htm"

BASIC_METRIC = "weighted_average_basic_shares"
DILUTED_METRIC = "weighted_average_diluted_shares"
PERIOD_START = "2026-04-01"
PERIOD_END = "2026-06-30"
VALUATION_AS_OF = "2026-09-14"

PROXY_ANCHOR_EXCERPT = "Total 2,177,904"
PROXY_PSU_EXCERPT = (
    "Amount shown includes an aggregate of 151,570 shares of common stock "
    "representing outstanding PSUs"
)
Q2_RSU_EXCERPT = "Granted 215 115.69"
Q2_PSU_EXCERPT = (
    "For year-to-date 2026, we awarded 116 thousand performance shares at a "
    "weighted average fair value of $136.63 per share."
)


class LocalExecutionError(RuntimeError):
    """Fail-closed local orchestration error."""


class LocalInputRequired(LocalExecutionError):
    def __init__(self, status: str, message: str, *, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.status = status
        self.details = details or {}


@dataclass(frozen=True)
class JsonArtifact:
    path: Path
    payload: dict[str, Any]


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise LocalExecutionError(f"refusing to overwrite local execution artifact: {path}")
    path.write_text(_canonical_json(value), encoding="utf-8")


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise LocalExecutionError(f"refusing to overwrite local execution artifact: {path}")
    path.write_text(value, encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LocalExecutionError(f"cannot read JSON artifact: {path}") from exc
    if not isinstance(value, dict):
        raise LocalExecutionError(f"JSON object required: {path}")
    return value


def _scan_json(root: Path) -> list[JsonArtifact]:
    if not root.exists():
        raise LocalInputRequired(
            "NEED_LOCAL_WORKSPACE",
            f"local artifact root does not exist: {root}",
        )
    result: list[JsonArtifact] = []
    for path in sorted(root.rglob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            result.append(JsonArtifact(path=path, payload=payload))
    return result


def _artifact_identity(payload: dict[str, Any], preferred: tuple[str, ...]) -> str:
    for key in preferred:
        value = payload.get(key)
        if isinstance(value, str) and value:
            return f"{key}:{value}"
    return _canonical_json(payload)


def _find_unique(
    artifacts: list[JsonArtifact],
    predicate: Callable[[dict[str, Any]], bool],
    *,
    label: str,
    identity_fields: tuple[str, ...],
    required: bool = True,
) -> JsonArtifact | None:
    matches = [item for item in artifacts if predicate(item.payload)]
    if not matches:
        if required:
            raise LocalInputRequired("NEED_LOCAL_ARTIFACTS", f"missing local artifact: {label}")
        return None
    by_identity: dict[str, list[JsonArtifact]] = {}
    for item in matches:
        identity = _artifact_identity(item.payload, identity_fields)
        by_identity.setdefault(identity, []).append(item)
    if len(by_identity) != 1:
        detail = {key: [str(x.path) for x in values] for key, values in by_identity.items()}
        raise LocalExecutionError(
            f"multiple distinct local artifacts match {label}: {json.dumps(detail, ensure_ascii=False)}"
        )
    values = next(iter(by_identity.values()))
    return sorted(values, key=lambda item: str(item.path))[0]


def _candidate_predicate(metric: str) -> Callable[[dict[str, Any]], bool]:
    def predicate(value: dict[str, Any]) -> bool:
        period = value.get("period")
        return (
            value.get("schema_version") == "share-dilution-candidate-v0.1"
            and value.get("class") == "FACT_CANDIDATE"
            and value.get("metric") == metric
            and isinstance(period, dict)
            and period.get("start") == PERIOD_START
            and period.get("end") == PERIOD_END
        )
    return predicate


def _observation_predicate(metric: str) -> Callable[[dict[str, Any]], bool]:
    def predicate(value: dict[str, Any]) -> bool:
        period = value.get("period")
        return (
            value.get("schema_version") == "share-dilution-observation-v0.1"
            and value.get("class") == "NORMALIZED_FACT_CANDIDATE"
            and value.get("metric") == metric
            and isinstance(period, dict)
            and period.get("start") == PERIOD_START
            and period.get("end") == PERIOD_END
        )
    return predicate


def discover_required_artifacts(artifact_root: Path) -> dict[str, JsonArtifact]:
    artifacts = _scan_json(artifact_root)
    return {
        "basic_candidate": _find_unique(
            artifacts,
            _candidate_predicate(BASIC_METRIC),
            label="M21 Q2 basic-share candidate",
            identity_fields=("candidate_sha256",),
        ),
        "basic_observation": _find_unique(
            artifacts,
            _observation_predicate(BASIC_METRIC),
            label="M21 Q2 basic-share normalized observation",
            identity_fields=("observation_sha256",),
        ),
        "diluted_candidate": _find_unique(
            artifacts,
            _candidate_predicate(DILUTED_METRIC),
            label="M21 Q2 diluted-share candidate",
            identity_fields=("candidate_sha256",),
        ),
        "diluted_observation": _find_unique(
            artifacts,
            _observation_predicate(DILUTED_METRIC),
            label="M21 Q2 diluted-share normalized observation",
            identity_fields=("observation_sha256",),
        ),
        "base_context": _find_unique(
            artifacts,
            lambda value: (
                value.get("schema_version") == "valuation-share-base-context-v0.1"
                and value.get("context_sha256") == BASE_CONTEXT_SHA
            ),
            label=f"M22 base context {BASE_CONTEXT_SHA}",
            identity_fields=("context_sha256",),
        ),
        "r4_inventory": _find_unique(
            artifacts,
            lambda value: (
                value.get("schema_version") == "ai-dilution-coverage-inventory-v0.1"
                and value.get("inventory_sha256") == R4_INVENTORY_SHA
            ),
            label=f"corrected R4.1 inventory {R4_INVENTORY_SHA}",
            identity_fields=("inventory_sha256",),
        ),
        "q2_snapshot": _find_unique(
            artifacts,
            lambda value: (
                value.get("schema_version") == "external-source-snapshot-v0.1"
                and value.get("snapshot_sha256") == Q2_EXTERNAL_SNAPSHOT_SHA
            ),
            label=f"Q2 external-source snapshot {Q2_EXTERNAL_SNAPSHOT_SHA}",
            identity_fields=("snapshot_sha256",),
        ),
    }


def _proxy_candidates(artifact_root: Path) -> list[JsonArtifact]:
    matches: list[JsonArtifact] = []
    for item in _scan_json(artifact_root):
        value = item.payload
        source = value.get("source")
        if (
            value.get("schema_version") == "external-source-snapshot-v0.1"
            and isinstance(source, dict)
            and source.get("locator") == PROXY_FILING
            and source.get("tier") == "A"
        ):
            validate_external_source_snapshot(value)
            matches.append(item)
    return matches


def _select_proxy_snapshot(artifact_root: Path) -> JsonArtifact | None:
    matches = _proxy_candidates(artifact_root)
    if not matches:
        return None
    body_hashes = {
        item.payload.get("body", {}).get("sha256")
        for item in matches
        if isinstance(item.payload.get("body"), dict)
    }
    if len(body_hashes) != 1:
        raise LocalExecutionError(
            "multiple distinct DEF 14A source bodies are sealed locally; resolve the conflict before execution"
        )
    return max(
        matches,
        key=lambda item: str(item.payload.get("capture", {}).get("captured_at", "")),
    )


def _run_git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise LocalExecutionError(f"git {' '.join(args)} failed: {message}")
    return result


def ensure_local_git(repo: Path, *, sync_main: bool) -> dict[str, Any]:
    root = _run_git(repo, "rev-parse", "--show-toplevel").stdout.strip()
    if Path(root).resolve() != repo.resolve():
        raise LocalExecutionError(f"repo root mismatch: expected {repo}, git reports {root}")

    dirty = _run_git(repo, "status", "--porcelain").stdout.strip()
    if dirty:
        raise LocalExecutionError(
            "Git worktree is not clean; preserve/commit/stash nonignored changes before M30 execution"
        )

    if sync_main:
        _run_git(repo, "fetch", "origin", "main")
        _run_git(repo, "switch", "main")
        _run_git(repo, "pull", "--ff-only", "origin", "main")
        dirty_after = _run_git(repo, "status", "--porcelain").stdout.strip()
        if dirty_after:
            raise LocalExecutionError("tracked working tree became dirty after sync; aborting")

    head = _run_git(repo, "rev-parse", "HEAD").stdout.strip()
    ancestor = _run_git(
        repo,
        "merge-base",
        "--is-ancestor",
        MINIMUM_STATE_SYNC_SHA,
        head,
        check=False,
    )
    if ancestor.returncode != 0:
        raise LocalExecutionError(
            "local checkout does not contain canonical M30-R7XS state; run with --sync-main from a clean checkout"
        )
    branch = _run_git(repo, "branch", "--show-current").stdout.strip()
    return {"head": head, "branch": branch, "minimum_state_sync_sha": MINIMUM_STATE_SYNC_SHA}


def _timestamp() -> str:
    return datetime.now().astimezone().isoformat()


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _build_r7(inputs: dict[str, JsonArtifact], run_dir: Path) -> dict[str, Any]:
    pair = (
        inputs["basic_candidate"].payload,
        inputs["basic_observation"].payload,
        inputs["diluted_candidate"].payload,
        inputs["diluted_observation"].payload,
    )
    evidence = build_ai_historical_dilution_evidence(
        *pair,
        primary_filing_locator=Q2_PRIMARY_FILING,
        evidence_basis=(
            "Exact SEC CompanyFacts Q2 weighted-average basic and diluted share denominators "
            "reproduce from the same issuer filing/source lineage; historical duration reference only."
        ),
        contradiction_search_summary=(
            "No material contradiction identified in the governed paired Q2 SEC basic/diluted "
            "candidate-observation lineage; uniqueness, entity, period, filing, and source are revalidated."
        ),
        material_contradictions=[],
        criteria={key: True for key in REQUIRED_CRITERIA},
    )
    adjudication = build_ai_historical_dilution_adjudication(
        evidence,
        *pair,
        adjudicated_at=_timestamp(),
    )
    package = build_ai_reviewed_historical_dilution_package(
        *pair,
        evidence,
        adjudication,
    )
    validate_ai_reviewed_historical_dilution_package(package)
    _write_json(run_dir / "r7_evidence.json", evidence)
    _write_json(run_dir / "r7_adjudication.json", adjudication)
    _write_json(run_dir / "r7_package.json", package)
    return package


def _seal_proxy_snapshot(
    repo: Path,
    artifact_root: Path,
    proxy_raw: Path | None,
) -> JsonArtifact:
    existing = _select_proxy_snapshot(artifact_root)
    if existing is not None:
        return existing
    if proxy_raw is None:
        raise LocalInputRequired(
            "NEED_PROXY_RAW_BYTES",
            "2026 DEF 14A immutable source snapshot is not present locally; supply the exact local filing HTML with --proxy-raw",
            details={"required_locator": PROXY_FILING},
        )
    raw_path = proxy_raw if proxy_raw.is_absolute() else (repo / proxy_raw)
    try:
        raw_text = raw_path.resolve().read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeError) as exc:
        raise LocalExecutionError(f"cannot read exact DEF 14A UTF-8 bytes: {raw_path}") from exc
    snapshot = build_external_source_snapshot(
        raw_text,
        source_publisher="U.S. Securities and Exchange Commission",
        source_type="issuer_filing_snapshot",
        source_tier="A",
        source_locator=PROXY_FILING,
        captured_at=_timestamp(),
    )
    output = repo / "workspace" / "source_snapshots" / f"INGR_2026_DEF14A_{snapshot['snapshot_sha256'][:12]}.json"
    materialize_external_source_snapshot(snapshot, output, repo)
    validate_external_source_snapshot(snapshot)
    return JsonArtifact(path=output, payload=snapshot)


def _envelope_specs(proxy: dict[str, Any], q2: dict[str, Any]) -> list[dict[str, Any]]:
    proxy_sha = proxy["snapshot_sha256"]
    q2_sha = q2["snapshot_sha256"]

    def binding(sha: str, excerpt: str, observed: int, multiplier: int = 1) -> dict[str, Any]:
        return {
            "snapshot_sha256": sha,
            "evidence_excerpt": excerpt,
            "observed_quantity": observed,
            "unit_multiplier": multiplier,
        }

    q2_rsu = binding(q2_sha, Q2_RSU_EXCERPT, 215, 1000)
    q2_psu = binding(q2_sha, Q2_PSU_EXCERPT, 116, 1000)
    return [
        {
            "component_id": "2025YE_EQUITY_PLAN_SECURITIES",
            "role": ROLE_ANCHOR,
            "shares": 2_177_904,
            "as_of": "2025-12-31",
            "evidence_basis": (
                "Issuer proxy total securities reflected in the equity-compensation-plan table; "
                "conservative no-netting anchor."
            ),
            "source_bindings": [
                binding(proxy_sha, PROXY_ANCHOR_EXCERPT, 2_177_904),
            ],
            "calculation": None,
        },
        {
            "component_id": "2026_YTD_RSU_GRANTS",
            "role": ROLE_SUBSEQUENT,
            "shares": 215_000,
            "as_of": "2026-06-30",
            "evidence_basis": "Issuer Q2 year-to-date employee RSU grants.",
            "source_bindings": [q2_rsu],
            "calculation": None,
        },
        {
            "component_id": "2026_YTD_PSU_GRANTS",
            "role": ROLE_SUBSEQUENT,
            "shares": 116_000,
            "as_of": "2026-06-30",
            "evidence_basis": "Issuer Q2 year-to-date performance-share grants.",
            "source_bindings": [q2_psu],
            "calculation": None,
        },
        {
            "component_id": "PSU_200_PERCENT_MAX_UPLIFT",
            "role": ROLE_PERFORMANCE_UPLIFT,
            "shares": 267_570,
            "as_of": "2026-06-30",
            "evidence_basis": (
                "Extra 100% conservative payout uplift above proxy target PSUs plus 2026 YTD PSU grants; "
                "the Q2 source also discloses a zero-to-200-percent 2026 performance-share vesting range."
            ),
            "source_bindings": [
                binding(proxy_sha, PROXY_PSU_EXCERPT, 151_570),
                q2_psu,
            ],
            "calculation": None,
        },
        {
            "component_id": "DISCLOSURE_LAG_BUFFER",
            "role": ROLE_BUFFER,
            "shares": 331_000 * 76 / 181,
            "as_of": VALUATION_AS_OF,
            "evidence_basis": (
                "Observed 2026 H1 gross RSU+PSU grant run-rate pro-rated across the 76-day disclosure lag."
            ),
            "source_bindings": [q2_rsu, q2_psu],
            "calculation": {
                "method": "PRO_RATA_GROSS_GRANT_RUN_RATE_V01",
                "observed_gross_grants": 331_000,
                "observed_days": 181,
                "lag_days": 76,
            },
        },
    ]


def _build_r7x(
    proxy_snapshot: JsonArtifact,
    q2_snapshot: JsonArtifact,
    run_dir: Path,
) -> dict[str, Any]:
    validate_external_source_snapshot(proxy_snapshot.payload)
    validate_external_source_snapshot(q2_snapshot.payload)
    specs = _envelope_specs(proxy_snapshot.payload, q2_snapshot.payload)
    manifest = build_source_bound_dilution_envelope_manifest(
        specs,
        [proxy_snapshot.payload, q2_snapshot.payload],
    )
    validate_source_bound_dilution_envelope_manifest(manifest)
    _write_json(run_dir / "r7x_component_specs.json", specs)
    _write_json(run_dir / "r7x_envelope_manifest.json", manifest)
    return manifest


def _build_r6(
    inputs: dict[str, JsonArtifact],
    r7_package: dict[str, Any],
    envelope_manifest: dict[str, Any],
    run_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    checked_manifest = validate_source_bound_dilution_envelope_manifest(envelope_manifest)
    components = checked_manifest["components"]
    base = inputs["base_context"].payload
    inventory = inputs["r4_inventory"].payload
    evidence = build_disclosure_limited_dilution_evidence(
        base,
        inventory,
        r7_package,
        components,
        as_of=VALUATION_AS_OF,
        materiality_threshold=0.05,
        max_historical_age_days=180,
    )
    adjudication = build_disclosure_limited_dilution_adjudication(
        evidence,
        base,
        inventory,
        r7_package,
        components,
        adjudicated_at=_timestamp(),
    )
    validate_disclosure_limited_dilution_adjudication(
        adjudication,
        evidence,
        base,
        inventory,
        r7_package,
        components,
    )
    _write_json(run_dir / "r6_evidence.json", evidence)
    _write_json(run_dir / "r6_adjudication.json", adjudication)

    package: dict[str, Any] | None = None
    if adjudication.get("decision") == APPROVE:
        package = finalize_disclosure_limited_dilution_assumption(
            evidence,
            adjudication,
            base,
            inventory,
            r7_package,
            components,
        )
        validate_disclosure_limited_dilution_assumption(
            package,
            evidence,
            adjudication,
            base,
            inventory,
            r7_package,
            components,
        )
        _write_json(run_dir / "r6_package.json", package)
    return evidence, adjudication, package


def _issue79_handoff(
    *,
    git_state: dict[str, Any],
    run_dir: Path,
    r7_package: dict[str, Any],
    envelope_manifest: dict[str, Any],
    r6_evidence: dict[str, Any],
    r6_adjudication: dict[str, Any],
    r6_package: dict[str, Any] | None,
) -> str:
    package_line = (
        f"- R6 package SHA: \`{r6_package['package_sha256']}\`\n"
        if r6_package is not None
        else "- R6 package: not finalized because adjudication did not approve\n"
    )
    next_action = (
        "Activate Issue #112 / M30-R8; preserve diluted shares as ASSUMPTION."
        if r6_package is not None
        else "Do not activate Issue #112; resolve the R6 materiality/evidence hold."
    )
    return (
        "## Real local R7 -> R7X -> R6 execution\n\n"
        f"- local HEAD: \`{git_state.get('head', 'git-check-disabled')}\`\n"
        f"- run directory: \`{run_dir}\`\n"
        f"- R7 package SHA: \`{r7_package['package_sha256']}\`\n"
        f"- R7X envelope manifest SHA: \`{envelope_manifest['manifest_sha256']}\`\n"
        f"- R6 evidence SHA: \`{r6_evidence['evidence_sha256']}\`\n"
        f"- R6 adjudication SHA: \`{r6_adjudication['adjudication_sha256']}\`\n"
        f"- R6 decision: \`{r6_adjudication['decision']}\`\n"
        + package_line
        + f"- next action: {next_action}\n"
    )


def run_local_execution(
    *,
    repo_root: Path,
    artifact_root: Path | None = None,
    proxy_raw: Path | None = None,
    sync_main: bool = False,
    enforce_git: bool = True,
) -> dict[str, Any]:
    repo = repo_root.resolve()
    if enforce_git:
        git_state = ensure_local_git(repo, sync_main=sync_main)
    else:
        git_state = {"head": "git-check-disabled", "branch": "test"}

    local_root = (artifact_root or (repo / "workspace")).resolve()
    inputs = discover_required_artifacts(local_root)
    validate_external_source_snapshot(inputs["q2_snapshot"].payload)

    run_dir = repo / "workspace" / "execution_artifacts" / CASE_ID / f"run_{_run_id()}"
    run_dir.mkdir(parents=True, exist_ok=False)

    r7_package = _build_r7(inputs, run_dir)

    try:
        proxy_snapshot = _seal_proxy_snapshot(repo, local_root, proxy_raw)
    except LocalInputRequired as exc:
        partial = {
            "status": exc.status,
            "message": str(exc),
            "details": exc.details,
            "git": git_state,
            "run_dir": str(run_dir),
            "r7_package_sha256": r7_package["package_sha256"],
            "next_action": "SUPPLY_EXACT_LOCAL_DEF14A_HTML_WITH_PROXY_RAW",
        }
        _write_json(run_dir / "partial_status.json", partial)
        return partial

    envelope_manifest = _build_r7x(proxy_snapshot, inputs["q2_snapshot"], run_dir)
    r6_evidence, r6_adjudication, r6_package = _build_r6(
        inputs,
        r7_package,
        envelope_manifest,
        run_dir,
    )

    approved = r6_package is not None
    result = {
        "status": (
            "REAL_INGR_R6_ASSUMPTION_APPROVED"
            if approved
            else "REAL_INGR_R6_NOT_APPROVED"
        ),
        "git": git_state,
        "run_dir": str(run_dir),
        "inputs": {
            key: str(value.path)
            for key, value in inputs.items()
        },
        "proxy_snapshot_path": str(proxy_snapshot.path),
        "proxy_snapshot_sha256": proxy_snapshot.payload["snapshot_sha256"],
        "r7_package_sha256": r7_package["package_sha256"],
        "r7x_manifest_sha256": envelope_manifest["manifest_sha256"],
        "r6_evidence_sha256": r6_evidence["evidence_sha256"],
        "r6_adjudication_sha256": r6_adjudication["adjudication_sha256"],
        "r6_decision": r6_adjudication["decision"],
        "r6_package_sha256": r6_package["package_sha256"] if approved else None,
        "fully_diluted_shares_assumption": r6_package["value"] if approved else None,
        "relative_upper_spread": r6_evidence["upper_envelope"]["relative_upper_spread"],
        "next_action": (
            "ACTIVATE_M30_R8_ISSUE_112"
            if approved
            else "DO_NOT_ACTIVATE_M30_R8_RESOLVE_R6_HOLD"
        ),
    }
    _write_json(run_dir / "result.json", result)
    handoff = _issue79_handoff(
        git_state=git_state,
        run_dir=run_dir,
        r7_package=r7_package,
        envelope_manifest=envelope_manifest,
        r6_evidence=r6_evidence,
        r6_adjudication=r6_adjudication,
        r6_package=r6_package,
    )
    _write_text(run_dir / "issue79_comment.md", handoff)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m valuation_hub.ingr_local_execution",
        description="Fail-closed local runner for the real Ingredion M30 R7 -> R7X -> R6 path.",
    )
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--artifact-root", type=Path, default=None)
    parser.add_argument("--proxy-raw", type=Path, default=None)
    parser.add_argument(
        "--sync-main",
        action="store_true",
        help="From a clean tracked worktree: git fetch origin main, switch main, and ff-only pull before execution.",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(sys.argv[1:] if argv is None else argv)
    repo = args.repo_root.resolve() if args.repo_root else find_repo_root()
    try:
        result = run_local_execution(
            repo_root=repo,
            artifact_root=args.artifact_root,
            proxy_raw=args.proxy_raw,
            sync_main=args.sync_main,
            enforce_git=True,
        )
    except LocalInputRequired as exc:
        result = {
            "status": exc.status,
            "message": str(exc),
            "details": exc.details,
            "next_action": "RESTORE_REQUIRED_USER_LOCAL_ARTIFACTS",
        }
        if args.as_json:
            print(_canonical_json(result), end="")
        else:
            print(f"{result['status']}: {result['message']}")
        return 3
    except (LocalExecutionError, CaseServiceError, OSError, ValueError, KeyError, TypeError) as exc:
        result = {"status": "ERROR", "error": str(exc)}
        if args.as_json:
            print(_canonical_json(result), end="")
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.as_json:
        print(_canonical_json(result), end="")
    else:
        print(f"status: {result['status']}")
        print(f"run_dir: {result.get('run_dir')}")
        if result.get("r6_decision"):
            print(f"r6_decision: {result['r6_decision']}")
        print(f"next_action: {result['next_action']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
