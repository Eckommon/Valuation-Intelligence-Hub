"""M27 market-price binding apply extension / M27 시장가격 바인딩 적용 확장.

Only v0.7 proposals are handled here. Older proposal versions delegate unchanged
to the M26 binding-apply implementation.
"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime
from typing import Any

from valuation_hub import binding_apply as prior_apply
from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_service import validate_draft
from valuation_hub.market_price_draft_binding import SCHEMA_VERSION_V7, validate_binding_proposal_v7

APPROVAL_SCHEMA = prior_apply.APPROVAL_SCHEMA
RESULT_SCHEMA = prior_apply.RESULT_SCHEMA
APPROVAL_STATUS = prior_apply.APPROVAL_STATUS
RESULT_STATUS = prior_apply.RESULT_STATUS


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result.pop(field, None)
    return result


def _parse_timestamp(value: Any) -> str:
    if not isinstance(value, str):
        raise CaseServiceError("approved_at timestamp required / 승인시각 필요")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CaseServiceError("approved_at ISO timestamp invalid / 승인시각 ISO 형식 오류") from exc
    if parsed.tzinfo is None:
        raise CaseServiceError("approved_at timezone required / 승인시각 시간대 필요")
    return parsed.isoformat()


def _is_v7(proposal: Any) -> bool:
    return isinstance(proposal, dict) and proposal.get("schema_version") == SCHEMA_VERSION_V7


def _direct_fields(proposal: dict[str, Any]) -> dict[str, dict[str, Any]]:
    validate_binding_proposal_v7(proposal)
    return {
        item["field"]: item
        for item in proposal["draft_input_matrix"]
        if item.get("state") == "DIRECT_BIND"
    }


def _market_context(proposal: dict[str, Any]) -> dict[str, Any]:
    context = proposal.get("baseline_context", {}).get("market_price_fact")
    if not isinstance(context, dict):
        raise CaseServiceError("market-price binding context missing / 시장가격 바인딩 context 누락")
    return context


def _validate_market_lineage(decision: dict[str, Any], context: dict[str, Any]) -> None:
    if decision.get("source_context_sha256") != context.get("context_sha256"):
        raise CaseServiceError("market-price context hash mismatch / 시장가격 context hash 불일치")
    if decision.get("source_market_price_package_sha256") != context.get("source_market_price_package_sha256"):
        raise CaseServiceError("market-price package hash mismatch / 시장가격 패키지 hash 불일치")
    if decision.get("source_snapshot_sha256") != context.get("source_snapshot_sha256"):
        raise CaseServiceError("market-price source snapshot hash mismatch / 시장가격 source snapshot hash 불일치")
    if decision.get("review_assertion_sha256") != context.get("review_assertion_sha256"):
        raise CaseServiceError("market-price review assertion lineage mismatch / 시장가격 검토승인 lineage 불일치")
    if decision.get("trading_date") != context.get("trading_date"):
        raise CaseServiceError("market-price trading-date lineage mismatch / 시장가격 거래일 lineage 불일치")
    if decision.get("observed_at") != context.get("observed_at"):
        raise CaseServiceError("market-price quote-time lineage mismatch / 시장가격 quote 시각 lineage 불일치")
    if decision.get("venue") != context.get("instrument", {}).get("venue"):
        raise CaseServiceError("market-price venue lineage mismatch / 시장가격 거래소 lineage 불일치")
    if decision.get("quote_type") != context.get("quote_type"):
        raise CaseServiceError("market-price quote-type lineage mismatch / 시장가격 quote 유형 lineage 불일치")
    if decision.get("source_metric") != "market_price_fact" or decision.get("source_class") != "FACT":
        raise CaseServiceError("market-price decision semantics invalid / 시장가격 판정 의미 오류")


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
    if not _is_v7(proposal):
        return prior_apply.build_binding_approval(
            proposal,
            draft,
            reviewer=reviewer,
            target_entity_id=target_entity_id,
            target_financial_scope=target_financial_scope,
            approved_fields=approved_fields,
            approved_at=approved_at,
        )
    validate_binding_proposal_v7(proposal)
    normalized_draft = validate_draft(draft)
    if normalized_draft["model"] != "equity_fcff":
        raise CaseServiceError("M27 requires equity_fcff Draft / M27은 equity_fcff Draft 전용")
    if not isinstance(reviewer, str) or not reviewer.strip() or len(reviewer) > 160:
        raise CaseServiceError("reviewer required / reviewer 필요")
    identity = proposal["identity"]
    if target_entity_id != identity.get("entity_id") or target_financial_scope != identity.get("financial_scope"):
        raise CaseServiceError("target entity/scope mismatch / 대상 entity·재무범위 불일치")
    monetary = identity.get("monetary_unit")
    if monetary and normalized_draft["currency"] != str(monetary).upper():
        raise CaseServiceError("Draft currency does not match binding proposal / Draft 통화와 바인딩 제안 통화 불일치")
    if not isinstance(approved_fields, list) or len(set(approved_fields)) != len(approved_fields):
        raise CaseServiceError("approved_fields must be unique list / approved_fields 고유 배열 필요")
    direct = _direct_fields(proposal)
    unknown = set(approved_fields) - set(direct)
    if unknown:
        raise CaseServiceError(f"only DIRECT_BIND fields may be approved / DIRECT_BIND 필드만 승인 가능: {sorted(unknown)}")
    # Preserve M26 all-six-or-none semantics through the embedded v0.6 proposal.
    prior_apply._validate_forecast_atomicity(approved_fields)
    if "scenario.wacc" in approved_fields:
        prior_apply._validate_wacc_targets(proposal, normalized_draft)
    if "scenario.terminal_growth" in approved_fields:
        prior_apply._validate_terminal_growth_targets(proposal, normalized_draft)
        prior_apply._validate_terminal_growth_wacc_dependency(proposal, normalized_draft, approved_fields)
    if set(approved_fields) & set(prior_apply.FORECAST_FIELDS):
        prior_apply._validate_forecast_targets(proposal, normalized_draft)
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
    if not _is_v7(proposal):
        return prior_apply.validate_binding_approval(approval, proposal, draft)
    validate_binding_proposal_v7(proposal)
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
    prior_apply._validate_forecast_atomicity(fields)
    if "scenario.wacc" in fields:
        prior_apply._validate_wacc_targets(proposal, normalized_draft)
    if "scenario.terminal_growth" in fields:
        prior_apply._validate_terminal_growth_targets(proposal, normalized_draft)
        prior_apply._validate_terminal_growth_wacc_dependency(proposal, normalized_draft, fields)
    if set(fields) & set(prior_apply.FORECAST_FIELDS):
        prior_apply._validate_forecast_targets(proposal, normalized_draft)
    _parse_timestamp(approval.get("approved_at"))
    expected = _sha(_without(approval, "approval_sha256"))
    if approval.get("approval_sha256") != expected:
        raise CaseServiceError("binding approval SHA-256 mismatch / 바인딩 승인 SHA-256 불일치")
    return {
        "status": "PASS_BINDING_APPROVAL_VALIDATION",
        "canonical": False,
        "approval_sha256": expected,
        "approved_field_count": len(fields),
    }


def _get_field(draft: dict[str, Any], field: str, context: dict[str, Any]) -> Any:
    if field == "market_price":
        return draft["market_price"]
    return prior_apply._get_field(draft, field, context)


def _target_value(field: str, context: dict[str, Any]) -> Any:
    if field == "market_price":
        return context.get("value")
    return prior_apply._target_value(field, context)


def _set_field(draft: dict[str, Any], field: str, value: Any, context: dict[str, Any]) -> None:
    if field == "market_price":
        draft["market_price"] = value
        return
    prior_apply._set_field(draft, field, value, context)


def _binding_context(proposal: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    if decision.get("field") == "market_price":
        context = _market_context(proposal)
        _validate_market_lineage(decision, context)
        return context
    # Existing contexts are unchanged inside the embedded v0.6 projection.
    return prior_apply._binding_context(proposal, decision)


def _diff_for(field: str, old: Any, new: Any, decision: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if field != "market_price":
        return prior_apply._diff_for(field, old, new, decision, context)
    return {
        "field": "market_price",
        "before": old,
        "after": new,
        "source_metric": "market_price_fact",
        "source_context_sha256": context["context_sha256"],
        "source_market_price_package_sha256": context["source_market_price_package_sha256"],
        "source_snapshot_sha256": context["source_snapshot_sha256"],
        "review_assertion_sha256": context["review_assertion_sha256"],
        "trading_date": context["trading_date"],
        "observed_at": context["observed_at"],
        "venue": context["instrument"]["venue"],
        "quote_type": context["quote_type"],
    }


def apply_binding_approval(proposal: dict[str, Any], draft: dict[str, Any], approval: dict[str, Any]) -> dict[str, Any]:
    if not _is_v7(proposal):
        return prior_apply.apply_binding_approval(proposal, draft, approval)
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
    proposal = result.get("binding_proposal") if isinstance(result, dict) else None
    if not _is_v7(proposal):
        return prior_apply.validate_bound_draft_result(result)
    if result.get("schema_version") != RESULT_SCHEMA or result.get("status") != RESULT_STATUS or result.get("canonical") is not False:
        raise CaseServiceError("bound Draft result schema/status invalid / 바인딩 Draft 결과 스키마·상태 오류")
    approval = result.get("approval")
    before = result.get("draft_before")
    after = result.get("draft_after")
    if not all(isinstance(item, dict) for item in (proposal, approval, before, after)):
        raise CaseServiceError("bound Draft result payload incomplete / 바인딩 Draft 결과 payload 불완전")
    validate_binding_proposal_v7(proposal)
    validate_binding_approval(approval, proposal, before)
    validate_draft(after)
    if result.get("draft_before_sha256") != _sha(before) or result.get("draft_after_sha256") != _sha(after):
        raise CaseServiceError("bound Draft before/after SHA mismatch / 바인딩 Draft 전후 SHA 불일치")
    direct = _direct_fields(proposal)
    approved = approval["approved_fields"]
    diffs = result.get("applied_diffs")
    if not isinstance(diffs, list) or len(diffs) != len(approved):
        raise CaseServiceError("bound Draft diff count mismatch / 바인딩 Draft diff 개수 불일치")
    diff_fields = [diff.get("field") if isinstance(diff, dict) else None for diff in diffs]
    if len(diff_fields) != len(set(diff_fields)) or set(diff_fields) != set(approved):
        raise CaseServiceError("bound Draft diff fields must exactly match approved fields / 바인딩 Draft diff 필드는 승인필드와 정확히 일치해야 함")
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
