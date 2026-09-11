"""Reviewed-Draft canonical admission planning / 검토 Draft 정식 수용 계획.

M11 turns a valid M10 staged package into deterministic *proposed* canonical
artifacts. The builder is read-only with respect to the repository; actual
canonicalization still requires a separately reviewed PR, CI, and merge.
"""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.promotion_package import validate_promotion_package
from valuation_hub.reviewed_adapter import (
    REVIEWED_ADMISSION_GATE,
    adapter_for_model,
    normalize_reviewed_runtime,
)

ADMISSION_SCHEMA_VERSION = "canonical-admission-bundle-v0.1"
ADMISSION_STATUS = "CANONICAL_ADMISSION_PROPOSED"
ADMISSION_ARTIFACTS = (
    "SOURCE_PACKAGE.json",
    "case_inputs.json",
    "evidence_manifest.json",
    "evidence_reviewed.json",
    "valuation_result.json",
    "REPORT.md",
)


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _artifact_bytes(value: Any) -> bytes:
    return value.encode("utf-8") if isinstance(value, str) else _json_bytes(value)


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _bundle_hash_payload(bundle: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(bundle)
    payload.pop("bundle_sha256", None)
    return payload


def _market_as_of(candidate: dict[str, Any]) -> str:
    bindings = candidate.get("input_governance")
    evidence = candidate.get("evidence")
    if not isinstance(bindings, list) or not isinstance(evidence, list):
        raise CaseServiceError("candidate governance/evidence missing / Candidate 거버넌스·근거 누락")
    market_bindings = [
        item
        for item in bindings
        if isinstance(item, dict) and item.get("path") == "market_price"
    ]
    if len(market_bindings) != 1:
        raise CaseServiceError(
            "exactly one market_price binding required / market_price binding은 정확히 하나여야 합니다"
        )
    claim_ids = market_bindings[0].get("claim_ids")
    if not isinstance(claim_ids, list) or not claim_ids:
        raise CaseServiceError("market_price evidence link required / market_price 연결 근거 필요")
    indexed = {
        item.get("claim_id"): item
        for item in evidence
        if isinstance(item, dict) and item.get("claim_id")
    }
    dates: set[str] = set()
    for claim_id in claim_ids:
        claim = indexed.get(claim_id)
        if claim is None:
            raise CaseServiceError(
                f"market_price evidence missing / 시장가격 근거 누락: {claim_id}"
            )
        raw = claim.get("as_of")
        if not isinstance(raw, str):
            raise CaseServiceError(
                f"market_price evidence as_of required / 시장가격 근거 기준일 필요: {claim_id}"
            )
        try:
            parsed = date.fromisoformat(raw)
        except ValueError as exc:
            raise CaseServiceError(
                f"market_price evidence as_of must be YYYY-MM-DD / 기준일 형식 오류: {raw}"
            ) from exc
        if parsed.isoformat() != raw:
            raise CaseServiceError(
                f"market_price evidence as_of must be canonical YYYY-MM-DD / 기준일 정규형식 오류: {raw}"
            )
        dates.add(raw)
    if len(dates) != 1:
        raise CaseServiceError("market_price evidence dates conflict / 시장가격 근거 기준일 충돌")
    return next(iter(dates))


def _report(
    case_id: str,
    name_en: str,
    name_ko: str,
    adapter: str,
    valuation_as_of: str,
    package_sha256: str,
) -> str:
    return f"""# Reviewed-Draft Canonical Admission / 검토 Draft 정식 수용

> **PROPOSED CANONICAL ARTIFACTS — EFFECTIVE ONLY AFTER REVIEWED PR MERGE**  
> **정식 제안 산출물 — 검토 PR 병합 이후에만 효력 발생**

- Case ID / 사례 ID: `{case_id}`
- Name / 이름: {name_en} / {name_ko}
- Adapter / 어댑터: `{adapter}`
- Valuation as of / 가치평가 기준일: `{valuation_as_of}`
- Source package SHA-256 / 원천 패키지 SHA-256: `{package_sha256}`
- Evidence gate / 근거 게이트: `{REVIEWED_ADMISSION_GATE}`

The embedded `reviewed_draft` is preserved exactly from the human-reviewed M10 source package. No legacy ratio reconstruction is performed. The adapter delegates valuation to the shared Draft/FCFF/Venture kernels and normalizes only the external service shape.

내장 `reviewed_draft`는 인간 검토된 M10 원천 패키지에서 정확히 보존됩니다. 기존 비율구조로 재구축하지 않습니다. Adapter는 공통 Draft/FCFF/Venture 커널에 가치계산을 위임하고 외부 서비스 형태만 정규화합니다.

These files become canonical only if a separate repository PR containing the exact reviewed artifacts passes full CI, human review, and merge.

이 파일은 정확한 검토 산출물을 포함한 별도 저장소 PR이 전체 CI·인간 검토·병합을 통과할 때만 정식 상태가 됩니다.
"""


def build_admission_bundle(
    package: dict[str, Any],
    root: Path | None = None,
    *,
    check_collision: bool = True,
) -> dict[str, Any]:
    """Build deterministic proposed canonical artifacts from a valid M10 package."""
    repo = root.resolve() if root else find_repo_root()
    package_validation = validate_promotion_package(
        package, repo, check_collision=check_collision
    )
    identity = package["case_identity"]
    candidate = package["artifacts"]["reviewed_candidate.json"]
    reviewed_draft = candidate["draft"]
    try:
        normalized_draft, draft_result, runtime = normalize_reviewed_runtime(
            reviewed_draft, require_canonical_profile=True
        )
    except ValueError as exc:
        raise CaseServiceError(
            f"reviewed Draft is not compatible with canonical adapter v0.1 / 정식 adapter v0.1 호환 실패: {exc}"
        ) from exc
    if normalized_draft != reviewed_draft:
        raise CaseServiceError(
            "reviewed Draft is not normalized/stable / 검토 Draft 정규화 drift"
        )

    staged = package["artifacts"]["staged_valuation_result.json"]
    if staged.get("valuation") != draft_result:
        raise CaseServiceError("M10 staged valuation drift / M10 staged 가치 결과 drift")

    model = reviewed_draft["model"]
    adapter = adapter_for_model(model)
    if package_validation["required_canonical_adapter"] != adapter:
        raise CaseServiceError("M10 adapter requirement mismatch / M10 adapter 요구 불일치")
    valuation_as_of = _market_as_of(candidate)
    case_id = identity["case_id"]
    target_path = f"analyses/equities/{case_id}"
    source_review = copy.deepcopy(package["source_review"])
    package_sha256 = package["package_sha256"]

    case_inputs = {
        "case_id": case_id,
        "model_version": adapter,
        "canonical": True,
        "valuation_as_of": valuation_as_of,
        "currency": reviewed_draft["currency"],
        "source_package_sha256": package_sha256,
        "source_candidate_sha256": source_review["candidate_sha256"],
        "review_scope_sha256": source_review["review_scope_sha256"],
        "reviewed_draft": copy.deepcopy(reviewed_draft),
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
        "currency": reviewed_draft["currency"],
        "market_price": reviewed_draft["market_price"],
        "source_package_sha256": package_sha256,
        "source_candidate_sha256": source_review["candidate_sha256"],
        "review_scope_sha256": source_review["review_scope_sha256"],
        "runtime": copy.deepcopy(runtime),
        "classification": {
            "valuation_state": "REVIEWED_DRAFT_CANONICAL",
            "decision_note_en": "Canonical result admitted from a human-reviewed, hash-locked Draft package.",
            "decision_note_ko": "인간 검토·해시 잠금 Draft 패키지에서 수용된 정식 결과입니다.",
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
        "REPORT.md": _report(
            case_id,
            identity["display_name_en"],
            identity["display_name_ko"],
            adapter,
            valuation_as_of,
            package_sha256,
        ),
    }
    hashes = {
        name: _sha(_artifact_bytes(artifacts[name])) for name in ADMISSION_ARTIFACTS
    }
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
    bundle["bundle_sha256"] = _sha(_json_bytes(_bundle_hash_payload(bundle)))
    return bundle


def validate_admission_bundle(
    bundle: dict[str, Any],
    root: Path | None = None,
    *,
    check_collision: bool = True,
) -> dict[str, Any]:
    repo = root.resolve() if root else find_repo_root()
    if not isinstance(bundle, dict):
        raise CaseServiceError(
            "admission bundle must be a JSON object / 수용 bundle은 JSON 객체여야 합니다"
        )
    if (
        bundle.get("schema_version") != ADMISSION_SCHEMA_VERSION
        or bundle.get("status") != ADMISSION_STATUS
    ):
        raise CaseServiceError(
            "admission bundle schema/status invalid / 수용 bundle 스키마·상태 오류"
        )
    if bundle.get("canonical") is not False:
        raise CaseServiceError(
            "admission bundle itself cannot be canonical / 수용 bundle 자체는 정식일 수 없습니다"
        )
    artifacts = bundle.get("artifacts")
    hashes = bundle.get("artifact_sha256")
    if not isinstance(artifacts, dict) or not isinstance(hashes, dict):
        raise CaseServiceError(
            "admission artifacts/hash manifest missing / 수용 산출물·해시 누락"
        )
    if set(artifacts) != set(ADMISSION_ARTIFACTS) or set(hashes) != set(
        ADMISSION_ARTIFACTS
    ):
        raise CaseServiceError(
            "admission artifact set mismatch / 수용 산출물 집합 불일치"
        )
    for name in ADMISSION_ARTIFACTS:
        if hashes.get(name) != _sha(_artifact_bytes(artifacts[name])):
            raise CaseServiceError(
                f"admission artifact hash mismatch / 수용 산출물 해시 불일치: {name}"
            )
    if bundle.get("bundle_sha256") != _sha(_json_bytes(_bundle_hash_payload(bundle))):
        raise CaseServiceError(
            "admission bundle SHA-256 mismatch / 수용 bundle SHA-256 불일치"
        )

    source_package = artifacts["SOURCE_PACKAGE.json"]
    validate_promotion_package(source_package, repo, check_collision=check_collision)
    case_id = source_package["case_identity"]["case_id"]
    if (
        bundle.get("case_id") != case_id
        or bundle.get("target_path") != f"analyses/equities/{case_id}"
    ):
        raise CaseServiceError("admission identity/path mismatch / 수용 식별·경로 불일치")

    expected = build_admission_bundle(
        source_package, repo, check_collision=check_collision
    )
    if bundle != expected:
        raise CaseServiceError(
            "admission bundle is not deterministic reconstruction / 수용 bundle 결정론적 재구축 불일치"
        )

    case_inputs = artifacts["case_inputs.json"]
    result = artifacts["valuation_result.json"]
    manifest = artifacts["evidence_manifest.json"]
    evidence_reviewed = artifacts["evidence_reviewed.json"]
    registry = bundle["registry_entry"]
    source_model = source_package["adapter_requirement"]["source_model"]
    adapter = adapter_for_model(source_model)
    if registry.get("adapter") != adapter or registry.get("model") != source_model:
        raise CaseServiceError(
            "admission registry adapter/model mismatch / 수용 registry adapter·model 불일치"
        )
    if case_inputs.get("model_version") != adapter or result.get("model_version") != adapter:
        raise CaseServiceError(
            "admission model_version mismatch / 수용 model_version 불일치"
        )
    if manifest.get("promotion_gate") != REVIEWED_ADMISSION_GATE:
        raise CaseServiceError(
            "admission evidence gate mismatch / 수용 근거게이트 불일치"
        )
    if case_inputs.get("source_package_sha256") != source_package["package_sha256"]:
        raise CaseServiceError(
            "case input package provenance mismatch / 사례입력 패키지 출처 불일치"
        )

    candidate = source_package["artifacts"]["reviewed_candidate.json"]
    if evidence_reviewed.get("claims") != candidate.get("evidence"):
        raise CaseServiceError("admission evidence drift / 수용 근거 drift")
    if evidence_reviewed.get("input_governance") != candidate.get("input_governance"):
        raise CaseServiceError("admission governance drift / 수용 거버넌스 drift")

    try:
        normalized, _, runtime = normalize_reviewed_runtime(
            case_inputs["reviewed_draft"], require_canonical_profile=True
        )
    except ValueError as exc:
        raise CaseServiceError(
            f"admission canonical profile mismatch / 수용 정식 프로파일 불일치: {exc}"
        ) from exc
    if normalized != case_inputs["reviewed_draft"] or result.get("runtime") != runtime:
        raise CaseServiceError(
            "admission runtime/economics drift / 수용 runtime·경제값 drift"
        )
    return {
        "status": ADMISSION_STATUS,
        "canonical": False,
        "valid": True,
        "case_id": case_id,
        "adapter": adapter,
        "valuation_as_of": case_inputs["valuation_as_of"],
        "bundle_sha256": bundle["bundle_sha256"],
        "source_package_sha256": source_package["package_sha256"],
        "next_action_en": "Review these exact proposed canonical artifacts in a separate repository PR; only merge can make them canonical.",
        "next_action_ko": "이 정확한 정식 제안 산출물을 별도 저장소 PR에서 검토해야 하며 병합 이후에만 정식 상태가 됩니다.",
    }
