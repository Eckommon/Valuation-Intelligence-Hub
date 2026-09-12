"""M26 reviewed integrated forecast → Draft binding proposal v0.6.

M26 wraps only a validated v0.5 proposal and replaces the six FCFF forecast-year
material decisions as one governed block from a single reviewed assumption package.
"""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_binding import DIRECT_BIND, MATERIAL_FIELDS, STATUS
from valuation_hub.forecast_assumption import FORECAST_COMPONENTS, validate_reviewed_forecast
from valuation_hub.terminal_growth_draft_binding import SCHEMA_VERSION_V5, validate_binding_proposal_v5

SCHEMA_VERSION_V6 = "draft-binding-proposal-v0.6"
POLICY_VERSION_V6 = "evidence-draft-binding-v0.6-integrated-forecast"
FORECAST_FIELDS = tuple(f"scenario.years.{component}" for component in FORECAST_COMPONENTS)
DIRECT_REQUIREMENTS = [
    "REVIEWED_ASSUMPTION",
    "INTEGRATED_FORECAST_BLOCK",
    "COMMON_FORECAST_YEAR_SET",
    "COMPLETE_SIX_COMPONENT_ROWS",
    "ATOMIC_ALL_SIX_APPROVAL",
    "HUMAN_REVIEW_ASSERTION",
    "EXACT_SCENARIO_TARGET_SET",
    "EXACT_FORECAST_YEAR_SET",
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
    checked = validate_reviewed_forecast(package)
    if (
        checked.get("eligible") is not True
        or package.get("class") != "ASSUMPTION"
        or package.get("binding_eligibility") != {"eligible": True, "reason": "REVIEWED_INTEGRATED_FORECAST_ASSUMPTION"}
    ):
        raise CaseServiceError("only reviewed eligible forecast package can bind / 검토완료 적격 Forecast 패키지만 바인딩 가능")


def _projection(package: dict[str, Any]) -> dict[str, Any]:
    return {
        "metric": "integrated_forecast_assumption",
        "value": copy.deepcopy(package["scenarios"]),
        "class": "ASSUMPTION",
        "entity": copy.deepcopy(package["entity"]),
        "capital_currency": package["capital_currency"],
        "as_of": package["as_of"],
        "scenario_names": copy.deepcopy(package["scenario_names"]),
        "forecast_years": copy.deepcopy(package["forecast_years"]),
        "methodology_version": package["methodology_version"],
        "context_sha256": package["package_sha256"],
        "source_forecast_package_sha256": package["package_sha256"],
        "forecast_block_sha256": package["forecast_block_sha256"],
        "review_assertion_sha256": package["review_assertion"]["assertion_sha256"],
    }


def _decision(package: dict[str, Any], component: str) -> dict[str, Any]:
    return {
        "field": f"scenario.years.{component}",
        "state": DIRECT_BIND,
        "rationale": "human-reviewed integrated forecast assumption / 인간검토완료 통합 Forecast 가정",
        "source_metric": "integrated_forecast_assumption",
        "source_class": "ASSUMPTION",
        "forecast_component": component,
        "source_context_sha256": package["package_sha256"],
        "source_forecast_package_sha256": package["package_sha256"],
        "forecast_block_sha256": package["forecast_block_sha256"],
        "review_assertion_sha256": package["review_assertion"]["assertion_sha256"],
        "scenario_names": copy.deepcopy(package["scenario_names"]),
        "forecast_years": copy.deepcopy(package["forecast_years"]),
    }


def _policy(base: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": POLICY_VERSION_V6,
        "as_of": base["policy"]["as_of"],
        "base_policy_version": base["policy"]["version"],
        "direct_bind_requires": copy.deepcopy(DIRECT_REQUIREMENTS),
        "atomic_forecast_fields": list(FORECAST_FIELDS),
    }


def _base_scenario_names(base: dict[str, Any]) -> list[str]:
    terminal_package = base.get("terminal_growth_package")
    if not isinstance(terminal_package, dict) or not isinstance(terminal_package.get("scenario_names"), list):
        raise CaseServiceError("M26 requires v0.5 terminal-growth scenario set / M26은 v0.5 영구성장률 시나리오 집합 필요")
    return terminal_package["scenario_names"]


def build_binding_proposal_with_forecast(base_proposal: dict[str, Any], forecast_package: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(base_proposal, dict) or base_proposal.get("schema_version") != SCHEMA_VERSION_V5:
        raise CaseServiceError("M26 requires draft-binding-proposal-v0.5 base / M26은 v0.5 base proposal 필요")
    validate_binding_proposal_v5(base_proposal)
    _eligible_package(forecast_package)
    identity = base_proposal["identity"]
    if forecast_package.get("entity") != {"id": identity.get("entity_id"), "financial_scope": identity.get("financial_scope")}:
        raise CaseServiceError("forecast package entity/scope mismatch / Forecast 패키지 entity·scope 불일치")
    monetary = identity.get("monetary_unit")
    if monetary is not None and forecast_package.get("capital_currency") != monetary:
        raise CaseServiceError("forecast capital currency mismatch / Forecast 자본통화 불일치")
    if forecast_package.get("as_of") != base_proposal.get("policy", {}).get("as_of"):
        raise CaseServiceError("forecast as_of must equal v0.5 proposal as_of / Forecast as_of와 v0.5 proposal 불일치")
    if forecast_package.get("scenario_names") != _base_scenario_names(base_proposal):
        raise CaseServiceError("forecast/base scenario set mismatch / Forecast·base 시나리오 집합 불일치")

    decision_by_field = {
        f"scenario.years.{component}": _decision(forecast_package, component)
        for component in FORECAST_COMPONENTS
    }
    matrix = [copy.deepcopy(decision_by_field.get(item["field"], item)) for item in base_proposal["draft_input_matrix"]]
    baseline = copy.deepcopy(base_proposal["baseline_context"])
    baseline["integrated_forecast_assumption"] = _projection(forecast_package)
    result = {
        "schema_version": SCHEMA_VERSION_V6,
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
        "source_forecast_package_sha256": forecast_package["package_sha256"],
        "forecast_block_sha256": forecast_package["forecast_block_sha256"],
        "forecast_package": copy.deepcopy(forecast_package),
        "base_proposal": copy.deepcopy(base_proposal),
        "base_proposal_sha256": base_proposal["proposal_sha256"],
        "warning_en": "Integrated forecast proposal only. Forecast rows remain reviewed valuation assumptions and must be approved atomically.",
        "warning_ko": "통합 Forecast 제안 전용입니다. Forecast 행은 검토완료 가치평가 가정이며 원자적으로 승인해야 합니다.",
        "proposal_sha256": "",
    }
    result["proposal_sha256"] = _sha(_without(result, "proposal_sha256"))
    validate_binding_proposal_v6(result)
    return result


def validate_binding_proposal_v6(proposal: dict[str, Any]) -> dict[str, Any]:
    if (
        not isinstance(proposal, dict)
        or proposal.get("schema_version") != SCHEMA_VERSION_V6
        or proposal.get("status") != STATUS
        or proposal.get("canonical") is not False
        or proposal.get("target") != {"draft_schema_version": "draft-case-v0.1", "model": "equity_fcff"}
    ):
        raise CaseServiceError("forecast-aware proposal schema/status/target invalid / Forecast-aware 제안 스키마·상태·대상 오류")
    base = proposal.get("base_proposal")
    package = proposal.get("forecast_package")
    if not isinstance(base, dict) or base.get("schema_version") != SCHEMA_VERSION_V5 or not isinstance(package, dict):
        raise CaseServiceError("forecast-aware v0.5 base/package missing / Forecast-aware v0.5 base·package 누락")
    validate_binding_proposal_v5(base)
    _eligible_package(package)
    if proposal.get("base_proposal_sha256") != base.get("proposal_sha256"):
        raise CaseServiceError("forecast base proposal SHA mismatch / Forecast base proposal SHA 불일치")
    if proposal.get("source_forecast_package_sha256") != package.get("package_sha256") or proposal.get("forecast_block_sha256") != package.get("forecast_block_sha256"):
        raise CaseServiceError("forecast package SHA lineage mismatch / Forecast 패키지 SHA lineage 불일치")
    if proposal.get("policy") != _policy(base):
        raise CaseServiceError("forecast-aware policy/base mismatch / Forecast-aware 정책·base 불일치")
    identity = proposal.get("identity")
    if identity != base.get("identity") or proposal.get("conflicts") != base.get("conflicts") or proposal.get("source_observation_sha256") != base.get("source_observation_sha256"):
        raise CaseServiceError("forecast proposal/base lineage mismatch / Forecast proposal·base lineage 불일치")
    if package.get("entity") != {"id": identity.get("entity_id"), "financial_scope": identity.get("financial_scope")} or package.get("as_of") != proposal["policy"]["as_of"]:
        raise CaseServiceError("forecast package identity/as_of mismatch / Forecast 패키지 식별·as_of 불일치")
    monetary = identity.get("monetary_unit")
    if monetary is not None and package.get("capital_currency") != monetary:
        raise CaseServiceError("forecast package capital currency mismatch / Forecast 패키지 자본통화 불일치")
    if package.get("scenario_names") != _base_scenario_names(base):
        raise CaseServiceError("forecast package scenario set mismatch / Forecast 패키지 시나리오 집합 불일치")

    expected_baseline = copy.deepcopy(base["baseline_context"])
    expected_baseline["integrated_forecast_assumption"] = _projection(package)
    if proposal.get("baseline_context") != expected_baseline:
        raise CaseServiceError("forecast baseline projection mismatch / Forecast baseline 투영 불일치")
    matrix = proposal.get("draft_input_matrix")
    if not isinstance(matrix, list) or len(matrix) != len(MATERIAL_FIELDS) or {item.get("field") for item in matrix if isinstance(item, dict)} != set(MATERIAL_FIELDS):
        raise CaseServiceError("forecast-aware binding matrix incomplete / Forecast-aware 바인딩 matrix 불완전")
    base_by = {item["field"]: item for item in base["draft_input_matrix"]}
    by_field = {item["field"]: item for item in matrix}
    for field in MATERIAL_FIELDS:
        if field in FORECAST_FIELDS:
            component = field.removeprefix("scenario.years.")
            if by_field[field] != _decision(package, component):
                raise CaseServiceError("forecast DIRECT_BIND lineage/classification mismatch / Forecast DIRECT_BIND lineage·판정 불일치")
        elif by_field[field] != base_by[field]:
            raise CaseServiceError("M26 may replace only six forecast-year decisions / M26은 여섯 Forecast 연도 판정만 변경 가능")
    if proposal.get("completeness") != _counts(matrix):
        raise CaseServiceError("forecast completeness mismatch / Forecast completeness 불일치")
    expected = _sha(_without(proposal, "proposal_sha256"))
    if proposal.get("proposal_sha256") != expected:
        raise CaseServiceError("forecast-aware proposal SHA mismatch / Forecast-aware proposal SHA 불일치")
    return {
        "status": "PASS_FORECAST_AWARE_BINDING_PROPOSAL_VALIDATION",
        "canonical": False,
        "proposal_sha256": expected,
        "direct_bind_count": proposal["completeness"]["direct_bind_count"],
        "unresolved_count": proposal["completeness"]["unresolved_count"],
        "atomic_forecast_fields": list(FORECAST_FIELDS),
    }


def validate_binding_proposal_any(proposal: dict[str, Any]) -> dict[str, Any]:
    if isinstance(proposal, dict) and proposal.get("schema_version") == SCHEMA_VERSION_V6:
        return validate_binding_proposal_v6(proposal)
    from valuation_hub.terminal_growth_draft_binding import validate_binding_proposal_any as validate_binding_proposal_any_v5

    return validate_binding_proposal_any_v5(proposal)
