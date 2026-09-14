"""M29 backward-compatible canonical-admission dispatcher.

Historical M11 v0.1 semantics are delegated unchanged. For promotion-candidate-v0.2,
the exact reviewed source candidate remains embedded in SOURCE_PACKAGE.json while
canonical case artifacts use the deterministic normalized Draft view required by
the existing reviewed-Draft adapter contract.
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from valuation_hub import admission as legacy
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.promotion_m29 import CANDIDATE_SCHEMA_VERSION_V2
from valuation_hub.promotion_package import validate_promotion_package
from valuation_hub.reviewed_adapter import REVIEWED_ADMISSION_GATE, adapter_for_model, normalize_reviewed_runtime

ADMISSION_SCHEMA_VERSION = legacy.ADMISSION_SCHEMA_VERSION
ADMISSION_STATUS = legacy.ADMISSION_STATUS
ADMISSION_ARTIFACTS = legacy.ADMISSION_ARTIFACTS


def _candidate_schema(package: dict[str, Any]) -> str | None:
    try:
        candidate = package["artifacts"]["reviewed_candidate.json"]
    except (KeyError, TypeError):
        return None
    return candidate.get("schema_version") if isinstance(candidate, dict) else None


def _report_v2(
    case_id: str,
    name_en: str,
    name_ko: str,
    adapter: str,
    valuation_as_of: str,
    package_sha256: str,
) -> str:
    return f"""# Complete Governed Equity Canonical Admission / 완전 거버넌스 Equity 정식 수용

> **PROPOSED CANONICAL ARTIFACTS — EFFECTIVE ONLY AFTER REVIEWED PR MERGE**  
> **정식 제안 산출물 — 검토 PR 병합 이후에만 효력 발생**

- Case ID / 사례 ID: `{case_id}`
- Name / 이름: {name_en} / {name_ko}
- Adapter / 어댑터: `{adapter}`
- Valuation as of / 가치평가 기준일: `{valuation_as_of}`
- Source package SHA-256 / 원천 패키지 SHA-256: `{package_sha256}`
- Evidence gate / 근거 게이트: `{REVIEWED_ADMISSION_GATE}`

`SOURCE_PACKAGE.json` preserves the exact human-reviewed M29 v0.2 candidate, including the exact M28 `draft_after` and full bound-result lineage. `case_inputs.json` uses only the deterministic normalized view of that same Draft required by the existing canonical adapter. No value, scenario, authority class, evidence claim, or source lineage is reconstructed or re-governed.

`SOURCE_PACKAGE.json`은 정확한 M28 `draft_after`와 전체 bound-result lineage를 포함한 인간검토 M29 v0.2 candidate를 그대로 보존합니다. `case_inputs.json`은 기존 canonical adapter가 요구하는 동일 Draft의 결정론적 정규화 view만 사용합니다. 값·시나리오·권위 class·근거 claim·source lineage를 재구축하거나 재거버넌스하지 않습니다.

These files become canonical only after the exact admission artifacts pass a separate repository PR, full CI, human review, and merge.

