"""M19 isolated SEC/OpenDART debt component source mapping tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub.dart_live import DartTransportResponse, capture_dart_snapshot
from valuation_hub.debt_components import (
    CORE_COMPONENTS,
    extract_dart_debt_component_candidate,
    extract_sec_debt_component_candidate,
    normalize_debt_component_candidate,
)
from valuation_hub.sec_live import TransportResponse, capture_companyfacts_snapshot

ROOT = Path(__file__).resolve().parents[1]
DART_FIXTURE = ROOT / "tests" / "fixtures" / "opendart_financials_sample.json"
SEC_FIXTURE = ROOT / "tests" / "fixtures" / "sec_companyfacts_sample.json"
DART_KEY = "K" * 40
SEC_AGENT = "Valuation-Intelligence-Hub test@example.com"


def _dart_snapshot() -> dict:
    payload = json.loads(DART_FIXTURE.read_text(encoding="utf-8"))
    rows = payload["list"]
    specs = [
        ("ifrs-full_ShorttermBorrowings", "단기차입금", "10"),
        ("ifrs-full_CurrentPortionOfLongtermBorrowings", "유동성장기차입금", "20"),
        ("ifrs-full_LongtermBorrowings", "장기차입금", "30"),
        ("ifrs-full_CurrentPortionOfBondsIssued", "유동성사채", "40"),
        ("ifrs-full_BondsIssued", "사채", "50"),
    ]
    for offset, (account_id, account_nm, amount) in enumerate(specs, start=80):
        rows.append({
            "rcept_no": "20260814000123", "reprt_code": "11012", "bsns_year": "2026", "corp_code": "00126380", "stock_code": "005930", "fs_div": "CFS", "fs_nm": "연결재무제표",
            "sj_div": "BS", "sj_nm": "재무상태표", "account_id": account_id, "account_nm": account_nm, "account_detail": "-", "thstrm_nm": "제58기 반기말", "thstrm_amount": amount, "ord": str(offset), "currency": "KRW"
        })
    body = json.dumps(payload, ensure_ascii=False).encode()
    def transport(locator: str, *, api_key: str) -> DartTransportResponse:
        assert api_key == DART_KEY
        return DartTransportResponse(200, "application/json", body, locator)
    return capture_dart_snapshot("00126380", "2026", "11012", "CFS", api_key=DART_KEY, transport=transport, fetched_at="2026-09-12T04:00:00+00:00")


def _sec_snapshot() -> dict:
    payload = json.loads(SEC_FIXTURE.read_text(encoding="utf-8"))
    payload["facts"]["us-gaap"]["ShortTermBorrowings"] = {
        "label": "Short-Term Borrowings",
        "units": {"USD": [{"end": "2026-03-31", "val": 123000000, "accn": "0001234567-26-000020", "fy": 2026, "fp": "Q1", "form": "10-Q", "filed": "2026-05-05", "frame": "CY2026Q1I"}]},
    }
    body = json.dumps(payload).encode()
    def transport(locator: str, *, user_agent: str) -> TransportResponse:
        assert user_agent == SEC_AGENT
        return TransportResponse(200, "application/json", body, locator)
    return capture_companyfacts_snapshot("1234567", user_agent=SEC_AGENT, transport=transport, fetched_at="2026-09-12T04:00:00+00:00")


def test_opendart_all_five_core_components_extract_exact_account_lineage() -> None:
    snapshot = _dart_snapshot()
    expected = [10, 20, 30, 40, 50]
    for metric, amount in zip(CORE_COMPONENTS, expected, strict=True):
        candidate = extract_dart_debt_component_candidate(snapshot, metric)
        assert candidate["metric"] == metric
        assert candidate["value"] == amount
        assert candidate["statement_section"] == "BS"
        assert candidate["account_selection"]["kind"] == "account_id"
        observation = normalize_debt_component_candidate(candidate)
        assert observation["metric"] == metric
        assert observation["period"]["kind"] == "INSTANT"
        assert observation["lineage"]["source_detail"]["account_id"].startswith("ifrs-full_")


def test_sec_v01_extracts_only_exact_short_term_borrowings() -> None:
    snapshot = _sec_snapshot()
    candidate = extract_sec_debt_component_candidate(snapshot, "short_term_borrowings")
    assert candidate["value"] == 123000000
    assert candidate["taxonomy"] == "us-gaap"
    assert candidate["concept"] == "ShortTermBorrowings"
    observation = normalize_debt_component_candidate(candidate)
    assert observation["period"]["kind"] == "INSTANT"
    assert observation["lineage"]["source_detail"] == {"taxonomy": "us-gaap", "concept": "ShortTermBorrowings", "frame": "CY2026Q1I"}
    with pytest.raises(CaseServiceError, match="unsupported SEC debt component|미지원 SEC debt 구성요소"):
        extract_sec_debt_component_candidate(snapshot, "long_term_borrowings")
