"""M29 complete governed equity handoff into promotion-candidate-v0.2.

This module is an additive successor to M9 promotion.py. Historical v0.1 behavior
is delegated unchanged. v0.2 accepts only a complete, human-approved M28 v0.8
bound Draft result and deterministically projects its governed authority/lineage
into the existing promotion-review flow.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime
from math import isclose
from typing import Any

from valuation_hub import promotion as legacy
from valuation_hub.binding_apply_m28 import validate_bound_draft_result
from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_binding import DIRECT_BIND, MATERIAL_FIELDS
from valuation_hub.draft_service import run_draft, validate_draft
from valuation_hub.evidence import ClaimClass, EvidenceRecord, EvidenceStatus, SourceTier, evaluate_canonical_promotion
from valuation_hub.minority_interest_draft_binding import SCHEMA_VERSION_V8

CANDIDATE_SCHEMA_VERSION_V2 = "promotion-candidate-v0.2"
CANDIDATE_STATUS = legacy.CANDIDATE_STATUS
READY_STATUS = legacy.READY_STATUS

OBSERVED_FIELD_CLASSES: dict[str, str] = {
    "market_price": "FACT",
    "equity.cash": "NORMALIZED_FACT",
    "equity.minority_interest": "NORMALIZED_FACT",
    "equity.debt": "DERIVED",
    "equity.diluted_shares": "DERIVED",
}
ALLOWED_V2_CLASSES = {"FACT", "NORMALIZED_FACT", "DERIVED", "ASSUMPTION"}
REVIEWABLE_SOURCE_TIERS = {"A", "B", "C"}
FORECAST_PATH_RE = re.compile(
    r"^equity\.scenarios\.[^.]+\.years\[\d+\]\.(revenue|ebit_margin|tax_rate|depreciation_amortization|capex|delta_nwc)$"
)
WACC_PATH_RE = re.compile(r"^equity\.scenarios\.[^.]+\.wacc$")
TERMINAL_GROWTH_PATH_RE = re.compile(r"^equity\.scenarios\.[^.]+\.terminal_growth$")


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _decision_by_field(proposal: dict[str, Any]) -> dict[str, dict[str, Any]]:
    matrix = proposal.get("draft_input_matrix")
    if not isinstance(matrix, list):
        raise CaseServiceError("binding matrix missing / 바인딩 matrix 누락")
    by: dict[str, dict[str, Any]] = {}
    for item in matrix:
        if not isinstance(item, dict) or not isinstance(item.get("field"), str):
            raise CaseServiceError("binding matrix row invalid / 바인딩 matrix 행 오류")
        field = item["field"]
        if field in by:
            raise CaseServiceError("duplicate binding decision / 중복 바인딩 판정")
        by[field] = item
    if set(by) != set(MATERIAL_FIELDS):
        raise CaseServiceError("complete material-field matrix required / 완전한 중요필드 matrix 필요")
    return by


def _complete_bound_result(result: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Revalidate and require an all-13-field M28 bound result."""
    checked = validate_bound_draft_result(result)
    if checked.get("canonical") is not False:
        raise CaseServiceError("source bound result must remain noncanonical / 원천 bound result는 비정식이어야 함")
    proposal = result.get("binding_proposal")
    approval = result.get("approval")
    draft_after = result.get("draft_after")
    if not isinstance(proposal, dict) or proposal.get("schema_version") != SCHEMA_VERSION_V8:
        raise CaseServiceError("M29 requires M28 v0.8 proposal / M29는 M28 v0.8 proposal 필요")
    if not isinstance(approval, dict) or not isinstance(draft_after, dict):
        raise CaseServiceError("complete approval/draft_after required / 완전한 승인·draft_after 필요")
    normalized = validate_draft(draft_after)
    if normalized.get("model") != "equity_fcff":
        raise CaseServiceError("M29 requires valid equity_fcff draft_after / M29는 유효한 equity_fcff draft_after 필요")

    decisions = _decision_by_field(proposal)
    if any(item.get("state") != DIRECT_BIND for item in decisions.values()):
        raise CaseServiceError("all 13 material fields must be DIRECT_BIND / 13개 중요필드 모두 DIRECT_BIND 필요")
    if proposal.get("completeness", {}).get("direct_bind_count") != len(MATERIAL_FIELDS) or proposal.get("completeness", {}).get("unresolved_count") != 0:
        raise CaseServiceError("v0.8 completeness must be fully bound / v0.8 completeness 완전바인딩 필요")

    approved = approval.get("approved_fields")
    if not isinstance(approved, list) or len(approved) != len(set(approved)) or set(approved) != set(MATERIAL_FIELDS):
        raise CaseServiceError("human approval must include exactly all 13 fields / 인간승인은 정확히 13개 필드 필요")
    diffs = result.get("applied_diffs")
    if not isinstance(diffs, list):
        raise CaseServiceError("applied_diffs required / applied_diffs 필요")
    diff_by: dict[str, dict[str, Any]] = {}
    for diff in diffs:
        if not isinstance(diff, dict) or not isinstance(diff.get("field"), str):
            raise CaseServiceError("applied diff invalid / 적용 diff 오류")
        field = diff["field"]
        if field in diff_by:
            raise CaseServiceError("duplicate applied diff field / 중복 적용 diff 필드")
        diff_by[field] = diff
    if set(diff_by) != set(MATERIAL_FIELDS):
        raise CaseServiceError("applied diffs must contain exactly all 13 fields / 적용 diff는 정확히 13개 필드 필요")
    if result.get("unresolved_binding_matrix") != []:
        raise CaseServiceError("complete bound result must have no unresolved matrix / 완전 bound result는 미해결 matrix가 없어야 함")
    if result.get("result_sha256") != checked.get("result_sha256"):
        raise CaseServiceError("bound-result SHA mismatch / bound-result SHA 불일치")
    return proposal, approval, copy.deepcopy(draft_after), decisions, diff_by


