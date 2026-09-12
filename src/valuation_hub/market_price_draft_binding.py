"""M27 reviewed market-price FACT → Draft binding proposal v0.7."""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_binding import DIRECT_BIND, MATERIAL_FIELDS, STATUS
from valuation_hub.forecast_draft_binding import SCHEMA_VERSION_V6, validate_binding_proposal_v6
from valuation_hub.market_price import validate_reviewed_market_price

SCHEMA_VERSION_V7 = "draft-binding-proposal-v0.7"
POLICY_VERSION_V7 = "evidence-draft-binding-v0.7-market-price"
DIRECT_REQUIREMENTS = [
    "REVIEWED_FACT",
    "FRESH_MARKET_PRICE",
    "TIER_A_OR_B_SOURCE",
    "AS_TRADED_PER_SHARE",
    "SUPPORTED_QUOTE_TYPE",
    "HUMAN_REVIEW_ASSERTION",
    "EXACT_ENTITY_SCOPE_CURRENCY_AS_OF",
]


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    out = copy.deepcopy(value)
    out.pop(key, None)
    return out


def _counts(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    state_counts: dict[str, int] = {}
    for item in matrix:
        state_counts[item["state"]] = state_counts.get(item["state"], 0) + 1
    return {
        "material_field_count": len(MATERIAL_FIELDS),
        "classified_field_count": len(matrix),
        "state_counts": state_counts,
        "direct_bind_count": state_counts.get(DIRECT_BIND, 0),
        "unresolved_count": sum(count for state, count in state_counts.items() if state != DIRECT_BIND),
    }


def _eligible_package(package: dict[str, Any]) -> None:
    checked = validate_reviewed_market_price(package)
    if (
        checked.get("eligible") is not True
        or package.get("class") != "FACT"
        or package.get("binding_eligibility") != {"eligible": True, "reason": "REVIEWED_FRESH_MARKET_PRICE_FACT"}
    ):
        raise CaseServiceError("only reviewed fresh market-price FACT can bind / 검토완료 최신 시장가격 FACT만 바인딩 가능")


def _projection(package: dict[str, Any]) -> dict[str, Any]:
    return {
        "metric": "market_price_fact",
        "value": package["price"],
        "unit": package["currency"],
        "class": "FACT",
        "entity": copy.deepcopy(package["entity"]),
        "instrument": copy.deepcopy(package["instrument"]),
        "currency": package["currency"],
        "price_basis": package["price_basis"],
        "quote_type": package["quote_type"],
        "trading_date": package["trading_date"],
        "observed_at": package["observed_at"],
        "as_of": package["as_of"],
        "freshness": copy.deepcopy(package["freshness"]),
        "context_sha256": package["package_sha256"],
        "source_market_price_package_sha256": package["package_sha256"],
        "source_snapshot_sha256": package["source"]["snapshot_sha256"],
        "review_assertion_sha256": package["review_assertion"]["assertion_sha256"],
    }


def _decision(package: dict[str, Any]) -> dict[str, Any]:
    return {
        "field": "market_price",
        "state": DIRECT_BIND,
        "rationale": "human-reviewed fresh source-backed market-price FACT / 인간검토완료 최신 출처기반 시장가격 FACT",
        "source_metric": "market_price_fact",
        "source_class": "FACT",
        "source_context_sha256": package["package_sha256"],
        "source_market_price_package_sha256": package["package_sha256"],
        "source_snapshot_sha256": package["source"]["snapshot_sha256"],
        "review_assertion_sha256": package["review_assertion"]["assertion_sha256"],
        "trading_date": package["trading_date"],
        "observed_at": package["observed_at"],
        "venue": package["instrument"]["venue"],
        "quote_type": package["quote_type"],
    }


def _policy(base: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": POLICY_VERSION_V7,
        "as_of": base["policy"]["as_of"],
        "base_policy_version": base["policy"]["version"],
        "direct_bind_requires": copy.deepcopy(DIRECT_REQUIREMENTS),
    }


def build_binding_proposal_with_market_price(base_proposal: dict[str, Any], market_price_package: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(base_proposal, dict) or base_proposal.get("schema_version") != SCHEMA_VERSION_V6:
        raise CaseServiceError("M27 requires draft-binding-proposal-v0.6 base / M27은 v0.6 base proposal 필요")
    validate_binding_proposal_v6(base_proposal)
    _eligible_package(market_price_package)
    identity = base_proposal["identity"]
    if market_price_package.get("entity") != {"id": identity.get("entity_id"), "financial_scope": identity.get("financial_scope")}:
        raise CaseServiceError("market-price package entity/scope mismatch / 시장가격 패키지 entity·scope 불일치")
    monetary = identity.get("monetary_unit")
    if monetary is not None and market_price_package.get("currency") != str(monetary).upper():
        raise CaseServiceError("market-price currency mismatch / 시장가격 통화 불일치")
    if market_price_package.get("as_of") != base_proposal.get("policy", {}).get("as_of"):
        raise CaseServiceError("market-price as_of must equal v0.6 proposal as_of / 시장가격 as_of와 v0.6 proposal 불일치")

    matrix = [
        _decision(market_price_package) if item["field"] == "market_price" else copy.deepcopy(item)
        for item in base_proposal["draft_input_matrix"]
    ]
    baseline = copy.deepcopy(base_proposal["baseline_context"])
    baseline["market_price_fact"] = _projection(market_price_package)
    proposal = {
        "schema_version": SCHEMA_VERSION_V7,
        "status": STATUS,
        "canonical": False,
        "target": copy.deepcopy(base_proposal["target"]),
        "policy": _policy(base_proposal),
        "identity": copy.deepcopy(identity),
        "baseline_context": baseline,
        "conflicts": copy.deepcopy(base_proposal["conflicts"]),
        "draft_input_matrix": matrix,
        "completeness": _counts(matrix),
        "source_observation_sha256": copy.deepcopy(base_proposal["source_observation_sha256"]),
        "source_market_price_package_sha256": market_price_package["package_sha256"],
        "market_price_package": copy.deepcopy(market_price_package),
        "base_proposal": copy.deepcopy(base_proposal),
        "base_proposal_sha256": base_proposal["proposal_sha256"],
        "warning_en": "Market-price proposal only. The quote is a reviewed noncanonical FACT and does not itself create canonical state.",
        "warning_ko": "시장가격 제안 전용입니다. quote는 검토완료 비정식 FACT이며 그 자체로 canonical state를 만들지 않습니다.",
        "proposal_sha256": "",
    }
    proposal["proposal_sha256"] = _sha(_without(proposal, "proposal_sha256"))
    validate_binding_proposal_v7(proposal)
    return proposal


def validate_binding_proposal_v7(proposal: dict[str, Any]) -> dict[str, Any]:
    if (
        not isinstance(proposal, dict)
        or proposal.get("schema_version") != SCHEMA_VERSION_V7
        or proposal.get("status") != STATUS
        or proposal.get("canonical") is not False
        or proposal.get("target") != {"draft_schema_version": "draft-case-v0.1", "model": "equity_fcff"}
    ):
        raise CaseServiceError("market-price-aware proposal schema/status/target invalid / 시장가격-aware 제안 스키마·상태·대상 오류")
    base = proposal.get("base_proposal")
    package = proposal.get("market_price_package")
    if not isinstance(base, dict) or base.get("schema_version") != SCHEMA_VERSION_V6 or not isinstance(package, dict):
        raise CaseServiceError("market-price-aware v0.6 base/package missing / 시장가격-aware v0.6 base·package 누락")
    validate_binding_proposal_v6(base)
    _eligible_package(package)
    if proposal.get("base_proposal_sha256") != base.get("proposal_sha256") or proposal.get("source_market_price_package_sha256") != package.get("package_sha256"):
        raise CaseServiceError("market-price source SHA lineage mismatch / 시장가격 source SHA lineage 불일치")
    if proposal.get("policy") != _policy(base):
        raise CaseServiceError("market-price-aware policy/base mismatch / 시장가격-aware 정책·base 불일치")
    identity = proposal.get("identity")
    if identity != base.get("identity") or proposal.get("conflicts") != base.get("conflicts") or proposal.get("source_observation_sha256") != base.get("source_observation_sha256"):
        raise CaseServiceError("market-price proposal/base lineage mismatch / 시장가격 proposal·base lineage 불일치")
    if package.get("entity") != {"id": identity.get("entity_id"), "financial_scope": identity.get("financial_scope")} or package.get("as_of") != proposal["policy"]["as_of"]:
        raise CaseServiceError("market-price package identity/as_of mismatch / 시장가격 패키지 식별·as_of 불일치")
    monetary = identity.get("monetary_unit")
    if monetary is not None and package.get("currency") != str(monetary).upper():
        raise CaseServiceError("market-price package currency mismatch / 시장가격 패키지 통화 불일치")

    expected_baseline = copy.deepcopy(base["baseline_context"])
    expected_baseline["market_price_fact"] = _projection(package)
    if proposal.get("baseline_context") != expected_baseline:
        raise CaseServiceError("market-price baseline projection mismatch / 시장가격 baseline 투영 불일치")
    matrix = proposal.get("draft_input_matrix")
    if not isinstance(matrix, list) or len(matrix) != len(MATERIAL_FIELDS) or {item.get("field") for item in matrix if isinstance(item, dict)} != set(MATERIAL_FIELDS):
        raise CaseServiceError("market-price-aware binding matrix incomplete / 시장가격-aware 바인딩 matrix 불완전")
    base_by = {item["field"]: item for item in base["draft_input_matrix"]}
    by = {item["field"]: item for item in matrix}
    for field in MATERIAL_FIELDS:
        if field == "market_price":
            if by[field] != _decision(package):
                raise CaseServiceError("market-price DIRECT_BIND lineage/classification mismatch / 시장가격 DIRECT_BIND lineage·판정 불일치")
        elif by[field] != base_by[field]:
            raise CaseServiceError("M27 may replace only market_price classification / M27은 market_price 판정만 변경 가능")
    if proposal.get("completeness") != _counts(matrix):
        raise CaseServiceError("market-price completeness mismatch / 시장가격 completeness 불일치")
    expected = _sha(_without(proposal, "proposal_sha256"))
    if proposal.get("proposal_sha256") != expected:
        raise CaseServiceError("market-price-aware proposal SHA mismatch / 시장가격-aware proposal SHA 불일치")
    return {
        "status": "PASS_MARKET_PRICE_AWARE_BINDING_PROPOSAL_VALIDATION",
        "canonical": False,
        "proposal_sha256": expected,
        "direct_bind_count": proposal["completeness"]["direct_bind_count"],
        "unresolved_count": proposal["completeness"]["unresolved_count"],
    }


def validate_binding_proposal_any(proposal: dict[str, Any]) -> dict[str, Any]:
    if isinstance(proposal, dict) and proposal.get("schema_version") == SCHEMA_VERSION_V7:
        return validate_binding_proposal_v7(proposal)
    from valuation_hub.forecast_draft_binding import validate_binding_proposal_any as validate_binding_proposal_any_v6

    return validate_binding_proposal_any_v6(proposal)
