"""Evidence-first AI authority for valuation-date dilution coverage.

M30-R4 preserves the M22 current-shares != fully-diluted-shares boundary while
allowing internal analytical review to be completed by a typed AI adjudicator.
Incomplete evidence produces a durable HOLD inventory; it never becomes zero,
absence, a reviewed adjustment, or COMPLETE coverage by implication.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime
from math import isfinite
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.market_price import validate_reviewed_market_price
from valuation_hub.valuation_shares import (
    ADJUSTMENT_CATEGORIES,
    COMPLETE,
    FRESH,
    build_diluted_share_bridge,
    build_dilution_adjustment,
    build_dilution_coverage_assertion,
    validate_diluted_share_bridge,
    validate_dilution_adjustment,
    validate_dilution_coverage_assertion,
    validate_valuation_share_base_context,
)

INVENTORY_SCHEMA = "ai-dilution-coverage-inventory-v0.1"
INVENTORY_STATUS = "AI_DILUTION_COVERAGE_INVENTORY_EVALUATED"
ADJUDICATION_SCHEMA = "ai-dilution-coverage-adjudication-v0.1"
ADJUDICATION_STATUS = "AI_DILUTION_COVERAGE_ADJUDICATED"
PACKAGE_SCHEMA = "ai-reviewed-dilution-package-v0.1"
PACKAGE_STATUS = "AI_REVIEWED_DILUTION_PACKAGE_READY"

ADJUDICATOR_TYPE = "AI"
ADJUDICATOR_ID = "AI_DILUTION_ADJUDICATOR_V01"
POLICY_ID = "EVIDENCE_FIRST_DILUTION_COVERAGE_V01"

PRESENT = "PRESENT"
ABSENT_SUPPORTED = "ABSENT_SUPPORTED"
BLOCKED_DEPENDENCY = "BLOCKED_DEPENDENCY"
UNKNOWN_CONFLICT = "UNKNOWN_CONFLICT"
CATEGORY_STATES = (PRESENT, ABSENT_SUPPORTED, BLOCKED_DEPENDENCY, UNKNOWN_CONFLICT)

READY = "READY_FOR_AI_DILUTION_ADJUDICATION"
HOLD = "HOLD_INCOMPLETE_DILUTION_COVERAGE"
APPROVE = "APPROVE_COMPLETE_DILUTION_COVERAGE"
HOLD_DECISION = "HOLD_INCOMPLETE_DILUTION_COVERAGE"

TSM_METHOD = "TREASURY_STOCK_METHOD_AGGREGATE_V01"
TSM_TRANCHES_METHOD = "TREASURY_STOCK_METHOD_TRANCHES_V01"
EXPLICIT_COUNT_METHOD = "EXPLICIT_OUTSTANDING_AWARD_COUNT_V01"
EXPLICIT_IF_CONVERTED_METHOD = "EXPLICIT_IF_CONVERTED_SHARE_COUNT_V01"
EXPLICIT_CONTINGENT_METHOD = "EXPLICIT_CONTINGENT_SHARE_COUNT_V01"
EXPLICIT_OTHER_METHOD = "EXPLICIT_OTHER_SHARE_COUNT_V01"
ALLOWED_METHODS = {
    "options_treasury_stock_method": {TSM_METHOD, TSM_TRANCHES_METHOD},
    "rsu_restricted_stock": {EXPLICIT_COUNT_METHOD},
    "warrants": {TSM_METHOD, TSM_TRANCHES_METHOD, EXPLICIT_COUNT_METHOD},
    "convertibles_if_converted": {EXPLICIT_IF_CONVERTED_METHOD},
    "contingent_shares": {EXPLICIT_CONTINGENT_METHOD},
    "other_explicit": {EXPLICIT_OTHER_METHOD, EXPLICIT_COUNT_METHOD},
}

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    out = copy.deepcopy(value)
    out.pop(key, None)
    return out


def _text(value: Any, field: str, maximum: int = 8000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
        raise CaseServiceError(f"{field} required/too long / {field} 필요·길이 오류")
    return value.strip()


def _timestamp(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise CaseServiceError(f"{field} timezone-aware timestamp required / {field} 시간대 포함 시각 필요")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CaseServiceError(f"{field} ISO timestamp invalid / {field} ISO 시각 오류") from exc
    if parsed.tzinfo is None:
        raise CaseServiceError(f"{field} timezone required / {field} 시간대 필요")
    return parsed.isoformat()


def _num(value: Any, field: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
        raise CaseServiceError(f"{field} finite numeric required / {field} 유한 숫자 필요")
    number = float(value)
    if positive and number <= 0:
        raise CaseServiceError(f"{field} must be > 0 / {field} 0 초과 필요")
    if not positive and number < 0:
        raise CaseServiceError(f"{field} must be nonnegative / {field} 음수 불가")
    return number


def _str_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise CaseServiceError(f"{field} string array required / {field} 문자열 배열 필요")
    return [item.strip() for item in value]


def _source_rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise CaseServiceError("dilution category requires source evidence / 희석 category 출처근거 필요")
    rows: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise CaseServiceError("dilution source must be object / 희석 출처 객체 필요")
        sha = item.get("snapshot_sha256")
        if not isinstance(sha, str) or not SHA256_RE.fullmatch(sha):
            raise CaseServiceError("dilution source snapshot SHA invalid / 희석 출처 snapshot SHA 오류")
        rows.append({
            "locator": _text(item.get("locator"), "source.locator", 2000),
            "snapshot_sha256": sha,
            "source_type": _text(item.get("source_type"), "source.source_type", 160),
        })
    return rows


def _contradiction(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("performed") is not True:
        raise CaseServiceError("explicit contradiction search required / 명시적 반증검색 필요")
    return {
        "performed": True,
        "summary": _text(value.get("summary"), "contradiction_search.summary", 4000),
        "material_contradictions": _str_list(value.get("material_contradictions"), "material_contradictions"),
    }


def _market_price_projection(package: dict[str, Any] | None, base_context: dict[str, Any]) -> dict[str, Any] | None:
    if package is None:
        return None
    checked = validate_reviewed_market_price(package)
    if checked.get("eligible") is not True or package.get("freshness", {}).get("status") != FRESH:
        raise CaseServiceError("fresh reviewed market price required / 최신 검토 시장가격 필요")
    if package.get("as_of") != base_context.get("policy", {}).get("as_of"):
        raise CaseServiceError("market-price/base as_of mismatch / 시장가격·주식기준 as_of 불일치")
    price_entity = package.get("entity")
    base_entity = base_context.get("entity")
    if not isinstance(price_entity, dict) or not isinstance(base_entity, dict) or (
        price_entity.get("id") != base_entity.get("id")
        or price_entity.get("financial_scope") != base_entity.get("financial_scope")
    ):
        raise CaseServiceError("market-price/base entity mismatch / 시장가격·주식기준 entity 불일치")
    return copy.deepcopy(package)


def _tsm_shares(outstanding: float, exercise_price: float, market_price: float) -> float:
    if market_price <= exercise_price:
        return 0.0
    return outstanding * (market_price - exercise_price) / market_price


def _tsm_tranche_shares(tranches: Any, market_price: float) -> tuple[float, list[dict[str, float]]]:
    if not isinstance(tranches, list) or not tranches:
        raise CaseServiceError("TSM tranche method requires nonempty strike tranches / TSM tranche 방식은 행사가 tranche 필요")
    normalized: list[dict[str, float]] = []
    total = 0.0
    for index, row in enumerate(tranches):
        if not isinstance(row, dict) or set(row) != {"outstanding_instruments", "exercise_price"}:
            raise CaseServiceError("TSM tranche contract invalid / TSM tranche 계약 오류")
        outstanding = _num(row.get("outstanding_instruments"), f"tranches[{index}].outstanding_instruments")
        strike = _num(row.get("exercise_price"), f"tranches[{index}].exercise_price")
        normalized.append({"outstanding_instruments": outstanding, "exercise_price": strike})
        total += _tsm_shares(outstanding, strike, market_price)
    return total, normalized


def _validate_category(row: dict[str, Any], *, market_price_package: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(row, dict):
        raise CaseServiceError("dilution category object required / 희석 category 객체 필요")
    category, state = row.get("category"), row.get("state")
    if category not in ADJUSTMENT_CATEGORIES or state not in CATEGORY_STATES:
        raise CaseServiceError("unsupported dilution category/state / 미지원 희석 category/state")

    sources = _source_rows(row.get("sources"))
    basis = _text(row.get("evidence_basis"), "evidence_basis", 8000)
    contradiction = _contradiction(row.get("contradiction_search"))
    dependencies = _str_list(row.get("dependencies"), "dependencies")
    method = row.get("calculation_method")
    inputs = row.get("calculation_inputs")
    shares = row.get("adjustment_shares")
    adjustment_id = row.get("adjustment_id")

    if state in {PRESENT, ABSENT_SUPPORTED} and contradiction["material_contradictions"]:
        raise CaseServiceError("resolved dilution category cannot contain material contradiction / 해결된 희석 category에 중대 반증 불가")
    if state == UNKNOWN_CONFLICT and not contradiction["material_contradictions"]:
        raise CaseServiceError("UNKNOWN_CONFLICT requires material contradiction / UNKNOWN_CONFLICT는 중대 반증 필요")

    if state == PRESENT:
        if dependencies:
            raise CaseServiceError("PRESENT dilution category cannot have unresolved dependency / PRESENT 희석 category 미해결 의존성 불가")
        if not isinstance(method, str) or method not in ALLOWED_METHODS[category]:
            raise CaseServiceError("unsupported dilution calculation method / 미지원 희석 계산방법")
        if "EPS" in method.upper() or "WEIGHTED_AVERAGE" in method.upper():
            raise CaseServiceError("historical weighted-average EPS dilution cannot be valuation-date adjustment / 기간평균 EPS 희석은 가치평가일 조정 불가")
        _text(adjustment_id, "adjustment_id", 120)
        supplied_shares = _num(shares, "adjustment_shares")
        if not isinstance(inputs, dict):
            raise CaseServiceError("PRESENT dilution category requires calculation_inputs / PRESENT 희석 category 계산입력 필요")
        if category in {"options_treasury_stock_method", "warrants"} and method in {TSM_METHOD, TSM_TRANCHES_METHOD}:
            if market_price_package is None:
                raise CaseServiceError("TSM dilution requires source-bound reviewed market price / TSM 희석은 출처결합 검토 시장가격 필요")
            market = _num(market_price_package.get("price"), "market price", positive=True)
            if method == TSM_METHOD:
                if inputs.get("homogeneous_exercise_price") is not True:
                    raise CaseServiceError(
                        "aggregate weighted-average strike cannot represent multi-strike TSM; explicit homogeneous strike proof or tranches required / 가중평균 행사가로 다중 strike TSM 계산 불가"
                    )
                outstanding = _num(inputs.get("outstanding_instruments"), "outstanding_instruments")
                strike = _num(inputs.get("weighted_average_exercise_price"), "weighted_average_exercise_price")
                expected = _tsm_shares(outstanding, strike, market)
            else:
                expected, normalized_tranches = _tsm_tranche_shares(inputs.get("tranches"), market)
                declared_total = _num(inputs.get("total_outstanding_instruments"), "total_outstanding_instruments")
                tranche_total = sum(row["outstanding_instruments"] for row in normalized_tranches)
                if abs(declared_total - tranche_total) > max(1e-6, abs(declared_total) * 1e-9):
                    raise CaseServiceError("TSM tranche outstanding total mismatch / TSM tranche 총수량 불일치")
            if abs(supplied_shares - expected) > max(1e-6, abs(expected) * 1e-9):
                raise CaseServiceError("TSM adjustment does not reproduce source-bound calculation / TSM 조정 재현 불일치")
        else:
            explicit = _num(inputs.get("explicit_share_count"), "explicit_share_count")
            if abs(supplied_shares - explicit) > max(1e-6, abs(explicit) * 1e-9):
                raise CaseServiceError("explicit dilution adjustment does not reproduce source count / 명시 희석조정 출처수량 불일치")
    else:
        if adjustment_id not in (None, "") or shares is not None or method not in (None, "") or inputs not in (None, {}):
            raise CaseServiceError("non-PRESENT category cannot carry numeric adjustment / 비PRESENT category 수치조정 불가")
        if state == ABSENT_SUPPORTED and dependencies:
            raise CaseServiceError("ABSENT_SUPPORTED cannot have unresolved dependency / ABSENT_SUPPORTED 미해결 의존성 불가")
        if state == BLOCKED_DEPENDENCY and not dependencies:
            raise CaseServiceError("BLOCKED_DEPENDENCY requires dependency / BLOCKED_DEPENDENCY 의존성 필요")

    normalized = {
        "category": category,
        "state": state,
        "sources": sources,
        "evidence_basis": basis,
        "contradiction_search": contradiction,
        "dependencies": dependencies,
        "adjustment_id": adjustment_id if state == PRESENT else None,
        "adjustment_shares": shares if state == PRESENT else None,
        "calculation_method": method if state == PRESENT else None,
        "calculation_inputs": copy.deepcopy(inputs) if state == PRESENT else None,
        "category_sha256": "",
    }
    normalized["category_sha256"] = _sha(_without(normalized, "category_sha256"))
    return normalized


def _blockers(rows: list[dict[str, Any]]) -> list[str]:
    result: list[str] = []
    for row in rows:
        if row["state"] == BLOCKED_DEPENDENCY:
            result.append(f'{row["category"]}:BLOCKED_DEPENDENCY:{"|".join(row["dependencies"])}')
        elif row["state"] == UNKNOWN_CONFLICT:
            result.append(f'{row["category"]}:UNKNOWN_CONFLICT')
    return result


def build_ai_dilution_inventory(
    base_context: dict[str, Any], categories: list[dict[str, Any]], *, market_price_package: dict[str, Any] | None = None
) -> dict[str, Any]:
    checked_base = validate_valuation_share_base_context(base_context)
    if checked_base.get("freshness") != FRESH:
        raise CaseServiceError("AI dilution inventory requires fresh valuation share base / AI 희석 inventory는 최신 주식기준 필요")
    if not isinstance(categories, list) or len(categories) != len(ADJUSTMENT_CATEGORIES):
        raise CaseServiceError("dilution inventory requires exactly six categories / 희석 inventory 정확히 6개 category 필요")

    price = _market_price_projection(market_price_package, base_context)
    rows = [_validate_category(row, market_price_package=price) for row in categories]
    if len({row["category"] for row in rows}) != len(ADJUSTMENT_CATEGORIES) or set(row["category"] for row in rows) != set(ADJUSTMENT_CATEGORIES):
        raise CaseServiceError("dilution inventory category coverage incomplete/duplicate / 희석 inventory category 누락·중복")
    rows = sorted(rows, key=lambda row: ADJUSTMENT_CATEGORIES.index(row["category"]))
    blockers = _blockers(rows)
    inventory = {
        "schema_version": INVENTORY_SCHEMA,
        "status": INVENTORY_STATUS,
        "canonical": False,
        "policy_id": POLICY_ID,
        "decision": READY if not blockers else HOLD,
        "base_context_sha256": base_context["context_sha256"],
        "as_of": base_context["policy"]["as_of"],
        "entity": copy.deepcopy(base_context["entity"]),
        "categories": rows,
        "market_price_package": price,
        "blockers": blockers,
        "semantic_boundary": {
            "current_common_shares_not_fully_diluted": True,
            "missing_category_never_zero_or_absent": True,
            "historical_weighted_average_eps_reference_only": True,
            "weighted_average_strike_not_portfolio_tsm": True,
            "complete_requires_all_six_categories_resolved": True,
        },
        "inventory_sha256": "",
    }
    inventory["inventory_sha256"] = _sha(_without(inventory, "inventory_sha256"))
    validate_ai_dilution_inventory(inventory, base_context)
    return inventory


def validate_ai_dilution_inventory(inventory: dict[str, Any], base_context: dict[str, Any]) -> dict[str, Any]:
    checked_base = validate_valuation_share_base_context(base_context)
    if checked_base.get("freshness") != FRESH:
        raise CaseServiceError("AI dilution inventory base is stale / AI 희석 inventory 주식기준 오래됨")
    if (
        not isinstance(inventory, dict)
        or inventory.get("schema_version") != INVENTORY_SCHEMA
        or inventory.get("status") != INVENTORY_STATUS
        or inventory.get("canonical") is not False
        or inventory.get("policy_id") != POLICY_ID
    ):
        raise CaseServiceError("AI dilution inventory schema/status invalid / AI 희석 inventory 스키마·상태 오류")
    if inventory.get("base_context_sha256") != base_context.get("context_sha256") or inventory.get("as_of") != base_context.get("policy", {}).get("as_of") or inventory.get("entity") != base_context.get("entity"):
        raise CaseServiceError("AI dilution inventory/base mismatch / AI 희석 inventory·주식기준 불일치")
    if inventory.get("semantic_boundary") != {
        "current_common_shares_not_fully_diluted": True,
        "missing_category_never_zero_or_absent": True,
        "historical_weighted_average_eps_reference_only": True,
        "weighted_average_strike_not_portfolio_tsm": True,
        "complete_requires_all_six_categories_resolved": True,
    }:
        raise CaseServiceError("AI dilution inventory semantic boundary invalid / AI 희석 inventory 의미경계 오류")

    price = inventory.get("market_price_package")
    price_projection = _market_price_projection(price, base_context) if price is not None else None
    raw_rows = inventory.get("categories")
    if not isinstance(raw_rows, list) or len(raw_rows) != len(ADJUSTMENT_CATEGORIES):
        raise CaseServiceError("AI dilution inventory categories invalid / AI 희석 inventory categories 오류")
    rows = [_validate_category(row, market_price_package=price_projection) for row in raw_rows]
    if [row["category"] for row in rows] != list(ADJUSTMENT_CATEGORIES):
        raise CaseServiceError("AI dilution inventory category order/coverage invalid / AI 희석 inventory category 순서·범위 오류")
    if raw_rows != rows:
        raise CaseServiceError("AI dilution inventory category projection mismatch / AI 희석 inventory category 투영 불일치")
    blockers = _blockers(rows)
    decision = READY if not blockers else HOLD
    if inventory.get("blockers") != blockers or inventory.get("decision") != decision:
        raise CaseServiceError("AI dilution inventory readiness mismatch / AI 희석 inventory 준비도 불일치")
    expected_sha = _sha(_without(inventory, "inventory_sha256"))
    if inventory.get("inventory_sha256") != expected_sha:
        raise CaseServiceError("AI dilution inventory SHA mismatch / AI 희석 inventory SHA 불일치")
    return {"status": "PASS_AI_DILUTION_INVENTORY_VALIDATION", "inventory_sha256": expected_sha, "decision": decision, "blockers": blockers}


def build_ai_dilution_adjudication(inventory: dict[str, Any], base_context: dict[str, Any], *, adjudicated_at: str) -> dict[str, Any]:
    checked = validate_ai_dilution_inventory(inventory, base_context)
    when = _timestamp(adjudicated_at, "adjudicated_at")
    decision = APPROVE if checked["decision"] == READY else HOLD_DECISION
    adjudication = {
        "schema_version": ADJUDICATION_SCHEMA,
        "status": ADJUDICATION_STATUS,
        "canonical": False,
        "policy_id": POLICY_ID,
        "adjudicator": {"type": ADJUDICATOR_TYPE, "id": ADJUDICATOR_ID},
        "decision": decision,
        "adjudicated_at": when,
        "inventory_sha256": inventory["inventory_sha256"],
        "base_context_sha256": base_context["context_sha256"],
        "blockers": copy.deepcopy(checked["blockers"]),
        "inventory": copy.deepcopy(inventory),
        "adjudication_sha256": "",
    }
    adjudication["adjudication_sha256"] = _sha(_without(adjudication, "adjudication_sha256"))
    validate_ai_dilution_adjudication(adjudication, inventory, base_context)
    return adjudication


def validate_ai_dilution_adjudication(adjudication: dict[str, Any], inventory: dict[str, Any], base_context: dict[str, Any]) -> dict[str, Any]:
    checked = validate_ai_dilution_inventory(inventory, base_context)
    if (
        not isinstance(adjudication, dict)
        or adjudication.get("schema_version") != ADJUDICATION_SCHEMA
        or adjudication.get("status") != ADJUDICATION_STATUS
        or adjudication.get("canonical") is not False
        or adjudication.get("policy_id") != POLICY_ID
        or adjudication.get("adjudicator") != {"type": ADJUDICATOR_TYPE, "id": ADJUDICATOR_ID}
    ):
        raise CaseServiceError("AI dilution adjudication schema/authority invalid / AI 희석 adjudication 스키마·권위 오류")
    _timestamp(adjudication.get("adjudicated_at"), "adjudicated_at")
    expected_decision = APPROVE if checked["decision"] == READY else HOLD_DECISION
    if (
        adjudication.get("decision") != expected_decision
        or adjudication.get("inventory_sha256") != inventory.get("inventory_sha256")
        or adjudication.get("base_context_sha256") != base_context.get("context_sha256")
        or adjudication.get("blockers") != checked["blockers"]
        or adjudication.get("inventory") != inventory
    ):
        raise CaseServiceError("AI dilution adjudication projection mismatch / AI 희석 adjudication 투영 불일치")
    expected_sha = _sha(_without(adjudication, "adjudication_sha256"))
    if adjudication.get("adjudication_sha256") != expected_sha:
        raise CaseServiceError("AI dilution adjudication SHA mismatch / AI 희석 adjudication SHA 불일치")
    return {"status": "PASS_AI_DILUTION_ADJUDICATION_VALIDATION", "adjudication_sha256": expected_sha, "decision": expected_decision}


def _reviewed_adjustment(row: dict[str, Any]) -> dict[str, Any]:
    description = f'{row["calculation_method"]}: {row["evidence_basis"]}'
    adjustment = build_dilution_adjustment(
        adjustment_id=row["adjustment_id"],
        category=row["category"],
        shares=row["adjustment_shares"],
        source_sha256=row["category_sha256"],
        source_description=description[:1000],
    )
    adjustment["class"] = "NORMALIZED_FACT"
    adjustment["adjustment_sha256"] = _sha(_without(adjustment, "adjustment_sha256"))
    validate_dilution_adjustment(adjustment)
    return adjustment


def build_ai_reviewed_dilution_package(base_context: dict[str, Any], inventory: dict[str, Any], adjudication: dict[str, Any]) -> dict[str, Any]:
    checked = validate_ai_dilution_adjudication(adjudication, inventory, base_context)
    if checked["decision"] != APPROVE:
        raise CaseServiceError("incomplete dilution coverage cannot finalize / 불완전 희석 coverage 최종화 불가")
    rows = inventory["categories"]
    adjustments = [_reviewed_adjustment(row) for row in rows if row["state"] == PRESENT]
    coverage_basis = json.dumps({
        "review_mode": "AI_EVIDENCE_ADJUDICATION",
        "policy_id": POLICY_ID,
        "adjudicator_id": ADJUDICATOR_ID,
        "inventory_sha256": inventory["inventory_sha256"],
        "adjudication_sha256": adjudication["adjudication_sha256"],
        "resolved_categories": {row["category"]: row["state"] for row in rows},
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    assertion = build_dilution_coverage_assertion(
        base_context,
        adjustments,
        reviewer=ADJUDICATOR_ID,
        approved_at=adjudication["adjudicated_at"],
        coverage_basis=coverage_basis,
        reviewed_categories=list(ADJUSTMENT_CATEGORIES),
    )
    bridge = build_diluted_share_bridge(base_context, adjustments, coverage_assertion=assertion)
    checked_bridge = validate_diluted_share_bridge(bridge)
    if checked_bridge.get("coverage_status") != COMPLETE or checked_bridge.get("eligible_for_future_direct_bind") is not True:
        raise CaseServiceError("AI dilution package failed complete bridge eligibility / AI 희석 package 완전 bridge 적격 실패")
    package = {
        "schema_version": PACKAGE_SCHEMA,
        "status": PACKAGE_STATUS,
        "canonical": False,
        "class": "DERIVED_FACT",
        "metric": "fully_diluted_shares",
        "policy_id": POLICY_ID,
        "review_authority": {
            "type": ADJUDICATOR_TYPE,
            "id": ADJUDICATOR_ID,
            "decision": APPROVE,
            "adjudicated_at": adjudication["adjudicated_at"],
            "inventory_sha256": inventory["inventory_sha256"],
            "adjudication_sha256": adjudication["adjudication_sha256"],
        },
        "base_context_sha256": base_context["context_sha256"],
        "adjustments": adjustments,
        "coverage_assertion": assertion,
        "bridge": bridge,
        "value": bridge["candidate_fully_diluted_shares"],
        "unit": "shares",
        "package_sha256": "",
    }
    package["package_sha256"] = _sha(_without(package, "package_sha256"))
    validate_ai_reviewed_dilution_package(package, base_context, inventory, adjudication)
    return package


def validate_ai_reviewed_dilution_package(package: dict[str, Any], base_context: dict[str, Any], inventory: dict[str, Any], adjudication: dict[str, Any]) -> dict[str, Any]:
    checked = validate_ai_dilution_adjudication(adjudication, inventory, base_context)
    if checked["decision"] != APPROVE:
        raise CaseServiceError("AI reviewed dilution package requires approved complete coverage / AI 검토 희석 package 완전 coverage 승인 필요")
    if (
        not isinstance(package, dict)
        or package.get("schema_version") != PACKAGE_SCHEMA
        or package.get("status") != PACKAGE_STATUS
        or package.get("canonical") is not False
        or package.get("class") != "DERIVED_FACT"
        or package.get("metric") != "fully_diluted_shares"
        or package.get("policy_id") != POLICY_ID
        or package.get("unit") != "shares"
    ):
        raise CaseServiceError("AI reviewed dilution package schema/status invalid / AI 검토 희석 package 스키마·상태 오류")
    expected_adjustments = [_reviewed_adjustment(row) for row in inventory["categories"] if row["state"] == PRESENT]
    if package.get("adjustments") != expected_adjustments:
        raise CaseServiceError("AI reviewed dilution adjustment projection mismatch / AI 검토 희석조정 투영 불일치")
    assertion, bridge = package.get("coverage_assertion"), package.get("bridge")
    if not isinstance(assertion, dict) or not isinstance(bridge, dict):
        raise CaseServiceError("AI reviewed dilution package lineage missing / AI 검토 희석 package lineage 누락")
    validate_dilution_coverage_assertion(assertion, base_context, expected_adjustments)
    checked_bridge = validate_diluted_share_bridge(bridge)
    if checked_bridge.get("coverage_status") != COMPLETE or checked_bridge.get("eligible_for_future_direct_bind") is not True:
        raise CaseServiceError("AI reviewed dilution bridge not complete/eligible / AI 검토 희석 bridge 미완전·부적격")
    if bridge != build_diluted_share_bridge(base_context, expected_adjustments, coverage_assertion=assertion):
        raise CaseServiceError("AI reviewed dilution bridge does not reproduce / AI 검토 희석 bridge 재현 불일치")
    expected_authority = {
        "type": ADJUDICATOR_TYPE,
        "id": ADJUDICATOR_ID,
        "decision": APPROVE,
        "adjudicated_at": adjudication["adjudicated_at"],
        "inventory_sha256": inventory["inventory_sha256"],
        "adjudication_sha256": adjudication["adjudication_sha256"],
    }
    if package.get("review_authority") != expected_authority or package.get("base_context_sha256") != base_context.get("context_sha256") or package.get("value") != bridge.get("candidate_fully_diluted_shares"):
        raise CaseServiceError("AI reviewed dilution package projection mismatch / AI 검토 희석 package 투영 불일치")
    expected_sha = _sha(_without(package, "package_sha256"))
    if package.get("package_sha256") != expected_sha:
        raise CaseServiceError("AI reviewed dilution package SHA mismatch / AI 검토 희석 package SHA 불일치")
    return {"status": "PASS_AI_REVIEWED_DILUTION_PACKAGE_VALIDATION", "package_sha256": expected_sha, "eligible": True, "fully_diluted_shares": package["value"]}
