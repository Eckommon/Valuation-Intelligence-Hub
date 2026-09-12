"""M28 reviewed minority-interest FACT → Draft binding proposal v0.8."""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_binding import DIRECT_BIND, MATERIAL_FIELDS, STATUS
from valuation_hub.market_price_draft_binding import SCHEMA_VERSION_V7, validate_binding_proposal_v7
from valuation_hub.minority_interest import validate_reviewed_minority_interest

SCHEMA_VERSION_V8 = "draft-binding-proposal-v0.8"
POLICY_VERSION_V8 = "evidence-draft-binding-v0.8-minority-interest"
DIRECT_REQUIREMENTS = [
    "REVIEWED_NORMALIZED_FACT",
    "FRESH_MINORITY_INTEREST",
    "EXACT_OR_HUMAN_RESOLVED_PERIOD_END",
    "TIER_A_SOURCE",
    "HUMAN_REVIEW_ASSERTION",
    "EXACT_ENTITY_SCOPE_CURRENCY_AS_OF",
    "MISSING_IS_NOT_ZERO",
]


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    out = copy.deepcopy(value); out.pop(key, None); return out


def _counts(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    state_counts: dict[str, int] = {}
    for item in matrix: state_counts[item["state"]] = state_counts.get(item["state"], 0) + 1
    return {
        "material_field_count": len(MATERIAL_FIELDS), "classified_field_count": len(matrix), "state_counts": state_counts,
        "direct_bind_count": state_counts.get(DIRECT_BIND, 0), "unresolved_count": sum(c for s, c in state_counts.items() if s != DIRECT_BIND),
    }


def _eligible_package(package: dict[str, Any]) -> None:
    checked = validate_reviewed_minority_interest(package)
    if checked.get("eligible") is not True or package.get("class") != "NORMALIZED_FACT" or package.get("binding_eligibility") != {"eligible": True, "reason": "REVIEWED_FRESH_MINORITY_INTEREST_FACT"}:
        raise CaseServiceError("only reviewed fresh minority-interest FACT can bind / 검토완료 최신 비지배지분 FACT만 바인딩 가능")


def _projection(package: dict[str, Any]) -> dict[str, Any]:
    observation = package["observation"]
    assertion = package["review_assertion"]
    return {
        "metric": "minority_interest_fact", "value": package["value"], "unit": package["unit"], "class": "NORMALIZED_FACT",
        "entity": copy.deepcopy(package["entity"]), "as_of": package["as_of"], "resolved_period_end": package["resolved_period_end"],
        "date_resolution": package["date_resolution"], "freshness": copy.deepcopy(package["freshness"]), "context_sha256": package["package_sha256"],
        "source_minority_interest_package_sha256": package["package_sha256"], "source_observation_sha256": observation["observation_sha256"],
        "source_snapshot_sha256": package["source"]["snapshot_sha256"], "review_assertion_sha256": assertion["assertion_sha256"],
    }


def _decision(package: dict[str, Any]) -> dict[str, Any]:
    observation = package["observation"]
    assertion = package["review_assertion"]
    return {
        "field": "equity.minority_interest", "state": DIRECT_BIND,
        "rationale": "human-reviewed fresh source-backed minority-interest FACT / 인간검토완료 최신 출처기반 비지배지분 FACT",
        "source_metric": "minority_interest_fact", "source_class": "NORMALIZED_FACT", "source_context_sha256": package["package_sha256"],
        "source_minority_interest_package_sha256": package["package_sha256"], "source_observation_sha256": observation["observation_sha256"],
        "source_snapshot_sha256": package["source"]["snapshot_sha256"], "review_assertion_sha256": assertion["assertion_sha256"],
        "resolved_period_end": package["resolved_period_end"], "date_resolution": package["date_resolution"],
    }


def _policy(base: dict[str, Any]) -> dict[str, Any]:
    return {"version": POLICY_VERSION_V8, "as_of": base["policy"]["as_of"], "base_policy_version": base["policy"]["version"], "direct_bind_requires": copy.deepcopy(DIRECT_REQUIREMENTS)}


def build_binding_proposal_with_minority_interest(base_proposal: dict[str, Any], package: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(base_proposal, dict) or base_proposal.get("schema_version") != SCHEMA_VERSION_V7:
        raise CaseServiceError("M28 requires draft-binding-proposal-v0.7 base / M28은 v0.7 base proposal 필요")
    validate_binding_proposal_v7(base_proposal); _eligible_package(package)
    identity = base_proposal["identity"]
    if package.get("entity") != {"id": identity.get("entity_id"), "financial_scope": identity.get("financial_scope")}:
        raise CaseServiceError("minority-interest package entity/scope mismatch / 비지배지분 패키지 entity·scope 불일치")
    monetary = identity.get("monetary_unit")
    if monetary is not None and package.get("unit") != str(monetary).upper():
        raise CaseServiceError("minority-interest currency mismatch / 비지배지분 통화 불일치")
    if package.get("as_of") != base_proposal.get("policy", {}).get("as_of"):
        raise CaseServiceError("minority-interest as_of must equal v0.7 proposal as_of / 비지배지분 as_of와 v0.7 proposal 불일치")
    matrix = [_decision(package) if item["field"] == "equity.minority_interest" else copy.deepcopy(item) for item in base_proposal["draft_input_matrix"]]
    baseline = copy.deepcopy(base_proposal["baseline_context"]); baseline["minority_interest_fact"] = _projection(package)
    proposal = {
        "schema_version": SCHEMA_VERSION_V8, "status": STATUS, "canonical": False, "target": copy.deepcopy(base_proposal["target"]),
        "policy": _policy(base_proposal), "identity": copy.deepcopy(identity), "baseline_context": baseline, "conflicts": copy.deepcopy(base_proposal["conflicts"]),
        "draft_input_matrix": matrix, "completeness": _counts(matrix), "source_observation_sha256": copy.deepcopy(base_proposal["source_observation_sha256"]),
        "source_minority_interest_package_sha256": package["package_sha256"], "minority_interest_package": copy.deepcopy(package),
        "base_proposal": copy.deepcopy(base_proposal), "base_proposal_sha256": base_proposal["proposal_sha256"],
        "warning_en": "Minority-interest proposal only. Missing evidence is never interpreted as zero and reviewed FACT remains noncanonical.",
        "warning_ko": "비지배지분 제안 전용입니다. 근거 누락을 0으로 해석하지 않으며 검토완료 FACT도 비정식 상태입니다.", "proposal_sha256": "",
    }
    proposal["proposal_sha256"] = _sha(_without(proposal, "proposal_sha256")); validate_binding_proposal_v8(proposal); return proposal


def validate_binding_proposal_v8(proposal: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(proposal, dict) or proposal.get("schema_version") != SCHEMA_VERSION_V8 or proposal.get("status") != STATUS or proposal.get("canonical") is not False or proposal.get("target") != {"draft_schema_version": "draft-case-v0.1", "model": "equity_fcff"}:
        raise CaseServiceError("minority-interest-aware proposal schema/status/target invalid / 비지배지분-aware 제안 스키마·상태·대상 오류")
    base, package = proposal.get("base_proposal"), proposal.get("minority_interest_package")
    if not isinstance(base, dict) or base.get("schema_version") != SCHEMA_VERSION_V7 or not isinstance(package, dict):
        raise CaseServiceError("minority-interest-aware v0.7 base/package missing / 비지배지분-aware v0.7 base·package 누락")
    validate_binding_proposal_v7(base); _eligible_package(package)
    if proposal.get("base_proposal_sha256") != base.get("proposal_sha256") or proposal.get("source_minority_interest_package_sha256") != package.get("package_sha256"):
        raise CaseServiceError("minority-interest source SHA lineage mismatch / 비지배지분 source SHA lineage 불일치")
    if proposal.get("policy") != _policy(base): raise CaseServiceError("minority-interest policy/base mismatch / 비지배지분 정책·base 불일치")
    identity = proposal.get("identity")
    if identity != base.get("identity") or proposal.get("conflicts") != base.get("conflicts") or proposal.get("source_observation_sha256") != base.get("source_observation_sha256"):
        raise CaseServiceError("minority-interest proposal/base lineage mismatch / 비지배지분 proposal·base lineage 불일치")
    if package.get("entity") != {"id": identity.get("entity_id"), "financial_scope": identity.get("financial_scope")} or package.get("as_of") != proposal["policy"]["as_of"]:
        raise CaseServiceError("minority-interest package identity/as_of mismatch / 비지배지분 패키지 식별·as_of 불일치")
    monetary = identity.get("monetary_unit")
    if monetary is not None and package.get("unit") != str(monetary).upper(): raise CaseServiceError("minority-interest package currency mismatch / 비지배지분 패키지 통화 불일치")
    expected_baseline = copy.deepcopy(base["baseline_context"]); expected_baseline["minority_interest_fact"] = _projection(package)
    if proposal.get("baseline_context") != expected_baseline: raise CaseServiceError("minority-interest baseline projection mismatch / 비지배지분 baseline 투영 불일치")
    matrix = proposal.get("draft_input_matrix")
    if not isinstance(matrix, list) or len(matrix) != len(MATERIAL_FIELDS) or {x.get("field") for x in matrix if isinstance(x, dict)} != set(MATERIAL_FIELDS): raise CaseServiceError("minority-interest binding matrix incomplete / 비지배지분 바인딩 matrix 불완전")
    base_by = {x["field"]: x for x in base["draft_input_matrix"]}; by = {x["field"]: x for x in matrix}
    for field in MATERIAL_FIELDS:
        if field == "equity.minority_interest":
            if by[field] != _decision(package): raise CaseServiceError("minority-interest DIRECT_BIND lineage mismatch / 비지배지분 DIRECT_BIND lineage 불일치")
        elif by[field] != base_by[field]: raise CaseServiceError("M28 may replace only equity.minority_interest / M28은 equity.minority_interest만 변경 가능")
    if proposal.get("completeness") != _counts(matrix): raise CaseServiceError("minority-interest completeness mismatch / 비지배지분 completeness 불일치")
    expected = _sha(_without(proposal, "proposal_sha256"))
    if proposal.get("proposal_sha256") != expected: raise CaseServiceError("minority-interest proposal SHA mismatch / 비지배지분 proposal SHA 불일치")
    return {"status": "PASS_MINORITY_INTEREST_AWARE_BINDING_PROPOSAL_VALIDATION", "canonical": False, "proposal_sha256": expected, "direct_bind_count": proposal["completeness"]["direct_bind_count"], "unresolved_count": proposal["completeness"]["unresolved_count"]}


def validate_binding_proposal_any(proposal: dict[str, Any]) -> dict[str, Any]:
    if isinstance(proposal, dict) and proposal.get("schema_version") == SCHEMA_VERSION_V8: return validate_binding_proposal_v8(proposal)
    from valuation_hub.market_price_draft_binding import validate_binding_proposal_any as validate_v7_any
    return validate_v7_any(proposal)
