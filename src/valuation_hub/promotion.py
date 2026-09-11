"""Reviewed Draft-to-candidate promotion protocol / 검토 기반 Draft→Candidate 승격 프로토콜.

M9 never writes canonical repository state. It builds a reviewable candidate,
requires governance for every material numeric model input, reuses the evidence
promotion gate, locks the reviewed scope with SHA-256, and can only declare a
candidate ready for a separately reviewed repository PR.

M9은 정식 저장소 상태를 기록하지 않는다. 모든 중요 숫자 모델 입력의 거버넌스를
요구하고 기존 근거 승격게이트를 재사용하며 SHA-256으로 검토 범위를 잠근 뒤,
별도 인간 검토 저장소 PR 준비 상태까지만 선언한다.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_service import run_draft, validate_draft
from valuation_hub.evidence import (
    ClaimClass,
    EvidenceRecord,
    EvidenceStatus,
    SourceTier,
    evaluate_canonical_promotion,
)

CANDIDATE_SCHEMA_VERSION = "promotion-candidate-v0.1"
CANDIDATE_STATUS = "CANDIDATE_REVIEW"
READY_STATUS = "REVIEW_APPROVED_READY_FOR_PR"
ALLOWED_INPUT_CLASSES = {"FACT", "NORMALIZED_FACT", "ASSUMPTION"}


def _material_numeric_paths(value: Any, path: str = "") -> list[str]:
    """Enumerate deterministic material numeric input paths / 중요 숫자 입력 경로 열거."""
    paths: list[str] = []
    if isinstance(value, bool):
        return paths
    if isinstance(value, (int, float)):
        leaf = path.rsplit(".", 1)[-1]
        if leaf != "year":
            paths.append(path)
        return paths
    if isinstance(value, dict):
        for key in sorted(value):
            if key == "canonical":
                continue
            child = f"{path}.{key}" if path else str(key)
            paths.extend(_material_numeric_paths(value[key], child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            child = f"{path}[{index}]"
            paths.extend(_material_numeric_paths(item, child))
    return paths


def build_candidate(draft_payload: dict[str, Any]) -> dict[str, Any]:
    """Build deterministic incomplete candidate skeleton / 결정론적 미완성 candidate 생성."""
    draft = validate_draft(draft_payload)
    bindings = [
        {"path": path, "class": "UNKNOWN", "claim_ids": [], "rationale": ""}
        for path in _material_numeric_paths(draft)
    ]
    return {
        "schema_version": CANDIDATE_SCHEMA_VERSION,
        "status": CANDIDATE_STATUS,
        "canonical": False,
        "draft": draft,
        "input_governance": bindings,
        "evidence": [],
        "review": {
            "decision": "PENDING",
            "reviewer": None,
            "reviewed_at": None,
            "rationale": None,
            "scope_sha256": None,
        },
    }


def _scope_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": candidate.get("schema_version"),
        "status": candidate.get("status"),
        "canonical": candidate.get("canonical"),
        "draft": candidate.get("draft"),
        "input_governance": candidate.get("input_governance"),
        "evidence": candidate.get("evidence"),
    }


def review_scope_sha256(candidate: dict[str, Any]) -> str:
    raw = json.dumps(
        _scope_payload(candidate),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _parse_evidence(candidate: dict[str, Any], blockers: list[str]) -> dict[str, tuple[dict[str, Any], EvidenceRecord]]:
    raw_evidence = candidate.get("evidence")
    if not isinstance(raw_evidence, list):
        blockers.append("EVIDENCE_MUST_BE_LIST")
        return {}
    indexed: dict[str, tuple[dict[str, Any], EvidenceRecord]] = {}
    records: list[EvidenceRecord] = []
    for index, item in enumerate(raw_evidence):
        if not isinstance(item, dict):
            blockers.append(f"EVIDENCE_NOT_OBJECT:{index}")
            continue
        claim_id = str(item.get("claim_id", "")).strip()
        metric = str(item.get("metric", "")).strip()
        if not claim_id or not metric:
            blockers.append(f"EVIDENCE_MISSING_ID_OR_METRIC:{index}")
            continue
        if claim_id in indexed:
            blockers.append(f"DUPLICATE_EVIDENCE_CLAIM:{claim_id}")
            continue
        source = item.get("source")
        if not isinstance(source, dict):
            blockers.append(f"EVIDENCE_SOURCE_REQUIRED:{claim_id}")
            continue
        publisher = str(source.get("publisher", "")).strip()
        locator = str(source.get("locator", "")).strip()
        if not publisher or not locator:
            blockers.append(f"EVIDENCE_SOURCE_INCOMPLETE:{claim_id}")
        try:
            claim_class = ClaimClass(str(item.get("class")))
            evidence_status = EvidenceStatus(str(item.get("status")))
            source_tier = SourceTier(str(source.get("tier")))
        except ValueError:
            blockers.append(f"EVIDENCE_ENUM_INVALID:{claim_id}")
            continue
        record = EvidenceRecord(
            claim_id=claim_id,
            claim_class=claim_class,
            metric=metric,
            source_tier=source_tier,
            status=evidence_status,
            waiver=item.get("waiver"),
        )
        indexed[claim_id] = (item, record)
        records.append(record)

    decision = evaluate_canonical_promotion(records)
    if not decision.allowed:
        blockers.extend(f"EVIDENCE_GATE:{reason}" for reason in decision.reasons)
    return indexed


def assess_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    """Return fail-closed readiness assessment without mutating candidate / 승격 준비도 평가."""
    blockers: list[str] = []
    if not isinstance(candidate, dict):
        raise CaseServiceError("candidate must be a JSON object / Candidate는 JSON 객체여야 합니다")
    if candidate.get("schema_version") != CANDIDATE_SCHEMA_VERSION:
        blockers.append("UNSUPPORTED_CANDIDATE_SCHEMA")
    if candidate.get("status") != CANDIDATE_STATUS:
        blockers.append("CANDIDATE_STATUS_INVALID")
    if candidate.get("canonical") is not False:
        blockers.append("CANDIDATE_CANNOT_BE_CANONICAL")

    draft = candidate.get("draft")
    try:
        normalized_draft = validate_draft(draft)
    except (CaseServiceError, TypeError) as exc:
        normalized_draft = None
        blockers.append(f"DRAFT_INVALID:{exc}")

    evidence_index = _parse_evidence(candidate, blockers)
    bindings = candidate.get("input_governance")
    if not isinstance(bindings, list):
        blockers.append("INPUT_GOVERNANCE_MUST_BE_LIST")
        bindings = []

    expected = set(_material_numeric_paths(normalized_draft)) if normalized_draft is not None else set()
    seen: dict[str, int] = {}
    for index, binding in enumerate(bindings):
        if not isinstance(binding, dict):
            blockers.append(f"BINDING_NOT_OBJECT:{index}")
            continue
        path = str(binding.get("path", "")).strip()
        if not path:
            blockers.append(f"BINDING_PATH_MISSING:{index}")
            continue
        seen[path] = seen.get(path, 0) + 1
        cls = str(binding.get("class", ""))
        claims = binding.get("claim_ids")
        rationale = str(binding.get("rationale", "")).strip()
        if cls not in ALLOWED_INPUT_CLASSES:
            blockers.append(f"INPUT_CLASS_INVALID:{path}:{cls or 'MISSING'}")
            continue
        if not isinstance(claims, list) or any(not isinstance(x, str) or not x.strip() for x in claims):
            blockers.append(f"CLAIM_IDS_INVALID:{path}")
            claims = []
        if len(claims) != len(set(claims)):
            blockers.append(f"DUPLICATE_CLAIM_LINK:{path}")
        if cls in {"FACT", "NORMALIZED_FACT"}:
            if not claims:
                blockers.append(f"FACT_WITHOUT_EVIDENCE:{path}")
            for claim_id in claims:
                pair = evidence_index.get(claim_id)
                if pair is None:
                    blockers.append(f"LINKED_EVIDENCE_MISSING:{path}:{claim_id}")
                    continue
                _, record = pair
                if record.claim_class.value != cls:
                    blockers.append(
                        f"EVIDENCE_CLASS_MISMATCH:{path}:{claim_id}:{record.claim_class.value}!={cls}"
                    )
        elif cls == "ASSUMPTION" and not rationale:
            blockers.append(f"ASSUMPTION_WITHOUT_RATIONALE:{path}")
        for claim_id in claims:
            if claim_id not in evidence_index:
                blockers.append(f"LINKED_EVIDENCE_MISSING:{path}:{claim_id}")

    duplicates = sorted(path for path, count in seen.items() if count > 1)
    blockers.extend(f"DUPLICATE_BINDING:{path}" for path in duplicates)
    actual = set(seen)
    blockers.extend(f"MISSING_BINDING:{path}" for path in sorted(expected - actual))
    blockers.extend(f"UNEXPECTED_BINDING:{path}" for path in sorted(actual - expected))

    try:
        scope_hash = review_scope_sha256(candidate)
    except (TypeError, ValueError) as exc:
        scope_hash = None
        blockers.append(f"REVIEW_SCOPE_NOT_HASHABLE:{exc}")

    deduped = list(dict.fromkeys(blockers))
    return {
        "status": CANDIDATE_STATUS,
        "canonical": False,
        "ready_for_review": not deduped,
        "review_scope_sha256": scope_hash,
        "material_input_count": len(expected),
        "binding_count": len(bindings),
        "evidence_count": len(evidence_index),
        "blockers": deduped,
    }


def validate_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    assessment = assess_candidate(candidate)
    if not assessment["ready_for_review"]:
        raise CaseServiceError(
            "candidate review gate blocked / Candidate 검토게이트 차단: "
            + "; ".join(assessment["blockers"])
        )
    return assessment


def _valid_reviewed_at(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    text = value.strip().replace("Z", "+00:00")
    try:
        datetime.fromisoformat(text)
    except ValueError:
        return False
    return True


def promotion_check(candidate: dict[str, Any]) -> dict[str, Any]:
    """Verify human review lock and declare PR readiness only / 인간검토 잠금·PR 준비 확인."""
    assessment = validate_candidate(candidate)
    review = candidate.get("review")
    if not isinstance(review, dict):
        raise CaseServiceError("review object required / review 객체가 필요합니다")
    if review.get("decision") != "APPROVE":
        raise CaseServiceError("explicit APPROVE review required / 명시적 APPROVE 검토가 필요합니다")
    reviewer = str(review.get("reviewer") or "").strip()
    rationale = str(review.get("rationale") or "").strip()
    if not reviewer:
        raise CaseServiceError("reviewer is required / 검토자 정보가 필요합니다")
    if not rationale:
        raise CaseServiceError("review rationale is required / 검토 근거가 필요합니다")
    if not _valid_reviewed_at(review.get("reviewed_at")):
        raise CaseServiceError("valid reviewed_at timestamp required / 유효한 검토시각이 필요합니다")
    locked_hash = str(review.get("scope_sha256") or "").strip().lower()
    expected_hash = str(assessment["review_scope_sha256"])
    if locked_hash != expected_hash:
        raise CaseServiceError(
            "review scope hash mismatch; candidate changed after approval / "
            "검토 범위 해시 불일치: 승인 후 Candidate가 변경되었습니다"
        )

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
        "grounding": "REVIEWED_EVIDENCE_AND_ASSUMPTIONS",
        "next_action_en": "Create a separately reviewed repository PR; CI and merge are still required before canonical status.",
        "next_action_ko": "별도 인간 검토 저장소 PR을 생성해야 하며, 정식 상태 전에는 CI와 병합이 추가로 필요합니다.",
    }


def load_candidate_file(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CaseServiceError(f"candidate file not found / Candidate 파일 없음: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CaseServiceError(f"invalid candidate JSON / Candidate JSON 오류: {exc}") from exc
    if not isinstance(payload, dict):
        raise CaseServiceError("candidate must be a JSON object / Candidate는 JSON 객체여야 합니다")
    return payload
