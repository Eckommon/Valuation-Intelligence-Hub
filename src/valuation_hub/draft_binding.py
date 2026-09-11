"""Governed normalized-evidence → Draft binding proposals / 정규화 근거→Draft 바인딩 제안.

M16 never mutates a Draft. It classifies what can be bound safely, what is only
reference context, and what still requires derivation or analyst assumptions.
"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import date
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.financial_normalization import INSTANT, validate_financial_observation

SCHEMA_VERSION = "draft-binding-proposal-v0.1"
STATUS = "DRAFT_BINDING_PROPOSED"
DIRECT_BIND = "DIRECT_BIND"
REFERENCE_ONLY = "REFERENCE_ONLY"
NEEDS_DERIVATION = "NEEDS_DERIVATION"
NEEDS_ASSUMPTION = "NEEDS_ASSUMPTION"
MISSING_REQUIRED = "MISSING_REQUIRED"
CONFLICT_BLOCKED = "CONFLICT_BLOCKED"
STALE_BLOCKED = "STALE_BLOCKED"
UNKNOWN_DATE_PRECISION = "UNKNOWN_DATE_PRECISION"

SUPPORTED_METRICS = {
    "revenue", "operating_income", "net_income", "assets", "cash",
    "equity", "liabilities", "shares_outstanding",
}
MATERIAL_FIELDS = (
    "market_price", "equity.diluted_shares", "equity.debt", "equity.cash",
    "equity.minority_interest", "scenario.wacc", "scenario.terminal_growth",
    "scenario.years.revenue", "scenario.years.ebit_margin", "scenario.years.tax_rate",
    "scenario.years.depreciation_amortization", "scenario.years.capex", "scenario.years.delta_nwc",
)


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result.pop(key, None)
    return result


def _parse_as_of(value: str) -> date:
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise CaseServiceError("as_of must be YYYY-MM-DD / as_of 날짜 형식 오류") from exc
    if parsed.isoformat() != value:
        raise CaseServiceError("as_of must be canonical YYYY-MM-DD / as_of 정규 날짜 형식 오류")
    return parsed


def _freshness(observation: dict[str, Any], as_of: date, max_age_days: int) -> dict[str, Any]:
    period = observation["period"]
    end = period.get("end")
    precision = period.get("date_precision")
    if not isinstance(end, str) or precision != "EXACT":
        return {"status": UNKNOWN_DATE_PRECISION, "age_days": None, "max_age_days": max_age_days}
    try:
        end_date = date.fromisoformat(end)
    except ValueError as exc:
        raise CaseServiceError("observation period.end invalid / observation 기간말 오류") from exc
    age = (as_of - end_date).days
    if age < 0:
        raise CaseServiceError("observation period is after as_of / observation 기간이 as_of 이후입니다")
    return {"status": "FRESH" if age <= max_age_days else STALE_BLOCKED, "age_days": age, "max_age_days": max_age_days}


def _select_context(observations: list[dict[str, Any]], as_of: date, max_age_days: int) -> tuple[dict[str, Any], dict[str, Any]]:
    context: dict[str, Any] = {}
    conflicts: dict[str, Any] = {}
    grouped: dict[str, list[dict[str, Any]]] = {}
    for raw in observations:
        validate_financial_observation(raw)
        metric = raw.get("metric")
        if metric not in SUPPORTED_METRICS:
            continue
        grouped.setdefault(metric, []).append(raw)

    for metric, items in grouped.items():
        # M16 v0.1 intentionally requires one already-reconciled observation per metric.
        hashes = {item["observation_sha256"] for item in items}
        if len(hashes) > 1:
            conflicts[metric] = {"state": CONFLICT_BLOCKED, "observation_sha256": sorted(hashes)}
            continue
        chosen = copy.deepcopy(items[0])
        context[metric] = {
            "metric": metric,
            "value": chosen["value"],
            "unit": chosen["unit"],
            "class": chosen["class"],
            "entity": copy.deepcopy(chosen["entity"]),
            "period": copy.deepcopy(chosen["period"]),
            "observation_sha256": chosen["observation_sha256"],
            "freshness": _freshness(chosen, as_of, max_age_days),
        }
    return context, conflicts


def _decision(field: str, state: str, rationale: str, *, source_metric: str | None = None, source: dict[str, Any] | None = None) -> dict[str, Any]:
    result = {"field": field, "state": state, "rationale": rationale}
    if source_metric is not None:
        result["source_metric"] = source_metric
    if source is not None:
        result["source_observation_sha256"] = source.get("observation_sha256")
        result["source_class"] = source.get("class")
        result["source_freshness"] = copy.deepcopy(source.get("freshness"))
    return result


def build_binding_proposal(observations: list[dict[str, Any]], *, as_of: str, max_age_days: int = 550) -> dict[str, Any]:
    if not isinstance(observations, list) or not observations:
        raise CaseServiceError("observations must be a non-empty list / observation 비어있지 않은 배열 필요")
    if isinstance(max_age_days, bool) or not isinstance(max_age_days, int) or not 0 <= max_age_days <= 3650:
        raise CaseServiceError("max_age_days out of range / max_age_days 범위 오류")
    as_of_date = _parse_as_of(as_of)

    identities: set[tuple[str, str]] = set()
    monetary_units: set[str] = set()
    for item in observations:
        validate_financial_observation(item)
        identities.add((item["entity"]["id"], item["entity"]["financial_scope"]))
        if item.get("metric") != "shares_outstanding":
            monetary_units.add(str(item.get("unit")))
    if len(identities) != 1:
        raise CaseServiceError("binding requires one entity and financial scope / 바인딩은 단일 entity·재무범위가 필요합니다")
    if len(monetary_units) > 1:
        raise CaseServiceError("binding monetary unit conflict / 바인딩 통화·단위 충돌")

    context, conflicts = _select_context(observations, as_of_date, max_age_days)
    decisions: list[dict[str, Any]] = []

    decisions.append(_decision("market_price", MISSING_REQUIRED, "M15 normalized financial evidence does not include market price / M15 재무근거에는 시장가격이 없음"))

    shares = context.get("shares_outstanding")
    if shares:
        decisions.append(_decision("equity.diluted_shares", NEEDS_DERIVATION, "shares_outstanding is not semantically equal to diluted_shares / 발행주식수는 희석주식수와 동일하지 않음", source_metric="shares_outstanding", source=shares))
    else:
        decisions.append(_decision("equity.diluted_shares", MISSING_REQUIRED, "no diluted-share-equivalent evidence / 희석주식수 동등 근거 없음"))

    liabilities = context.get("liabilities")
    if liabilities:
        decisions.append(_decision("equity.debt", NEEDS_DERIVATION, "liabilities is not semantically equal to interest-bearing debt / 부채총계는 이자부채와 동일하지 않음", source_metric="liabilities", source=liabilities))
    else:
        decisions.append(_decision("equity.debt", MISSING_REQUIRED, "no debt-equivalent normalized evidence / debt 동등 정규화근거 없음"))

    cash = context.get("cash")
    if "cash" in conflicts:
        decisions.append(_decision("equity.cash", CONFLICT_BLOCKED, "multiple unreconciled cash observations / 미조정 cash observation 충돌", source_metric="cash"))
    elif cash is None:
        decisions.append(_decision("equity.cash", MISSING_REQUIRED, "cash evidence missing / cash 근거 없음"))
    elif cash["class"] != "NORMALIZED_FACT":
        decisions.append(_decision("equity.cash", REFERENCE_ONLY, "candidate authority cannot DIRECT_BIND / 후보 권위는 직접 바인딩 불가", source_metric="cash", source=cash))
    elif cash["period"].get("kind") != INSTANT:
        decisions.append(_decision("equity.cash", NEEDS_DERIVATION, "cash direct bind requires INSTANT semantics / cash 직접 바인딩은 INSTANT 필요", source_metric="cash", source=cash))
    elif cash["freshness"]["status"] == STALE_BLOCKED:
        decisions.append(_decision("equity.cash", STALE_BLOCKED, "cash evidence exceeds freshness policy / cash 근거가 최신성 정책 초과", source_metric="cash", source=cash))
    elif cash["freshness"]["status"] == UNKNOWN_DATE_PRECISION:
        decisions.append(_decision("equity.cash", REFERENCE_ONLY, "cash date precision is insufficient for automatic freshness approval / cash 날짜정밀도가 자동 최신성 승인에 부족", source_metric="cash", source=cash))
    else:
        decisions.append(_decision("equity.cash", DIRECT_BIND, "semantic-exact reviewed fresh INSTANT cash / 의미가 정확히 일치하는 검토완료 최신 INSTANT cash", source_metric="cash", source=cash))

    decisions.append(_decision("equity.minority_interest", MISSING_REQUIRED, "no normalized minority-interest metric in M16 v0.1 / M16 v0.1 minority-interest 정규화 지표 없음"))
    decisions.append(_decision("scenario.wacc", NEEDS_ASSUMPTION, "WACC is a valuation assumption, not a historical financial fact / WACC는 가치평가 가정"))
    decisions.append(_decision("scenario.terminal_growth", NEEDS_ASSUMPTION, "terminal growth is a valuation assumption / 영구성장률은 가치평가 가정"))

    revenue = context.get("revenue")
    decisions.append(_decision("scenario.years.revenue", NEEDS_ASSUMPTION, "historical/TTM revenue is reference context, not forecast revenue / 과거·TTM 매출은 미래 매출 가정과 동일하지 않음", source_metric="revenue" if revenue else None, source=revenue))

    op = context.get("operating_income")
    decisions.append(_decision("scenario.years.ebit_margin", NEEDS_ASSUMPTION, "historical operating margin may inform but cannot equal forecast EBIT margin / 과거 영업마진은 미래 EBIT margin의 참고값일 뿐 동일하지 않음", source_metric="operating_income" if op else None, source=op))
    decisions.append(_decision("scenario.years.tax_rate", NEEDS_ASSUMPTION, "forecast tax rate requires an explicit assumption / 미래 세율은 명시적 가정 필요"))
    decisions.append(_decision("scenario.years.depreciation_amortization", NEEDS_ASSUMPTION, "forecast D&A requires explicit modeling / 미래 D&A 모델링 필요"))
    decisions.append(_decision("scenario.years.capex", NEEDS_ASSUMPTION, "forecast CAPEX requires explicit modeling / 미래 CAPEX 모델링 필요"))
    decisions.append(_decision("scenario.years.delta_nwc", NEEDS_ASSUMPTION, "forecast ΔNWC requires explicit modeling / 미래 ΔNWC 모델링 필요"))

    if {item["field"] for item in decisions} != set(MATERIAL_FIELDS):
        raise CaseServiceError("binding matrix incomplete / 바인딩 matrix 불완전")

    state_counts: dict[str, int] = {}
    for item in decisions:
        state_counts[item["state"]] = state_counts.get(item["state"], 0) + 1
    entity_id, scope = next(iter(identities))
    proposal = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "canonical": False,
        "target": {"draft_schema_version": "draft-case-v0.1", "model": "equity_fcff"},
        "policy": {"version": "evidence-draft-binding-v0.1", "as_of": as_of, "max_age_days": max_age_days, "direct_bind_requires": ["SEMANTIC_EXACT", "NORMALIZED_FACT", "FRESH", "PERIOD_COMPATIBLE"]},
        "identity": {"entity_id": entity_id, "financial_scope": scope, "monetary_unit": next(iter(monetary_units)) if monetary_units else None},
        "baseline_context": context,
        "conflicts": conflicts,
        "draft_input_matrix": decisions,
        "completeness": {"material_field_count": len(MATERIAL_FIELDS), "classified_field_count": len(decisions), "state_counts": state_counts, "direct_bind_count": state_counts.get(DIRECT_BIND, 0), "unresolved_count": sum(count for state, count in state_counts.items() if state != DIRECT_BIND)},
        "source_observation_sha256": sorted({item["observation_sha256"] for item in observations}),
        "warning_en": "Proposal only. It does not mutate a Draft or promote evidence authority.",
        "warning_ko": "제안 전용입니다. Draft를 변경하거나 근거 권위를 승격하지 않습니다.",
        "proposal_sha256": "",
    }
    proposal["proposal_sha256"] = _sha(_without(proposal, "proposal_sha256"))
    validate_binding_proposal(proposal)
    return proposal


def validate_binding_proposal(proposal: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(proposal, dict) or proposal.get("schema_version") != SCHEMA_VERSION or proposal.get("status") != STATUS:
        raise CaseServiceError("binding proposal schema/status invalid / 바인딩 제안 스키마·상태 오류")
    if proposal.get("canonical") is not False or proposal.get("target") != {"draft_schema_version": "draft-case-v0.1", "model": "equity_fcff"}:
        raise CaseServiceError("binding proposal target/authority invalid / 바인딩 제안 대상·권위 오류")
    matrix = proposal.get("draft_input_matrix")
    if not isinstance(matrix, list) or {item.get("field") for item in matrix if isinstance(item, dict)} != set(MATERIAL_FIELDS):
        raise CaseServiceError("binding proposal matrix incomplete / 바인딩 제안 matrix 불완전")
    allowed = {DIRECT_BIND, REFERENCE_ONLY, NEEDS_DERIVATION, NEEDS_ASSUMPTION, MISSING_REQUIRED, CONFLICT_BLOCKED, STALE_BLOCKED}
    for item in matrix:
        if not isinstance(item, dict) or item.get("state") not in allowed:
            raise CaseServiceError("binding proposal decision invalid / 바인딩 제안 판정 오류")
        if item.get("state") == DIRECT_BIND:
            if item.get("field") != "equity.cash" or item.get("source_class") != "NORMALIZED_FACT" or item.get("source_freshness", {}).get("status") != "FRESH":
                raise CaseServiceError("unsafe DIRECT_BIND detected / 안전하지 않은 DIRECT_BIND 감지")
    expected = _sha(_without(proposal, "proposal_sha256"))
    if proposal.get("proposal_sha256") != expected:
        raise CaseServiceError("binding proposal SHA-256 mismatch / 바인딩 제안 SHA-256 불일치")
    return {"status": "PASS_DRAFT_BINDING_PROPOSAL_VALIDATION", "canonical": False, "proposal_sha256": expected, "direct_bind_count": proposal.get("completeness", {}).get("direct_bind_count", 0), "unresolved_count": proposal.get("completeness", {}).get("unresolved_count")}
