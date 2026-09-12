"""M25 governed terminal-growth assumption package.

Terminal growth is a perpetual valuation assumption, not a historical fact.
M25 requires a reviewed M24 WACC package, explicit long-run macro anchors,
scenario-specific analyst assumptions, and a separate human review lock.
"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import date, datetime
from math import isfinite
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.wacc_assumption import validate_reviewed_wacc

ANCHOR_SCHEMA = "terminal-growth-anchor-input-v0.1"
ANCHOR_STATUS = "TERMINAL_GROWTH_ANCHOR_INPUT"
CANDIDATE_SCHEMA = "terminal-growth-assumption-candidate-v0.1"
CANDIDATE_STATUS = "TERMINAL_GROWTH_ASSUMPTION_CANDIDATE"
REVIEW_SCHEMA = "terminal-growth-review-assertion-v0.1"
REVIEW_STATUS = "TERMINAL_GROWTH_REVIEW_APPROVED"
PACKAGE_SCHEMA = "reviewed-terminal-growth-assumption-v0.1"
PACKAGE_STATUS = "TERMINAL_GROWTH_ASSUMPTION_REVIEWED"
METHODOLOGY_VERSION = "terminal-growth-macro-anchor-v0.1"

LONG_RUN_INFLATION = "long_run_inflation"
LONG_RUN_REAL_GROWTH = "long_run_real_growth"
REQUIRED_ANCHORS = (LONG_RUN_INFLATION, LONG_RUN_REAL_GROWTH)
SOURCE_CLAIM_CLASSES = ("FACT", "NORMALIZED_FACT", "ASSUMPTION")
SOURCE_TIERS = ("A", "B", "C", "D")
REVIEWABLE_TIERS = {"A", "B", "C"}
FRESHNESS_MAX_AGE_DAYS = {
    LONG_RUN_INFLATION: 365,
    LONG_RUN_REAL_GROWTH: 365,
}


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result.pop(key, None)
    return result


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
        raise CaseServiceError(f"{label} must be finite number / {label} 유한 숫자 필요")
    return float(value)


def _canonical_date(value: Any, label: str) -> date:
    if not isinstance(value, str):
        raise CaseServiceError(f"{label} date required / {label} 날짜 필요")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise CaseServiceError(f"{label} must be YYYY-MM-DD / {label} 날짜 형식 오류") from exc
    if parsed.isoformat() != value:
        raise CaseServiceError(f"{label} must be canonical YYYY-MM-DD / {label} 정규 날짜 필요")
    return parsed


def _timestamp(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise CaseServiceError(f"{label} timestamp required / {label} 시각 필요")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CaseServiceError(f"{label} ISO timestamp invalid / {label} ISO 시각 오류") from exc
    if parsed.tzinfo is None:
        raise CaseServiceError(f"{label} timezone required / {label} 시간대 필요")
    return parsed.isoformat()


def _rate_range(metric: str, value: float) -> None:
    # These are input-sanity bounds, not economic forecasts.
    if not -0.50 < value < 0.50:
        raise CaseServiceError(f"{metric} outside v0.1 sanity range / {metric} v0.1 범위 오류")


def _scenario_names(value: Any) -> list[str]:
    if not isinstance(value, list) or not value:
        raise CaseServiceError("scenario_names non-empty list required / scenario_names 필요")
    names = [str(item).strip().upper() for item in value]
    if any(not name or len(name) > 80 for name in names) or len(set(names)) != len(names):
        raise CaseServiceError("scenario_names must be unique non-empty names / scenario_names 고유 이름 필요")
    return sorted(names)


def _scenario_assumptions(value: Any, expected_names: list[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != len(expected_names):
        raise CaseServiceError("one terminal-growth assumption per scenario required / 시나리오별 영구성장률 가정 필요")
    by_name: dict[str, dict[str, Any]] = {}
    for raw in value:
        if not isinstance(raw, dict):
            raise CaseServiceError("terminal-growth scenario assumption object required / 영구성장률 시나리오 가정 객체 필요")
        name = str(raw.get("scenario_name", "")).strip().upper()
        growth = _finite(raw.get("terminal_growth"), f"{name or 'scenario'}.terminal_growth")
        rationale = raw.get("rationale")
        if not name or name in by_name or not isinstance(rationale, str) or not rationale.strip() or len(rationale) > 4000:
            raise CaseServiceError("terminal-growth scenario name/rationale invalid / 영구성장률 시나리오 이름·근거 오류")
        if growth <= -1:
            raise CaseServiceError("terminal growth must be greater than -1 / 영구성장률은 -1보다 커야 함")
        by_name[name] = {
            "scenario_name": name,
            "terminal_growth": growth,
            "rationale": rationale.strip(),
        }
    if set(by_name) != set(expected_names):
        raise CaseServiceError("terminal-growth scenario set mismatch / 영구성장률 시나리오 집합 불일치")
    return [by_name[name] for name in expected_names]


def build_terminal_growth_anchor_input(
    *,
    metric: str,
    value: float,
    observed_on: str,
    claim_class: str,
    source_publisher: str,
    source_type: str,
    source_tier: str,
    source_locator: str,
    source_sha256: str,
) -> dict[str, Any]:
    if metric not in REQUIRED_ANCHORS:
        raise CaseServiceError("unsupported terminal-growth anchor metric / 미지원 영구성장률 anchor 지표")
    number = _finite(value, metric)
    _rate_range(metric, number)
    _canonical_date(observed_on, "observed_on")
    if claim_class not in SOURCE_CLAIM_CLASSES:
        raise CaseServiceError("terminal-growth anchor claim_class invalid / 영구성장률 anchor claim_class 오류")
    if source_tier not in SOURCE_TIERS:
        raise CaseServiceError("terminal-growth anchor source tier invalid / 영구성장률 anchor source tier 오류")
    for label, text in (
        ("source_publisher", source_publisher),
        ("source_type", source_type),
        ("source_locator", source_locator),
    ):
        if not isinstance(text, str) or not text.strip():
            raise CaseServiceError(f"{label} required / {label} 필요")
    if not isinstance(source_sha256, str) or len(source_sha256) != 64 or any(ch not in "0123456789abcdef" for ch in source_sha256):
        raise CaseServiceError("source_sha256 invalid / source_sha256 오류")
    result = {
        "schema_version": ANCHOR_SCHEMA,
        "status": ANCHOR_STATUS,
        "canonical": False,
        "claim_class": claim_class,
        "metric": metric,
        "value": number,
        "unit": "decimal",
        "observed_on": observed_on,
        "source": {
            "publisher": source_publisher.strip(),
            "type": source_type.strip(),
            "tier": source_tier,
            "locator": source_locator.strip(),
            "source_sha256": source_sha256,
        },
        "input_sha256": "",
    }
    result["input_sha256"] = _sha(_without(result, "input_sha256"))
    validate_terminal_growth_anchor_input(result)
    return result


def validate_terminal_growth_anchor_input(value: dict[str, Any]) -> dict[str, Any]:
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != ANCHOR_SCHEMA
        or value.get("status") != ANCHOR_STATUS
        or value.get("canonical") is not False
    ):
        raise CaseServiceError("terminal-growth anchor schema/status invalid / 영구성장률 anchor 스키마·상태 오류")
    metric = value.get("metric")
    if metric not in REQUIRED_ANCHORS or value.get("unit") != "decimal":
        raise CaseServiceError("terminal-growth anchor metric/unit invalid / 영구성장률 anchor 지표·단위 오류")
    number = _finite(value.get("value"), str(metric))
    _rate_range(str(metric), number)
    _canonical_date(value.get("observed_on"), "observed_on")
    if value.get("claim_class") not in SOURCE_CLAIM_CLASSES:
        raise CaseServiceError("terminal-growth anchor claim class invalid / 영구성장률 anchor claim class 오류")
    source = value.get("source")
    if not isinstance(source, dict) or source.get("tier") not in SOURCE_TIERS:
        raise CaseServiceError("terminal-growth anchor provenance invalid / 영구성장률 anchor provenance 오류")
    for field in ("publisher", "type", "locator"):
        if not isinstance(source.get(field), str) or not source[field].strip():
            raise CaseServiceError("terminal-growth anchor provenance incomplete / 영구성장률 anchor provenance 불완전")
    source_sha = source.get("source_sha256")
    if not isinstance(source_sha, str) or len(source_sha) != 64 or any(ch not in "0123456789abcdef" for ch in source_sha):
        raise CaseServiceError("terminal-growth anchor source SHA invalid / 영구성장률 anchor source SHA 오류")
    expected = _sha(_without(value, "input_sha256"))
    if value.get("input_sha256") != expected:
        raise CaseServiceError("terminal-growth anchor input SHA mismatch / 영구성장률 anchor input SHA 불일치")
    return {"status": "PASS_TERMINAL_GROWTH_ANCHOR_VALIDATION", "metric": metric, "input_sha256": expected}


def _freshness(item: dict[str, Any], as_of: date) -> dict[str, Any]:
    observed = _canonical_date(item["observed_on"], "observed_on")
    age = (as_of - observed).days
    if age < 0:
        raise CaseServiceError("terminal-growth anchor observed_on after as_of / 영구성장률 anchor 일자가 as_of 이후")
    maximum = FRESHNESS_MAX_AGE_DAYS[item["metric"]]
    return {
        "status": "FRESH" if age <= maximum else "STALE_BLOCKED",
        "age_days": age,
        "max_age_days": maximum,
    }


def _nominal_anchor(by_metric: dict[str, dict[str, Any]]) -> float:
    inflation = by_metric[LONG_RUN_INFLATION]["value"]
    real_growth = by_metric[LONG_RUN_REAL_GROWTH]["value"]
    nominal = (1 + inflation) * (1 + real_growth) - 1
    if not isfinite(nominal) or nominal <= -1:
        raise CaseServiceError("nominal growth anchor invalid / 명목 성장 anchor 오류")
    return nominal


def build_terminal_growth_candidate(
    anchors: list[dict[str, Any]],
    wacc_package: dict[str, Any],
    *,
    scenario_assumptions: list[dict[str, Any]],
) -> dict[str, Any]:
    checked_wacc = validate_reviewed_wacc(wacc_package)
    if checked_wacc.get("eligible") is not True:
        raise CaseServiceError("reviewed WACC package required / 검토완료 WACC 패키지 필요")
    if not isinstance(anchors, list) or len(anchors) != len(REQUIRED_ANCHORS):
        raise CaseServiceError("exact two terminal-growth anchors required / 영구성장률 anchor 정확히 2개 필요")
    by_metric: dict[str, dict[str, Any]] = {}
    for item in anchors:
        validate_terminal_growth_anchor_input(item)
        metric = item["metric"]
        if metric in by_metric:
            raise CaseServiceError("duplicate terminal-growth anchor / 영구성장률 anchor 중복")
        by_metric[metric] = copy.deepcopy(item)
    if list(by_metric) != list(REQUIRED_ANCHORS):
        raise CaseServiceError("terminal-growth anchor order/coverage invalid / 영구성장률 anchor 순서·coverage 오류")

    as_of_date = _canonical_date(wacc_package["as_of"], "as_of")
    names = _scenario_names(wacc_package["scenario_names"])
    assumptions = _scenario_assumptions(scenario_assumptions, names)
    nominal = _nominal_anchor(by_metric)
    wacc = _finite(wacc_package["wacc"], "wacc")
    for item in assumptions:
        growth = item["terminal_growth"]
        if growth >= wacc:
            raise CaseServiceError("terminal growth must be lower than reviewed WACC / 영구성장률은 검토완료 WACC보다 낮아야 함")
        if growth > nominal:
            raise CaseServiceError("terminal growth exceeds long-run nominal macro anchor / 영구성장률이 장기 명목 거시 anchor 초과")

    freshness = {metric: _freshness(item, as_of_date) for metric, item in by_metric.items()}
    all_fresh = all(item["status"] == "FRESH" for item in freshness.values())
    all_tiers = all(item["source"]["tier"] in REVIEWABLE_TIERS for item in by_metric.values())
    result = {
        "schema_version": CANDIDATE_SCHEMA,
        "status": CANDIDATE_STATUS,
        "canonical": False,
        "class": "ASSUMPTION_CANDIDATE",
        "methodology_version": METHODOLOGY_VERSION,
        "entity": copy.deepcopy(wacc_package["entity"]),
        "capital_currency": wacc_package["capital_currency"],
        "as_of": wacc_package["as_of"],
        "scenario_names": names,
        "wacc_package": copy.deepcopy(wacc_package),
        "source_wacc_package_sha256": wacc_package["package_sha256"],
        "anchors": [by_metric[metric] for metric in REQUIRED_ANCHORS],
        "freshness": freshness,
        "calculation": {"nominal_growth_anchor": nominal, "reviewed_wacc": wacc},
        "scenario_assumptions": assumptions,
        "review_readiness": {
            "all_required_anchors_present": True,
            "all_anchors_fresh": all_fresh,
            "all_source_tiers_reviewable": all_tiers,
            "all_scenario_constraints_satisfied": True,
            "eligible_for_human_review": all_fresh and all_tiers,
        },
        "candidate_sha256": "",
    }
    result["candidate_sha256"] = _sha(_without(result, "candidate_sha256"))
    validate_terminal_growth_candidate(result)
    return result


def validate_terminal_growth_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    if (
        not isinstance(candidate, dict)
        or candidate.get("schema_version") != CANDIDATE_SCHEMA
        or candidate.get("status") != CANDIDATE_STATUS
        or candidate.get("canonical") is not False
        or candidate.get("class") != "ASSUMPTION_CANDIDATE"
    ):
        raise CaseServiceError("terminal-growth candidate schema/status/authority invalid / 영구성장률 candidate 스키마·상태·권위 오류")
    if candidate.get("methodology_version") != METHODOLOGY_VERSION:
        raise CaseServiceError("terminal-growth methodology version invalid / 영구성장률 방법론 버전 오류")
    wacc_package = candidate.get("wacc_package")
    if not isinstance(wacc_package, dict):
        raise CaseServiceError("terminal-growth candidate WACC package missing / 영구성장률 candidate WACC 패키지 누락")
    checked_wacc = validate_reviewed_wacc(wacc_package)
    if checked_wacc.get("eligible") is not True or candidate.get("source_wacc_package_sha256") != wacc_package.get("package_sha256"):
        raise CaseServiceError("terminal-growth WACC lineage invalid / 영구성장률 WACC lineage 오류")
    expected_projection = {
        "entity": wacc_package["entity"],
        "capital_currency": wacc_package["capital_currency"],
        "as_of": wacc_package["as_of"],
        "scenario_names": _scenario_names(wacc_package["scenario_names"]),
    }
    for field, expected in expected_projection.items():
        if candidate.get(field) != expected:
            raise CaseServiceError("terminal-growth candidate WACC projection mismatch / 영구성장률 candidate WACC 투영 불일치")

    anchors = candidate.get("anchors")
    if not isinstance(anchors, list) or len(anchors) != len(REQUIRED_ANCHORS):
        raise CaseServiceError("terminal-growth candidate anchors invalid / 영구성장률 candidate anchor 오류")
    by_metric: dict[str, dict[str, Any]] = {}
    for item in anchors:
        validate_terminal_growth_anchor_input(item)
        metric = item["metric"]
        if metric in by_metric:
            raise CaseServiceError("terminal-growth candidate duplicate anchor / 영구성장률 candidate anchor 중복")
        by_metric[metric] = item
    if list(by_metric) != list(REQUIRED_ANCHORS):
        raise CaseServiceError("terminal-growth candidate anchor order/coverage invalid / 영구성장률 candidate anchor 순서·coverage 오류")

    nominal = _nominal_anchor(by_metric)
    wacc = _finite(wacc_package["wacc"], "wacc")
    calculation = candidate.get("calculation")
    expected_calculation = {"nominal_growth_anchor": nominal, "reviewed_wacc": wacc}
    if not isinstance(calculation, dict) or set(calculation) != set(expected_calculation):
        raise CaseServiceError("terminal-growth candidate calculation shape invalid / 영구성장률 candidate 계산구조 오류")
    for field, expected in expected_calculation.items():
        actual = _finite(calculation.get(field), f"calculation.{field}")
        if abs(actual - expected) > 1e-12:
            raise CaseServiceError("terminal-growth candidate calculation mismatch / 영구성장률 candidate 계산 불일치")

    names = expected_projection["scenario_names"]
    assumptions = _scenario_assumptions(candidate.get("scenario_assumptions"), names)
    if candidate.get("scenario_assumptions") != assumptions:
        raise CaseServiceError("terminal-growth scenario assumptions not canonical / 영구성장률 시나리오 가정 정규화 오류")
    for item in assumptions:
        growth = item["terminal_growth"]
        if growth >= wacc:
            raise CaseServiceError("terminal growth is not below reviewed WACC / 영구성장률이 검토완료 WACC 미만이 아님")
        if growth > nominal:
            raise CaseServiceError("terminal growth exceeds nominal macro anchor / 영구성장률이 명목 거시 anchor 초과")

    as_of_date = _canonical_date(candidate["as_of"], "as_of")
    freshness = {metric: _freshness(item, as_of_date) for metric, item in by_metric.items()}
    if candidate.get("freshness") != freshness:
        raise CaseServiceError("terminal-growth candidate freshness mismatch / 영구성장률 candidate 최신성 불일치")
    all_fresh = all(item["status"] == "FRESH" for item in freshness.values())
    all_tiers = all(item["source"]["tier"] in REVIEWABLE_TIERS for item in by_metric.values())
    readiness = {
        "all_required_anchors_present": True,
        "all_anchors_fresh": all_fresh,
        "all_source_tiers_reviewable": all_tiers,
        "all_scenario_constraints_satisfied": True,
        "eligible_for_human_review": all_fresh and all_tiers,
    }
    if candidate.get("review_readiness") != readiness:
        raise CaseServiceError("terminal-growth review readiness mismatch / 영구성장률 검토준비도 불일치")
    expected_sha = _sha(_without(candidate, "candidate_sha256"))
    if candidate.get("candidate_sha256") != expected_sha:
        raise CaseServiceError("terminal-growth candidate SHA mismatch / 영구성장률 candidate SHA 불일치")
    return {
        "status": "PASS_TERMINAL_GROWTH_CANDIDATE_VALIDATION",
        "candidate_sha256": expected_sha,
        "nominal_growth_anchor": nominal,
        "reviewed_wacc": wacc,
        "eligible_for_human_review": readiness["eligible_for_human_review"],
    }


def build_terminal_growth_review_assertion(
    candidate: dict[str, Any],
    *,
    reviewer: str,
    approved_at: str,
    review_basis: str,
) -> dict[str, Any]:
    checked = validate_terminal_growth_candidate(candidate)
    if checked["eligible_for_human_review"] is not True:
        raise CaseServiceError("terminal-growth candidate not eligible for human review / 영구성장률 candidate 인간검토 부적격")
    if not isinstance(reviewer, str) or not reviewer.strip() or len(reviewer) > 160:
        raise CaseServiceError("terminal-growth reviewer required / 영구성장률 reviewer 필요")
    timestamp = _timestamp(approved_at, "approved_at")
    if datetime.fromisoformat(timestamp).date() < _canonical_date(candidate["as_of"], "as_of"):
        raise CaseServiceError("terminal-growth approval cannot predate valuation as_of / 영구성장률 승인이 가치평가 as_of보다 앞설 수 없음")
    if not isinstance(review_basis, str) or not review_basis.strip() or len(review_basis) > 4000:
        raise CaseServiceError("terminal-growth review_basis required / 영구성장률 review_basis 필요")
    result = {
        "schema_version": REVIEW_SCHEMA,
        "status": REVIEW_STATUS,
        "canonical": False,
        "decision": "APPROVE_TERMINAL_GROWTH_ASSUMPTION",
        "candidate_sha256": candidate["candidate_sha256"],
        "source_wacc_package_sha256": candidate["source_wacc_package_sha256"],
        "methodology_version": candidate["methodology_version"],
        "as_of": candidate["as_of"],
        "scenario_names": copy.deepcopy(candidate["scenario_names"]),
        "scenario_assumptions": copy.deepcopy(candidate["scenario_assumptions"]),
        "reviewer": reviewer.strip(),
        "approved_at": timestamp,
        "review_basis": review_basis.strip(),
        "assertion_sha256": "",
    }
    result["assertion_sha256"] = _sha(_without(result, "assertion_sha256"))
    validate_terminal_growth_review_assertion(result, candidate)
    return result


def validate_terminal_growth_review_assertion(assertion: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    checked = validate_terminal_growth_candidate(candidate)
    if checked["eligible_for_human_review"] is not True:
        raise CaseServiceError("review assertion cannot approve ineligible terminal-growth candidate / 부적격 영구성장률 candidate 승인 불가")
    if (
        not isinstance(assertion, dict)
        or assertion.get("schema_version") != REVIEW_SCHEMA
        or assertion.get("status") != REVIEW_STATUS
        or assertion.get("canonical") is not False
        or assertion.get("decision") != "APPROVE_TERMINAL_GROWTH_ASSUMPTION"
    ):
        raise CaseServiceError("terminal-growth review assertion schema/status invalid / 영구성장률 검토승인 스키마·상태 오류")
    expected_projection = {
        "candidate_sha256": candidate["candidate_sha256"],
        "source_wacc_package_sha256": candidate["source_wacc_package_sha256"],
        "methodology_version": candidate["methodology_version"],
        "as_of": candidate["as_of"],
        "scenario_names": candidate["scenario_names"],
        "scenario_assumptions": candidate["scenario_assumptions"],
    }
    for field, expected in expected_projection.items():
        if assertion.get(field) != expected:
            raise CaseServiceError("terminal-growth review assertion candidate lineage mismatch / 영구성장률 검토승인 candidate lineage 불일치")
    if not isinstance(assertion.get("reviewer"), str) or not assertion["reviewer"].strip() or not isinstance(assertion.get("review_basis"), str) or not assertion["review_basis"].strip():
        raise CaseServiceError("terminal-growth review reviewer/basis invalid / 영구성장률 검토 reviewer·basis 오류")
    timestamp = _timestamp(assertion.get("approved_at"), "approved_at")
    if datetime.fromisoformat(timestamp).date() < _canonical_date(candidate["as_of"], "as_of"):
        raise CaseServiceError("terminal-growth approval predates valuation as_of / 영구성장률 승인이 가치평가 as_of보다 앞섬")
    expected_sha = _sha(_without(assertion, "assertion_sha256"))
    if assertion.get("assertion_sha256") != expected_sha:
        raise CaseServiceError("terminal-growth review assertion SHA mismatch / 영구성장률 검토승인 SHA 불일치")
    return {"status": "PASS_TERMINAL_GROWTH_REVIEW_ASSERTION_VALIDATION", "assertion_sha256": expected_sha}


def finalize_reviewed_terminal_growth(candidate: dict[str, Any], assertion: dict[str, Any]) -> dict[str, Any]:
    validate_terminal_growth_candidate(candidate)
    validate_terminal_growth_review_assertion(assertion, candidate)
    values = {item["scenario_name"]: item["terminal_growth"] for item in candidate["scenario_assumptions"]}
    result = {
        "schema_version": PACKAGE_SCHEMA,
        "status": PACKAGE_STATUS,
        "canonical": False,
        "class": "ASSUMPTION",
        "methodology_version": candidate["methodology_version"],
        "entity": copy.deepcopy(candidate["entity"]),
        "capital_currency": candidate["capital_currency"],
        "as_of": candidate["as_of"],
        "scenario_names": copy.deepcopy(candidate["scenario_names"]),
        "terminal_growth": values,
        "nominal_growth_anchor": candidate["calculation"]["nominal_growth_anchor"],
        "reviewed_wacc": candidate["calculation"]["reviewed_wacc"],
        "source_wacc_package_sha256": candidate["source_wacc_package_sha256"],
        "candidate": copy.deepcopy(candidate),
        "review_assertion": copy.deepcopy(assertion),
        "binding_eligibility": {"eligible": True, "reason": "REVIEWED_TERMINAL_GROWTH_ASSUMPTION"},
        "package_sha256": "",
    }
    result["package_sha256"] = _sha(_without(result, "package_sha256"))
    validate_reviewed_terminal_growth(result)
    return result


def validate_reviewed_terminal_growth(package: dict[str, Any]) -> dict[str, Any]:
    if (
        not isinstance(package, dict)
        or package.get("schema_version") != PACKAGE_SCHEMA
        or package.get("status") != PACKAGE_STATUS
        or package.get("canonical") is not False
        or package.get("class") != "ASSUMPTION"
    ):
        raise CaseServiceError("reviewed terminal-growth package schema/status/authority invalid / 검토완료 영구성장률 패키지 스키마·상태·권위 오류")
    candidate = package.get("candidate")
    assertion = package.get("review_assertion")
    if not isinstance(candidate, dict) or not isinstance(assertion, dict):
        raise CaseServiceError("reviewed terminal-growth nested candidate/assertion missing / 검토완료 영구성장률 중첩객체 누락")
    checked = validate_terminal_growth_candidate(candidate)
    validate_terminal_growth_review_assertion(assertion, candidate)
    if checked["eligible_for_human_review"] is not True:
        raise CaseServiceError("reviewed terminal-growth candidate no longer eligible / 검토완료 영구성장률 candidate 부적격")
    values = {item["scenario_name"]: item["terminal_growth"] for item in candidate["scenario_assumptions"]}
    expected_projection = {
        "methodology_version": candidate["methodology_version"],
        "entity": candidate["entity"],
        "capital_currency": candidate["capital_currency"],
        "as_of": candidate["as_of"],
        "scenario_names": candidate["scenario_names"],
        "terminal_growth": values,
        "nominal_growth_anchor": candidate["calculation"]["nominal_growth_anchor"],
        "reviewed_wacc": candidate["calculation"]["reviewed_wacc"],
        "source_wacc_package_sha256": candidate["source_wacc_package_sha256"],
    }
    for field, expected in expected_projection.items():
        if package.get(field) != expected:
            raise CaseServiceError("reviewed terminal-growth projection mismatch / 검토완료 영구성장률 투영 불일치")
    if package.get("binding_eligibility") != {"eligible": True, "reason": "REVIEWED_TERMINAL_GROWTH_ASSUMPTION"}:
        raise CaseServiceError("reviewed terminal-growth binding eligibility invalid / 검토완료 영구성장률 바인딩 적격성 오류")
    expected_sha = _sha(_without(package, "package_sha256"))
    if package.get("package_sha256") != expected_sha:
        raise CaseServiceError("reviewed terminal-growth package SHA mismatch / 검토완료 영구성장률 패키지 SHA 불일치")
    return {
        "status": "PASS_REVIEWED_TERMINAL_GROWTH_VALIDATION",
        "package_sha256": expected_sha,
        "terminal_growth": copy.deepcopy(package["terminal_growth"]),
        "eligible": True,
    }
