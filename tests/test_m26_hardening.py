"""M26 re-signing and projection hardening / M26 재서명·투영 강화 테스트."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub.forecast_assumption import build_forecast_candidate, validate_forecast_candidate
from valuation_hub.forecast_draft_binding import build_binding_proposal_with_forecast, validate_binding_proposal_v6


def _rehash(value: dict, field: str) -> str:
    copied = copy.deepcopy(value)
    copied.pop(field, None)
    return hashlib.sha256(
        json.dumps(copied, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _fixture_module():
    path = Path(__file__).with_name("test_m26_integrated_forecast_binding.py")
    spec = importlib.util.spec_from_file_location("_m26_fixture_module", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_candidate_diagnostic_tamper_rejected_after_outer_resign() -> None:
    scenarios = [
        {
            "scenario_name": "BASE",
            "rationale": "Explicit reviewed operating forecast.",
            "years": [
                {
                    "year": 2027,
                    "revenue": 2000.0,
                    "ebit_margin": 0.10,
                    "tax_rate": 0.25,
                    "depreciation_amortization": 80.0,
                    "capex": 100.0,
                    "delta_nwc": 50.0,
                }
            ],
        }
    ]
    candidate = build_forecast_candidate(
        scenarios,
        entity_id="DART_CORP:00126380",
        financial_scope="CFS",
        capital_currency="KRW",
        as_of="2026-09-12",
    )
    tampered = copy.deepcopy(candidate)
    tampered["diagnostics"]["BASE"][0]["fcff"] += 1.0
    tampered["candidate_sha256"] = _rehash(tampered, "candidate_sha256")

    with pytest.raises(CaseServiceError, match="diagnostics mismatch|diagnostics 불일치"):
        validate_forecast_candidate(tampered)


def test_v06_policy_weakening_rejected_after_outer_resign() -> None:
    fixtures = _fixture_module()
    proposal = build_binding_proposal_with_forecast(
        fixtures._v05(["BASE"]),
        fixtures._forecast_package(["BASE"]),
    )
    tampered = copy.deepcopy(proposal)
    tampered["policy"]["direct_bind_requires"].remove("ATOMIC_ALL_SIX_APPROVAL")
    tampered["proposal_sha256"] = _rehash(tampered, "proposal_sha256")

    with pytest.raises(CaseServiceError, match="policy/base mismatch|정책·base 불일치"):
        validate_binding_proposal_v6(tampered)


def test_v06_baseline_projection_tamper_rejected_after_outer_resign() -> None:
    fixtures = _fixture_module()
    proposal = build_binding_proposal_with_forecast(
        fixtures._v05(["BASE"]),
        fixtures._forecast_package(["BASE"]),
    )
    tampered = copy.deepcopy(proposal)
    tampered["baseline_context"]["integrated_forecast_assumption"]["value"][0]["years"][0]["revenue"] += 1.0
    tampered["proposal_sha256"] = _rehash(tampered, "proposal_sha256")

    with pytest.raises(CaseServiceError, match="baseline projection mismatch|baseline 투영 불일치"):
        validate_binding_proposal_v6(tampered)
