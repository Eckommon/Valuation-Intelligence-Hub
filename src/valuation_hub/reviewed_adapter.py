"""Versioned reviewed-Draft canonical adapter helpers / 검토 Draft 정식 adapter 도우미.

This module defines adapter identity and lossless runtime normalization. It does
not own valuation formulas; reviewed Draft execution is delegated to the M8
Draft service, which already routes to the shared FCFF/Venture kernels.
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


def normalize_reviewed_runtime(draft: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Validate exact reviewed Draft and normalize runtime to canonical service shape.

    Returns `(normalized_draft, draft_result, canonical_runtime)`.
    Equity Draft runtime is unwrapped from `runtime.scenarios` so existing Web and
    service consumers continue receiving the legacy external equity runtime shape.
    """
    # Local import avoids module-initialization cycle: draft_service uses CaseServiceError.
    from valuation_hub.draft_service import run_draft, validate_draft

    normalized = validate_draft(draft)
    result = run_draft(normalized)
    if normalized["model"] == "equity_fcff":
        runtime = result["runtime"]["scenarios"]
    else:
        runtime = result["runtime"]
    return normalized, result, runtime
