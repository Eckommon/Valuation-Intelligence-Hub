from __future__ import annotations

import copy
import hashlib
import json

import pytest

from valuation_hub.ai_dilution_authority import (
    ABSENT_SUPPORTED,
    BLOCKED_DEPENDENCY,
    EXPLICIT_COUNT_METHOD,
    PRESENT,
    UNKNOWN_CONFLICT,
    build_ai_dilution_inventory,
)
from valuation_hub.bounded_dilution import (
    ASSUMPTION_CONDITIONAL,
    BOUNDED,
    EVIDENCE_IMPLIED,
    EXACT,
    EXACT_REPRODUCED,
    HOLD_MATERIAL,
    HOLD_UNBOUNDED,
    RANGE_READY,
    UNBOUNDED_DEPENDENCY,
    UNBOUNDED_DISCLOSURE,
    build_bounded_dilution_envelope,
    validate_bounded_dilution_envelope,
)
from valuation_hub.case_service import CaseServiceError


def _hash(value: dict, field: str) -> str:
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


def _source(seed: str) -> list[dict]:
    return [
        {
            "locator": f"repo://issuer/{seed}",
            "snapshot_sha256": seed * 64,
            "source_type": "issuer_filing_snapshot",
        }
    ]


def _base() -> dict:
    result = {
        "schema_version": "valuation-share-base-context-v0.1",
        "status": "VALUATION_SHARE_BASE_CONTEXT_EVALUATED",
        "canonical": False,
        "class": "NORMALIZED_FACT",
        "metric": "current_common_shares",
        "value": 63_063_979,
        "unit": "shares",
        "entity": {
            "id": "SEC_CIK:0001046257",
            "source_system": "SEC",
            "financial_scope": "AS_REPORTED",
        },
        "source_period": {
            "kind": "INSTANT",
            "start": None,
            "end": "2026-08-05",
            "date_precision": "EXACT",
        },
        "policy": {
            "version": "VALUATION_SHARE_BASE_V01",
            "as_of": "2026-09-14",
            "max_age_days": 180,
        },
        "freshness": {"status": "FRESH", "age_days": 40, "max_age_days": 180},
        "semantic_boundary": {
            "current_common_shares_base": True,
            "fully_diluted_shares": False,
            "direct_bind_to_diluted_shares": False,
        },
        "source_observation_sha256": "9" * 64,
        "context_sha256": "",
    }
    result["context_sha256"] = _hash(result, "context_sha256")
    return result


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
    ]
    return build_ai_dilution_inventory(_base(), rows)


def _range(
    category: str,
    state: str,
    kind: str,
    lower: float,
    upper: float | None,
    seed: str,
    *,
    assumptions: list[str] | None = None,
) -> dict:
    return {
        "category": category,
        "state": state,
        "bound_kind": kind,
        "lower_shares": lower,
        "upper_shares": upper,
        "sources": _source(seed),
        "evidence_basis": f"Source-bound range basis for {category}.",
        "assumptions": assumptions or [],
    }


def _ranges(*, director_upper: float = 387_901, director_unbounded: bool = False) -> list[dict]:
    director = (
        _range(
            "other_explicit",
            UNBOUNDED_DEPENDENCY,
            UNBOUNDED_DISCLOSURE,
            0,
            None,
            "6",
        )
        if director_unbounded
        else _range(
            "other_explicit",
            BOUNDED,
            ASSUMPTION_CONDITIONAL,
            0,
            director_upper,
            "6",
            assumptions=[
                "Post-March deferred-plan additions through the valuation date do not exceed the explicit research buffer."
            ],
        )
    )
    return [
        _range(
            "options_treasury_stock_method",
            BOUNDED,
            ASSUMPTION_CONDITIONAL,
            0,
            84_850,
            "1",
            assumptions=["No option grants after 2026-06-30 through the valuation date."],
        ),
        _range(
            "rsu_restricted_stock",
            EXACT,
            EXACT_REPRODUCED,
            534_000,
            534_000,
            "2",
        ),
        _range("warrants", EXACT, EXACT_REPRODUCED, 0, 0, "3"),
        _range("convertibles_if_converted", EXACT, EXACT_REPRODUCED, 0, 0, "4"),
        _range(
            "contingent_shares",
            BOUNDED,
            ASSUMPTION_CONDITIONAL,
            0,
            505_140,
            "5",
            assumptions=["No off-cycle performance-share grants after 2026-06-30 through the valuation date."],
        ),
        director,
    ]


