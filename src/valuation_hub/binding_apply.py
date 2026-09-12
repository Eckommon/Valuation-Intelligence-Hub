"""Human-approved binding application to a noncanonical Draft / 인간승인 비정식 Draft 바인딩 적용.

M17 applies only explicitly approved DIRECT_BIND decisions in memory. M20, M23,
M24, and M25 extend the same approval lock to debt, diluted shares, governed WACC,
and governed terminal growth while preserving older proposal behavior. No path
overwrites a Draft file or creates canonical state.
"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_binding import DIRECT_BIND
from valuation_hub.draft_service import validate_draft
from valuation_hub.terminal_growth_draft_binding import validate_binding_proposal_any

APPROVAL_SCHEMA = "binding-approval-v0.1"
RESULT_SCHEMA = "bound-draft-result-v0.1"
APPROVAL_STATUS = "BINDING_APPROVED"
RESULT_STATUS = "BOUND_DRAFT_RESULT"


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result.pop(field, None)
    return result


def _parse_timestamp(value: str) -> str:
    if not isinstance(value, str):
        raise CaseServiceError("approved_at timestamp required / 승인시각 필요")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CaseServiceError("approved_at ISO timestamp invalid / 승인시각 ISO 형식 오류") from exc
    if parsed.tzinfo is None:
        raise CaseServiceError("approved_at timezone required / 승인시각 시간대 필요")
    return parsed.isoformat()


def _direct_fields(proposal: dict[str, Any]) -> dict[str, dict[str, Any]]:
    validate_binding_proposal_any(proposal)
    return {item["field"]: item for item in proposal["draft_input_matrix"] if item["state"] == DIRECT_BIND}


def _scenario_context(proposal: dict[str, Any], key: str, label: str) -> dict[str, Any]:
    context = proposal.get("baseline_context", {}).get(key)
    if not isinstance(context, dict):
        raise CaseServiceError(f"{label} binding context missing / {label} 바인딩 context 누락")
    return context


def _wacc_context(proposal: dict[str, Any]) -> dict[str, Any]:
    return _scenario_context(proposal, "wacc_assumption", "WACC")


def _terminal_growth_context(proposal: dict[str, Any]) -> dict[str, Any]:
    return _scenario_context(proposal, "terminal_growth_assumption", "terminal growth")


def _scenario_key_map(draft: dict[str, Any]) -> dict[str, str]:
    scenarios = draft.get("equity", {}).get("scenarios")
    if not isinstance(scenarios, dict):
        raise CaseServiceError("Draft scenarios missing / Draft 시나리오 누락")
    result: dict[str, str] = {}
    for raw in scenarios:
        normalized = str(raw).strip().upper()
        if not normalized or normalized in result:
            raise CaseServiceError("Draft scenario names ambiguous / Draft 시나리오 이름 모호")
        result[normalized] = raw
    return result


def _validate_scenario_targets(context: dict[str, Any], normalized_draft: dict[str, Any], label: str) -> None:
    names = context.get("scenario_names")
    if not isinstance(names, list) or not names:
        raise CaseServiceError(f"{label} scenario target set missing / {label} 시나리오 대상집합 누락")
    actual = sorted(normalized_draft["equity"]["scenarios"])
    if sorted(names) != actual:
        raise CaseServiceError(f"{label} scenario target set must exactly match Draft scenarios / {label} 대상 시나리오는 Draft 시나리오와 정확히 일치해야 함")


def _validate_wacc_targets(proposal: dict[str, Any], normalized_draft: dict[str, Any]) -> None:
    _validate_scenario_targets(_wacc_context(proposal), normalized_draft, "WACC")


def _validate_terminal_growth_targets(proposal: dict[str, Any], normalized_draft: dict[str, Any]) -> None:
    _validate_scenario_targets(_terminal_growth_context(proposal), normalized_draft, "terminal growth")


def _validate_terminal_growth_wacc_dependency(
    proposal: dict[str, Any],
    normalized_draft: dict[str, Any],
    approved_fields: list[str],
) -> None:
    terminal_context = _terminal_growth_context(proposal)
    reviewed_wacc = terminal_context.get("reviewed_wacc")
    if isinstance(reviewed_wacc, bool) or not isinstance(reviewed_wacc, (int, float)):
        raise CaseServiceError("terminal-growth reviewed WACC missing / 영구성장률 reviewed WACC 누락")
    if "scenario.wacc" in approved_fields:
        wacc_context = _wacc_context(proposal)
        if abs(float(wacc_context.get("value")) - float(reviewed_wacc)) > 1e-12:
            raise CaseServiceError("terminal-growth and proposal WACC dependency mismatch / 영구성장률과 proposal WACC dependency 불일치")
        return
    keys = _scenario_key_map(normalized_draft)
    names = terminal_context.get("scenario_names", [])
    for name in names:
        current = normalized_draft["equity"]["scenarios"][keys[name]]["wacc"]
        if abs(float(current) - float(reviewed_wacc)) > 1e-12:
            raise CaseServiceError("terminal growth requires reviewed WACC already in Draft or approved together / 영구성장률은 reviewed WACC가 Draft에 이미 적용되었거나 함께 승인되어야 함")


def build_binding_approval(
    proposal: dict[str, Any],
    draft: dict[str, Any],
    *,
    reviewer: str,
    target_entity_id: str,
    target_financial_scope: str,
    approved_fields: list[str],
    approved_at: str,
) -> dict[str, Any]:
    validate_binding_proposal_any(proposal)
    normalized_draft = validate_draft(draft)
    if normalized_draft["model"] != "equity_fcff":
        raise CaseServiceError("M17/M20/M23/M24/M25 requires equity_fcff Draft / M17/M20/M23/M24/M25는 equity_fcff Draft 전용")
    if not isinstance(reviewer, str) or not reviewer.strip() or len(reviewer) > 160:
        raise CaseServiceError("reviewer required / reviewer 필요")
    identity = proposal["identity"]
    if target_entity_id != identity.get("entity_id") or target_financial_scope != identity.get("financial_scope"):
        raise CaseServiceError("target entity/scope mismatch / 대상 entity·재무범위 불일치")
    monetary_unit = identity.get("monetary_unit")
    if monetary_unit and normalized_draft["currency"] != str(monetary_unit).upper():
        raise CaseServiceError("Draft currency does not match binding proposal / Draft 통화와 바인딩 제안 통화 불일치")
    if not isinstance(approved_fields, list) or len(set(approved_fields)) != len(approved_fields):
        raise CaseServiceError("approved_fields must be unique list / approved_fields 고유 배열 필요")
    direct = _direct_fields(proposal)
    unknown = set(approved_fields) - set(direct)
    if unknown:
        raise CaseServiceError(f"only DIRECT_BIND fields may be approved / DIRECT_BIND 필드만 승인 가능: {sorted(unknown)}")
    if "scenario.wacc" in approved_fields:
        _validate_wacc_targets(proposal, normalized_draft)
    if "scenario.terminal_growth" in approved_fields:
        _validate_terminal_growth_targets(proposal, normalized_draft)
        _validate_terminal_growth_wacc_dependency(proposal, normalized_draft, approved_fields)
    timestamp = _parse_timestamp(approved_at)
    approval = {
        "schema_version": APPROVAL_SCHEMA,
        "status": APPROVAL_STATUS,
        "canonical": False,
        "decision": "APPROVE",
        "reviewer": reviewer.strip(),
        "approved_at": timestamp,
        "proposal_sha256": proposal["proposal_sha256"],
        "draft_before_sha256": _sha(draft),
        "target_identity": {"entity_id": target_entity_id, "financial_scope": target_financial_scope},
        "approved_fields": sorted(approved_fields),
        "approval_sha256": "",
    }
    approval["approval_sha256"] = _sha(_without(approval, "approval_sha256"))
    validate_binding_approval(approval, proposal, draft)
    return approval


def validate_binding_approval(approval: dict[str, Any], proposal: dict[str, Any], draft: dict[str, Any]) -> dict[str, Any]:
    validate_binding_proposal_any(proposal)
    normalized_draft = validate_draft(draft)
    if not isinstance(approval, dict) or approval.get("schema_version") != APPROVAL_SCHEMA or approval.get("status") != APPROVAL_STATUS:
        raise CaseServiceError("binding approval schema/status invalid / 바인딩 승인 스키마·상태 오류")
    if approval.get("canonical") is not False or approval.get("decision") != "APPROVE":
        raise CaseServiceError("binding approval authority/decision invalid / 바인딩 승인 권위·결정 오류")
    if approval.get("proposal_sha256") != proposal.get("proposal_sha256"):
        raise CaseServiceError("approval proposal SHA mismatch / 승인 proposal SHA 불일치")
    if approval.get("draft_before_sha256") != _sha(draft):
        raise CaseServiceError("approval Draft SHA mismatch / 승인 Draft SHA 불일치")
    identity = proposal["identity"]
    if approval.get("target_identity") != {"entity_id": identity.get("entity_id"), "financial_scope": identity.get("financial_scope")}:
        raise CaseServiceError("approval target identity mismatch / 승인 대상 식별 불일치")
    direct = set(_direct_fields(proposal))
    fields = approval.get("approved_fields")
    if not isinstance(fields, list) or len(set(fields)) != len(fields) or not set(fields).issubset(direct):
        raise CaseServiceError("approval contains non-DIRECT_BIND field / 승인에 비-DIRECT_BIND 필드 포함")
    if "scenario.wacc" in fields:
        _validate_wacc_targets(proposal, normalized_draft)
    if "scenario.terminal_growth" in fields:
        _validate_terminal_growth_targets(proposal, normalized_draft)
        _validate_terminal_growth_wacc_dependency(proposal, normalized_draft, fields)
    _parse_timestamp(approval.get("approved_at"))
    expected = _sha(_without(approval, "approval_sha256"))
    if approval.get("approval_sha256") != expected:
        raise CaseServiceError("binding approval SHA-256 mismatch / 바인딩 승인 SHA-256 불일치")
    return {"status": "PASS_BINDING_APPROVAL_VALIDATION", "canonical": False, "approval_sha256": expected, "approved_field_count": len(fields)}


def _get_field(draft: dict[str, Any], field: str, context: dict[str, Any] | None = None) -> Any:
    if field == "equity.cash":
        return draft["equity"]["cash"]
    if field == "equity.debt":
        return draft["equity"]["debt"]
    if field == "equity.diluted_shares":
        return draft["equity"]["diluted_shares"]
    if field in {"scenario.wacc", "scenario.terminal_growth"}:
        if not isinstance(context, dict) or not isinstance(context.get("scenario_names"), list):
            raise CaseServiceError("scenario context required for Draft read / Draft 시나리오 읽기에 context 필요")
        keys = _scenario_key_map(draft)
        names = context["scenario_names"]
        if set(names) != set(keys):
            raise CaseServiceError("scenario target set mismatch Draft / 대상 시나리오와 Draft 불일치")
        draft_key = "wacc" if field == "scenario.wacc" else "terminal_growth"
        return {name: draft["equity"]["scenarios"][keys[name]][draft_key] for name in sorted(names)}
    raise CaseServiceError(f"unsupported binding apply field / 미지원 바인딩 적용필드: {field}")


def _target_value(field: str, context: dict[str, Any]) -> Any:
    if field == "scenario.wacc":
        names = context.get("scenario_names")
        if not isinstance(names, list) or not names:
            raise CaseServiceError("WACC target scenarios missing / WACC 대상 시나리오 누락")
        return {name: context.get("value") for name in sorted(names)}
    if field == "scenario.terminal_growth":
        names = context.get("scenario_names")
        values = context.get("value")
        if not isinstance(names, list) or not names or not isinstance(values, dict) or set(values) != set(names):
            raise CaseServiceError("terminal-growth target mapping invalid / 영구성장률 대상 mapping 오류")
        return {name: values[name] for name in sorted(names)}
    return context.get("value")


def _set_field(draft: dict[str, Any], field: str, value: Any, context: dict[str, Any] | None = None) -> None:
    if field == "equity.cash":
        draft["equity"]["cash"] = value
        return
    if field == "equity.debt":
        draft["equity"]["debt"] = value
        return
    if field == "equity.diluted_shares":
        draft["equity"]["diluted_shares"] = value
        return
    if field in {"scenario.wacc", "scenario.terminal_growth"}:
        if not isinstance(context, dict) or not isinstance(value, dict):
            raise CaseServiceError("scenario context/value mapping required / 시나리오 context·값 mapping 필요")
        keys = _scenario_key_map(draft)
        if set(value) != set(keys) or set(context.get("scenario_names", [])) != set(keys):
            raise CaseServiceError("scenario write target set mismatch / 시나리오 쓰기 대상집합 불일치")
        draft_key = "wacc" if field == "scenario.wacc" else "terminal_growth"
        for name, new_value in value.items():
            draft["equity"]["scenarios"][keys[name]][draft_key] = new_value
        return
    raise CaseServiceError(f"unsupported binding apply field / 미지원 바인딩 적용필드: {field}")


def _binding_context(proposal: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    metric = decision.get("source_metric")
    context = proposal.get("baseline_context", {}).get(metric)
    if not isinstance(context, dict):
        raise CaseServiceError("binding source context missing / 바인딩 source context 누락")
    if "source_observation_sha256" in decision:
        if context.get("observation_sha256") != decision.get("source_observation_sha256"):
            raise CaseServiceError("binding source observation hash mismatch / 바인딩 source observation hash 불일치")
    elif "source_context_sha256" in decision:
        if context.get("context_sha256") != decision.get("source_context_sha256"):
            raise CaseServiceError("binding source context hash mismatch / 바인딩 source context hash 불일치")
        if "source_debt_sha256" in decision:
            if context.get("source_debt_sha256") != decision.get("source_debt_sha256"):
                raise CaseServiceError("binding debt context hash mismatch / 바인딩 debt context hash 불일치")
            if context.get("date_resolution", {}).get("date_assertion_sha256") != decision.get("date_assertion_sha256"):
                raise CaseServiceError("binding debt date assertion lineage mismatch / 바인딩 debt 날짜승인 lineage 불일치")
        elif "source_bridge_sha256" in decision:
            if context.get("source_bridge_sha256") != decision.get("source_bridge_sha256"):
                raise CaseServiceError("binding share bridge hash mismatch / 바인딩 share bridge hash 불일치")
            if context.get("base_context_sha256") != decision.get("base_context_sha256"):
                raise CaseServiceError("binding share base context lineage mismatch / 바인딩 share base context lineage 불일치")
            if context.get("coverage_assertion_sha256") != decision.get("coverage_assertion_sha256"):
                raise CaseServiceError("binding share coverage assertion lineage mismatch / 바인딩 share coverage 승인 lineage 불일치")
        elif "source_terminal_growth_package_sha256" in decision:
            if context.get("source_terminal_growth_package_sha256") != decision.get("source_terminal_growth_package_sha256"):
                raise CaseServiceError("binding terminal-growth package hash mismatch / 바인딩 영구성장률 패키지 hash 불일치")
            if context.get("source_wacc_package_sha256") != decision.get("source_wacc_package_sha256"):
                raise CaseServiceError("binding terminal-growth WACC lineage mismatch / 바인딩 영구성장률 WACC lineage 불일치")
            if context.get("review_assertion_sha256") != decision.get("review_assertion_sha256"):
                raise CaseServiceError("binding terminal-growth review lineage mismatch / 바인딩 영구성장률 검토 lineage 불일치")
            if context.get("scenario_names") != decision.get("scenario_names"):
                raise CaseServiceError("binding terminal-growth scenario lineage mismatch / 바인딩 영구성장률 시나리오 lineage 불일치")
        elif "source_package_sha256" in decision:
            if context.get("source_package_sha256") != decision.get("source_package_sha256"):
                raise CaseServiceError("binding WACC package hash mismatch / 바인딩 WACC 패키지 hash 불일치")
            if context.get("review_assertion_sha256") != decision.get("review_assertion_sha256"):
                raise CaseServiceError("binding WACC review assertion lineage mismatch / 바인딩 WACC 검토승인 lineage 불일치")
            if context.get("scenario_names") != decision.get("scenario_names"):
                raise CaseServiceError("binding WACC scenario lineage mismatch / 바인딩 WACC 시나리오 lineage 불일치")
        else:
            raise CaseServiceError("unknown binding context lineage / 알 수 없는 바인딩 context lineage")
    else:
        raise CaseServiceError("binding decision source hash missing / 바인딩 판정 source hash 누락")
    return context


def _diff_for(field: str, old: Any, new: Any, decision: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    diff = {"field": field, "before": old, "after": new, "source_metric": decision.get("source_metric")}
    if "source_observation_sha256" in decision:
        diff["source_observation_sha256"] = context["observation_sha256"]
    elif "source_debt_sha256" in decision:
        diff["source_context_sha256"] = context["context_sha256"]
        diff["source_debt_sha256"] = context["source_debt_sha256"]
        diff["date_assertion_sha256"] = context.get("date_resolution", {}).get("date_assertion_sha256")
    elif "source_bridge_sha256" in decision:
        diff["source_context_sha256"] = context["context_sha256"]
        diff["source_bridge_sha256"] = context["source_bridge_sha256"]
        diff["base_context_sha256"] = context["base_context_sha256"]
        diff["coverage_assertion_sha256"] = context["coverage_assertion_sha256"]
    elif "source_terminal_growth_package_sha256" in decision:
        diff["source_context_sha256"] = context["context_sha256"]
        diff["source_terminal_growth_package_sha256"] = context["source_terminal_growth_package_sha256"]
        diff["source_wacc_package_sha256"] = context["source_wacc_package_sha256"]
        diff["review_assertion_sha256"] = context["review_assertion_sha256"]
        diff["scenario_names"] = copy.deepcopy(context["scenario_names"])
    elif "source_package_sha256" in decision:
        diff["source_context_sha256"] = context["context_sha256"]
        diff["source_package_sha256"] = context["source_package_sha256"]
        diff["review_assertion_sha256"] = context["review_assertion_sha256"]
        diff["scenario_names"] = copy.deepcopy(context["scenario_names"])
    else:
        raise CaseServiceError("binding diff source lineage unknown / 바인딩 diff source lineage 미상")
    return diff


def apply_binding_approval(proposal: dict[str, Any], draft: dict[str, Any], approval: dict[str, Any]) -> dict[str, Any]:
    validate_binding_approval(approval, proposal, draft)
    before = copy.deepcopy(draft)
    after = copy.deepcopy(draft)
    direct = _direct_fields(proposal)
    diffs: list[dict[str, Any]] = []
    for field in approval["approved_fields"]:
        decision = direct[field]
        context = _binding_context(proposal, decision)
        old = _get_field(after, field, context)
        new = _target_value(field, context)
        _set_field(after, field, new, context)
        diffs.append(_diff_for(field, old, new, decision, context))
    validate_draft(after)
    unresolved = [copy.deepcopy(item) for item in proposal["draft_input_matrix"] if item["field"] not in approval["approved_fields"]]
    result = {
        "schema_version": RESULT_SCHEMA,
        "status": RESULT_STATUS,
        "canonical": False,
        "binding_proposal": copy.deepcopy(proposal),
        "approval": copy.deepcopy(approval),
        "draft_before": before,
        "draft_before_sha256": _sha(before),
        "applied_diffs": diffs,
        "draft_after": after,
        "draft_after_sha256": _sha(after),
        "unresolved_binding_matrix": unresolved,
        "warning_en": "Noncanonical Draft result only. Existing evidence governance and human review are still required before promotion.",
        "warning_ko": "비정식 Draft 결과입니다. 승격 전 기존 근거 거버넌스와 인간검토가 계속 필요합니다.",
        "result_sha256": "",
    }
    result["result_sha256"] = _sha(_without(result, "result_sha256"))
    validate_bound_draft_result(result)
    return result


def validate_bound_draft_result(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("schema_version") != RESULT_SCHEMA or result.get("status") != RESULT_STATUS or result.get("canonical") is not False:
        raise CaseServiceError("bound Draft result schema/status invalid / 바인딩 Draft 결과 스키마·상태 오류")
    proposal = result.get("binding_proposal")
    approval = result.get("approval")
    before = result.get("draft_before")
    after = result.get("draft_after")
    if not all(isinstance(item, dict) for item in (proposal, approval, before, after)):
        raise CaseServiceError("bound Draft result payload incomplete / 바인딩 Draft 결과 payload 불완전")
    validate_binding_proposal_any(proposal)
    validate_binding_approval(approval, proposal, before)
    validate_draft(after)
    if result.get("draft_before_sha256") != _sha(before) or result.get("draft_after_sha256") != _sha(after):
        raise CaseServiceError("bound Draft before/after SHA mismatch / 바인딩 Draft 전후 SHA 불일치")
    direct = _direct_fields(proposal)
    approved = approval["approved_fields"]
    diffs = result.get("applied_diffs")
    if not isinstance(diffs, list) or len(diffs) != len(approved):
        raise CaseServiceError("bound Draft diff count mismatch / 바인딩 Draft diff 개수 불일치")
    reconstructed = copy.deepcopy(before)
    for diff in diffs:
        if not isinstance(diff, dict) or diff.get("field") not in approved or diff.get("field") not in direct:
            raise CaseServiceError("bound Draft diff field invalid / 바인딩 Draft diff 필드 오류")
        field = diff["field"]
        decision = direct[field]
        context = _binding_context(proposal, decision)
        current = _get_field(reconstructed, field, context)
        if diff.get("before") != current:
            raise CaseServiceError("bound Draft diff before mismatch / 바인딩 Draft diff 이전값 불일치")
        target = _target_value(field, context)
        if diff.get("after") != target:
            raise CaseServiceError("bound Draft diff source/value mismatch / 바인딩 Draft diff source·값 불일치")
        expected_diff = _diff_for(field, current, target, decision, context)
        if diff != expected_diff:
            raise CaseServiceError("bound Draft diff lineage mismatch / 바인딩 Draft diff lineage 불일치")
        _set_field(reconstructed, field, diff["after"], context)
    if reconstructed != after:
        raise CaseServiceError("bound Draft reconstructed result mismatch / 바인딩 Draft 재구성 결과 불일치")
    expected_unresolved = [item for item in proposal["draft_input_matrix"] if item["field"] not in approved]
    if result.get("unresolved_binding_matrix") != expected_unresolved:
        raise CaseServiceError("unresolved binding matrix mismatch / 미해결 바인딩 matrix 불일치")
    expected = _sha(_without(result, "result_sha256"))
    if result.get("result_sha256") != expected:
        raise CaseServiceError("bound Draft result SHA-256 mismatch / 바인딩 Draft 결과 SHA-256 불일치")
    return {
        "status": "PASS_BOUND_DRAFT_RESULT_VALIDATION",
        "canonical": False,
        "result_sha256": expected,
        "applied_field_count": len(approved),
        "unresolved_count": len(expected_unresolved),
    }
