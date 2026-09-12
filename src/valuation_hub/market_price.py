"""M27 governed valuation-date market-price fact / M27 가치평가일 시장가격 FACT 거버넌스."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import date, datetime
from math import isfinite
from typing import Any

from valuation_hub.case_service import CaseServiceError

CANDIDATE_SCHEMA = "market-price-fact-candidate-v0.1"
CANDIDATE_STATUS = "MARKET_PRICE_FACT_CANDIDATE"
REVIEW_SCHEMA = "market-price-review-assertion-v0.1"
REVIEW_STATUS = "MARKET_PRICE_REVIEW_APPROVED"
PACKAGE_SCHEMA = "reviewed-market-price-fact-v0.1"
PACKAGE_STATUS = "MARKET_PRICE_FACT_REVIEWED"
METHODOLOGY_VERSION = "market-price-as-traded-v0.1"
QUOTE_TYPES = ("OFFICIAL_CLOSE", "LAST_TRADE")
REVIEWABLE_TIERS = frozenset({"A", "B"})
PRICE_BASIS = "AS_TRADED_PER_SHARE"
SECURITY_TYPE = "COMMON_EQUITY"
FRESH = "FRESH"
STALE_BLOCKED = "STALE_BLOCKED"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    out = copy.deepcopy(value)
    out.pop(key, None)
    return out


def _date(value: Any, field: str) -> date:
    if not isinstance(value, str):
        raise CaseServiceError(f"{field} YYYY-MM-DD required / {field} 날짜 필요")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise CaseServiceError(f"{field} invalid date / {field} 날짜 오류") from exc
    if parsed.isoformat() != value:
        raise CaseServiceError(f"{field} canonical YYYY-MM-DD required / {field} 정규 날짜 필요")
    return parsed


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise CaseServiceError(f"{field} timezone-aware timestamp required / {field} 시간대 포함 시각 필요")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CaseServiceError(f"{field} ISO timestamp invalid / {field} 시각 오류") from exc
    if parsed.tzinfo is None:
        raise CaseServiceError(f"{field} timezone required / {field} 시간대 필요")
    return parsed


def _text(value: Any, field: str, *, maximum: int = 500) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
        raise CaseServiceError(f"{field} required / {field} 필요")
    return value.strip()


def _positive(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)) or float(value) <= 0:
        raise CaseServiceError(f"{field} finite positive number required / {field} 유한 양수 필요")
    return float(value)


def _freshness(trading_date: str, as_of: str, max_age_days: int) -> dict[str, Any]:
    trade = _date(trading_date, "trading_date")
    valuation = _date(as_of, "as_of")
    if isinstance(max_age_days, bool) or not isinstance(max_age_days, int) or not 0 <= max_age_days <= 30:
        raise CaseServiceError("market-price max_age_days must be 0..30 / 시장가격 max_age_days 범위 오류")
    age = (valuation - trade).days
    if age < 0:
        raise CaseServiceError("market-price trading date is after valuation as_of / 시장가격 거래일이 가치평가일 이후")
    return {"status": FRESH if age <= max_age_days else STALE_BLOCKED, "age_days": age, "max_age_days": max_age_days}


def _review_chronology(approved_at: Any, candidate: dict[str, Any]) -> datetime:
    approved = _timestamp(approved_at, "approved_at")
    quote = _timestamp(candidate.get("observed_at"), "observed_at")
    if approved < quote:
        raise CaseServiceError("market-price approval cannot predate quote observation / 시장가격 승인은 quote 관측시각보다 빠를 수 없음")
    if approved.date() < _date(candidate.get("as_of"), "as_of"):
        raise CaseServiceError("market-price approval cannot predate valuation as_of / 시장가격 승인은 가치평가일보다 빠를 수 없음")
    return approved


def build_market_price_candidate(
    *, price: float, currency: str, entity_id: str, financial_scope: str,
    instrument_id: str, symbol: str, venue: str, quote_type: str,
    trading_date: str, observed_at: str, as_of: str, source_publisher: str,
    source_type: str, source_tier: str, source_locator: str,
    source_snapshot_sha256: str, max_age_days: int = 7,
) -> dict[str, Any]:
    value = _positive(price, "market price")
    ccy = _text(currency, "currency", maximum=8).upper()
    if not 3 <= len(ccy) <= 8:
        raise CaseServiceError("market-price currency invalid / 시장가격 통화 오류")
    entity = {"id": _text(entity_id, "entity_id", maximum=200), "financial_scope": _text(financial_scope, "financial_scope", maximum=80)}
    instrument = {
        "id": _text(instrument_id, "instrument_id", maximum=200),
        "symbol": _text(symbol, "symbol", maximum=80),
        "venue": _text(venue, "venue", maximum=120),
        "security_type": SECURITY_TYPE,
    }
    if quote_type not in QUOTE_TYPES:
        raise CaseServiceError("unsupported market-price quote type / 미지원 시장가격 quote 유형")
    trade = _date(trading_date, "trading_date")
    quote_ts = _timestamp(observed_at, "observed_at")
    if quote_ts.date() != trade:
        raise CaseServiceError("quote timestamp local date must equal trading_date / quote 시각의 현지 날짜와 trading_date 불일치")
    valuation = _date(as_of, "as_of")
    if trade > valuation:
        raise CaseServiceError("market-price trading date is after valuation as_of / 시장가격 거래일이 가치평가일 이후")
    if source_tier not in {"A", "B", "C", "D"}:
        raise CaseServiceError("market-price source tier invalid / 시장가격 source tier 오류")
    if not isinstance(source_snapshot_sha256, str) or not SHA256_RE.fullmatch(source_snapshot_sha256):
        raise CaseServiceError("market-price source snapshot SHA required / 시장가격 source snapshot SHA 필요")
    source = {
        "publisher": _text(source_publisher, "source_publisher", maximum=300),
        "source_type": _text(source_type, "source_type", maximum=160),
        "tier": source_tier,
        "locator": _text(source_locator, "source_locator", maximum=2000),
        "snapshot_sha256": source_snapshot_sha256,
    }
    freshness = _freshness(trading_date, as_of, max_age_days)
    reviewable = source_tier in REVIEWABLE_TIERS and freshness["status"] == FRESH
    candidate = {
        "schema_version": CANDIDATE_SCHEMA, "status": CANDIDATE_STATUS, "canonical": False,
        "class": "FACT_CANDIDATE", "methodology_version": METHODOLOGY_VERSION, "metric": "market_price",
        "price": value, "currency": ccy, "price_basis": PRICE_BASIS, "quote_type": quote_type,
        "trading_date": trading_date, "observed_at": quote_ts.isoformat(), "as_of": as_of,
        "entity": entity, "instrument": instrument, "source": source,
        "policy": {"version": "MARKET_PRICE_FRESHNESS_V01", "max_age_days": max_age_days},
        "freshness": freshness,
        "semantic_boundary": {"valuation_date_market_price": True, "historical_price_substitution": False, "split_adjustment_performed": False},
        "review_readiness": {"source_tier_reviewable": source_tier in REVIEWABLE_TIERS, "fresh": freshness["status"] == FRESH, "eligible_for_human_review": reviewable},
        "candidate_sha256": "",
    }
    candidate["candidate_sha256"] = _sha(_without(candidate, "candidate_sha256"))
    validate_market_price_candidate(candidate)
    return candidate


def validate_market_price_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    if (
        not isinstance(candidate, dict) or candidate.get("schema_version") != CANDIDATE_SCHEMA
        or candidate.get("status") != CANDIDATE_STATUS or candidate.get("canonical") is not False
        or candidate.get("class") != "FACT_CANDIDATE" or candidate.get("methodology_version") != METHODOLOGY_VERSION
        or candidate.get("metric") != "market_price"
    ):
        raise CaseServiceError("market-price candidate schema/status/authority invalid / 시장가격 candidate 스키마·상태·권위 오류")
    _positive(candidate.get("price"), "market price")
    currency = candidate.get("currency")
    if not isinstance(currency, str) or not 3 <= len(currency) <= 8 or currency != currency.upper():
        raise CaseServiceError("market-price candidate currency invalid / 시장가격 candidate 통화 오류")
    if candidate.get("price_basis") != PRICE_BASIS or candidate.get("quote_type") not in QUOTE_TYPES:
        raise CaseServiceError("market-price candidate price basis/quote type invalid / 시장가격 candidate 가격기준·quote 유형 오류")
    entity, instrument, source, policy = candidate.get("entity"), candidate.get("instrument"), candidate.get("source"), candidate.get("policy")
    if not all(isinstance(item, dict) for item in (entity, instrument, source, policy)):
        raise CaseServiceError("market-price candidate identity/provenance incomplete / 시장가격 candidate 식별·출처 불완전")
    _text(entity.get("id"), "entity.id", maximum=200); _text(entity.get("financial_scope"), "entity.financial_scope", maximum=80)
    _text(instrument.get("id"), "instrument.id", maximum=200); _text(instrument.get("symbol"), "instrument.symbol", maximum=80); _text(instrument.get("venue"), "instrument.venue", maximum=120)
    if instrument.get("security_type") != SECURITY_TYPE:
        raise CaseServiceError("market-price security type invalid / 시장가격 security type 오류")
    trade = _date(candidate.get("trading_date"), "trading_date")
    quote_ts = _timestamp(candidate.get("observed_at"), "observed_at")
    valuation = _date(candidate.get("as_of"), "as_of")
    if quote_ts.date() != trade or trade > valuation:
        raise CaseServiceError("market-price quote/trading/as_of chronology invalid / 시장가격 quote·거래일·as_of 시간관계 오류")
    tier = source.get("tier")
    if tier not in {"A", "B", "C", "D"}:
        raise CaseServiceError("market-price source tier invalid / 시장가격 source tier 오류")
    for field, maximum in (("publisher", 300), ("source_type", 160), ("locator", 2000)):
        _text(source.get(field), f"source.{field}", maximum=maximum)
    snapshot_sha = source.get("snapshot_sha256")
    if not isinstance(snapshot_sha, str) or not SHA256_RE.fullmatch(snapshot_sha):
        raise CaseServiceError("market-price source snapshot SHA invalid / 시장가격 source snapshot SHA 오류")
    if policy.get("version") != "MARKET_PRICE_FRESHNESS_V01":
        raise CaseServiceError("market-price freshness policy invalid / 시장가격 최신성 정책 오류")
    expected_freshness = _freshness(candidate["trading_date"], candidate["as_of"], policy.get("max_age_days"))
    if candidate.get("freshness") != expected_freshness:
        raise CaseServiceError("market-price freshness mismatch / 시장가격 최신성 불일치")
    expected_boundary = {"valuation_date_market_price": True, "historical_price_substitution": False, "split_adjustment_performed": False}
    if candidate.get("semantic_boundary") != expected_boundary:
        raise CaseServiceError("market-price semantic boundary invalid / 시장가격 의미경계 오류")
    expected_ready = {
        "source_tier_reviewable": tier in REVIEWABLE_TIERS,
        "fresh": expected_freshness["status"] == FRESH,
        "eligible_for_human_review": tier in REVIEWABLE_TIERS and expected_freshness["status"] == FRESH,
    }
    if candidate.get("review_readiness") != expected_ready:
        raise CaseServiceError("market-price review readiness mismatch / 시장가격 검토준비도 불일치")
    expected = _sha(_without(candidate, "candidate_sha256"))
    if candidate.get("candidate_sha256") != expected:
        raise CaseServiceError("market-price candidate SHA mismatch / 시장가격 candidate SHA 불일치")
    return {"status": "PASS_MARKET_PRICE_CANDIDATE_VALIDATION", "candidate_sha256": expected, "eligible_for_human_review": expected_ready["eligible_for_human_review"], "freshness": expected_freshness["status"]}


def build_market_price_review_assertion(candidate: dict[str, Any], *, reviewer: str, approved_at: str, review_basis: str) -> dict[str, Any]:
    checked = validate_market_price_candidate(candidate)
    if checked["eligible_for_human_review"] is not True:
        raise CaseServiceError("market-price candidate not eligible for review / 시장가격 candidate 인간검토 부적격")
    approved = _review_chronology(approved_at, candidate)
    assertion = {
        "schema_version": REVIEW_SCHEMA, "status": REVIEW_STATUS, "canonical": False,
        "decision": "APPROVE_MARKET_PRICE_FACT", "candidate_sha256": candidate["candidate_sha256"],
        "source_snapshot_sha256": candidate["source"]["snapshot_sha256"], "methodology_version": candidate["methodology_version"],
        "metric": "market_price", "price": candidate["price"], "currency": candidate["currency"], "price_basis": candidate["price_basis"],
        "quote_type": candidate["quote_type"], "trading_date": candidate["trading_date"], "observed_at": candidate["observed_at"], "as_of": candidate["as_of"],
        "entity": copy.deepcopy(candidate["entity"]), "instrument": copy.deepcopy(candidate["instrument"]),
        "policy": copy.deepcopy(candidate["policy"]), "freshness": copy.deepcopy(candidate["freshness"]),
        "reviewer": _text(reviewer, "reviewer", maximum=160), "approved_at": approved.isoformat(),
        "review_basis": _text(review_basis, "review_basis", maximum=4000), "assertion_sha256": "",
    }
    assertion["assertion_sha256"] = _sha(_without(assertion, "assertion_sha256"))
    validate_market_price_review_assertion(assertion, candidate)
    return assertion


def validate_market_price_review_assertion(assertion: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    checked = validate_market_price_candidate(candidate)
    if checked["eligible_for_human_review"] is not True:
        raise CaseServiceError("market-price candidate not reviewable / 시장가격 candidate 검토 불가")
    if (
        not isinstance(assertion, dict) or assertion.get("schema_version") != REVIEW_SCHEMA or assertion.get("status") != REVIEW_STATUS
        or assertion.get("canonical") is not False or assertion.get("decision") != "APPROVE_MARKET_PRICE_FACT"
    ):
        raise CaseServiceError("market-price review schema/status invalid / 시장가격 검토 스키마·상태 오류")
    expected_projection = {
        "candidate_sha256": candidate["candidate_sha256"], "source_snapshot_sha256": candidate["source"]["snapshot_sha256"],
        "methodology_version": candidate["methodology_version"], "metric": "market_price", "price": candidate["price"],
        "currency": candidate["currency"], "price_basis": candidate["price_basis"], "quote_type": candidate["quote_type"],
        "trading_date": candidate["trading_date"], "observed_at": candidate["observed_at"], "as_of": candidate["as_of"],
        "entity": candidate["entity"], "instrument": candidate["instrument"], "policy": candidate["policy"], "freshness": candidate["freshness"],
    }
    for key, expected_value in expected_projection.items():
        if assertion.get(key) != expected_value:
            raise CaseServiceError("market-price review/candidate projection mismatch / 시장가격 검토·candidate 투영 불일치")
    _text(assertion.get("reviewer"), "reviewer", maximum=160); _text(assertion.get("review_basis"), "review_basis", maximum=4000)
    _review_chronology(assertion.get("approved_at"), candidate)
    expected = _sha(_without(assertion, "assertion_sha256"))
    if assertion.get("assertion_sha256") != expected:
        raise CaseServiceError("market-price review SHA mismatch / 시장가격 검토 SHA 불일치")
    return {"status": "PASS_MARKET_PRICE_REVIEW_VALIDATION", "assertion_sha256": expected}


def finalize_reviewed_market_price(candidate: dict[str, Any], assertion: dict[str, Any]) -> dict[str, Any]:
    validate_market_price_candidate(candidate); validate_market_price_review_assertion(assertion, candidate)
    package = {
        "schema_version": PACKAGE_SCHEMA, "status": PACKAGE_STATUS, "canonical": False, "class": "FACT",
        "methodology_version": candidate["methodology_version"], "metric": "market_price", "price": candidate["price"],
        "currency": candidate["currency"], "price_basis": candidate["price_basis"], "quote_type": candidate["quote_type"],
        "trading_date": candidate["trading_date"], "observed_at": candidate["observed_at"], "as_of": candidate["as_of"],
        "entity": copy.deepcopy(candidate["entity"]), "instrument": copy.deepcopy(candidate["instrument"]),
        "source": copy.deepcopy(candidate["source"]), "policy": copy.deepcopy(candidate["policy"]), "freshness": copy.deepcopy(candidate["freshness"]),
        "semantic_boundary": copy.deepcopy(candidate["semantic_boundary"]), "candidate": copy.deepcopy(candidate),
        "review_assertion": copy.deepcopy(assertion), "binding_eligibility": {"eligible": True, "reason": "REVIEWED_FRESH_MARKET_PRICE_FACT"},
        "package_sha256": "",
    }
    package["package_sha256"] = _sha(_without(package, "package_sha256"))
    validate_reviewed_market_price(package)
    return package


def validate_reviewed_market_price(package: dict[str, Any]) -> dict[str, Any]:
    if (
        not isinstance(package, dict) or package.get("schema_version") != PACKAGE_SCHEMA or package.get("status") != PACKAGE_STATUS
        or package.get("canonical") is not False or package.get("class") != "FACT" or package.get("methodology_version") != METHODOLOGY_VERSION
        or package.get("metric") != "market_price"
    ):
        raise CaseServiceError("reviewed market-price schema/status/authority invalid / 검토완료 시장가격 스키마·상태·권위 오류")
    candidate, assertion = package.get("candidate"), package.get("review_assertion")
    if not isinstance(candidate, dict) or not isinstance(assertion, dict):
        raise CaseServiceError("reviewed market-price nested lineage missing / 검토완료 시장가격 중첩 lineage 누락")
    checked = validate_market_price_candidate(candidate); validate_market_price_review_assertion(assertion, candidate)
    if checked["eligible_for_human_review"] is not True:
        raise CaseServiceError("reviewed market-price source no longer eligible / 검토완료 시장가격 source 부적격")
    projected = {
        "methodology_version": candidate["methodology_version"], "metric": "market_price", "price": candidate["price"],
        "currency": candidate["currency"], "price_basis": candidate["price_basis"], "quote_type": candidate["quote_type"],
        "trading_date": candidate["trading_date"], "observed_at": candidate["observed_at"], "as_of": candidate["as_of"],
        "entity": candidate["entity"], "instrument": candidate["instrument"], "source": candidate["source"],
        "policy": candidate["policy"], "freshness": candidate["freshness"], "semantic_boundary": candidate["semantic_boundary"],
    }
    for key, expected_value in projected.items():
        if package.get(key) != expected_value:
            raise CaseServiceError("reviewed market-price projection mismatch / 검토완료 시장가격 투영 불일치")
    if package.get("binding_eligibility") != {"eligible": True, "reason": "REVIEWED_FRESH_MARKET_PRICE_FACT"}:
        raise CaseServiceError("reviewed market-price binding eligibility invalid / 검토완료 시장가격 바인딩 적격성 오류")
    expected = _sha(_without(package, "package_sha256"))
    if package.get("package_sha256") != expected:
        raise CaseServiceError("reviewed market-price package SHA mismatch / 검토완료 시장가격 패키지 SHA 불일치")
    return {"status": "PASS_REVIEWED_MARKET_PRICE_VALIDATION", "package_sha256": expected, "eligible": True, "price": package["price"]}
