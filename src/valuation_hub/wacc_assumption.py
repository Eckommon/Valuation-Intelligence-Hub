"""M24 governed WACC assumption package.

WACC is a valuation assumption, not a historical fact. This module keeps sourced
inputs, deterministic arithmetic, and human review as separate authority states.
"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import date, datetime
from math import isfinite
from typing import Any

from valuation_hub.case_service import CaseServiceError

SOURCE_SCHEMA = "wacc-source-input-v0.1"
SOURCE_STATUS = "WACC_SOURCE_INPUT"
CANDIDATE_SCHEMA = "wacc-assumption-candidate-v0.1"
CANDIDATE_STATUS = "WACC_ASSUMPTION_CANDIDATE"
REVIEW_SCHEMA = "wacc-review-assertion-v0.1"
REVIEW_STATUS = "WACC_REVIEW_APPROVED"
PACKAGE_SCHEMA = "reviewed-wacc-assumption-v0.1"
PACKAGE_STATUS = "WACC_ASSUMPTION_REVIEWED"
METHODOLOGY_VERSION = "wacc-capm-market-weights-v0.1"

SOURCE_CLAIM_CLASSES = ("FACT", "NORMALIZED_FACT", "ASSUMPTION")
SOURCE_TIERS = ("A", "B", "C", "D")
REVIEWABLE_TIERS = {"A", "B", "C"}

RISK_FREE_RATE = "risk_free_rate"
EQUITY_RISK_PREMIUM = "equity_risk_premium"
LEVERED_BETA = "levered_beta"
PRE_TAX_COST_OF_DEBT = "pre_tax_cost_of_debt"
EQUITY_MARKET_VALUE = "equity_market_value"
DEBT_MARKET_VALUE = "debt_market_value"
TAX_RATE = "tax_rate"
REQUIRED_METRICS = (
    RISK_FREE_RATE,
    EQUITY_RISK_PREMIUM,
    LEVERED_BETA,
    PRE_TAX_COST_OF_DEBT,
    EQUITY_MARKET_VALUE,
    DEBT_MARKET_VALUE,
    TAX_RATE,
)

RATE_METRICS = {RISK_FREE_RATE, EQUITY_RISK_PREMIUM, PRE_TAX_COST_OF_DEBT, TAX_RATE}
FRESHNESS_MAX_AGE_DAYS = {
    RISK_FREE_RATE: 30,
    EQUITY_RISK_PREMIUM: 90,
    LEVERED_BETA: 180,
    PRE_TAX_COST_OF_DEBT: 180,
    EQUITY_MARKET_VALUE: 30,
    DEBT_MARKET_VALUE: 550,
    TAX_RATE: 550,
}


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    out = copy.deepcopy(value)
    out.pop(key, None)
    return out


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


def _metric_unit(metric: str, capital_currency: str) -> str:
    if metric in RATE_METRICS:
        return "decimal"
    if metric == LEVERED_BETA:
        return "ratio"
    if metric in {EQUITY_MARKET_VALUE, DEBT_MARKET_VALUE}:
        return capital_currency
    raise CaseServiceError(f"unsupported WACC metric / 미지원 WACC 지표: {metric}")


def _range(metric: str, value: float) -> None:
    if metric == RISK_FREE_RATE and not -0.10 <= value <= 0.50:
        raise CaseServiceError("risk_free_rate outside v0.1 range / 무위험금리 범위 오류")
    if metric == EQUITY_RISK_PREMIUM and not 0 <= value <= 0.50:
        raise CaseServiceError("equity_risk_premium outside v0.1 range / ERP 범위 오류")
    if metric == LEVERED_BETA and not -5 <= value <= 10:
        raise CaseServiceError("levered_beta outside v0.1 range / beta 범위 오류")
    if metric == PRE_TAX_COST_OF_DEBT and not 0 <= value <= 0.99:
        raise CaseServiceError("pre_tax_cost_of_debt outside v0.1 range / 세전부채비용 범위 오류")
    if metric == TAX_RATE and not 0 <= value <= 0.99:
        raise CaseServiceError("tax_rate outside v0.1 range / 세율 범위 오류")
    if metric == EQUITY_MARKET_VALUE and value <= 0:
        raise CaseServiceError("equity_market_value must be positive / 자기자본 시장가치 양수 필요")
    if metric == DEBT_MARKET_VALUE and value < 0:
        raise CaseServiceError("debt_market_value must be nonnegative / 부채 시장가치 음수 불가")


def build_wacc_source_input(
    *,
    metric: str,
    value: float,
    unit: str,
    observed_on: str,
    claim_class: str,
    source_publisher: str,
    source_type: str,
    source_tier: str,
    source_locator: str,
    source_sha256: str,
) -> dict[str, Any]:
    if metric not in REQUIRED_METRICS:
        raise CaseServiceError("unsupported WACC source metric / 미지원 WACC 원천지표")
    number = _finite(value, metric)
    _range(metric, number)
    _canonical_date(observed_on, "observed_on")
    if claim_class not in SOURCE_CLAIM_CLASSES:
        raise CaseServiceError("WACC source claim_class invalid / WACC 원천 claim_class 오류")
    if source_tier not in SOURCE_TIERS:
        raise CaseServiceError("WACC source tier invalid / WACC 원천 tier 오류")
    for label, text in (("unit", unit), ("source_publisher", source_publisher), ("source_type", source_type), ("source_locator", source_locator)):
        if not isinstance(text, str) or not text.strip():
            raise CaseServiceError(f"{label} required / {label} 필요")
    if not isinstance(source_sha256, str) or len(source_sha256) != 64 or any(ch not in "0123456789abcdef" for ch in source_sha256):
        raise CaseServiceError("source_sha256 invalid / source_sha256 오류")
    result = {
        "schema_version": SOURCE_SCHEMA,
        "status": SOURCE_STATUS,
        "canonical": False,
        "claim_class": claim_class,
        "metric": metric,
        "value": number,
        "unit": unit.strip(),
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
    validate_wacc_source_input(result)
    return result


def validate_wacc_source_input(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema_version") != SOURCE_SCHEMA or value.get("status") != SOURCE_STATUS or value.get("canonical") is not False:
        raise CaseServiceError("WACC source input schema/status invalid / WACC 원천입력 스키마·상태 오류")
    metric = value.get("metric")
    if metric not in REQUIRED_METRICS:
        raise CaseServiceError("WACC source metric invalid / WACC 원천지표 오류")
    number = _finite(value.get("value"), str(metric)); _range(str(metric), number)
    _canonical_date(value.get("observed_on"), "observed_on")
    if value.get("claim_class") not in SOURCE_CLAIM_CLASSES:
        raise CaseServiceError("WACC source claim_class invalid / WACC 원천 claim_class 오류")
    source = value.get("source")
    if not isinstance(source, dict) or source.get("tier") not in SOURCE_TIERS:
        raise CaseServiceError("WACC source provenance invalid / WACC 원천 provenance 오류")
    for field in ("publisher", "type", "locator"):
        if not isinstance(source.get(field), str) or not source[field].strip():
            raise CaseServiceError("WACC source provenance incomplete / WACC 원천 provenance 불완전")
    source_sha = source.get("source_sha256")
    if not isinstance(source_sha, str) or len(source_sha) != 64 or any(ch not in "0123456789abcdef" for ch in source_sha):
        raise CaseServiceError("WACC source SHA invalid / WACC 원천 SHA 오류")
    expected = _sha(_without(value, "input_sha256"))
    if value.get("input_sha256") != expected:
        raise CaseServiceError("WACC source input SHA-256 mismatch / WACC 원천입력 SHA 불일치")
    return {"status": "PASS_WACC_SOURCE_INPUT_VALIDATION", "input_sha256": expected, "metric": metric}


def _freshness(item: dict[str, Any], as_of: date) -> dict[str, Any]:
    metric = item["metric"]
    observed = _canonical_date(item["observed_on"], "observed_on")
    age = (as_of - observed).days
    if age < 0:
        raise CaseServiceError("WACC source observed_on after as_of / WACC 원천일자가 as_of 이후")
    maximum = FRESHNESS_MAX_AGE_DAYS[metric]
    return {"status": "FRESH" if age <= maximum else "STALE_BLOCKED", "age_days": age, "max_age_days": maximum}


def _scenario_names(values: Any) -> list[str]:
    if not isinstance(values, list) or not values:
        raise CaseServiceError("scenario_names non-empty list required / scenario_names 필요")
    names = [str(x).strip().upper() for x in values]
    if any(not x or len(x) > 80 for x in names) or len(set(names)) != len(names):
        raise CaseServiceError("scenario_names must be unique non-empty names / scenario_names 고유 이름 필요")
    return sorted(names)


def build_wacc_candidate(
    inputs: list[dict[str, Any]],
    *,
    entity_id: str,
    financial_scope: str,
    capital_currency: str,
    as_of: str,
    scenario_names: list[str],
) -> dict[str, Any]:
    if not isinstance(inputs, list) or len(inputs) != len(REQUIRED_METRICS):
        raise CaseServiceError("exact seven WACC source inputs required / WACC 원천입력 정확히 7개 필요")
    if not isinstance(entity_id, str) or not entity_id.strip() or not isinstance(financial_scope, str) or not financial_scope.strip():
        raise CaseServiceError("WACC entity/scope required / WACC entity·scope 필요")
    if not isinstance(capital_currency, str) or not 3 <= len(capital_currency.strip()) <= 8:
        raise CaseServiceError("capital_currency invalid / 자본 통화 오류")
    currency = capital_currency.strip().upper()
    as_of_date = _canonical_date(as_of, "as_of")
    names = _scenario_names(scenario_names)
    by: dict[str, dict[str, Any]] = {}
    for item in inputs:
        validate_wacc_source_input(item)
        metric = item["metric"]
        if metric in by:
            raise CaseServiceError("duplicate WACC source metric / WACC 원천지표 중복")
        expected_unit = _metric_unit(metric, currency)
        if item["unit"] != expected_unit:
            raise CaseServiceError(f"WACC source unit mismatch for {metric} / WACC 원천단위 불일치")
        by[metric] = copy.deepcopy(item)
    if set(by) != set(REQUIRED_METRICS):
        raise CaseServiceError("WACC required metric set incomplete / WACC 필수지표 불완전")

    rf = by[RISK_FREE_RATE]["value"]
    erp = by[EQUITY_RISK_PREMIUM]["value"]
    beta = by[LEVERED_BETA]["value"]
    rd = by[PRE_TAX_COST_OF_DEBT]["value"]
    e = by[EQUITY_MARKET_VALUE]["value"]
    d = by[DEBT_MARKET_VALUE]["value"]
    tax = by[TAX_RATE]["value"]
    total = e + d
    if total <= 0:
        raise CaseServiceError("WACC capital total must be positive / WACC 총자본 양수 필요")
    cost_equity = rf + beta * erp
    weight_equity = e / total
    weight_debt = d / total
    after_tax_debt = rd * (1 - tax)
    wacc = weight_equity * cost_equity + weight_debt * after_tax_debt
    if not isfinite(wacc) or not 0 < wacc <= 0.99:
        raise CaseServiceError("calculated WACC outside Draft-valid range / 계산 WACC가 Draft 허용범위 밖")

    freshness = {metric: _freshness(item, as_of_date) for metric, item in by.items()}
    all_fresh = all(x["status"] == "FRESH" for x in freshness.values())
    all_reviewable_tier = all(item["source"]["tier"] in REVIEWABLE_TIERS for item in by.values())
    candidate = {
        "schema_version": CANDIDATE_SCHEMA,
        "status": CANDIDATE_STATUS,
        "canonical": False,
        "class": "ASSUMPTION_CANDIDATE",
        "methodology_version": METHODOLOGY_VERSION,
        "entity": {"id": entity_id.strip(), "financial_scope": financial_scope.strip()},
        "capital_currency": currency,
        "as_of": as_of,
        "scenario_names": names,
        "inputs": [by[metric] for metric in REQUIRED_METRICS],
        "freshness": freshness,
        "calculation": {
            "cost_of_equity": cost_equity,
            "after_tax_cost_of_debt": after_tax_debt,
            "weight_equity": weight_equity,
            "weight_debt": weight_debt,
            "wacc": wacc,
        },
        "review_readiness": {
            "all_required_inputs_present": True,
            "all_inputs_fresh": all_fresh,
            "all_source_tiers_reviewable": all_reviewable_tier,
            "eligible_for_human_review": all_fresh and all_reviewable_tier,
        },
        "candidate_sha256": "",
    }
    candidate["candidate_sha256"] = _sha(_without(candidate, "candidate_sha256"))
    validate_wacc_candidate(candidate)
    return candidate


def validate_wacc_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(candidate, dict) or candidate.get("schema_version") != CANDIDATE_SCHEMA or candidate.get("status") != CANDIDATE_STATUS or candidate.get("canonical") is not False or candidate.get("class") != "ASSUMPTION_CANDIDATE":
        raise CaseServiceError("WACC candidate schema/status/authority invalid / WACC candidate 스키마·상태·권위 오류")
    if candidate.get("methodology_version") != METHODOLOGY_VERSION:
        raise CaseServiceError("WACC methodology version invalid / WACC 방법론 버전 오류")
    entity = candidate.get("entity")
    if not isinstance(entity, dict) or not isinstance(entity.get("id"), str) or not entity["id"] or not isinstance(entity.get("financial_scope"), str) or not entity["financial_scope"]:
        raise CaseServiceError("WACC candidate entity invalid / WACC candidate entity 오류")
    currency = candidate.get("capital_currency")
    if not isinstance(currency, str) or not 3 <= len(currency) <= 8:
        raise CaseServiceError("WACC candidate currency invalid / WACC candidate 통화 오류")
    as_of = _canonical_date(candidate.get("as_of"), "as_of")
    names = _scenario_names(candidate.get("scenario_names"))
    if candidate.get("scenario_names") != names:
        raise CaseServiceError("WACC scenario_names must be sorted canonical names / WACC scenario_names 정규화 오류")
    inputs = candidate.get("inputs")
    if not isinstance(inputs, list) or len(inputs) != len(REQUIRED_METRICS):
        raise CaseServiceError("WACC candidate inputs invalid / WACC candidate 입력 오류")
    by: dict[str, dict[str, Any]] = {}
    for item in inputs:
        validate_wacc_source_input(item)
        metric = item["metric"]
        if metric in by or item["unit"] != _metric_unit(metric, currency):
            raise CaseServiceError("WACC candidate metric/unit conflict / WACC candidate 지표·단위 충돌")
        by[metric] = item
    if list(by) != list(REQUIRED_METRICS):
        raise CaseServiceError("WACC candidate input order/coverage invalid / WACC candidate 입력순서·coverage 오류")

    rf=by[RISK_FREE_RATE]["value"]; erp=by[EQUITY_RISK_PREMIUM]["value"]; beta=by[LEVERED_BETA]["value"]
    rd=by[PRE_TAX_COST_OF_DEBT]["value"]; e=by[EQUITY_MARKET_VALUE]["value"]; d=by[DEBT_MARKET_VALUE]["value"]; tax=by[TAX_RATE]["value"]
    total=e+d
    cost_equity=rf+beta*erp; after_tax_debt=rd*(1-tax); we=e/total; wd=d/total
    wacc=we*cost_equity+wd*after_tax_debt
    expected_calc={"cost_of_equity":cost_equity,"after_tax_cost_of_debt":after_tax_debt,"weight_equity":we,"weight_debt":wd,"wacc":wacc}
    calc=candidate.get("calculation")
    if not isinstance(calc, dict) or any(abs(float(calc.get(k, float("nan")))-v)>1e-12 for k,v in expected_calc.items()):
        raise CaseServiceError("WACC candidate arithmetic mismatch / WACC candidate 계산 불일치")
    if abs((we+wd)-1.0)>1e-12:
        raise CaseServiceError("WACC weights do not sum to one / WACC 가중치 합 오류")
    if not 0 < wacc <= 0.99:
        raise CaseServiceError("WACC candidate final rate invalid / WACC candidate 최종금리 오류")
    freshness={metric:_freshness(item,as_of) for metric,item in by.items()}
    if candidate.get("freshness")!=freshness:
        raise CaseServiceError("WACC candidate freshness mismatch / WACC candidate 최신성 불일치")
    all_fresh=all(x["status"]=="FRESH" for x in freshness.values())
    all_tiers=all(item["source"]["tier"] in REVIEWABLE_TIERS for item in by.values())
    expected_ready={"all_required_inputs_present":True,"all_inputs_fresh":all_fresh,"all_source_tiers_reviewable":all_tiers,"eligible_for_human_review":all_fresh and all_tiers}
    if candidate.get("review_readiness")!=expected_ready:
        raise CaseServiceError("WACC candidate review readiness mismatch / WACC candidate 검토준비도 불일치")
    expected=_sha(_without(candidate,"candidate_sha256"))
    if candidate.get("candidate_sha256")!=expected:
        raise CaseServiceError("WACC candidate SHA-256 mismatch / WACC candidate SHA 불일치")
    return {"status":"PASS_WACC_CANDIDATE_VALIDATION","candidate_sha256":expected,"wacc":wacc,"eligible_for_human_review":all_fresh and all_tiers}


def build_wacc_review_assertion(
    candidate: dict[str, Any],
    *,
    reviewer: str,
    approved_at: str,
    review_basis: str,
) -> dict[str, Any]:
    checked=validate_wacc_candidate(candidate)
    if checked["eligible_for_human_review"] is not True:
        raise CaseServiceError("WACC candidate not eligible for human review / WACC candidate 인간검토 부적격")
    if not isinstance(reviewer,str) or not reviewer.strip() or len(reviewer)>160:
        raise CaseServiceError("WACC reviewer required / WACC reviewer 필요")
    timestamp=_timestamp(approved_at,"approved_at")
    if not isinstance(review_basis,str) or not review_basis.strip() or len(review_basis)>4000:
        raise CaseServiceError("WACC review_basis required / WACC review_basis 필요")
    assertion={
        "schema_version":REVIEW_SCHEMA,
        "status":REVIEW_STATUS,
        "canonical":False,
        "decision":"APPROVE_WACC_ASSUMPTION",
        "candidate_sha256":candidate["candidate_sha256"],
        "methodology_version":candidate["methodology_version"],
        "as_of":candidate["as_of"],
        "scenario_names":copy.deepcopy(candidate["scenario_names"]),
        "reviewer":reviewer.strip(),
        "approved_at":timestamp,
        "review_basis":review_basis.strip(),
        "assertion_sha256":"",
    }
    assertion["assertion_sha256"]=_sha(_without(assertion,"assertion_sha256"))
    validate_wacc_review_assertion(assertion,candidate)
    return assertion


def validate_wacc_review_assertion(assertion:dict[str,Any],candidate:dict[str,Any])->dict[str,Any]:
    checked=validate_wacc_candidate(candidate)
    if checked["eligible_for_human_review"] is not True:
        raise CaseServiceError("review assertion cannot approve ineligible WACC candidate / 부적격 WACC candidate 승인 불가")
    if not isinstance(assertion,dict) or assertion.get("schema_version")!=REVIEW_SCHEMA or assertion.get("status")!=REVIEW_STATUS or assertion.get("canonical") is not False or assertion.get("decision")!="APPROVE_WACC_ASSUMPTION":
        raise CaseServiceError("WACC review assertion schema/status invalid / WACC 검토승인 스키마·상태 오류")
    if assertion.get("candidate_sha256")!=candidate.get("candidate_sha256") or assertion.get("methodology_version")!=candidate.get("methodology_version") or assertion.get("as_of")!=candidate.get("as_of") or assertion.get("scenario_names")!=candidate.get("scenario_names"):
        raise CaseServiceError("WACC review assertion candidate lineage mismatch / WACC 검토승인 candidate lineage 불일치")
    if not isinstance(assertion.get("reviewer"),str) or not assertion["reviewer"].strip() or not isinstance(assertion.get("review_basis"),str) or not assertion["review_basis"].strip():
        raise CaseServiceError("WACC review assertion reviewer/basis invalid / WACC 검토승인 reviewer·basis 오류")
    _timestamp(assertion.get("approved_at"),"approved_at")
    expected=_sha(_without(assertion,"assertion_sha256"))
    if assertion.get("assertion_sha256")!=expected:
        raise CaseServiceError("WACC review assertion SHA-256 mismatch / WACC 검토승인 SHA 불일치")
    return {"status":"PASS_WACC_REVIEW_ASSERTION_VALIDATION","assertion_sha256":expected}


def finalize_reviewed_wacc(candidate:dict[str,Any],assertion:dict[str,Any])->dict[str,Any]:
    validate_wacc_candidate(candidate);validate_wacc_review_assertion(assertion,candidate)
    package={
        "schema_version":PACKAGE_SCHEMA,
        "status":PACKAGE_STATUS,
        "canonical":False,
        "class":"ASSUMPTION",
        "methodology_version":candidate["methodology_version"],
        "entity":copy.deepcopy(candidate["entity"]),
        "capital_currency":candidate["capital_currency"],
        "as_of":candidate["as_of"],
        "scenario_names":copy.deepcopy(candidate["scenario_names"]),
        "wacc":candidate["calculation"]["wacc"],
        "candidate":copy.deepcopy(candidate),
        "review_assertion":copy.deepcopy(assertion),
        "binding_eligibility":{"eligible":True,"reason":"REVIEWED_WACC_ASSUMPTION"},
        "package_sha256":"",
    }
    package["package_sha256"]=_sha(_without(package,"package_sha256"))
    validate_reviewed_wacc(package)
    return package


def validate_reviewed_wacc(package:dict[str,Any])->dict[str,Any]:
    if not isinstance(package,dict) or package.get("schema_version")!=PACKAGE_SCHEMA or package.get("status")!=PACKAGE_STATUS or package.get("canonical") is not False or package.get("class")!="ASSUMPTION":
        raise CaseServiceError("reviewed WACC package schema/status/authority invalid / 검토완료 WACC 패키지 스키마·상태·권위 오류")
    candidate=package.get("candidate");assertion=package.get("review_assertion")
    if not isinstance(candidate,dict) or not isinstance(assertion,dict):
        raise CaseServiceError("reviewed WACC nested candidate/assertion missing / 검토완료 WACC 중첩객체 누락")
    checked=validate_wacc_candidate(candidate);validate_wacc_review_assertion(assertion,candidate)
    if checked["eligible_for_human_review"] is not True:
        raise CaseServiceError("reviewed WACC candidate no longer eligible / 검토완료 WACC candidate 부적격")
    expected_projection={
        "methodology_version":candidate["methodology_version"],"entity":candidate["entity"],"capital_currency":candidate["capital_currency"],
        "as_of":candidate["as_of"],"scenario_names":candidate["scenario_names"],"wacc":candidate["calculation"]["wacc"],
    }
    for key,val in expected_projection.items():
        if package.get(key)!=val:
            raise CaseServiceError("reviewed WACC projection mismatch / 검토완료 WACC 투영 불일치")
    if package.get("binding_eligibility")!={"eligible":True,"reason":"REVIEWED_WACC_ASSUMPTION"}:
        raise CaseServiceError("reviewed WACC binding eligibility invalid / 검토완료 WACC 바인딩 적격성 오류")
    expected=_sha(_without(package,"package_sha256"))
    if package.get("package_sha256")!=expected:
        raise CaseServiceError("reviewed WACC package SHA-256 mismatch / 검토완료 WACC 패키지 SHA 불일치")
    return {"status":"PASS_REVIEWED_WACC_VALIDATION","package_sha256":expected,"wacc":package["wacc"],"scenario_names":copy.deepcopy(package["scenario_names"]),"eligible":True}
