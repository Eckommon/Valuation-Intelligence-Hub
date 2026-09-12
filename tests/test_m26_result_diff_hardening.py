"""M26 result-diff completeness hardening tests / M26 결과 diff 완전성 강화 테스트."""
from __future__ import annotations

import pytest

from valuation_hub import binding_apply
from valuation_hub.case_service import CaseServiceError


def test_bound_result_rejects_duplicate_diff_fields_even_when_resealed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Approved fields and applied diff fields must be an exact one-to-one set.

    This fixture intentionally models the pre-hardening bypass: approval contains
    fields A+B, while the result carries two sequentially valid A diffs and never
    applies B. All outer hashes are treated as freshly re-sealed so only the
    structural completeness invariant can reject the result.
    """
    monkeypatch.setattr(binding_apply, "validate_binding_proposal_any", lambda proposal: {})
    monkeypatch.setattr(binding_apply, "validate_binding_approval", lambda approval, proposal, draft: {})
    monkeypatch.setattr(binding_apply, "validate_draft", lambda draft: draft)
    monkeypatch.setattr(
        binding_apply,
        "_direct_fields",
        lambda proposal: {"A": {"field": "A"}, "B": {"field": "B"}},
    )
    monkeypatch.setattr(binding_apply, "_binding_context", lambda proposal, decision: {})
    monkeypatch.setattr(binding_apply, "_get_field", lambda draft, field, context=None: draft["value"])
    monkeypatch.setattr(binding_apply, "_target_value", lambda field, context: 1 if field == "A" else 2)

    def set_field(draft: dict, field: str, value: int, context=None) -> None:
        draft["value"] = value

    monkeypatch.setattr(binding_apply, "_set_field", set_field)
    monkeypatch.setattr(
        binding_apply,
        "_diff_for",
        lambda field, old, new, decision, context: {
            "field": field,
            "before": old,
            "after": new,
            "source_metric": None,
        },
    )
    monkeypatch.setattr(binding_apply, "_sha", lambda value: "sealed")

    result = {
        "schema_version": binding_apply.RESULT_SCHEMA,
        "status": binding_apply.RESULT_STATUS,
        "canonical": False,
        "binding_proposal": {"draft_input_matrix": [{"field": "A"}, {"field": "B"}]},
        "approval": {"approved_fields": ["A", "B"]},
        "draft_before": {"value": 0},
        "draft_before_sha256": "sealed",
        "applied_diffs": [
            {"field": "A", "before": 0, "after": 1, "source_metric": None},
            {"field": "A", "before": 1, "after": 1, "source_metric": None},
        ],
        "draft_after": {"value": 1},
        "draft_after_sha256": "sealed",
        "unresolved_binding_matrix": [],
        "result_sha256": "sealed",
    }

    with pytest.raises(CaseServiceError, match="exactly match approved fields|승인필드와 정확히 일치"):
        binding_apply.validate_bound_draft_result(result)
