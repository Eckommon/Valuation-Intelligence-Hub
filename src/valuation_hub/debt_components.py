"""Governed interest-bearing debt components / 거버넌스 이자부채 구성요소.

M19 deliberately refuses `liabilities → debt`. Only explicit point-in-time debt
component observations may be aggregated. Missing components remain missing.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from math import isfinite
from typing import Any

from valuation_hub import dart_live, financial_normalization, sec_live
from valuation_hub.case_service import CaseServiceError

DEBT_SCHEMA_VERSION = "interest-bearing-debt-evidence-v0.1"
DEBT_STATUS = "INTEREST_BEARING_DEBT_EVIDENCE"
CORE_COMPONENTS = (
    "short_term_borrowings",
    "current_portion_long_term_borrowings",
    "long_term_borrowings",
    "current_portion_bonds",
    "bonds_noncurrent",
)
CORE_COMPONENT_SET = frozenset(CORE_COMPONENTS)
COMPLETE = "COMPLETE_CORE_COMPONENTS"
PARTIAL = "PARTIAL_COMPONENTS"
CONFLICT = "CONFLICT_BLOCKED"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

# SEC CompanyFacts v0.1 support is intentionally narrow. LongTermDebtCurrent and
# LongTermDebtNoncurrent are broad aggregates and are NOT relabeled as narrow
# borrowing/bond components because doing so can double count or misclassify debt.
SEC_COMPONENT_SUPPORT = frozenset({"short_term_borrowings"})

DART_COMPONENT_SPECS = {
    "short_term_borrowings": dart_live.DartMetricSpec(
        "short_term_borrowings", ("BS",), ("ifrs-full_ShorttermBorrowings",), ("단기차입금",)
    ),
    "current_portion_long_term_borrowings": dart_live.DartMetricSpec(
        "current_portion_long_term_borrowings", ("BS",), ("ifrs-full_CurrentPortionOfLongtermBorrowings",), ("유동성장기차입금", "유동성 장기차입금")
    ),
    "long_term_borrowings": dart_live.DartMetricSpec(
        "long_term_borrowings", ("BS",), ("ifrs-full_LongtermBorrowings",), ("장기차입금",)
    ),
    "current_portion_bonds": dart_live.DartMetricSpec(
        "current_portion_bonds", ("BS",), ("ifrs-full_CurrentPortionOfBondsIssued",), ("유동성사채", "유동성 사채")
    ),
    "bonds_noncurrent": dart_live.DartMetricSpec(
        "bonds_noncurrent", ("BS",), ("ifrs-full_BondsIssued",), ("사채",)
    ),
}


def register_debt_component_mappings() -> None:
    """Register conservative exact mappings in existing source/normalization kernels."""
    sec_live.METRIC_SPECS.setdefault(
        "short_term_borrowings",
        sec_live.MetricSpec(
            metric="short_term_borrowings",
            concepts=(("us-gaap", "ShortTermBorrowings"),),
            units=("USD",),
            forms=("10-Q", "10-Q/A", "10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A"),
        ),
    )
    for metric, spec in DART_COMPONENT_SPECS.items():
        dart_live.DART_METRIC_SPECS.setdefault(metric, spec)
    financial_normalization.INSTANT_METRICS.update(CORE_COMPONENTS)


register_debt_component_mappings()


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result.pop(key, None)
    return result


def _number(value: Any, field: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
        raise CaseServiceError(f"{field} must be finite numeric / {field} 유한 숫자 필요")
    return value


def _identity(observation: dict[str, Any]) -> tuple[str, str, str, str]:
    financial_normalization.validate_financial_observation(observation)
    if observation.get("metric") not in CORE_COMPONENT_SET:
        raise CaseServiceError("only explicit debt components may be aggregated / 명시적 debt 구성요소만 집계 가능")
    if observation.get("period", {}).get("kind") != financial_normalization.INSTANT:
        raise CaseServiceError("debt components must be INSTANT observations / debt 구성요소는 INSTANT observation이어야 함")
    return (
        observation["entity"]["id"],
        observation["entity"]["financial_scope"],
        observation["unit"],
        json.dumps(observation["period"], ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False),
    )


def _result_class(observations: list[dict[str, Any]]) -> str:
    classes = [item.get("class") for item in observations]
    if any(value not in {"NORMALIZED_FACT", "NORMALIZED_FACT_CANDIDATE"} for value in classes):
        raise CaseServiceError("debt aggregation requires normalized fact inputs / debt 집계는 정규화 fact 입력 필요")
    return "DERIVED_FACT" if all(value == "NORMALIZED_FACT" for value in classes) else "DERIVED_FACT_CANDIDATE"


def aggregate_interest_bearing_debt(observations: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate explicit compatible debt components without imputing missing values."""
    if not isinstance(observations, list) or not observations or not all(isinstance(item, dict) for item in observations):
        raise CaseServiceError("debt aggregation requires non-empty observation list / debt 집계 observation 목록 필요")
    identities = {_identity(item) for item in observations}
    if len(identities) != 1:
        raise CaseServiceError("debt component entity/scope/unit/period mismatch / debt 구성요소 entity·scope·unit·period 불일치")
    entity_id, scope, unit, period_json = next(iter(identities))
    period = json.loads(period_json)

    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in observations:
        grouped.setdefault(item["metric"], []).append(item)

    selected: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    for metric in CORE_COMPONENTS:
        group = grouped.get(metric, [])
        if not group:
            continue
        distinct_values = {_number(item.get("value"), f"{metric}.value") for item in group}
        if len(distinct_values) > 1:
            conflicts.append({
                "metric": metric,
                "values": sorted(distinct_values),
                "observation_sha256": sorted(item["observation_sha256"] for item in group),
                "source_classes": sorted(item["class"] for item in group),
            })
            continue
        # Equal values reconcile deterministically. A reviewed observation outranks
        # a candidate representation of the identical value.
        chosen = sorted(
            group,
            key=lambda item: (item.get("class") == "NORMALIZED_FACT", item.get("observation_sha256", "")),
            reverse=True,
        )[0]
        selected.append(chosen)

    present = [item["metric"] for item in selected]
    missing = [metric for metric in CORE_COMPONENTS if metric not in grouped]
    conflict_metrics = [item["metric"] for item in conflicts]
    if conflicts:
        coverage_status = CONFLICT
        known_sum: int | float | None = None
        debt_value: int | float | None = None
    else:
        known_sum = sum(_number(item["value"], f"{item['metric']}.value") for item in selected)
        if len(present) == len(CORE_COMPONENTS):
            coverage_status = COMPLETE
            debt_value = known_sum
        else:
            coverage_status = PARTIAL
            debt_value = None

    result_class = _result_class(observations)
    eligible = coverage_status == COMPLETE and result_class == "DERIVED_FACT"
    components = [
        {
            "metric": item["metric"],
            "value": item["value"],
            "class": item["class"],
            "observation_sha256": item["observation_sha256"],
        }
        for item in sorted(selected, key=lambda item: CORE_COMPONENTS.index(item["metric"]))
    ]
    result: dict[str, Any] = {
        "schema_version": DEBT_SCHEMA_VERSION,
        "status": DEBT_STATUS,
        "canonical": False,
        "class": result_class,
        "metric": "interest_bearing_debt",
        "unit": unit,
        "entity": {"id": entity_id, "financial_scope": scope},
        "period": period,
        "coverage": {
            "status": coverage_status,
            "expected_components": list(CORE_COMPONENTS),
            "present_components": present,
            "missing_components": missing,
            "conflict_components": conflict_metrics,
        },
        "components": components,
        "conflicts": conflicts,
        "known_component_sum": known_sum,
        "interest_bearing_debt_value": debt_value,
        "semantic_boundary": {
            "total_liabilities_used": False,
            "lease_liabilities_included": False,
            "missing_as_zero": False,
            "eligible_for_draft_direct_bind": eligible,
            "warning_en": "Debt is derived only from explicit core components; total liabilities and missing components are never substituted.",
            "warning_ko": "Debt는 명시적 핵심 구성요소만으로 파생하며 총부채나 누락항목을 대체값으로 사용하지 않습니다.",
        },
        "policy": {"version": "CORE_INTEREST_BEARING_DEBT_V01", "lease_policy": "EXCLUDED_PENDING_EXPLICIT_POLICY"},
        "debt_sha256": "",
    }
    result["debt_sha256"] = _sha(_without(result, "debt_sha256"))
    validate_interest_bearing_debt_evidence(result)
    return result


