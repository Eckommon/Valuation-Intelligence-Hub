"""M13 SEC live-evidence acquisition tests / SEC live 근거 수집 테스트."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub.sec_live import (
    METRIC_SPECS,
    SecRateLimiter,
    TransportResponse,
    capture_companyfacts_snapshot,
    companyfacts_locator,
    extract_sec_evidence_candidate,
    materialize_source_snapshot,
    normalize_cik,
    validate_source_snapshot,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "sec_companyfacts_sample.json"
FETCHED_AT = "2026-09-11T06:30:00+00:00"


def _body() -> bytes:
    return FIXTURE.read_bytes()


def _transport(body: bytes | None = None, *, final_locator: str | None = None, content_type: str = "application/json; charset=utf-8"):
    payload = body if body is not None else _body()

    def fake(locator: str, *, user_agent: str) -> TransportResponse:
        assert user_agent == "Valuation-Intelligence-Hub test@example.com"
        return TransportResponse(
            status=200,
            content_type=content_type,
            body=payload,
            final_locator=final_locator or locator,
            etag='"fixture-etag"',
            last_modified="Fri, 11 Sep 2026 06:00:00 GMT",
        )

    return fake


def _snapshot() -> dict:
    return capture_companyfacts_snapshot(
        "1234567",
        user_agent="Valuation-Intelligence-Hub test@example.com",
        transport=_transport(),
        fetched_at=FETCHED_AT,
    )


def test_cik_and_locator_are_deterministic() -> None:
    assert normalize_cik(1234567) == "0001234567"
    assert normalize_cik("0001234567") == "0001234567"
    assert companyfacts_locator("1234567") == "https://data.sec.gov/api/xbrl/companyfacts/CIK0001234567.json"
    with pytest.raises(CaseServiceError, match="CIK"):
        normalize_cik("12A")


def test_snapshot_capture_is_hash_locked_and_never_persists_user_agent() -> None:
    left = _snapshot()
    right = _snapshot()
    assert left == right
    assert left["canonical"] is False
    assert left["status"] == "SOURCE_SNAPSHOT_CAPTURED"
    assert left["source"]["tier"] == "A"
    assert left["request"] == {"method": "GET", "cik": "0001234567", "user_agent_provided": True}
    assert "test@example.com" not in json.dumps(left, ensure_ascii=False)
    result = validate_source_snapshot(left)
    assert result["status"] == "PASS_SOURCE_SNAPSHOT_VALIDATION"
    assert len(result["snapshot_sha256"]) == 64

    tampered = copy.deepcopy(left)
    tampered["raw_text"] = tampered["raw_text"].replace("280000000", "280000001", 1)
    with pytest.raises(CaseServiceError, match="hash|해시"):
        validate_source_snapshot(tampered)


def test_snapshot_rejects_identity_host_content_type_and_invalid_json() -> None:
    wrong = json.loads(_body())
    wrong["cik"] = 7654321
    with pytest.raises(CaseServiceError, match="CIK"):
        capture_companyfacts_snapshot(
            1234567,
            user_agent="Valuation-Intelligence-Hub test@example.com",
            transport=_transport(json.dumps(wrong).encode()),
            fetched_at=FETCHED_AT,
        )

    with pytest.raises(CaseServiceError, match="host"):
        capture_companyfacts_snapshot(
            1234567,
            user_agent="Valuation-Intelligence-Hub test@example.com",
            transport=_transport(final_locator="https://example.com/companyfacts.json"),
            fetched_at=FETCHED_AT,
        )

    with pytest.raises(CaseServiceError, match="JSON"):
        capture_companyfacts_snapshot(
            1234567,
            user_agent="Valuation-Intelligence-Hub test@example.com",
            transport=_transport(content_type="text/html"),
            fetched_at=FETCHED_AT,
        )

    with pytest.raises(CaseServiceError, match="JSON"):
        capture_companyfacts_snapshot(
            1234567,
            user_agent="Valuation-Intelligence-Hub test@example.com",
            transport=_transport(b"not-json"),
            fetched_at=FETCHED_AT,
        )


def test_metric_extraction_preserves_exact_filing_provenance_and_fallback() -> None:
    snapshot = _snapshot()
    revenue = extract_sec_evidence_candidate(snapshot, "revenue")
    assert revenue["status"] == "EVIDENCE_CANDIDATE_UNREVIEWED"
    assert revenue["canonical"] is False
    assert revenue["class"] == "FACT_CANDIDATE"
    assert revenue["value"] == 280000000
    assert revenue["unit"] == "USD"
    assert revenue["concept"] == "RevenueFromContractWithCustomerExcludingAssessedTax"
    assert revenue["filing"] == {
        "accession": "0001234567-26-000020",
        "form": "10-Q",
        "filed": "2026-05-05",
    }
    assert revenue["period"]["start"] == "2026-01-01"
    assert revenue["period"]["end"] == "2026-03-31"
    assert revenue["source"]["snapshot_sha256"] == snapshot["snapshot_sha256"]

    net_income = extract_sec_evidence_candidate(snapshot, "net_income")
    assert net_income["concept"] == "ProfitLoss"
    assert net_income["concept_fallback_used"] is True
    assert net_income["concept_fallback_index"] == 1
    assert net_income["value"] == 31000000

    shares = extract_sec_evidence_candidate(snapshot, "shares_outstanding")
    assert shares["taxonomy"] == "dei"
    assert shares["unit"] == "shares"
    assert shares["value"] == 50500000
    assert shares["period"]["end"] == "2026-04-30"


def test_form_and_period_filters_are_explicit() -> None:
    snapshot = _snapshot()
    annual = extract_sec_evidence_candidate(snapshot, "revenue", form="10-K", period_end="2025-12-31")
    assert annual["value"] == 1000000000
    assert annual["filing"]["form"] == "10-K"
    assert annual["selection"]["requested_period_end"] == "2025-12-31"
    with pytest.raises(CaseServiceError, match="form"):
        extract_sec_evidence_candidate(snapshot, "revenue", form="8-K")
    with pytest.raises(CaseServiceError, match="no SEC fact"):
        extract_sec_evidence_candidate(snapshot, "revenue", period_end="2020-01-01")
    with pytest.raises(CaseServiceError, match="unsupported SEC metric"):
        extract_sec_evidence_candidate(snapshot, "ebitda")


def test_equal_precedence_conflicting_values_fail_closed() -> None:
    payload = json.loads(_body())
    series = payload["facts"]["us-gaap"]["OperatingIncomeLoss"]["units"]["USD"]
    conflict = copy.deepcopy(series[0])
    conflict["val"] = 43000000
    conflict["accn"] = "0001234567-26-000021"
    series.append(conflict)
    snapshot = capture_companyfacts_snapshot(
        1234567,
        user_agent="Valuation-Intelligence-Hub test@example.com",
        transport=_transport(json.dumps(payload, separators=(",", ":")).encode()),
        fetched_at=FETCHED_AT,
    )
    with pytest.raises(CaseServiceError, match="conflict|충돌"):
        extract_sec_evidence_candidate(snapshot, "operating_income")


def test_same_value_duplicates_at_equal_precedence_are_deterministic() -> None:
    payload = json.loads(_body())
    series = payload["facts"]["us-gaap"]["OperatingIncomeLoss"]["units"]["USD"]
    duplicate = copy.deepcopy(series[0])
    duplicate["accn"] = "0001234567-26-000021"
    series.append(duplicate)
    snapshot = capture_companyfacts_snapshot(
        1234567,
        user_agent="Valuation-Intelligence-Hub test@example.com",
        transport=_transport(json.dumps(payload, separators=(",", ":")).encode()),
        fetched_at=FETCHED_AT,
    )
    candidate = extract_sec_evidence_candidate(snapshot, "operating_income")
    assert candidate["value"] == 42000000
    assert candidate["selection"]["equal_precedence_count"] == 2
    assert candidate["filing"]["accession"] == "0001234567-26-000021"


def test_rate_limiter_enforces_conservative_interval() -> None:
    now = [10.0]
    sleeps: list[float] = []

    def clock() -> float:
        return now[0]

    def sleeper(delay: float) -> None:
        sleeps.append(delay)
        now[0] += delay

    limiter = SecRateLimiter(min_interval=0.11, clock=clock, sleeper=sleeper)
    limiter.acquire()
    now[0] += 0.03
    limiter.acquire()
    assert len(sleeps) == 1
    assert sleeps[0] == pytest.approx(0.08)


def test_materialization_is_workspace_only_and_no_overwrite(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "workspace" / "source_snapshots").mkdir(parents=True)
    snapshot = _snapshot()
    output = repo / "workspace" / "source_snapshots" / "fixture.json"
    result = materialize_source_snapshot(snapshot, output, repo)
    assert result["status"] == "SOURCE_SNAPSHOT_MATERIALIZED"
    assert output.is_file()
    with pytest.raises(CaseServiceError, match="already exists|이미 존재"):
        materialize_source_snapshot(snapshot, output, repo)
    with pytest.raises(CaseServiceError, match="workspace/source_snapshots"):
        materialize_source_snapshot(snapshot, repo / "outside.json", repo)


def test_metric_registry_contains_initial_supported_set() -> None:
    assert set(METRIC_SPECS) == {
        "revenue",
        "operating_income",
        "net_income",
        "assets",
        "cash",
        "shares_outstanding",
    }
