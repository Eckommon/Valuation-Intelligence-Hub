"""Deterministic reviewed promotion-package staging / 검토 완료 승격 패키지 스테이징.

A promotion package is tamper-evident review material. It preserves an approved
M9 candidate without coercing it into the legacy reference-case input shape.
It never writes registry/canonical analysis state and is intentionally not a
canonical executable case.

승격 패키지는 변조 탐지 가능한 검토 자료다. 승인된 M9 Candidate를 기존 reference
입력 구조로 억지 변환하지 않고 보존하며 정식 레지스트리·분석상태를 기록하지 않는다.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from valuation_hub.case_service import CaseServiceError, find_repo_root, load_registry
from valuation_hub.draft_service import run_draft
from valuation_hub.promotion import promotion_check

PACKAGE_SCHEMA_VERSION = "promotion-package-v0.1"
PACKAGE_STATUS = "PROMOTION_PACKAGE_STAGED"
COMPATIBILITY_STATUS = "NOT_EXECUTABLE_UNTIL_CANONICAL_ADAPTER"
CASE_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9_]{2,79}$")
ARTIFACT_NAMES = (
    "reviewed_candidate.json",
    "reviewed_case_payload.json",
    "evidence_bundle.json",
    "staged_valuation_result.json",
    "REGISTRY_PROPOSAL.json",
    "REPORT.md",
)


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _artifact_bytes(value: Any) -> bytes:
    if isinstance(value, str):
        return value.encode("utf-8")
    return _canonical_json_bytes(value)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(_canonical_json_bytes(value))


def _validate_identity(
    case_id: str,
    display_name_en: str,
    display_name_ko: str,
    asset_class: str,
) -> dict[str, str]:
    if not isinstance(case_id, str) or CASE_ID_RE.fullmatch(case_id) is None:
        raise CaseServiceError(
            "case_id must match ^[A-Z0-9][A-Z0-9_]{2,79}$ / case_id 형식 오류"
        )
    values = {
        "display_name_en": display_name_en,
        "display_name_ko": display_name_ko,
        "asset_class": asset_class,
    }
    limits = {"display_name_en": 160, "display_name_ko": 160, "asset_class": 80}
    for name, value in values.items():
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > limits[name]:
            raise CaseServiceError(f"{name} is required or too long / {name} 값 오류")
    return {
        "case_id": case_id,
        "display_name_en": display_name_en.strip(),
        "display_name_ko": display_name_ko.strip(),
        "asset_class": asset_class.strip(),
    }


def _ensure_no_canonical_collision(case_id: str, root: Path) -> None:
    registry = load_registry(root)
    if any(item.get("case_id") == case_id for item in registry["cases"]):
        raise CaseServiceError(
            f"case_id already exists in canonical registry / 정식 레지스트리 ID 충돌: {case_id}"
        )


def _adapter_requirement(model: str) -> dict[str, Any]:
    if model == "equity_fcff":
        adapter = "reviewed-draft-equity-fcff-v0.1"
        reason_en = (
            "M8 Draft FCFF preserves absolute D&A, CAPEX and ΔNWC while legacy reference equity cases "
            "use opening core NWC and revenue-linked ratios. Lossy coercion is prohibited."
        )
        reason_ko = (
            "M8 Draft FCFF는 D&A·CAPEX·ΔNWC 절대값을 보존하지만 기존 reference equity 사례는 "
            "opening core NWC와 매출연동 비율을 사용하므로 손실 변환을 금지한다."
        )
    elif model == "venture_probability":
        adapter = "reviewed-draft-venture-probability-v0.1"
        reason_en = (
            "The reviewed Draft must be accepted through an explicit versioned canonical adapter rather than "
            "being mislabeled as a legacy reference-venture case."
        )
        reason_ko = (
            "검토 Draft는 기존 reference-venture 사례로 오표시하지 않고 명시적 버전 canonical adapter를 "
            "통해 수용해야 한다."
        )
    else:
        raise CaseServiceError(f"unsupported candidate model / 미지원 Candidate 모델: {model}")
    return {
        "source_model": model,
        "required_canonical_adapter": adapter,
        "compatibility_status": COMPATIBILITY_STATUS,
        "reason_en": reason_en,
        "reason_ko": reason_ko,
    }


def _report(
    identity: dict[str, str],
    readiness: dict[str, Any],
    adapter: dict[str, Any],
    candidate_sha256: str,
) -> str:
    return f"""# Promotion Package Review / 승격 패키지 검토

