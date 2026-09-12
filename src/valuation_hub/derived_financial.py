"""Governed derived financial evidence / 거버넌스 파생재무근거.

Only semantically exact arithmetic relationships are derived. Derived historical
facts remain noncanonical evidence and never become forecast assumptions by
arithmetic alone.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from math import isfinite
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.financial_normalization import validate_financial_observation

DERIVED_SCHEMA_VERSION = "derived-financial-evidence-v0.1"
DERIVED_STATUS = "DERIVED_FINANCIAL_EVIDENCE"
DERIVED_CLASSES = {"DERIVED_FACT", "DERIVED_FACT_CANDIDATE"}
DERIVATIONS: dict[str, tuple[str, str, str]] = {
    "historical_operating_margin": ("operating_income", "revenue", "HISTORICAL_OPERATING_MARGIN_V01"),
    "historical_net_income_margin": ("net_income", "revenue", "HISTORICAL_NET_INCOME_MARGIN_V01"),
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result.pop(key, None)
    return result


def _number(value: Any, field: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
        raise CaseServiceError(f"{field} must be finite numeric / {field} 유한 숫자 필요")
    return value


def _authority(inputs: list[dict[str, Any]]) -> str:
    classes = [item.get("class") for item in inputs]
    if any(value not in {"NORMALIZED_FACT", "NORMALIZED_FACT_CANDIDATE"} for value in classes):
        raise CaseServiceError("derived evidence requires normalized fact inputs / 파생근거는 정규화 fact 입력 필요")
    return "DERIVED_FACT" if all(value == "NORMALIZED_FACT" for value in classes) else "DERIVED_FACT_CANDIDATE"


def _compatible(left: dict[str, Any], right: dict[str, Any]) -> None:
    left_entity, right_entity = left.get("entity"), right.get("entity")
    if not isinstance(left_entity, dict) or not isinstance(right_entity, dict):
        raise CaseServiceError("derived evidence entity identity missing / 파생근거 entity 식별 누락")
    if left_entity.get("id") != right_entity.get("id"):
        raise CaseServiceError("derived evidence entity mismatch / 파생근거 entity 불일치")
    if left_entity.get("financial_scope") != right_entity.get("financial_scope"):
        raise CaseServiceError("derived evidence financial scope mismatch / 파생근거 재무범위 불일치")
    if left.get("unit") != right.get("unit"):
        raise CaseServiceError("derived evidence source unit mismatch / 파생근거 원천 unit 불일치")
    if left.get("period") != right.get("period"):
        raise CaseServiceError("derived evidence period identity mismatch / 파생근거 기간식별 불일치")


def derive_historical_margin(numerator: dict[str, Any], revenue: dict[str, Any], *, metric: str) -> dict[str, Any]:
    """Derive one exact historical margin ratio / 역사적 마진 ratio 파생."""
    if metric not in DERIVATIONS:
        raise CaseServiceError(f"unsupported derived metric / 미지원 파생지표: {metric}")
    expected_numerator, expected_denominator, rule = DERIVATIONS[metric]
    validate_financial_observation(numerator)
    validate_financial_observation(revenue)
    if numerator.get("metric") != expected_numerator:
        raise CaseServiceError(f"{metric} requires {expected_numerator} numerator / 분자 지표 오류")
    if revenue.get("metric") != expected_denominator:
        raise CaseServiceError(f"{metric} requires revenue denominator / 분모는 revenue 필요")
    _compatible(numerator, revenue)
    num = _number(numerator.get("value"), "numerator value")
    den = _number(revenue.get("value"), "revenue value")
    if den == 0:
        raise CaseServiceError("revenue denominator must be nonzero / revenue 분모는 0일 수 없음")
    value = num / den
    if not isfinite(float(value)):
        raise CaseServiceError("derived ratio must be finite / 파생 ratio 유한값 필요")
    result: dict[str, Any] = {
        "schema_version": DERIVED_SCHEMA_VERSION,
        "status": DERIVED_STATUS,
        "canonical": False,
        "class": _authority([numerator, revenue]),
        "metric": metric,
        "value": value,
        "unit": "ratio",
        "entity": {
            "id": numerator["entity"]["id"],
            "financial_scope": numerator["entity"]["financial_scope"],
        },
        "period": copy.deepcopy(numerator["period"]),
        "derivation": {
            "rule": rule,
            "formula": f"{expected_numerator} / revenue",
            "numerator_metric": expected_numerator,
            "denominator_metric": "revenue",
            "numerator_value": num,
            "denominator_value": den,
            "source_unit": numerator["unit"],
            "source_observation_sha256": {
                "numerator": numerator["observation_sha256"],
                "denominator": revenue["observation_sha256"],
            },
            "source_classes": [numerator["class"], revenue["class"]],
        },
        "semantic_boundary": {
            "historical_only": True,
            "forecast_direct_bind": False,
            "warning_en": "Historical derived ratio is evidence context, not a forecast assumption.",
            "warning_ko": "역사적 파생 ratio는 근거 context이며 미래 가정이 아닙니다.",
        },
        "derived_sha256": "",
    }
    result["derived_sha256"] = _sha(_without(result, "derived_sha256"))
    validate_derived_financial_evidence(result)
    return result


def derive_historical_operating_margin(operating_income: dict[str, Any], revenue: dict[str, Any]) -> dict[str, Any]:
    return derive_historical_margin(operating_income, revenue, metric="historical_operating_margin")


def derive_historical_net_income_margin(net_income: dict[str, Any], revenue: dict[str, Any]) -> dict[str, Any]:
    return derive_historical_margin(net_income, revenue, metric="historical_net_income_margin")


def validate_derived_financial_evidence(value: dict[str, Any]) -> dict[str, Any]:
    """Validate hash, arithmetic, authority, and semantic boundary / 파생근거 검증."""
    if not isinstance(value, dict) or value.get("schema_version") != DERIVED_SCHEMA_VERSION or value.get("status") != DERIVED_STATUS:
        raise CaseServiceError("derived financial evidence schema/status invalid / 파생재무근거 스키마·상태 오류")
    if value.get("canonical") is not False or value.get("class") not in DERIVED_CLASSES:
        raise CaseServiceError("derived financial evidence authority invalid / 파생재무근거 권위 오류")
    metric = value.get("metric")
    if metric not in DERIVATIONS or value.get("unit") != "ratio":
        raise CaseServiceError("derived metric/unit invalid / 파생지표·unit 오류")
    entity, period, derivation, boundary = value.get("entity"), value.get("period"), value.get("derivation"), value.get("semantic_boundary")
    if not isinstance(entity, dict) or not isinstance(entity.get("id"), str) or not entity.get("id") or not isinstance(entity.get("financial_scope"), str) or not entity.get("financial_scope"):
        raise CaseServiceError("derived entity identity invalid / 파생 entity 식별 오류")
    if not isinstance(period, dict) or not isinstance(derivation, dict) or not isinstance(boundary, dict):
        raise CaseServiceError("derived period/lineage missing / 파생 기간·lineage 누락")
    expected_num, _, expected_rule = DERIVATIONS[metric]
    if derivation.get("rule") != expected_rule or derivation.get("formula") != f"{expected_num} / revenue" or derivation.get("numerator_metric") != expected_num or derivation.get("denominator_metric") != "revenue":
        raise CaseServiceError("derived formula contract invalid / 파생식 계약 오류")
    num = _number(derivation.get("numerator_value"), "derived numerator")
    den = _number(derivation.get("denominator_value"), "derived denominator")
    if den == 0 or _number(value.get("value"), "derived value") != num / den:
        raise CaseServiceError("derived arithmetic mismatch / 파생 산술 불일치")
    hashes = derivation.get("source_observation_sha256")
    if not isinstance(hashes, dict) or any(not isinstance(hashes.get(key), str) or not SHA256_RE.fullmatch(hashes[key]) for key in ("numerator", "denominator")):
        raise CaseServiceError("derived source hashes invalid / 파생 source hash 오류")
    classes = derivation.get("source_classes")
    if not isinstance(classes, list) or len(classes) != 2 or any(item not in {"NORMALIZED_FACT", "NORMALIZED_FACT_CANDIDATE"} for item in classes):
        raise CaseServiceError("derived source classes invalid / 파생 source 권위 오류")
    expected_class = "DERIVED_FACT" if all(item == "NORMALIZED_FACT" for item in classes) else "DERIVED_FACT_CANDIDATE"
    if value.get("class") != expected_class:
        raise CaseServiceError("derived authority propagation mismatch / 파생 권위전파 불일치")
    if boundary.get("historical_only") is not True or boundary.get("forecast_direct_bind") is not False:
        raise CaseServiceError("derived semantic boundary invalid / 파생 의미경계 오류")
    sha = value.get("derived_sha256")
    if not isinstance(sha, str) or not SHA256_RE.fullmatch(sha) or sha != _sha(_without(value, "derived_sha256")):
        raise CaseServiceError("derived SHA-256 mismatch / 파생 SHA-256 불일치")
    return {
        "status": "PASS_DERIVED_FINANCIAL_EVIDENCE_VALIDATION",
        "metric": metric,
        "class": value["class"],
        "historical_only": True,
        "forecast_direct_bind": False,
        "derived_sha256": sha,
    }
