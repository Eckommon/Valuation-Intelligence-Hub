"""R8 governed noncanonical draft application, preserving R6 share ASSUMPTION."""
import copy
from valuation_hub import binding_apply_m28 as m28
from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_service import validate_draft
from valuation_hub.r8_assumption_proposal import SHARE, digest, sha_field, validate_assumption_proposal
from valuation_hub.r8_assumption_approval import validate_assumption_approval

def _project(proposal, draft, approval):
    base = m28.apply_binding_approval(proposal["base_proposal"], draft, approval["base_approval"])
    after = copy.deepcopy(base["draft_after"])
    diffs = copy.deepcopy(base["applied_diffs"])
    if SHARE in approval["approved_fields"]:
        ctx = proposal["baseline_context"]["fully_diluted_shares"]
        diffs.append({"field": SHARE, "before": after["equity"]["diluted_shares"],
                      "after": ctx["value"], "source_class": "ASSUMPTION",
                      "source_route": ctx["route"], "source_metric": "fully_diluted_shares",
                      "source_context_sha256": ctx["source_context_sha256"],
                      "source_r6_package_sha256": ctx["source_r6_package_sha256"],
                      "source_r7x_manifest_sha256": ctx["source_r7x_manifest_sha256"]})
        after["equity"]["diluted_shares"] = ctx["value"]
    validate_draft(after)
    result = {"schema_version": m28.RESULT_SCHEMA, "status": m28.RESULT_STATUS,
              "canonical": False, "binding_proposal": copy.deepcopy(proposal),
              "approval": copy.deepcopy(approval), "draft_before": copy.deepcopy(draft),
              "draft_before_sha256": digest(draft), "applied_diffs": diffs,
              "draft_after": after, "draft_after_sha256": digest(after),
              "unresolved_binding_matrix": [copy.deepcopy(row) for row in proposal["draft_input_matrix"]
                                            if row["field"] not in approval["approved_fields"]],
              "base_bound_result": base, "result_sha256": ""}
    result["result_sha256"] = sha_field(result, "result_sha256")
    return result

def validate_bound_result(result):
    if not isinstance(result, dict):
        raise CaseServiceError("R8 bound result must be object")
    p, a, d = result.get("binding_proposal"), result.get("approval"), result.get("draft_before")
    validate_assumption_proposal(p)
    validate_assumption_approval(a, p, d)
    if result != _project(p, d, a):
        raise CaseServiceError("R8 bound result does not reproduce")
    return {"status": "PASS_R8_BOUND_RESULT", "canonical": False, "result_sha256": result["result_sha256"],
            "applied_field_count": len(a["approved_fields"]), "share_class": "ASSUMPTION"}

def apply_approval(proposal, draft, approval):
    validate_assumption_approval(approval, proposal, draft)
    result = _project(proposal, draft, approval)
    validate_bound_result(result)
    return result
