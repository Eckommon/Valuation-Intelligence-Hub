from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from valuation_hub import cli_entry_m30r6
from valuation_hub.ai_dilution_authority import (
    ABSENT_SUPPORTED,
    BLOCKED_DEPENDENCY,
    HOLD,
    PRESENT,
    UNKNOWN_CONFLICT,
    EXPLICIT_COUNT_METHOD,
    build_ai_dilution_inventory,
)
from valuation_hub.case_service import CaseServiceError
from valuation_hub.disclosure_limited_dilution import (
    ADJUDICATOR_ID,
    APPROVE,
    HOLD_MATERIALITY,
    ROLE_ANCHOR,
    ROLE_BUFFER,
    ROLE_PERFORMANCE_UPLIFT,
    ROLE_SUBSEQUENT,
    build_disclosure_limited_dilution_adjudication,
    build_disclosure_limited_dilution_evidence,
    finalize_disclosure_limited_dilution_assumption,
    validate_disclosure_limited_dilution_adjudication,
    validate_disclosure_limited_dilution_assumption,
    validate_disclosure_limited_dilution_evidence,
)
from valuation_hub.sec_live import TransportResponse, capture_companyfacts_snapshot
from valuation_hub.share_dilution import (
    derive_historical_dilution,
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
        json.dumps(copied, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _snapshot() -> dict:
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
                            "form": "10-Q",
                            "filed": "2026-08-07",
                            "fy": 2026,
                            "fp": "Q2",
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
                            "form": "10-Q",
                            "filed": "2026-08-07",
                            "fy": 2026,
                            "fp": "Q2",
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
        user_agent="M30R6 test@example.com",
        transport=transport,
        fetched_at="2026-09-15T17:42:53+00:00",
    )


def _base() -> dict:
    candidate = extract_sec_current_common_shares_candidate(_snapshot(), period_end="2026-08-05", form="10-Q")
    candidate["class"] = "FACT"
    candidate["candidate_sha256"] = _sha(candidate, "candidate_sha256")
    observation = normalize_current_common_shares_candidate(candidate)
    return build_valuation_share_base_context(observation, as_of="2026-09-14")


def _historical() -> dict:
    snapshot = _snapshot()
    basic = extract_sec_dilution_candidate(
        snapshot, "weighted_average_basic_shares", period_start="2026-04-01", period_end="2026-06-30", form="10-Q"
    )
    diluted = extract_sec_dilution_candidate(
        snapshot, "weighted_average_diluted_shares", period_start="2026-04-01", period_end="2026-06-30", form="10-Q"
    )
    for candidate in (basic, diluted):
        candidate["class"] = "FACT"
        candidate["candidate_sha256"] = _sha(candidate, "candidate_sha256")
    return derive_historical_dilution(
        normalize_share_dilution_candidate(basic),
        normalize_share_dilution_candidate(diluted),
    )


def _source(seed: str) -> list[dict]:
    return [{"locator": f"repo://issuer/{seed}", "snapshot_sha256": seed * 64, "source_type": "issuer_filing_snapshot"}]


def _row(category: str, state: str, seed: str, **kwargs) -> dict:
    return {
        "category": category,
        "state": state,
        "sources": _source(seed),
        "evidence_basis": kwargs.get("basis", f"Issuer evidence for {category}."),
        "contradiction_search": {
            "performed": True,
            "summary": kwargs.get("summary", "No material contradiction identified."),
            "material_contradictions": kwargs.get("contradictions", []),
        },
        "dependencies": kwargs.get("dependencies", []),
        "adjustment_id": kwargs.get("adjustment_id"),
        "adjustment_shares": kwargs.get("adjustment_shares"),
        "calculation_method": kwargs.get("calculation_method"),
        "calculation_inputs": kwargs.get("calculation_inputs"),
    }


def _hold_inventory() -> dict:
    rows = [
        _row("options_treasury_stock_method", BLOCKED_DEPENDENCY, "a", dependencies=["complete_option_strike_distribution_for_valuation_date_tsm"]),
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
        _row("contingent_shares", BLOCKED_DEPENDENCY, "e", dependencies=["complete_point_in_time_payout_weighted_performance_award_count"]),
        _row("other_explicit", BLOCKED_DEPENDENCY, "f", dependencies=["current_director_and_deferred_equity_unit_count_as_of_2026_09_14"]),
    ]
    result = build_ai_dilution_inventory(_base(), rows)
    assert result["decision"] == HOLD
    return result


def _components(extra_anchor: float = 0.0) -> list[dict]:
    # Real-shaped conservative public envelope:
    # 2,177,904 securities at 2025-12-31, plus known 2026 gross grants,
    # a 200%-payout PSU uplift, and explicit disclosure-lag buffer.
    return [
        {
            "component_id": "2025YE_EQUITY_PLAN_SECURITIES",
            "role": ROLE_ANCHOR,
            "shares": 2_177_904 + extra_anchor,
            "as_of": "2025-12-31",
            "sources": _source("1"),
            "evidence_basis": "Proxy total securities underlying equity compensation plans at 2025-12-31; conservative no-netting anchor.",
        },
        {
            "component_id": "2026_YTD_RSU_GRANTS",
            "role": ROLE_SUBSEQUENT,
            "shares": 215_000,
            "as_of": "2026-06-30",
            "sources": _source("2"),
            "evidence_basis": "Issuer Q2 employee RSU grants through 2026-06-30.",
        },
        {
            "component_id": "2026_YTD_PSU_GRANTS",
            "role": ROLE_SUBSEQUENT,
            "shares": 116_000,
            "as_of": "2026-06-30",
            "sources": _source("3"),
            "evidence_basis": "Issuer Q2 performance-share grants through 2026-06-30.",
        },
        {
            "component_id": "PSU_200_PERCENT_MAX_UPLIFT",
            "role": ROLE_PERFORMANCE_UPLIFT,
            "shares": 267_570,
            "as_of": "2026-06-30",
            "sources": _source("4"),
            "evidence_basis": "Extra 100% uplift above the 100%-target PSU counts for 151,570 year-end units plus 116,000 2026 grants.",
        },
        {
            "component_id": "DISCLOSURE_LAG_BUFFER",
            "role": ROLE_BUFFER,
            "shares": 158_000,
            "as_of": "2026-09-14",
            "sources": _source("5"),
            "evidence_basis": "Explicit buffer for post-quarter unitemized awards through valuation date; not presented as a fact.",
        },
    ]


def _evidence(extra_anchor: float = 0.0) -> dict:
    return build_disclosure_limited_dilution_evidence(
        _base(),
        _hold_inventory(),
        _historical(),
        _components(extra_anchor),
        as_of="2026-09-14",
        materiality_threshold=0.05,
        max_historical_age_days=180,
    )


def test_real_shaped_disclosure_limited_envelope_selects_issuer_anchor_and_passes_materiality() -> None:
    evidence = _evidence()
    checked = validate_disclosure_limited_dilution_evidence(
        evidence, _base(), _hold_inventory(), _historical(), _components()
    )
    assert checked["decision"] == "READY_FOR_DISCLOSURE_LIMITED_DILUTION_ADJUDICATION"
    assert evidence["selection"]["historical_diluted_anchor"] == 63_900_000
    assert evidence["selection"]["exact_present_floor"] == 63_597_979
    assert evidence["selection"]["selected_shares"] == 63_900_000
    assert evidence["upper_envelope"]["upper_shares"] == 65_998_453
    assert evidence["upper_envelope"]["relative_upper_spread"] < 0.05
    assert evidence["semantic_boundary"]["direct_bind_as_m22_derived_fact"] is False


def test_materiality_gate_holds_when_public_upper_envelope_is_too_wide() -> None:
    evidence = _evidence(extra_anchor=3_000_000)
    assert evidence["decision"] == HOLD_MATERIALITY
    adjudication = build_disclosure_limited_dilution_adjudication(
        evidence, adjudicated_at="2026-09-29T12:00:00+09:00"
    )
    assert adjudication["decision"] == HOLD_MATERIALITY
    with pytest.raises(CaseServiceError, match="materiality"):
        finalize_disclosure_limited_dilution_assumption(evidence, adjudication)


def test_unknown_conflict_cannot_use_r6_fallback() -> None:
    rows = [
        _row("options_treasury_stock_method", UNKNOWN_CONFLICT, "a", contradictions=["Conflicting issuer evidence."]),
        _row("rsu_restricted_stock", ABSENT_SUPPORTED, "b"),
        _row("warrants", ABSENT_SUPPORTED, "c"),
        _row("convertibles_if_converted", ABSENT_SUPPORTED, "d"),
        _row("contingent_shares", ABSENT_SUPPORTED, "e"),
        _row("other_explicit", ABSENT_SUPPORTED, "f"),
    ]
    inventory = build_ai_dilution_inventory(_base(), rows)
    with pytest.raises(CaseServiceError, match="UNKNOWN_CONFLICT"):
        build_disclosure_limited_dilution_evidence(
            _base(), inventory, _historical(), _components(), as_of="2026-09-14"
        )


def test_exact_ready_r4_path_outranks_fallback() -> None:
    rows = [
        _row("options_treasury_stock_method", ABSENT_SUPPORTED, "a"),
        _row("rsu_restricted_stock", ABSENT_SUPPORTED, "b"),
        _row("warrants", ABSENT_SUPPORTED, "c"),
        _row("convertibles_if_converted", ABSENT_SUPPORTED, "d"),
        _row("contingent_shares", ABSENT_SUPPORTED, "e"),
        _row("other_explicit", ABSENT_SUPPORTED, "f"),
    ]
    inventory = build_ai_dilution_inventory(_base(), rows)
    with pytest.raises(CaseServiceError, match="exact READY path"):
        build_disclosure_limited_dilution_evidence(
            _base(), inventory, _historical(), _components(), as_of="2026-09-14"
        )


def test_validator_independently_recomputes_selected_value() -> None:
    evidence = _evidence()
    tampered = copy.deepcopy(evidence)
    tampered["selection"]["selected_shares"] += 1_000_000
    tampered["evidence_sha256"] = _sha(tampered, "evidence_sha256")
    with pytest.raises(CaseServiceError, match="independent projection"):
        validate_disclosure_limited_dilution_evidence(
            tampered, _base(), _hold_inventory(), _historical(), _components()
        )


def test_approved_r6_finalizes_as_assumption_not_derived_fact() -> None:
    evidence = _evidence()
    adjudication = build_disclosure_limited_dilution_adjudication(
        evidence, adjudicated_at="2026-09-29T12:00:00+09:00"
    )
    assert adjudication["decision"] == APPROVE
    assert adjudication["adjudicator"] == {"type": "AI", "id": ADJUDICATOR_ID}
    assert validate_disclosure_limited_dilution_adjudication(adjudication, evidence)["decision"] == APPROVE
    package = finalize_disclosure_limited_dilution_assumption(evidence, adjudication)
    checked = validate_disclosure_limited_dilution_assumption(package, evidence, adjudication)
    assert checked["eligible_for_assumption_aware_successor"] is True
    assert package["class"] == "ASSUMPTION"
    assert package["value"] == 63_900_000
    assert package["binding_eligibility"]["eligible_for_m22_derived_fact_direct_bind"] is False


def test_cli_builds_real_shaped_evidence_and_delegates_prior_commands(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = {}
    for name, value in {
        "base": _base(),
        "inventory": _hold_inventory(),
        "historical": _historical(),
        "components": _components(),
    }.items():
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        paths[name] = path

    rc = cli_entry_m30r6.main([
        "--json",
        "dilution-assumption-evidence-build",
        str(paths["base"]),
        str(paths["inventory"]),
        str(paths["historical"]),
        str(paths["components"]),
        "--as-of",
        "2026-09-14",
    ])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["selection"]["selected_shares"] == 63_900_000

    seen: list[list[str]] = []
    monkeypatch.setattr(cli_entry_m30r6.prior_cli, "main", lambda argv: seen.append(list(argv)) or 47)
    old = ["market-price-ai-package-validate", "x", "y", "z", "a", "--corroborations", "m"]
    assert cli_entry_m30r6.main(old) == 47
    assert seen == [old]
