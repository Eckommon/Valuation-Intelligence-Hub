"""M22 valuation-date common-share base + diluted-share bridge foundation.

Current common shares are an instant base, not fully diluted shares. Historical
M21 weighted-average dilution is reference-only and never creates an adjustment.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import date, datetime
from math import isfinite
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.sec_live import ACCESSION_RE, validate_source_snapshot
from valuation_hub.share_dilution import validate_historical_dilution

CANDIDATE_SCHEMA = "current-common-shares-candidate-v0.1"
CANDIDATE_STATUS = "CURRENT_COMMON_SHARES_CANDIDATE_UNREVIEWED"
OBSERVATION_SCHEMA = "current-common-shares-observation-v0.1"
OBSERVATION_STATUS = "CURRENT_COMMON_SHARES_OBSERVATION_NORMALIZED"
CONTEXT_SCHEMA = "valuation-share-base-context-v0.1"
CONTEXT_STATUS = "VALUATION_SHARE_BASE_CONTEXT_EVALUATED"
ADJUSTMENT_SCHEMA = "dilution-adjustment-v0.1"
ADJUSTMENT_STATUS = "DILUTION_ADJUSTMENT_EVIDENCE"
ASSERTION_SCHEMA = "dilution-coverage-assertion-v0.1"
ASSERTION_STATUS = "DILUTION_COVERAGE_ASSERTED"
BRIDGE_SCHEMA = "diluted-share-bridge-v0.1"
BRIDGE_STATUS = "DILUTED_SHARE_BRIDGE_EVALUATED"
FRESH = "FRESH"
STALE_BLOCKED = "STALE_BLOCKED"
BASE_ONLY = "BASE_ONLY"
PARTIAL = "PARTIAL_DILUTION_COVERAGE"
COMPLETE = "COMPLETE_REVIEWED_DILUTION_COVERAGE"
CONFLICT = "CONFLICT_BLOCKED"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
CONCEPT = "EntityCommonStockSharesOutstanding"
ALLOWED_FORMS = frozenset({"10-Q", "10-Q/A", "10-K", "10-K/A"})
ADJUSTMENT_CATEGORIES = (
    "options_treasury_stock_method",
    "rsu_restricted_stock",
    "warrants",
    "convertibles_if_converted",
    "contingent_shares",
    "other_explicit",
)


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    out = copy.deepcopy(value); out.pop(key, None); return out


def _iso(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise CaseServiceError(f"{field} date required / {field} 날짜 필요")
    try: parsed = date.fromisoformat(value)
    except ValueError as exc: raise CaseServiceError(f"{field} invalid / {field} 날짜 오류") from exc
    if parsed.isoformat() != value:
        raise CaseServiceError(f"{field} canonical YYYY-MM-DD required / {field} 정규 날짜 필요")
    return value


def _timestamp(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise CaseServiceError(f"{field} timezone-aware timestamp required / {field} 시간대 포함 시각 필요")
    try: parsed = datetime.fromisoformat(value)
    except ValueError as exc: raise CaseServiceError(f"{field} ISO timestamp invalid / {field} 시각 오류") from exc
    if parsed.tzinfo is None:
        raise CaseServiceError(f"{field} timezone required / {field} 시간대 필요")
    return parsed.isoformat()


def _num(value: Any, field: str, *, positive: bool = False) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
        raise CaseServiceError(f"{field} finite numeric required / {field} 유한 숫자 필요")
    if positive and value <= 0:
        raise CaseServiceError(f"{field} must be > 0 / {field} 0 초과 필요")
    if not positive and value < 0:
        raise CaseServiceError(f"{field} must be nonnegative / {field} 음수 불가")
    return value


def _source_class(value: Any) -> str:
    if value == "FACT": return "NORMALIZED_FACT"
    if value == "FACT_CANDIDATE": return "NORMALIZED_FACT_CANDIDATE"
    raise CaseServiceError("share source class must be FACT or FACT_CANDIDATE / 주식수 source class 오류")


def extract_sec_current_common_shares_candidate(snapshot: dict[str, Any], *, period_end: str, form: str | None = None) -> dict[str, Any]:
    validation = validate_source_snapshot(snapshot)
    end = _iso(period_end, "period_end")
    requested_form = form.upper() if form else None
    if requested_form is not None and requested_form not in ALLOWED_FORMS:
        raise CaseServiceError("unsupported SEC form for current shares / 현재주식수 SEC form 오류")
    payload = json.loads(snapshot["raw_text"])
    facts = payload.get("facts", {}); dei = facts.get("dei", {}) if isinstance(facts, dict) else {}
    obj = dei.get(CONCEPT) if isinstance(dei, dict) else None
    units = obj.get("units") if isinstance(obj, dict) else None
    series = units.get("shares") if isinstance(units, dict) else None
    if not isinstance(series, list):
        raise CaseServiceError("SEC current common shares concept unavailable / SEC 현재 보통주수 concept 없음")
    candidates: list[dict[str, Any]] = []
    for raw in series:
        if not isinstance(raw, dict) or raw.get("end") != end or "start" in raw:
            continue
        raw_form = raw.get("form")
        if raw_form not in ALLOWED_FORMS or (requested_form and raw_form != requested_form):
            continue
        filed, accn = raw.get("filed"), raw.get("accn")
        if not isinstance(filed, str) or not isinstance(accn, str) or not ACCESSION_RE.fullmatch(accn) or "val" not in raw:
            continue
        _iso(filed, "filed")
        candidates.append(copy.deepcopy(raw))
    if not candidates:
        raise CaseServiceError("no exact SEC current-share fact for requested instant / 요청 시점과 일치하는 SEC 현재주식수 fact 없음")
    latest_filed = max(item["filed"] for item in candidates)
    top = [item for item in candidates if item["filed"] == latest_filed]
    distinct = {json.dumps(item.get("val"), sort_keys=True, allow_nan=False) for item in top}
    if len(distinct) != 1:
        raise CaseServiceError("ambiguous equal-precedence SEC current-share values / 동일 우선순위 SEC 현재주식수 값 충돌")
    chosen = sorted(top, key=lambda x: (str(x.get("accn", "")), str(x.get("form", "")), str(x.get("frame", ""))), reverse=True)[0]
    candidate = {
        "schema_version": CANDIDATE_SCHEMA, "status": CANDIDATE_STATUS, "canonical": False, "class": "FACT_CANDIDATE",
        "metric": "current_common_shares", "value": chosen["val"], "unit": "shares",
        "entity": {"id": f"SEC_CIK:{validation['cik']}", "source_system": "SEC", "financial_scope": "AS_REPORTED"},
        "period": {"kind": "INSTANT", "start": None, "end": end, "date_precision": "EXACT"},
        "filing": {"accession": chosen["accn"], "form": chosen["form"], "filed": chosen["filed"]},
        "taxonomy": "dei", "concept": CONCEPT,
        "source": {"publisher": "U.S. Securities and Exchange Commission", "source_type": "official_edgar_companyfacts_api", "tier_proposal": "A", "locator": snapshot["source"]["final_locator"], "snapshot_sha256": snapshot["snapshot_sha256"], "body_sha256": snapshot["response"]["body_sha256"]},
        "selection": {"rule": "EXACT_INSTANT_THEN_LATEST_FILED", "requested_end": end, "requested_form": requested_form, "equal_precedence_count": len(top)},
        "semantic_boundary": {"current_common_shares_only": True, "fully_diluted_shares": False},
        "candidate_sha256": "",
    }
    candidate["candidate_sha256"] = _sha(_without(candidate, "candidate_sha256")); validate_current_common_shares_candidate(candidate); return candidate


def validate_current_common_shares_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(candidate, dict) or candidate.get("schema_version") != CANDIDATE_SCHEMA or candidate.get("status") != CANDIDATE_STATUS or candidate.get("canonical") is not False:
        raise CaseServiceError("current-share candidate schema/status invalid / 현재주식수 candidate 스키마·상태 오류")
    if candidate.get("metric") != "current_common_shares" or candidate.get("unit") != "shares" or candidate.get("taxonomy") != "dei" or candidate.get("concept") != CONCEPT:
        raise CaseServiceError("current-share candidate semantics invalid / 현재주식수 candidate 의미 오류")
    _source_class(candidate.get("class")); _num(candidate.get("value"), "current common shares", positive=True)
    period, filing, source, selection = candidate.get("period"), candidate.get("filing"), candidate.get("source"), candidate.get("selection")
    if not all(isinstance(x, dict) for x in (period, filing, source, selection)):
        raise CaseServiceError("current-share candidate provenance incomplete / 현재주식수 candidate 출처정보 불완전")
    if period != {"kind": "INSTANT", "start": None, "end": period.get("end"), "date_precision": "EXACT"}:
        raise CaseServiceError("current-share candidate period must be exact instant / 현재주식수 candidate 기간은 정확시점이어야 함")
    end = _iso(period.get("end"), "period.end")
    if selection.get("rule") != "EXACT_INSTANT_THEN_LATEST_FILED" or selection.get("requested_end") != end:
        raise CaseServiceError("current-share selection/period mismatch / 현재주식수 selection·기간 불일치")
    if filing.get("form") not in ALLOWED_FORMS or not isinstance(filing.get("accession"), str) or not ACCESSION_RE.fullmatch(filing["accession"]):
        raise CaseServiceError("current-share filing invalid / 현재주식수 filing 오류")
    _iso(filing.get("filed"), "filing.filed")
    for key in ("snapshot_sha256", "body_sha256"):
        if not isinstance(source.get(key), str) or not SHA256_RE.fullmatch(source[key]):
            raise CaseServiceError("current-share source SHA invalid / 현재주식수 source SHA 오류")
    if candidate.get("semantic_boundary") != {"current_common_shares_only": True, "fully_diluted_shares": False}:
        raise CaseServiceError("current-share semantic boundary invalid / 현재주식수 의미경계 오류")
    expected = _sha(_without(candidate, "candidate_sha256"))
    if candidate.get("candidate_sha256") != expected:
        raise CaseServiceError("current-share candidate SHA mismatch / 현재주식수 candidate SHA 불일치")
    return {"status": "PASS_CURRENT_COMMON_SHARES_CANDIDATE_VALIDATION", "candidate_sha256": expected}


def normalize_current_common_shares_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    validate_current_common_shares_candidate(candidate)
    result = {
        "schema_version": OBSERVATION_SCHEMA, "status": OBSERVATION_STATUS, "canonical": False, "class": _source_class(candidate["class"]),
        "metric": "current_common_shares", "value": candidate["value"], "unit": "shares", "entity": copy.deepcopy(candidate["entity"]), "period": copy.deepcopy(candidate["period"]),
        "lineage": {"normalization_rule": "SEC_DEI_CURRENT_COMMON_SHARES_INSTANT_V01", "source_candidate_sha256": candidate["candidate_sha256"], "source_class": candidate["class"], "source_snapshot_sha256": candidate["source"]["snapshot_sha256"], "source_body_sha256": candidate["source"]["body_sha256"], "filing_identity": copy.deepcopy(candidate["filing"]), "source_detail": {"taxonomy": "dei", "concept": CONCEPT}},
        "semantic_boundary": {"current_common_shares_only": True, "fully_diluted_shares": False}, "observation_sha256": "",
    }
    result["observation_sha256"] = _sha(_without(result, "observation_sha256")); validate_current_common_shares_observation(result); return result


def validate_current_common_shares_observation(obs: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(obs, dict) or obs.get("schema_version") != OBSERVATION_SCHEMA or obs.get("status") != OBSERVATION_STATUS or obs.get("canonical") is not False:
        raise CaseServiceError("current-share observation schema/status invalid / 현재주식수 observation 스키마·상태 오류")
    if obs.get("class") not in {"NORMALIZED_FACT", "NORMALIZED_FACT_CANDIDATE"} or obs.get("metric") != "current_common_shares" or obs.get("unit") != "shares":
        raise CaseServiceError("current-share observation semantics invalid / 현재주식수 observation 의미 오류")
    _num(obs.get("value"), "current common shares", positive=True)
    period, lineage = obs.get("period"), obs.get("lineage")
    if not isinstance(period, dict) or period.get("kind") != "INSTANT" or period.get("start") is not None or period.get("date_precision") != "EXACT":
        raise CaseServiceError("current-share observation must be exact INSTANT / 현재주식수 observation은 정확 INSTANT 필요")
    _iso(period.get("end"), "period.end")
    if not isinstance(lineage, dict) or lineage.get("normalization_rule") != "SEC_DEI_CURRENT_COMMON_SHARES_INSTANT_V01":
        raise CaseServiceError("current-share lineage invalid / 현재주식수 lineage 오류")
    for key in ("source_candidate_sha256", "source_snapshot_sha256", "source_body_sha256"):
        if not isinstance(lineage.get(key), str) or not SHA256_RE.fullmatch(lineage[key]):
            raise CaseServiceError("current-share lineage SHA invalid / 현재주식수 lineage SHA 오류")
    if obs.get("semantic_boundary") != {"current_common_shares_only": True, "fully_diluted_shares": False}:
        raise CaseServiceError("current-share observation boundary invalid / 현재주식수 observation 경계 오류")
    expected = _sha(_without(obs, "observation_sha256"))
    if obs.get("observation_sha256") != expected:
        raise CaseServiceError("current-share observation SHA mismatch / 현재주식수 observation SHA 불일치")
    return {"status": "PASS_CURRENT_COMMON_SHARES_OBSERVATION_VALIDATION", "observation_sha256": expected, "class": obs["class"]}


def _freshness(end: str, as_of: str, max_age_days: int) -> dict[str, Any]:
    end_date = date.fromisoformat(_iso(end, "period.end")); as_of_date = date.fromisoformat(_iso(as_of, "as_of"))
    if isinstance(max_age_days, bool) or not isinstance(max_age_days, int) or not 0 <= max_age_days <= 3650:
        raise CaseServiceError("max_age_days out of range / max_age_days 범위 오류")
    age = (as_of_date - end_date).days
    if age < 0: raise CaseServiceError("share instant is after as_of / 주식수 시점이 as_of 이후")
    return {"status": FRESH if age <= max_age_days else STALE_BLOCKED, "age_days": age, "max_age_days": max_age_days}


def build_valuation_share_base_context(obs: dict[str, Any], *, as_of: str, max_age_days: int = 180) -> dict[str, Any]:
    validate_current_common_shares_observation(obs)
    if obs["class"] != "NORMALIZED_FACT":
        raise CaseServiceError("valuation share base requires reviewed fact / 가치평가 주식기준은 검토완료 fact 필요")
    freshness = _freshness(obs["period"]["end"], as_of, max_age_days)
    result = {
        "schema_version": CONTEXT_SCHEMA, "status": CONTEXT_STATUS, "canonical": False, "class": "NORMALIZED_FACT",
        "metric": "current_common_shares", "value": obs["value"], "unit": "shares", "entity": copy.deepcopy(obs["entity"]), "source_period": copy.deepcopy(obs["period"]),
        "policy": {"version": "VALUATION_SHARE_BASE_V01", "as_of": as_of, "max_age_days": max_age_days}, "freshness": freshness,
        "semantic_boundary": {"current_common_shares_base": True, "fully_diluted_shares": False, "direct_bind_to_diluted_shares": False},
        "source_observation_sha256": obs["observation_sha256"], "context_sha256": "",
    }
    result["context_sha256"] = _sha(_without(result, "context_sha256")); validate_valuation_share_base_context(result, observation=obs); return result


def validate_valuation_share_base_context(context: dict[str, Any], *, observation: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(context, dict) or context.get("schema_version") != CONTEXT_SCHEMA or context.get("status") != CONTEXT_STATUS or context.get("canonical") is not False:
        raise CaseServiceError("valuation share context schema/status invalid / 가치평가 주식 context 스키마·상태 오류")
    if context.get("class") != "NORMALIZED_FACT" or context.get("metric") != "current_common_shares" or context.get("unit") != "shares":
        raise CaseServiceError("valuation share context semantics invalid / 가치평가 주식 context 의미 오류")
    _num(context.get("value"), "current common shares", positive=True)
    policy, period = context.get("policy"), context.get("source_period")
    if not isinstance(policy, dict) or policy.get("version") != "VALUATION_SHARE_BASE_V01" or not isinstance(period, dict):
        raise CaseServiceError("valuation share context policy/period invalid / 가치평가 주식 context 정책·기간 오류")
    expected_freshness = _freshness(period.get("end"), policy.get("as_of"), policy.get("max_age_days"))
    if context.get("freshness") != expected_freshness:
        raise CaseServiceError("valuation share freshness mismatch / 가치평가 주식 최신성 불일치")
    if context.get("semantic_boundary") != {"current_common_shares_base": True, "fully_diluted_shares": False, "direct_bind_to_diluted_shares": False}:
        raise CaseServiceError("valuation share context boundary invalid / 가치평가 주식 context 경계 오류")
    if not isinstance(context.get("source_observation_sha256"), str) or not SHA256_RE.fullmatch(context["source_observation_sha256"]):
        raise CaseServiceError("valuation share source SHA invalid / 가치평가 주식 source SHA 오류")
    if observation is not None:
        validate_current_common_shares_observation(observation)
        if observation["class"] != "NORMALIZED_FACT" or context["source_observation_sha256"] != observation["observation_sha256"] or context["entity"] != observation["entity"] or context["value"] != observation["value"] or context["source_period"] != observation["period"]:
            raise CaseServiceError("valuation share context/source mismatch / 가치평가 주식 context·source 불일치")
    expected = _sha(_without(context, "context_sha256"))
    if context.get("context_sha256") != expected:
        raise CaseServiceError("valuation share context SHA mismatch / 가치평가 주식 context SHA 불일치")
    return {"status": "PASS_VALUATION_SHARE_BASE_CONTEXT_VALIDATION", "context_sha256": expected, "freshness": expected_freshness["status"]}


def build_dilution_adjustment(*, adjustment_id: str, category: str, shares: int | float, source_sha256: str, source_description: str) -> dict[str, Any]:
    if not isinstance(adjustment_id, str) or not adjustment_id.strip() or len(adjustment_id) > 120:
        raise CaseServiceError("adjustment_id required / adjustment_id 필요")
    if category not in ADJUSTMENT_CATEGORIES:
        raise CaseServiceError("unsupported dilution adjustment category / 미지원 희석조정 category")
    if not isinstance(source_sha256, str) or not SHA256_RE.fullmatch(source_sha256):
        raise CaseServiceError("source_sha256 required / source_sha256 필요")
    if not isinstance(source_description, str) or not source_description.strip() or len(source_description) > 1000:
        raise CaseServiceError("source_description required / source_description 필요")
    adjustment = {
        "schema_version": ADJUSTMENT_SCHEMA, "status": ADJUSTMENT_STATUS, "canonical": False, "class": "NORMALIZED_FACT_CANDIDATE",
        "adjustment_id": adjustment_id.strip(), "category": category, "shares": _num(shares, "adjustment shares"),
        "source_sha256": source_sha256, "source_description": source_description.strip(),
        "semantic_boundary": {"explicit_only": True, "historical_factor_generated": False}, "adjustment_sha256": "",
    }
    adjustment["adjustment_sha256"] = _sha(_without(adjustment, "adjustment_sha256")); validate_dilution_adjustment(adjustment); return adjustment


def validate_dilution_adjustment(adjustment: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(adjustment, dict) or adjustment.get("schema_version") != ADJUSTMENT_SCHEMA or adjustment.get("status") != ADJUSTMENT_STATUS or adjustment.get("canonical") is not False:
        raise CaseServiceError("dilution adjustment schema/status invalid / 희석조정 스키마·상태 오류")
    if adjustment.get("class") not in {"NORMALIZED_FACT", "NORMALIZED_FACT_CANDIDATE"} or adjustment.get("category") not in ADJUSTMENT_CATEGORIES:
        raise CaseServiceError("dilution adjustment authority/category invalid / 희석조정 권위·category 오류")
    if not isinstance(adjustment.get("adjustment_id"), str) or not adjustment["adjustment_id"]:
        raise CaseServiceError("dilution adjustment id invalid / 희석조정 id 오류")
    _num(adjustment.get("shares"), "adjustment shares")
    if not isinstance(adjustment.get("source_sha256"), str) or not SHA256_RE.fullmatch(adjustment["source_sha256"]):
        raise CaseServiceError("dilution adjustment source SHA invalid / 희석조정 source SHA 오류")
    if not isinstance(adjustment.get("source_description"), str) or not adjustment["source_description"].strip():
        raise CaseServiceError("dilution adjustment source description invalid / 희석조정 source 설명 오류")
    if adjustment.get("semantic_boundary") != {"explicit_only": True, "historical_factor_generated": False}:
        raise CaseServiceError("dilution adjustment boundary invalid / 희석조정 경계 오류")
    expected = _sha(_without(adjustment, "adjustment_sha256"))
    if adjustment.get("adjustment_sha256") != expected:
        raise CaseServiceError("dilution adjustment SHA mismatch / 희석조정 SHA 불일치")
    return {"status": "PASS_DILUTION_ADJUSTMENT_VALIDATION", "adjustment_sha256": expected, "class": adjustment["class"]}


def build_dilution_coverage_assertion(base_context: dict[str, Any], adjustments: list[dict[str, Any]], *, reviewer: str, approved_at: str, coverage_basis: str, reviewed_categories: list[str]) -> dict[str, Any]:
    validate_valuation_share_base_context(base_context)
    if base_context["freshness"]["status"] != FRESH:
        raise CaseServiceError("complete coverage assertion requires fresh base / 완전 coverage 승인은 최신 base 필요")
    if not isinstance(adjustments, list): raise CaseServiceError("adjustments list required / adjustments 배열 필요")
    for item in adjustments:
        validate_dilution_adjustment(item)
        if item["class"] != "NORMALIZED_FACT":
            raise CaseServiceError("complete coverage assertion requires reviewed adjustment facts / 완전 coverage 승인은 검토완료 조정근거 필요")
    if not isinstance(reviewer, str) or not reviewer.strip() or len(reviewer) > 160:
        raise CaseServiceError("reviewer required / reviewer 필요")
    if not isinstance(coverage_basis, str) or not coverage_basis.strip() or len(coverage_basis) > 2000:
        raise CaseServiceError("coverage_basis required / coverage_basis 필요")
    if not isinstance(reviewed_categories, list) or sorted(set(reviewed_categories)) != sorted(ADJUSTMENT_CATEGORIES):
        raise CaseServiceError("all dilution categories must be explicitly reviewed / 모든 희석 category 명시검토 필요")
    approved = _timestamp(approved_at, "approved_at")
    assertion = {
        "schema_version": ASSERTION_SCHEMA, "status": ASSERTION_STATUS, "canonical": False, "decision": COMPLETE,
        "reviewer": reviewer.strip(), "approved_at": approved, "base_context_sha256": base_context["context_sha256"],
        "adjustment_sha256": sorted(item["adjustment_sha256"] for item in adjustments), "reviewed_categories": list(ADJUSTMENT_CATEGORIES),
        "coverage_basis": coverage_basis.strip(), "assertion_sha256": "",
    }
    assertion["assertion_sha256"] = _sha(_without(assertion, "assertion_sha256")); validate_dilution_coverage_assertion(assertion, base_context, adjustments); return assertion


def validate_dilution_coverage_assertion(assertion: dict[str, Any], base_context: dict[str, Any], adjustments: list[dict[str, Any]]) -> dict[str, Any]:
    validate_valuation_share_base_context(base_context)
    if not isinstance(assertion, dict) or assertion.get("schema_version") != ASSERTION_SCHEMA or assertion.get("status") != ASSERTION_STATUS or assertion.get("canonical") is not False or assertion.get("decision") != COMPLETE:
        raise CaseServiceError("dilution coverage assertion schema/status invalid / 희석 coverage 승인 스키마·상태 오류")
    if base_context["freshness"]["status"] != FRESH or assertion.get("base_context_sha256") != base_context.get("context_sha256"):
        raise CaseServiceError("dilution coverage base lock invalid / 희석 coverage base 잠금 오류")
    if not isinstance(adjustments, list): raise CaseServiceError("adjustments list required / adjustments 배열 필요")
    for item in adjustments:
        validate_dilution_adjustment(item)
        if item["class"] != "NORMALIZED_FACT": raise CaseServiceError("candidate adjustment cannot be complete coverage / 후보 조정은 완전 coverage 불가")
    expected_hashes = sorted(item["adjustment_sha256"] for item in adjustments)
    if assertion.get("adjustment_sha256") != expected_hashes or assertion.get("reviewed_categories") != list(ADJUSTMENT_CATEGORIES):
        raise CaseServiceError("dilution coverage adjustment/category lock mismatch / 희석 coverage 조정·category 잠금 불일치")
    if not isinstance(assertion.get("reviewer"), str) or not assertion["reviewer"].strip() or not isinstance(assertion.get("coverage_basis"), str) or not assertion["coverage_basis"].strip():
        raise CaseServiceError("dilution coverage reviewer/basis invalid / 희석 coverage reviewer·근거 오류")
    _timestamp(assertion.get("approved_at"), "approved_at")
    expected = _sha(_without(assertion, "assertion_sha256"))
    if assertion.get("assertion_sha256") != expected:
        raise CaseServiceError("dilution coverage assertion SHA mismatch / 희석 coverage 승인 SHA 불일치")
    return {"status": "PASS_DILUTION_COVERAGE_ASSERTION_VALIDATION", "assertion_sha256": expected}


def build_diluted_share_bridge(base_context: dict[str, Any], adjustments: list[dict[str, Any]], *, coverage_assertion: dict[str, Any] | None = None, historical_reference: dict[str, Any] | None = None) -> dict[str, Any]:
    validate_valuation_share_base_context(base_context)
    if not isinstance(adjustments, list): raise CaseServiceError("adjustments list required / adjustments 배열 필요")
    for item in adjustments: validate_dilution_adjustment(item)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in adjustments: grouped.setdefault(item["adjustment_id"], []).append(item)
    conflicts = []
    selected = []
    for adjustment_id, group in sorted(grouped.items()):
        hashes = {item["adjustment_sha256"] for item in group}
        if len(hashes) > 1:
            conflicts.append({"adjustment_id": adjustment_id, "adjustment_sha256": sorted(hashes)})
        else:
            selected.append(group[0])
    historical = None
    if historical_reference is not None:
        validate_historical_dilution(historical_reference)
        historical = {"derived_sha256": historical_reference["derived_sha256"], "historical_dilution_factor": historical_reference["historical_dilution_factor"], "reference_only": True, "auto_adjustment_created": False}
    assertion_projection = None
    if conflicts:
        coverage_status, candidate_value = CONFLICT, None
        if coverage_assertion is not None: raise CaseServiceError("coverage assertion cannot override adjustment conflict / coverage 승인은 조정충돌을 덮을 수 없음")
    else:
        if coverage_assertion is not None:
            validate_dilution_coverage_assertion(coverage_assertion, base_context, selected)
            coverage_status = COMPLETE
            assertion_projection = {"assertion_sha256": coverage_assertion["assertion_sha256"], "reviewer": coverage_assertion["reviewer"], "approved_at": coverage_assertion["approved_at"]}
        else:
            coverage_status = BASE_ONLY if not selected else PARTIAL
        candidate_value = base_context["value"] + sum(item["shares"] for item in selected)
    all_reviewed = all(item["class"] == "NORMALIZED_FACT" for item in selected)
    eligible = coverage_status == COMPLETE and base_context["freshness"]["status"] == FRESH and all_reviewed
    bridge_class = "DERIVED_FACT" if eligible else "DERIVED_FACT_CANDIDATE"
    result = {
        "schema_version": BRIDGE_SCHEMA, "status": BRIDGE_STATUS, "canonical": False, "class": bridge_class,
        "entity": copy.deepcopy(base_context["entity"]), "unit": "shares", "as_of": base_context["policy"]["as_of"],
        "base": {"current_common_shares": base_context["value"], "context_sha256": base_context["context_sha256"], "freshness": copy.deepcopy(base_context["freshness"])},
        "adjustments": [{"adjustment_id": x["adjustment_id"], "category": x["category"], "shares": x["shares"], "class": x["class"], "source_sha256": x["source_sha256"], "adjustment_sha256": x["adjustment_sha256"]} for x in selected],
        "conflicts": conflicts,
        "coverage": {"status": coverage_status, "missing_as_zero": False, "coverage_assertion": assertion_projection},
        "candidate_fully_diluted_shares": candidate_value,
        "historical_reference": historical,
        "binding_eligibility": {"eligible_for_future_direct_bind": eligible, "reason": "COMPLETE_REVIEWED_FRESH" if eligible else coverage_status},
        "semantic_boundary": {"current_common_shares_equal_fully_diluted": False, "historical_factor_auto_adjustment": False, "missing_adjustments_as_zero": False},
        "bridge_sha256": "",
    }
    result["bridge_sha256"] = _sha(_without(result, "bridge_sha256")); validate_diluted_share_bridge(result); return result


def validate_diluted_share_bridge(bridge: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(bridge, dict) or bridge.get("schema_version") != BRIDGE_SCHEMA or bridge.get("status") != BRIDGE_STATUS or bridge.get("canonical") is not False:
        raise CaseServiceError("diluted-share bridge schema/status invalid / 희석주식 bridge 스키마·상태 오류")
    if bridge.get("class") not in {"DERIVED_FACT", "DERIVED_FACT_CANDIDATE"} or bridge.get("unit") != "shares":
        raise CaseServiceError("diluted-share bridge authority/unit invalid / 희석주식 bridge 권위·unit 오류")
    base, coverage, adjustments, conflicts = bridge.get("base"), bridge.get("coverage"), bridge.get("adjustments"), bridge.get("conflicts")
    if not isinstance(base, dict) or not isinstance(coverage, dict) or not isinstance(adjustments, list) or not isinstance(conflicts, list):
        raise CaseServiceError("diluted-share bridge structure invalid / 희석주식 bridge 구조 오류")
    base_value = _num(base.get("current_common_shares"), "base current common shares", positive=True)
    if not isinstance(base.get("context_sha256"), str) or not SHA256_RE.fullmatch(base["context_sha256"]):
        raise CaseServiceError("diluted-share bridge base SHA invalid / 희석주식 bridge base SHA 오류")
    status = coverage.get("status")
    if status not in {BASE_ONLY, PARTIAL, COMPLETE, CONFLICT} or coverage.get("missing_as_zero") is not False:
        raise CaseServiceError("diluted-share bridge coverage invalid / 희석주식 bridge coverage 오류")
    seen: set[str] = set(); adjustment_sum = 0; all_reviewed = True
    for item in adjustments:
        if not isinstance(item, dict) or item.get("category") not in ADJUSTMENT_CATEGORIES or item.get("adjustment_id") in seen:
            raise CaseServiceError("diluted-share bridge adjustment invalid / 희석주식 bridge 조정 오류")
        seen.add(item["adjustment_id"]); adjustment_sum += _num(item.get("shares"), "bridge adjustment shares")
        if item.get("class") not in {"NORMALIZED_FACT", "NORMALIZED_FACT_CANDIDATE"}: raise CaseServiceError("bridge adjustment class invalid / bridge 조정 class 오류")
        all_reviewed = all_reviewed and item["class"] == "NORMALIZED_FACT"
        for key in ("source_sha256", "adjustment_sha256"):
            if not isinstance(item.get(key), str) or not SHA256_RE.fullmatch(item[key]): raise CaseServiceError("bridge adjustment SHA invalid / bridge 조정 SHA 오류")
    if status == CONFLICT:
        if bridge.get("candidate_fully_diluted_shares") is not None or not conflicts:
            raise CaseServiceError("conflict bridge must hide candidate total / 충돌 bridge는 candidate 합계 비공개 필요")
    else:
        if conflicts: raise CaseServiceError("non-conflict bridge cannot carry conflicts / 비충돌 bridge conflict 포함 불가")
        expected_value = base_value + adjustment_sum
        if _num(bridge.get("candidate_fully_diluted_shares"), "candidate fully diluted shares", positive=True) != expected_value:
            raise CaseServiceError("diluted-share bridge arithmetic mismatch / 희석주식 bridge 산술 불일치")
        if status == BASE_ONLY and adjustments: raise CaseServiceError("BASE_ONLY cannot carry adjustments / BASE_ONLY 조정 포함 불가")
        if status == PARTIAL and not adjustments: raise CaseServiceError("PARTIAL requires adjustment evidence / PARTIAL 조정근거 필요")
    assertion = coverage.get("coverage_assertion")
    if status == COMPLETE:
        if not isinstance(assertion, dict) or not isinstance(assertion.get("assertion_sha256"), str) or not SHA256_RE.fullmatch(assertion["assertion_sha256"]) or not all_reviewed:
            raise CaseServiceError("complete bridge requires reviewed coverage assertion / 완전 bridge는 검토완료 coverage 승인 필요")
    elif assertion is not None:
        raise CaseServiceError("non-complete bridge cannot carry coverage assertion / 비완전 bridge coverage 승인 불가")
    historical = bridge.get("historical_reference")
    if historical is not None and (not isinstance(historical, dict) or historical.get("reference_only") is not True or historical.get("auto_adjustment_created") is not False or not isinstance(historical.get("derived_sha256"), str) or not SHA256_RE.fullmatch(historical["derived_sha256"])):
        raise CaseServiceError("historical dilution reference boundary invalid / 역사적 희석도 참조경계 오류")
    eligible = status == COMPLETE and base.get("freshness", {}).get("status") == FRESH and all_reviewed
    expected_binding = {"eligible_for_future_direct_bind": eligible, "reason": "COMPLETE_REVIEWED_FRESH" if eligible else status}
    if bridge.get("binding_eligibility") != expected_binding:
        raise CaseServiceError("diluted-share bridge eligibility mismatch / 희석주식 bridge 적격성 불일치")
    expected_class = "DERIVED_FACT" if eligible else "DERIVED_FACT_CANDIDATE"
    if bridge.get("class") != expected_class:
        raise CaseServiceError("diluted-share bridge authority propagation mismatch / 희석주식 bridge 권위전파 불일치")
    if bridge.get("semantic_boundary") != {"current_common_shares_equal_fully_diluted": False, "historical_factor_auto_adjustment": False, "missing_adjustments_as_zero": False}:
        raise CaseServiceError("diluted-share bridge semantic boundary invalid / 희석주식 bridge 의미경계 오류")
    expected = _sha(_without(bridge, "bridge_sha256"))
    if bridge.get("bridge_sha256") != expected:
        raise CaseServiceError("diluted-share bridge SHA mismatch / 희석주식 bridge SHA 불일치")
    return {"status": "PASS_DILUTED_SHARE_BRIDGE_VALIDATION", "bridge_sha256": expected, "coverage_status": status, "eligible_for_future_direct_bind": eligible}