def validate_interest_bearing_debt_evidence(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema_version") != DEBT_SCHEMA_VERSION or value.get("status") != DEBT_STATUS:
        raise CaseServiceError("interest-bearing debt schema/status invalid / 이자부채 스키마·상태 오류")
    if value.get("canonical") is not False or value.get("class") not in {"DERIVED_FACT", "DERIVED_FACT_CANDIDATE"}:
        raise CaseServiceError("interest-bearing debt authority invalid / 이자부채 권위 오류")
    if value.get("metric") != "interest_bearing_debt" or not isinstance(value.get("unit"), str) or not value["unit"]:
        raise CaseServiceError("interest-bearing debt metric/unit invalid / 이자부채 metric·unit 오류")
    entity, period, coverage, boundary = value.get("entity"), value.get("period"), value.get("coverage"), value.get("semantic_boundary")
    if not isinstance(entity, dict) or not isinstance(entity.get("id"), str) or not entity.get("id") or not isinstance(entity.get("financial_scope"), str) or not entity.get("financial_scope"):
        raise CaseServiceError("interest-bearing debt entity invalid / 이자부채 entity 오류")
    if not isinstance(period, dict) or period.get("kind") != financial_normalization.INSTANT:
        raise CaseServiceError("interest-bearing debt period invalid / 이자부채 period 오류")
    if not isinstance(coverage, dict) or coverage.get("status") not in {COMPLETE, PARTIAL, CONFLICT}:
        raise CaseServiceError("interest-bearing debt coverage invalid / 이자부채 coverage 오류")
    if coverage.get("expected_components") != list(CORE_COMPONENTS):
        raise CaseServiceError("interest-bearing debt component policy mismatch / 이자부채 구성요소 정책 불일치")
    present = coverage.get("present_components")
    missing = coverage.get("missing_components")
    conflict_metrics = coverage.get("conflict_components")
    if not all(isinstance(item, list) for item in (present, missing, conflict_metrics)):
        raise CaseServiceError("interest-bearing debt coverage lists invalid / 이자부채 coverage 목록 오류")
    if any(metric not in CORE_COMPONENT_SET for metric in present + missing + conflict_metrics):
        raise CaseServiceError("interest-bearing debt coverage metric invalid / 이자부채 coverage metric 오류")
    components = value.get("components")
    conflicts = value.get("conflicts")
    if not isinstance(components, list) or not isinstance(conflicts, list):
        raise CaseServiceError("interest-bearing debt component lineage invalid / 이자부채 구성요소 lineage 오류")
    component_metrics: list[str] = []
    component_sum: int | float = 0
    source_classes: list[str] = []
    for component in components:
        if not isinstance(component, dict) or component.get("metric") not in CORE_COMPONENT_SET or component.get("metric") in component_metrics:
            raise CaseServiceError("interest-bearing debt selected component invalid / 이자부채 선택 구성요소 오류")
        component_metrics.append(component["metric"])
        component_sum += _number(component.get("value"), "component value")
        if component.get("class") not in {"NORMALIZED_FACT", "NORMALIZED_FACT_CANDIDATE"}:
            raise CaseServiceError("interest-bearing debt source class invalid / 이자부채 source class 오류")
        source_classes.append(component["class"])
        sha = component.get("observation_sha256")
        if not isinstance(sha, str) or not SHA256_RE.fullmatch(sha):
            raise CaseServiceError("interest-bearing debt source SHA invalid / 이자부채 source SHA 오류")
    if component_metrics != present:
        raise CaseServiceError("interest-bearing debt present component lineage mismatch / 이자부채 present lineage 불일치")
    for conflict in conflicts:
        if not isinstance(conflict, dict) or conflict.get("metric") not in CORE_COMPONENT_SET or conflict.get("metric") not in conflict_metrics:
            raise CaseServiceError("interest-bearing debt conflict lineage invalid / 이자부채 충돌 lineage 오류")
        hashes = conflict.get("observation_sha256")
        values = conflict.get("values")
        classes = conflict.get("source_classes")
        if not isinstance(hashes, list) or len(hashes) < 2 or any(not isinstance(sha, str) or not SHA256_RE.fullmatch(sha) for sha in hashes):
            raise CaseServiceError("interest-bearing debt conflict hashes invalid / 이자부채 충돌 hash 오류")
        if not isinstance(values, list) or len(values) < 2:
            raise CaseServiceError("interest-bearing debt conflict values invalid / 이자부채 충돌값 오류")
        if not isinstance(classes, list) or len(classes) != len(hashes) or any(item not in {"NORMALIZED_FACT", "NORMALIZED_FACT_CANDIDATE"} for item in classes):
            raise CaseServiceError("interest-bearing debt conflict source classes invalid / 이자부채 충돌 source class 오류")
        source_classes.extend(classes)
    expected_class = "DERIVED_FACT" if source_classes and all(item == "NORMALIZED_FACT" for item in source_classes) else "DERIVED_FACT_CANDIDATE"
    if value.get("class") != expected_class:
        raise CaseServiceError("interest-bearing debt authority propagation mismatch / 이자부채 권위전파 불일치")
    status = coverage["status"]
    known_sum = value.get("known_component_sum")
    debt_value = value.get("interest_bearing_debt_value")
    if status == CONFLICT:
        if not conflicts or known_sum is not None or debt_value is not None:
            raise CaseServiceError("conflict-blocked debt must not expose numeric total / 충돌차단 debt는 numeric total 불가")
    elif status == COMPLETE:
        if missing or conflict_metrics or set(present) != CORE_COMPONENT_SET or _number(known_sum, "known_component_sum") != component_sum or _number(debt_value, "interest_bearing_debt_value") != component_sum:
            raise CaseServiceError("complete debt coverage arithmetic invalid / 완전 debt coverage 산술 오류")
    else:
        if not missing or conflicts or debt_value is not None or _number(known_sum, "known_component_sum") != component_sum:
            raise CaseServiceError("partial debt coverage contract invalid / 부분 debt coverage 계약 오류")
    if not isinstance(boundary, dict) or boundary.get("total_liabilities_used") is not False or boundary.get("lease_liabilities_included") is not False or boundary.get("missing_as_zero") is not False:
        raise CaseServiceError("interest-bearing debt semantic boundary invalid / 이자부채 의미경계 오류")
    eligible = status == COMPLETE and value.get("class") == "DERIVED_FACT"
    if boundary.get("eligible_for_draft_direct_bind") is not eligible:
        raise CaseServiceError("interest-bearing debt Draft eligibility mismatch / 이자부채 Draft 적격성 오류")
    policy = value.get("policy")
    if not isinstance(policy, dict) or policy.get("version") != "CORE_INTEREST_BEARING_DEBT_V01" or policy.get("lease_policy") != "EXCLUDED_PENDING_EXPLICIT_POLICY":
        raise CaseServiceError("interest-bearing debt policy invalid / 이자부채 정책 오류")
    sha = value.get("debt_sha256")
    if not isinstance(sha, str) or not SHA256_RE.fullmatch(sha) or sha != _sha(_without(value, "debt_sha256")):
        raise CaseServiceError("interest-bearing debt SHA-256 mismatch / 이자부채 SHA-256 불일치")
    return {
        "status": "PASS_INTEREST_BEARING_DEBT_VALIDATION",
        "coverage_status": status,
        "class": value["class"],
        "eligible_for_draft_direct_bind": eligible,
        "debt_sha256": sha,
    }
