"""Financial evidence normalization / 재무근거 정규화.

SEC/OpenDART evidence becomes period-aware observations and reproducible TTM
transforms. Arithmetic never upgrades evidence authority.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import date
from typing import Any, Iterable
from urllib.parse import urlparse

from valuation_hub.case_service import CaseServiceError

OBSERVATION_SCHEMA_VERSION = "financial-observation-v0.1"
TTM_SCHEMA_VERSION = "financial-ttm-v0.1"
OBSERVATION_STATUS = "FINANCIAL_OBSERVATION_NORMALIZED"
TTM_STATUS = "FINANCIAL_TTM_NORMALIZED"
INSTANT = "INSTANT"
DURATION_QUARTER = "DURATION_QUARTER"
DURATION_YTD = "DURATION_YTD"
DURATION_ANNUAL = "DURATION_ANNUAL"
DURATION_TTM = "DURATION_TTM"
UNKNOWN_PERIOD = "UNKNOWN_PERIOD"
PERIOD_KINDS = {INSTANT, DURATION_QUARTER, DURATION_YTD, DURATION_ANNUAL, DURATION_TTM, UNKNOWN_PERIOD}
INSTANT_METRICS = {"assets", "cash", "equity", "liabilities", "shares_outstanding"}
DURATION_METRICS = {"revenue", "operating_income", "net_income"}
DART_STAGE = {"11013": ("Q1", 1), "11012": ("H1", 2), "11014": ("Q3", 3), "11011": ("FY", 4)}
CIK_PATH_RE = re.compile(r"/CIK([0-9]{10})\.json$")


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result.pop(key, None)
    return result


def _num(value: Any, field: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CaseServiceError(f"{field} must be numeric / {field} 숫자 필요")
    return value


def _iso(value: Any, field: str, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise CaseServiceError(f"{field} must be ISO date / {field} ISO 날짜 필요")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise CaseServiceError(f"{field} invalid / {field} 오류") from exc
    if parsed.isoformat() != value:
        raise CaseServiceError(f"{field} must be YYYY-MM-DD / {field} 정규형식 오류")
    return value


def _days(start: str, end: str) -> int:
    days = (date.fromisoformat(end) - date.fromisoformat(start)).days + 1
    if days <= 0:
        raise CaseServiceError("duration start/end invalid / 기간 시작·종료 오류")
    return days


def _source_class(value: Any) -> str:
    if value == "FACT":
        return "NORMALIZED_FACT"
    if value == "FACT_CANDIDATE":
        return "NORMALIZED_FACT_CANDIDATE"
    raise CaseServiceError("normalization requires FACT or FACT_CANDIDATE / 정규화는 FACT 또는 FACT_CANDIDATE 필요")


def _derived_class(values: Iterable[str]) -> str:
    classes = list(values)
    if not classes or any(v not in {"NORMALIZED_FACT", "NORMALIZED_FACT_CANDIDATE"} for v in classes):
        raise CaseServiceError("TTM requires normalized fact inputs / TTM 정규화 fact 입력 필요")
    return "NORMALIZED_FACT" if all(v == "NORMALIZED_FACT" for v in classes) else "NORMALIZED_FACT_CANDIDATE"


def _dart_amount(raw: Any, field: str) -> int | None:
    if raw is None:
        return None
    if isinstance(raw, bool):
        raise CaseServiceError(f"{field} invalid / {field} 오류")
    if isinstance(raw, int):
        return raw
    if not isinstance(raw, str):
        raise CaseServiceError(f"{field} must be integer text / {field} 정수문자열 필요")
    text = raw.strip()
    if text in {"", "-"}:
        return None
    paren = text.startswith("(") and text.endswith(")")
    if paren:
        text = text[1:-1].strip()
    compact = text.replace(",", "")
    if not re.fullmatch(r"[-+]?[0-9]+", compact):
        raise CaseServiceError(f"{field} malformed / {field} 숫자형식 오류")
    value = int(compact)
    return -abs(value) if paren else value


def _finish_observation(value: dict[str, Any]) -> dict[str, Any]:
    value["observation_sha256"] = _sha(_without(value, "observation_sha256"))
    validate_financial_observation(value)
    return value


def normalize_sec_candidate(candidate: dict[str, Any], *, declared_period_kind: str | None = None) -> dict[str, Any]:
    if not isinstance(candidate, dict) or candidate.get("schema_version") != "sec-evidence-candidate-v0.1" or candidate.get("canonical") is not False:
        raise CaseServiceError("noncanonical SEC evidence candidate v0.1 required / 비정식 SEC evidence candidate v0.1 필요")
    metric = candidate.get("metric")
    if metric not in INSTANT_METRICS | DURATION_METRICS:
        raise CaseServiceError(f"unsupported metric / 미지원 지표: {metric}")
    source, period, filing = candidate.get("source"), candidate.get("period"), candidate.get("filing")
    if not all(isinstance(x, dict) for x in (source, period, filing)):
        raise CaseServiceError("SEC provenance incomplete / SEC 출처정보 불완전")
    locator = source.get("locator")
    match = CIK_PATH_RE.search(urlparse(locator).path) if isinstance(locator, str) else None
    if not match:
        raise CaseServiceError("SEC CIK unavailable from locator / SEC locator에서 CIK 확인 불가")
    end = _iso(period.get("end"), "SEC period.end")
    start = _iso(period.get("start"), "SEC period.start", True)
    form = filing.get("form")
    duration: int | None = None
    fq: int | None = None
    if metric in INSTANT_METRICS:
        if start is not None:
            raise CaseServiceError("instant SEC metric cannot have start / SEC instant 지표 시작일 불가")
        kind = INSTANT
    else:
        if start is None:
            raise CaseServiceError("duration SEC metric requires start / SEC duration 지표 시작일 필요")
        duration = _days(start, end)
        if form in {"10-K", "10-K/A"}:
            if not 330 <= duration <= 400 or declared_period_kind not in {None, DURATION_ANNUAL}:
                raise CaseServiceError("SEC 10-K annual semantics invalid / SEC 10-K 연간 의미 오류")
            kind, fq = DURATION_ANNUAL, 4
        elif form in {"10-Q", "10-Q/A"}:
            if declared_period_kind not in {DURATION_QUARTER, DURATION_YTD}:
                raise CaseServiceError("SEC 10-Q requires explicit DURATION_QUARTER or DURATION_YTD / SEC 10-Q 기간종류 명시 필요")
            fq = {"Q1": 1, "Q2": 2, "Q3": 3}.get(str(period.get("fp")))
            if fq is None:
                raise CaseServiceError("SEC 10-Q fp must be Q1/Q2/Q3 / SEC 10-Q fp 오류")
            if declared_period_kind == DURATION_QUARTER and not 60 <= duration <= 120:
                raise CaseServiceError("SEC quarter duration outside safe range / SEC 분기 기간범위 오류")
            lo, hi = {1: (60, 120), 2: (140, 220), 3: (230, 320)}[fq]
            if declared_period_kind == DURATION_YTD and not lo <= duration <= hi:
                raise CaseServiceError("SEC YTD duration outside safe range / SEC 누적 기간범위 오류")
            kind = declared_period_kind
        else:
            raise CaseServiceError(f"unsupported SEC form / 미지원 SEC form: {form}")
    unit = candidate.get("unit")
    if not isinstance(unit, str) or not unit:
        raise CaseServiceError("SEC unit missing / SEC unit 누락")
    result = {
        "schema_version": OBSERVATION_SCHEMA_VERSION, "status": OBSERVATION_STATUS, "canonical": False,
        "class": _source_class(candidate.get("class")), "metric": metric, "value": _num(candidate.get("value"), "SEC value"), "unit": unit,
        "entity": {"id": f"SEC_CIK:{match.group(1)}", "source_system": "SEC", "financial_scope": "AS_REPORTED"},
        "period": {"kind": kind, "start": start, "end": end, "duration_days": duration, "fiscal_year": period.get("fy"), "fiscal_period": period.get("fp"), "fiscal_quarter": fq, "report_stage": period.get("fp"), "date_precision": "EXACT"},
        "lineage": {"normalization_rule": "SEC_PERIOD_CLASSIFICATION_V01", "source_candidate_sha256": _sha(candidate), "source_class": candidate.get("class"), "source_snapshot_sha256": source.get("snapshot_sha256"), "source_body_sha256": source.get("body_sha256"), "filing_identity": copy.deepcopy(filing), "source_detail": {"taxonomy": candidate.get("taxonomy"), "concept": candidate.get("concept"), "frame": period.get("frame")}},
        "observation_sha256": "",
    }
    return _finish_observation(result)


def normalize_dart_candidate(candidate: dict[str, Any], *, amount_basis: str = "CURRENT") -> dict[str, Any]:
    if not isinstance(candidate, dict) or candidate.get("schema_version") != "dart-evidence-candidate-v0.1" or candidate.get("canonical") is not False:
        raise CaseServiceError("noncanonical OpenDART evidence candidate v0.1 required / 비정식 OpenDART evidence candidate v0.1 필요")
    metric = candidate.get("metric")
    if metric not in INSTANT_METRICS | DURATION_METRICS:
        raise CaseServiceError(f"unsupported metric / 미지원 지표: {metric}")
    request, row, source = candidate.get("request_identity"), candidate.get("row"), candidate.get("source")
    if not all(isinstance(x, dict) for x in (request, row, source)):
        raise CaseServiceError("OpenDART provenance incomplete / OpenDART 출처정보 불완전")
    corp, year, report, scope = request.get("corp_code"), request.get("bsns_year"), request.get("reprt_code"), request.get("fs_div")
    if not all(isinstance(x, str) and x for x in (corp, year, report, scope)) or report not in DART_STAGE:
        raise CaseServiceError("OpenDART request identity invalid / OpenDART 요청식별 오류")
    stage, quarter = DART_STAGE[report]
    section = candidate.get("statement_section")
    basis = amount_basis.upper()
    if basis not in {"CURRENT", "CUMULATIVE"}:
        raise CaseServiceError("OpenDART amount_basis invalid / OpenDART amount_basis 오류")
    if metric in INSTANT_METRICS:
        if section != "BS" or basis != "CURRENT":
            raise CaseServiceError("OpenDART instant metric requires BS current amount / OpenDART instant 지표는 BS 당기금액 필요")
        kind, value, fq = INSTANT, _num(candidate.get("value"), "OpenDART value"), quarter
    else:
        if section not in {"IS", "CIS"}:
            raise CaseServiceError("OpenDART duration metric requires IS/CIS / OpenDART duration 지표는 IS/CIS 필요")
        if report == "11011":
            if basis != "CURRENT":
                raise CaseServiceError("OpenDART annual duration uses current amount / OpenDART 연간값은 당기금액 사용")
            kind, value, fq = DURATION_ANNUAL, _num(candidate.get("value"), "OpenDART value"), 4
        elif basis == "CURRENT":
            kind, value, fq = DURATION_QUARTER, _num(candidate.get("value"), "OpenDART value"), quarter
        else:
            value = _dart_amount(row.get("thstrm_add_amount"), "thstrm_add_amount")
            if value is None:
                raise CaseServiceError("OpenDART cumulative amount unavailable / OpenDART 누적금액 없음")
            kind, fq = DURATION_YTD, quarter
    unit = candidate.get("unit")
    if not isinstance(unit, str) or not unit:
        raise CaseServiceError("OpenDART unit missing / OpenDART unit 누락")
    result = {
        "schema_version": OBSERVATION_SCHEMA_VERSION, "status": OBSERVATION_STATUS, "canonical": False,
        "class": _source_class(candidate.get("class")), "metric": metric, "value": value, "unit": unit,
        "entity": {"id": f"DART_CORP:{corp}", "source_system": "OPENDART", "financial_scope": scope},
        "period": {"kind": kind, "start": None, "end": None, "duration_days": None, "fiscal_year": int(year), "fiscal_period": stage, "fiscal_quarter": fq, "report_stage": stage, "date_precision": "REPORT_STAGE_ONLY"},
        "lineage": {"normalization_rule": "OPENDART_PERIOD_SEMANTICS_V01", "source_candidate_sha256": _sha(candidate), "source_class": candidate.get("class"), "source_snapshot_sha256": source.get("snapshot_sha256"), "source_body_sha256": source.get("body_sha256"), "filing_identity": {"rcept_no": row.get("rcept_no"), "reprt_code": report, "bsns_year": year}, "source_detail": {"statement_section": section, "account_id": row.get("account_id"), "account_nm": row.get("account_nm"), "amount_basis": basis, "raw_current": row.get("thstrm_amount"), "raw_cumulative": row.get("thstrm_add_amount")}},
        "observation_sha256": "",
    }
    return _finish_observation(result)


def validate_financial_observation(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema_version") != OBSERVATION_SCHEMA_VERSION or value.get("status") != OBSERVATION_STATUS:
        raise CaseServiceError("financial observation schema/status invalid / 재무 observation 스키마·상태 오류")
    if value.get("canonical") is not False or value.get("class") not in {"NORMALIZED_FACT", "NORMALIZED_FACT_CANDIDATE"}:
        raise CaseServiceError("financial observation authority invalid / 재무 observation 권위 오류")
    if value.get("metric") not in INSTANT_METRICS | DURATION_METRICS:
        raise CaseServiceError("financial observation metric invalid / 재무 observation 지표 오류")
    _num(value.get("value"), "observation value")
    if not isinstance(value.get("unit"), str) or not value["unit"]:
        raise CaseServiceError("financial observation unit missing / 재무 observation unit 누락")
    entity, period, lineage = value.get("entity"), value.get("period"), value.get("lineage")
    if not isinstance(entity, dict) or not isinstance(entity.get("id"), str) or not isinstance(entity.get("financial_scope"), str):
        raise CaseServiceError("financial observation entity invalid / 재무 observation entity 오류")
    if not isinstance(period, dict) or period.get("kind") not in PERIOD_KINDS:
        raise CaseServiceError("financial observation period invalid / 재무 observation 기간 오류")
    if not isinstance(lineage, dict) or not isinstance(lineage.get("normalization_rule"), str):
        raise CaseServiceError("financial observation lineage invalid / 재무 observation lineage 오류")
    expected = _sha(_without(value, "observation_sha256"))
    if value.get("observation_sha256") != expected:
        raise CaseServiceError("financial observation SHA-256 mismatch / 재무 observation SHA-256 불일치")
    return {"status": "PASS_FINANCIAL_OBSERVATION_VALIDATION", "canonical": False, "class": value["class"], "metric": value["metric"], "period_kind": period["kind"], "observation_sha256": expected}


def _compat(value: dict[str, Any]) -> tuple[str, str, str, str]:
    validate_financial_observation(value)
    return value["metric"], value["entity"]["id"], value["entity"]["financial_scope"], value["unit"]


def _finish_ttm(value: dict[str, Any]) -> dict[str, Any]:
    value["ttm_sha256"] = _sha(_without(value, "ttm_sha256"))
    validate_ttm_result(value)
    return value


def ttm_four_quarters(observations: list[dict[str, Any]]) -> dict[str, Any]:
    if len(observations) != 4:
        raise CaseServiceError("four-quarter TTM requires 4 observations / 4분기 TTM은 4개 observation 필요")
    keys = {_compat(x) for x in observations}
    if len(keys) != 1 or any(x["period"]["kind"] != DURATION_QUARTER for x in observations):
        raise CaseServiceError("quarter TTM metric/entity/scope/unit/period mismatch / 분기 TTM 입력 호환성 오류")
    seq: list[tuple[int, int, dict[str, Any]]] = []
    for item in observations:
        fy, fq = item["period"].get("fiscal_year"), item["period"].get("fiscal_quarter")
        if isinstance(fy, bool) or not isinstance(fy, int) or isinstance(fq, bool) or not isinstance(fq, int) or fq not in {1,2,3,4}:
            raise CaseServiceError("quarter TTM requires fiscal year/quarter / 분기 TTM 회계연도·분기 필요")
        seq.append((fy, fq, item))
    seq.sort(key=lambda x: (x[0], x[1]))
    indexes = [fy * 4 + fq for fy, fq, _ in seq]
    if len(set(indexes)) != 4 or any(b-a != 1 for a,b in zip(indexes, indexes[1:])):
        raise CaseServiceError("quarter TTM duplicate/gap / 분기 TTM 중복·공백")
    ordered = [x for _,_,x in seq]
    metric, entity, scope, unit = next(iter(keys))
    result = {"schema_version": TTM_SCHEMA_VERSION, "status": TTM_STATUS, "canonical": False, "class": _derived_class(x["class"] for x in ordered), "metric": metric, "value": sum(x["value"] for x in ordered), "unit": unit, "entity": {"id": entity, "financial_scope": scope}, "period": {"kind": DURATION_TTM, "through_fiscal_year": seq[-1][0], "through_fiscal_quarter": seq[-1][1]}, "transform": {"rule": "TTM_FOUR_QUARTERS_V01", "formula": "Q[-3] + Q[-2] + Q[-1] + Q[0]", "components": [x["value"] for x in ordered], "input_observation_sha256": [x["observation_sha256"] for x in ordered]}, "ttm_sha256": ""}
    return _finish_ttm(result)


def ttm_annual_bridge(prior_annual: dict[str, Any], current_ytd: dict[str, Any], prior_ytd: dict[str, Any]) -> dict[str, Any]:
    inputs = [prior_annual, current_ytd, prior_ytd]
    keys = {_compat(x) for x in inputs}
    if len(keys) != 1:
        raise CaseServiceError("annual bridge metric/entity/scope/unit mismatch / annual bridge 입력 호환성 오류")
    if [x["period"]["kind"] for x in inputs] != [DURATION_ANNUAL, DURATION_YTD, DURATION_YTD]:
        raise CaseServiceError("annual bridge requires annual,current YTD,prior YTD / annual bridge 기간종류 오류")
    annual_fy, current_fy, prior_fy = (prior_annual["period"].get("fiscal_year"), current_ytd["period"].get("fiscal_year"), prior_ytd["period"].get("fiscal_year"))
    if any(isinstance(v, bool) or not isinstance(v, int) for v in (annual_fy,current_fy,prior_fy)) or current_fy != prior_fy + 1 or annual_fy != prior_fy:
        raise CaseServiceError("annual bridge fiscal years not comparable / annual bridge 회계연도 비교 불가")
    stage = current_ytd["period"].get("report_stage")
    if stage != prior_ytd["period"].get("report_stage") or stage not in {"Q1","H1","Q3"}:
        raise CaseServiceError("annual bridge YTD stages must match / annual bridge 누적단계 일치 필요")
    metric, entity, scope, unit = next(iter(keys))
    result = {"schema_version": TTM_SCHEMA_VERSION, "status": TTM_STATUS, "canonical": False, "class": _derived_class(x["class"] for x in inputs), "metric": metric, "value": prior_annual["value"] + current_ytd["value"] - prior_ytd["value"], "unit": unit, "entity": {"id": entity, "financial_scope": scope}, "period": {"kind": DURATION_TTM, "through_fiscal_year": current_fy, "through_fiscal_quarter": current_ytd["period"].get("fiscal_quarter"), "report_stage": stage}, "transform": {"rule": "TTM_ANNUAL_BRIDGE_V01", "formula": "PRIOR_FY + CURRENT_YTD - PRIOR_COMPARABLE_YTD", "components": {"prior_fy": prior_annual["value"], "current_ytd": current_ytd["value"], "prior_comparable_ytd": prior_ytd["value"]}, "input_observation_sha256": [x["observation_sha256"] for x in inputs]}, "ttm_sha256": ""}
    return _finish_ttm(result)


def validate_ttm_result(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema_version") != TTM_SCHEMA_VERSION or value.get("status") != TTM_STATUS or value.get("canonical") is not False:
        raise CaseServiceError("TTM schema/status invalid / TTM 스키마·상태 오류")
    if value.get("class") not in {"NORMALIZED_FACT", "NORMALIZED_FACT_CANDIDATE"} or value.get("period", {}).get("kind") != DURATION_TTM:
        raise CaseServiceError("TTM authority/period invalid / TTM 권위·기간 오류")
    _num(value.get("value"), "TTM value")
    if value.get("transform", {}).get("rule") not in {"TTM_FOUR_QUARTERS_V01", "TTM_ANNUAL_BRIDGE_V01"}:
        raise CaseServiceError("TTM transform invalid / TTM 변환 오류")
    expected = _sha(_without(value, "ttm_sha256"))
    if value.get("ttm_sha256") != expected:
        raise CaseServiceError("TTM SHA-256 mismatch / TTM SHA-256 불일치")
    return {"status": "PASS_TTM_VALIDATION", "canonical": False, "class": value["class"], "metric": value["metric"], "ttm_sha256": expected}


def reconcile_same_period(observations: list[dict[str, Any]]) -> dict[str, Any]:
    if not observations:
        raise CaseServiceError("reconciliation requires observations / 조정 observation 필요")
    if len({_compat(x) for x in observations}) != 1:
        raise CaseServiceError("reconciliation identity mismatch / 조정 identity 불일치")
    if len({_bytes(x["period"]) for x in observations}) != 1:
        raise CaseServiceError("reconciliation requires same period / 동일 기간 조정 필요")
    if len({json.dumps(x["value"], sort_keys=True) for x in observations}) != 1:
        raise CaseServiceError("UNKNOWN_CONFLICT: same-period values disagree / 동일기간 값 충돌")
    return copy.deepcopy(sorted(observations, key=lambda x: (x["class"] == "NORMALIZED_FACT", x["observation_sha256"]), reverse=True)[0])
