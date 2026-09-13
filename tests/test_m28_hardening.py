"""M28 tamper, stale, and explicit-zero hardening regressions."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from valuation_hub.binding_apply_m28 import apply_binding_approval, build_binding_approval
from valuation_hub.case_service import CaseServiceError
from valuation_hub.minority_interest import (
    build_minority_interest_review_assertion,
    extract_dart_minority_interest_candidate,
    finalize_reviewed_minority_interest,
    normalize_minority_interest_candidate,
    validate_minority_interest_review_assertion,
)
from valuation_hub.minority_interest_draft_binding import build_binding_proposal_with_minority_interest


def _rehash(value: dict, field: str) -> str:
    copied = copy.deepcopy(value); copied.pop(field, None)
    return hashlib.sha256(json.dumps(copied, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _fixtures():
    path = Path(__file__).with_name("test_m28_minority_interest_binding.py")
    spec = importlib.util.spec_from_file_location("_m28_hardening_fixture", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def test_resigned_review_cannot_change_resolved_period_or_freshness() -> None:
    f = _fixtures()
    observation = normalize_minority_interest_candidate(extract_dart_minority_interest_candidate(f._dart_snapshot()))
    assertion = build_minority_interest_review_assertion(
        observation, as_of="2026-09-12", reviewer="human", approved_at="2026-09-12T21:00:00+09:00",
        review_basis="Reviewed H1 period end.", asserted_period_end="2026-06-30", max_age_days=550,
    )
    forged = copy.deepcopy(assertion)
    forged["resolved_period_end"] = "2026-09-01"
    forged["assertion_sha256"] = _rehash(forged, "assertion_sha256")
    with pytest.raises(CaseServiceError, match="date resolution mismatch|날짜해결 불일치|freshness mismatch|최신성 불일치"):
        validate_minority_interest_review_assertion(forged, observation)

    forged = copy.deepcopy(assertion)
    forged["freshness"] = {"status": "FRESH", "age_days": 0, "max_age_days": 550}
    forged["assertion_sha256"] = _rehash(forged, "assertion_sha256")
    with pytest.raises(CaseServiceError, match="freshness mismatch|최신성 불일치"):
        validate_minority_interest_review_assertion(forged, observation)


def test_stale_reviewed_package_cannot_bind() -> None:
    f = _fixtures()
    observation = normalize_minority_interest_candidate(extract_dart_minority_interest_candidate(f._dart_snapshot()))
    assertion = build_minority_interest_review_assertion(
        observation, as_of="2026-09-12", reviewer="human", approved_at="2026-09-12T21:00:00+09:00",
        review_basis="Explicit stale-policy regression.", asserted_period_end="2026-06-30", max_age_days=1,
    )
    package = finalize_reviewed_minority_interest(observation, assertion)
    assert package["binding_eligibility"] == {"eligible": False, "reason": "STALE_MINORITY_INTEREST"}
    with pytest.raises(CaseServiceError, match="reviewed fresh|검토완료 최신"):
        build_binding_proposal_with_minority_interest(f._v07(), package)


def test_explicit_zero_survives_v08_and_apply_without_missing_inference() -> None:
    f = _fixtures()
    package = f._minority_package("0")
    proposal = build_binding_proposal_with_minority_interest(f._v07(), package)
    draft = f._draft(); draft["equity"]["minority_interest"] = 123.0
    approval = build_binding_approval(
        proposal, draft, reviewer="human", target_entity_id="DART_CORP:00126380", target_financial_scope="CFS",
        approved_fields=["equity.minority_interest"], approved_at="2026-09-12T21:30:00+09:00",
    )
    result = apply_binding_approval(proposal, draft, approval)
    assert result["applied_diffs"][0]["before"] == 123.0
    assert result["applied_diffs"][0]["after"] == 0
    assert result["draft_after"]["equity"]["minority_interest"] == 0
