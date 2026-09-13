"""M28 minority-interest binding apply extension / M28 비지배지분 바인딩 적용 확장."""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime
from typing import Any

from valuation_hub import binding_apply_m27 as prior_apply
from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_service import validate_draft
from valuation_hub.minority_interest_draft_binding import SCHEMA_VERSION_V8, validate_binding_proposal_v8

APPROVAL_SCHEMA = prior_apply.APPROVAL_SCHEMA
RESULT_SCHEMA = prior_apply.RESULT_SCHEMA
APPROVAL_STATUS = prior_apply.APPROVAL_STATUS
RESULT_STATUS = prior_apply.RESULT_STATUS


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = copy.deepcopy(value); result.pop(field, None); return result


def _parse_timestamp(value: Any) -> str:
    if not isinstance(value, str): raise CaseServiceError("approved_at timestamp required / 승인시각 필요")
    try: parsed = datetime.fromisoformat(value)
    except ValueError as exc: raise CaseServiceError("approved_at ISO timestamp invalid / 승인시각 ISO 형식 오류") from exc
    if parsed.tzinfo is None: raise CaseServiceError("approved_at timezone required / 승인시각 시간대 필요")
    return parsed.isoformat()


def _is_v8(proposal: Any) -> bool:
    return isinstance(proposal, dict) and proposal.get("schema_version") == SCHEMA_VERSION_V8


def _direct_fields(proposal: dict[str, Any]) -> dict[str, dict[str, Any]]:
    validate_binding_proposal_v8(proposal)
    return {item["field"]: item for item in proposal["draft_input_matrix"] if item.get("state") == "DIRECT_BIND"}


def _minority_context(proposal: dict[str, Any]) -> dict[str, Any]:
    context = proposal.get("baseline_context", {}).get("minority_interest_fact")
    if not isinstance(context, dict): raise CaseServiceError("minority-interest binding context missing / 비지배지분 바인딩 context 누락")
    return context


def _validate_minority_lineage(decision: dict[str, Any], context: dict[str, Any]) -> None:
    pairs = (
        ("source_context_sha256", "context_sha256"),
        ("source_minority_interest_package_sha256", "source_minority_interest_package_sha256"),
        ("source_observation_sha256", "source_observation_sha256"),
        ("source_snapshot_sha256", "source_snapshot_sha256"),
        ("review_assertion_sha256", "review_assertion_sha256"),
        ("resolved_period_end", "resolved_period_end"),
        ("date_resolution", "date_resolution"),
    )
    for decision_key, context_key in pairs:
        if decision.get(decision_key) != context.get(context_key): raise CaseServiceError("minority-interest lineage mismatch / 비지배지분 lineage 불일치")
    if decision.get("source_metric") != "minority_interest_fact" or decision.get("source_class") != "NORMALIZED_FACT":
        raise CaseServiceError("minority-interest decision semantics invalid / 비지배지분 판정 의미 오류")


def _validate_inherited_targets(proposal: dict[str, Any], draft: dict[str, Any], fields: list[str]) -> None:
    # Preserve the M24-M26 target and atomicity contracts through the embedded v0.7/v0.6 chain.
    helpers = prior_apply.prior_apply
    helpers._validate_forecast_atomicity(fields)
    if "scenario.wacc" in fields: helpers._validate_wacc_targets(proposal, draft)
    if "scenario.terminal_growth" in fields:
        helpers._validate_terminal_growth_targets(proposal, draft)
        helpers._validate_terminal_growth_wacc_dependency(proposal, draft, fields)
    if set(fields) & set(helpers.FORECAST_FIELDS): helpers._validate_forecast_targets(proposal, draft)


