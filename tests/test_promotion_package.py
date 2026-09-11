"""Promotion-package staging tests / 승격 패키지 스테이징 테스트."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_service import run_draft, template
from valuation_hub.promotion import build_candidate, validate_candidate
from valuation_hub.promotion_package import (
    build_promotion_package,
    materialize_promotion_package,
    validate_materialized_package,
    validate_promotion_package,
)

ROOT = Path(__file__).resolve().parents[1]


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _approved_candidate() -> dict:
    candidate = build_candidate(template("equity_fcff", ROOT))
    draft = candidate["draft"]
    observed = {
        "market_price": draft["market_price"],
        "equity.diluted_shares": draft["equity"]["diluted_shares"],
        "equity.debt": draft["equity"]["debt"],
        "equity.cash": draft["equity"]["cash"],
        "equity.minority_interest": draft["equity"]["minority_interest"],
    }
    evidence = []
    for binding in candidate["input_governance"]:
        path = binding["path"]
        if path in observed:
            claim_id = "pkg_" + path.replace(".", "_")
            binding.update({"class": "FACT", "claim_ids": [claim_id], "rationale": "Observed value."})
            evidence.append(
                {
                    "claim_id": claim_id,
                    "class": "FACT",
                    "metric": path,
                    "value": observed[path],
                    "unit": draft["currency"],
                    "as_of": "2026-09-11",
                    "status": "CURRENT",
                    "waiver": None,
                    "source": {"publisher": "Package test evidence", "locator": "https://example.invalid/package", "tier": "B"},
                }
            )
        else:
            binding.update({"class": "ASSUMPTION", "claim_ids": [], "rationale": "Reviewed forward assumption."})
    candidate["evidence"] = evidence
    assessment = validate_candidate(candidate)
    candidate["review"] = {
        "decision": "APPROVE",
        "reviewer": "package-human-reviewer",
        "reviewed_at": "2026-09-11T14:50:00+09:00",
        "rationale": "Reviewed candidate for deterministic package staging.",
        "scope_sha256": assessment["review_scope_sha256"],
    }
    return candidate


def _build(candidate: dict | None = None) -> dict:
    return build_promotion_package(
        candidate or _approved_candidate(),
        case_id="KR_TEST_DETERMINISTIC_CO",
        display_name_en="Deterministic Co",
        display_name_ko="결정론 테스트",
        asset_class="public_equity",
        root=ROOT,
    )


def test_same_reviewed_candidate_produces_identical_package_and_hashes() -> None:
    candidate = _approved_candidate()
    left = _build(copy.deepcopy(candidate))
    right = _build(copy.deepcopy(candidate))
    assert left == right
    assert len(left["package_sha256"]) == 64
    assert set(left["artifact_sha256"]) == set(left["artifacts"])
    assert left["status"] == "PROMOTION_PACKAGE_STAGED"
    assert left["canonical"] is False


def test_package_preserves_draft_and_declares_adapter_requirement_without_lossy_coercion() -> None:
    candidate = _approved_candidate()
    package = _build(candidate)
    reviewed = package["artifacts"]["reviewed_case_payload.json"]
    assert reviewed["draft"] == candidate["draft"]
    assert package["adapter_requirement"]["compatibility_status"] == "NOT_EXECUTABLE_UNTIL_CANONICAL_ADAPTER"
    assert package["adapter_requirement"]["required_canonical_adapter"] == "reviewed-draft-equity-fcff-v0.1"
    proposal = package["artifacts"]["REGISTRY_PROPOSAL.json"]
    assert proposal["registration_blocked"] is True
    assert proposal["status"] == "PROPOSAL_ONLY_NOT_REGISTRY_ENTRY"


def test_staged_valuation_reproduces_shared_draft_kernel() -> None:
    candidate = _approved_candidate()
    package = _build(candidate)
    expected = run_draft(candidate["draft"])
    assert package["artifacts"]["staged_valuation_result.json"]["valuation"] == expected
    result = validate_promotion_package(package, ROOT)
    assert result["valid"] is True
    assert result["canonical"] is False


def test_nonapproved_or_post_review_mutated_candidate_fails_closed() -> None:
    candidate = _approved_candidate()
    candidate["review"]["decision"] = "PENDING"
    with pytest.raises(CaseServiceError, match="APPROVE"):
        _build(candidate)

    candidate = _approved_candidate()
    next(item for item in candidate["input_governance"] if item["class"] == "ASSUMPTION")["rationale"] += " mutated"
    with pytest.raises(CaseServiceError, match="hash mismatch"):
        _build(candidate)


def test_unsafe_or_existing_case_ids_fail_closed() -> None:
    candidate = _approved_candidate()
    with pytest.raises(CaseServiceError, match="case_id"):
        build_promotion_package(
            candidate,
            case_id="../ESCAPE",
            display_name_en="Bad",
            display_name_ko="Bad",
            asset_class="public_equity",
            root=ROOT,
        )
    with pytest.raises(CaseServiceError, match="ID 충돌"):
        build_promotion_package(
            candidate,
            case_id="KR_010120_LS_ELECTRIC",
            display_name_en="Collision",
            display_name_ko="충돌",
            asset_class="public_equity",
            root=ROOT,
        )


def test_any_embedded_artifact_tamper_invalidates_package() -> None:
    package = _build()
    tampered = copy.deepcopy(package)
    tampered["artifacts"]["staged_valuation_result.json"]["valuation"]["market_price"] += 1
    with pytest.raises(CaseServiceError, match="artifact hash mismatch"):
        validate_promotion_package(tampered, ROOT)


def test_materialized_package_is_byte_verified_and_tamper_detected(tmp_path: Path) -> None:
    package = _build()
    output = tmp_path / "promotion-package"
    materialized = materialize_promotion_package(package, output, ROOT)
    assert materialized["materialized"] is True
    assert (output / "PACKAGE.json").is_file()
    assert validate_materialized_package(output, ROOT)["valid"] is True

    report = output / "REPORT.md"
    report.write_text(report.read_text(encoding="utf-8") + "tamper", encoding="utf-8")
    with pytest.raises(CaseServiceError, match="bytes mismatch"):
        validate_materialized_package(output, ROOT)


def test_inside_repo_output_is_restricted_to_promotion_workspace() -> None:
    package = _build()
    with pytest.raises(CaseServiceError, match="workspace/promotion_packages"):
        materialize_promotion_package(package, ROOT / "analyses" / "bad-output", ROOT)


def test_package_workflow_never_mutates_canonical_repository_state(tmp_path: Path) -> None:
    protected = [
        ROOT / "registry" / "cases.json",
        ROOT / "analyses" / "equities" / "KR_010120_LS_ELECTRIC" / "case_inputs.json",
        ROOT / "analyses" / "equities" / "KR_010120_LS_ELECTRIC" / "valuation_result.json",
        ROOT / "analyses" / "equities" / "KR_010120_LS_ELECTRIC" / "evidence_manifest.json",
    ]
    before = {path: _digest(path) for path in protected}
    package = _build()
    validate_promotion_package(package, ROOT)
    materialize_promotion_package(package, tmp_path / "safe", ROOT)
    after = {path: _digest(path) for path in protected}
    assert before == after