def test_real_shaped_category_envelope_is_narrow_and_nonbinding() -> None:
    base = _base()
    inventory = _hold_inventory()
    ranges = _ranges()
    result = build_bounded_dilution_envelope(base, inventory, ranges)

    assert result["decision"] == RANGE_READY
    assert result["envelope"]["lower_fully_diluted_shares"] == 63_597_979
    assert result["envelope"]["upper_fully_diluted_shares"] == 64_575_870
    assert result["envelope"]["range_width_shares"] == 977_891
    assert result["envelope"]["relative_share_uncertainty"] == pytest.approx(0.015376133257316349)
    assert result["envelope"]["max_per_share_value_reduction"] == pytest.approx(0.015143288042422043)
    assert result["semantic_boundary"]["direct_bind_as_equity_diluted_shares"] is False
    assert result["class"] == "ANALYTICAL_RANGE"

    checked = validate_bounded_dilution_envelope(result, base, inventory, ranges)
    assert checked["decision"] == RANGE_READY


def test_r4_exact_categories_must_reproduce_without_assumptions() -> None:
    ranges = _ranges()
    ranges[1]["upper_shares"] = 534_001
    with pytest.raises(CaseServiceError, match="reproduce"):
        build_bounded_dilution_envelope(_base(), _hold_inventory(), ranges)

    ranges = _ranges()
    ranges[2]["assumptions"] = ["should not exist"]
    with pytest.raises(CaseServiceError, match="cannot add assumptions"):
        build_bounded_dilution_envelope(_base(), _hold_inventory(), ranges)


def test_blocked_category_cannot_be_promoted_to_exact_inside_r6() -> None:
    ranges = _ranges()
    ranges[0].update(
        {
            "state": EXACT,
            "bound_kind": EXACT_REPRODUCED,
            "lower_shares": 10,
            "upper_shares": 10,
            "assumptions": [],
        }
    )
    with pytest.raises(CaseServiceError, match="rebuild R4"):
        build_bounded_dilution_envelope(_base(), _hold_inventory(), ranges)


def test_unbounded_category_holds_without_fabricating_upper() -> None:
    result = build_bounded_dilution_envelope(
        _base(),
        _hold_inventory(),
        _ranges(director_unbounded=True),
    )
    assert result["decision"] == HOLD_UNBOUNDED
    assert result["envelope"]["upper_fully_diluted_shares"] is None
    assert result["envelope"]["relative_share_uncertainty"] is None
    assert result["envelope"]["unbounded_categories"] == ["other_explicit"]


def test_materiality_gate_holds_when_interval_is_too_wide() -> None:
    result = build_bounded_dilution_envelope(
        _base(),
        _hold_inventory(),
        _ranges(director_upper=5_000_000),
        materiality_threshold=0.05,
    )
    assert result["decision"] == HOLD_MATERIAL
    assert result["envelope"]["relative_share_uncertainty"] > 0.05


def test_evidence_implied_bound_cannot_smuggle_assumptions() -> None:
    ranges = _ranges()
    ranges[0]["bound_kind"] = EVIDENCE_IMPLIED
    with pytest.raises(CaseServiceError, match="cannot carry assumptions"):
        build_bounded_dilution_envelope(_base(), _hold_inventory(), ranges)


def test_unknown_conflict_never_uses_bounded_fallback() -> None:
    rows = [
        _row(
            "options_treasury_stock_method",
            UNKNOWN_CONFLICT,
            "a",
            contradictions=["Material option evidence conflict."],
        ),
        _row("rsu_restricted_stock", ABSENT_SUPPORTED, "b"),
        _row("warrants", ABSENT_SUPPORTED, "c"),
        _row("convertibles_if_converted", ABSENT_SUPPORTED, "d"),
        _row("contingent_shares", ABSENT_SUPPORTED, "e"),
        _row("other_explicit", ABSENT_SUPPORTED, "f"),
    ]
    inventory = build_ai_dilution_inventory(_base(), rows)
    with pytest.raises(CaseServiceError, match="UNKNOWN_CONFLICT"):
        build_bounded_dilution_envelope(_base(), inventory, _ranges())


def test_validator_recomputes_projection_and_sha() -> None:
    base = _base()
    inventory = _hold_inventory()
    ranges = _ranges()
    envelope = build_bounded_dilution_envelope(base, inventory, ranges)

    tampered = copy.deepcopy(envelope)
    tampered["envelope"]["upper_fully_diluted_shares"] += 1_000
    tampered["envelope_sha256"] = _hash(tampered, "envelope_sha256")
    with pytest.raises(CaseServiceError, match="independent projection"):
        validate_bounded_dilution_envelope(tampered, base, inventory, ranges)