def build_binding_approval(proposal: dict[str, Any], draft: dict[str, Any], *, reviewer: str, target_entity_id: str, target_financial_scope: str, approved_fields: list[str], approved_at: str) -> dict[str, Any]:
    if not _is_v8(proposal):
        return prior_apply.build_binding_approval(proposal, draft, reviewer=reviewer, target_entity_id=target_entity_id, target_financial_scope=target_financial_scope, approved_fields=approved_fields, approved_at=approved_at)
    validate_binding_proposal_v8(proposal); normalized = validate_draft(draft)
    if normalized["model"] != "equity_fcff": raise CaseServiceError("M28 requires equity_fcff Draft / M28은 equity_fcff Draft 전용")
    if not isinstance(reviewer, str) or not reviewer.strip() or len(reviewer) > 160: raise CaseServiceError("reviewer required / reviewer 필요")
    identity = proposal["identity"]
    if target_entity_id != identity.get("entity_id") or target_financial_scope != identity.get("financial_scope"): raise CaseServiceError("target entity/scope mismatch / 대상 entity·재무범위 불일치")
    monetary = identity.get("monetary_unit")
    if monetary and normalized["currency"] != str(monetary).upper(): raise CaseServiceError("Draft currency does not match proposal / Draft 통화와 제안 통화 불일치")
    if not isinstance(approved_fields, list) or len(set(approved_fields)) != len(approved_fields): raise CaseServiceError("approved_fields must be unique / approved_fields 고유 배열 필요")
    direct = _direct_fields(proposal); unknown = set(approved_fields) - set(direct)
    if unknown: raise CaseServiceError(f"only DIRECT_BIND fields may be approved / DIRECT_BIND 필드만 승인 가능: {sorted(unknown)}")
    _validate_inherited_targets(proposal, normalized, approved_fields)
    timestamp = _parse_timestamp(approved_at)
    approval = {
        "schema_version": APPROVAL_SCHEMA, "status": APPROVAL_STATUS, "canonical": False, "decision": "APPROVE", "reviewer": reviewer.strip(),
        "approved_at": timestamp, "proposal_sha256": proposal["proposal_sha256"], "draft_before_sha256": _sha(draft),
        "target_identity": {"entity_id": target_entity_id, "financial_scope": target_financial_scope}, "approved_fields": sorted(approved_fields), "approval_sha256": "",
    }
    approval["approval_sha256"] = _sha(_without(approval, "approval_sha256")); validate_binding_approval(approval, proposal, draft); return approval


def validate_binding_approval(approval: dict[str, Any], proposal: dict[str, Any], draft: dict[str, Any]) -> dict[str, Any]:
    if not _is_v8(proposal): return prior_apply.validate_binding_approval(approval, proposal, draft)
    validate_binding_proposal_v8(proposal); normalized = validate_draft(draft)
    if not isinstance(approval, dict) or approval.get("schema_version") != APPROVAL_SCHEMA or approval.get("status") != APPROVAL_STATUS or approval.get("canonical") is not False or approval.get("decision") != "APPROVE": raise CaseServiceError("binding approval schema/status invalid / 바인딩 승인 스키마·상태 오류")
    if approval.get("proposal_sha256") != proposal.get("proposal_sha256") or approval.get("draft_before_sha256") != _sha(draft): raise CaseServiceError("binding approval proposal/Draft SHA mismatch / 바인딩 승인 proposal·Draft SHA 불일치")
    identity = proposal["identity"]
    if approval.get("target_identity") != {"entity_id": identity.get("entity_id"), "financial_scope": identity.get("financial_scope")}: raise CaseServiceError("approval target identity mismatch / 승인 대상 식별 불일치")
    fields = approval.get("approved_fields"); direct = set(_direct_fields(proposal))
    if not isinstance(fields, list) or len(set(fields)) != len(fields) or not set(fields).issubset(direct): raise CaseServiceError("approval contains non-DIRECT_BIND field / 승인에 비-DIRECT_BIND 필드 포함")
    _validate_inherited_targets(proposal, normalized, fields); _parse_timestamp(approval.get("approved_at"))
    expected = _sha(_without(approval, "approval_sha256"))
    if approval.get("approval_sha256") != expected: raise CaseServiceError("binding approval SHA mismatch / 바인딩 승인 SHA 불일치")
    return {"status": "PASS_BINDING_APPROVAL_VALIDATION", "canonical": False, "approval_sha256": expected, "approved_field_count": len(fields)}


def _get_field(draft: dict[str, Any], field: str, context: dict[str, Any]) -> Any:
    if field == "equity.minority_interest": return draft["equity"]["minority_interest"]
    return prior_apply._get_field(draft, field, context)


def _target_value(field: str, context: dict[str, Any]) -> Any:
    if field == "equity.minority_interest": return context.get("value")
    return prior_apply._target_value(field, context)


def _set_field(draft: dict[str, Any], field: str, value: Any, context: dict[str, Any]) -> None:
    if field == "equity.minority_interest": draft["equity"]["minority_interest"] = value; return
    prior_apply._set_field(draft, field, value, context)