이 파일은 정확한 수용 산출물이 별도 저장소 PR·전체 CI·인간 검토·병합을 통과한 이후에만 정식 상태가 됩니다.
"""


def _build_v2(
    package: dict[str, Any],
    root: Path | None = None,
    *,
    check_collision: bool = True,
) -> dict[str, Any]:
    repo = root.resolve() if root else find_repo_root()
    package_validation = validate_promotion_package(package, repo, check_collision=check_collision)
    identity = package["case_identity"]
    candidate = package["artifacts"]["reviewed_candidate.json"]
    if candidate.get("schema_version") != CANDIDATE_SCHEMA_VERSION_V2:
        raise CaseServiceError("M29 admission requires promotion-candidate-v0.2 / M29 수용은 promotion-candidate-v0.2 필요")
    reviewed_draft = candidate["draft"]
    try:
        normalized_draft, draft_result, runtime = normalize_reviewed_runtime(
            reviewed_draft, require_canonical_profile=True
        )
    except ValueError as exc:
        raise CaseServiceError(
            f"M29 reviewed Draft is not compatible with canonical adapter v0.1 / M29 검토 Draft adapter 호환 실패: {exc}"
        ) from exc

    staged = package["artifacts"]["staged_valuation_result.json"]
    if staged.get("valuation") != draft_result:
        raise CaseServiceError("M10 staged valuation drift / M10 staged 가치 결과 drift")

    model = normalized_draft["model"]
    adapter = adapter_for_model(model)
    if package_validation["required_canonical_adapter"] != adapter:
        raise CaseServiceError("M10 adapter requirement mismatch / M10 adapter 요구 불일치")
    valuation_as_of = legacy._market_as_of(candidate)
    case_id = identity["case_id"]
    target_path = f"analyses/equities/{case_id}"
    source_review = copy.deepcopy(package["source_review"])
    package_sha256 = package["package_sha256"]

    case_inputs = {
        "case_id": case_id,
        "model_version": adapter,
        "canonical": True,
        "valuation_as_of": valuation_as_of,
        "currency": normalized_draft["currency"],
        "source_package_sha256": package_sha256,
        "source_candidate_sha256": source_review["candidate_sha256"],
        "review_scope_sha256": source_review["review_scope_sha256"],
        "reviewed_draft": copy.deepcopy(normalized_draft),
    }
    evidence_reviewed = {
        "case_id": case_id,
        "bundle": "REVIEWED_DRAFT_ADMISSION_EVIDENCE",
        "as_of": valuation_as_of,
        "claims": copy.deepcopy(candidate["evidence"]),
        "input_governance": copy.deepcopy(candidate["input_governance"]),
        "source_package_sha256": package_sha256,
        "source_candidate_sha256": source_review["candidate_sha256"],
        "review_scope_sha256": source_review["review_scope_sha256"],
    }
    evidence_manifest = {
        "case_id": case_id,
        "status": "CANONICAL_REVIEWED_DRAFT_EVIDENCE_RECONCILED",
        "canonical": True,
        "valuation_as_of": valuation_as_of,
        "promotion_gate": REVIEWED_ADMISSION_GATE,
        "canonical_bundles": ["evidence_reviewed.json"],
        "pending_material_inputs": [],
        "source_package_sha256": package_sha256,
        "source_candidate_sha256": source_review["candidate_sha256"],
        "review_scope_sha256": source_review["review_scope_sha256"],
    }
    valuation_result = {
        "case_id": case_id,
        "model": model,
        "model_version": adapter,
        "status": "CANONICAL_REVIEWED_DRAFT_RESULT",
        "canonical": True,
        "valuation_as_of": valuation_as_of,
        "currency": normalized_draft["currency"],
        "market_price": normalized_draft["market_price"],
        "source_package_sha256": package_sha256,
        "source_candidate_sha256": source_review["candidate_sha256"],
        "review_scope_sha256": source_review["review_scope_sha256"],
        "runtime": copy.deepcopy(runtime),
        "classification": {
            "valuation_state": "REVIEWED_DRAFT_CANONICAL",
            "decision_note_en": "Canonical result admitted from a complete governed M29 handoff and human-reviewed hash lock.",
            "decision_note_ko": "완전 거버넌스 M29 인계와 인간검토 해시 잠금에서 수용된 정식 결과입니다.",
        },
    }
    registry_entry = {
        "case_id": case_id,
        "display_name_en": identity["display_name_en"],
        "display_name_ko": identity["display_name_ko"],
        "asset_class": identity["asset_class"],
        "model": model,
        "adapter": adapter,
        "path": target_path,
    }
    artifacts: dict[str, Any] = {
        "SOURCE_PACKAGE.json": copy.deepcopy(package),
        "case_inputs.json": case_inputs,
        "evidence_manifest.json": evidence_manifest,
        "evidence_reviewed.json": evidence_reviewed,
        "valuation_result.json": valuation_result,
        "REPORT.md": _report_v2(
            case_id,
            identity["display_name_en"],
            identity["display_name_ko"],
            adapter,
            valuation_as_of,
            package_sha256,
        ),
    }
    hashes = {name: legacy._sha(legacy._artifact_bytes(artifacts[name])) for name in ADMISSION_ARTIFACTS}
    bundle: dict[str, Any] = {
        "schema_version": ADMISSION_SCHEMA_VERSION,
        "status": ADMISSION_STATUS,
        "canonical": False,
        "case_id": case_id,
        "target_path": target_path,
        "registry_entry": registry_entry,
        "artifacts": artifacts,
        "artifact_sha256": hashes,
        "bundle_sha256": "",
    }
    bundle["bundle_sha256"] = legacy._sha(legacy._json_bytes(legacy._bundle_hash_payload(bundle)))
    return bundle


def build_admission_bundle(
    package: dict[str, Any],
    root: Path | None = None,
    *,
    check_collision: bool = True,
) -> dict[str, Any]:
    if _candidate_schema(package) == CANDIDATE_SCHEMA_VERSION_V2:
        return _build_v2(package, root, check_collision=check_collision)
    return legacy.build_admission_bundle(package, root, check_collision=check_collision)


def validate_admission_bundle(
    bundle: dict[str, Any],
    root: Path | None = None,
    *,
    check_collision: bool = True,
) -> dict[str, Any]:
    if not isinstance(bundle, dict):
        raise CaseServiceError("admission bundle must be a JSON object / 수용 bundle은 JSON 객체여야 합니다")
    artifacts = bundle.get("artifacts")
    source_package = artifacts.get("SOURCE_PACKAGE.json") if isinstance(artifacts, dict) else None
    if not isinstance(source_package, dict) or _candidate_schema(source_package) != CANDIDATE_SCHEMA_VERSION_V2:
        return legacy.validate_admission_bundle(bundle, root, check_collision=check_collision)

    repo = root.resolve() if root else find_repo_root()
    if bundle.get("schema_version") != ADMISSION_SCHEMA_VERSION or bundle.get("status") != ADMISSION_STATUS or bundle.get("canonical") is not False:
        raise CaseServiceError("M29 admission bundle schema/status invalid / M29 수용 bundle 스키마·상태 오류")
    hashes = bundle.get("artifact_sha256")
    if not isinstance(artifacts, dict) or not isinstance(hashes, dict) or set(artifacts) != set(ADMISSION_ARTIFACTS) or set(hashes) != set(ADMISSION_ARTIFACTS):
        raise CaseServiceError("M29 admission artifact set/hash manifest mismatch / M29 수용 산출물·해시 집합 불일치")
    for name in ADMISSION_ARTIFACTS:
        if hashes.get(name) != legacy._sha(legacy._artifact_bytes(artifacts[name])):
            raise CaseServiceError(f"M29 admission artifact hash mismatch / M29 수용 산출물 해시 불일치: {name}")
    if bundle.get("bundle_sha256") != legacy._sha(legacy._json_bytes(legacy._bundle_hash_payload(bundle))):
        raise CaseServiceError("M29 admission bundle SHA-256 mismatch / M29 수용 bundle SHA 불일치")

    validate_promotion_package(source_package, repo, check_collision=check_collision)
    case_id = source_package["case_identity"]["case_id"]
    if bundle.get("case_id") != case_id or bundle.get("target_path") != f"analyses/equities/{case_id}":
        raise CaseServiceError("M29 admission identity/path mismatch / M29 수용 식별·경로 불일치")
    expected = _build_v2(source_package, repo, check_collision=check_collision)
    if bundle != expected:
        raise CaseServiceError("M29 admission bundle deterministic reconstruction mismatch / M29 수용 bundle 결정론적 재구축 불일치")

    case_inputs = artifacts["case_inputs.json"]
    result = artifacts["valuation_result.json"]
    manifest = artifacts["evidence_manifest.json"]
    evidence_reviewed = artifacts["evidence_reviewed.json"]
    registry = bundle["registry_entry"]
    source_model = source_package["adapter_requirement"]["source_model"]
    adapter = adapter_for_model(source_model)
    if registry.get("adapter") != adapter or registry.get("model") != source_model:
        raise CaseServiceError("M29 admission registry adapter/model mismatch / M29 수용 registry adapter·model 불일치")
    if case_inputs.get("model_version") != adapter or result.get("model_version") != adapter:
        raise CaseServiceError("M29 admission model_version mismatch / M29 수용 model_version 불일치")
    if manifest.get("promotion_gate") != REVIEWED_ADMISSION_GATE:
        raise CaseServiceError("M29 admission evidence gate mismatch / M29 수용 근거게이트 불일치")
    if case_inputs.get("source_package_sha256") != source_package["package_sha256"]:
        raise CaseServiceError("M29 case input package provenance mismatch / M29 사례입력 패키지 출처 불일치")
    candidate = source_package["artifacts"]["reviewed_candidate.json"]
    normalized_draft, _, expected_runtime = normalize_reviewed_runtime(candidate["draft"], require_canonical_profile=True)
    if case_inputs.get("reviewed_draft") != normalized_draft:
        raise CaseServiceError("M29 canonical reviewed Draft normalization mismatch / M29 정식 reviewed Draft 정규화 불일치")
    if result.get("runtime") != expected_runtime:
        raise CaseServiceError("M29 admission runtime mismatch / M29 수용 runtime 불일치")
    if evidence_reviewed.get("claims") != candidate.get("evidence") or evidence_reviewed.get("input_governance") != candidate.get("input_governance"):
        raise CaseServiceError("M29 admission evidence/governance drift / M29 수용 근거·거버넌스 drift")
    return {
        "status": ADMISSION_STATUS,
        "canonical": False,
        "valid": True,
        "case_id": case_id,
        "target_path": bundle["target_path"],
        "adapter": adapter,
        "artifact_count": len(ADMISSION_ARTIFACTS),
        "bundle_sha256": bundle["bundle_sha256"],
        "next_action_en": "Apply only through the guarded admission/* repository workflow and merge after full CI and human review.",
        "next_action_ko": "guarded admission/* 저장소 흐름으로만 적용하고 전체 CI·인간검토 후 병합하십시오.",
    }
