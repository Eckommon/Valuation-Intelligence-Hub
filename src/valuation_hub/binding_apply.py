"""Human-approved binding application to a noncanonical Draft / 인간승인 비정식 Draft 바인딩 적용.

M17 applies only explicitly approved M16 DIRECT_BIND decisions in memory. It
never overwrites a Draft file and never creates canonical state.
"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_binding import DIRECT_BIND, validate_binding_proposal
from valuation_hub.draft_service import validate_draft

APPROVAL_SCHEMA = "binding-approval-v0.1"
RESULT_SCHEMA = "bound-draft-result-v0.1"
APPROVAL_STATUS = "BINDING_APPROVED"
RESULT_STATUS = "BOUND_DRAFT_RESULT"


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = copy.deepcopy(value); result.pop(field, None); return result


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
    validate_binding_proposal(proposal)
    return {item["field"]: item for item in proposal["draft_input_matrix"] if item["state"] == DIRECT_BIND}


def build_binding_approval(
    proposal: dict[str, Any],
    draft: dict[str, Any],
    *, reviewer: str,
    target_entity_id: str,
    target_financial_scope: str,
    approved_fields: list[str],
    approved_at: str,
) -> dict[str, Any]:
    validate_binding_proposal(proposal)
    normalized_draft = validate_draft(draft)
    if normalized_draft["model"] != "equity_fcff":
        raise CaseServiceError("M17 v0.1 requires equity_fcff Draft / M17 v0.1은 equity_fcff Draft 전용")
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
    validate_binding_proposal(proposal)
    validate_draft(draft)
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
    _parse_timestamp(approval.get("approved_at"))
    expected = _sha(_without(approval, "approval_sha256"))
    if approval.get("approval_sha256") != expected:
        raise CaseServiceError("binding approval SHA-256 mismatch / 바인딩 승인 SHA-256 불일치")
    return {"status": "PASS_BINDING_APPROVAL_VALIDATION", "canonical": False, "approval_sha256": expected, "approved_field_count": len(fields)}


def _get_field(draft: dict[str, Any], field: str) -> Any:
    if field == "equity.cash":
        return draft["equity"]["cash"]
    raise CaseServiceError(f"unsupported M17 apply field / 미지원 M17 적용필드: {field}")


def _set_field(draft: dict[str, Any], field: str, value: Any) -> None:
    if field == "equity.cash":
        draft["equity"]["cash"] = value
        return
    raise CaseServiceError(f"unsupported M17 apply field / 미지원 M17 적용필드: {field}")


def apply_binding_approval(proposal: dict[str, Any], draft: dict[str, Any], approval: dict[str, Any]) -> dict[str, Any]:
    validate_binding_approval(approval, proposal, draft)
    before = copy.deepcopy(draft)
    after = copy.deepcopy(draft)
    direct = _direct_fields(proposal)
    diffs: list[dict[str, Any]] = []
    for field in approval["approved_fields"]:
        decision = direct[field]
        metric = decision.get("source_metric")
        context = proposal.get("baseline_context", {}).get(metric)
        if not isinstance(context, dict) or context.get("observation_sha256") != decision.get("source_observation_sha256"):
            raise CaseServiceError("binding source context/hash mismatch / 바인딩 source context·해시 불일치")
        old = _get_field(after, field)
        new = context.get("value")
        _set_field(after, field, new)
        diffs.append({
            "field": field,
            "before": old,
            "after": new,
            "source_metric": metric,
            "source_observation_sha256": context["observation_sha256"],
        })
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
    proposal = result.get("binding_proposal"); approval = result.get("approval"); before = result.get("draft_before"); after = result.get("draft_after")
    if not all(isinstance(x, dict) for x in (proposal, approval, before, after)):
        raise CaseServiceError("bound Draft result payload incomplete / 바인딩 Draft 결과 payload 불완전")
    validate_binding_proposal(proposal)
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
        if diff.get("before") != _get_field(reconstructed, field):
            raise CaseServiceError("bound Draft diff before mismatch / 바인딩 Draft diff 이전값 불일치")
        decision = direct[field]
        context = proposal["baseline_context"].get(decision.get("source_metric"))
        if not isinstance(context, dict) or diff.get("after") != context.get("value") or diff.get("source_observation_sha256") != context.get("observation_sha256"):
            raise CaseServiceError("bound Draft diff source/value mismatch / 바인딩 Draft diff source·값 불일치")
        _set_field(reconstructed, field, diff["after"])
    if reconstructed != after:
        raise CaseServiceError("bound Draft reconstructed result mismatch / 바인딩 Draft 재구성 결과 불일치")
    expected_unresolved = [item for item in proposal["draft_input_matrix"] if item["field"] not in approved]
    if result.get("unresolved_binding_matrix") != expected_unresolved:
        raise CaseServiceError("unresolved binding matrix mismatch / 미해결 바인딩 matrix 불일치")
    expected = _sha(_without(result, "result_sha256"))
    if result.get("result_sha256") != expected:
        raise CaseServiceError("bound Draft result SHA-256 mismatch / 바인딩 Draft 결과 SHA-256 불일치")
    return {"status": "PASS_BOUND_DRAFT_RESULT_VALIDATION", "canonical": False, "result_sha256": expected, "applied_field_count": len(approved), "unresolved_count": len(expected_unresolved)}
