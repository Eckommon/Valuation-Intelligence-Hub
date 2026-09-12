"""M25 reviewed terminal-growth assumption → Draft binding proposal v0.5.

M25 requires an already validated M24 v0.4 WACC-aware proposal and replaces
only `scenario.terminal_growth`. The terminal-growth package must depend on the
exact same reviewed WACC package embedded in the v0.4 proposal.
"""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_binding import DIRECT_BIND, MATERIAL_FIELDS, STATUS
from valuation_hub.terminal_growth_assumption import validate_reviewed_terminal_growth
from valuation_hub.wacc_draft_binding import SCHEMA_VERSION_V4, validate_binding_proposal_v4

SCHEMA_VERSION_V5 = "draft-binding-proposal-v0.5"
POLICY_VERSION_V5 = "evidence-draft-binding-v0.5-terminal-growth"
DIRECT_REQUIREMENTS = [
    "REVIEWED_ASSUMPTION",
    "REVIEWED_WACC_DEPENDENCY",
    "FRESH_MACRO_ANCHORS",
    "MACRO_NOMINAL_GROWTH_CEILING",
    "TERMINAL_GROWTH_BELOW_WACC",
    "HUMAN_REVIEW_ASSERTION",
    "EXACT_SCENARIO_TARGET_SET",
]


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result.pop(key, None)
    return result


