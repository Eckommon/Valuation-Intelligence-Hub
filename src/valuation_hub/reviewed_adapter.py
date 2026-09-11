"""Versioned reviewed-Draft canonical adapter helpers / 검토 Draft 정식 adapter 도우미.

This module defines adapter identity, admission compatibility profiles, and
lossless runtime normalization. It does not own valuation formulas; reviewed
Draft execution is delegated to the M8 Draft service, which already routes to
the shared FCFF/Venture kernels.
"""

from __future__ import annotations

from typing import Any

REVIEWED_EQUITY_ADAPTER = "reviewed-draft-equity-fcff-v0.1"
REVIEWED_VENTURE_ADAPTER = "reviewed-draft-venture-probability-v0.1"
MODEL_TO_REVIEWED_ADAPTER = {
    "equity_fcff": REVIEWED_EQUITY_ADAPTER,
    "venture_probability": REVIEWED_VENTURE_ADAPTER,
}
REVIEWED_ADAPTER_TO_MODEL = {value: key for key, value in MODEL_TO_REVIEWED_ADAPTER.items()}
REVIEWED_ADMISSION_GATE = "PASS_REVIEWED_DRAFT_PACKAGE_ADMISSION"

# v0.1 canonical admission deliberately preserves the scenario names expected by
# the existing Web/product contract. Generic user Drafts remain free to use other
# names; only canonical admission through these adapter versions is constrained.
CANONICAL_SCENARIO_PROFILES = {
    "equity_fcff": ("BEAR", "BASE", "BULL"),
    "venture_probability": ("FAILURE", "SURVIVAL", "BREAKOUT"),
}


def adapter_for_model(model: str) -> str:
    try:
        return MODEL_TO_REVIEWED_ADAPTER[model]
    except KeyError as exc:
        raise ValueError(f"unsupported reviewed-Draft model: {model}") from exc


def model_for_adapter(adapter: str) -> str:
    try:
        return REVIEWED_ADAPTER_TO_MODEL[adapter]
    except KeyError as exc:
        raise ValueError(f"unsupported reviewed-Draft adapter: {adapter}") from exc


def validate_canonical_profile(draft: dict[str, Any]) -> None:
    """Fail closed when a reviewed Draft cannot satisfy the v0.1 product contract."""
    model = str(draft.get("model", ""))
    expected = CANONICAL_SCENARIO_PROFILES.get(model)
    if expected is None:
        raise ValueError(f"unsupported reviewed-Draft model: {model}")
    if model == "equity_fcff":
        equity = draft.get("equity")
        scenarios = equity.get("scenarios") if isinstance(equity, dict) else None
        actual = tuple(scenarios.keys()) if isinstance(scenarios, dict) else ()
        if set(actual) != set(expected) or len(actual) != len(expected):
            raise ValueError(
                "reviewed equity canonical admission requires exactly BEAR/BASE/BULL scenarios"
            )
    else:
        venture = draft.get("venture")
        rows = venture.get("scenarios") if isinstance(venture, dict) else None
        actual = tuple(str(item.get("name", "")) for item in rows) if isinstance(rows, list) else ()
        if set(actual) != set(expected) or len(actual) != len(expected):
            raise ValueError(
                "reviewed venture canonical admission requires exactly FAILURE/SURVIVAL/BREAKOUT scenarios"
            )


def normalize_reviewed_runtime(
    draft: dict[str, Any], *, require_canonical_profile: bool = False
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Validate exact reviewed Draft and normalize runtime to canonical service shape.

    Returns `(normalized_draft, draft_result, canonical_runtime)`.
    Equity Draft runtime is unwrapped from `runtime.scenarios` so existing Web and
    service consumers continue receiving the legacy external equity runtime shape.
    """
    # Local import avoids module-initialization cycle: draft_service uses CaseServiceError.
    from valuation_hub.draft_service import run_draft, validate_draft

    normalized = validate_draft(draft)
    if require_canonical_profile:
        validate_canonical_profile(normalized)
    result = run_draft(normalized)
    if normalized["model"] == "equity_fcff":
        runtime = result["runtime"]["scenarios"]
    else:
        runtime = result["runtime"]
    return normalized, result, runtime
