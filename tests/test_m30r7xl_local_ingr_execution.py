from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from valuation_hub import ingr_local_execution as runner
from valuation_hub.ai_dilution_authority import (
    ABSENT_SUPPORTED,
    BLOCKED_DEPENDENCY,
    EXPLICIT_COUNT_METHOD,
    PRESENT,
    build_ai_dilution_inventory,
)
from valuation_hub.case_service import CaseServiceError
from valuation_hub.external_source import build_external_source_snapshot
from valuation_hub.sec_live import TransportResponse, capture_companyfacts_snapshot
from valuation_hub.share_dilution import (
    extract_sec_dilution_candidate,
    normalize_share_dilution_candidate,
)
from valuation_hub.valuation_shares import (
    build_valuation_share_base_context,
    extract_sec_current_common_shares_candidate,
    normalize_current_common_shares_candidate,
)


def _sha(value: dict, field: str) -> str:
    copied = copy.deepcopy(value)
    copied.pop(field, None)
    return hashlib.sha256(
        json.dumps(
            copied,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()


def _companyfacts_snapshot() -> dict:
    payload = {
        "cik": 1046257,
        "entityName": "Ingredion Incorporated",
        "facts": {
            "dei": {
                "EntityCommonStockSharesOutstanding": {
                    "units": {
                        "shares": [{
                            "end": "2026-08-05",
                            "val": 63_063_979,
                            "accn": "0001628280-26-054722",
                            "form": "10-Q",
                            "filed": "2026-08-07",
                        }]
                    }
                }
            },
            "us-gaap": {
                "WeightedAverageNumberOfSharesOutstandingBasic": {
                    "units": {
                        "shares": [{
                            "start": "2026-04-01",
                            "end": "2026-06-30",
                            "val": 63_300_000,
                            "accn": "0001628280-26-054722",
                            "fy": 2026,
                            "fp": "Q2",
                            "form": "10-Q",
                            "filed": "2026-08-07",
                            "frame": "CY2026Q2",
                        }]
                    }
                },
                "WeightedAverageNumberOfDilutedSharesOutstanding": {
                    "units": {
                        "shares": [{
                            "start": "2026-04-01",
                            "end": "2026-06-30",
                            "val": 63_900_000,
                            "accn": "0001628280-26-054722",
                            "fy": 2026,
                            "fp": "Q2",
                            "form": "10-Q",
                            "filed": "2026-08-07",
                            "frame": "CY2026Q2",
                        }]
                    }
                },
            },
        },
    }
    body = json.dumps(payload, separators=(",", ":")).encode()

    def transport(locator: str, *, user_agent: str) -> TransportResponse:
        return TransportResponse(200, "application/json", body, locator)

    return capture_companyfacts_snapshot(
        "1046257",
        user_agent="M30R7XL test@example.com",
        transport=transport,
        fetched_at="2026-09-15T17:42:53+00:00",
    )


def _source(seed: str) -> list[dict]:
    return [{
        "locator": f"https://www.sec.gov/Archives/edgar/data/1046257/{seed}.htm",
        "snapshot_sha256": seed[0] * 64,
        "source_type": "issuer_filing_snapshot",
    }]


def _row(category: str, state: str, seed: str, **kwargs) -> dict:
    return {
        "category": category,
        "state": state,
        "sources": _source(seed),
        "evidence_basis": kwargs.get("basis", f"Issuer evidence for {category}."),
        "contradiction_search": {
            "performed": True,
            "summary": "No material contradiction identified.",
            "material_contradictions": [],
        },
        "dependencies": kwargs.get("dependencies", []),
        "adjustment_id": kwargs.get("adjustment_id"),
        "adjustment_shares": kwargs.get("adjustment_shares"),
        "calculation_method": kwargs.get("calculation_method"),
        "calculation_inputs": kwargs.get("calculation_inputs"),
    }


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def _prepare_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    inputs = workspace / "inputs"
    snapshots = workspace / "source_snapshots"
    inputs.mkdir(parents=True)
    snapshots.mkdir(parents=True)

    sec = _companyfacts_snapshot()
    basic = extract_sec_dilution_candidate(
        sec,
        "weighted_average_basic_shares",
        period_start="2026-04-01",
        period_end="2026-06-30",
        form="10-Q",
    )
    diluted = extract_sec_dilution_candidate(
        sec,
        "weighted_average_diluted_shares",
        period_start="2026-04-01",
        period_end="2026-06-30",
        form="10-Q",
    )
    basic_obs = normalize_share_dilution_candidate(basic)
    diluted_obs = normalize_share_dilution_candidate(diluted)

    current = extract_sec_current_common_shares_candidate(
        sec,
        period_end="2026-08-05",
        form="10-Q",
    )
    current["class"] = "FACT"
    current["candidate_sha256"] = _sha(current, "candidate_sha256")
    current_obs = normalize_current_common_shares_candidate(current)
    base = build_valuation_share_base_context(current_obs, as_of="2026-09-14")

    inventory = build_ai_dilution_inventory(
        base,
        [
            _row(
                "options_treasury_stock_method",
                BLOCKED_DEPENDENCY,
                "a",
                dependencies=["complete_option_strike_distribution_for_valuation_date_tsm"],
            ),
            _row(
                "rsu_restricted_stock",
                PRESENT,
                "b",
                adjustment_id="INGR-RSU-20260630",
                adjustment_shares=534_000,
                calculation_method=EXPLICIT_COUNT_METHOD,
                calculation_inputs={"explicit_share_count": 534_000},
            ),
            _row("warrants", ABSENT_SUPPORTED, "c"),
            _row("convertibles_if_converted", ABSENT_SUPPORTED, "d"),
            _row(
                "contingent_shares",
                BLOCKED_DEPENDENCY,
                "e",
                dependencies=["complete_point_in_time_payout_weighted_performance_award_count"],
            ),
            _row(
                "other_explicit",
                BLOCKED_DEPENDENCY,
                "f",
                dependencies=["current_director_and_deferred_equity_unit_count_as_of_2026_09_14"],
            ),
        ],
    )

    q2_text = """
    <html><body>
      <p>RSU activity for year-to-date 2026 was as follows:</p>
      <p>Granted 215 115.69</p>
      <p>For the 2026 performance shares awarded based on our total shareholder return, the number of shares that ultimately vest can range from zero to 200 percent of the grant.</p>
      <p>For year-to-date 2026, we awarded 116 thousand performance shares at a weighted average fair value of $136.63 per share.</p>
    </body></html>
    """
    q2 = build_external_source_snapshot(
        q2_text,
        source_publisher="U.S. Securities and Exchange Commission",
        source_type="issuer_filing_snapshot",
        source_tier="A",
        source_locator=runner.Q2_PRIMARY_FILING,
        captured_at="2026-09-30T09:00:00+09:00",
    )

    proxy_raw = tmp_path / "ingr-20260402.htm"
    proxy_raw.write_text(
        """
        <html><body>
          <p>The following table provides information about our equity compensation plans as of December 31, 2025.</p>
          <p>Total 2,177,904</p>
          <p>Amount shown includes an aggregate of 151,570 shares of common stock representing outstanding PSUs that will vest only upon completion of the relevant long-term incentive performance cycle.</p>
        </body></html>
        """,
        encoding="utf-8",
    )

    _write(inputs / "basic_candidate.json", basic)
    _write(inputs / "basic_observation.json", basic_obs)
    _write(inputs / "diluted_candidate.json", diluted)
    _write(inputs / "diluted_observation.json", diluted_obs)
    _write(inputs / "base_context.json", base)
    _write(inputs / "r4_inventory.json", inventory)
    _write(snapshots / "q2_external_snapshot.json", q2)

    monkeypatch.setattr(runner, "BASE_CONTEXT_SHA", base["context_sha256"])
    monkeypatch.setattr(runner, "R4_INVENTORY_SHA", inventory["inventory_sha256"])
    monkeypatch.setattr(runner, "Q2_EXTERNAL_SNAPSHOT_SHA", q2["snapshot_sha256"])
    return workspace, proxy_raw


def test_real_shaped_local_runner_reaches_r6_approval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, proxy_raw = _prepare_workspace(tmp_path, monkeypatch)
    result = runner.run_local_execution(
        repo_root=tmp_path,
        artifact_root=workspace,
        proxy_raw=proxy_raw,
        enforce_git=False,
    )

    assert result["status"] == "REAL_INGR_R6_ASSUMPTION_APPROVED"
    assert result["r6_decision"] == "APPROVE_DISCLOSURE_LIMITED_DILUTION_ASSUMPTION"
    assert result["fully_diluted_shares_assumption"] == 63_900_000
    assert result["relative_upper_spread"] < 0.05
    assert result["next_action"] == "ACTIVATE_M30_R8_ISSUE_112"

    run_dir = Path(result["run_dir"])
    assert (run_dir / "r7_package.json").exists()
    assert (run_dir / "r7x_envelope_manifest.json").exists()
    assert (run_dir / "r6_package.json").exists()
    assert (run_dir / "issue79_comment.md").exists()


def test_runner_stops_after_r7_when_proxy_raw_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, _ = _prepare_workspace(tmp_path, monkeypatch)
    result = runner.run_local_execution(
        repo_root=tmp_path,
        artifact_root=workspace,
        proxy_raw=None,
        enforce_git=False,
    )
    assert result["status"] == "NEED_PROXY_RAW_BYTES"
    assert result["r7_package_sha256"]
    assert result["next_action"] == "SUPPLY_EXACT_LOCAL_DEF14A_HTML_WITH_PROXY_RAW"


def test_duplicate_distinct_basic_candidates_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, _ = _prepare_workspace(tmp_path, monkeypatch)
    original = json.loads((workspace / "inputs" / "basic_candidate.json").read_text(encoding="utf-8"))
    duplicate = copy.deepcopy(original)
    duplicate["candidate_sha256"] = "f" * 64
    _write(workspace / "inputs" / "basic_candidate_conflict.json", duplicate)

    with pytest.raises(runner.LocalExecutionError, match="multiple distinct"):
        runner.discover_required_artifacts(workspace)


def _git(path: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(path), *args],
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def test_git_preflight_requires_clean_tree_and_minimum_ancestor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("canonical\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")
    _git(tmp_path, "commit", "-m", "canonical")
    head = _git(tmp_path, "rev-parse", "HEAD")
    monkeypatch.setattr(runner, "MINIMUM_STATE_SYNC_SHA", head)

    state = runner.ensure_local_git(tmp_path, sync_main=False)
    assert state["head"] == head

    tracked.write_text("dirty\n", encoding="utf-8")
    with pytest.raises(runner.LocalExecutionError, match="not clean"):
        runner.ensure_local_git(tmp_path, sync_main=False)


def test_envelope_specs_keep_case_specific_source_binding() -> None:
    proxy = build_external_source_snapshot(
        "<p>Total 2,177,904</p><p>Amount shown includes an aggregate of 151,570 shares of common stock representing outstanding PSUs</p>",
        source_publisher="U.S. Securities and Exchange Commission",
        source_type="issuer_filing_snapshot",
        source_tier="A",
        source_locator=runner.PROXY_FILING,
        captured_at="2026-09-30T09:00:00+09:00",
    )
    q2 = build_external_source_snapshot(
        "<p>Granted 215 115.69</p><p>For year-to-date 2026, we awarded 116 thousand performance shares at a weighted average fair value of $136.63 per share.</p>",
        source_publisher="U.S. Securities and Exchange Commission",
        source_type="issuer_filing_snapshot",
        source_tier="A",
        source_locator=runner.Q2_PRIMARY_FILING,
        captured_at="2026-09-30T09:00:00+09:00",
    )
    specs = runner._envelope_specs(proxy, q2)
    assert specs[0]["shares"] == 2_177_904
    assert specs[3]["shares"] == 267_570
    assert specs[4]["calculation"]["observed_gross_grants"] == 331_000
    assert specs[4]["calculation"]["lag_days"] == 76
