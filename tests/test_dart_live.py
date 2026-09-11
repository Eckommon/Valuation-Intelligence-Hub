"""M14 OpenDART immutable live-evidence tests / OpenDART 불변 live 근거 테스트."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub.dart_live import (
    DART_METRIC_SPECS,
    DartRateLimiter,
    DartTransportResponse,
    capture_dart_snapshot,
    dart_sanitized_locator,
    extract_dart_evidence_candidate,
    materialize_dart_snapshot,
    validate_dart_snapshot,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "opendart_financials_sample.json"
KEY = "K" * 40
FETCHED_AT = "2026-09-11T07:40:00+00:00"


def _body() -> bytes:
    return FIXTURE.read_bytes()


def _transport(body: bytes | None = None, *, final_locator: str | None = None, content_type: str = "application/json; charset=utf-8"):
    payload = _body() if body is None else body

    def fake(locator: str, *, api_key: str) -> DartTransportResponse:
        assert api_key == KEY
        return DartTransportResponse(
            status=200,
            content_type=content_type,
            body=payload,
            sanitized_final_locator=final_locator or locator,
            etag='"dart-fixture"',
            last_modified="Fri, 11 Sep 2026 07:30:00 GMT",
        )

    return fake


def _snapshot() -> dict:
    return capture_dart_snapshot(
        "00126380",
        "2026",
        "11012",
        "CFS",
        api_key=KEY,
        transport=_transport(),
        fetched_at=FETCHED_AT,
    )


def test_sanitized_locator_is_deterministic_and_secret_free() -> None:
    locator = dart_sanitized_locator("00126380", 2026, "11012", "cfs")
    assert locator.startswith("https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json?")
    assert "corp_code=00126380" in locator
    assert "fs_div=CFS" in locator
    assert "crtfc_key" not in locator
    with pytest.raises(CaseServiceError, match="corp_code"):
        dart_sanitized_locator("123", 2026, "11012", "CFS")
    with pytest.raises(CaseServiceError, match="reprt_code"):
        dart_sanitized_locator("00126380", 2026, "BAD", "CFS")
    with pytest.raises(CaseServiceError, match="fs_div"):
        dart_sanitized_locator("00126380", 2026, "11012", "BAD")


def test_snapshot_is_hash_locked_noncanonical_and_never_contains_api_key() -> None:
    left = _snapshot()
    right = _snapshot()
    assert left == right
    assert left["canonical"] is False
    assert left["status"] == "SOURCE_SNAPSHOT_CAPTURED"
    assert left["request"]["api_key_provided"] is True
    dumped = json.dumps(left, ensure_ascii=False)
    assert KEY not in dumped
    assert "crtfc_key" not in dumped
    result = validate_dart_snapshot(left)
    assert result["status"] == "PASS_DART_SOURCE_SNAPSHOT_VALIDATION"
    assert result["corp_code"] == "00126380"

    tampered = copy.deepcopy(left)
    tampered["raw_text"] = tampered["raw_text"].replace("500,000,000,000", "500,000,000,001", 1)
    with pytest.raises(CaseServiceError, match="hash|해시"):
        validate_dart_snapshot(tampered)


def test_api_status_and_request_identity_fail_closed() -> None:
    payload = json.loads(_body())
    payload["status"] = "013"
    payload["message"] = "조회된 데이타가 없습니다."
    with pytest.raises(CaseServiceError, match="status 013"):
        capture_dart_snapshot("00126380", 2026, "11012", "CFS", api_key=KEY, transport=_transport(json.dumps(payload).encode()), fetched_at=FETCHED_AT)

    payload = json.loads(_body())
    payload["list"][0]["corp_code"] = "99999999"
    with pytest.raises(CaseServiceError, match="corp_code"):
        capture_dart_snapshot("00126380", 2026, "11012", "CFS", api_key=KEY, transport=_transport(json.dumps(payload).encode()), fetched_at=FETCHED_AT)

    with pytest.raises(CaseServiceError, match="endpoint|locator"):
        capture_dart_snapshot("00126380", 2026, "11012", "CFS", api_key=KEY, transport=_transport(final_locator="https://example.com/api.json"), fetched_at=FETCHED_AT)


def test_extraction_prefers_account_id_and_preserves_row_provenance() -> None:
    snapshot = _snapshot()
    revenue = extract_dart_evidence_candidate(snapshot, "revenue")
    assert revenue["status"] == "DART_EVIDENCE_CANDIDATE_UNREVIEWED"
    assert revenue["canonical"] is False
    assert revenue["class"] == "FACT_CANDIDATE"
    assert revenue["value"] == 165_000_000_000
    assert revenue["unit"] == "KRW"
    assert revenue["statement_section"] == "IS"
    assert revenue["account_selection"]["kind"] == "account_id"
    assert revenue["account_selection"]["fallback_used"] is False
    assert revenue["row"]["account_id"] == "ifrs-full_Revenue"
    assert revenue["row"]["rcept_no"] == "20260814000123"
    assert revenue["source"]["snapshot_sha256"] == snapshot["snapshot_sha256"]


def test_exact_account_name_fallback_is_visible_and_statement_scope_is_not_crossed() -> None:
    snapshot = _snapshot()
    cash = extract_dart_evidence_candidate(snapshot, "cash")
    assert cash["value"] == 52_000_000_000
    assert cash["account_selection"]["kind"] == "account_nm"
    assert cash["account_selection"]["fallback_used"] is True

    profit = extract_dart_evidence_candidate(snapshot, "net_income")
    assert profit["value"] == 18_000_000_000
    assert profit["statement_section"] == "IS"
    assert profit["row"]["sj_div"] == "IS"
    assert profit["row"]["thstrm_amount"] == "18,000,000,000"
    with pytest.raises(CaseServiceError, match="statement section"):
        extract_dart_evidence_candidate(snapshot, "net_income", statement_section="CF")


def test_equal_precedence_conflict_fails_closed() -> None:
    payload = json.loads(_body())
    row = copy.deepcopy(next(item for item in payload["list"] if item.get("account_id") == "ifrs-full_Revenue"))
    row["rcept_no"] = "20260814000124"
    row["thstrm_amount"] = "166,000,000,000"
    payload["list"].append(row)
    snapshot = capture_dart_snapshot("00126380", 2026, "11012", "CFS", api_key=KEY, transport=_transport(json.dumps(payload, ensure_ascii=False).encode()), fetched_at=FETCHED_AT)
    with pytest.raises(CaseServiceError, match="conflict|충돌"):
        extract_dart_evidence_candidate(snapshot, "revenue")


def test_same_value_duplicate_is_deterministic() -> None:
    payload = json.loads(_body())
    row = copy.deepcopy(next(item for item in payload["list"] if item.get("account_id") == "ifrs-full_Revenue"))
    row["rcept_no"] = "20260814000124"
    payload["list"].append(row)
    snapshot = capture_dart_snapshot("00126380", 2026, "11012", "CFS", api_key=KEY, transport=_transport(json.dumps(payload, ensure_ascii=False).encode()), fetched_at=FETCHED_AT)
    candidate = extract_dart_evidence_candidate(snapshot, "revenue")
    assert candidate["value"] == 165_000_000_000
    assert candidate["account_selection"]["equal_precedence_count"] == 2
    assert candidate["row"]["rcept_no"] == "20260814000124"


def test_rate_limiter_enforces_conservative_interval() -> None:
    now = [2.0]
    sleeps: list[float] = []

    def clock() -> float:
        return now[0]

    def sleeper(delay: float) -> None:
        sleeps.append(delay)
        now[0] += delay

    limiter = DartRateLimiter(min_interval=0.11, clock=clock, sleeper=sleeper)
    limiter.acquire()
    now[0] += 0.04
    limiter.acquire()
    assert sleeps == pytest.approx([0.07])


def test_materialization_is_workspace_only_and_refuses_overwrite(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "workspace" / "source_snapshots").mkdir(parents=True)
    snapshot = _snapshot()
    output = repo / "workspace" / "source_snapshots" / "dart.json"
    result = materialize_dart_snapshot(snapshot, output, repo)
    assert result["status"] == "DART_SOURCE_SNAPSHOT_MATERIALIZED"
    with pytest.raises(CaseServiceError, match="already exists|이미 존재"):
        materialize_dart_snapshot(snapshot, output, repo)
    with pytest.raises(CaseServiceError, match="workspace/source_snapshots"):
        materialize_dart_snapshot(snapshot, repo / "outside.json", repo)


def test_initial_metric_registry_is_explicit() -> None:
    assert set(DART_METRIC_SPECS) == {"revenue", "operating_income", "net_income", "assets", "cash", "equity", "liabilities"}