def _counts(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for item in matrix:
        counts[item["state"]] = counts.get(item["state"], 0) + 1
    return {
        "material_field_count": len(MATERIAL_FIELDS),
        "classified_field_count": len(matrix),
        "state_counts": counts,
        "direct_bind_count": counts.get(DIRECT_BIND, 0),
        "unresolved_count": sum(count for state, count in counts.items() if state != DIRECT_BIND),
    }


def _eligible_package(package: dict[str, Any]) -> None:
    checked = validate_reviewed_terminal_growth(package)
    if (
        checked.get("eligible") is not True
        or package.get("class") != "ASSUMPTION"
        or package.get("binding_eligibility") != {"eligible": True, "reason": "REVIEWED_TERMINAL_GROWTH_ASSUMPTION"}
    ):
        raise CaseServiceError("only reviewed eligible terminal-growth assumption can bind / 검토완료 적격 영구성장률 가정만 바인딩 가능")


def _projection(package: dict[str, Any]) -> dict[str, Any]:
    return {
        "metric": "terminal_growth_assumption",
        "value": copy.deepcopy(package["terminal_growth"]),
        "unit": "decimal",
        "class": "ASSUMPTION",
        "entity": copy.deepcopy(package["entity"]),
        "capital_currency": package["capital_currency"],
        "as_of": package["as_of"],
        "scenario_names": copy.deepcopy(package["scenario_names"]),
        "methodology_version": package["methodology_version"],
        "nominal_growth_anchor": package["nominal_growth_anchor"],
        "reviewed_wacc": package["reviewed_wacc"],
        "context_sha256": package["package_sha256"],
        "source_terminal_growth_package_sha256": package["package_sha256"],
        "source_wacc_package_sha256": package["source_wacc_package_sha256"],
        "review_assertion_sha256": package["review_assertion"]["assertion_sha256"],
    }


def _decision(package: dict[str, Any]) -> dict[str, Any]:
    return {
        "field": "scenario.terminal_growth",
        "state": DIRECT_BIND,
        "rationale": "human-reviewed governed terminal-growth assumption / 인간검토완료 거버넌스 영구성장률 가정",
        "source_metric": "terminal_growth_assumption",
        "source_class": "ASSUMPTION",
        "source_context_sha256": package["package_sha256"],
        "source_terminal_growth_package_sha256": package["package_sha256"],
        "source_wacc_package_sha256": package["source_wacc_package_sha256"],
        "review_assertion_sha256": package["review_assertion"]["assertion_sha256"],
        "scenario_names": copy.deepcopy(package["scenario_names"]),
    }


def _policy(base: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": POLICY_VERSION_V5,
        "as_of": base["policy"]["as_of"],
        "base_policy_version": base["policy"]["version"],
        "direct_bind_requires": copy.deepcopy(DIRECT_REQUIREMENTS),
    }


def _same_wacc_dependency(base: dict[str, Any], package: dict[str, Any]) -> None:
    base_wacc = base.get("wacc_package")
    if not isinstance(base_wacc, dict):
        raise CaseServiceError("M25 requires embedded M24 WACC package / M25는 M24 WACC 패키지 필요")
    if package.get("source_wacc_package_sha256") != base_wacc.get("package_sha256"):
        raise CaseServiceError("terminal-growth/WACC package lineage mismatch / 영구성장률·WACC 패키지 lineage 불일치")
    candidate = package.get("candidate")
    if not isinstance(candidate, dict) or candidate.get("wacc_package") != base_wacc:
        raise CaseServiceError("terminal-growth embedded WACC differs from v0.4 base / 영구성장률 내장 WACC와 v0.4 base 불일치")


def build_binding_proposal_with_terminal_growth(
    base_proposal: dict[str, Any],
    terminal_growth_package: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(base_proposal, dict) or base_proposal.get("schema_version") != SCHEMA_VERSION_V4:
        raise CaseServiceError("M25 requires draft-binding-proposal-v0.4 base / M25는 v0.4 base proposal 필요")
    validate_binding_proposal_v4(base_proposal)
    _eligible_package(terminal_growth_package)
    _same_wacc_dependency(base_proposal, terminal_growth_package)

    identity = base_proposal["identity"]
    if terminal_growth_package.get("entity") != {"id": identity.get("entity_id"), "financial_scope": identity.get("financial_scope")}:
        raise CaseServiceError("terminal-growth package entity/scope mismatch / 영구성장률 패키지 entity·scope 불일치")
    monetary = identity.get("monetary_unit")
    if monetary is not None and terminal_growth_package.get("capital_currency") != monetary:
        raise CaseServiceError("terminal-growth capital currency mismatch / 영구성장률 자본통화 불일치")
    base_as_of = base_proposal.get("policy", {}).get("as_of")
    if terminal_growth_package.get("as_of") != base_as_of:
        raise CaseServiceError("terminal-growth as_of must equal v0.4 proposal as_of / 영구성장률 as_of와 v0.4 proposal 불일치")
    base_wacc = base_proposal["wacc_package"]
    if terminal_growth_package.get("scenario_names") != base_wacc.get("scenario_names"):
        raise CaseServiceError("terminal-growth/WACC scenario set mismatch / 영구성장률·WACC 시나리오 집합 불일치")

    matrix = [
        _decision(terminal_growth_package) if item["field"] == "scenario.terminal_growth" else copy.deepcopy(item)
        for item in base_proposal["draft_input_matrix"]
    ]
    baseline = copy.deepcopy(base_proposal["baseline_context"])
    baseline["terminal_growth_assumption"] = _projection(terminal_growth_package)
    result = {
        "schema_version": SCHEMA_VERSION_V5,
        "status": STATUS,
        "canonical": False,
        "target": copy.deepcopy(base_proposal["target"]),
        "policy": _policy(base_proposal),
        "identity": copy.deepcopy(identity),
        "baseline_context": baseline,
        "conflicts": copy.deepcopy(base_proposal["conflicts"]),
        "draft_input_matrix": matrix,
        "completeness": _counts(matrix),
        "source_observation_sha256": copy.deepcopy(base_proposal["source_observation_sha256"]),
        "source_terminal_growth_package_sha256": terminal_growth_package["package_sha256"],
        "source_wacc_package_sha256": terminal_growth_package["source_wacc_package_sha256"],
        "terminal_growth_package": copy.deepcopy(terminal_growth_package),
        "base_proposal": copy.deepcopy(base_proposal),
        "base_proposal_sha256": base_proposal["proposal_sha256"],
        "warning_en": "Terminal-growth-aware proposal only. Terminal growth remains a reviewed valuation assumption, not a historical fact.",
        "warning_ko": "영구성장률-aware 제안 전용입니다. 영구성장률은 과거 사실이 아니라 검토완료 가치평가 가정입니다.",
        "proposal_sha256": "",
    }
    result["proposal_sha256"] = _sha(_without(result, "proposal_sha256"))
    validate_binding_proposal_v5(result)
    return result


def validate_binding_proposal_v5(proposal: dict[str, Any]) -> dict[str, Any]:
    if (
        not isinstance(proposal, dict)
        or proposal.get("schema_version") != SCHEMA_VERSION_V5
        or proposal.get("status") != STATUS
        or proposal.get("canonical") is not False
    ):
        raise CaseServiceError("terminal-growth-aware proposal schema/status invalid / 영구성장률-aware 제안 스키마·상태 오류")
    if proposal.get("target") != {"draft_schema_version": "draft-case-v0.1", "model": "equity_fcff"}:
        raise CaseServiceError("terminal-growth-aware target invalid / 영구성장률-aware 대상 오류")
    base = proposal.get("base_proposal")
    package = proposal.get("terminal_growth_package")
    if not isinstance(base, dict) or not isinstance(package, dict) or base.get("schema_version") != SCHEMA_VERSION_V4:
        raise CaseServiceError("terminal-growth-aware v0.4 base/package missing / 영구성장률-aware v0.4 base·package 누락")
    validate_binding_proposal_v4(base)
    _eligible_package(package)
    _same_wacc_dependency(base, package)
    if proposal.get("base_proposal_sha256") != base.get("proposal_sha256"):
        raise CaseServiceError("terminal-growth base proposal SHA mismatch / 영구성장률 base proposal SHA 불일치")
    if proposal.get("source_terminal_growth_package_sha256") != package.get("package_sha256"):
        raise CaseServiceError("terminal-growth package SHA lineage mismatch / 영구성장률 패키지 SHA lineage 불일치")
    if proposal.get("source_wacc_package_sha256") != package.get("source_wacc_package_sha256"):
        raise CaseServiceError("terminal-growth WACC SHA lineage mismatch / 영구성장률 WACC SHA lineage 불일치")
    if proposal.get("policy") != _policy(base):
        raise CaseServiceError("terminal-growth-aware policy/base mismatch / 영구성장률-aware 정책·base 불일치")

    identity = proposal.get("identity")
    if identity != base.get("identity") or proposal.get("conflicts") != base.get("conflicts") or proposal.get("source_observation_sha256") != base.get("source_observation_sha256"):
        raise CaseServiceError("terminal-growth proposal/base lineage mismatch / 영구성장률 proposal·base lineage 불일치")
    if package.get("entity") != {"id": identity.get("entity_id"), "financial_scope": identity.get("financial_scope")} or package.get("as_of") != proposal["policy"]["as_of"]:
        raise CaseServiceError("terminal-growth package identity/as_of mismatch / 영구성장률 패키지 식별·as_of 불일치")
    monetary = identity.get("monetary_unit")
    if monetary is not None and package.get("capital_currency") != monetary:
        raise CaseServiceError("terminal-growth package capital currency mismatch / 영구성장률 패키지 자본통화 불일치")
    if package.get("scenario_names") != base["wacc_package"].get("scenario_names"):
        raise CaseServiceError("terminal-growth scenario set mismatch with WACC / 영구성장률 시나리오 집합과 WACC 불일치")

    expected_baseline = copy.deepcopy(base["baseline_context"])
    expected_baseline["terminal_growth_assumption"] = _projection(package)
    if proposal.get("baseline_context") != expected_baseline:
        raise CaseServiceError("terminal-growth baseline projection mismatch / 영구성장률 baseline 투영 불일치")
    matrix = proposal.get("draft_input_matrix")
    if not isinstance(matrix, list) or len(matrix) != len(MATERIAL_FIELDS) or {item.get("field") for item in matrix if isinstance(item, dict)} != set(MATERIAL_FIELDS):
        raise CaseServiceError("terminal-growth-aware binding matrix incomplete / 영구성장률-aware 바인딩 matrix 불완전")
    base_by = {item["field"]: item for item in base["draft_input_matrix"]}
    by_field = {item["field"]: item for item in matrix}
    for field in MATERIAL_FIELDS:
        if field != "scenario.terminal_growth" and by_field[field] != base_by[field]:
            raise CaseServiceError("M25 may replace only scenario.terminal_growth / M25는 scenario.terminal_growth 판정만 변경 가능")
    if by_field["scenario.terminal_growth"] != _decision(package):
        raise CaseServiceError("terminal-growth DIRECT_BIND lineage/classification mismatch / 영구성장률 DIRECT_BIND lineage·판정 불일치")
    if proposal.get("completeness") != _counts(matrix):
        raise CaseServiceError("terminal-growth completeness mismatch / 영구성장률 completeness 불일치")
    expected_sha = _sha(_without(proposal, "proposal_sha256"))
    if proposal.get("proposal_sha256") != expected_sha:
        raise CaseServiceError("terminal-growth-aware proposal SHA mismatch / 영구성장률-aware proposal SHA 불일치")
    return {
        "status": "PASS_TERMINAL_GROWTH_AWARE_BINDING_PROPOSAL_VALIDATION",
        "canonical": False,
        "proposal_sha256": expected_sha,
        "direct_bind_count": proposal["completeness"]["direct_bind_count"],
        "unresolved_count": proposal["completeness"]["unresolved_count"],
    }


def validate_binding_proposal_any(proposal: dict[str, Any]) -> dict[str, Any]:
    if isinstance(proposal, dict) and proposal.get("schema_version") == SCHEMA_VERSION_V5:
        return validate_binding_proposal_v5(proposal)
    from valuation_hub.wacc_draft_binding import validate_binding_proposal_any as validate_binding_proposal_any_v4

    return validate_binding_proposal_any_v4(proposal)
