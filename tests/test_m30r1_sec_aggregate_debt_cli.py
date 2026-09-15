from __future__ import annotations

import json
from pathlib import Path

import pytest

from valuation_hub import cli_entry_m30r1
from valuation_hub.sec_aggregate_debt import SEMANTIC_DECISION
from valuation_hub.sec_live import TransportResponse, capture_companyfacts_snapshot, companyfacts_locator

CIK = "0001046257"
ACCN = "0001628280-26-054722"


def _snapshot() -> dict:
    payload = {
        "cik": 1046257,
        "entityName": "Ingredion Incorporated",
        "facts": {
            "us-gaap": {
                "DebtLongtermAndShorttermCombinedAmount": {"units": {"USD": [
                    {
                        "val": 1_783_000_000,
                        "end": "2026-06-30",
                        "fy": 2026,
                        "fp": "Q2",
                        "form": "10-Q",
                        "filed": "2026-08-07",
                        "accn": ACCN,
                    }
                ]}}
            }
        },
    }
    body = json.dumps(payload, separators=(",", ":")).encode()

    def transport(locator: str, *, user_agent: str):
        assert locator == companyfacts_locator(CIK)
        return TransportResponse(200, "application/json", body, locator)

    return capture_companyfacts_snapshot(
        CIK,
        user_agent="M30R1 test-contact@example.com",
        transport=transport,
        fetched_at="2026-09-15T17:42:53+00:00",
    )


def _write(path: Path, value) -> Path:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _run_json(capsys: pytest.CaptureFixture[str], argv: list[str]) -> tuple[int, dict]:
    code = cli_entry_m30r1.main(["--json", *argv])
    out = json.loads(capsys.readouterr().out)
    return code, out