def _normalized_numeric_map(draft: dict[str, Any]) -> dict[str, float]:
    return legacy._material_numeric_map(validate_draft(draft))


def _normalized_numeric_paths(draft: dict[str, Any]) -> list[str]:
    return legacy._material_numeric_paths(validate_draft(draft))


def _expected_lineage(proposal: dict[str, Any], decision: dict[str, Any], diff: dict[str, Any]) -> dict[str, Any]:
    return {
        "proposal_sha256": proposal["proposal_sha256"],
        "proposal_decision": copy.deepcopy(decision),
        "applied_diff": copy.deepcopy(diff),
    }


def build_evidence_catalog_claim(
    bound_result: dict[str, Any],
    *,
    field: str,
    claim_id: str,
    metric: str,
    publisher: str,
    locator: str,
    tier: str,
    source_type: str | None = None,
    source_date: str | None = None,
) -> dict[str, Any]:
    """Build one descriptive evidence-catalog claim locked to exact bound lineage."""
    proposal, _, draft, decisions, diff_by = _complete_bound_result(bound_result)
    if field not in OBSERVED_FIELD_CLASSES:
        raise CaseServiceError("catalog supports only five observed fields / catalog은 5개 관측필드만 지원")
    values = _normalized_numeric_map(draft)
    if field not in values:
        raise CaseServiceError("observed field missing from Draft / Draft 관측필드 누락")
    for name, value, limit in (
        ("claim_id", claim_id, 200), ("metric", metric, 200), ("publisher", publisher, 300), ("locator", locator, 2000),
    ):
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
            raise CaseServiceError(f"{name} required/too long / {name} 필요·길이 오류")
    if tier not in REVIEWABLE_SOURCE_TIERS:
        raise CaseServiceError("Tier D/invalid source forbidden for M29 observed evidence / M29 관측근거 Tier D·잘못된 tier 금지")
    source: dict[str, Any] = {"publisher": publisher.strip(), "locator": locator.strip(), "tier": tier}
    if source_type is not None:
        if not isinstance(source_type, str) or not source_type.strip():
            raise CaseServiceError("source_type must be non-empty / source_type 비어있을 수 없음")
        source["type"] = source_type.strip()
    if source_date is not None:
        if not isinstance(source_date, str) or not source_date.strip():
            raise CaseServiceError("source_date must be non-empty / source_date 비어있을 수 없음")
        source["date"] = source_date.strip()
    return {
        "binding_field": field,
        "claim_id": claim_id.strip(),
        "class": OBSERVED_FIELD_CLASSES[field],
        "metric": metric.strip(),
        "value": values[field],
        "status": "CURRENT",
        "source": source,
        "lineage": _expected_lineage(proposal, decisions[field], diff_by[field]),
    }


