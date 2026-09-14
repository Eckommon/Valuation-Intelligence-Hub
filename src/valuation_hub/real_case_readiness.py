"""M30-D deterministic real-equity readiness manifest / 실기업 준비도 manifest.

This module does not acquire sources, create human approvals, mutate Drafts, or write
canonical state. It converts the already-governed M13-M29 contract into an explicit
13-field prerequisite DAG and optionally projects a validated M30-B v0.2 preflight.
"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import date
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_binding import MATERIAL_FIELDS
from valuation_hub.forecast_draft_binding import FORECAST_FIELDS
from valuation_hub.real_case_preflight_m30b import validate_real_equity_source_preflight_v2
from valuation_hub.terminal_growth_assumption import REQUIRED_ANCHORS
from valuation_hub.wacc_assumption import REQUIRED_METRICS

SCHEMA_VERSION = "real-equity-readiness-manifest-v0.1"
STATUS = "REAL_EQUITY_READINESS_EVALUATED"
DECISION_HOLD = "HOLD_AT_GOVERNED_BOUNDARIES"
READY = "READY"
AWAITING_REAL_SOURCE = "AWAITING_REAL_SOURCE"
AWAITING_HUMAN_REVIEW = "AWAITING_HUMAN_REVIEW"
AWAITING_DEPENDENCY = "AWAITING_DEPENDENCY"
BLOCKED = "BLOCKED"
ALLOWED_STATES = {READY, AWAITING_REAL_SOURCE, AWAITING_HUMAN_REVIEW, AWAITING_DEPENDENCY, BLOCKED}

AUTHORITY_BY_FIELD = {
    "market_price": "FACT",
    "equity.diluted_shares": "DERIVED",
    "equity.debt": "DERIVED",
    "equity.cash": "NORMALIZED_FACT",
    "equity.minority_interest": "NORMALIZED_FACT",
    "scenario.wacc": "ASSUMPTION",
    "scenario.terminal_growth": "ASSUMPTION",
    "scenario.years.revenue": "ASSUMPTION",
    "scenario.years.ebit_margin": "ASSUMPTION",
    "scenario.years.tax_rate": "ASSUMPTION",
    "scenario.years.depreciation_amortization": "ASSUMPTION",
    "scenario.years.capex": "ASSUMPTION",
    "scenario.years.delta_nwc": "ASSUMPTION",
}

FIELD_PREREQUISITE = {
    "market_price": "m27.market_price.reviewed_fact",
    "equity.cash": "m15.cash.reviewed_normalized_fact",
    "equity.diluted_shares": "m22.shares.diluted_bridge",
    "equity.debt": "m30p1.debt.binding_context",
    "equity.minority_interest": "m28.minority_interest.reviewed_fact",
    "scenario.wacc": "m24.wacc.reviewed_package",
    "scenario.terminal_growth": "m25.terminal_growth.reviewed_package",
    **{field: "m26.forecast.reviewed_package" for field in FORECAST_FIELDS},
}


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    out = copy.deepcopy(value)
    out.pop(key, None)
    return out


def _text(value: Any, field: str, *, upper: bool = False) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CaseServiceError(f"{field} required / {field} 필요")
    text = value.strip()
    return text.upper() if upper else text


def _date(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise CaseServiceError(f"{field} YYYY-MM-DD required / {field} 날짜 필요")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise CaseServiceError(f"{field} invalid / {field} 날짜 오류") from exc
    if parsed.isoformat() != value:
        raise CaseServiceError(f"{field} canonical YYYY-MM-DD required / {field} 정규 날짜 필요")
    return value


def _cik(value: Any) -> str:
    text = str(value).strip()
    if not text.isdigit() or len(text) > 10:
        raise CaseServiceError("CIK must be numeric up to 10 digits / CIK 숫자 형식 오류")
    return text.zfill(10)


def _target(*, case_id: str, legal_name: str, ticker: str, exchange: str, cik: str | int,
            financial_period_end: str, valuation_as_of: str, form: str) -> dict[str, Any]:
    return {
        "case_id": _text(case_id, "case_id"),
        "legal_name": _text(legal_name, "legal_name"),
        "ticker": _text(ticker, "ticker", upper=True),
        "exchange": _text(exchange, "exchange", upper=True),
        "cik": _cik(cik),
        "financial_period_end": _date(financial_period_end, "financial_period_end"),
        "valuation_as_of": _date(valuation_as_of, "valuation_as_of"),
        "form": _text(form, "form", upper=True),
    }


def _node(node_id: str, kind: str, authority: str, state: str, dependencies: list[str], *,
          requires_real_source: bool = False, requires_human_review: bool = False) -> dict[str, Any]:
    if state not in ALLOWED_STATES:
        raise CaseServiceError("readiness node state invalid / 준비도 node 상태 오류")
    return {
        "node_id": node_id,
        "kind": kind,
        "authority": authority,
        "state": state,
        "dependencies": dependencies,
        "requires_real_source": requires_real_source,
        "requires_human_review": requires_human_review,
    }


def _preflight_projection(preflight: dict[str, Any] | None) -> tuple[dict[str, Any] | None, dict[str, Any], list[dict[str, Any]], bool]:
    if preflight is None:
        return None, {}, [{"code": "REAL_SEC_PREFLIGHT_NOT_SUPPLIED", "detail": "Real M30-B v0.2 preflight has not been supplied."}], False
    checked = validate_real_equity_source_preflight_v2(preflight)
    projection = {
        "schema_version": preflight["schema_version"],
        "status": preflight["status"],
        "preflight_sha256": preflight["preflight_sha256"],
        "blocker_count": checked["blocker_count"],
        "successor_debt_candidate_available": checked["successor_debt_candidate_available"],
    }
    checks = preflight["checks"]
    collision = any(item.get("code") == "REGISTRY_CASE_ID_COLLISION" for item in preflight["blockers"] if isinstance(item, dict))
    return projection, checks, copy.deepcopy(preflight["blockers"]), collision


def _require_target_match(target: dict[str, Any], preflight: dict[str, Any] | None) -> None:
    if preflight is None:
        return
    source = preflight.get("target")
    if not isinstance(source, dict):
        raise CaseServiceError("M30-B target missing / M30-B target 누락")
    for key in ("case_id", "legal_name", "ticker", "exchange", "cik", "financial_period_end", "valuation_as_of", "form"):
        if key in source and str(source[key]).strip().upper() != str(target[key]).strip().upper():
            raise CaseServiceError(f"readiness target/preflight mismatch: {key} / 준비도 target·preflight 불일치: {key}")


def _nodes(preflight: dict[str, Any] | None, checks: dict[str, Any], collision: bool) -> list[dict[str, Any]]:
    if collision:
        blocked = BLOCKED
    else:
        blocked = None
    snapshot_ready = preflight is not None and checks.get("sec_snapshot") is not None
    cash_available = preflight is not None and checks.get("cash_candidate") is not None
    shares_available = preflight is not None and checks.get("shares_candidate") is not None
    debt_available = preflight is not None and checks.get("sec_aggregate_debt_candidate") is not None
    nci_available = preflight is not None and checks.get("minority_interest_candidate") is not None

    nodes: list[dict[str, Any]] = [
        _node("m13.sec.companyfacts_snapshot", "SOURCE_SNAPSHOT", "FACT_CANDIDATE_SOURCE", blocked or (READY if snapshot_ready else AWAITING_REAL_SOURCE), [], requires_real_source=True),
        _node("m30b.real_source_preflight", "PREFLIGHT", "GOVERNANCE_CHECK", blocked or (READY if preflight is not None else AWAITING_DEPENDENCY), ["m13.sec.companyfacts_snapshot"]),
        _node("m27.market_price.source", "SOURCE_INPUT", "FACT_CANDIDATE", blocked or AWAITING_REAL_SOURCE, [], requires_real_source=True),
        _node("m27.market_price.reviewed_fact", "REVIEWED_ARTIFACT", "FACT", blocked or AWAITING_DEPENDENCY, ["m27.market_price.source"], requires_human_review=True),
        _node("m15.cash.reviewed_normalized_fact", "REVIEWED_ARTIFACT", "NORMALIZED_FACT", blocked or (AWAITING_HUMAN_REVIEW if cash_available else AWAITING_REAL_SOURCE), ["m30b.real_source_preflight"], requires_real_source=True, requires_human_review=True),
        _node("m22.shares.diluted_bridge", "DERIVED_REVIEWED_ARTIFACT", "DERIVED", blocked or (AWAITING_HUMAN_REVIEW if shares_available else AWAITING_REAL_SOURCE), ["m30b.real_source_preflight"], requires_real_source=True, requires_human_review=True),
        _node("m30p1.debt.reviewed_profile", "REVIEWED_ARTIFACT", "NORMALIZED_FACT", blocked or (AWAITING_HUMAN_REVIEW if debt_available else AWAITING_REAL_SOURCE), ["m30b.real_source_preflight"], requires_real_source=True, requires_human_review=True),
        _node("m30p1.debt.binding_context", "DERIVED_BINDING_CONTEXT", "DERIVED", blocked or AWAITING_DEPENDENCY, ["m30p1.debt.reviewed_profile"]),
        _node("m28.minority_interest.reviewed_fact", "REVIEWED_ARTIFACT", "NORMALIZED_FACT", blocked or (AWAITING_HUMAN_REVIEW if nci_available else AWAITING_REAL_SOURCE), ["m30b.real_source_preflight"], requires_real_source=True, requires_human_review=True),
    ]
    for metric in REQUIRED_METRICS:
        nodes.append(_node(f"m24.wacc.source.{metric}", "SOURCE_INPUT", "SOURCE_CLAIM", blocked or AWAITING_REAL_SOURCE, [], requires_real_source=True))
    wacc_sources = [f"m24.wacc.source.{metric}" for metric in REQUIRED_METRICS]
    nodes.extend([
        _node("m24.wacc.candidate", "ASSUMPTION_CANDIDATE", "ASSUMPTION_CANDIDATE", blocked or AWAITING_DEPENDENCY, wacc_sources),
        _node("m24.wacc.reviewed_package", "REVIEWED_ASSUMPTION", "ASSUMPTION", blocked or AWAITING_DEPENDENCY, ["m24.wacc.candidate"], requires_human_review=True),
    ])
    for anchor in REQUIRED_ANCHORS:
        nodes.append(_node(f"m25.terminal_growth.anchor.{anchor}", "SOURCE_INPUT", "SOURCE_CLAIM", blocked or AWAITING_REAL_SOURCE, [], requires_real_source=True))
    tg_anchors = [f"m25.terminal_growth.anchor.{anchor}" for anchor in REQUIRED_ANCHORS]
    nodes.extend([
        _node("m25.terminal_growth.candidate", "ASSUMPTION_CANDIDATE", "ASSUMPTION_CANDIDATE", blocked or AWAITING_DEPENDENCY, ["m24.wacc.reviewed_package", *tg_anchors]),
        _node("m25.terminal_growth.reviewed_package", "REVIEWED_ASSUMPTION", "ASSUMPTION", blocked or AWAITING_DEPENDENCY, ["m25.terminal_growth.candidate"], requires_human_review=True),
        _node("m26.forecast.candidate", "ATOMIC_ASSUMPTION_BLOCK", "ASSUMPTION_CANDIDATE", blocked or AWAITING_HUMAN_REVIEW, [], requires_human_review=True),
        _node("m26.forecast.reviewed_package", "REVIEWED_ASSUMPTION", "ASSUMPTION", blocked or AWAITING_DEPENDENCY, ["m26.forecast.candidate"], requires_human_review=True),
    ])
    direct_prereqs = [
        "m27.market_price.reviewed_fact", "m15.cash.reviewed_normalized_fact", "m22.shares.diluted_bridge",
        "m30p1.debt.binding_context", "m28.minority_interest.reviewed_fact", "m24.wacc.reviewed_package",
        "m25.terminal_growth.reviewed_package", "m26.forecast.reviewed_package",
    ]
    nodes.extend([
        _node("m28.binding_proposal_v08", "BINDING_PROPOSAL", "GOVERNANCE_PROJECTION", blocked or AWAITING_DEPENDENCY, direct_prereqs),
        _node("m28.human_binding_approval", "HUMAN_APPROVAL", "HUMAN_DECISION", blocked or AWAITING_DEPENDENCY, ["m28.binding_proposal_v08"], requires_human_review=True),
        _node("m28.complete_bound_result", "BOUND_DRAFT_RESULT", "NONCANONICAL_RESULT", blocked or AWAITING_DEPENDENCY, ["m28.binding_proposal_v08", "m28.human_binding_approval"]),
        _node("m29.promotion_candidate_v02", "PROMOTION_CANDIDATE", "GOVERNANCE_PROJECTION", blocked or AWAITING_DEPENDENCY, ["m28.complete_bound_result"]),
        _node("m10.promotion_package", "PROMOTION_PACKAGE", "HUMAN_REVIEWED_PACKAGE", blocked or AWAITING_DEPENDENCY, ["m29.promotion_candidate_v02"], requires_human_review=True),
        _node("m29.admission_bundle", "ADMISSION_BUNDLE", "GOVERNANCE_PROJECTION", blocked or AWAITING_DEPENDENCY, ["m10.promotion_package"]),
        _node("m29.guarded_change_plan", "REPOSITORY_CHANGE_PLAN", "GOVERNANCE_PROJECTION", blocked or AWAITING_DEPENDENCY, ["m29.admission_bundle"]),
    ])
    return nodes


def _field_state(field: str, preflight: dict[str, Any] | None, checks: dict[str, Any], collision: bool) -> str:
    if collision:
        return BLOCKED
    if field == "market_price":
        return AWAITING_REAL_SOURCE
    if field == "equity.cash":
        return AWAITING_HUMAN_REVIEW if preflight is not None and checks.get("cash_candidate") is not None else AWAITING_REAL_SOURCE
    if field == "equity.diluted_shares":
        return AWAITING_HUMAN_REVIEW if preflight is not None and checks.get("shares_candidate") is not None else AWAITING_REAL_SOURCE
    if field == "equity.debt":
        return AWAITING_HUMAN_REVIEW if preflight is not None and checks.get("sec_aggregate_debt_candidate") is not None else AWAITING_REAL_SOURCE
    if field == "equity.minority_interest":
        return AWAITING_HUMAN_REVIEW if preflight is not None and checks.get("minority_interest_candidate") is not None else AWAITING_REAL_SOURCE
    if field == "scenario.wacc":
        return AWAITING_REAL_SOURCE
    if field == "scenario.terminal_growth" or field in FORECAST_FIELDS:
        return AWAITING_DEPENDENCY
    raise CaseServiceError(f"unknown material field / 알 수 없는 material field: {field}")


def _fields(preflight: dict[str, Any] | None, checks: dict[str, Any], collision: bool) -> list[dict[str, Any]]:
    return [
        {
            "field": field,
            "required_authority": AUTHORITY_BY_FIELD[field],
            "prerequisite_node": FIELD_PREREQUISITE[field],
            "state": _field_state(field, preflight, checks, collision),
        }
        for field in MATERIAL_FIELDS
    ]


def _validate_dag(nodes: list[dict[str, Any]]) -> None:
    if not isinstance(nodes, list) or not nodes:
        raise CaseServiceError("readiness DAG nodes required / 준비도 DAG node 필요")
    ids = [item.get("node_id") for item in nodes if isinstance(item, dict)]
    if len(ids) != len(nodes) or any(not isinstance(node_id, str) or not node_id for node_id in ids) or len(set(ids)) != len(ids):
        raise CaseServiceError("readiness DAG node ids must be unique / 준비도 DAG node id 고유성 오류")
    known = set(ids)
    graph: dict[str, list[str]] = {}
    for item in nodes:
        state = item.get("state")
        if state not in ALLOWED_STATES:
            raise CaseServiceError("readiness DAG node state invalid / 준비도 DAG node 상태 오류")
        deps = item.get("dependencies")
        if not isinstance(deps, list) or any(not isinstance(dep, str) or dep not in known for dep in deps):
            raise CaseServiceError("readiness DAG unknown dependency / 준비도 DAG 미등록 dependency")
        graph[item["node_id"]] = deps
    visiting: set[str] = set()
    visited: set[str] = set()

    def walk(node_id: str) -> None:
        if node_id in visiting:
            raise CaseServiceError("readiness DAG cycle detected / 준비도 DAG 순환 dependency")
        if node_id in visited:
            return
        visiting.add(node_id)
        for dep in graph[node_id]:
            walk(dep)
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in ids:
        walk(node_id)


def _next_actions(preflight: dict[str, Any] | None, checks: dict[str, Any], blockers: list[dict[str, Any]], collision: bool) -> list[str]:
    if collision:
        return ["RESOLVE_REGISTRY_CASE_ID_COLLISION"]
    actions: list[str] = []
    if preflight is None:
        actions.extend(["CAPTURE_REAL_M13_SEC_COMPANYFACTS", "RUN_M30B_REAL_SOURCE_PREFLIGHT_V2"])
    elif blockers:
        actions.append("RESOLVE_M30B_REAL_SOURCE_BLOCKERS")
    if preflight is not None:
        if checks.get("cash_candidate") is not None:
            actions.append("REVIEW_AND_NORMALIZE_CASH_EVIDENCE")
        if checks.get("shares_candidate") is not None:
            actions.append("BUILD_AND_HUMAN_REVIEW_DILUTED_SHARE_BRIDGE")
        if checks.get("sec_aggregate_debt_candidate") is not None:
            actions.append("PERFORM_M30P1_DEBT_SEMANTIC_REVIEW")
        if checks.get("minority_interest_candidate") is not None:
            actions.append("PERFORM_M28_MINORITY_INTEREST_REVIEW")
    actions.extend([
        "CAPTURE_VALUATION_DATE_MARKET_PRICE_SOURCE",
        "COLLECT_M24_SEVEN_WACC_SOURCE_INPUTS",
        "COLLECT_M25_TWO_LONG_RUN_MACRO_ANCHORS",
        "AUTHOR_AND_HUMAN_REVIEW_M26_ATOMIC_FORECAST_BLOCK",
    ])
    return list(dict.fromkeys(actions))


def _assemble(target: dict[str, Any], preflight: dict[str, Any] | None) -> dict[str, Any]:
    projection, checks, blockers, collision = _preflight_projection(preflight)
    _require_target_match(target, preflight)
    nodes = _nodes(preflight, checks, collision)
    _validate_dag(nodes)
    fields = _fields(preflight, checks, collision)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "canonical": False,
        "decision": DECISION_HOLD,
        "target": copy.deepcopy(target),
        "source_preflight": copy.deepcopy(preflight),
        "source_preflight_projection": projection,
        "fields": fields,
        "prerequisite_dag": nodes,
        "blockers": blockers,
        "human_review_boundary": {
            "automatic_approval_forbidden": True,
            "reviewer_must_be_explicit": True,
            "review_timestamp_must_be_explicit": True,
            "review_state_may_be_inferred": False,
            "draft_mutation": False,
            "registry_write": False,
            "canonical_write": False,
        },
        "next_actions": _next_actions(preflight, checks, blockers, collision),
        "manifest_sha256": "",
    }


def build_real_equity_readiness_manifest(*, case_id: str, legal_name: str, ticker: str, exchange: str,
                                         cik: str | int, financial_period_end: str, valuation_as_of: str,
                                         form: str = "10-Q", preflight: dict[str, Any] | None = None) -> dict[str, Any]:
    target = _target(
        case_id=case_id, legal_name=legal_name, ticker=ticker, exchange=exchange, cik=cik,
        financial_period_end=financial_period_end, valuation_as_of=valuation_as_of, form=form,
    )
    manifest = _assemble(target, preflight)
    manifest["manifest_sha256"] = _sha(_without(manifest, "manifest_sha256"))
    validate_real_equity_readiness_manifest(manifest)
    return manifest


def validate_real_equity_readiness_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(manifest, dict) or manifest.get("schema_version") != SCHEMA_VERSION or manifest.get("status") != STATUS:
        raise CaseServiceError("readiness manifest schema/status invalid / 준비도 manifest 스키마·상태 오류")
    if manifest.get("canonical") is not False or manifest.get("decision") != DECISION_HOLD:
        raise CaseServiceError("readiness manifest authority invalid / 준비도 manifest 권위 오류")
    target = manifest.get("target")
    if not isinstance(target, dict):
        raise CaseServiceError("readiness target missing / 준비도 target 누락")
    normalized_target = _target(**target)
    if target != normalized_target:
        raise CaseServiceError("readiness target normalization mismatch / 준비도 target 정규화 불일치")
    fields = manifest.get("fields")
    if not isinstance(fields, list) or [item.get("field") for item in fields if isinstance(item, dict)] != list(MATERIAL_FIELDS):
        raise CaseServiceError("readiness manifest must cover exact 13 material fields / 준비도 manifest 13개 material field 정확 일치 필요")
    if set(AUTHORITY_BY_FIELD) != set(MATERIAL_FIELDS) or set(FIELD_PREREQUISITE) != set(MATERIAL_FIELDS):
        raise CaseServiceError("internal readiness field contract drift / 내부 준비도 field 계약 drift")
    _validate_dag(manifest.get("prerequisite_dag"))
    preflight = manifest.get("source_preflight")
    if preflight is not None and not isinstance(preflight, dict):
        raise CaseServiceError("source_preflight must be object or null / source_preflight 형식 오류")
    expected = _assemble(normalized_target, preflight)
    expected["manifest_sha256"] = manifest.get("manifest_sha256")
    if manifest != expected:
        raise CaseServiceError("readiness manifest deterministic reconstruction mismatch / 준비도 manifest 결정론적 재구성 불일치")
    sha = manifest.get("manifest_sha256")
    if not isinstance(sha, str) or len(sha) != 64 or sha != _sha(_without(manifest, "manifest_sha256")):
        raise CaseServiceError("readiness manifest SHA-256 mismatch / 준비도 manifest SHA-256 불일치")
    state_counts: dict[str, int] = {}
    for item in fields:
        state_counts[item["state"]] = state_counts.get(item["state"], 0) + 1
    return {
        "status": "PASS_REAL_EQUITY_READINESS_MANIFEST_VALIDATION",
        "canonical": False,
        "material_field_count": len(fields),
        "state_counts": state_counts,
        "dag_node_count": len(manifest["prerequisite_dag"]),
        "manifest_sha256": sha,
    }