def test_candidate_to_observation_runs_without_human_approval(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    snapshot = _write(tmp_path / "snapshot.json", _snapshot())
    code, candidate = _run_json(capsys, [
        "sec-aggregate-debt-extract", str(snapshot), "--form", "10-Q", "--period-end", "2026-06-30"
    ])
    assert code == 0
    assert candidate["status"] == "SEC_AGGREGATE_DEBT_CANDIDATE"
    assert candidate["value"] == 1_783_000_000
    candidate_path = _write(tmp_path / "candidate.json", candidate)

    code, checked = _run_json(capsys, ["sec-aggregate-debt-candidate-validate", str(candidate_path)])
    assert code == 0
    assert checked["status"] == "PASS_SEC_AGGREGATE_DEBT_CANDIDATE_VALIDATION"

    code, observation = _run_json(capsys, ["sec-aggregate-debt-normalize", str(candidate_path)])
    assert code == 0
    assert observation["status"] == "SEC_AGGREGATE_DEBT_NORMALIZED"
    observation_path = _write(tmp_path / "observation.json", observation)

    code, checked = _run_json(capsys, ["sec-aggregate-debt-observation-validate", str(observation_path)])
    assert code == 0
    assert checked["status"] == "PASS_SEC_AGGREGATE_DEBT_OBSERVATION_VALIDATION"


def test_review_build_is_fail_closed_and_requires_exact_semantic_decision(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    snapshot = _write(tmp_path / "snapshot.json", _snapshot())
    code, candidate = _run_json(capsys, [
        "sec-aggregate-debt-extract", str(snapshot), "--form", "10-Q", "--period-end", "2026-06-30"
    ])
    assert code == 0
    candidate_path = _write(tmp_path / "candidate.json", candidate)
    code, observation = _run_json(capsys, ["sec-aggregate-debt-normalize", str(candidate_path)])
    assert code == 0
    observation_path = _write(tmp_path / "observation.json", observation)

    common = [
        "sec-aggregate-debt-review-build", str(observation_path),
        "--reviewer", "Explicit Human Reviewer",
        "--reviewed-at", "2026-09-16T03:00:00+09:00",
        "--review-basis", "Reviewed issuer filing debt reconciliation and lease-liability boundary.",
        "--source-basis-locator", "https://www.sec.gov/Archives/edgar/data/1046257/",
    ]
    code, error = _run_json(capsys, [*common, "--semantic-scope-decision", "INFERRED_APPROVAL"])
    assert code == 2
    assert "lease liabilities" in error["error"]

    code, error = _run_json(capsys, [
        "sec-aggregate-debt-review-build", str(observation_path),
        "--reviewer", "Explicit Human Reviewer",
        "--reviewed-at", "2026-09-16T03:00:00",
        "--review-basis", "Reviewed issuer filing debt reconciliation and lease-liability boundary.",
        "--source-basis-locator", "https://www.sec.gov/Archives/edgar/data/1046257/",
        "--semantic-scope-decision", SEMANTIC_DECISION,
    ])
    assert code == 2
    assert "timezone" in error["error"]


def test_explicit_review_finalizes_profile_and_context(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    snapshot = _write(tmp_path / "snapshot.json", _snapshot())
    code, candidate = _run_json(capsys, [
        "sec-aggregate-debt-extract", str(snapshot), "--form", "10-Q", "--period-end", "2026-06-30"
    ])
    assert code == 0
    candidate_path = _write(tmp_path / "candidate.json", candidate)
    code, observation = _run_json(capsys, ["sec-aggregate-debt-normalize", str(candidate_path)])
    assert code == 0
    observation_path = _write(tmp_path / "observation.json", observation)

    code, assertion = _run_json(capsys, [
        "sec-aggregate-debt-review-build", str(observation_path),
        "--reviewer", "Explicit Human Reviewer",
        "--reviewed-at", "2026-09-16T03:00:00+09:00",
        "--review-basis", "Reviewed issuer filing debt reconciliation and lease-liability boundary.",
        "--source-basis-locator", "https://www.sec.gov/Archives/edgar/data/1046257/",
        "--semantic-scope-decision", SEMANTIC_DECISION,
    ])
    assert code == 0
    assert assertion["decision"] == "APPROVE"
    assertion_path = _write(tmp_path / "assertion.json", assertion)

    code, checked = _run_json(capsys, [
        "sec-aggregate-debt-review-validate", str(assertion_path), str(observation_path)
    ])
    assert code == 0
    assert checked["status"] == "PASS_SEC_AGGREGATE_DEBT_REVIEW_VALIDATION"

    code, profile = _run_json(capsys, [
        "sec-aggregate-debt-finalize", str(observation_path), str(assertion_path)
    ])
    assert code == 0
    assert profile["class"] == "NORMALIZED_FACT"
    assert profile["semantic_boundary"]["lease_liabilities_included"] is False
    profile_path = _write(tmp_path / "profile.json", profile)

    code, checked = _run_json(capsys, ["sec-aggregate-debt-profile-validate", str(profile_path)])
    assert code == 0
    assert checked["status"] == "PASS_REVIEWED_SEC_AGGREGATE_DEBT_VALIDATION"

    code, context = _run_json(capsys, [
        "sec-aggregate-debt-context-build", str(profile_path), "--as-of", "2026-09-14"
    ])
    assert code == 0
    assert context["class"] == "DERIVED_FACT"
    assert context["binding_eligibility"]["eligible"] is True
    context_path = _write(tmp_path / "context.json", context)

    code, checked = _run_json(capsys, ["sec-aggregate-debt-context-validate", str(context_path)])
    assert code == 0
    assert checked["status"] == "PASS_SEC_AGGREGATE_DEBT_CONTEXT_VALIDATION"
    assert checked["eligible"] is True


def test_m30_commands_delegate_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[list[str]] = []
    monkeypatch.setattr(cli_entry_m30r1.prior_cli, "main", lambda argv: seen.append(list(argv)) or 23)
    argv = ["real-equity-readiness-validate", "manifest.json"]
    assert cli_entry_m30r1.main(argv) == 23
    assert seen == [argv]
