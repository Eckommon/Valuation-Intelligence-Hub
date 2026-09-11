"""Guarded repository application for M11 canonical admission bundles.

M12 closes the manual-copy gap between a validated admission bundle and a PR-ready
working tree. Planning is deterministic. Application is restricted to an explicit
`admission/*` Git branch/worktree, never overwrites an existing case, uses registry
optimistic concurrency, stages exact artifact bytes, and rolls back on failure.

M12는 검증된 M11 수용 bundle과 PR 준비 working tree 사이의 수작업 복사 간극을
닫는다. 계획은 결정론적이며 적용은 명시적 `admission/*` Git branch/worktree에만
허용한다. 기존 사례를 덮어쓰지 않고 registry 낙관적 동시성·정확한 bytes·실패 롤백을
강제한다.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any

from valuation_hub.admission import ADMISSION_ARTIFACTS, validate_admission_bundle
from valuation_hub.case_service import CaseServiceError, run_case, validate_case
from valuation_hub.interactive import evidence_view, preview_case

PLAN_SCHEMA_VERSION = "repository-change-plan-v0.1"
PLAN_STATUS = "REPOSITORY_CHANGE_PLANNED"
APPLIED_STATUS = "GUARDED_BRANCH_APPLIED"
REGISTRY_RELATIVE_PATH = "registry/cases.json"
REQUIRED_BRANCH_PREFIX = "admission/"
BLOCKED_BRANCHES = {"main", "master"}


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _pretty_registry_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _artifact_bytes(value: Any) -> bytes:
    return value.encode("utf-8") if isinstance(value, str) else _canonical_json_bytes(value)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _plan_hash_payload(plan: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(plan)
    payload.pop("plan_sha256", None)
    return payload


def _repo(root: Path) -> Path:
    repo = root.resolve()
    registry = repo / REGISTRY_RELATIVE_PATH
    if not registry.is_file():
        raise CaseServiceError(
            "target repository requires registry/cases.json / 대상 저장소에 registry/cases.json이 필요합니다"
        )
    return repo


def _read_registry_bytes(repo: Path) -> bytes:
    try:
        return (repo / REGISTRY_RELATIVE_PATH).read_bytes()
    except OSError as exc:
        raise CaseServiceError("cannot read registry baseline / registry 기준선을 읽을 수 없습니다") from exc


def _read_registry(repo: Path) -> dict[str, Any]:
    raw = _read_registry_bytes(repo)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CaseServiceError("target registry is not valid UTF-8 JSON / 대상 registry JSON 오류") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("cases"), list):
        raise CaseServiceError("target registry is malformed / 대상 registry 구조 오류")
    return payload


def _safe_relative(repo: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or relative.startswith(("/", "\\")):
        raise CaseServiceError(f"unsafe repository path / 위험한 저장소 경로: {relative}")
    rel = Path(relative)
    if any(part in {"", ".", ".."} for part in rel.parts):
        raise CaseServiceError(f"unsafe repository path / 위험한 저장소 경로: {relative}")
    target = repo.joinpath(*rel.parts)
    try:
        target.resolve(strict=False).relative_to(repo)
    except ValueError as exc:
        raise CaseServiceError(f"repository path escapes root / 저장소 경로탈출: {relative}") from exc
    current = repo
    for part in rel.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise CaseServiceError(f"symlink path component blocked / symlink 경로 차단: {relative}")
    return target


def _parse_gitdir(repo: Path) -> Path:
    marker = repo / ".git"
    if marker.is_symlink():
        raise CaseServiceError("symlink .git is blocked / symlink .git 차단")
    if marker.is_dir():
        return marker
    if marker.is_file():
        try:
            text = marker.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise CaseServiceError("cannot read .git worktree marker / .git worktree marker 읽기 실패") from exc
        if not text.startswith("gitdir:"):
            raise CaseServiceError("invalid .git worktree marker / .git worktree marker 오류")
        raw = text.split(":", 1)[1].strip()
        gitdir = Path(raw)
        if not gitdir.is_absolute():
            gitdir = (repo / gitdir).resolve()
        if not gitdir.is_dir():
            raise CaseServiceError("worktree gitdir does not exist / worktree gitdir 없음")
        return gitdir
    raise CaseServiceError("explicit Git checkout/worktree required / 명시적 Git checkout/worktree가 필요합니다")


def current_git_branch(root: Path) -> str:
    repo = _repo(root)
    gitdir = _parse_gitdir(repo)
    try:
        head = (gitdir / "HEAD").read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise CaseServiceError("cannot read Git HEAD / Git HEAD 읽기 실패") from exc
    prefix = "ref: refs/heads/"
    if not head.startswith(prefix):
        raise CaseServiceError("detached HEAD is blocked / detached HEAD는 적용할 수 없습니다")
    branch = head[len(prefix) :]
    if not branch or branch in BLOCKED_BRANCHES or not branch.startswith(REQUIRED_BRANCH_PREFIX):
        raise CaseServiceError(
            f"admission apply requires an {REQUIRED_BRANCH_PREFIX}* branch; current={branch or 'UNKNOWN'} / "
            f"정식 수용 적용은 {REQUIRED_BRANCH_PREFIX}* 브랜치에서만 허용됩니다"
        )
    return branch


def build_repository_change_plan(
    admission_bundle: dict[str, Any], target_root: Path
) -> dict[str, Any]:
    """Build a deterministic PR-ready change plan against current registry bytes."""
    repo = _repo(target_root)
    validation = validate_admission_bundle(admission_bundle, repo, check_collision=True)
    case_id = str(validation["case_id"])
    target_path = str(admission_bundle["target_path"])
    if target_path != f"analyses/equities/{case_id}":
        raise CaseServiceError("admission target path mismatch / 정식 수용 대상경로 불일치")
    case_dir = _safe_relative(repo, target_path)
    if case_dir.exists():
        raise CaseServiceError(f"canonical target already exists / 정식 대상경로가 이미 존재합니다: {target_path}")

    registry_raw = _read_registry_bytes(repo)
    registry = _read_registry(repo)
    if any(isinstance(item, dict) and item.get("case_id") == case_id for item in registry["cases"]):
        raise CaseServiceError(f"case already exists in registry / registry 사례 충돌: {case_id}")

    registry_after = copy.deepcopy(registry)
    registry_after["cases"].append(copy.deepcopy(admission_bundle["registry_entry"]))
    planned_registry_raw = _pretty_registry_bytes(registry_after)

    writes: list[dict[str, str]] = []
    for name in ADMISSION_ARTIFACTS:
        path = f"{target_path}/{name}"
        _safe_relative(repo, path)
        expected = admission_bundle["artifact_sha256"].get(name)
        actual = _sha(_artifact_bytes(admission_bundle["artifacts"][name]))
        if expected != actual:
            raise CaseServiceError(f"admission artifact hash drift / 수용 산출물 해시 drift: {name}")
        writes.append({"path": path, "sha256": actual})

    plan: dict[str, Any] = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "status": PLAN_STATUS,
        "canonical": False,
        "case_id": case_id,
        "source_admission_bundle_sha256": admission_bundle["bundle_sha256"],
        "target_path": target_path,
        "registry_path": REGISTRY_RELATIVE_PATH,
        "expected_registry_sha256": _sha(registry_raw),
        "planned_registry_sha256": _sha(planned_registry_raw),
        "registry_after": registry_after,
        "artifact_writes": writes,
        "branch_policy": {
            "required_prefix": REQUIRED_BRANCH_PREFIX,
            "blocked_branches": ["main", "master"],
            "detached_head_allowed": False,
        },
        "plan_sha256": "",
    }
    plan["plan_sha256"] = _sha(_canonical_json_bytes(_plan_hash_payload(plan)))
    return plan


def validate_repository_change_plan(
    plan: dict[str, Any], admission_bundle: dict[str, Any], target_root: Path
) -> dict[str, Any]:
    """Validate plan integrity and optimistic-concurrency baseline without applying it."""
    repo = _repo(target_root)
    if not isinstance(plan, dict):
        raise CaseServiceError("repository change plan must be an object / 변경계획은 객체여야 합니다")
    if plan.get("schema_version") != PLAN_SCHEMA_VERSION or plan.get("status") != PLAN_STATUS:
        raise CaseServiceError("repository change plan schema/status invalid / 변경계획 스키마·상태 오류")
    if plan.get("canonical") is not False:
        raise CaseServiceError("repository change plan cannot be canonical / 변경계획 자체는 정식일 수 없습니다")
    if plan.get("plan_sha256") != _sha(_canonical_json_bytes(_plan_hash_payload(plan))):
        raise CaseServiceError("repository change plan SHA-256 mismatch / 변경계획 SHA-256 불일치")
    if plan.get("source_admission_bundle_sha256") != admission_bundle.get("bundle_sha256"):
        raise CaseServiceError("plan/admission bundle mismatch / 계획과 수용 bundle 불일치")

    baseline = _sha(_read_registry_bytes(repo))
    if plan.get("expected_registry_sha256") != baseline:
        raise CaseServiceError(
            "registry baseline drift since plan creation / 계획 생성 이후 registry 기준선이 변경되었습니다"
        )

    expected = build_repository_change_plan(admission_bundle, repo)
    if plan != expected:
        raise CaseServiceError("repository change plan is not deterministic reconstruction / 변경계획 결정론적 재구축 불일치")
    return {
        "status": PLAN_STATUS,
        "canonical": False,
        "valid": True,
        "case_id": plan["case_id"],
        "plan_sha256": plan["plan_sha256"],
        "expected_registry_sha256": plan["expected_registry_sha256"],
        "planned_registry_sha256": plan["planned_registry_sha256"],
        "artifact_count": len(plan["artifact_writes"]),
        "branch_required": f"{REQUIRED_BRANCH_PREFIX}*",
    }


def _write_exclusive(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise CaseServiceError(f"staging path already exists / staging 경로 충돌: {path}") from exc
    except OSError as exc:
        raise CaseServiceError(f"failed to stage repository bytes / 저장소 bytes 스테이징 실패: {path}") from exc


def _restore_registry(registry_path: Path, original: bytes, token: str) -> None:
    temp = registry_path.parent / f".m12-rollback-{token}.tmp"
    if temp.exists():
        temp.unlink()
    _write_exclusive(temp, original)
    os.replace(temp, registry_path)


def apply_repository_change_plan(
    plan: dict[str, Any], admission_bundle: dict[str, Any], target_root: Path
) -> dict[str, Any]:
    """Apply exact admission bytes to an explicit `admission/*` checkout with rollback."""
    repo = _repo(target_root)
    validation = validate_repository_change_plan(plan, admission_bundle, repo)
    branch = current_git_branch(repo)
    case_dir = _safe_relative(repo, plan["target_path"])
    if case_dir.exists():
        raise CaseServiceError("canonical target appeared after planning / 계획 후 정식 대상경로가 생성되었습니다")

    registry_path = _safe_relative(repo, REGISTRY_RELATIVE_PATH)
    original_registry = registry_path.read_bytes()
    if _sha(original_registry) != plan["expected_registry_sha256"]:
        raise CaseServiceError("registry baseline drift before apply / 적용 직전 registry 기준선 drift")

    parent = case_dir.parent
    parent.mkdir(parents=True, exist_ok=True)
    if parent.is_symlink():
        raise CaseServiceError("canonical parent symlink blocked / 정식 상위경로 symlink 차단")
    token = plan["plan_sha256"][:16]
    stage_dir = parent / f".m12-stage-{token}"
    registry_tmp = registry_path.parent / f".m12-registry-{token}.tmp"
    if stage_dir.exists() or registry_tmp.exists():
        raise CaseServiceError("staging collision; clean prior failed staging first / 이전 staging 흔적과 충돌합니다")

    artifacts = admission_bundle["artifacts"]
    moved_case = False
    registry_replaced = False
    try:
        stage_dir.mkdir(parents=False, exist_ok=False)
        for name in ADMISSION_ARTIFACTS:
            raw = _artifact_bytes(artifacts[name])
            expected = admission_bundle["artifact_sha256"][name]
            if _sha(raw) != expected:
                raise CaseServiceError(f"artifact changed before apply / 적용 전 산출물 변경: {name}")
            _write_exclusive(stage_dir / name, raw)
            if _sha((stage_dir / name).read_bytes()) != expected:
                raise CaseServiceError(f"staged artifact bytes mismatch / staged bytes 불일치: {name}")

        planned_registry_raw = _pretty_registry_bytes(plan["registry_after"])
        if _sha(planned_registry_raw) != plan["planned_registry_sha256"]:
            raise CaseServiceError("planned registry bytes mismatch / 계획된 registry bytes 불일치")
        _write_exclusive(registry_tmp, planned_registry_raw)

        os.replace(stage_dir, case_dir)
        moved_case = True
        os.replace(registry_tmp, registry_path)
        registry_replaced = True

        for item in plan["artifact_writes"]:
            applied = _safe_relative(repo, item["path"])
            if _sha(applied.read_bytes()) != item["sha256"]:
                raise CaseServiceError(f"applied artifact bytes mismatch / 적용 산출물 bytes 불일치: {item['path']}")
        if _sha(registry_path.read_bytes()) != plan["planned_registry_sha256"]:
            raise CaseServiceError("applied registry bytes mismatch / 적용 registry bytes 불일치")

        case_id = plan["case_id"]
        canonical_validation = validate_case(case_id, repo)
        runtime = run_case(case_id, repo)
        evidence = evidence_view(case_id, repo)
        preview = preview_case(case_id, {}, repo)
        expected_runtime = admission_bundle["artifacts"]["valuation_result.json"]["runtime"]
        if runtime["runtime"] != expected_runtime:
            raise CaseServiceError("post-apply runtime differs from admission / 적용 후 runtime 수용값 불일치")
        if not evidence.get("read_only") or preview.get("status") != "PREVIEW_NOT_CANONICAL":
            raise CaseServiceError("post-apply read-path validation failed / 적용 후 읽기경로 검증 실패")

        return {
            "status": APPLIED_STATUS,
            "canonical": False,
            "repository_change_applied": True,
            "case_id": case_id,
            "branch": branch,
            "plan_sha256": validation["plan_sha256"],
            "registry_sha256": plan["planned_registry_sha256"],
            "adapter": canonical_validation.get("adapter"),
            "post_apply_validation": "PASS",
            "next_action_en": "Review the exact working-tree diff, open a repository PR, run full CI, and merge only after human review.",
            "next_action_ko": "정확한 working-tree diff를 검토하고 저장소 PR을 생성한 뒤 전체 CI와 인간 검토 후에만 병합하십시오.",
        }
    except Exception as exc:
        rollback_errors: list[str] = []
        if registry_replaced:
            try:
                _restore_registry(registry_path, original_registry, token)
            except Exception as rollback_exc:  # pragma: no cover - catastrophic filesystem failure
                rollback_errors.append(f"registry rollback failed: {rollback_exc}")
        if moved_case and case_dir.exists():
            try:
                shutil.rmtree(case_dir)
            except OSError as rollback_exc:  # pragma: no cover - catastrophic filesystem failure
                rollback_errors.append(f"case rollback failed: {rollback_exc}")
        if stage_dir.exists():
            shutil.rmtree(stage_dir, ignore_errors=True)
        if registry_tmp.exists():
            try:
                registry_tmp.unlink()
            except OSError:
                pass
        if rollback_errors:
            raise CaseServiceError(
                "admission apply failed and rollback was incomplete / 적용 실패 후 롤백 불완전: "
                + "; ".join(rollback_errors)
            ) from exc
        if isinstance(exc, CaseServiceError):
            raise
        raise CaseServiceError(f"admission apply failed and was rolled back / 적용 실패·롤백 완료: {exc}") from exc


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CaseServiceError(f"{label} file not found / {label} 파일 없음: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CaseServiceError(f"invalid {label} JSON / {label} JSON 오류: {exc}") from exc
    if not isinstance(payload, dict):
        raise CaseServiceError(f"{label} must be a JSON object / {label}는 JSON 객체여야 합니다")
    return payload
