"""M29 guarded repository-plan dispatcher.

Historical M12 behavior remains in admission_apply.py. This module adds v0.2-aware
plan build/validation while keeping actual canonical application a separately
governed admission/* operation.
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from valuation_hub import admission_apply as legacy
from valuation_hub.admission_m29 import ADMISSION_ARTIFACTS, validate_admission_bundle
from valuation_hub.case_service import CaseServiceError

PLAN_SCHEMA_VERSION = legacy.PLAN_SCHEMA_VERSION
PLAN_STATUS = legacy.PLAN_STATUS
REGISTRY_RELATIVE_PATH = legacy.REGISTRY_RELATIVE_PATH
REQUIRED_BRANCH_PREFIX = legacy.REQUIRED_BRANCH_PREFIX
BLOCKED_BRANCHES = legacy.BLOCKED_BRANCHES


def build_repository_change_plan(admission_bundle: dict[str, Any], target_root: Path) -> dict[str, Any]:
    """Build the existing M12 deterministic plan using the M29 admission dispatcher."""
    repo = legacy._repo(target_root)
    validation = validate_admission_bundle(admission_bundle, repo, check_collision=True)
    case_id = str(validation["case_id"])
    target_path = str(admission_bundle["target_path"])
    if target_path != f"analyses/equities/{case_id}":
        raise CaseServiceError("admission target path mismatch / 정식 수용 대상경로 불일치")
    case_dir = legacy._safe_relative(repo, target_path)
    if case_dir.exists():
        raise CaseServiceError(f"canonical target already exists / 정식 대상경로가 이미 존재합니다: {target_path}")

    registry_raw = legacy._read_registry_bytes(repo)
    registry = legacy._read_registry(repo)
    if any(isinstance(item, dict) and item.get("case_id") == case_id for item in registry["cases"]):
        raise CaseServiceError(f"case already exists in registry / registry 사례 충돌: {case_id}")

    registry_after = copy.deepcopy(registry)
    registry_after["cases"].append(copy.deepcopy(admission_bundle["registry_entry"]))
    planned_registry_raw = legacy._pretty_registry_bytes(registry_after)

    writes: list[dict[str, str]] = []
    for name in ADMISSION_ARTIFACTS:
        path = f"{target_path}/{name}"
        legacy._safe_relative(repo, path)
        expected = admission_bundle["artifact_sha256"].get(name)
        actual = legacy._sha(legacy._artifact_bytes(admission_bundle["artifacts"][name]))
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
        "expected_registry_sha256": legacy._sha(registry_raw),
        "planned_registry_sha256": legacy._sha(planned_registry_raw),
        "registry_after": registry_after,
        "artifact_writes": writes,
        "branch_policy": {
            "required_prefix": REQUIRED_BRANCH_PREFIX,
            "blocked_branches": ["main", "master"],
            "detached_head_allowed": False,
        },
        "plan_sha256": "",
    }
    plan["plan_sha256"] = legacy._sha(legacy._canonical_json_bytes(legacy._plan_hash_payload(plan)))
    return plan


def validate_repository_change_plan(
    plan: dict[str, Any], admission_bundle: dict[str, Any], target_root: Path
) -> dict[str, Any]:
    repo = legacy._repo(target_root)
    if not isinstance(plan, dict):
        raise CaseServiceError("repository change plan must be an object / 변경계획은 객체여야 합니다")
    if plan.get("schema_version") != PLAN_SCHEMA_VERSION or plan.get("status") != PLAN_STATUS or plan.get("canonical") is not False:
        raise CaseServiceError("repository change plan schema/status invalid / 변경계획 스키마·상태 오류")
    if plan.get("plan_sha256") != legacy._sha(legacy._canonical_json_bytes(legacy._plan_hash_payload(plan))):
        raise CaseServiceError("repository change plan SHA-256 mismatch / 변경계획 SHA-256 불일치")
    if plan.get("source_admission_bundle_sha256") != admission_bundle.get("bundle_sha256"):
        raise CaseServiceError("plan/admission bundle mismatch / 계획과 수용 bundle 불일치")
    if plan.get("expected_registry_sha256") != legacy._sha(legacy._read_registry_bytes(repo)):
        raise CaseServiceError("registry baseline drift since plan creation / 계획 생성 이후 registry 기준선 변경")
    expected = build_repository_change_plan(admission_bundle, repo)
    if plan != expected:
        raise CaseServiceError("repository change plan deterministic reconstruction mismatch / 변경계획 결정론적 재구축 불일치")
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
