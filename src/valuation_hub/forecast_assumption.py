"""M26 governed integrated FCFF forecast-scenario assumptions.

Forecasts remain valuation assumptions. Historical facts or deterministic FCFF
calculations may inform review but never create forecast authority automatically.
"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import date, datetime
from math import isfinite
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.core import FcFFInputs, fcff, nopat

CANDIDATE_SCHEMA = "forecast-scenario-assumption-candidate-v0.1"
CANDIDATE_STATUS = "FORECAST_SCENARIO_ASSUMPTION_CANDIDATE"
REVIEW_SCHEMA = "forecast-scenario-review-assertion-v0.1"
REVIEW_STATUS = "FORECAST_SCENARIO_REVIEW_APPROVED"
PACKAGE_SCHEMA = "reviewed-forecast-scenario-assumption-v0.1"
PACKAGE_STATUS = "FORECAST_SCENARIO_ASSUMPTION_REVIEWED"
METHODOLOGY_VERSION = "integrated-fcff-forecast-v0.1"
MAX_SCENARIOS = 12
MAX_FORECAST_YEARS = 30
FORECAST_COMPONENTS = (
    "revenue",
    "ebit_margin",
    "tax_rate",
    "depreciation_amortization",
    "capex",
    "delta_nwc",
)


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


def _entity(entity_id: Any, financial_scope: Any) -> dict[str, str]:
    if not isinstance(entity_id, str) or not entity_id.strip() or not isinstance(financial_scope, str) or not financial_scope.strip():
        raise CaseServiceError("forecast entity/scope required / Forecast entity·scope 필요")
    return {"id": entity_id.strip(), "financial_scope": financial_scope.strip()}


def _currency(value: Any) -> str:
    if not isinstance(value, str) or not 3 <= len(value.strip()) <= 8:
        raise CaseServiceError("forecast capital currency invalid / Forecast 자본통화 오류")
    return value.strip().upper()


def _normalize_row(raw: Any, as_of_year: int, label: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise CaseServiceError(f"{label} forecast row object required / {label} Forecast 행 객체 필요")
    year = raw.get("year")
    if isinstance(year, bool) or not isinstance(year, int) or year <= as_of_year:
        raise CaseServiceError(f"{label} forecast year must be after valuation year / {label} Forecast 연도는 가치평가 연도 이후여야 함")
    revenue = _finite(raw.get("revenue"), f"{label}.{year}.revenue")
    margin = _finite(raw.get("ebit_margin"), f"{label}.{year}.ebit_margin")
    tax = _finite(raw.get("tax_rate"), f"{label}.{year}.tax_rate")
    da = _finite(raw.get("depreciation_amortization"), f"{label}.{year}.depreciation_amortization")
    capex = _finite(raw.get("capex"), f"{label}.{year}.capex")
    delta_nwc = _finite(raw.get("delta_nwc"), f"{label}.{year}.delta_nwc")
    if revenue < 0:
        raise CaseServiceError("forecast revenue must be non-negative / Forecast 매출은 0 이상이어야 함")
    if not -1 <= margin <= 1:
        raise CaseServiceError("forecast EBIT margin must be in [-1,1] / Forecast EBIT margin 범위 오류")
    if not 0 <= tax < 1:
        raise CaseServiceError("forecast tax rate must be in [0,1) / Forecast 세율 범위 오류")
    if da < 0 or capex < 0:
        raise CaseServiceError("forecast D&A/CAPEX must be non-negative / Forecast D&A·CAPEX는 0 이상이어야 함")
    return {
        "year": year,
        "revenue": revenue,
        "ebit_margin": margin,
        "tax_rate": tax,
        "depreciation_amortization": da,
        "capex": capex,
        "delta_nwc": delta_nwc,
    }


def _normalize_scenarios(value: Any, as_of_year: int) -> tuple[list[dict[str, Any]], list[str], list[int]]:
    if not isinstance(value, list) or not 1 <= len(value) <= MAX_SCENARIOS:
        raise CaseServiceError("forecast scenarios must contain 1..12 entries / Forecast 시나리오 1..12개 필요")
    by_name: dict[str, dict[str, Any]] = {}
    shared_years: list[int] | None = None
    for raw in value:
        if not isinstance(raw, dict):
            raise CaseServiceError("forecast scenario object required / Forecast 시나리오 객체 필요")
        name = str(raw.get("scenario_name", "")).strip().upper()
        rationale = raw.get("rationale")
        rows = raw.get("years")
        if not name or len(name) > 80 or name in by_name:
            raise CaseServiceError("forecast scenario names must be unique / Forecast 시나리오 이름은 고유해야 함")
        if not isinstance(rationale, str) or not rationale.strip() or len(rationale) > 8000:
            raise CaseServiceError("forecast scenario rationale required / Forecast 시나리오 rationale 필요")
        if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_FORECAST_YEARS:
            raise CaseServiceError("forecast scenario years must contain 1..30 rows / Forecast 연도행 1..30개 필요")
        normalized_rows = [_normalize_row(row, as_of_year, name) for row in rows]
        years = [row["year"] for row in normalized_rows]
        if years != sorted(years) or len(years) != len(set(years)):
            raise CaseServiceError("forecast years must be unique and ascending / Forecast 연도는 고유 오름차순이어야 함")
        if shared_years is None:
            shared_years = years
        elif years != shared_years:
            raise CaseServiceError("all scenarios must use identical forecast-year set / 모든 시나리오는 동일 Forecast 연도집합 필요")
        by_name[name] = {"scenario_name": name, "rationale": rationale.strip(), "years": normalized_rows}
    names = sorted(by_name)
    assert shared_years is not None
    return [by_name[name] for name in names], names, shared_years


def _diagnostics(scenarios: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for scenario in scenarios:
        rows: list[dict[str, Any]] = []
        previous_revenue: float | None = None
        for row in scenario["years"]:
            ebit = row["revenue"] * row["ebit_margin"]
            nopat_value = nopat(ebit, row["tax_rate"])
            fcff_value = fcff(FcFFInputs(
                ebit=ebit,
                tax_rate=row["tax_rate"],
                depreciation_amortization=row["depreciation_amortization"],
                capex=row["capex"],
                delta_nwc=row["delta_nwc"],
            ))
            growth = None
            if previous_revenue is not None:
                growth = None if previous_revenue == 0 else (row["revenue"] / previous_revenue) - 1
            rows.append({
                "year": row["year"],
                "ebit": ebit,
                "nopat": nopat_value,
                "fcff": fcff_value,
                "revenue_growth": growth,
            })
            previous_revenue = row["revenue"]
        result[scenario["scenario_name"]] = rows
    return result


def build_forecast_candidate(
    scenarios: list[dict[str, Any]],
    *,
    entity_id: str,
    financial_scope: str,
    capital_currency: str,
    as_of: str,
) -> dict[str, Any]:
    as_of_date = _canonical_date(as_of, "as_of")
    normalized, names, years = _normalize_scenarios(scenarios, as_of_date.year)
    result = {
        "schema_version": CANDIDATE_SCHEMA,
        "status": CANDIDATE_STATUS,
        "canonical": False,
        "class": "ASSUMPTION_CANDIDATE",
        "methodology_version": METHODOLOGY_VERSION,
        "entity": _entity(entity_id, financial_scope),
        "capital_currency": _currency(capital_currency),
        "as_of": as_of,
        "scenario_names": names,
        "forecast_years": years,
        "scenarios": normalized,
        "diagnostics": _diagnostics(normalized),
        "review_readiness": {
            "complete_scenario_set": True,
            "common_forecast_year_set": True,
            "all_rows_complete": True,
            "eligible_for_human_review": True,
        },
        "forecast_block_sha256": _sha(normalized),
        "candidate_sha256": "",
    }
    result["candidate_sha256"] = _sha(_without(result, "candidate_sha256"))
    validate_forecast_candidate(result)
    return result


def validate_forecast_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    if (
        not isinstance(candidate, dict)
        or candidate.get("schema_version") != CANDIDATE_SCHEMA
        or candidate.get("status") != CANDIDATE_STATUS
        or candidate.get("canonical") is not False
        or candidate.get("class") != "ASSUMPTION_CANDIDATE"
        or candidate.get("methodology_version") != METHODOLOGY_VERSION
    ):
        raise CaseServiceError("forecast candidate schema/status/authority invalid / Forecast candidate 스키마·상태·권위 오류")
    entity = candidate.get("entity")
    if not isinstance(entity, dict) or entity != _entity(entity.get("id"), entity.get("financial_scope")):
        raise CaseServiceError("forecast candidate entity invalid / Forecast candidate entity 오류")
    currency = _currency(candidate.get("capital_currency"))
    if candidate.get("capital_currency") != currency:
        raise CaseServiceError("forecast currency must be canonical uppercase / Forecast 통화 정규화 오류")
    as_of_date = _canonical_date(candidate.get("as_of"), "as_of")
    normalized, names, years = _normalize_scenarios(candidate.get("scenarios"), as_of_date.year)
    if candidate.get("scenarios") != normalized or candidate.get("scenario_names") != names or candidate.get("forecast_years") != years:
        raise CaseServiceError("forecast scenario/year canonicalization mismatch / Forecast 시나리오·연도 정규화 불일치")
    diagnostics = _diagnostics(normalized)
    if candidate.get("diagnostics") != diagnostics:
        raise CaseServiceError("forecast diagnostics mismatch / Forecast diagnostics 불일치")
    readiness = {
        "complete_scenario_set": True,
        "common_forecast_year_set": True,
        "all_rows_complete": True,
        "eligible_for_human_review": True,
    }
    if candidate.get("review_readiness") != readiness:
        raise CaseServiceError("forecast review readiness mismatch / Forecast 검토준비도 불일치")
    block_sha = _sha(normalized)
    if candidate.get("forecast_block_sha256") != block_sha:
        raise CaseServiceError("forecast block SHA mismatch / Forecast block SHA 불일치")
    expected = _sha(_without(candidate, "candidate_sha256"))
    if candidate.get("candidate_sha256") != expected:
        raise CaseServiceError("forecast candidate SHA mismatch / Forecast candidate SHA 불일치")
    return {
        "status": "PASS_FORECAST_CANDIDATE_VALIDATION",
        "candidate_sha256": expected,
        "forecast_block_sha256": block_sha,
        "scenario_names": copy.deepcopy(names),
        "forecast_years": copy.deepcopy(years),
        "eligible_for_human_review": True,
    }


def build_forecast_review_assertion(
    candidate: dict[str, Any],
    *,
    reviewer: str,
    approved_at: str,
    review_basis: str,
) -> dict[str, Any]:
    validate_forecast_candidate(candidate)
    if not isinstance(reviewer, str) or not reviewer.strip() or len(reviewer) > 160:
        raise CaseServiceError("forecast reviewer required / Forecast reviewer 필요")
    timestamp = _timestamp(approved_at, "approved_at")
    if datetime.fromisoformat(timestamp).date() < _canonical_date(candidate["as_of"], "as_of"):
        raise CaseServiceError("forecast approval cannot predate valuation as_of / Forecast 승인이 가치평가 as_of보다 앞설 수 없음")
    if not isinstance(review_basis, str) or not review_basis.strip() or len(review_basis) > 8000:
        raise CaseServiceError("forecast review_basis required / Forecast review_basis 필요")
    result = {
        "schema_version": REVIEW_SCHEMA,
        "status": REVIEW_STATUS,
        "canonical": False,
        "decision": "APPROVE_FORECAST_SCENARIO_ASSUMPTION",
        "candidate_sha256": candidate["candidate_sha256"],
        "forecast_block_sha256": candidate["forecast_block_sha256"],
        "methodology_version": candidate["methodology_version"],
        "entity": copy.deepcopy(candidate["entity"]),
        "capital_currency": candidate["capital_currency"],
        "as_of": candidate["as_of"],
        "scenario_names": copy.deepcopy(candidate["scenario_names"]),
        "forecast_years": copy.deepcopy(candidate["forecast_years"]),
        "reviewer": reviewer.strip(),
        "approved_at": timestamp,
        "review_basis": review_basis.strip(),
        "assertion_sha256": "",
    }
    result["assertion_sha256"] = _sha(_without(result, "assertion_sha256"))
    validate_forecast_review_assertion(result, candidate)
    return result


def validate_forecast_review_assertion(assertion: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    validate_forecast_candidate(candidate)
    if (
        not isinstance(assertion, dict)
        or assertion.get("schema_version") != REVIEW_SCHEMA
        or assertion.get("status") != REVIEW_STATUS
        or assertion.get("canonical") is not False
        or assertion.get("decision") != "APPROVE_FORECAST_SCENARIO_ASSUMPTION"
    ):
        raise CaseServiceError("forecast review assertion schema/status invalid / Forecast 검토승인 스키마·상태 오류")
    projection = {
        "candidate_sha256": candidate["candidate_sha256"],
        "forecast_block_sha256": candidate["forecast_block_sha256"],
        "methodology_version": candidate["methodology_version"],
        "entity": candidate["entity"],
        "capital_currency": candidate["capital_currency"],
        "as_of": candidate["as_of"],
        "scenario_names": candidate["scenario_names"],
        "forecast_years": candidate["forecast_years"],
    }
    for field, expected_value in projection.items():
        if assertion.get(field) != expected_value:
            raise CaseServiceError("forecast review candidate lineage mismatch / Forecast 검토 candidate lineage 불일치")
    if not isinstance(assertion.get("reviewer"), str) or not assertion["reviewer"].strip() or not isinstance(assertion.get("review_basis"), str) or not assertion["review_basis"].strip():
        raise CaseServiceError("forecast review reviewer/basis invalid / Forecast 검토 reviewer·basis 오류")
    timestamp = _timestamp(assertion.get("approved_at"), "approved_at")
    if datetime.fromisoformat(timestamp).date() < _canonical_date(candidate["as_of"], "as_of"):
        raise CaseServiceError("forecast approval predates valuation as_of / Forecast 승인이 가치평가 as_of보다 앞섬")
    expected = _sha(_without(assertion, "assertion_sha256"))
    if assertion.get("assertion_sha256") != expected:
        raise CaseServiceError("forecast review assertion SHA mismatch / Forecast 검토승인 SHA 불일치")
    return {"status": "PASS_FORECAST_REVIEW_ASSERTION_VALIDATION", "assertion_sha256": expected}


def finalize_reviewed_forecast(candidate: dict[str, Any], assertion: dict[str, Any]) -> dict[str, Any]:
    validate_forecast_candidate(candidate)
    validate_forecast_review_assertion(assertion, candidate)
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
        "forecast_years": copy.deepcopy(candidate["forecast_years"]),
        "scenarios": copy.deepcopy(candidate["scenarios"]),
        "forecast_block_sha256": candidate["forecast_block_sha256"],
        "candidate": copy.deepcopy(candidate),
        "review_assertion": copy.deepcopy(assertion),
        "binding_eligibility": {"eligible": True, "reason": "REVIEWED_INTEGRATED_FORECAST_ASSUMPTION"},
        "package_sha256": "",
    }
    result["package_sha256"] = _sha(_without(result, "package_sha256"))
    validate_reviewed_forecast(result)
    return result


def validate_reviewed_forecast(package: dict[str, Any]) -> dict[str, Any]:
    if (
        not isinstance(package, dict)
        or package.get("schema_version") != PACKAGE_SCHEMA
        or package.get("status") != PACKAGE_STATUS
        or package.get("canonical") is not False
        or package.get("class") != "ASSUMPTION"
    ):
        raise CaseServiceError("reviewed forecast package schema/status/authority invalid / 검토완료 Forecast 패키지 스키마·상태·권위 오류")
    candidate = package.get("candidate")
    assertion = package.get("review_assertion")
    if not isinstance(candidate, dict) or not isinstance(assertion, dict):
        raise CaseServiceError("reviewed forecast nested candidate/assertion missing / 검토완료 Forecast 중첩객체 누락")
    validate_forecast_candidate(candidate)
    validate_forecast_review_assertion(assertion, candidate)
    projection = {
        "methodology_version": candidate["methodology_version"],
        "entity": candidate["entity"],
        "capital_currency": candidate["capital_currency"],
        "as_of": candidate["as_of"],
        "scenario_names": candidate["scenario_names"],
        "forecast_years": candidate["forecast_years"],
        "scenarios": candidate["scenarios"],
        "forecast_block_sha256": candidate["forecast_block_sha256"],
    }
    for field, expected_value in projection.items():
        if package.get(field) != expected_value:
            raise CaseServiceError("reviewed forecast projection mismatch / 검토완료 Forecast 투영 불일치")
    if package.get("binding_eligibility") != {"eligible": True, "reason": "REVIEWED_INTEGRATED_FORECAST_ASSUMPTION"}:
        raise CaseServiceError("reviewed forecast binding eligibility invalid / 검토완료 Forecast 바인딩 적격성 오류")
    expected = _sha(_without(package, "package_sha256"))
    if package.get("package_sha256") != expected:
        raise CaseServiceError("reviewed forecast package SHA mismatch / 검토완료 Forecast 패키지 SHA 불일치")
    return {
        "status": "PASS_REVIEWED_FORECAST_VALIDATION",
        "package_sha256": expected,
        "scenario_names": copy.deepcopy(package["scenario_names"]),
        "forecast_years": copy.deepcopy(package["forecast_years"]),
        "eligible": True,
    }