def _binding_context(proposal: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    if decision.get("field") == "equity.minority_interest":
        context = _minority_context(proposal); _validate_minority_lineage(decision, context); return context
    return prior_apply._binding_context(proposal, decision)


def _diff_for(field: str, old: Any, new: Any, decision: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if field != "equity.minority_interest": return prior_apply._diff_for(field, old, new, decision, context)
    return {
        "field": field, "before": old, "after": new, "source_metric": "minority_interest_fact", "source_context_sha256": context["context_sha256"],
        "source_minority_interest_package_sha256": context["source_minority_interest_package_sha256"], "source_observation_sha256": context["source_observation_sha256"],
        "source_snapshot_sha256": context["source_snapshot_sha256"], "review_assertion_sha256": context["review_assertion_sha256"],
        "resolved_period_end": context["resolved_period_end"], "date_resolution": context["date_resolution"],
    }


def apply_binding_approval(proposal: dict[str, Any], draft: dict[str, Any], approval: dict[str, Any]) -> dict[str, Any]:
    if not _is_v8(proposal): return prior_apply.apply_binding_approval(proposal, draft, approval)
    validate_binding_approval(approval, proposal, draft)
    before = copy.deepcopy(draft); after = copy.deepcopy(draft); direct = _direct_fields(proposal); diffs: list[dict[str, Any]] = []
    for field in approval["approved_fields"]:
        decision = direct[field]; context = _binding_context(proposal, decision); old = _get_field(after, field, context); new = _target_value(field, context)
        _set_field(after, field, new, context); diffs.append(_diff_for(field, old, new, decision, context))
    validate_draft(after)
    unresolved = [copy.deepcopy(item) for item in proposal["draft_input_matrix"] if item["field"] not in approval["approved_fields"]]
    result = {
        "schema_version": RESULT_SCHEMA, "status": RESULT_STATUS, "canonical": False, "binding_proposal": copy.deepcopy(proposal), "approval": copy.deepcopy(approval),
        "draft_before": before, "draft_before_sha256": _sha(before), "applied_diffs": diffs, "draft_after": after, "draft_after_sha256": _sha(after),
        "unresolved_binding_matrix": unresolved, "warning_en": "Noncanonical Draft result only.", "warning_ko": "비정식 Draft 결과입니다.", "result_sha256": "",
    }
    result["result_sha256"] = _sha(_without(result, "result_sha256")); validate_bound_draft_result(result); return result


def validate_bound_draft_result(result: dict[str, Any]) -> dict[str, Any]:
    proposal = result.get("binding_proposal") if isinstance(result, dict) else None
    if not _is_v8(proposal): return prior_apply.validate_bound_draft_result(result)
    if result.get("schema_version") != RESULT_SCHEMA or result.get("status") != RESULT_STATUS or result.get("canonical") is not False: raise CaseServiceError("bound Draft result schema/status invalid / 바인딩 Draft 결과 스키마·상태 오류")
    approval, before, after = result.get("approval"), result.get("draft_before"), result.get("draft_after")
    if not all(isinstance(x, dict) for x in (proposal, approval, before, after)): raise CaseServiceError("bound Draft result payload incomplete / 바인딩 Draft 결과 payload 불완전")
    validate_binding_proposal_v8(proposal); validate_binding_approval(approval, proposal, before); validate_draft(after)
    if result.get("draft_before_sha256") != _sha(before) or result.get("draft_after_sha256") != _sha(after): raise CaseServiceError("bound Draft before/after SHA mismatch / 바인딩 Draft 전후 SHA 불일치")
    direct = _direct_fields(proposal); approved = approval["approved_fields"]; diffs = result.get("applied_diffs")
    if not isinstance(diffs, list) or len(diffs) != len(approved): raise CaseServiceError("bound Draft diff count mismatch / 바인딩 Draft diff 개수 불일치")
    diff_fields = [d.get("field") for d in diffs if isinstance(d, dict)]
    if len(diff_fields) != len(set(diff_fields)) or set(diff_fields) != set(approved): raise CaseServiceError("bound Draft diff fields must uniquely equal approved fields / 바인딩 Draft diff 필드는 승인필드와 고유·정확 일치해야 함")
    reconstructed = copy.deepcopy(before)
    for diff in diffs:
        field = diff.get("field")
        if field not in direct or field not in approved: raise CaseServiceError("bound Draft diff field invalid / 바인딩 Draft diff 필드 오류")
        decision = direct[field]; context = _binding_context(proposal, decision); old = _get_field(reconstructed, field, context); new = _target_value(field, context)
        expected_diff = _diff_for(field, old, new, decision, context)
        if diff != expected_diff: raise CaseServiceError("bound Draft diff lineage/value mismatch / 바인딩 Draft diff lineage·값 불일치")
        _set_field(reconstructed, field, new, context)
    if reconstructed != after: raise CaseServiceError("bound Draft reconstructed result mismatch / 바인딩 Draft 재구성 결과 불일치")
    expected_unresolved = [item for item in proposal["draft_input_matrix"] if item["field"] not in approved]
    if result.get("unresolved_binding_matrix") != expected_unresolved: raise CaseServiceError("unresolved binding matrix mismatch / 미해결 바인딩 matrix 불일치")
    expected = _sha(_without(result, "result_sha256"))
    if result.get("result_sha256") != expected: raise CaseServiceError("bound Draft result SHA mismatch / 바인딩 Draft 결과 SHA 불일치")
    return {"status": "PASS_BOUND_DRAFT_RESULT_VALIDATION", "canonical": False, "result_sha256": expected, "applied_field_count": len(approved)}
