"""M30-R8 v0.9: R6 diluted shares inherit ASSUMPTION authority."""
import copy
import hashlib
import json
from math import isfinite
from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_binding import DIRECT_BIND, MATERIAL_FIELDS, STATUS
from valuation_hub.minority_interest_draft_binding import validate_binding_proposal_v8
from valuation_hub.debt_draft_binding import validate_binding_proposal_any as validate_v2
from valuation_hub.share_draft_binding import SCHEMA_VERSION_V3
from valuation_hub.r8_assumption_proof import ROUTE, validate_r6_binding_proof

SCHEMA = "draft-binding-proposal-v0.9"
R6_V3_POLICY = "evidence-draft-binding-v0.3-r6-assumption"
SHARE = "equity.diluted_shares"


def digest(x):
    return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def sha_field(x, key):
    y = copy.deepcopy(x)
    y.pop(key, None)
    return digest(y)


def counts(rows):
    cs = {}
    for row in rows:
        cs[row["state"]] = cs.get(row["state"], 0) + 1
    return dict(material_field_count=len(MATERIAL_FIELDS), classified_field_count=len(rows),
                state_counts=cs, direct_bind_count=cs.get(DIRECT_BIND, 0),
                unresolved_count=sum(v for k, v in cs.items() if k != DIRECT_BIND))


def make_r6_v3(base, proof):
    """Canonical M23-compatible share route produced from v0.2 debt proposal."""
    validate_v2(base)
    validate_r6_binding_proof(proof)
    p = proof["package"]
    ident = base["identity"]
    if (p["entity"] != {"id": ident.get("entity_id"), "financial_scope": ident.get("financial_scope")}
        or p["as_of"] != base["policy"]["as_of"] or p["unit"] != "shares"
        or p["metric"] != "fully_diluted_shares"):
        raise CaseServiceError("M23 R6 assumption identity/period/unit mismatch")
    matrix = [decision(proof) if row["field"] == SHARE else copy.deepcopy(row) for row in base["draft_input_matrix"]]
    baseline = copy.deepcopy(base["baseline_context"])
    baseline["fully_diluted_shares"] = projection(proof)
    out = dict(schema_version=SCHEMA_VERSION_V3, status=STATUS, canonical=False,
               target=copy.deepcopy(base["target"]),
               policy=dict(version=R6_V3_POLICY, as_of=base["policy"]["as_of"],
                           base_policy_version=base["policy"]["version"],
                           direct_bind_requires=["R6_SOURCE_BOUND_PROOF", "ASSUMPTION_NOT_DERIVED", "MATERIALITY_PASS"]),
               identity=copy.deepcopy(base["identity"]), baseline_context=baseline,
               conflicts=copy.deepcopy(base["conflicts"]), draft_input_matrix=matrix,
               completeness=counts(matrix),
               source_observation_sha256=copy.deepcopy(base["source_observation_sha256"]),
               share_route=ROUTE, r6_binding_proof=copy.deepcopy(proof),
               source_r6_package_sha256=proof["package_sha256"],
               source_r6_proof_sha256=proof["proof_sha256"],
               base_proposal=copy.deepcopy(base), base_proposal_sha256=base["proposal_sha256"],
               warning_en="R6 diluted-share ASSUMPTION. Not an exact M22 DERIVED bridge.",
               warning_ko="R6 희석주식수 가정이며 정확한 M22 DERIVED bridge가 아닙니다.",
               proposal_sha256="")
    out["proposal_sha256"] = sha_field(out, "proposal_sha256")
    return out


def build_r6_v3_proposal(base, proof):
    out = make_r6_v3(base, proof)
    validate_r6_v3_proposal(out)
    return out


def validate_r6_v3_proposal(value):
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION_V3 or value.get("share_route") != ROUTE:
        raise CaseServiceError("M23 R6 share route schema invalid")
    if not isinstance(value.get("base_proposal"), dict) or not isinstance(value.get("r6_binding_proof"), dict):
        raise CaseServiceError("M23 R6 source proof/base missing")
    if value != make_r6_v3(value["base_proposal"], value["r6_binding_proof"]):
        raise CaseServiceError("M23 R6 share route lineage or SHA mismatch")
    return {"status":"PASS_R6_M23_ASSUMPTION_PROPOSAL", "proposal_sha256":value["proposal_sha256"],
            "source_class":"ASSUMPTION"}


def _ancestor_v3(proposal):
    current = proposal
    for _ in range(7):
        if not isinstance(current, dict):
            raise CaseServiceError("M28 R6 ancestor chain malformed")
        if current.get("schema_version") == SCHEMA_VERSION_V3:
            return current
        current = current.get("base_proposal")
    raise CaseServiceError("M28 R6 ancestor not found")


