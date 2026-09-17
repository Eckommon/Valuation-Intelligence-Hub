"""Evidence-first AI authority for valuation-date market-price facts."""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.external_source import validate_external_source_snapshot, validate_market_price_candidate_against_snapshot
from valuation_hub.market_price import (
    FRESH,
    REVIEWABLE_TIERS,
    build_market_price_review_assertion,
    finalize_reviewed_market_price,
    validate_market_price_candidate,
    validate_reviewed_market_price,
)

EVIDENCE_SCHEMA = "ai-market-price-evidence-v0.1"
EVIDENCE_STATUS = "AI_MARKET_PRICE_EVIDENCE_READY"
ADJUDICATION_SCHEMA = "ai-market-price-adjudication-v0.1"
ADJUDICATION_STATUS = "AI_MARKET_PRICE_ADJUDICATED"
ADJUDICATOR_ID = "AI_MARKET_PRICE_ADJUDICATOR_V01"
POLICY_ID = "EVIDENCE_FIRST_MARKET_PRICE_V01"
APPROVE = "APPROVE"


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    out = copy.deepcopy(value); out.pop(key, None); return out


def _text(value: Any, field: str, limit: int = 8000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise CaseServiceError(f"{field} required/too long / {field} 필요·길이 오류")
    return value.strip()


def _timestamp(value: Any) -> str:
    if not isinstance(value, str):
        raise CaseServiceError("adjudicated_at timezone-aware timestamp required / adjudicated_at 시간대 포함 시각 필요")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CaseServiceError("adjudicated_at ISO timestamp invalid / adjudicated_at ISO 시각 오류") from exc
    if parsed.tzinfo is None:
        raise CaseServiceError("adjudicated_at timezone required / adjudicated_at 시간대 필요")
    return parsed.isoformat()


def _excerpt(snapshot: dict[str, Any], excerpt: Any, label: str) -> str:
    validate_external_source_snapshot(snapshot)
    value = _text(excerpt, label, 12000)
    if value not in snapshot.get("raw_text", ""):
        raise CaseServiceError(f"{label} must be exact substring of source snapshot / {label}는 source snapshot의 정확 부분문자열이어야 함")
    return value


def _date_tokens(value: str) -> tuple[str, ...]:
    year, month, day = value.split("-")
    names = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
    name = names[int(month)-1]
    return value, f"{name} {int(day)}, {year}", f"{name} {day}, {year}", f"{day}-{month}-{year}", f"{day}/{month}/{year}", f"{month}/{day}/{year}"


def _price_tokens(price: float) -> tuple[str, ...]:
    return f"{price:.2f}", f"${price:.2f}", f"{price:g}"


def _claim_visible(
    snapshot: dict[str, Any], excerpt: str, candidate: dict[str, Any], *, require_primary_identity: bool = False
) -> None:
    if not any(token in excerpt for token in _date_tokens(candidate["trading_date"])):
        raise CaseServiceError("source excerpt does not visibly contain trading date / source excerpt에 거래일이 보이지 않음")
    if not any(token in excerpt for token in _price_tokens(float(candidate["price"]))):
        raise CaseServiceError("source excerpt does not visibly contain candidate price / source excerpt에 candidate 가격이 보이지 않음")
    raw = snapshot["raw_text"].lower()
    symbol = candidate["instrument"]["symbol"].lower()
    venue = candidate["instrument"]["venue"].lower()
    if symbol not in raw:
        raise CaseServiceError("source snapshot does not identify candidate symbol / source snapshot에 candidate symbol 식별 없음")
    if venue not in raw:
        raise CaseServiceError("source snapshot does not identify candidate venue / source snapshot에 candidate venue 식별 없음")
    if require_primary_identity:
        currency = candidate["currency"].lower()
        if currency not in raw:
            raise CaseServiceError("primary source snapshot does not identify candidate currency / primary source snapshot에 candidate 통화 식별 없음")
        if candidate["quote_type"] == "OFFICIAL_CLOSE" and "close" not in raw and "price" not in raw:
            raise CaseServiceError("primary source snapshot does not identify closing-price semantics / primary source snapshot에 종가 의미 식별 없음")


def _source_id(snapshot: dict[str, Any]) -> tuple[str, str]:
    source = snapshot["source"]
    return str(source["publisher"]).strip().lower(), str(source["locator"]).strip().lower()


def _corroboration_rows(candidate: dict[str, Any], primary: dict[str, Any], corroborations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(corroborations, list):
        raise CaseServiceError("corroborations array required / corroborations 배열 필요")
    rows: list[dict[str, Any]] = []
    seen = {_source_id(primary)}
    for i, item in enumerate(corroborations):
        if not isinstance(item, dict) or not isinstance(item.get("snapshot"), dict):
            raise CaseServiceError("corroboration snapshot required / corroboration snapshot 필요")
        snap = item["snapshot"]
        validate_external_source_snapshot(snap)
        sid = _source_id(snap)
        if sid in seen:
            raise CaseServiceError("corroborating source must be independent / corroborating source는 독립 출처여야 함")
        seen.add(sid)
        excerpt = _excerpt(snap, item.get("excerpt"), f"corroborations[{i}].excerpt")
        _claim_visible(snap, excerpt, candidate)
        rows.append({"source": copy.deepcopy(snap["source"]), "snapshot_sha256": snap["snapshot_sha256"], "body_sha256": snap["body"]["sha256"], "excerpt": excerpt})
    return rows


def build_ai_market_price_evidence(
    candidate: dict[str, Any], primary_snapshot: dict[str, Any], *, primary_excerpt: str,
    corroborations: list[dict[str, Any]], contradiction_search_summary: str,
    material_contradictions: list[str],
) -> dict[str, Any]:
    checked = validate_market_price_candidate_against_snapshot(candidate, primary_snapshot)
    if checked.get("freshness") != FRESH or candidate["source"]["tier"] not in REVIEWABLE_TIERS:
        raise CaseServiceError("AI market-price authority requires fresh reviewable candidate / AI 시장가격 권위는 최신 검토가능 candidate 필요")
    if candidate["quote_type"] != "OFFICIAL_CLOSE":
        raise CaseServiceError("M30-R5 v0.1 requires OFFICIAL_CLOSE / M30-R5 v0.1은 OFFICIAL_CLOSE 필요")
    primary_excerpt = _excerpt(primary_snapshot, primary_excerpt, "primary_excerpt")
    _claim_visible(primary_snapshot, primary_excerpt, candidate, require_primary_identity=True)
    rows = _corroboration_rows(candidate, primary_snapshot, corroborations)
    if candidate["source"]["tier"] == "B" and not rows:
        raise CaseServiceError("Tier B market price requires independent corroborating snapshot / Tier B 시장가격은 독립 corroborating snapshot 필요")
    if not isinstance(material_contradictions, list) or not all(isinstance(x, str) and x.strip() for x in material_contradictions):
        raise CaseServiceError("material_contradictions string array required / material_contradictions 문자열 배열 필요")
    if material_contradictions:
        raise CaseServiceError("material market-price contradiction requires HOLD/escalation / 중대 시장가격 반증은 HOLD/escalation 필요")
    evidence = {
        "schema_version": EVIDENCE_SCHEMA, "status": EVIDENCE_STATUS, "canonical": False, "policy_id": POLICY_ID,
        "candidate_sha256": candidate["candidate_sha256"],
        "claim": {"symbol": candidate["instrument"]["symbol"], "venue": candidate["instrument"]["venue"], "currency": candidate["currency"], "quote_type": candidate["quote_type"], "trading_date": candidate["trading_date"], "price": candidate["price"], "as_of": candidate["as_of"]},
        "primary": {"source": copy.deepcopy(primary_snapshot["source"]), "snapshot_sha256": primary_snapshot["snapshot_sha256"], "body_sha256": primary_snapshot["body"]["sha256"], "excerpt": primary_excerpt},
        "corroborations": rows,
        "contradiction_search": {"performed": True, "summary": _text(contradiction_search_summary, "contradiction_search_summary", 4000), "material_contradictions": []},
        "semantic_boundary": {"valuation_date_close_only": True, "historical_substitution_for_other_dates": False, "source_claim_must_be_visible_in_snapshot": True},
        "evidence_sha256": "",
    }
    evidence["evidence_sha256"] = _sha(_without(evidence, "evidence_sha256"))
    validate_ai_market_price_evidence(evidence, candidate, primary_snapshot, corroborations)
    return evidence


def validate_ai_market_price_evidence(evidence: dict[str, Any], candidate: dict[str, Any], primary_snapshot: dict[str, Any], corroborations: list[dict[str, Any]]) -> dict[str, Any]:
    checked = validate_market_price_candidate_against_snapshot(candidate, primary_snapshot)
    if checked.get("freshness") != FRESH or candidate["source"]["tier"] not in REVIEWABLE_TIERS or candidate["quote_type"] != "OFFICIAL_CLOSE":
        raise CaseServiceError("AI market-price candidate not eligible / AI 시장가격 candidate 부적격")
    if not isinstance(evidence, dict) or evidence.get("schema_version") != EVIDENCE_SCHEMA or evidence.get("status") != EVIDENCE_STATUS or evidence.get("canonical") is not False or evidence.get("policy_id") != POLICY_ID:
        raise CaseServiceError("AI market-price evidence schema/status invalid / AI 시장가격 evidence 스키마·상태 오류")
    expected_claim = {"symbol": candidate["instrument"]["symbol"], "venue": candidate["instrument"]["venue"], "currency": candidate["currency"], "quote_type": candidate["quote_type"], "trading_date": candidate["trading_date"], "price": candidate["price"], "as_of": candidate["as_of"]}
    if evidence.get("candidate_sha256") != candidate["candidate_sha256"] or evidence.get("claim") != expected_claim:
        raise CaseServiceError("AI market-price evidence/candidate mismatch / AI 시장가격 evidence·candidate 불일치")
    primary = evidence.get("primary")
    if not isinstance(primary, dict) or primary.get("source") != primary_snapshot["source"] or primary.get("snapshot_sha256") != primary_snapshot["snapshot_sha256"] or primary.get("body_sha256") != primary_snapshot["body"]["sha256"]:
        raise CaseServiceError("AI market-price primary provenance mismatch / AI 시장가격 primary provenance 불일치")
    pexcerpt = _excerpt(primary_snapshot, primary.get("excerpt"), "primary_excerpt"); _claim_visible(primary_snapshot, pexcerpt, candidate, require_primary_identity=True)
    expected_rows = _corroboration_rows(candidate, primary_snapshot, corroborations)
    if candidate["source"]["tier"] == "B" and not expected_rows:
        raise CaseServiceError("Tier B market price requires corroboration / Tier B 시장가격 corroboration 필요")
    if evidence.get("corroborations") != expected_rows:
        raise CaseServiceError("AI market-price corroboration mismatch / AI 시장가격 corroboration 불일치")
    contradiction = evidence.get("contradiction_search")
    if not isinstance(contradiction, dict) or contradiction.get("performed") is not True or contradiction.get("material_contradictions") != []:
        raise CaseServiceError("AI market-price contradiction contract invalid / AI 시장가격 반증 계약 오류")
    _text(contradiction.get("summary"), "contradiction_search.summary", 4000)
    if evidence.get("semantic_boundary") != {"valuation_date_close_only": True, "historical_substitution_for_other_dates": False, "source_claim_must_be_visible_in_snapshot": True}:
        raise CaseServiceError("AI market-price semantic boundary invalid / AI 시장가격 의미경계 오류")
    expected = _sha(_without(evidence, "evidence_sha256"))
    if evidence.get("evidence_sha256") != expected:
        raise CaseServiceError("AI market-price evidence SHA mismatch / AI 시장가격 evidence SHA 불일치")
    return {"status": "PASS_AI_MARKET_PRICE_EVIDENCE_VALIDATION", "evidence_sha256": expected, "price": candidate["price"]}


def build_ai_market_price_adjudication(candidate: dict[str, Any], evidence: dict[str, Any], primary_snapshot: dict[str, Any], corroborations: list[dict[str, Any]], *, adjudicated_at: str) -> dict[str, Any]:
    validate_ai_market_price_evidence(evidence, candidate, primary_snapshot, corroborations)
    adjudication = {"schema_version": ADJUDICATION_SCHEMA, "status": ADJUDICATION_STATUS, "canonical": False, "policy_id": POLICY_ID, "adjudicator": {"type": "AI", "id": ADJUDICATOR_ID}, "decision": APPROVE, "adjudicated_at": _timestamp(adjudicated_at), "candidate_sha256": candidate["candidate_sha256"], "evidence_sha256": evidence["evidence_sha256"], "claim": copy.deepcopy(evidence["claim"]), "adjudication_sha256": ""}
    adjudication["adjudication_sha256"] = _sha(_without(adjudication, "adjudication_sha256"))
    validate_ai_market_price_adjudication(adjudication, candidate, evidence, primary_snapshot, corroborations)
    return adjudication


def validate_ai_market_price_adjudication(adjudication: dict[str, Any], candidate: dict[str, Any], evidence: dict[str, Any], primary_snapshot: dict[str, Any], corroborations: list[dict[str, Any]]) -> dict[str, Any]:
    validate_ai_market_price_evidence(evidence, candidate, primary_snapshot, corroborations)
    if not isinstance(adjudication, dict) or adjudication.get("schema_version") != ADJUDICATION_SCHEMA or adjudication.get("status") != ADJUDICATION_STATUS or adjudication.get("canonical") is not False or adjudication.get("policy_id") != POLICY_ID or adjudication.get("adjudicator") != {"type": "AI", "id": ADJUDICATOR_ID} or adjudication.get("decision") != APPROVE:
        raise CaseServiceError("AI market-price adjudication schema/authority invalid / AI 시장가격 adjudication 스키마·권위 오류")
    _timestamp(adjudication.get("adjudicated_at"))
    if adjudication.get("candidate_sha256") != candidate["candidate_sha256"] or adjudication.get("evidence_sha256") != evidence["evidence_sha256"] or adjudication.get("claim") != evidence["claim"]:
        raise CaseServiceError("AI market-price adjudication projection mismatch / AI 시장가격 adjudication 투영 불일치")
    expected = _sha(_without(adjudication, "adjudication_sha256"))
    if adjudication.get("adjudication_sha256") != expected:
        raise CaseServiceError("AI market-price adjudication SHA mismatch / AI 시장가격 adjudication SHA 불일치")
    return {"status": "PASS_AI_MARKET_PRICE_ADJUDICATION_VALIDATION", "adjudication_sha256": expected, "decision": APPROVE}


def build_ai_reviewed_market_price(candidate: dict[str, Any], evidence: dict[str, Any], adjudication: dict[str, Any], primary_snapshot: dict[str, Any], corroborations: list[dict[str, Any]]) -> dict[str, Any]:
    validate_ai_market_price_adjudication(adjudication, candidate, evidence, primary_snapshot, corroborations)
    basis = json.dumps({"review_mode": "AI_EVIDENCE_ADJUDICATION", "policy_id": POLICY_ID, "adjudicator_id": ADJUDICATOR_ID, "evidence_sha256": evidence["evidence_sha256"], "adjudication_sha256": adjudication["adjudication_sha256"]}, sort_keys=True, separators=(",", ":"))
    assertion = build_market_price_review_assertion(candidate, reviewer=ADJUDICATOR_ID, approved_at=adjudication["adjudicated_at"], review_basis=basis)
    package = finalize_reviewed_market_price(candidate, assertion)
    package["review_authority"] = {"type": "AI", "id": ADJUDICATOR_ID, "policy_id": POLICY_ID, "evidence_sha256": evidence["evidence_sha256"], "adjudication_sha256": adjudication["adjudication_sha256"]}
    package["package_sha256"] = _sha(_without(package, "package_sha256"))
    validate_ai_reviewed_market_price(package, candidate, evidence, adjudication, primary_snapshot, corroborations)
    return package


def validate_ai_reviewed_market_price(package: dict[str, Any], candidate: dict[str, Any], evidence: dict[str, Any], adjudication: dict[str, Any], primary_snapshot: dict[str, Any], corroborations: list[dict[str, Any]]) -> dict[str, Any]:
    validate_ai_market_price_adjudication(adjudication, candidate, evidence, primary_snapshot, corroborations)
    checked = validate_reviewed_market_price(package)
    expected_authority = {"type": "AI", "id": ADJUDICATOR_ID, "policy_id": POLICY_ID, "evidence_sha256": evidence["evidence_sha256"], "adjudication_sha256": adjudication["adjudication_sha256"]}
    if package.get("review_authority") != expected_authority or package.get("candidate") != candidate:
        raise CaseServiceError("AI reviewed market-price authority/lineage mismatch / AI 검토 시장가격 권위·lineage 불일치")
    return {"status": "PASS_AI_REVIEWED_MARKET_PRICE_VALIDATION", "package_sha256": checked["package_sha256"], "eligible": True, "price": package["price"], "review_authority": "AI"}
