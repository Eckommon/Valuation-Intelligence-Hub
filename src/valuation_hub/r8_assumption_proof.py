"""M30-R8 independently validated R6 ASSUMPTION proof.

The R6 decision must be reproduced from immutable sources; a reported
package SHA alone is not binding authority.
"""
from __future__ import annotations
import copy
import hashlib
import json
from math import isfinite
from typing import Any
from valuation_hub.case_service import CaseServiceError
from valuation_hub.disclosure_limited_dilution import (
    APPROVE, validate_disclosure_limited_dilution_assumption,
)
from valuation_hub.dilution_envelope_source import validate_source_bound_dilution_envelope_manifest

SCHEMA = "r6-dilution-assumption-binding-proof-v0.1"
ROUTE = "R6_DISCLOSURE_LIMITED_ASSUMPTION"


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _unhashed(obj: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(obj)
    result.pop("proof_sha256", None)
    return result


def build_r6_binding_proof(package: dict[str, Any], base_context: dict[str, Any],
                           hold_inventory: dict[str, Any], historical_dilution: dict[str, Any],
                           source_bound_envelope: dict[str, Any]) -> dict[str, Any]:
    manifest = validate_source_bound_dilution_envelope_manifest(source_bound_envelope)
    checked = validate_disclosure_limited_dilution_assumption(
        package, package["evidence"], package["adjudication"],
        base_context, hold_inventory, historical_dilution, manifest["components"],
    )
    threshold = package["evidence"]["upper_envelope"]["materiality_threshold"]
    spread = package["range"]["relative_upper_spread"]
    if (checked.get("eligible_for_assumption_aware_successor") is not True
        or package.get("class") != "ASSUMPTION"
        or package.get("review_authority", {}).get("decision") != APPROVE
        or package["binding_eligibility"]["eligible_for_m22_derived_fact_direct_bind"] is not False
        or isinstance(threshold, bool) or isinstance(spread, bool)
        or not isinstance(threshold, (int, float)) or not isinstance(spread, (int, float))
        or not isfinite(threshold) or not isfinite(spread) or spread > threshold):
        raise CaseServiceError("R6 package is not a materiality-approved ASSUMPTION")
    result = {
        "schema_version": SCHEMA, "canonical": False, "route": ROUTE,
        "package": copy.deepcopy(package), "base_context": copy.deepcopy(base_context),
        "hold_inventory": copy.deepcopy(hold_inventory),
        "historical_dilution": copy.deepcopy(historical_dilution),
        "source_bound_envelope": copy.deepcopy(source_bound_envelope),
        "package_sha256": package["package_sha256"],
        "envelope_manifest_sha256": source_bound_envelope["manifest_sha256"],
        "proof_sha256": "",
    }
    result["proof_sha256"] = _sha(_unhashed(result))
    return result


def validate_r6_binding_proof(proof: dict[str, Any]) -> dict[str, Any]:
    if (not isinstance(proof, dict) or proof.get("schema_version") != SCHEMA
        or proof.get("canonical") is not False or proof.get("route") != ROUTE):
        raise CaseServiceError("R8 proof schema/authority invalid")
    expected = build_r6_binding_proof(
        proof.get("package"), proof.get("base_context"), proof.get("hold_inventory"),
        proof.get("historical_dilution"), proof.get("source_bound_envelope"),
    )
    if proof != expected:
        raise CaseServiceError("R8 proof underlying source/projection/SHA mismatch")
    return {"status": "PASS_R8_R6_PROOF", "proof_sha256": proof["proof_sha256"],
            "package_sha256": proof["package_sha256"]}
