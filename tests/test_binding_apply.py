"""M17 human-approved noncanonical Draft binding application tests."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from valuation_hub.binding_apply import build_binding_approval, validate_binding_approval, apply_binding_approval, validate_bound_draft_result
from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_binding import build_binding_proposal

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "draft_equity_fcff.json"


def _hash(value: dict, field: str) -> str:
    payload = copy.deepcopy(value); payload.pop(field, None)
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _cash(value: int = 777) -> dict:
    obs = {
        "schema_version": "financial-observation-v0.1", "status": "FINANCIAL_OBSERVATION_NORMALIZED", "canonical": False,
        "class": "NORMALIZED_FACT", "metric": "cash", "value": value, "unit": "KRW",
        "entity": {"id": "DART_CORP:00126380", "source_system": "TEST", "financial_scope": "CFS"},
        "period": {"kind": "INSTANT", "start": None, "end": "2026-06-30", "duration_days": None, "fiscal_year": 2026, "fiscal_period": "H1", "fiscal_quarter": 2, "report_stage": "H1", "date_precision": "EXACT"},
        "lineage": {"normalization_rule": "TEST", "source_candidate_sha256": "a" * 64}, "observation_sha256": "",
    }
    obs["observation_sha256"] = _hash(obs, "observation_sha256")
    return obs


def _draft() -> dict:
    draft = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    draft["currency"] = "KRW"
    draft["name"] = "M17 Test Company"
    return draft


def _proposal() -> dict:
    return build_binding_proposal([_cash()], as_of="2026-09-11")


def _approval(proposal: dict, draft: dict, fields: list[str] | None = None) -> dict:
    return build_binding_approval(
        proposal, draft,
        reviewer="human-reviewer",
        target_entity_id="DART_CORP:00126380",
        target_financial_scope="CFS",
        approved_fields=["equity.cash"] if fields is None else fields,
        approved_at="2026-09-11T17:50:00+09:00",
    )


def test_approval_locks_proposal_draft_identity_and_direct_fields() -> None:
    proposal, draft = _proposal(), _draft()
    approval = _approval(proposal, draft)
    checked = validate_binding_approval(approval, proposal, draft)
    assert checked["approved_field_count"] == 1
    assert approval["canonical"] is False


def test_apply_changes_only_approved_cash_and_preserves_original() -> None:
    proposal, draft = _proposal(), _draft()
    original = copy.deepcopy(draft)
    result = apply_binding_approval(proposal, draft, _approval(proposal, draft))
    assert draft == original
    assert result["draft_before"] == original
    assert result["draft_after"]["equity"]["cash"] == 777
    assert result["draft_after"]["equity"]["debt"] == original["equity"]["debt"]
    assert result["applied_diffs"] == [{
        "field": "equity.cash", "before": original["equity"]["cash"], "after": 777,
        "source_metric": "cash", "source_observation_sha256": proposal["baseline_context"]["cash"]["observation_sha256"],
    }]
    assert result["canonical"] is False
    assert validate_bound_draft_result(result)["applied_field_count"] == 1


def test_non_direct_field_cannot_be_approved() -> None:
    proposal, draft = _proposal(), _draft()
    with pytest.raises(CaseServiceError, match="DIRECT_BIND"):
        _approval(proposal, draft, ["equity.debt"])


def test_entity_scope_and_currency_mismatch_fail_closed() -> None:
    proposal, draft = _proposal(), _draft()
    with pytest.raises(CaseServiceError, match="entity|식별|범위"):
        build_binding_approval(proposal, draft, reviewer="r", target_entity_id="DART_CORP:99999999", target_financial_scope="CFS", approved_fields=["equity.cash"], approved_at="2026-09-11T17:50:00+09:00")
    bad_currency = _draft(); bad_currency["currency"] = "USD"
    with pytest.raises(CaseServiceError, match="currency|통화"):
        _approval(proposal, bad_currency)


def test_approval_breaks_if_proposal_or_draft_changes() -> None:
    proposal, draft = _proposal(), _draft()
    approval = _approval(proposal, draft)
    changed_draft = copy.deepcopy(draft); changed_draft["market_price"] = 999
    with pytest.raises(CaseServiceError, match="Draft SHA"):
        validate_binding_approval(approval, proposal, changed_draft)
    changed_proposal = copy.deepcopy(proposal); changed_proposal["proposal_sha256"] = "0" * 64
    with pytest.raises(CaseServiceError):
        validate_binding_approval(approval, changed_proposal, draft)


def test_approval_and_result_tampering_detected() -> None:
    proposal, draft = _proposal(), _draft()
    approval = _approval(proposal, draft)
    bad_approval = copy.deepcopy(approval); bad_approval["reviewer"] = "other"
    with pytest.raises(CaseServiceError, match="approval SHA-256|승인 SHA-256"):
        validate_binding_approval(bad_approval, proposal, draft)

    result = apply_binding_approval(proposal, draft, approval)
    result["draft_after"]["equity"]["cash"] += 1
    with pytest.raises(CaseServiceError):
        validate_bound_draft_result(result)


def test_empty_explicit_approval_is_allowed_and_changes_nothing() -> None:
    proposal, draft = _proposal(), _draft()
    approval = _approval(proposal, draft, [])
    result = apply_binding_approval(proposal, draft, approval)
    assert result["draft_after"] == draft
    assert result["applied_diffs"] == []
    assert validate_bound_draft_result(result)["applied_field_count"] == 0
