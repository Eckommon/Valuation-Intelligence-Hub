"""Governed interest-bearing debt components / 거버넌스 이자부채 구성요소.

M19 is deliberately isolated from the M13/M14 source registries and M15 financial
observation registry. It never mutates those historical contracts. Explicit debt
component evidence follows its own candidate → normalized observation → aggregate
pipeline and `liabilities → debt` is prohibited.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import date
from math import isfinite
from typing import Any
from urllib.parse import urlparse

from valuation_hub import dart_live, sec_live
from valuation_hub.case_service import CaseServiceError

DEBT_COMPONENT_OBSERVATION_SCHEMA = "debt-component-observation-v0.1"
DEBT_COMPONENT_OBSERVATION_STATUS = "DEBT_COMPONENT_NORMALIZED"
DEBT_SCHEMA_VERSION = "interest-bearing-debt-evidence-v0.1"
DEBT_STATUS = "INTEREST_BEARING_DEBT_EVIDENCE"
INSTANT = "INSTANT"
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
CIK_PATH_RE = re.compile(r"/CIK([0-9]{10})\.json$")
DART_STAGE = {"11013": ("Q1", 1), "11012": ("H1", 2), "11014": ("Q3", 3), "11011": ("FY", 4)}

# SEC CompanyFacts v0.1 support is intentionally narrow. Broad LongTermDebt*
# concepts are not relabeled as narrow borrowing/bond components because they can
# include multiple instrument classes and would create double-counting risk.
SEC_COMPONENT_SUPPORT = frozenset({"short_term_borrowings"})
SEC_COMPONENT_SPECS = {
    "short_term_borrowings": sec_live.MetricSpec(
        metric="short_term_borrowings",
        concepts=(("us-gaap", "ShortTermBorrowings"),),
        units=("USD",),
        forms=("10-Q", "10-Q/A", "10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A"),
    )
}

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


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result.pop(key, None)
    return result


def _number(value: Any, field: str, *, nonnegative: bool = False) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
        raise CaseServiceError(f"{field} must be finite numeric / {field} 유한 숫자 필요")
    if nonnegative and value < 0:
        raise CaseServiceError(f"{field} must be nonnegative / {field} 음수 불가")
    return value


def _source_class(value: Any) -> str:
    if value == "FACT":
        return "NORMALIZED_FACT"
    if value == "FACT_CANDIDATE":
        return "NORMALIZED_FACT_CANDIDATE"
    raise CaseServiceError("debt component normalization requires FACT or FACT_CANDIDATE / debt 구성요소 정규화는 FACT 또는 FACT_CANDIDATE 필요")


def _iso(value: Any, field: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise CaseServiceError(f"{field} date missing / {field} 날짜 누락")
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise CaseServiceError(f"{field} date invalid / {field} 날짜 오류") from exc


def _parse_dart_amount(raw: Any) -> int | None:
    if raw is None:
        return None
    if isinstance(raw, bool):
        raise CaseServiceError("OpenDART debt amount invalid / OpenDART debt 금액 오류")
    if isinstance(raw, int):
        return raw
    if not isinstance(raw, str):
        raise CaseServiceError("OpenDART debt amount must be integer text / OpenDART debt 금액형식 오류")
    text = raw.strip()
    if text in {"", "-"}:
        return None
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1].strip()
    compact = text.replace(",", "")
    if not re.fullmatch(r"[-+]?[0-9]+", compact):
        raise CaseServiceError("OpenDART debt amount malformed / OpenDART debt 금액 숫자형식 오류")
    value = int(compact)
    return -abs(value) if negative else value


def extract_sec_debt_component_candidate(snapshot: dict[str, Any], metric: str, *, form: str | None = None, period_end: str | None = None) -> dict[str, Any]:
    """Extract one exact SEC debt component without touching the M13 metric registry."""
    validation = sec_live.validate_source_snapshot(snapshot)
    spec = SEC_COMPONENT_SPECS.get(metric)
    if spec is None:
        raise CaseServiceError(f"unsupported SEC debt component / 미지원 SEC debt 구성요소: {metric}")
    requested_form = form.upper() if form else None
    if requested_form is not None and requested_form not in spec.forms:
        raise CaseServiceError("SEC form not allowed for debt component / debt 구성요소 SEC form 오류")
    requested_end = _iso(period_end, "SEC period_end") if period_end else None
    payload = json.loads(snapshot["raw_text"])
    facts = payload.get("facts")
    if not isinstance(facts, dict):
        raise CaseServiceError("SEC CompanyFacts facts missing / SEC CompanyFacts facts 누락")
    taxonomy, concept = spec.concepts[0]
    taxonomy_obj = facts.get(taxonomy)
    concept_obj = taxonomy_obj.get(concept) if isinstance(taxonomy_obj, dict) else None
    units_obj = concept_obj.get("units") if isinstance(concept_obj, dict) else None
    if not isinstance(units_obj, dict):
        raise CaseServiceError(f"SEC debt concept unavailable / SEC debt concept 없음: {taxonomy}:{concept}")
    candidates: list[dict[str, Any]] = []
    selected_unit = ""
    for unit in spec.units:
        series = units_obj.get(unit)
        if not isinstance(series, list):
            continue
        for raw in series:
            if not isinstance(raw, dict) or raw.get("form") not in spec.forms or (requested_form and raw.get("form") != requested_form):
                continue
            end = _iso(raw.get("end"), "SEC debt end")
            if requested_end and end != requested_end:
                continue
            filed = _iso(raw.get("filed"), "SEC debt filed")
            accn = raw.get("accn")
            if not isinstance(accn, str) or not sec_live.ACCESSION_RE.fullmatch(accn) or "val" not in raw:
                continue
            item = copy.deepcopy(raw)
            item["end"], item["filed"] = end, filed
            if "start" in item:
                item["start"] = _iso(item.get("start"), "SEC debt start", optional=True)
            candidates.append(item)
            selected_unit = unit
    if not candidates:
        raise CaseServiceError(f"no SEC debt component fact matches filters / SEC debt 구성요소 fact 없음: {metric}")
    latest_filed = max(item["filed"] for item in candidates)
    top = [item for item in candidates if item["filed"] == latest_filed]
    latest_end = max(item["end"] for item in top)
    top = [item for item in top if item["end"] == latest_end]
    distinct = {json.dumps(item["val"], ensure_ascii=False, sort_keys=True, allow_nan=False) for item in top}
    if len(distinct) != 1:
        raise CaseServiceError("equal-precedence SEC debt facts conflict / 동일 우선순위 SEC debt fact 충돌")
    chosen = sorted(top, key=lambda item: (str(item.get("accn", "")), str(item.get("form", "")), str(item.get("frame", ""))), reverse=True)[0]
    return {
        "schema_version": "sec-debt-component-candidate-v0.1",
        "status": "DEBT_COMPONENT_EVIDENCE_CANDIDATE_UNREVIEWED",
        "canonical": False,
        "class": "FACT_CANDIDATE",
        "metric": metric,
        "value": chosen["val"],
        "unit": selected_unit,
        "period": {"start": chosen.get("start"), "end": chosen["end"], "fy": chosen.get("fy"), "fp": chosen.get("fp"), "frame": chosen.get("frame")},
        "filing": {"accession": chosen["accn"], "form": chosen["form"], "filed": chosen["filed"]},
        "taxonomy": taxonomy,
        "concept": concept,
        "source": {"publisher": sec_live.SEC_PUBLISHER, "source_type": sec_live.SEC_SOURCE_TYPE, "tier_proposal": sec_live.SEC_TIER, "locator": snapshot["source"]["final_locator"], "snapshot_sha256": snapshot["snapshot_sha256"], "body_sha256": snapshot["response"]["body_sha256"]},
        "selection": {"rule": "EXACT_DEBT_CONCEPT_THEN_LATEST_FILED_THEN_LATEST_END", "requested_form": requested_form, "requested_period_end": requested_end, "equal_precedence_count": len(top)},
    }


def extract_dart_debt_component_candidate(snapshot: dict[str, Any], metric: str) -> dict[str, Any]:
    """Extract one exact OpenDART BS debt component without touching M14 registry."""
    validation = dart_live.validate_dart_snapshot(snapshot)
    spec = DART_COMPONENT_SPECS.get(metric)
    if spec is None:
        raise CaseServiceError(f"unsupported OpenDART debt component / 미지원 OpenDART debt 구성요소: {metric}")
    payload = json.loads(snapshot["raw_text"])
    rows = payload.get("list")
    if not isinstance(rows, list):
        raise CaseServiceError("OpenDART debt rows missing / OpenDART debt row 누락")
    section_rows = [row for row in rows if isinstance(row, dict) and str(row.get("sj_div", "")).upper() == "BS"]
    selected: list[dict[str, Any]] = []
    selection_kind = ""
    fallback_index = -1
    for index, account_id in enumerate(spec.account_ids):
        selected = [row for row in section_rows if row.get("account_id") == account_id]
        if selected:
            selection_kind, fallback_index = "account_id", index
            break
    if not selected:
        for index, account_name in enumerate(spec.account_names):
            selected = [row for row in section_rows if row.get("account_nm") == account_name]
            if selected:
                selection_kind, fallback_index = "account_nm", len(spec.account_ids) + index
                break
    if not selected:
        raise CaseServiceError(f"no OpenDART debt row matches component / OpenDART debt 구성요소 row 없음: {metric}")
    parsed = {_parse_dart_amount(row.get("thstrm_amount")) for row in selected}
    non_null = {value for value in parsed if value is not None}
    if len(non_null) > 1:
        raise CaseServiceError("equal-precedence OpenDART debt rows conflict / 동일 우선순위 OpenDART debt row 충돌")
    if not non_null:
        raise CaseServiceError("OpenDART debt current amount blank/unknown / OpenDART debt 당기금액 공란·미상")
    value = next(iter(non_null))
    chosen = sorted(selected, key=lambda row: (str(row.get("rcept_no", "")), str(row.get("ord", "")), str(row.get("account_detail", ""))), reverse=True)[0]
    provenance_fields = ("rcept_no", "reprt_code", "bsns_year", "corp_code", "stock_code", "fs_div", "fs_nm", "sj_div", "sj_nm", "account_id", "account_nm", "account_detail", "thstrm_nm", "thstrm_amount", "frmtrm_nm", "frmtrm_amount", "ord", "currency")
    return {
        "schema_version": "dart-debt-component-candidate-v0.1",
        "status": "DEBT_COMPONENT_EVIDENCE_CANDIDATE_UNREVIEWED",
        "canonical": False,
        "class": "FACT_CANDIDATE",
        "metric": metric,
        "value": value,
        "unit": chosen.get("currency") or "KRW",
        "request_identity": {"corp_code": validation["corp_code"], "bsns_year": validation["bsns_year"], "reprt_code": validation["reprt_code"], "fs_div": validation["fs_div"]},
        "statement_section": "BS",
        "account_selection": {"kind": selection_kind, "fallback_index": fallback_index, "fallback_used": selection_kind == "account_nm", "equal_precedence_count": len(selected)},
        "row": {field: chosen.get(field) for field in provenance_fields},
        "source": {"publisher": dart_live.DART_PUBLISHER, "source_type": dart_live.DART_SOURCE_TYPE, "tier_proposal": dart_live.DART_TIER, "locator": snapshot["source"]["final_locator"], "snapshot_sha256": snapshot["snapshot_sha256"], "body_sha256": snapshot["response"]["body_sha256"]},
    }


def normalize_debt_component_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    """Normalize one SEC/OpenDART debt component into an isolated INSTANT observation."""
    if not isinstance(candidate, dict) or candidate.get("canonical") is not False or candidate.get("metric") not in CORE_COMPONENT_SET:
        raise CaseServiceError("noncanonical supported debt component candidate required / 지원 debt 구성요소 후보 필요")
    schema = candidate.get("schema_version")
    source = candidate.get("source")
    if not isinstance(source, dict):
        raise CaseServiceError("debt component source provenance missing / debt 구성요소 출처정보 누락")
    metric = candidate["metric"]
    value = _number(candidate.get("value"), "debt component value", nonnegative=True)
    unit = candidate.get("unit")
    if not isinstance(unit, str) or not unit:
        raise CaseServiceError("debt component unit missing / debt 구성요소 unit 누락")
    klass = _source_class(candidate.get("class"))
    if schema == "sec-debt-component-candidate-v0.1":
        if metric not in SEC_COMPONENT_SUPPORT:
            raise CaseServiceError("SEC debt component not supported by v0.1 mapping / SEC debt 구성요소 v0.1 미지원")
        period, filing = candidate.get("period"), candidate.get("filing")
        if not isinstance(period, dict) or not isinstance(filing, dict):
            raise CaseServiceError("SEC debt candidate provenance incomplete / SEC debt 후보 출처정보 불완전")
        start = _iso(period.get("start"), "SEC debt period.start", optional=True)
        if start is not None:
            raise CaseServiceError("SEC debt component must be point-in-time / SEC debt 구성요소는 point-in-time이어야 함")
        end = _iso(period.get("end"), "SEC debt period.end")
        locator = source.get("locator")
        match = CIK_PATH_RE.search(urlparse(locator).path) if isinstance(locator, str) else None
        if not match:
            raise CaseServiceError("SEC debt CIK unavailable from locator / SEC debt locator CIK 확인 불가")
        entity = {"id": f"SEC_CIK:{match.group(1)}", "source_system": "SEC", "financial_scope": "AS_REPORTED"}
        period_out = {"kind": INSTANT, "start": None, "end": end, "duration_days": None, "fiscal_year": period.get("fy"), "fiscal_period": period.get("fp"), "fiscal_quarter": None, "report_stage": period.get("fp"), "date_precision": "EXACT"}
        source_detail = {"taxonomy": candidate.get("taxonomy"), "concept": candidate.get("concept"), "frame": period.get("frame")}
        filing_identity = copy.deepcopy(filing)
        rule = "SEC_DEBT_COMPONENT_INSTANT_V01"
    elif schema == "dart-debt-component-candidate-v0.1":
        request, row = candidate.get("request_identity"), candidate.get("row")
        if not isinstance(request, dict) or not isinstance(row, dict) or candidate.get("statement_section") != "BS":
            raise CaseServiceError("OpenDART debt candidate provenance incomplete / OpenDART debt 후보 출처정보 불완전")
        corp, year, report, scope = request.get("corp_code"), request.get("bsns_year"), request.get("reprt_code"), request.get("fs_div")
        if not all(isinstance(item, str) and item for item in (corp, year, report, scope)) or report not in DART_STAGE:
            raise CaseServiceError("OpenDART debt request identity invalid / OpenDART debt 요청식별 오류")
        stage, quarter = DART_STAGE[report]
        entity = {"id": f"DART_CORP:{corp}", "source_system": "OPENDART", "financial_scope": scope}
        period_out = {"kind": INSTANT, "start": None, "end": None, "duration_days": None, "fiscal_year": int(year), "fiscal_period": stage, "fiscal_quarter": quarter, "report_stage": stage, "date_precision": "REPORT_STAGE_ONLY"}
        source_detail = {"statement_section": "BS", "account_id": row.get("account_id"), "account_nm": row.get("account_nm"), "raw_current": row.get("thstrm_amount")}
        filing_identity = {"rcept_no": row.get("rcept_no"), "reprt_code": report, "bsns_year": year}
        rule = "OPENDART_DEBT_COMPONENT_INSTANT_V01"
    else:
        raise CaseServiceError(f"unsupported debt component candidate schema / 미지원 debt 구성요소 후보 스키마: {schema}")
    result = {
        "schema_version": DEBT_COMPONENT_OBSERVATION_SCHEMA,
        "status": DEBT_COMPONENT_OBSERVATION_STATUS,
        "canonical": False,
        "class": klass,
        "metric": metric,
        "value": value,
        "unit": unit,
        "entity": entity,
        "period": period_out,
        "lineage": {"normalization_rule": rule, "source_candidate_sha256": _sha(candidate), "source_class": candidate.get("class"), "source_snapshot_sha256": source.get("snapshot_sha256"), "source_body_sha256": source.get("body_sha256"), "filing_identity": filing_identity, "source_detail": source_detail},
        "observation_sha256": "",
    }
    result["observation_sha256"] = _sha(_without(result, "observation_sha256"))
    validate_debt_component_observation(result)
    return result


def validate_debt_component_observation(observation: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(observation, dict) or observation.get("schema_version") != DEBT_COMPONENT_OBSERVATION_SCHEMA or observation.get("status") != DEBT_COMPONENT_OBSERVATION_STATUS:
        raise CaseServiceError("debt component observation schema/status invalid / debt 구성요소 observation 스키마·상태 오류")
    if observation.get("canonical") is not False or observation.get("class") not in {"NORMALIZED_FACT", "NORMALIZED_FACT_CANDIDATE"}:
        raise CaseServiceError("debt component observation authority invalid / debt 구성요소 observation 권위 오류")
    if observation.get("metric") not in CORE_COMPONENT_SET:
        raise CaseServiceError("only explicit debt components are valid / 명시적 debt 구성요소만 유효")
    _number(observation.get("value"), "debt component value", nonnegative=True)
    if not isinstance(observation.get("unit"), str) or not observation["unit"]:
        raise CaseServiceError("debt component unit invalid / debt 구성요소 unit 오류")
    entity, period, lineage = observation.get("entity"), observation.get("period"), observation.get("lineage")
    if not isinstance(entity, dict) or not isinstance(entity.get("id"), str) or not entity.get("id") or not isinstance(entity.get("financial_scope"), str) or not entity.get("financial_scope"):
        raise CaseServiceError("debt component entity invalid / debt 구성요소 entity 오류")
    if not isinstance(period, dict) or period.get("kind") != INSTANT:
        raise CaseServiceError("debt component period must be INSTANT / debt 구성요소 period는 INSTANT 필요")
    if not isinstance(lineage, dict) or not isinstance(lineage.get("source_detail"), dict) or not isinstance(lineage.get("source_candidate_sha256"), str):
        raise CaseServiceError("debt component lineage invalid / debt 구성요소 lineage 오류")
    sha = observation.get("observation_sha256")
    if not isinstance(sha, str) or not SHA256_RE.fullmatch(sha) or sha != _sha(_without(observation, "observation_sha256")):
        raise CaseServiceError("debt component observation SHA-256 mismatch / debt 구성요소 observation SHA-256 불일치")
    return {"status": "PASS_DEBT_COMPONENT_OBSERVATION_VALIDATION", "metric": observation["metric"], "class": observation["class"], "observation_sha256": sha}


def _identity(observation: dict[str, Any]) -> tuple[str, str, str, str]:
    validate_debt_component_observation(observation)
    return (observation["entity"]["id"], observation["entity"]["financial_scope"], observation["unit"], json.dumps(observation["period"], ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False))


def aggregate_interest_bearing_debt(observations: list[dict[str, Any]]) -> dict[str, Any]:
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
        distinct_values = {_number(item.get("value"), f"{metric}.value", nonnegative=True) for item in group}
        if len(distinct_values) > 1:
            conflicts.append({"metric": metric, "values": sorted(distinct_values), "observation_sha256": sorted(item["observation_sha256"] for item in group), "source_classes": sorted(item["class"] for item in group)})
            continue
        selected.append(sorted(group, key=lambda item: (item.get("class") == "NORMALIZED_FACT", item.get("observation_sha256", "")), reverse=True)[0])
    present = [item["metric"] for item in selected]
    missing = [metric for metric in CORE_COMPONENTS if metric not in grouped]
    conflict_metrics = [item["metric"] for item in conflicts]
    result_class = "DERIVED_FACT" if all(item["class"] == "NORMALIZED_FACT" for item in observations) else "DERIVED_FACT_CANDIDATE"
    if conflicts:
        coverage_status, known_sum, debt_value = CONFLICT, None, None
    else:
        known_sum = sum(_number(item["value"], f"{item['metric']}.value", nonnegative=True) for item in selected)
        coverage_status = COMPLETE if len(present) == len(CORE_COMPONENTS) else PARTIAL
        debt_value = known_sum if coverage_status == COMPLETE else None
    eligible = coverage_status == COMPLETE and result_class == "DERIVED_FACT"
    components = [{"metric": item["metric"], "value": item["value"], "class": item["class"], "observation_sha256": item["observation_sha256"], "source_detail": copy.deepcopy(item["lineage"]["source_detail"])} for item in sorted(selected, key=lambda item: CORE_COMPONENTS.index(item["metric"]))]
    input_observations = [{"metric": item["metric"], "value": item["value"], "class": item["class"], "observation_sha256": item["observation_sha256"], "source_detail": copy.deepcopy(item["lineage"]["source_detail"])} for item in sorted(observations, key=lambda item: (CORE_COMPONENTS.index(item["metric"]), item["observation_sha256"]))]
    result = {
        "schema_version": DEBT_SCHEMA_VERSION, "status": DEBT_STATUS, "canonical": False, "class": result_class,
        "metric": "interest_bearing_debt", "unit": unit, "entity": {"id": entity_id, "financial_scope": scope}, "period": period,
        "coverage": {"status": coverage_status, "expected_components": list(CORE_COMPONENTS), "present_components": present, "missing_components": missing, "conflict_components": conflict_metrics},
        "input_observations": input_observations, "components": components, "conflicts": conflicts,
        "known_component_sum": known_sum, "interest_bearing_debt_value": debt_value,
        "semantic_boundary": {"total_liabilities_used": False, "lease_liabilities_included": False, "missing_as_zero": False, "eligible_for_draft_direct_bind": eligible, "warning_en": "Debt is derived only from explicit core components; total liabilities and missing components are never substituted.", "warning_ko": "Debt는 명시적 핵심 구성요소만으로 파생하며 총부채나 누락항목을 대체값으로 사용하지 않습니다."},
        "policy": {"version": "CORE_INTEREST_BEARING_DEBT_V01", "lease_policy": "EXCLUDED_PENDING_EXPLICIT_POLICY"}, "debt_sha256": "",
    }
    result["debt_sha256"] = _sha(_without(result, "debt_sha256"))
    validate_interest_bearing_debt_evidence(result)
    return result


def validate_interest_bearing_debt_evidence(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema_version") != DEBT_SCHEMA_VERSION or value.get("status") != DEBT_STATUS or value.get("canonical") is not False:
        raise CaseServiceError("interest-bearing debt schema/status invalid / 이자부채 스키마·상태 오류")
    if value.get("class") not in {"DERIVED_FACT", "DERIVED_FACT_CANDIDATE"} or value.get("metric") != "interest_bearing_debt":
        raise CaseServiceError("interest-bearing debt authority/metric invalid / 이자부채 권위·metric 오류")
    entity, period, coverage, boundary = value.get("entity"), value.get("period"), value.get("coverage"), value.get("semantic_boundary")
    if not isinstance(entity, dict) or not entity.get("id") or not entity.get("financial_scope") or not isinstance(period, dict) or period.get("kind") != INSTANT:
        raise CaseServiceError("interest-bearing debt identity/period invalid / 이자부채 식별·period 오류")
    if not isinstance(value.get("unit"), str) or not value["unit"] or not isinstance(coverage, dict) or coverage.get("status") not in {COMPLETE, PARTIAL, CONFLICT}:
        raise CaseServiceError("interest-bearing debt unit/coverage invalid / 이자부채 unit·coverage 오류")
    if coverage.get("expected_components") != list(CORE_COMPONENTS):
        raise CaseServiceError("interest-bearing debt component policy mismatch / 이자부채 구성요소 정책 불일치")
    inputs = value.get("input_observations")
    components = value.get("components")
    conflicts = value.get("conflicts")
    if not isinstance(inputs, list) or not inputs or not isinstance(components, list) or not isinstance(conflicts, list):
        raise CaseServiceError("interest-bearing debt lineage invalid / 이자부채 lineage 오류")
    for item in inputs:
        if not isinstance(item, dict) or item.get("metric") not in CORE_COMPONENT_SET or item.get("class") not in {"NORMALIZED_FACT", "NORMALIZED_FACT_CANDIDATE"} or not isinstance(item.get("source_detail"), dict):
            raise CaseServiceError("interest-bearing debt input lineage invalid / 이자부채 입력 lineage 오류")
        _number(item.get("value"), "debt input value", nonnegative=True)
        sha = item.get("observation_sha256")
        if not isinstance(sha, str) or not SHA256_RE.fullmatch(sha):
            raise CaseServiceError("interest-bearing debt input SHA invalid / 이자부채 입력 SHA 오류")
    expected_class = "DERIVED_FACT" if all(item["class"] == "NORMALIZED_FACT" for item in inputs) else "DERIVED_FACT_CANDIDATE"
    if value.get("class") != expected_class:
        raise CaseServiceError("interest-bearing debt authority propagation mismatch / 이자부채 권위전파 불일치")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in inputs:
        grouped.setdefault(item["metric"], []).append(item)
    expected_components: list[dict[str, Any]] = []
    expected_conflicts: list[dict[str, Any]] = []
    for metric in CORE_COMPONENTS:
        group = grouped.get(metric, [])
        if not group:
            continue
        distinct = {_number(item["value"], "debt input value", nonnegative=True) for item in group}
        if len(distinct) > 1:
            expected_conflicts.append({"metric": metric, "values": sorted(distinct), "observation_sha256": sorted(item["observation_sha256"] for item in group), "source_classes": sorted(item["class"] for item in group)})
        else:
            chosen = sorted(group, key=lambda item: (item["class"] == "NORMALIZED_FACT", item["observation_sha256"]), reverse=True)[0]
            expected_components.append({"metric": chosen["metric"], "value": chosen["value"], "class": chosen["class"], "observation_sha256": chosen["observation_sha256"], "source_detail": copy.deepcopy(chosen["source_detail"])})
    if components != expected_components or conflicts != expected_conflicts:
        raise CaseServiceError("interest-bearing debt reconciliation lineage mismatch / 이자부채 조정 lineage 불일치")
    present = [item["metric"] for item in expected_components]
    missing = [metric for metric in CORE_COMPONENTS if metric not in grouped]
    conflict_metrics = [item["metric"] for item in expected_conflicts]
    expected_status = CONFLICT if expected_conflicts else (COMPLETE if len(present) == len(CORE_COMPONENTS) else PARTIAL)
    expected_coverage = {"status": expected_status, "expected_components": list(CORE_COMPONENTS), "present_components": present, "missing_components": missing, "conflict_components": conflict_metrics}
    if coverage != expected_coverage:
        raise CaseServiceError("interest-bearing debt coverage mismatch / 이자부채 coverage 불일치")
    component_sum = sum(_number(item["value"], "component value", nonnegative=True) for item in expected_components)
    known_sum, debt_value = value.get("known_component_sum"), value.get("interest_bearing_debt_value")
    if expected_status == CONFLICT:
        if known_sum is not None or debt_value is not None:
            raise CaseServiceError("conflict-blocked debt must not expose totals / 충돌차단 debt 합계 노출 불가")
    elif expected_status == COMPLETE:
        if _number(known_sum, "known_component_sum", nonnegative=True) != component_sum or _number(debt_value, "interest_bearing_debt_value", nonnegative=True) != component_sum:
            raise CaseServiceError("complete debt arithmetic invalid / 완전 debt 산술 오류")
    else:
        if _number(known_sum, "known_component_sum", nonnegative=True) != component_sum or debt_value is not None:
            raise CaseServiceError("partial debt arithmetic invalid / 부분 debt 산술 오류")
    if not isinstance(boundary, dict) or boundary.get("total_liabilities_used") is not False or boundary.get("lease_liabilities_included") is not False or boundary.get("missing_as_zero") is not False:
        raise CaseServiceError("interest-bearing debt semantic boundary invalid / 이자부채 의미경계 오류")
    eligible = expected_status == COMPLETE and expected_class == "DERIVED_FACT"
    if boundary.get("eligible_for_draft_direct_bind") is not eligible:
        raise CaseServiceError("interest-bearing debt Draft eligibility mismatch / 이자부채 Draft 적격성 오류")
    policy = value.get("policy")
    if not isinstance(policy, dict) or policy.get("version") != "CORE_INTEREST_BEARING_DEBT_V01" or policy.get("lease_policy") != "EXCLUDED_PENDING_EXPLICIT_POLICY":
        raise CaseServiceError("interest-bearing debt policy invalid / 이자부채 정책 오류")
    sha = value.get("debt_sha256")
    if not isinstance(sha, str) or not SHA256_RE.fullmatch(sha) or sha != _sha(_without(value, "debt_sha256")):
        raise CaseServiceError("interest-bearing debt SHA-256 mismatch / 이자부채 SHA-256 불일치")
    return {"status": "PASS_INTEREST_BEARING_DEBT_VALIDATION", "coverage_status": expected_status, "class": expected_class, "eligible_for_draft_direct_bind": eligible, "debt_sha256": sha}
