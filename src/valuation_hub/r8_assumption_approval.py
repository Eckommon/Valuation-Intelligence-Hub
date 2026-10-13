"""R8 human-governed approval: preserve M28 approval for all non-share fields."""
from __future__ import annotations
import copy
from datetime import datetime
from valuation_hub import binding_apply_m28 as m28
from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_service import validate_draft
from valuation_hub.draft_binding import DIRECT_BIND
from valuation_hub.r8_assumption_proposal import SHARE, digest, sha_field, validate_assumption_proposal


def _date(value):
    if not isinstance(value, str):
        raise CaseServiceError("approved_at required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CaseServiceError("invalid approved_at") from exc
    if parsed.tzinfo is None:
        raise CaseServiceError("approved_at must have timezone")
    return parsed.isoformat()


def _fields(proposal, fields):
    if not isinstance(fields, list) or len(set(fields)) != len(fields):
        raise CaseServiceError("R8 approved_fields must be unique")
    direct = {r["field"] for r in proposal["draft_input_matrix"] if r["state"] == DIRECT_BIND}
    if not set(fields).issubset(direct):
        raise CaseServiceError("R8 cannot approve unresolved material fields")


def _approval(proposal, draft, reviewer, entity, scope, fields, time):
    prior = m28.build_binding_approval(
        proposal["base_proposal"], draft, reviewer=reviewer,
        target_entity_id=entity, target_financial_scope=scope,
        approved_fields=[f for f in fields if f != SHARE], approved_at=time,
    )
    result = dict(
        schema_version=m28.APPROVAL_SCHEMA, status=m28.APPROVAL_STATUS, canonical=False,
        decision="APPROVE", reviewer=reviewer, approved_at=time,
        proposal_sha256=proposal["proposal_sha256"], draft_before_sha256=digest(draft),
        target_identity={"entity_id":entity,"financial_scope":scope},
        approved_fields=sorted(fields), base_approval=copy.deepcopy(prior),
        approval_sha256="")
    result["approval_sha256"] = sha_field(result, "approval_sha256")
    return result


def build_assumption_approval(proposal, draft, *, reviewer, target_entity_id,
                              target_financial_scope, approved_fields, approved_at):
    validate_assumption_proposal(proposal)
    validate_draft(draft)
    _fields(proposal, approved_fields)
    if not isinstance(reviewer, str) or not reviewer.strip() or len(reviewer) > 160:
        raise CaseServiceError("R8 human approval requires explicit reviewer")
    result = _approval(proposal, draft, reviewer.strip(), target_entity_id,
                       target_financial_scope, approved_fields, _date(approved_at))
    validate_assumption_approval(result, proposal, draft)
    return result


def validate_assumption_approval(approval, proposal, draft):
    validate_assumption_proposal(proposal)
    validate_draft(draft)
    if not isinstance(approval, dict) or approval.get("canonical") is not False:
        raise CaseServiceError("R8 approval invalid")
    fields = approval.get("approved_fields")
    _fields(proposal, fields)
    if fields != sorted(fields):
        raise CaseServiceError("R8 approved fields must be sorted")
    identity = proposal["identity"]
    reviewer = approval.get("reviewer")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise CaseServiceError("R8 missing explicit reviewer")
    expected = _approval(proposal, draft, reviewer, identity["entity_id"],
                         identity["financial_scope"], fields, _date(approval.get("approved_at")))
    if approval != expected:
        raise CaseServiceError("R8 approval identity/source/fields/SHA mismatch")
    return {"status":"PASS_R8_APPROVAL", "approval_sha256":approval["approval_sha256"]}