def _catalog_index(
    catalog: list[dict[str, Any]],
    proposal: dict[str, Any],
    draft: dict[str, Any],
    decisions: dict[str, dict[str, Any]],
    diff_by: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    if not isinstance(catalog, list) or len(catalog) != len(OBSERVED_FIELD_CLASSES):
        raise CaseServiceError("evidence catalog must contain exactly five claims / 근거 catalog는 정확히 5개 claim 필요")
    values = _normalized_numeric_map(draft)
    indexed: dict[str, dict[str, Any]] = {}
    claim_ids: set[str] = set()
    records: list[EvidenceRecord] = []
    for item in catalog:
        if not isinstance(item, dict):
            raise CaseServiceError("catalog claim must be object / catalog claim 객체 필요")
        field = item.get("binding_field")
        if field not in OBSERVED_FIELD_CLASSES or field in indexed:
            raise CaseServiceError("catalog field duplicate/unsupported / catalog 필드 중복·미지원")
        claim_id = item.get("claim_id")
        metric = item.get("metric")
        if not isinstance(claim_id, str) or not claim_id.strip() or claim_id in claim_ids:
            raise CaseServiceError("catalog claim_id missing/duplicate / catalog claim_id 누락·중복")
        if not isinstance(metric, str) or not metric.strip():
            raise CaseServiceError("catalog metric required / catalog metric 필요")
        claim_ids.add(claim_id)
        expected_class = OBSERVED_FIELD_CLASSES[field]
        if item.get("class") != expected_class or item.get("status") != "CURRENT":
            raise CaseServiceError("catalog class/status mismatch / catalog class·status 불일치")
        value = item.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or field not in values or not isclose(float(value), values[field], rel_tol=1e-9, abs_tol=1e-9):
            raise CaseServiceError("catalog value cannot alter bound Draft value / catalog 값은 bound Draft 값을 변경할 수 없음")
        source = item.get("source")
        if not isinstance(source, dict) or not str(source.get("publisher", "")).strip() or not str(source.get("locator", "")).strip():
            raise CaseServiceError("catalog source publisher/locator required / catalog 출처 publisher·locator 필요")
        tier = str(source.get("tier", ""))
        if tier not in REVIEWABLE_SOURCE_TIERS:
            raise CaseServiceError("Tier D/invalid source cannot support M29 observed field / Tier D·잘못된 출처는 M29 관측필드 지원 불가")
        if item.get("lineage") != _expected_lineage(proposal, decisions[field], diff_by[field]):
            raise CaseServiceError("catalog lineage mismatch / catalog lineage 불일치")
        try:
            record = EvidenceRecord(
                claim_id=claim_id,
                claim_class=ClaimClass(expected_class),
                metric=metric,
                source_tier=SourceTier(tier),
                status=EvidenceStatus.CURRENT,
            )
        except ValueError as exc:
            raise CaseServiceError("catalog evidence enum invalid / catalog 근거 enum 오류") from exc
        records.append(record)
        indexed[field] = copy.deepcopy(item)
    if set(indexed) != set(OBSERVED_FIELD_CLASSES):
        raise CaseServiceError("catalog must cover exactly five observed fields / catalog는 정확히 5개 관측필드 coverage 필요")
    decision = evaluate_canonical_promotion(records)
    if not decision.allowed:
        raise CaseServiceError("catalog evidence gate blocked / catalog 근거게이트 차단: " + "; ".join(decision.reasons))
    return indexed


def _aggregate_field_for_path(path: str) -> str:
    if path in OBSERVED_FIELD_CLASSES:
        return path
    if WACC_PATH_RE.fullmatch(path):
        return "scenario.wacc"
    if TERMINAL_GROWTH_PATH_RE.fullmatch(path):
        return "scenario.terminal_growth"
    match = FORECAST_PATH_RE.fullmatch(path)
    if match:
        return f"scenario.years.{match.group(1)}"
    raise CaseServiceError(f"unmapped material numeric path / 미매핑 중요 숫자 path: {path}")


def _governance_projection(
    draft: dict[str, Any],
    catalog_by_field: dict[str, dict[str, Any]],
    proposal: dict[str, Any],
    decisions: dict[str, dict[str, Any]],
    diff_by: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = []
    for path in _normalized_numeric_paths(draft):
        aggregate = _aggregate_field_for_path(path)
        decision = decisions[aggregate]
        lineage = _expected_lineage(proposal, decision, diff_by[aggregate])
        if aggregate in OBSERVED_FIELD_CLASSES:
            claim = catalog_by_field[aggregate]
            bindings.append({
                "path": path,
                "binding_field": aggregate,
                "class": OBSERVED_FIELD_CLASSES[aggregate],
                "claim_ids": [claim["claim_id"]],
                "rationale": "governed observed input from complete M28 bound result / 완전 M28 bound result의 거버넌스 관측입력",
                "lineage": lineage,
            })
        else:
            if decision.get("source_class") != "ASSUMPTION":
                raise CaseServiceError("forecast/WACC/terminal input must remain ASSUMPTION / forecast·WACC·terminal 입력은 ASSUMPTION이어야 함")
            rationale = str(decision.get("rationale", "")).strip()
            if not rationale:
                raise CaseServiceError("governed assumption decision rationale missing / 거버넌스 가정 판정 rationale 누락")
            bindings.append({
                "path": path,
                "binding_field": aggregate,
                "class": "ASSUMPTION",
                "claim_ids": [],
                "rationale": rationale,
                "lineage": lineage,
            })
    return bindings


def build_complete_equity_candidate(bound_result: dict[str, Any], evidence_catalog: list[dict[str, Any]]) -> dict[str, Any]:
    proposal, _, draft, decisions, diff_by = _complete_bound_result(bound_result)
    catalog_by = _catalog_index(evidence_catalog, proposal, draft, decisions, diff_by)
    candidate = {
        "schema_version": CANDIDATE_SCHEMA_VERSION_V2,
        "status": CANDIDATE_STATUS,
        "canonical": False,
        "draft": copy.deepcopy(draft),
        "input_governance": _governance_projection(draft, catalog_by, proposal, decisions, diff_by),
        "evidence": [copy.deepcopy(catalog_by[field]) for field in OBSERVED_FIELD_CLASSES],
        "source_bound_result": copy.deepcopy(bound_result),
        "source_bound_result_sha256": bound_result["result_sha256"],
        "review": {"decision": "PENDING", "reviewer": None, "reviewed_at": None, "rationale": None, "scope_sha256": None},
    }
    validate_candidate_v2(candidate)
    return candidate


def _scope_payload_v2(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": candidate.get("schema_version"),
        "status": candidate.get("status"),
        "canonical": candidate.get("canonical"),
        "draft": candidate.get("draft"),
        "input_governance": candidate.get("input_governance"),
        "evidence": candidate.get("evidence"),
        "source_bound_result": candidate.get("source_bound_result"),
        "source_bound_result_sha256": candidate.get("source_bound_result_sha256"),
    }


def review_scope_sha256(candidate: dict[str, Any]) -> str:
    if isinstance(candidate, dict) and candidate.get("schema_version") == CANDIDATE_SCHEMA_VERSION_V2:
        return _sha(_scope_payload_v2(candidate))
    return legacy.review_scope_sha256(candidate)


def _validate_governance_rows(candidate: dict[str, Any], expected: list[dict[str, Any]]) -> None:
    rows = candidate.get("input_governance")
    if not isinstance(rows, list) or rows != expected:
        raise CaseServiceError("v0.2 input governance projection mismatch / v0.2 입력거버넌스 투영 불일치")
    if any(row.get("class") not in ALLOWED_V2_CLASSES for row in rows):
        raise CaseServiceError("v0.2 input class invalid / v0.2 입력 class 오류")
    paths = [row.get("path") for row in rows]
    if len(paths) != len(set(paths)):
        raise CaseServiceError("v0.2 governance path duplicate / v0.2 거버넌스 path 중복")


def validate_candidate_v2(candidate: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(candidate, dict) or candidate.get("schema_version") != CANDIDATE_SCHEMA_VERSION_V2:
        raise CaseServiceError("promotion candidate v0.2 schema required / promotion candidate v0.2 스키마 필요")
    if candidate.get("status") != CANDIDATE_STATUS or candidate.get("canonical") is not False:
        raise CaseServiceError("promotion candidate v0.2 state invalid / promotion candidate v0.2 상태 오류")
    source_result = candidate.get("source_bound_result")
    if not isinstance(source_result, dict):
        raise CaseServiceError("source bound result required / 원천 bound result 필요")
    proposal, _, draft, decisions, diff_by = _complete_bound_result(source_result)
    if candidate.get("source_bound_result_sha256") != source_result.get("result_sha256"):
        raise CaseServiceError("source bound-result SHA lineage mismatch / 원천 bound-result SHA lineage 불일치")
    if candidate.get("draft") != draft:
        raise CaseServiceError("candidate Draft must exactly equal bound draft_after / candidate Draft는 bound draft_after와 정확히 같아야 함")
    evidence = candidate.get("evidence")
    catalog_by = _catalog_index(evidence, proposal, draft, decisions, diff_by)
    expected_governance = _governance_projection(draft, catalog_by, proposal, decisions, diff_by)
    _validate_governance_rows(candidate, expected_governance)
    expected_paths = set(_normalized_numeric_paths(draft))
    actual_paths = {row["path"] for row in expected_governance}
    if actual_paths != expected_paths:
        raise CaseServiceError("v0.2 material path coverage mismatch / v0.2 중요 path coverage 불일치")
    review = candidate.get("review")
    if not isinstance(review, dict):
        raise CaseServiceError("review object required / review 객체 필요")
    return {
        "status": CANDIDATE_STATUS,
        "canonical": False,
        "ready_for_review": True,
        "review_scope_sha256": review_scope_sha256(candidate),
        "material_input_count": len(expected_paths),
        "binding_count": len(expected_governance),
        "evidence_count": len(catalog_by),
        "source_bound_result_sha256": source_result["result_sha256"],
        "blockers": [],
    }


def assess_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(candidate, dict) or candidate.get("schema_version") != CANDIDATE_SCHEMA_VERSION_V2:
        return legacy.assess_candidate(candidate)
    try:
        return validate_candidate_v2(candidate)
    except (CaseServiceError, TypeError, ValueError, KeyError) as exc:
        return {
            "status": CANDIDATE_STATUS,
            "canonical": False,
            "ready_for_review": False,
            "review_scope_sha256": None,
            "material_input_count": 0,
            "binding_count": 0,
            "evidence_count": 0,
            "blockers": [f"V2_VALIDATION:{exc}"],
        }


def validate_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    if isinstance(candidate, dict) and candidate.get("schema_version") == CANDIDATE_SCHEMA_VERSION_V2:
        return validate_candidate_v2(candidate)
    return legacy.validate_candidate(candidate)


def _valid_reviewed_at(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def promotion_check(candidate: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(candidate, dict) or candidate.get("schema_version") != CANDIDATE_SCHEMA_VERSION_V2:
        return legacy.promotion_check(candidate)
    assessment = validate_candidate_v2(candidate)
    review = candidate.get("review")
    if not isinstance(review, dict) or review.get("decision") != "APPROVE":
        raise CaseServiceError("explicit APPROVE review required / 명시적 APPROVE 검토 필요")
    reviewer = str(review.get("reviewer") or "").strip()
    rationale = str(review.get("rationale") or "").strip()
    if not reviewer or not rationale:
        raise CaseServiceError("reviewer and rationale required / reviewer·rationale 필요")
    if not _valid_reviewed_at(review.get("reviewed_at")):
        raise CaseServiceError("timezone-aware reviewed_at required / 시간대 포함 reviewed_at 필요")
    expected_hash = assessment["review_scope_sha256"]
    if str(review.get("scope_sha256") or "").strip().lower() != expected_hash:
        raise CaseServiceError("review scope hash mismatch; candidate changed after approval / 검토 scope hash 불일치")
    runtime = run_draft(candidate["draft"])
    return {
        "status": READY_STATUS,
        "canonical": False,
        "promotion_ready": True,
        "reviewer": reviewer,
        "reviewed_at": review["reviewed_at"],
        "review_scope_sha256": expected_hash,
        "model": runtime["model"],
        "name": runtime["name"],
        "grounding": "COMPLETE_GOVERNED_BOUND_RESULT",
        "source_bound_result_sha256": candidate["source_bound_result_sha256"],
        "next_action_en": "Stage the reviewed promotion package; canonical admission/apply remains separately governed.",
        "next_action_ko": "검토완료 승격 패키지를 스테이징하십시오. 정식 admission/apply는 별도 거버넌스가 유지됩니다.",
    }


def load_candidate_file(path):
    return legacy.load_candidate_file(path)
