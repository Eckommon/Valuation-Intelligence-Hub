"""Executable case service layer / 실행형 사례 서비스 계층.

This module is the shared application-service boundary for CLI, future Web UI,
and future API adapters. It routes versioned case files into already-tested
valuation kernels; it must not reimplement valuation formulas.

본 모듈은 CLI, 향후 Web UI, API가 공유하는 애플리케이션 서비스 경계다.
버전 관리 사례 파일을 기존 검증 가치평가 커널로 라우팅하며 계산공식을
재구현해서는 안 된다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from valuation_hub.scenario import ForecastYear, ScenarioDefinition, run_fcff_scenario
from valuation_hub.venture import VentureScenario, probability_weighted_venture_value


SUPPORTED_MODELS = {"equity_fcff", "venture_probability"}
PASS_GATES = {"PASS_MATERIAL_INPUTS_RECONCILED", "PASS_VENTURE_MODEL_INPUTS_RECONCILED"}
DEFAULT_DRIFT_TOLERANCE = {
    "equity_fcff": 1.0,           # one currency unit/share; e.g. KRW 1
    "venture_probability": 1e-6, # sub-cent precision for USD option-like cases
}


class CaseServiceError(RuntimeError):
    """Fail-closed case execution error / fail-closed 사례 실행 오류."""


def find_repo_root(start: Path | None = None) -> Path:
    """Find repository root by versioned case registry / 사례 레지스트리로 저장소 루트 탐색."""
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "registry" / "cases.json").is_file():
            return candidate
    raise CaseServiceError(
        "repository root not found: registry/cases.json is required; "
        "저장소 루트를 찾지 못했습니다: registry/cases.json이 필요합니다."
    )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CaseServiceError(f"required file missing / 필수 파일 누락: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CaseServiceError(f"invalid JSON / JSON 오류: {path}: {exc}") from exc


def load_registry(root: Path | None = None) -> dict[str, Any]:
    repo = root.resolve() if root else find_repo_root()
    registry = _read_json(repo / "registry" / "cases.json")
    cases = registry.get("cases")
    if not isinstance(cases, list) or not cases:
        raise CaseServiceError("case registry is empty or malformed / 사례 레지스트리 오류")
    ids = [item.get("case_id") for item in cases]
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        raise CaseServiceError("case registry has missing/duplicate IDs / 사례 ID 누락·중복")
    return registry


def list_cases(root: Path | None = None) -> list[dict[str, Any]]:
    return list(load_registry(root)["cases"])


def _case_entry(case_id: str, root: Path) -> dict[str, Any]:
    for entry in load_registry(root)["cases"]:
        if entry["case_id"] == case_id:
            if entry.get("model") not in SUPPORTED_MODELS:
                raise CaseServiceError(f"unsupported model / 미지원 모델: {entry.get('model')}")
            return entry
    raise CaseServiceError(f"unknown case / 알 수 없는 사례: {case_id}")


def _case_dir(entry: dict[str, Any], root: Path) -> Path:
    path = (root / entry["path"]).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise CaseServiceError("case path escapes repository root / 사례 경로가 저장소 밖을 가리킵니다") from exc
    return path


def validate_case(case_id: str, root: Path | None = None) -> dict[str, Any]:
    """Validate execution contract without silently filling inputs / 입력 자동보완 없이 사례 검증."""
    repo = root.resolve() if root else find_repo_root()
    entry = _case_entry(case_id, repo)
    directory = _case_dir(entry, repo)
    required = ["case_inputs.json", "evidence_manifest.json", "valuation_result.json", "REPORT.md"]
    missing = [name for name in required if not (directory / name).is_file()]
    if missing:
        raise CaseServiceError(f"missing case files / 사례 파일 누락: {', '.join(missing)}")

    inputs = _read_json(directory / "case_inputs.json")
    manifest = _read_json(directory / "evidence_manifest.json")
    stored = _read_json(directory / "valuation_result.json")
    for label, payload in (("inputs", inputs), ("manifest", manifest), ("result", stored)):
        if payload.get("case_id") != case_id:
            raise CaseServiceError(f"case_id mismatch in {label} / {label}의 case_id 불일치")

    gate = manifest.get("promotion_gate")
    if gate not in PASS_GATES:
        raise CaseServiceError(f"evidence gate is not PASS / 근거 게이트 미통과: {gate}")
    model = entry["model"]
    expected_prefix = "reference-equity-fcff" if model == "equity_fcff" else "reference-venture-probability"
    if not str(inputs.get("model_version", "")).startswith(expected_prefix):
        raise CaseServiceError("model version does not match registry route / 모델 버전-라우터 불일치")

    return {
        "case_id": case_id,
        "valid": True,
        "model": model,
        "promotion_gate": gate,
        "model_version": inputs["model_version"],
        "path": entry["path"],
    }


def _equity_forecast(case: dict[str, Any], scenario_name: str) -> list[ForecastYear]:
    scenario = case["scenarios"][scenario_name]
    prior_nwc = case["opening_core_nwc"]["value"]
    rows: list[ForecastYear] = []
    for item in scenario["years"]:
        revenue = item["revenue"]
        current_nwc = revenue * item["nwc_to_sales"]
        rows.append(
            ForecastYear(
                year=item["year"],
                revenue=revenue,
                ebit_margin=item["ebit_margin"],
                tax_rate=item["tax_rate"],
                depreciation_amortization=revenue * item["da_to_sales"],
                capex=revenue * item["capex_to_sales"],
                delta_nwc=current_nwc - prior_nwc,
            )
        )
        prior_nwc = current_nwc
    return rows


def _run_equity(case: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for name in ("BEAR", "BASE", "BULL"):
        scenario = case["scenarios"][name]
        definition = ScenarioDefinition(
            name=name,
            wacc=scenario["wacc"],
            terminal_growth=scenario["terminal_growth"],
            diluted_shares=case["market"]["diluted_shares"],
            debt=scenario["future_net_debt"],
            cash=0.0,
            minority_interest=scenario["future_minority_interest"],
        )
        result = run_fcff_scenario(definition, _equity_forecast(case, name))
        output[name] = {
            "value_per_share": result.value_per_share,
            "enterprise_value": result.enterprise_value,
            "equity_value": result.equity_value,
            "forecast_fcff": list(result.forecast_fcff),
        }
    return output


def _run_venture(case: dict[str, Any]) -> dict[str, Any]:
    scenarios = [
        VentureScenario(
            name=item["name"],
            probability=item["probability"],
            terminal_revenue=item["terminal_revenue"],
            ev_to_sales=item["ev_to_sales"],
            terminal_net_debt=item["terminal_net_debt"],
            diluted_shares=item["diluted_shares"],
            discount_rate=item["discount_rate"],
            recovery_equity_value=item.get("recovery_equity_value", 0.0),
        )
        for item in case["scenarios"]
    ]
    result = probability_weighted_venture_value(scenarios, case["holding_period_years"])
    return {
        "expected_present_value_per_share": result.expected_present_value_per_share,
        "scenarios": {
            item.name: {
                "probability": item.probability,
                "terminal_value_per_share": item.terminal_value_per_share,
                "present_value_per_share": item.present_value_per_share,
                "weighted_present_value_per_share": item.probability_weighted_present_value_per_share,
            }
            for item in result.scenario_results
        },
    }


def _verify_against_stored(
    model: str,
    runtime: dict[str, Any],
    stored: dict[str, Any],
    tolerance: float | None,
) -> None:
    allowed = DEFAULT_DRIFT_TOLERANCE[model] if tolerance is None else tolerance
    if allowed < 0:
        raise CaseServiceError("drift tolerance cannot be negative / 허용오차는 음수일 수 없습니다")

    if model == "equity_fcff":
        for name in ("BEAR", "BASE", "BULL"):
            expected = float(stored["scenario_results"][name]["current_intrinsic_value_per_share"])
            actual = float(runtime[name]["value_per_share"])
            if abs(actual - expected) > allowed:
                raise CaseServiceError(
                    f"runtime/stored drift for {name}: {actual} vs {expected}; "
                    "실행값과 정식 저장값 불일치"
                )
    else:
        expected = float(stored["probability_weighted"]["expected_present_value_per_share"])
        actual = float(runtime["expected_present_value_per_share"])
        if abs(actual - expected) > allowed:
            raise CaseServiceError(
                f"runtime/stored drift: {actual} vs {expected}; 실행값과 정식 저장값 불일치"
            )


def run_case(
    case_id: str,
    root: Path | None = None,
    *,
    tolerance: float | None = None,
) -> dict[str, Any]:
    """Validate, route, execute, and ground against stored canonical result."""
    repo = root.resolve() if root else find_repo_root()
    validation = validate_case(case_id, repo)
    entry = _case_entry(case_id, repo)
    directory = _case_dir(entry, repo)
    case = _read_json(directory / "case_inputs.json")
    stored = _read_json(directory / "valuation_result.json")
    runtime = _run_equity(case) if entry["model"] == "equity_fcff" else _run_venture(case)
    _verify_against_stored(entry["model"], runtime, stored, tolerance)
    return {
        "case_id": case_id,
        "model": entry["model"],
        "model_version": case["model_version"],
        "valuation_as_of": case["valuation_as_of"],
        "market_price": case["market"]["price"],
        "grounded": True,
        "promotion_gate": validation["promotion_gate"],
        "drift_tolerance": DEFAULT_DRIFT_TOLERANCE[entry["model"]] if tolerance is None else tolerance,
        "runtime": runtime,
    }


def read_report(case_id: str, root: Path | None = None) -> str:
    repo = root.resolve() if root else find_repo_root()
    entry = _case_entry(case_id, repo)
    validate_case(case_id, repo)
    path = _case_dir(entry, repo) / "REPORT.md"
    return path.read_text(encoding="utf-8")