> **PROMOTION_PACKAGE_STAGED · NOT_CANONICAL**  
> **승격 패키지 스테이징 · 정식 아님**

## Identity / 식별

- Case ID / 사례 ID: `{identity['case_id']}`
- Name / 이름: {identity['display_name_en']} / {identity['display_name_ko']}
- Asset class / 자산분류: `{identity['asset_class']}`
- Source model / 원천 모델: `{readiness['model']}`

## Human review provenance / 인간 검토 출처

- Reviewer / 검토자: `{readiness['reviewer']}`
- Reviewed at / 검토시각: `{readiness['reviewed_at']}`
- Review scope SHA-256 / 검토범위 SHA-256: `{readiness['review_scope_sha256']}`
- Candidate SHA-256 / Candidate SHA-256: `{candidate_sha256}`

## Canonical compatibility / 정식 호환성

- Status / 상태: `{adapter['compatibility_status']}`
- Required adapter / 필요 adapter: `{adapter['required_canonical_adapter']}`
- EN: {adapter['reason_en']}
- KO: {adapter['reason_ko']}

This package is deterministic review material. It is **not** a registry entry, canonical analysis directory, or authorization to merge. A separately reviewed canonical-adapter PR and full CI are still required.

이 패키지는 결정론적 검토 자료이며 **정식 레지스트리 항목·정식 분석 디렉터리·병합 승인**이 아니다. 별도 canonical-adapter PR, 인간 검토, 전체 CI가 추가로 필요하다.
"""


def _package_hash_payload(package: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(package)
    payload.pop("package_sha256", None)
    return payload


def build_promotion_package(
    candidate: dict[str, Any],
    *,
    case_id: str,
    display_name_en: str,
    display_name_ko: str,
    asset_class: str,
    root: Path | None = None,
) -> dict[str, Any]:
    """Build deterministic staged package from hash-locked approved candidate."""
    repo = root.resolve() if root else find_repo_root()
    identity = _validate_identity(case_id, display_name_en, display_name_ko, asset_class)
    _ensure_no_canonical_collision(case_id, repo)
    readiness = promotion_check(candidate)
    if readiness.get("canonical") is not False or not readiness.get("promotion_ready"):
        raise CaseServiceError("candidate is not PR-ready / Candidate가 PR 준비상태가 아닙니다")

    approved_candidate = copy.deepcopy(candidate)
    candidate_sha256 = _sha256_json(approved_candidate)
    valuation = run_draft(approved_candidate["draft"])
    adapter = _adapter_requirement(str(readiness["model"]))
    proposed_target = f"analyses/equities/{case_id}"
    source_review = {
        "candidate_sha256": candidate_sha256,
        "review_scope_sha256": readiness["review_scope_sha256"],
        "reviewer": readiness["reviewer"],
        "reviewed_at": readiness["reviewed_at"],
    }

    reviewed_case = {
        "schema_version": "reviewed-draft-case-v0.1",
        "status": "STAGED_NOT_CANONICAL",
        "canonical": False,
        "case_identity": identity,
        "source_review": source_review,
        "draft": copy.deepcopy(approved_candidate["draft"]),
        "adapter_requirement": adapter,
    }
    evidence_bundle = {
        "schema_version": "reviewed-evidence-bundle-v0.1",
        "status": "STAGED_NOT_CANONICAL",
        "canonical": False,
        "case_id": case_id,
        "review_scope_sha256": readiness["review_scope_sha256"],
        "input_governance": copy.deepcopy(approved_candidate["input_governance"]),
        "evidence": copy.deepcopy(approved_candidate["evidence"]),
    }
    staged_result = {
        "schema_version": "staged-valuation-result-v0.1",
        "status": "STAGED_NOT_CANONICAL",
        "canonical": False,
        "case_id": case_id,
        "candidate_sha256": candidate_sha256,
        "valuation": valuation,
    }
    registry_proposal = {
        "status": "PROPOSAL_ONLY_NOT_REGISTRY_ENTRY",
        "canonical": False,
        "registration_blocked": True,
        "case_id": case_id,
        "display_name_en": identity["display_name_en"],
        "display_name_ko": identity["display_name_ko"],
        "asset_class": identity["asset_class"],
        "source_model": readiness["model"],
        "proposed_target_path": proposed_target,
        "required_canonical_adapter": adapter["required_canonical_adapter"],
        "compatibility_status": COMPATIBILITY_STATUS,
    }
    artifacts: dict[str, Any] = {
        "reviewed_candidate.json": approved_candidate,
        "reviewed_case_payload.json": reviewed_case,
        "evidence_bundle.json": evidence_bundle,
        "staged_valuation_result.json": staged_result,
        "REGISTRY_PROPOSAL.json": registry_proposal,
        "REPORT.md": _report(identity, readiness, adapter, candidate_sha256),
    }
    hashes = {name: _sha256_bytes(_artifact_bytes(artifacts[name])) for name in ARTIFACT_NAMES}
    package: dict[str, Any] = {
        "schema_version": PACKAGE_SCHEMA_VERSION,
        "status": PACKAGE_STATUS,
        "canonical": False,
        "case_identity": identity,
        "source_review": source_review,
        "adapter_requirement": adapter,
        "artifacts": artifacts,
        "artifact_sha256": hashes,
        "package_sha256": "",
    }
    package["package_sha256"] = _sha256_json(_package_hash_payload(package))
    return package


def validate_promotion_package(
    package: dict[str, Any],
    root: Path | None = None,
    *,
    check_collision: bool = True,
) -> dict[str, Any]:
    """Validate package integrity, review provenance, and valuation reproduction."""
    repo = root.resolve() if root else find_repo_root()
    if not isinstance(package, dict):
        raise CaseServiceError("package must be a JSON object / 패키지는 JSON 객체여야 합니다")
    if package.get("schema_version") != PACKAGE_SCHEMA_VERSION:
        raise CaseServiceError("unsupported promotion package schema / 미지원 승격 패키지 스키마")
    if package.get("status") != PACKAGE_STATUS or package.get("canonical") is not False:
        raise CaseServiceError("promotion package state invalid / 승격 패키지 상태 오류")

    identity = package.get("case_identity")
    if not isinstance(identity, dict):
        raise CaseServiceError("case_identity required / case_identity 필요")
    normalized_identity = _validate_identity(
        identity.get("case_id"),
        identity.get("display_name_en"),
        identity.get("display_name_ko"),
        identity.get("asset_class"),
    )
    if check_collision:
        _ensure_no_canonical_collision(normalized_identity["case_id"], repo)

    artifacts = package.get("artifacts")
    hashes = package.get("artifact_sha256")
    if not isinstance(artifacts, dict) or not isinstance(hashes, dict):
        raise CaseServiceError("package artifacts/hash manifest missing / 패키지 산출물·해시 누락")
    if set(artifacts) != set(ARTIFACT_NAMES) or set(hashes) != set(ARTIFACT_NAMES):
        raise CaseServiceError("artifact set mismatch / 패키지 산출물 집합 불일치")
    for name in ARTIFACT_NAMES:
        actual = _sha256_bytes(_artifact_bytes(artifacts[name]))
        if hashes.get(name) != actual:
            raise CaseServiceError(f"artifact hash mismatch / 산출물 해시 불일치: {name}")

    expected_package_hash = _sha256_json(_package_hash_payload(package))
    if package.get("package_sha256") != expected_package_hash:
        raise CaseServiceError("package SHA-256 mismatch / 패키지 SHA-256 불일치")

    candidate = artifacts["reviewed_candidate.json"]
    if not isinstance(candidate, dict):
        raise CaseServiceError("reviewed candidate artifact invalid / 검토 Candidate 산출물 오류")
    readiness = promotion_check(candidate)
    source_review = package.get("source_review")
    if not isinstance(source_review, dict):
        raise CaseServiceError("source_review missing / source_review 누락")
    candidate_hash = _sha256_json(candidate)
    if source_review.get("candidate_sha256") != candidate_hash:
        raise CaseServiceError("candidate SHA-256 mismatch / Candidate SHA-256 불일치")
    if source_review.get("review_scope_sha256") != readiness["review_scope_sha256"]:
        raise CaseServiceError("review scope provenance mismatch / 검토범위 출처 해시 불일치")
    if source_review.get("reviewer") != readiness["reviewer"] or source_review.get("reviewed_at") != readiness["reviewed_at"]:
        raise CaseServiceError("review provenance mismatch / 검토 출처 불일치")

    adapter = package.get("adapter_requirement")
    expected_adapter = _adapter_requirement(readiness["model"])
    if adapter != expected_adapter:
        raise CaseServiceError("canonical adapter requirement mismatch / canonical adapter 요구사항 불일치")

    reviewed_case = artifacts["reviewed_case_payload.json"]
    if not isinstance(reviewed_case, dict) or reviewed_case.get("draft") != candidate.get("draft"):
        raise CaseServiceError("reviewed case payload drift / reviewed case payload drift")
    if reviewed_case.get("case_identity") != normalized_identity:
        raise CaseServiceError("reviewed case identity mismatch / reviewed case 식별 불일치")
    if reviewed_case.get("adapter_requirement") != expected_adapter:
        raise CaseServiceError("reviewed case adapter mismatch / reviewed case adapter 불일치")

    evidence_bundle = artifacts["evidence_bundle.json"]
    if not isinstance(evidence_bundle, dict):
        raise CaseServiceError("evidence bundle invalid / 근거 bundle 오류")
    if evidence_bundle.get("input_governance") != candidate.get("input_governance") or evidence_bundle.get("evidence") != candidate.get("evidence"):
        raise CaseServiceError("evidence bundle drift / 근거 bundle drift")

    staged_result = artifacts["staged_valuation_result.json"]
    expected_valuation = run_draft(candidate["draft"])
    if not isinstance(staged_result, dict) or staged_result.get("valuation") != expected_valuation:
        raise CaseServiceError("staged valuation does not reproduce shared kernel / staged 가치가 공통커널을 재현하지 못함")
    if staged_result.get("candidate_sha256") != candidate_hash:
        raise CaseServiceError("staged result candidate hash mismatch / staged 결과 Candidate 해시 불일치")

    proposal = artifacts["REGISTRY_PROPOSAL.json"]
    if not isinstance(proposal, dict) or proposal.get("registration_blocked") is not True:
        raise CaseServiceError("registry proposal must remain blocked / 레지스트리 제안은 차단상태여야 함")
    if proposal.get("compatibility_status") != COMPATIBILITY_STATUS:
        raise CaseServiceError("registry proposal compatibility state invalid / 레지스트리 제안 호환상태 오류")
    if proposal.get("case_id") != normalized_identity["case_id"]:
        raise CaseServiceError("registry proposal case_id mismatch / 레지스트리 제안 case_id 불일치")

    return {
        "status": PACKAGE_STATUS,
        "canonical": False,
        "valid": True,
        "case_id": normalized_identity["case_id"],
        "source_model": readiness["model"],
        "required_canonical_adapter": expected_adapter["required_canonical_adapter"],
        "compatibility_status": COMPATIBILITY_STATUS,
        "artifact_count": len(ARTIFACT_NAMES),
        "package_sha256": package["package_sha256"],
        "next_action_en": "Review the staged package and implement the declared canonical adapter in a separate governed PR before registry admission.",
        "next_action_ko": "스테이징 패키지를 검토하고 레지스트리 수용 전 별도 거버넌스 PR에서 명시된 canonical adapter를 구현해야 합니다.",
    }


def _safe_output_directory(output_dir: Path, root: Path) -> Path:
    resolved = output_dir.expanduser().resolve()
    repo = root.resolve()
    try:
        relative = resolved.relative_to(repo)
    except ValueError:
        return resolved
    allowed = repo / "workspace" / "promotion_packages"
    try:
        resolved.relative_to(allowed)
    except ValueError as exc:
        raise CaseServiceError(
            "inside-repository package output is allowed only under workspace/promotion_packages / "
            "저장소 내부 출력은 workspace/promotion_packages 아래만 허용됩니다"
        ) from exc
    if ".." in relative.parts:
        raise CaseServiceError("unsafe output path / 위험한 출력 경로")
    return resolved


def materialize_promotion_package(
    package: dict[str, Any],
    output_dir: Path,
    root: Path | None = None,
) -> dict[str, Any]:
    """Write validated package only to an explicit non-canonical output directory."""
    repo = root.resolve() if root else find_repo_root()
    validation = validate_promotion_package(package, repo)
    target = _safe_output_directory(output_dir, repo)
    if target.exists() and any(target.iterdir()):
        raise CaseServiceError(f"output directory must be empty / 출력 디렉터리는 비어 있어야 합니다: {target}")
    target.mkdir(parents=True, exist_ok=True)
    for name in ARTIFACT_NAMES:
        path = target / name
        value = package["artifacts"][name]
        if isinstance(value, str):
            path.write_text(value, encoding="utf-8", newline="\n")
        else:
            path.write_bytes(_canonical_json_bytes(value) + b"\n")
    (target / "PACKAGE.json").write_bytes(_canonical_json_bytes(package) + b"\n")
    return {
        **validation,
        "materialized": True,
        "output_dir": str(target),
        "files": ["PACKAGE.json", *ARTIFACT_NAMES],
    }


def load_package_file(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CaseServiceError(f"package file not found / 패키지 파일 없음: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CaseServiceError(f"invalid package JSON / 패키지 JSON 오류: {exc}") from exc
    if not isinstance(payload, dict):
        raise CaseServiceError("package must be a JSON object / 패키지는 JSON 객체여야 합니다")
    return payload


def validate_materialized_package(directory: Path, root: Path | None = None) -> dict[str, Any]:
    """Verify PACKAGE.json and each materialized artifact byte-for-byte."""
    repo = root.resolve() if root else find_repo_root()
    target = directory.expanduser().resolve()
    package = load_package_file(target / "PACKAGE.json")
    validation = validate_promotion_package(package, repo)
    for name in ARTIFACT_NAMES:
        path = target / name
        try:
            raw = path.read_bytes()
        except FileNotFoundError as exc:
            raise CaseServiceError(f"materialized artifact missing / materialized 산출물 누락: {name}") from exc
        expected_value = package["artifacts"][name]
        expected = (
            expected_value.encode("utf-8")
            if isinstance(expected_value, str)
            else _canonical_json_bytes(expected_value) + b"\n"
        )
        if raw != expected:
            raise CaseServiceError(f"materialized artifact bytes mismatch / materialized bytes 불일치: {name}")
    return {**validation, "materialized": True, "output_dir": str(target)}