def eligibility(base, proof):
    validate_binding_proposal_v8(base)
    validate_r6_binding_proof(proof)
    current_share = next(x for x in base["draft_input_matrix"] if x["field"] == SHARE)
    ancestor = _ancestor_v3(base)
    if ancestor.get("share_route") != ROUTE:
        raise CaseServiceError("M22 exact DERIVED route outranks R6 fallback")
    validate_r6_v3_proposal(ancestor)
    if (current_share != decision(proof)
        or ancestor["r6_binding_proof"] != proof
        or ancestor["source_r6_package_sha256"] != proof["package_sha256"]):
        raise CaseServiceError("M28 and M23 R6 assumption proof lineage mismatch")
    p, identity = proof["package"], base["identity"]
    if (p.get("entity") != {"id": identity.get("entity_id"), "financial_scope": identity.get("financial_scope")}
        or p.get("as_of") != base["policy"]["as_of"] or p.get("metric") != "fully_diluted_shares"
        or p.get("unit") != "shares"):
        raise CaseServiceError("R6 identity/period/metric mismatch")
    n = p.get("value")
    if isinstance(n, bool) or not isinstance(n, (int, float)) or not isfinite(n) or n <= 0:
        raise CaseServiceError("invalid R6 assumption value")
    return p


def projection(proof):
    p = proof["package"]
    return dict(metric="fully_diluted_shares", value=p["value"], unit="shares",
                **{"class":"ASSUMPTION"}, route=ROUTE, entity=copy.deepcopy(p["entity"]),
                as_of=p["as_of"], range=copy.deepcopy(p["range"]),
                materiality_threshold=p["evidence"]["upper_envelope"]["materiality_threshold"],
                source_context_sha256=proof["proof_sha256"],
                source_r6_package_sha256=p["package_sha256"],
                source_r7x_manifest_sha256=proof["envelope_manifest_sha256"])


def decision(proof):
    return dict(field=SHARE, state=DIRECT_BIND,
                rationale="R6 bounded disclosure-limited materiality-PASS diluted shares ASSUMPTION",
                source_metric="fully_diluted_shares", source_class="ASSUMPTION", source_route=ROUTE,
                source_context_sha256=proof["proof_sha256"],
                source_r6_package_sha256=proof["package_sha256"],
                source_r7x_manifest_sha256=proof["envelope_manifest_sha256"])


def make_proposal(base, proof):
    matrix = [decision(proof) if x["field"] == SHARE else copy.deepcopy(x) for x in base["draft_input_matrix"]]
    baseline = copy.deepcopy(base["baseline_context"])
    baseline["fully_diluted_shares"] = projection(proof)
    result = dict(
        schema_version=SCHEMA, status=STATUS, canonical=False, target=copy.deepcopy(base["target"]),
        policy=dict(version="evidence-draft-binding-v0.9-r6-assumption", as_of=base["policy"]["as_of"],
                    base_policy_version=base["policy"]["version"], share_route=ROUTE,
                    direct_bind_requires=["R6_REVALIDATED","MATERIALITY_PASS","ASSUMPTION_NOT_DERIVED","EXPLICIT_DRAFT_APPROVAL"]),
        identity=copy.deepcopy(base["identity"]), baseline_context=baseline,
        conflicts=copy.deepcopy(base["conflicts"]), draft_input_matrix=matrix, completeness=counts(matrix),
        source_observation_sha256=copy.deepcopy(base["source_observation_sha256"]),
        source_r6_package_sha256=proof["package_sha256"], source_r6_proof_sha256=proof["proof_sha256"],
        r6_binding_proof=copy.deepcopy(proof), base_proposal=copy.deepcopy(base),
        base_proposal_sha256=base["proposal_sha256"],
        warning_en="Noncanonical; diluted shares class is ASSUMPTION, not DERIVED.",
        warning_ko="비정식이며 희석주식수는 가정입니다.", proposal_sha256="")
    result["proposal_sha256"] = sha_field(result, "proposal_sha256")
    return result


def build_assumption_proposal(base, proof):
    eligibility(base, proof)
    value = make_proposal(base, proof)
    validate_assumption_proposal(value)
    return value


def validate_assumption_proposal(value):
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA or value.get("canonical") is not False:
        raise CaseServiceError("R8 proposal schema/authority invalid")
    base, proof = value.get("base_proposal"), value.get("r6_binding_proof")
    if not isinstance(base, dict) or not isinstance(proof, dict):
        raise CaseServiceError("R8 needs M28 base and complete R6 proof")
    eligibility(base, proof)
    if value != make_proposal(base, proof):
        raise CaseServiceError("R8 proposal provenance/identity/SHA projection mismatch")
    return dict(status="PASS_R8_PROPOSAL", proposal_sha256=value["proposal_sha256"],
                source_class="ASSUMPTION", package_sha256=proof["package_sha256"])
