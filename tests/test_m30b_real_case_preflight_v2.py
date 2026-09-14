from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub.real_case_preflight_m30b import (
    LEGACY_DEBT_BLOCKER,
    NEXT_DEBT_REVIEW,
    STATUS_HOLD,
    STATUS_PASS,
    SUCCESSOR_DEBT_BLOCKER,
    build_real_equity_source_preflight_v2,
    validate_real_equity_source_preflight_v2,
)
from valuation_hub.sec_live import TransportResponse, capture_companyfacts_snapshot, companyfacts_locator

CIK = "0001046257"
ACCN = "0001628280-26-054722"
DEBT = 1_783_000_000


def _repo(tmp_path: Path, *, collision: bool = False) -> Path:
    (tmp_path / "registry").mkdir()
    cases = [{
        "case_id": "US_INGR_INGREDION" if collision else "US_EXISTING_CASE",
        "display_name_en": "Existing",
        "display_name_ko": "기존",
        "asset_class": "Public Equity",
        "model": "equity_fcff",
        "path": "analyses/equities/existing",
    }]
    (tmp_path / "registry" / "cases.json").write_text(json.dumps({"cases": cases}), encoding="utf-8")
    return tmp_path


def _payload(*, include_debt: bool = True, debt_values: list[int] | None = None) -> dict:
    us_gaap: dict[str, dict] = {
        "CashAndCashEquivalentsAtCarryingValue": {"units": {"USD": [
            {"val": 948_000_000, "end": "2026-06-30", "fy": 2026, "fp": "Q2", "form": "10-Q", "filed": "2026-08-07", "accn": ACCN}
        ]}},
        "ShortTermBorrowings": {"units": {"USD": [
            {"val": 41_000_000, "end": "2026-06-30", "fy": 2026, "fp": "Q2", "form": "10-Q", "filed": "2026-08-07", "accn": ACCN}
        ]}},
        "NonredeemableNoncontrollingInterest": {"units": {"USD": [
            {"val": 0, "end": "2026-06-30", "fy": 2026, "fp": "Q2", "form": "10-Q", "filed": "2026-08-07", "accn": ACCN}
        ]}},
    }
    if include_debt:
        us_gaap["DebtLongtermAndShorttermCombinedAmount"] = {"units": {"USD": [
            {"val": value, "end": "2026-06-30", "fy": 2026, "fp": "Q2", "form": "10-Q", "filed": "2026-08-07", "accn": ACCN}
            for value in (debt_values or [DEBT])
        ]}}
    return {
        "cik": 1046257,
        "entityName": "Ingredion Incorporated",
        "facts": {
            "us-gaap": us_gaap,
            "dei": {"EntityCommonStockSharesOutstanding": {"units": {"shares": [
                {"val": 63_063_979, "end": "2026-08-05", "fy": 2026, "fp": "Q2", "form": "10-Q", "filed": "2026-08-07", "accn": ACCN}
            ]}}},
        },
    }


def _snapshot(*, include_debt: bool = True, debt_values: list[int] | None = None) -> dict:
    body = json.dumps(_payload(include_debt=include_debt, debt_values=debt_values), separators=(",", ":")).encode()

    def transport(locator: str, *, user_agent: str):
        assert locator == companyfacts_locator(CIK)
        assert user_agent == "M30B-test test@example.com"
        return TransportResponse(200, "application/json; charset=utf-8", body, locator)

    return capture_companyfacts_snapshot(CIK, user_agent="M30B-test test@example.com", transport=transport, fetched_at="2026-09-14T00:00:00+00:00")


def _build(root: Path, snapshot: dict | None):
    return build_real_equity_source_preflight_v2(
        case_id="US_INGR_INGREDION",
        legal_name="Ingredion Incorporated",
        ticker="INGR",
        exchange="NYSE",
        cik=CIK,
        financial_period_end="2026-06-30",
        valuation_as_of="2026-09-14",
        sec_snapshot=snapshot,
        root=root,
        form="10-Q",
    )


def test_v2_resolves_only_legacy_debt_architecture_and_stops_at_human_review(tmp_path: Path) -> None:
    result = _build(_repo(tmp_path), _snapshot())
    assert result["status"] == STATUS_PASS
    assert result["next_action"] == NEXT_DEBT_REVIEW
    assert result["blockers"] == []
    assert result["checks"]["cash_candidate"]["value"] == 948_000_000
    assert result["checks"]["shares_candidate"]["value"] == 63_063_979
    assert result["checks"]["minority_interest_candidate"]["explicit_zero"] is True
    debt = result["checks"]["sec_aggregate_debt_candidate"]
    assert debt["value"] == DEBT
    assert debt["source_identity"] == {"taxonomy": "us-gaap", "concept": "DebtLongtermAndShorttermCombinedAmount"}
    assert debt["requires_human_semantic_review"] is True
    assert debt["review_may_be_inferred"] is False
    assert result["checks"]["us_sec_debt_profile"]["successor_candidate_available"] is True
    assert any(item["code"] == LEGACY_DEBT_BLOCKER for item in result["base_v01_preflight"]["blockers"])
    assert all(item["code"] != LEGACY_DEBT_BLOCKER for item in result["blockers"])
    checked = validate_real_equity_source_preflight_v2(result)
    assert checked["decision"] == STATUS_PASS
    assert checked["successor_debt_candidate_available"] is True


def test_v2_missing_exact_aggregate_debt_becomes_source_blocker_not_legacy_blocker(tmp_path: Path) -> None:
    result = _build(_repo(tmp_path), _snapshot(include_debt=False))
    assert result["status"] == STATUS_HOLD
    codes = {item["code"] for item in result["blockers"]}
    assert SUCCESSOR_DEBT_BLOCKER in codes
    assert LEGACY_DEBT_BLOCKER not in codes
    assert result["checks"]["sec_aggregate_debt_candidate"] is None


def test_v2_equal_precedence_aggregate_debt_conflict_fails_closed(tmp_path: Path) -> None:
    result = _build(_repo(tmp_path), _snapshot(debt_values=[DEBT, DEBT + 1]))
    assert result["status"] == STATUS_HOLD
    blocker = next(item for item in result["blockers"] if item["code"] == SUCCESSOR_DEBT_BLOCKER)
    assert "conflict" in blocker["detail"] or "충돌" in blocker["detail"]


def test_v2_snapshot_absence_retains_runtime_source_blocker_but_not_resolved_architecture(tmp_path: Path) -> None:
    result = _build(_repo(tmp_path), None)
    codes = {item["code"] for item in result["blockers"]}
    assert "SEC_SOURCE_SNAPSHOT_REQUIRED" in codes
    assert LEGACY_DEBT_BLOCKER not in codes
    assert result["status"] == STATUS_HOLD


def test_v2_registry_collision_still_blocks(tmp_path: Path) -> None:
    result = _build(_repo(tmp_path, collision=True), _snapshot())
    assert "REGISTRY_CASE_ID_COLLISION" in {item["code"] for item in result["blockers"]}


def test_v2_resigned_projection_tamper_fails_independent_validator(tmp_path: Path) -> None:
    result = _build(_repo(tmp_path), _snapshot())
    tampered = copy.deepcopy(result)
    tampered["checks"]["sec_aggregate_debt_candidate"]["source_identity"]["concept"] = "Liabilities"
    unsigned = copy.deepcopy(tampered)
    unsigned.pop("preflight_sha256")
    tampered["preflight_sha256"] = hashlib.sha256(json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    with pytest.raises(CaseServiceError, match="exact aggregate debt identity|exact aggregate debt 식별"):
        validate_real_equity_source_preflight_v2(tampered)
