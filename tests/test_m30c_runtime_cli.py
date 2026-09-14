from __future__ import annotations

import json
from pathlib import Path

import pytest

from valuation_hub import cli_entry_m30
from valuation_hub.sec_live import TransportResponse, capture_companyfacts_snapshot as real_capture, companyfacts_locator

CIK = "0001046257"
ACCN = "0001628280-26-054722"
USER_AGENT = "ValuationHub-M30C sec-contact@example.com"


def _repo(tmp_path: Path) -> Path:
    (tmp_path / "registry").mkdir(parents=True)
    (tmp_path / "registry" / "cases.json").write_text(
        json.dumps({"cases": [{
            "case_id": "US_EXISTING_CASE",
            "display_name_en": "Existing",
            "display_name_ko": "기존",
            "asset_class": "Public Equity",
            "model": "equity_fcff",
            "path": "analyses/equities/existing",
        }]}),
        encoding="utf-8",
    )
    (tmp_path / "workspace" / "source_snapshots").mkdir(parents=True)
    return tmp_path


def _payload() -> dict:
    return {
        "cik": 1046257,
        "entityName": "Ingredion Incorporated",
        "facts": {
            "us-gaap": {
                "CashAndCashEquivalentsAtCarryingValue": {"units": {"USD": [
                    {"val": 948_000_000, "end": "2026-06-30", "fy": 2026, "fp": "Q2", "form": "10-Q", "filed": "2026-08-07", "accn": ACCN}
                ]}},
                "ShortTermBorrowings": {"units": {"USD": [
                    {"val": 41_000_000, "end": "2026-06-30", "fy": 2026, "fp": "Q2", "form": "10-Q", "filed": "2026-08-07", "accn": ACCN}
                ]}},
                "DebtLongtermAndShorttermCombinedAmount": {"units": {"USD": [
                    {"val": 1_783_000_000, "end": "2026-06-30", "fy": 2026, "fp": "Q2", "form": "10-Q", "filed": "2026-08-07", "accn": ACCN}
                ]}},
                "NonredeemableNoncontrollingInterest": {"units": {"USD": [
                    {"val": 0, "end": "2026-06-30", "fy": 2026, "fp": "Q2", "form": "10-Q", "filed": "2026-08-07", "accn": ACCN}
                ]}},
            },
            "dei": {
                "EntityCommonStockSharesOutstanding": {"units": {"shares": [
                    {"val": 63_063_979, "end": "2026-08-05", "fy": 2026, "fp": "Q2", "form": "10-Q", "filed": "2026-08-07", "accn": ACCN}
                ]}}
            },
        },
    }


def _install_fake_capture(monkeypatch: pytest.MonkeyPatch) -> None:
    body = json.dumps(_payload(), separators=(",", ":")).encode()

    def transport(locator: str, *, user_agent: str):
        assert locator == companyfacts_locator(CIK)
        assert user_agent == USER_AGENT
        return TransportResponse(200, "application/json; charset=utf-8", body, locator)

    def capture(cik: str, *, user_agent: str):
        return real_capture(
            cik,
            user_agent=user_agent,
            transport=transport,
            fetched_at="2026-09-14T01:35:00+00:00",
        )

    monkeypatch.setattr(cli_entry_m30, "capture_companyfacts_snapshot", capture)


def test_missing_runtime_user_agent_fails_before_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    root = _repo(tmp_path)
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    monkeypatch.setattr(cli_entry_m30, "capture_companyfacts_snapshot", lambda *a, **k: (_ for _ in ()).throw(AssertionError("network must not run")))
    code = cli_entry_m30.main(["--root", str(root), "--json", "sec-companyfacts-fetch", CIK, "--output", "workspace/source_snapshots/ingr.json"])
    assert code == 2
    payload = json.loads(capsys.readouterr().out)
    assert "SEC_USER_AGENT" in payload["error"]
    assert not (root / "workspace/source_snapshots/ingr.json").exists()


def test_unsafe_output_is_rejected_before_credential_read_or_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    root = _repo(tmp_path)
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    monkeypatch.setattr(cli_entry_m30, "capture_companyfacts_snapshot", lambda *a, **k: (_ for _ in ()).throw(AssertionError("network must not run")))
    code = cli_entry_m30.main(["--root", str(root), "--json", "sec-companyfacts-fetch", CIK, "--output", "outside.json"])
    assert code == 2
    payload = json.loads(capsys.readouterr().out)
    assert "workspace/source_snapshots" in payload["error"]


def test_fetch_materializes_without_persisting_identifying_user_agent_and_validates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    root = _repo(tmp_path)
    monkeypatch.setenv("SEC_USER_AGENT", USER_AGENT)
    _install_fake_capture(monkeypatch)
    relative = Path("workspace/source_snapshots/INGR_companyfacts_20260914.json")

    code = cli_entry_m30.main(["--root", str(root), "--json", "sec-companyfacts-fetch", CIK, "--output", str(relative)])
    assert code == 0
    fetch_result = json.loads(capsys.readouterr().out)
    assert fetch_result["status"] == "SOURCE_SNAPSHOT_MATERIALIZED"
    assert fetch_result["user_agent_persisted"] is False

    path = root / relative
    text = path.read_text(encoding="utf-8")
    assert USER_AGENT not in text
    snapshot = json.loads(text)
    assert snapshot["request"] == {"method": "GET", "cik": CIK, "user_agent_provided": True}

    code = cli_entry_m30.main(["--root", str(root), "--json", "sec-source-snapshot-validate", str(relative)])
    assert code == 0
    validation = json.loads(capsys.readouterr().out)
    assert validation["status"] == "PASS_SOURCE_SNAPSHOT_VALIDATION"
    assert validation["user_agent_persisted"] is False


def test_materialized_snapshot_runs_m30b_preflight_to_human_debt_review_boundary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    root = _repo(tmp_path)
    monkeypatch.setenv("SEC_USER_AGENT", USER_AGENT)
    _install_fake_capture(monkeypatch)
    relative = "workspace/source_snapshots/INGR_companyfacts_20260914.json"
    assert cli_entry_m30.main(["--root", str(root), "--json", "sec-companyfacts-fetch", CIK, "--output", relative]) == 0
    capsys.readouterr()

    code = cli_entry_m30.main([
        "--root", str(root), "--json", "real-equity-preflight-v2", relative,
        "--case-id", "US_INGR_INGREDION",
        "--legal-name", "Ingredion Incorporated",
        "--ticker", "INGR",
        "--exchange", "NYSE",
        "--cik", CIK,
        "--financial-period-end", "2026-06-30",
        "--valuation-as-of", "2026-09-14",
        "--form", "10-Q",
    ])
    assert code == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "PASS_REAL_EQUITY_SOURCE_PREFLIGHT"
    assert result["blockers"] == []
    assert result["next_action"] == "CONTINUE_TO_HUMAN_DEBT_SEMANTIC_REVIEW"
    assert result["checks"]["sec_aggregate_debt_candidate"]["value"] == 1_783_000_000
    assert result["checks"]["minority_interest_candidate"]["explicit_zero"] is True
    assert result["human_review_boundary"]["debt_semantic_review_required"] is True
    assert result["human_review_boundary"]["debt_semantic_review_may_be_inferred"] is False


def test_m29_commands_delegate_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[list[str]] = []
    monkeypatch.setattr(cli_entry_m30.prior_cli, "main", lambda argv: seen.append(list(argv)) or 17)
    argv = ["promotion-check", "candidate.json"]
    assert cli_entry_m30.main(argv) == 17
    assert seen == [argv]
