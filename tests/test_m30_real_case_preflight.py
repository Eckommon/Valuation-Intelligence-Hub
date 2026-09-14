from __future__ import annotations

import json
from pathlib import Path

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub.real_case_preflight import (
    HOLD_STATUS,
    build_real_equity_source_preflight,
    validate_real_equity_source_preflight,
)
from valuation_hub.sec_live import TransportResponse, capture_companyfacts_snapshot, companyfacts_locator

CIK = "0001046257"
ACCN = "0001628280-26-054722"


def _repo(tmp_path: Path, *, collision: bool = False) -> Path:
    (tmp_path / "registry").mkdir()
    cases = [
        {
            "case_id": "US_INGR_INGREDION" if collision else "US_EXISTING_CASE",
            "display_name_en": "Existing",
            "display_name_ko": "기존",
            "asset_class": "Public Equity",
            "model": "equity_fcff",
            "path": "analyses/equities/existing",
        }
    ]
    (tmp_path / "registry" / "cases.json").write_text(
        json.dumps({"cases": cases}, ensure_ascii=False), encoding="utf-8"
    )
    return tmp_path


def _payload(*, include_nci: bool = True, nci_value: int = 0) -> dict:
    us_gaap = {
        "CashAndCashEquivalentsAtCarryingValue": {
            "units": {
                "USD": [
                    {"val": 948_000_000, "end": "2026-06-30", "fy": 2026, "fp": "Q2", "form": "10-Q", "filed": "2026-08-07", "accn": ACCN}
                ]
            }
        },
        "ShortTermBorrowings": {
            "units": {
                "USD": [
                    {"val": 41_000_000, "end": "2026-06-30", "fy": 2026, "fp": "Q2", "form": "10-Q", "filed": "2026-08-07", "accn": ACCN}
                ]
            }
        },
    }
    if include_nci:
        us_gaap["NonredeemableNoncontrollingInterest"] = {
            "units": {
                "USD": [
                    {"val": nci_value, "end": "2026-06-30", "fy": 2026, "fp": "Q2", "form": "10-Q", "filed": "2026-08-07", "accn": ACCN}
                ]
            }
        }
    return {
        "cik": 1046257,
        "entityName": "Ingredion Incorporated",
        "facts": {
            "us-gaap": us_gaap,
            "dei": {
                "EntityCommonStockSharesOutstanding": {
                    "units": {
                        "shares": [
                            {"val": 63_063_979, "end": "2026-08-05", "fy": 2026, "fp": "Q2", "form": "10-Q", "filed": "2026-08-07", "accn": ACCN}
                        ]
                    }
                }
            },
        },
    }


def _snapshot(*, include_nci: bool = True, nci_value: int = 0) -> dict:
    body = json.dumps(_payload(include_nci=include_nci, nci_value=nci_value), separators=(",", ":")).encode()

    def transport(locator: str, *, user_agent: str):
        assert locator == companyfacts_locator(CIK)
        assert user_agent == "M30-test test@example.com"
        return TransportResponse(
            status=200,
            content_type="application/json; charset=utf-8",
            body=body,
            final_locator=locator,
        )

    return capture_companyfacts_snapshot(
        CIK,
        user_agent="M30-test test@example.com",
        transport=transport,
        fetched_at="2026-09-14T00:00:00+00:00",
    )


def _build(root: Path, snapshot: dict | None):
    return build_real_equity_source_preflight(
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


def test_real_snapshot_probe_preserves_explicit_zero_and_fails_on_known_debt_prerequisite(tmp_path: Path):
    result = _build(_repo(tmp_path), _snapshot())
    assert result["status"] == HOLD_STATUS
    assert result["checks"]["cash_candidate"]["value"] == 948_000_000
    assert result["checks"]["shares_candidate"]["value"] == 63_063_979
    minority = result["checks"]["minority_interest_candidate"]
    assert minority["value"] == 0
    assert minority["explicit_zero"] is True
    assert minority["source_identity"] == {
        "taxonomy": "us-gaap",
        "concept": "NonredeemableNoncontrollingInterest",
        "form": "10-Q",
        "accession": ACCN,
        "filed": "2026-08-07",
    }
    codes = {item["code"] for item in result["blockers"]}
    assert codes == {"M19_SEC_COMPLETE_DEBT_PROFILE_UNAVAILABLE"}
    assert result["checks"]["us_sec_debt_profile"]["complete_profile_supported"] is False
    assert result["human_review_boundary"]["automatic_approval_forbidden"] is True
    assert validate_real_equity_source_preflight(result)["decision"] == HOLD_STATUS


def test_missing_nci_is_not_interpreted_as_zero(tmp_path: Path):
    result = _build(_repo(tmp_path), _snapshot(include_nci=False))
    codes = {item["code"] for item in result["blockers"]}
    assert "SEC_EXACT_MINORITY_INTEREST_UNAVAILABLE" in codes
    assert result["checks"]["minority_interest_candidate"] is None


def test_snapshot_absence_is_explicit_runtime_blocker(tmp_path: Path):
    result = _build(_repo(tmp_path), None)
    codes = {item["code"] for item in result["blockers"]}
    assert "SEC_SOURCE_SNAPSHOT_REQUIRED" in codes
    assert "M19_SEC_COMPLETE_DEBT_PROFILE_UNAVAILABLE" in codes
    assert result["checks"]["cash_candidate"] is None


def test_registry_collision_blocks_even_with_valid_snapshot(tmp_path: Path):
    result = _build(_repo(tmp_path, collision=True), _snapshot())
    codes = {item["code"] for item in result["blockers"]}
    assert "REGISTRY_CASE_ID_COLLISION" in codes


def test_tampered_preflight_hash_fails_closed(tmp_path: Path):
    result = _build(_repo(tmp_path), _snapshot())
    result["target"]["ticker"] = "FAKE"
    with pytest.raises(CaseServiceError, match="SHA"):
        validate_real_equity_source_preflight(result)
