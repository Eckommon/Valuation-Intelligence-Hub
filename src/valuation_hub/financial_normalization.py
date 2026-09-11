"""Financial evidence normalization kernel / 재무근거 정규화 커널.

M15 converts SEC/OpenDART evidence records into period-aware observations and
reproducible TTM transforms. Arithmetic never upgrades evidence authority.
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
ALLOWED_SOURCE_CLASSES = {"FACT", "FACT_CANDIDATE"}
DART_STAGE = {"11013": ("Q1", 1), "11012": ("H1", 2), "11014": ("Q3", 3), "11011": ("FY", 4)}
CIK_PATH_RE = re.compile(r"/CIK([0-9]{10})\.json$")


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _without_hash(value: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(value)
    payload.pop("observation_sha256", None)
    payload.pop("ttm_sha256", None)
    return payload


def _source_authority(source_class: Any) -> str:
    if source_class not in ALLOWED_SOURCE_CLASSES:
        raise CaseServiceError("normalization requires FACT or FACT_CANDIDATE input / 정규화 입력은 FACT 또는 FACT_CANDIDATE여야 합니다")
    return "NORMALIZED_FACT" if source_class == "FACT" else "NORMALIZED_FACT_CANDIDATE"


def _derived_authority(classes: Iterable[str]) -> str:
    values = list(classes)
    if not values:
        raise CaseServiceError("normalization transform requires inputs / 정규화 변환 입력이 필요합니다")
    allowed = {"NORMALIZED_FACT", "NORMALIZED_FACT_CANDIDATE"}
    if any(value not in allowed for value in values):
        raise CaseServiceError("TTM requires normalized fact inputs / TTM은 정규화 fact 입력이 필요합니다")
    return "NORMALIZED_FACT" if all(value == "NORMALIZED_FACT" for value in values) else "NORMALIZED_FACT_CANDIDATE"


def _number(value: Any, field: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CaseServiceError(f"{field} must be numeric / {field} 숫자 필요")
    return value


def _iso(value: Any, field: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise CaseServiceError(f"{field} must be ISO date / {field} ISO 날짜 필요")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise CaseServiceError(f"{field} invalid date / {field} 날짜 오류") from exc
    if parsed.isoformat() != value:
        raise CaseServiceError(f"{field} must be canonical YYYY-MM-DD / {field} 날짜 정규형식 오류")
    return value


def _duration_days(start: str, end: str) -> int:
    left = date.fromisoformat(start)
    right = date.fromisoformat(end)
    days = (right - left).days + 1
    if days <= 0:
        raise CaseServiceError("duration start must precede end / 기간 시작일은 종료일보다 앞서야 합니다")
    return days


def _parse_dart_amount(raw: Any, field: str) -> int | None:
    if raw is None:
        return None
    if isinstance(raw, bool):
        raise CaseServiceError(f"{field} invalid / {field} 오류")
    if isinstance(raw, int):
        return raw
    if not isinstance(raw, str):
        raise CaseServiceError(f"{field} must be integer text / {field} 정수 문자열 필요")
    text = raw.strip()
    if text in {"", "-"}:
        return None
    parenthesized = text.startswith("(") and text.endswith(")")
    if parenthesized:
        text = text[1:-1].strip()
    compact = text.replace(",", "")
    if not re.fullmatch(r"[-+]?[0-9]+", compact):
        raise CaseServiceError(f"{field} malformed / {field} 숫자 형식 오류")
    value = int(compact)
    return -abs(value) if parenthesized else value


def _finish_observation(payload: dict[str, Any]) -> dict[str, Any]:
    payload["observation_sha256"] = _sha(payload)
    validate_financial_observation(payload)
    return payload


def normalize_sec_candidate(candidate: dict[str, Any], *, declared_period_kind: str | None = None) -> dict[str, Any]:
    """Normalize one SEC evidence candidate without guessing 10-Q duration semantics."""
    if not isinstance(candidate, dict) or candidate.get("schema_version") != "sec-evidence-candidate-v0.1":
        raise CaseServiceError("SEC evidence candidate v0.1 required / SEC evidence candidate v0.1 필요")
    if candidate.get("canonical") is not False:
        raise CaseServiceError("source evidence candidate must be noncanonical / 원천 근거후보는 비정식이어야 합니다")
    metric = candidate.get("metric")
    if metric not in INSTANT_METRICS | DURATION_METRICS:
        raise CaseServiceError(f"unsupported normalized metric / 미지원 정규화 지표: {metric}")
    source_class = candidate.get("class")
    authority = _source_authority(source_class)
    source = candidate.get("source")
    period = candidate.get("period")
    filing = candidate.get("filing")
    if not isinstance(source, dict) or not isinstance(period, dict) or not isinstance(filing, dict):
        raise CaseServiceError("SEC candidate provenance incomplete / SEC 후보 출처정보 불완전")
    locator = source.get("locator")
    if not isinstance(locator, str):
        raise CaseServiceError("SEC source locator missing / SEC source locator 누락")
    match = CIK_PATH_RE.search(urlparse(locator).path)
    if not match:
        raise CaseServiceError("SEC CIK cannot be recovered from source locator / SEC source locator에서 CIK 복원 불가")
    entity_id = f"SEC_CIK:{match.group(1)}"
    value = _number(candidate.get("value"), "SEC value")
    unit = candidate.get("unit")
    if not isinstance(unit, str) or not unit:
        raise CaseServiceError("SEC candidate unit missing / SEC 후보 unit 누락")
    end = _iso(period.get("end"), "SEC period.end")
    start = _iso(period.get("start"), "SEC period.start", optional=True)
    form = filing.get("form")
    if not isinstance(form, str):
        raise CaseServiceError("SEC filing form missing / SEC filing form 누락")
    fiscal_year = period.get("fy")
    fp = period.get("fp")
    frame = period.get("frame")

    duration_days: int | None = None
    fiscal_quarter: int | None = None
    if metric in INSTANT_METRICS:
        if start is not None:
            raise CaseServiceError("instant SEC metric must not have period start / SEC instant 지표에 시작일이 있으면 안 됩니다")
        kind = INSTANT
    else:
        if start is None:
            raise CaseServiceError("duration SEC metric requires period start / SEC duration 지표는 시작일 필요")
        duration_days = _duration_days(start, end)
        if form in {"10-K", "10-K/A"}:
            if not 330 <= duration_days <= 400:
                raise CaseServiceError("SEC 10-K duration is not annual-like / SEC 10-K 기간이 연간 범위가 아닙니다")
            if declared_period_kind not in (None, DURATION_ANNUAL):
                raise CaseServiceError("SEC 10-K period kind conflicts with annual semantics / SEC 10-K 기간종류 충돌")
            kind = DURATION_ANNUAL
            fiscal_quarter = 4
        elif form in {"10-Q", "10-Q/A"}:
            if declared_period_kind not in {DURATION_QUARTER, DURATION_YTD}:
                raise CaseServiceError("SEC 10-Q requires explicit DURATION_QUARTER or DURATION_YTD / SEC 10-Q는 기간종류를 명시해야 합니다")
            kind = declared_period_kind
            fp_map = {"Q1": 1, "Q2": 2, "Q3": 3}
            fiscal_quarter = fp_map.get(str(fp))
            if fiscal_quarter is None:
                raise CaseServiceError("SEC 10-Q requires fp Q1/Q2/Q3 / SEC 10-Q fp 오류")
            if kind == DURATION_QUARTER and not 60 <= duration_days <= 120:
                raise CaseServiceError("declared SEC quarter duration outside safe range / SEC 분기 기간 범위 오류")
            if kind == DURATION_YTD:
                minimum = {1: 60, 2: 140, 3: 230}[fiscal_quarter]
                maximum = {1: 120, 2: 220, 3: 320}[fiscal_quarter]
                if not minimum <= duration_days <= maximum:
                    raise CaseServiceError("declared SEC YTD duration outside safe range / SEC 누적 기간 범위 오류")
        else:
            raise CaseServiceError(f"SEC form unsupported for normalization / 정규화 미지원 SEC form: {form}")

    observation = {
        "schema_version": OBSERVATION_SCHEMA_VERSION,
        "status": OBSERVATION_STATUS,
        "canonical": False,
        "class": authority,
        "metric": metric,
        "value": value,
        "unit": unit,
        "entity": {"id": entity_id, "source_system": "SEC", "financial_scope": "AS_REPORTED"},
        "period": {
            "kind": kind,
            "start": start,
            "end": end,
            "duration_days": duration_days,
            "fiscal_year": fiscal_year,
            "fiscal_period": fp,
            "fiscal_quarter": fiscal_quarter,
            "report_stage": fp,
            "date_precision": "EXACT",
        },
        "lineage": {
            "normalization_rule": "SEC_PERIOD_CLASSIFICATION_V01",
            "source_candidate_sha256": _sha(candidate),
            "source_class": source_class,
            "source_snapshot_sha256": source.get("snapshot_sha256"),
            "source_body_sha256": source.get("body_sha256"),
            "filing_identity": copy.deepcopy(filing),
            "source_detail": {"taxonomy": candidate.get("taxonomy"), "concept": candidate.get("concept"), "frame": frame},
        },
        "observation_sha256": "",
    }
    return _finish_observation(observation)


def normalize_dart_candidate(candidate: dict[str, Any], *, amount_basis: str = "CURRENT") -> dict[str, Any]:
    """Normalize one OpenDART candidate using documented current/cumulative semantics."""
    if not isinstance(candidate, dict) or candidate.get("schema_version") != "dart-evidence-candidate-v0.1":
        raise CaseServiceError("OpenDART evidence candidate v0.1 required / OpenDART evidence candidate v0.1 필요")
    if candidate.get("canonical") is not False:
        raise CaseServiceError("source evidence candidate must be noncanonical / 원천 근거후보는 비정식이어야 합니다")
    metric = candidate.get("metric")
    if metric not in INSTANT_METRICS | DURATION_METRICS:
        raise CaseServiceError(f"unsupported normalized metric / 미지원 정규화 지표: {metric}")
    source_class = candidate.get("class")
    authority = _source_authority(source_class)
    request = candidate.get("request_identity")
    row = candidate.get("row")
    source = candidate.get("source")
    if not isinstance(request, dict) or not isinstance(row, dict) or not isinstance(source, dict):
        raise CaseServiceError("OpenDART candidate provenance incomplete / OpenDART 후보 출처정보 불완전")
    corp_code = request.get("corp_code")
    year = request.get("bsns_year")
    report = request.get("reprt_code")
    fs_div = request.get("fs_div")
    if not all(isinstance(x, str) and x for x in (corp_code, year, report, fs_div)) or report not in DART_STAGE:
        raise CaseServiceError("OpenDART request identity invalid / OpenDART 요청 식별 오류")
    stage, quarter = DART_STAGE[report]
    section = candidate.get("statement_section")
    basis = amount_basis.upper()
    if basis not in {"CURRENT", "CUMULATIVE"}:
        raise CaseServiceError("OpenDART amount_basis must be CURRENT or CUMULATIVE / OpenDART amount_basis 오류")

    if metric in INSTANT_METRICS:
        if section != "BS":
            raise CaseServiceError("OpenDART instant metric requires BS / OpenDART instant 지표는 BS 필요")
        if basis != "CURRENT":
            raise CaseServiceError("OpenDART instant metric cannot use cumulative amount / OpenDART instant 지표는 누적금액 사용 불가")
        kind = INSTANT
        value = _number(candidate.get("value"), "OpenDART value")
        fiscal_quarter = quarter
    else:
        if section not in {"IS", "CIS"}:
            raise CaseServiceError("OpenDART duration metric requires IS/CIS / OpenDART duration 지표는 IS/CIS 필요")
        if report == "11011":
            if basis != "CURRENT":
                raise CaseServiceError("annual OpenDART duration uses current annual amount / OpenDART 연간 duration은 당기금액 사용")
            kind = DURATION_ANNUAL
            value = _number(candidate.get("value"), "OpenDART value")
            fiscal_quarter = 4
        elif basis == "CURRENT":
            kind = DURATION_QUARTER
            value = _number(candidate.get("value"), "OpenDART value")
            fiscal_quarter = quarter
        else:
            kind = DURATION_YTD
            value = _parse_dart_amount(row.get("thstrm_add_amount"), "thstrm_add_amount")
            if value is None:
                raise CaseServiceError("OpenDART cumulative amount unavailable / OpenDART 누적금액 없음")
            fiscal_quarter = quarter

    unit = candidate.get("unit")
    if not isinstance(unit, str) or not unit:
        raise CaseServiceError("OpenDART unit missing / OpenDART unit 누락")
    observation = {
        "schema_version": OBSERVATION_SCHEMA_VERSION,
        "status": OBSERVATION_STATUS,
        "canonical": False,
        "class": authority,
        "metric": metric,
        "value": value,
        "unit": unit,
        "entity": {"id": f"DART_CORP:{corp_code}", "source_system": "OPENDART", "financial_scope": fs_div},
        "period": {
            "kind": kind,
            "start": None,
            "end": None,
            "duration_days": None,
            "fiscal_year": int(year),
            "fiscal_period": stage,
            "fiscal_quarter": fiscal_quarter,
            "report_stage": stage,
            "date_precision": "REPORT_STAGE_ONLY",
        },
        "lineage": {
            "normalization_rule": "OPENDART_PERIOD_SEMANTICS_V01",
            "source_candidate_sha256": _sha(candidate),
            "source_class": source_class,
            "source_snapshot_sha256": source.get("snapshot_sha256"),
            "source_body_sha256": source.get("body_sha256"),
            "filing_identity": {"rcept_no": row.get("rcept_no"), "reprt_code": report, "bsns_year": year},
            "source_detail": {"statement_section": section, "account_id": row.get("account_id"), "account_nm": row.get("account_nm"), "amount_basis": basis, "raw_current": row.get("thstrm_amount"), "raw_cumulative": row.get("thstrm_add_amount")},
        },
        "observation_sha256": "",
    }
    return _finish_observation(observation)


def validate_financial_observation(observation: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(observation, dict) or observation.get("schema_version") != OBSERVATION_SCHEMA_VERSION or observation.get("status") != OBSERVATION_STATUS:
        raise CaseServiceError("financial observation schema/status invalid / 재무 observation 스키마·상태 오류")
    if observation.get("canonical") is not False:
        raise CaseServiceError("normalized observation itself is noncanonical / 정규화 observation 자체는 비정식입니다")
    if observation.get("class") not in {"NORMALIZED_FACT", "NORMALIZED_FACT_CANDIDATE"}:
        raise CaseServiceError("financial observation authority class invalid / 재무 observation 권위 class 오류")
    metric = observation.get("metric")
    if metric not in INSTANT_METRICS | DURATION_METRICS:
        raise CaseServiceError("financial observation metric unsupported / 재무 observation 지표 미지원")
    _number(observation.get("value"), "observation value")
    if not isinstance(observation.get("unit"), str) or not observation["unit"]:
        raise CaseServiceError("financial observation unit missing / 재무 observation unit 누락")
    entity = observation.get("entity")
    period = observation.get("period")
    lineage = observation.get("lineage")
    if not isinstance(entity, dict) or not isinstance(entity.get("id"), str) or not isinstance(entity.get("financial_scope"), str):
        raise CaseServiceError("financial observation entity identity invalid / 재무 observation entity 식별 오류")
    if not isinstance(period, dict) or period.get("kind") not in PERIOD_KINDS:
        raise CaseServiceError("financial observation period invalid / 재무 observation 기간 오류")
    if not isinstance(lineage, dict) or not isinstance(lineage.get("normalization_rule"), str):
        raise CaseServiceError("financial observation lineage invalid / 재무 observation lineage 오류")
    expected = _sha(_without_hash(observation))
    if observation.get("observation_sha256") != expected:
        raise CaseServiceError("financial observation SHA-256 mismatch / 재무 observation SHA-256 불일치")
    return {"status": "PASS_FINANCIAL_OBSERVATION_VALIDATION", "canonical": False, "class": observation["class"], "metric": metric, "period_kind": period["kind"], "observation_sha256": expected}


def _compatibility_key(observation: dict[str, Any]) -> tuple[str, str, str, str]:
    validate_financial_observation(observation)
    entity = observation["entity"]
    return observation["metric"], entity["id"], entity["financial_scope"], observation["unit"]


def _finish_ttm(payload: dict[str, Any]) -> dict[str, Any]:
    payload["ttm_sha256"] = _sha(payload)
    validate_ttm_result(payload)
    return payload


def ttm_four_quarters(observations: list[dict[str, Any]]) -> dict[str, Any]:
    if len(observations) != 4:
        raise CaseServiceError("four-quarter TTM requires exactly 4 observations / 4분기 TTM은 정확히 4개 observation 필요")
    keys = {_compatibility_key(item) for item in observations}
    if len(keys) != 1:
        raise CaseServiceError("TTM input metric/entity/scope/unit mismatch / TTM 입력 지표·entity·scope·unit 불일치")
    if any(item["period"]["kind"] != DURATION_QUARTER for item in observations):
        raise CaseServiceError("four-quarter TTM requires quarter-duration inputs / 4분기 TTM은 분기 duration 입력 필요")
    sequence: list[tuple[int, int, dict[str, Any]]] = []
    for item in observations:
        fy = item["period"].get("fiscal_year")
        fq = item["period"].get("fiscal_quarter")
        if isinstance(fy, bool) or not isinstance(fy, int) or isinstance(fq, bool) or not isinstance(fq, int) or fq not in {1, 2, 3, 4}:
            raise CaseServiceError("quarter TTM requires fiscal year/quarter identity / 분기 TTM은 회계연도·분기 식별 필요")
        sequence.append((fy, fq, item))
    sequence.sort(key=lambda x: (x[0], x[1]))
    indexes = [fy * 4 + fq for fy, fq, _ in sequence]
    if len(set(indexes)) != 4 or any(right - left != 1 for left, right in zip(indexes, indexes[1:])):
        raise CaseServiceError("quarter TTM inputs contain duplicate or gap / 분기 TTM 입력에 중복 또는 공백 존재")
    ordered = [item for _, _, item in sequence]
    value = sum(item["value"] for item in ordered)
    authority = _derived_authority(item["class"] for item in ordered)
    metric, entity_id, scope, unit = next(iter(keys))
    result = {
        "schema_version": TTM_SCHEMA_VERSION,
        "status": TTM_STATUS,
        "canonical": False,
        "class": authority,
        "metric": metric,
        "value": value,
        "unit": unit,
        "entity": {"id": entity_id, "financial_scope": scope},
        "period": {"kind": DURATION_TTM, "through_fiscal_year": sequence[-1][0], "through_fiscal_quarter": sequence[-1][1]},
        "transform": {
            "rule": "TTM_FOUR_QUARTERS_V01",
            "formula": "Q[-3] + Q[-2] + Q[-1] + Q[0]",
            "components": [item["value"] for item in ordered],
            "input_observation_sha256": [item["observation_sha256"] for item in ordered],
        },
        "ttm_sha256": "",
    }
    return _finish_ttm(result)


def ttm_annual_bridge(prior_annual: dict[str, Any], current_ytd: dict[str, Any], prior_ytd: dict[str, Any]) -> dict[str, Any]:
    inputs = [prior_annual, current_ytd, prior_ytd]
    keys = {_compatibility_key(item) for item in inputs}
    if len(keys) != 1:
        raise CaseServiceError("TTM input metric/entity/scope/unit mismatch / TTM 입력 지표·entity·scope·unit 불일치")
    if prior_annual["period"]["kind"] != DURATION_ANNUAL or current_ytd["period"]["kind"] != DURATION_YTD or prior_ytd["period"]["kind"] != DURATION_YTD:
        raise CaseServiceError("annual bridge requires annual + current YTD - prior YTD / annual bridge 입력 기간종류 오류")
    current_fy = current_ytd["period"].get("fiscal_year")
    prior_fy = prior_ytd["period"].get("fiscal_year")
    annual_fy = prior_annual["period"].get("fiscal_year")
    current_stage = current_ytd["period"].get("report_stage")
    prior_stage = prior_ytd["period"].get("report_stage")
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in (current_fy, prior_fy, annual_fy)):
        raise CaseServiceError("annual bridge requires fiscal-year identities / annual bridge는 회계연도 식별 필요")
    if current_fy != prior_fy + 1 or annual_fy != prior_fy:
        raise CaseServiceError("annual bridge fiscal years are not comparable / annual bridge 회계연도 비교 불가")
    if current_stage != prior_stage or current_stage not in {"Q1", "H1", "Q3"}:
        raise CaseServiceError("annual bridge YTD stages must match / annual bridge 누적 단계가 일치해야 합니다")
    value = prior_annual["value"] + current_ytd["value"] - prior_ytd["value"]
    authority = _derived_authority(item["class"] for item in inputs)
    metric, entity_id, scope, unit = next(iter(keys))
    result = {
        "schema_version": TTM_SCHEMA_VERSION,
        "status": TTM_STATUS,
        "canonical": False,
        "class": authority,
        "metric": metric,
        "value": value,
        "unit": unit,
        "entity": {"id": entity_id, "financial_scope": scope},
        "period": {"kind": DURATION_TTM, "through_fiscal_year": current_fy, "through_fiscal_quarter": current_ytd["period"].get("fiscal_quarter"), "report_stage": current_stage},
        "transform": {
            "rule": "TTM_ANNUAL_BRIDGE_V01",
            "formula": "PRIOR_FY + CURRENT_YTD - PRIOR_COMPARABLE_YTD",
            "components": {"prior_fy": prior_annual["value"], "current_ytd": current_ytd["value"], "prior_comparable_ytd": prior_ytd["value"]},
            "input_observation_sha256": [item["observation_sha256"] for item in inputs],
        },
        "ttm_sha256": "",
    }
    return _finish_ttm(result)


def validate_ttm_result(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("schema_version") != TTM_SCHEMA_VERSION or result.get("status") != TTM_STATUS:
        raise CaseServiceError("TTM schema/status invalid / TTM 스키마·상태 오류")
    if result.get("canonical") is not False or result.get("class") not in {"NORMALIZED_FACT", "NORMALIZED_FACT_CANDIDATE"}:
        raise CaseServiceError("TTM authority state invalid / TTM 권위상태 오류")
    if result.get("period", {}).get("kind") != DURATION_TTM:
        raise CaseServiceError("TTM period kind invalid / TTM 기간종류 오류")
    _number(result.get("value"), "TTM value")
    transform = result.get("transform")
    if not isinstance(transform, dict) or transform.get("rule") not in {"TTM_FOUR_QUARTERS_V01", "TTM_ANNUAL_BRIDGE_V01"}:
        raise CaseServiceError("TTM transform metadata invalid / TTM 변환 메타데이터 오류")
    expected = _sha(_without_hash(result))
    if result.get("ttm_sha256") != expected:
        raise CaseServiceError("TTM SHA-256 mismatch / TTM SHA-256 불일치")
    return {"status": "PASS_TTM_VALIDATION", "canonical": False, "class": result["class"], "metric": result["metric"], "ttm_sha256": expected}


def reconcile_same_period(observations: list[dict[str, Any]]) -> dict[str, Any]:
    """Reconcile semantically identical period observations; never average conflicts."""
    if not observations:
        raise CaseServiceError("reconciliation requires observations / 조정할 observation 필요")
    keys = {_compatibility_key(item) for item in observations}
    if len(keys) != 1:
        raise CaseServiceError("reconciliation identity mismatch / 조정 identity 불일치")
    period_fingerprints = {
        _canonical_json_bytes(item["period"])
        for item in observations
    }
    if len(period_fingerprints) != 1:
        raise CaseServiceError("reconciliation requires same economic period / 동일 경제기간만 조정 가능")
    values = {json.dumps(item["value"], sort_keys=True) for item in observations}
    if len(values) != 1:
        raise CaseServiceError("UNKNOWN_CONFLICT: same-period normalized values disagree / 동일기간 정규화 값 충돌")
    # Prefer reviewed authority over candidate authority; tie-break by stable hash.
    ordered = sorted(observations, key=lambda item: (item["class"] == "NORMALIZED_FACT", item["observation_sha256"]), reverse=True)
    return copy.deepcopy(ordered[0])
