"""M12 guarded admission-plan/apply tests / 정식 수용 안전 적용 테스트."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from valuation_hub.admission import build_admission_bundle
from valuation_hub.admission_apply import (
    APPLIED_STATUS,
    apply_repository_change_plan,
    build_repository_change_plan,
    validate_repository_change_plan,
)
from valuation_hub.case_service import CaseServiceError, run_case, validate_case
from valuation_hub.draft_service import template
from valuation_hub.interactive import evidence_view, preview_case
from valuation_hub.promotion import build_candidate, validate_candidate
from valuation_hub.promotion_package import build_promotion_package

ROOT = Path(__file__).resolve().parents[1]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _approved_candidate(model: str) -> dict:
    draft = template(model, ROOT)
    if model == "equity_fcff":
        base = draft["equity"]["scenarios"]["BASE"]
        bear = copy.deepcopy(base)
        bull = copy.deepcopy(base)
        bear["wacc"], bear["terminal_growth"] = 0.12, 0.015
        bull["wacc"], bull["terminal_growth"] = 0.09, 0.03
        draft["equity"]["scenarios"] = {"BEAR": bear, "BASE": base, "BULL": bull}

    candidate = build_candidate(draft)
    normalized = candidate["draft"]
    observed = {"market_price": normalized["market_price"]}
    if model == "equity_fcff":
        observed.update(
            {
                "equity.diluted_shares": normalized["equity"]["diluted_shares"],
                "equity.debt": normalized["equity"]["debt"],
                "equity.cash": normalized["equity"]["cash"],
                "equity.minority_interest": normalized["equity"]["minority_interest"],
            }
        )

    evidence = []
    for binding in candidate["input_governance"]:
        path = binding["path"]
        if path in observed:
            claim_id = "m12_" + path.replace(".", "_").replace("[", "_").replace("]", "")
            binding.update({"class": "FACT", "claim_ids": [claim_id], "rationale": "Observed M12 fixture."})
            evidence.append(
                {
                    "claim_id": claim_id,
                    "class": "FACT",
                    "metric": path,
                    "value": observed[path],
                    "unit": normalized["currency"],
                    "as_of": "2026-09-11",
                    "status": "CURRENT",
                    "waiver": None,
                    "source": {
                        "publisher": "M12 fixture",
                        "locator": f"https://example.invalid/{claim_id}",
                        "tier": "B",
                    },
                }
            )
        else:
            binding.update(
                {
                    "class": "ASSUMPTION",
                    "claim_ids": [],
                    "rationale": "Explicit reviewed forward assumption for M12.",
                }
            )
    candidate["evidence"] = evidence
    assessment = validate_candidate(candidate)
    candidate["review"] = {
        "decision": "APPROVE",
        "reviewer": "m12-human-reviewer",
        "reviewed_at": "2026-09-11T15:40:00+09:00",
        "rationale": "Reviewed for guarded admission application test.",
        "scope_sha256": assessment["review_scope_sha256"],
    }
    return candidate


def _admission(model: str) -> dict:
    if model == "equity_fcff":
        case_id = "KR_M12_TEST_EQUITY"
        name_en, name_ko, asset_class = "M12 Equity", "M12 주식", "public_equity"
    else:
        case_id = "US_M12_TEST_VENTURE"
        name_en, name_ko, asset_class = "M12 Venture", "M12 벤처", "public_equity_venture"
    package = build_promotion_package(
        _approved_candidate(model),
        case_id=case_id,
        display_name_en=name_en,
        display_name_ko=name_ko,
        asset_class=asset_class,
        root=ROOT,
    )
    return build_admission_bundle(package, ROOT)


def _target_repo(tmp_path: Path, branch: str = "admission/m12-test") -> Path:
    repo = tmp_path / "target"
    (repo / "registry").mkdir(parents=True)
    (repo / "registry" / "cases.json").write_bytes((ROOT / "registry" / "cases.json").read_bytes())
    (repo / "analyses" / "equities").mkdir(parents=True)
    (repo / ".git").mkdir()
    (repo / ".git" / "HEAD").write_text(f"ref: refs/heads/{branch}\n", encoding="utf-8")
    return repo


def test_same_admission_and_registry_baseline_produce_identical_plan(tmp_path: Path) -> None:
    admission = _admission("equity_fcff")
    repo = _target_repo(tmp_path)
    left = build_repository_change_plan(copy.deepcopy(admission), repo)
    right = build_repository_change_plan(copy.deepcopy(admission), repo)
    assert left == right
    assert left["status"] == "REPOSITORY_CHANGE_PLANNED"
    assert left["canonical"] is False
    assert len(left["plan_sha256"]) == 64
    assert left["planned_registry_sha256"] != left["expected_registry_sha256"]
    assert len(left["artifact_writes"]) == 6
    assert validate_repository_change_plan(left, admission, repo)["valid"] is True


def test_registry_drift_between_plan_and_apply_fails_closed_without_case_write(tmp_path: Path) -> None:
    admission = _admission("equity_fcff")
    repo = _target_repo(tmp_path)
    plan = build_repository_change_plan(admission, repo)
    registry = repo / "registry" / "cases.json"
    original = registry.read_bytes()
    registry.write_bytes(original + b"\n")
    drifted = registry.read_bytes()
    with pytest.raises(CaseServiceError, match="baseline drift"):
        apply_repository_change_plan(plan, admission, repo)
    assert registry.read_bytes() == drifted
    assert not (repo / plan["target_path"]).exists()


@pytest.mark.parametrize("branch", ["main", "master", "feature/not-admission"])
def test_apply_blocks_non_admission_branches_without_mutation(tmp_path: Path, branch: str) -> None:
    admission = _admission("venture_probability")
    repo = _target_repo(tmp_path, branch)
    plan = build_repository_change_plan(admission, repo)
    registry = repo / "registry" / "cases.json"
    before = registry.read_bytes()
    with pytest.raises(CaseServiceError, match="admission/.*branch"):
        apply_repository_change_plan(plan, admission, repo)
    assert registry.read_bytes() == before
    assert not (repo / plan["target_path"]).exists()


def test_apply_blocks_detached_head(tmp_path: Path) -> None:
    admission = _admission("equity_fcff")
    repo = _target_repo(tmp_path)
    plan = build_repository_change_plan(admission, repo)
    (repo / ".git" / "HEAD").write_text("243f941b2f323ac5fdca31b86e13966950156114\n", encoding="utf-8")
    with pytest.raises(CaseServiceError, match="detached HEAD"):
        apply_repository_change_plan(plan, admission, repo)
    assert not (repo / plan["target_path"]).exists()


@pytest.mark.parametrize("model", ["equity_fcff", "venture_probability"])
def test_guarded_apply_creates_exact_pr_ready_case_and_passes_full_read_path(model: str, tmp_path: Path) -> None:
    admission = _admission(model)
    repo = _target_repo(tmp_path)
    plan = build_repository_change_plan(admission, repo)
    result = apply_repository_change_plan(plan, admission, repo)
    assert result["status"] == APPLIED_STATUS
    assert result["canonical"] is False
    assert result["branch"] == "admission/m12-test"
    assert result["post_apply_validation"] == "PASS"

    case_id = admission["case_id"]
    validation = validate_case(case_id, repo)
    run = run_case(case_id, repo)
    evidence = evidence_view(case_id, repo)
    preview = preview_case(case_id, {}, repo)
    assert validation["adapter"] == admission["registry_entry"]["adapter"]
    assert run["runtime"] == admission["artifacts"]["valuation_result.json"]["runtime"]
    assert evidence["read_only"] is True
    assert preview["status"] == "PREVIEW_NOT_CANONICAL"
    assert _sha(repo / "registry" / "cases.json") == plan["planned_registry_sha256"]
    for item in plan["artifact_writes"]:
        assert _sha(repo / item["path"]) == item["sha256"]


def test_existing_target_path_or_registry_case_fails_before_write(tmp_path: Path) -> None:
    admission = _admission("equity_fcff")
    repo = _target_repo(tmp_path)
    target = repo / admission["target_path"]
    target.mkdir(parents=True)
    registry_before = (repo / "registry" / "cases.json").read_bytes()
    with pytest.raises(CaseServiceError, match="already exists"):
        build_repository_change_plan(admission, repo)
    assert (repo / "registry" / "cases.json").read_bytes() == registry_before


def test_symlink_escape_is_blocked(tmp_path: Path) -> None:
    admission = _admission("equity_fcff")
    repo = _target_repo(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    equities = repo / "analyses" / "equities"
    equities.rmdir()
    try:
        equities.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable on this platform")
    with pytest.raises(CaseServiceError, match="symlink|escapes"):
        build_repository_change_plan(admission, repo)
    assert list(outside.iterdir()) == []


def test_post_apply_validation_failure_rolls_back_registry_and_case(tmp_path: Path, monkeypatch) -> None:
    import valuation_hub.admission_apply as module

    admission = _admission("equity_fcff")
    repo = _target_repo(tmp_path)
    plan = build_repository_change_plan(admission, repo)
    registry = repo / "registry" / "cases.json"
    before = registry.read_bytes()

    def fail_validation(*args, **kwargs):
        raise CaseServiceError("forced post-apply validation failure")

    monkeypatch.setattr(module, "validate_case", fail_validation)
    with pytest.raises(CaseServiceError, match="forced post-apply"):
        apply_repository_change_plan(plan, admission, repo)
    assert registry.read_bytes() == before
    assert not (repo / plan["target_path"]).exists()


def test_tampered_plan_or_admission_fails_before_apply(tmp_path: Path) -> None:
    admission = _admission("venture_probability")
    repo = _target_repo(tmp_path)
    plan = build_repository_change_plan(admission, repo)
    registry_before = (repo / "registry" / "cases.json").read_bytes()

    tampered_plan = copy.deepcopy(plan)
    tampered_plan["registry_after"]["cases"][-1]["display_name_en"] = "Tampered"
    with pytest.raises(CaseServiceError, match="SHA-256"):
        apply_repository_change_plan(tampered_plan, admission, repo)

    tampered_admission = copy.deepcopy(admission)
    tampered_admission["artifacts"]["REPORT.md"] += "tamper"
    with pytest.raises(CaseServiceError):
        build_repository_change_plan(tampered_admission, repo)

    assert (repo / "registry" / "cases.json").read_bytes() == registry_before
    assert not (repo / plan["target_path"]).exists()
