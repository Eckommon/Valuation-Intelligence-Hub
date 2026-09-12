"""M28 governed noncontrolling/minority-interest evidence.

M28 is intentionally isolated from M13/M14 metric registries. It reads validated
immutable SEC/OpenDART snapshots, extracts only exact noncontrolling-interest
concepts, and never converts missing evidence into zero.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import date, datetime
from math import isfinite
from typing import Any

from valuation_hub import dart_live, sec_live
from valuation_hub.case_service import CaseServiceError

CANDIDATE_SCHEMA = "minority-interest-candidate-v0.1"
OBSERVATION_SCHEMA = "minority-interest-observation-v0.1"
REVIEW_SCHEMA = "minority-interest-review-assertion-v0.1"
PACKAGE_SCHEMA = "reviewed-minority-interest-fact-v0.1"
METRIC = "minority_interest"
SEC_CONCEPT = ("us-gaap", "NoncontrollingInterestInConsolidatedEntity")
DART_ACCOUNT_ID = "ifrs-full_NoncontrollingInterests"
SEC_FORMS = frozenset({"10-Q", "10-Q/A", "10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A"})
DART_STAGE = {"11013": ("Q1", 1), "11012": ("H1", 2), "11014": ("Q3", 3), "11011": ("FY", 4)}
FRESH = "FRESH"
STALE_BLOCKED = "STALE_BLOCKED"
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    result = copy.deepcopy(value); result.pop(key, None); return result


def _number(value: Any, field: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)) or value < 0:
        raise CaseServiceError(f"{field} must be finite nonnegative / {field} 유한 비음수 필요")
    return value


def _date(value: Any, field: str) -> date:
    if not isinstance(value, str): raise CaseServiceError(f"{field} date required / {field} 날짜 필요")
    try: parsed = date.fromisoformat(value)
    except ValueError as exc: raise CaseServiceError(f"{field} invalid date / {field} 날짜 오류") from exc
    if parsed.isoformat() != value: raise CaseServiceError(f"{field} canonical date required / {field} 정규 날짜 필요")
    return parsed


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str): raise CaseServiceError(f"{field} timestamp required / {field} 시각 필요")
    try: parsed = datetime.fromisoformat(value)
    except ValueError as exc: raise CaseServiceError(f"{field} timestamp invalid / {field} 시각 오류") from exc
    if parsed.tzinfo is None: raise CaseServiceError(f"{field} timezone required / {field} 시간대 필요")
    return parsed


def _text(value: Any, field: str, maximum: int = 1000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
        raise CaseServiceError(f"{field} required / {field} 필요")
    return value.strip()


def _parse_dart_amount(raw: Any) -> int | None:
    if raw is None: return None
    if isinstance(raw, bool): raise CaseServiceError("OpenDART minority-interest amount invalid / OpenDART 비지배지분 금액 오류")
    if isinstance(raw, int): return raw
    if not isinstance(raw, str): raise CaseServiceError("OpenDART minority-interest amount format invalid / OpenDART 비지배지분 금액형식 오류")
    text = raw.strip()
    if text in {"", "-"}: return None
    negative = text.startswith("(") and text.endswith(")")
    if negative: text = text[1:-1].strip()
    compact = text.replace(",", "")
    if not re.fullmatch(r"[-+]?[0-9]+", compact): raise CaseServiceError("OpenDART minority-interest amount malformed / OpenDART 비지배지분 숫자형식 오류")
    value = int(compact)
    return -abs(value) if negative else value


def _seal(candidate: dict[str, Any]) -> dict[str, Any]:
    candidate["candidate_sha256"] = _sha(_without(candidate, "candidate_sha256"))
    validate_minority_interest_candidate(candidate)
    return candidate


def extract_sec_minority_interest_candidate(snapshot: dict[str, Any], *, form: str | None = None, period_end: str | None = None) -> dict[str, Any]:
    validation = sec_live.validate_source_snapshot(snapshot)
    requested_form = form.upper() if form else None
    if requested_form and requested_form not in SEC_FORMS: raise CaseServiceError("SEC form not allowed / SEC form 오류")
    requested_end = _date(period_end, "period_end").isoformat() if period_end else None
    payload = json.loads(snapshot["raw_text"])
    facts = payload.get("facts", {})
    taxonomy, concept = SEC_CONCEPT
    concept_obj = facts.get(taxonomy, {}).get(concept) if isinstance(facts.get(taxonomy), dict) else None
    units = concept_obj.get("units") if isinstance(concept_obj, dict) else None
    series = units.get("USD") if isinstance(units, dict) else None
    if not isinstance(series, list):
        raise CaseServiceError("exact SEC noncontrolling-interest concept unavailable / 정확한 SEC 비지배지분 concept 없음")
    candidates: list[dict[str, Any]] = []
    for raw in series:
        if not isinstance(raw, dict) or raw.get("form") not in SEC_FORMS: continue
        if requested_form and raw.get("form") != requested_form: continue
        if raw.get("start") not in (None, ""): continue  # instant fact only
        end = raw.get("end")
        try: canonical_end = _date(end, "SEC minority-interest end").isoformat()
        except CaseServiceError: continue
        if requested_end and canonical_end != requested_end: continue
        filed = raw.get("filed")
        try: canonical_filed = _date(filed, "SEC minority-interest filed").isoformat()
        except CaseServiceError: continue
        accn = raw.get("accn")
        if not isinstance(accn, str) or not sec_live.ACCESSION_RE.fullmatch(accn) or "val" not in raw: continue
        _number(raw["val"], "SEC minority interest")
        item = copy.deepcopy(raw); item["end"] = canonical_end; item["filed"] = canonical_filed; candidates.append(item)
    if not candidates:
        raise CaseServiceError("no exact SEC minority-interest fact matches filters / 정확한 SEC 비지배지분 fact 없음")
    latest_filed = max(x["filed"] for x in candidates)
    top = [x for x in candidates if x["filed"] == latest_filed]
    latest_end = max(x["end"] for x in top)
    top = [x for x in top if x["end"] == latest_end]
    distinct = {json.dumps(x["val"], sort_keys=True, allow_nan=False) for x in top}
    if len(distinct) != 1: raise CaseServiceError("equal-precedence SEC minority-interest facts conflict / 동일 우선순위 SEC 비지배지분 fact 충돌")
    chosen = sorted(top, key=lambda x: (str(x.get("accn", "")), str(x.get("form", ""))), reverse=True)[0]
    return _seal({
        "schema_version": CANDIDATE_SCHEMA, "status": "MINORITY_INTEREST_EVIDENCE_CANDIDATE", "canonical": False, "class": "FACT_CANDIDATE", "metric": METRIC,
        "value": chosen["val"], "unit": "USD", "entity": {"id": f"SEC_CIK:{validation['cik']}", "financial_scope": "CFS"},
        "period": {"end": chosen["end"], "date_precision": "EXACT", "report_stage": None, "report_stage_ordinal": None},
        "source_adapter": "SEC_COMPANYFACTS_EXACT", "source_identity": {"taxonomy": taxonomy, "concept": concept, "form": chosen["form"], "accession": chosen["accn"], "filed": chosen["filed"]},
        "source": {"publisher": sec_live.SEC_PUBLISHER, "source_type": sec_live.SEC_SOURCE_TYPE, "tier": sec_live.SEC_TIER, "locator": snapshot["source"]["final_locator"], "snapshot_sha256": snapshot["snapshot_sha256"], "body_sha256": snapshot["response"]["body_sha256"]},
        "selection": {"rule": "EXACT_CONCEPT_THEN_LATEST_FILED_THEN_LATEST_END", "equal_precedence_count": len(top)}, "candidate_sha256": "",
    })


def extract_dart_minority_interest_candidate(snapshot: dict[str, Any]) -> dict[str, Any]:
    validation = dart_live.validate_dart_snapshot(snapshot)
    if validation["fs_div"] != "CFS": raise CaseServiceError("OpenDART minority interest requires consolidated CFS / OpenDART 비지배지분은 연결 CFS 필요")
    payload = json.loads(snapshot["raw_text"]); rows = payload.get("list")
    if not isinstance(rows, list): raise CaseServiceError("OpenDART minority-interest rows missing / OpenDART 비지배지분 row 누락")
    selected = [r for r in rows if isinstance(r, dict) and str(r.get("sj_div", "")).upper() == "BS" and r.get("account_id") == DART_ACCOUNT_ID]
    if not selected: raise CaseServiceError("exact OpenDART noncontrolling-interest account unavailable / 정확한 OpenDART 비지배지분 account 없음")
    values = {_parse_dart_amount(r.get("thstrm_amount")) for r in selected}
    non_null = {v for v in values if v is not None}
    if len(non_null) != 1: raise CaseServiceError("OpenDART minority-interest rows missing/conflicting / OpenDART 비지배지분 row 공란·충돌")
    value = next(iter(non_null)); _number(value, "OpenDART minority interest")
    chosen = sorted(selected, key=lambda r: (str(r.get("rcept_no", "")), str(r.get("ord", ""))), reverse=True)[0]
    stage, ordinal = DART_STAGE[validation["reprt_code"]]
    currency = chosen.get("currency") or "KRW"
    return _seal({
        "schema_version": CANDIDATE_SCHEMA, "status": "MINORITY_INTEREST_EVIDENCE_CANDIDATE", "canonical": False, "class": "FACT_CANDIDATE", "metric": METRIC,
        "value": value, "unit": currency, "entity": {"id": f"DART_CORP:{validation['corp_code']}", "financial_scope": "CFS"},
        "period": {"end": None, "date_precision": "REPORT_STAGE_ONLY", "report_stage": stage, "report_stage_ordinal": ordinal, "bsns_year": validation["bsns_year"], "reprt_code": validation["reprt_code"]},
        "source_adapter": "OPENDART_EXACT_ACCOUNT", "source_identity": {"account_id": DART_ACCOUNT_ID, "account_nm": chosen.get("account_nm"), "rcept_no": chosen.get("rcept_no")},
        "source": {"publisher": dart_live.DART_PUBLISHER, "source_type": dart_live.DART_SOURCE_TYPE, "tier": dart_live.DART_TIER, "locator": snapshot["source"]["final_locator"], "snapshot_sha256": snapshot["snapshot_sha256"], "body_sha256": snapshot["response"]["body_sha256"]},
        "selection": {"rule": "EXACT_ACCOUNT_ID_ONLY", "equal_precedence_count": len(selected)}, "candidate_sha256": "",
    })


def validate_minority_interest_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(candidate, dict) or candidate.get("schema_version") != CANDIDATE_SCHEMA or candidate.get("status") != "MINORITY_INTEREST_EVIDENCE_CANDIDATE" or candidate.get("canonical") is not False or candidate.get("class") != "FACT_CANDIDATE" or candidate.get("metric") != METRIC:
        raise CaseServiceError("minority-interest candidate schema/status invalid / 비지배지분 candidate 스키마·상태 오류")
    _number(candidate.get("value"), "minority interest")
    if not isinstance(candidate.get("unit"), str) or not candidate["unit"]: raise CaseServiceError("minority-interest unit required / 비지배지분 단위 필요")
    entity, period, source = candidate.get("entity"), candidate.get("period"), candidate.get("source")
    if not all(isinstance(x, dict) for x in (entity, period, source)): raise CaseServiceError("minority-interest candidate structure incomplete / 비지배지분 candidate 구조 불완전")
    _text(entity.get("id"), "entity.id", 200)
    if entity.get("financial_scope") != "CFS": raise CaseServiceError("minority interest requires consolidated CFS / 비지배지분은 연결 CFS 필요")
    precision = period.get("date_precision")
    if precision == "EXACT":
        _date(period.get("end"), "period.end")
        if period.get("report_stage") is not None: raise CaseServiceError("EXACT period cannot carry report stage / EXACT 기간의 report stage 불가")
    elif precision == "REPORT_STAGE_ONLY":
        if period.get("end") is not None or period.get("report_stage") not in {"Q1", "H1", "Q3", "FY"}: raise CaseServiceError("REPORT_STAGE_ONLY minority-interest period invalid / REPORT_STAGE_ONLY 비지배지분 기간 오류")
    else: raise CaseServiceError("minority-interest date precision invalid / 비지배지분 날짜정밀도 오류")
    for field in ("publisher", "source_type", "tier", "locator", "snapshot_sha256", "body_sha256"):
        if field not in source: raise CaseServiceError("minority-interest provenance incomplete / 비지배지분 출처 불완전")
    if source.get("tier") != "A": raise CaseServiceError("minority-interest source must be Tier A in v0.1 / M28 v0.1 비지배지분은 Tier A 필요")
    for field in ("snapshot_sha256", "body_sha256"):
        if not isinstance(source.get(field), str) or not SHA_RE.fullmatch(source[field]): raise CaseServiceError("minority-interest source SHA invalid / 비지배지분 source SHA 오류")
    expected = _sha(_without(candidate, "candidate_sha256"))
    if candidate.get("candidate_sha256") != expected: raise CaseServiceError("minority-interest candidate SHA mismatch / 비지배지분 candidate SHA 불일치")
    return {"status": "PASS_MINORITY_INTEREST_CANDIDATE_VALIDATION", "candidate_sha256": expected, "date_precision": precision}


def normalize_minority_interest_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    validate_minority_interest_candidate(candidate)
    observation = {
        "schema_version": OBSERVATION_SCHEMA, "status": "MINORITY_INTEREST_NORMALIZED", "canonical": False, "class": "NORMALIZED_FACT_CANDIDATE", "metric": METRIC,
        "value": candidate["value"], "unit": candidate["unit"], "entity": copy.deepcopy(candidate["entity"]), "period": copy.deepcopy(candidate["period"]),
        "source": copy.deepcopy(candidate["source"]), "source_adapter": candidate["source_adapter"], "source_identity": copy.deepcopy(candidate["source_identity"]),
        "source_candidate_sha256": candidate["candidate_sha256"], "candidate": copy.deepcopy(candidate), "observation_sha256": "",
    }
    observation["observation_sha256"] = _sha(_without(observation, "observation_sha256")); validate_minority_interest_observation(observation); return observation


def validate_minority_interest_observation(observation: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(observation, dict) or observation.get("schema_version") != OBSERVATION_SCHEMA or observation.get("status") != "MINORITY_INTEREST_NORMALIZED" or observation.get("canonical") is not False or observation.get("class") != "NORMALIZED_FACT_CANDIDATE" or observation.get("metric") != METRIC:
        raise CaseServiceError("minority-interest observation schema/status invalid / 비지배지분 observation 스키마·상태 오류")
    candidate = observation.get("candidate")
    if not isinstance(candidate, dict): raise CaseServiceError("minority-interest source candidate missing / 비지배지분 source candidate 누락")
    validate_minority_interest_candidate(candidate)
    for key in ("value", "unit", "entity", "period", "source", "source_adapter", "source_identity"):
        if observation.get(key) != candidate.get(key): raise CaseServiceError("minority-interest normalization projection mismatch / 비지배지분 정규화 투영 불일치")
    if observation.get("source_candidate_sha256") != candidate.get("candidate_sha256"): raise CaseServiceError("minority-interest candidate lineage mismatch / 비지배지분 candidate lineage 불일치")
    expected = _sha(_without(observation, "observation_sha256"))
    if observation.get("observation_sha256") != expected: raise CaseServiceError("minority-interest observation SHA mismatch / 비지배지분 observation SHA 불일치")
    return {"status": "PASS_MINORITY_INTEREST_OBSERVATION_VALIDATION", "observation_sha256": expected}


def _resolve_end(observation: dict[str, Any], asserted_period_end: str | None) -> tuple[str, str]:
    period = observation["period"]
    if period["date_precision"] == "EXACT":
        if asserted_period_end is not None: raise CaseServiceError("EXACT minority interest must not be overridden / EXACT 비지배지분 날짜 덮어쓰기 불가")
        return _date(period["end"], "period.end").isoformat(), "SOURCE_EXACT"
    if asserted_period_end is None: raise CaseServiceError("REPORT_STAGE_ONLY minority interest requires human date assertion / REPORT_STAGE_ONLY 비지배지분은 인간 날짜승인 필요")
    return _date(asserted_period_end, "asserted_period_end").isoformat(), "HUMAN_DATE_ASSERTION"


def _freshness(period_end: str, as_of: str, max_age_days: int) -> dict[str, Any]:
    if isinstance(max_age_days, bool) or not isinstance(max_age_days, int) or not 0 <= max_age_days <= 3650: raise CaseServiceError("minority-interest max_age_days out of range / 비지배지분 max_age_days 범위 오류")
    age = (_date(as_of, "as_of") - _date(period_end, "resolved_period_end")).days
    if age < 0: raise CaseServiceError("minority-interest period end after as_of / 비지배지분 기간말이 as_of 이후")
    return {"status": FRESH if age <= max_age_days else STALE_BLOCKED, "age_days": age, "max_age_days": max_age_days}


def build_minority_interest_review_assertion(observation: dict[str, Any], *, as_of: str, reviewer: str, approved_at: str, review_basis: str, asserted_period_end: str | None = None, max_age_days: int = 550) -> dict[str, Any]:
    validate_minority_interest_observation(observation)
    approved = _timestamp(approved_at, "approved_at"); _text(reviewer, "reviewer", 160); _text(review_basis, "review_basis", 4000)
    resolved_end, method = _resolve_end(observation, asserted_period_end)
    if _date(resolved_end, "resolved_period_end") > approved.date(): raise CaseServiceError("minority-interest period end cannot follow approval / 비지배지분 기간말이 승인일 이후일 수 없음")
    freshness = _freshness(resolved_end, as_of, max_age_days)
    assertion = {
        "schema_version": REVIEW_SCHEMA, "status": "MINORITY_INTEREST_REVIEW_APPROVED", "canonical": False, "decision": "APPROVE_MINORITY_INTEREST_FACT",
        "source_observation_sha256": observation["observation_sha256"], "source_snapshot_sha256": observation["source"]["snapshot_sha256"],
        "entity": copy.deepcopy(observation["entity"]), "value": observation["value"], "unit": observation["unit"], "source_period": copy.deepcopy(observation["period"]),
        "resolved_period_end": resolved_end, "date_resolution": method, "as_of": as_of, "freshness": freshness,
        "reviewer": reviewer.strip(), "approved_at": approved.isoformat(), "review_basis": review_basis.strip(), "assertion_sha256": "",
    }
    assertion["assertion_sha256"] = _sha(_without(assertion, "assertion_sha256")); validate_minority_interest_review_assertion(assertion, observation); return assertion


def validate_minority_interest_review_assertion(assertion: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    validate_minority_interest_observation(observation)
    if not isinstance(assertion, dict) or assertion.get("schema_version") != REVIEW_SCHEMA or assertion.get("status") != "MINORITY_INTEREST_REVIEW_APPROVED" or assertion.get("canonical") is not False or assertion.get("decision") != "APPROVE_MINORITY_INTEREST_FACT": raise CaseServiceError("minority-interest review schema/status invalid / 비지배지분 검토 스키마·상태 오류")
    if assertion.get("source_observation_sha256") != observation["observation_sha256"] or assertion.get("source_snapshot_sha256") != observation["source"]["snapshot_sha256"]: raise CaseServiceError("minority-interest review lineage mismatch / 비지배지분 검토 lineage 불일치")
    if assertion.get("entity") != observation["entity"] or assertion.get("value") != observation["value"] or assertion.get("unit") != observation["unit"] or assertion.get("source_period") != observation["period"]: raise CaseServiceError("minority-interest review projection mismatch / 비지배지분 검토 투영 불일치")
    method = assertion.get("date_resolution")
    if observation["period"]["date_precision"] == "EXACT":
        expected_end, expected_method = _resolve_end(observation, None)
    else:
        expected_end, expected_method = _resolve_end(observation, assertion.get("resolved_period_end"))
    if assertion.get("resolved_period_end") != expected_end or method != expected_method: raise CaseServiceError("minority-interest date resolution mismatch / 비지배지분 날짜해결 불일치")
    approved = _timestamp(assertion.get("approved_at"), "approved_at")
    if _date(expected_end, "resolved_period_end") > approved.date(): raise CaseServiceError("minority-interest approval chronology invalid / 비지배지분 승인 시간관계 오류")
    _text(assertion.get("reviewer"), "reviewer", 160); _text(assertion.get("review_basis"), "review_basis", 4000)
    expected_freshness = _freshness(expected_end, assertion.get("as_of"), assertion.get("freshness", {}).get("max_age_days"))
    if assertion.get("freshness") != expected_freshness: raise CaseServiceError("minority-interest freshness mismatch / 비지배지분 최신성 불일치")
    expected = _sha(_without(assertion, "assertion_sha256"))
    if assertion.get("assertion_sha256") != expected: raise CaseServiceError("minority-interest review SHA mismatch / 비지배지분 검토 SHA 불일치")
    return {"status": "PASS_MINORITY_INTEREST_REVIEW_VALIDATION", "assertion_sha256": expected, "freshness": expected_freshness["status"]}


def finalize_reviewed_minority_interest(observation: dict[str, Any], assertion: dict[str, Any]) -> dict[str, Any]:
    validate_minority_interest_observation(observation); checked = validate_minority_interest_review_assertion(assertion, observation)
    package = {
        "schema_version": PACKAGE_SCHEMA, "status": "MINORITY_INTEREST_FACT_REVIEWED", "canonical": False, "class": "NORMALIZED_FACT", "metric": METRIC,
        "value": observation["value"], "unit": observation["unit"], "entity": copy.deepcopy(observation["entity"]), "as_of": assertion["as_of"],
        "resolved_period_end": assertion["resolved_period_end"], "date_resolution": assertion["date_resolution"], "freshness": copy.deepcopy(assertion["freshness"]),
        "source": copy.deepcopy(observation["source"]), "observation": copy.deepcopy(observation), "review_assertion": copy.deepcopy(assertion),
        "binding_eligibility": {"eligible": checked["freshness"] == FRESH, "reason": "REVIEWED_FRESH_MINORITY_INTEREST_FACT" if checked["freshness"] == FRESH else "STALE_MINORITY_INTEREST"}, "package_sha256": "",
    }
    package["package_sha256"] = _sha(_without(package, "package_sha256")); validate_reviewed_minority_interest(package); return package


def validate_reviewed_minority_interest(package: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(package, dict) or package.get("schema_version") != PACKAGE_SCHEMA or package.get("status") != "MINORITY_INTEREST_FACT_REVIEWED" or package.get("canonical") is not False or package.get("class") != "NORMALIZED_FACT" or package.get("metric") != METRIC: raise CaseServiceError("reviewed minority-interest schema/status invalid / 검토완료 비지배지분 스키마·상태 오류")
    observation, assertion = package.get("observation"), package.get("review_assertion")
    if not isinstance(observation, dict) or not isinstance(assertion, dict): raise CaseServiceError("reviewed minority-interest lineage missing / 검토완료 비지배지분 lineage 누락")
    validate_minority_interest_observation(observation); checked = validate_minority_interest_review_assertion(assertion, observation)
    projection = {"value": observation["value"], "unit": observation["unit"], "entity": observation["entity"], "as_of": assertion["as_of"], "resolved_period_end": assertion["resolved_period_end"], "date_resolution": assertion["date_resolution"], "freshness": assertion["freshness"], "source": observation["source"]}
    for key, value in projection.items():
        if package.get(key) != value: raise CaseServiceError("reviewed minority-interest projection mismatch / 검토완료 비지배지분 투영 불일치")
    eligible = checked["freshness"] == FRESH; reason = "REVIEWED_FRESH_MINORITY_INTEREST_FACT" if eligible else "STALE_MINORITY_INTEREST"
    if package.get("binding_eligibility") != {"eligible": eligible, "reason": reason}: raise CaseServiceError("minority-interest eligibility mismatch / 비지배지분 적격성 불일치")
    expected = _sha(_without(package, "package_sha256"))
    if package.get("package_sha256") != expected: raise CaseServiceError("reviewed minority-interest package SHA mismatch / 검토완료 비지배지분 패키지 SHA 불일치")
    return {"status": "PASS_REVIEWED_MINORITY_INTEREST_VALIDATION", "package_sha256": expected, "eligible": eligible, "value": package["value"]}
