"""M16 governed normalized-evidence → Draft binding tests / 바인딩 제안 정책 테스트."""

from __future__ import annotations

import copy
import hashlib
import json

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_binding import (
    DIRECT_BIND,
    MISSING_REQUIRED,
    NEEDS_ASSUMPTION,
    NEEDS_DERIVATION,
    REFERENCE_ONLY,
    STALE_BLOCKED,
    build_binding_proposal,
    validate_binding_proposal,
)


def _sha_payload(value: dict, field: str) -> str:
    payload = copy.deepcopy(value)
    payload.pop(field, None)
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _obs(metric: str, value: int, *, klass: str = "NORMALIZED_FACT_CANDIDATE", unit: str = "KRW", entity: str = "DART_CORP:00126380", scope: str = "CFS", kind: str = "INSTANT", end: str | None = "2026-06-30", precision: str = "EXACT") -> dict:
    period = {
        "kind": kind,
        "start": None if kind == "INSTANT" else "2025-07-01",
        "end": end,
        "duration_days": None if kind == "INSTANT" else 365,
        "fiscal_year": 2026,
        "fiscal_period": "H1" if kind == "INSTANT" else "FY",
        "fiscal_quarter": 2 if kind == "INSTANT" else 4,
        "report_stage": "H1" if kind == "INSTANT" else "FY",
        "date_precision": precision,
    }
    result = {
        "schema_version": "financial-observation-v0.1",
        "status": "FINANCIAL_OBSERVATION_NORMALIZED",
        "canonical": False,
        "class": klass,
        "metric": metric,
        "value": value,
        "unit": unit,
        "entity": {"id": entity, "source_system": "TEST", "financial_scope": scope},
        "period": period,
        "lineage": {"normalization_rule": "TEST", "source_candidate_sha256": "a" * 64},
        "observation_sha256": "",
    }
    result["observation_sha256"] = _sha_payload(result, "observation_sha256")
    return result


def _decision(proposal: dict, field: str) -> dict:
    return next(item for item in proposal["draft_input_matrix"] if item["field"] == field)


def test_candidate_cash_is_reference_only_and_never_direct_bind() -> None:
    proposal = build_binding_proposal([_obs("cash", 100)], as_of="2026-09-11")
    assert _decision(proposal, "equity.cash")["state"] == REFERENCE_ONLY
    assert proposal["completeness"]["direct_bind_count"] == 0
    assert proposal["canonical"] is False


def test_reviewed_fresh_instant_cash_is_only_safe_direct_bind_v01() -> None:
    proposal = build_binding_proposal([_obs("cash", 100, klass="NORMALIZED_FACT")], as_of="2026-09-11")
    assert _decision(proposal, "equity.cash")["state"] == DIRECT_BIND
    assert proposal["completeness"]["direct_bind_count"] == 1
    assert validate_binding_proposal(proposal)["direct_bind_count"] == 1


def test_semantic_non_equivalence_is_regression_blocked() -> None:
    observations = [
        _obs("liabilities", 900, klass="NORMALIZED_FACT"),
        _obs("shares_outstanding", 150, klass="NORMALIZED_FACT", unit="shares"),
        _obs("revenue", 1200, klass="NORMALIZED_FACT", kind="DURATION_TTM"),
    ]
    proposal = build_binding_proposal(observations, as_of="2026-09-11")
    assert _decision(proposal, "equity.debt")["state"] == NEEDS_DERIVATION
    assert _decision(proposal, "equity.diluted_shares")["state"] == NEEDS_DERIVATION
    assert _decision(proposal, "scenario.years.revenue")["state"] == NEEDS_ASSUMPTION
    assert _decision(proposal, "market_price")["state"] == MISSING_REQUIRED


def test_stale_or_unknown_date_cash_cannot_direct_bind() -> None:
    stale = build_binding_proposal([_obs("cash", 100, klass="NORMALIZED_FACT", end="2020-12-31")], as_of="2026-09-11", max_age_days=550)
    assert _decision(stale, "equity.cash")["state"] == STALE_BLOCKED

    unknown = build_binding_proposal([_obs("cash", 100, klass="NORMALIZED_FACT", end=None, precision="REPORT_STAGE_ONLY")], as_of="2026-09-11")
    assert _decision(unknown, "equity.cash")["state"] == REFERENCE_ONLY


def test_entity_scope_and_monetary_unit_conflicts_fail_closed() -> None:
    with pytest.raises(CaseServiceError, match="entity|재무범위"):
        build_binding_proposal([_obs("cash", 100), _obs("assets", 200, entity="DART_CORP:99999999")], as_of="2026-09-11")
    with pytest.raises(CaseServiceError, match="unit|통화"):
        build_binding_proposal([_obs("cash", 100), _obs("assets", 200, unit="USD")], as_of="2026-09-11")


def test_unreconciled_duplicate_metric_is_conflict_blocked() -> None:
    left = _obs("cash", 100, klass="NORMALIZED_FACT")
    right = _obs("cash", 101, klass="NORMALIZED_FACT")
    proposal = build_binding_proposal([left, right], as_of="2026-09-11")
    assert _decision(proposal, "equity.cash")["state"] != DIRECT_BIND
    assert proposal["conflicts"]["cash"]["state"] == "CONFLICT_BLOCKED"


def test_proposal_hash_tamper_is_detected_and_matrix_complete() -> None:
    proposal = build_binding_proposal([_obs("cash", 100, klass="NORMALIZED_FACT")], as_of="2026-09-11")
    assert proposal["completeness"]["material_field_count"] == 13
    assert proposal["completeness"]["classified_field_count"] == 13
    proposal["policy"]["max_age_days"] += 1
    with pytest.raises(CaseServiceError, match="SHA-256"):
        validate_binding_proposal(proposal)
