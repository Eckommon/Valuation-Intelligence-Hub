"""Executable case service layer / 실행형 사례 서비스 계층.

The service supports legacy reference cases and explicitly versioned reviewed-Draft
canonical adapters. Interface consumers receive a stable external runtime shape;
valuation formulas remain in the shared FCFF/Venture kernels.
"""

from __future__ import annotations

import json
from numbers import Real
from pathlib import Path
from typing import Any

from valuation_hub.reviewed_adapter import (
    REVIEWED_ADAPTER_TO_MODEL,
    REVIEWED_ADMISSION_GATE,
    normalize_reviewed_runtime,
)
from valuation_hub.scenario import ForecastYear, ScenarioDefinition, run_fcff_scenario
from valuation_hub.venture import VentureScenario, probability_weighted_venture_value

SUPPORTED_MODELS = {"equity_fcff", "venture_probability"}
PASS_GATES = {
    "PASS_MATERIAL_INPUTS_RECONCILED",
    "PASS_VENTURE_MODEL_INPUTS_RECONCILED",
    REVIEWED_ADMISSION_GATE,
}
DEFAULT_DRIFT_TOLERANCE = {
    "equity_fcff": 1.0,
    "venture_probability": 1e-6,
}


class CaseServiceError(RuntimeError):
    """Fail-closed case execution error / fail-closed 사례 실행 오류."""


def find_repo_root(start: Path | None = None) -> Path:
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
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CaseServiceError(f"required file missing / 필수 파일 누락: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CaseServiceError(f"invalid JSON / JSON 오류: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise CaseServiceError(f"JSON object required / JSON 객체 필요: {path}")
    return payload


def load_registry(root: Path | None = None) -> dict[str, Any]:
    repo = root.resolve() if root else find_repo_root()
    registry = _read_json(repo / "registry" / "cases.json")
    cases = registry.get("cases")
    if not isinstance(cases, list) or not cases:
        raise CaseServiceError("case registry is empty or malformed / 사례 레지스트리 오류")
    ids = [item.get("case_id") if isinstance(item, dict) else None for item in cases]
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        raise CaseServiceError("case registry has missing/duplicate IDs / 사례 ID 누락·중복")
    return registry


def list_cases(root: Path | None = None) -> list[dict[str, Any]]:
    return list(load_registry(root)["cases"])


def _case_entry(case_id: str, root: Path) -> dict[str, Any]:
    for entry in load_registry(root)["cases"]:
        if entry["case_id"] == case_id:
            model = entry.get("model")
            if model not in SUPPORTED_MODELS:
                raise CaseServiceError(f"unsupported model / 미지원 모델: {model}")
            adapter = entry.get("adapter")
            if adapter is not None:
                expected_model = REVIEWED_ADAPTER_TO_MODEL.get(str(adapter))
                if expected_model is None:
                    raise CaseServiceError(f"unsupported adapter / 미지원 adapter: {adapter}")
                if expected_model != model:
                    raise CaseServiceError(
                        f"adapter/model mismatch / adapter·model 불일치: {adapter} -> {expected_model}, registry={model}"
                    )
            return entry
    raise CaseServiceError(f"unknown case / 알 수 없는 사례: {case_id}")


def _case_dir(entry: dict[str, Any], root: Path) -> Path:
    raw_path = entry.get("path")
    if not isinstance(raw_path, str) or not raw_path:
        raise CaseServiceError("case path missing / 사례 경로 누락")
    path = (root / raw_path).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise CaseServiceError("case path escapes repository root / 사례 경로가 저장소 밖을 가리킵니다") from exc
    return path


def _validate_reviewed_case(
    case_id: str,
    entry: dict[str, Any],
    directory: Path,
    inputs: dict[str, Any],
    manifest: dict[str, Any],
    stored: dict[str, Any],
) -> None:
    adapter = str(entry["adapter"])
    model = str(entry["model"])
    if inputs.get("model_version") != adapter or stored.get("model_version") != adapter:
        raise CaseServiceError("reviewed adapter model_version mismatch / 검토 adapter model_version 불일치")
    if inputs.get("canonical") is not True or manifest.get("canonical") is not True or stored.get("canonical") is not True:
        raise CaseServiceError("reviewed canonical files must declare canonical=true / 검토 정식 파일 canonical=true 필요")
    if manifest.get("promotion_gate") != REVIEWED_ADMISSION_GATE:
        raise CaseServiceError("reviewed admission gate mismatch / 검토 Draft 수용게이트 불일치")

    source_path = directory / "SOURCE_PACKAGE.json"
    if not source_path.is_file():
        raise CaseServiceError("SOURCE_PACKAGE.json required for reviewed adapter / 검토 adapter는 SOURCE_PACKAGE.json 필수")
    source_package = _read_json(source_path)

    # Runtime-local imports avoid module initialization cycles because promotion_package
    # itself imports CaseServiceError/find_repo_root from this module.
    from valuation_hub.promotion_package import validate_promotion_package

    package_validation = validate_promotion_package(source_package, directory.parents[2], check_collision=False)
    if source_package.get("case_identity", {}).get("case_id") != case_id:
        raise CaseServiceError("source package case_id mismatch / 원천 패키지 case_id 불일치")
    if package_validation.get("required_canonical_adapter") != adapter:
        raise CaseServiceError("source package adapter mismatch / 원천 패키지 adapter 불일치")
    package_sha = source_package.get("package_sha256")
    candidate_sha = source_package.get("source_review", {}).get("candidate_sha256")
    review_sha = source_package.get("source_review", {}).get("review_scope_sha256")
    for label, payload in (("inputs", inputs), ("manifest", manifest), ("result", stored)):
        if payload.get("source_package_sha256") != package_sha:
            raise CaseServiceError(f"source package SHA mismatch in {label} / {label} 원천 패키지 SHA 불일치")
        if payload.get("source_candidate_sha256") != candidate_sha:
            raise CaseServiceError(f"candidate SHA mismatch in {label} / {label} Candidate SHA 불일치")
        if payload.get("review_scope_sha256") != review_sha:
            raise CaseServiceError(f"review scope SHA mismatch in {label} / {label} 검토범위 SHA 불일치")

    draft = inputs.get("reviewed_draft")
    if not isinstance(draft, dict):
        raise CaseServiceError("reviewed_draft missing / reviewed_draft 누락")
    normalized, _, _ = normalize_reviewed_runtime(draft)
    if normalized != draft:
        raise CaseServiceError("reviewed_draft normalization drift / reviewed_draft 정규화 drift")
    if draft.get("model") != model:
        raise CaseServiceError("reviewed_draft model mismatch / reviewed_draft 모델 불일치")
    packaged_draft = source_package.get("artifacts", {}).get("reviewed_candidate.json", {}).get("draft")
    if draft != packaged_draft:
        raise CaseServiceError("canonical reviewed_draft differs from approved package / 정식 reviewed_draft가 승인 패키지와 다름")
    valuation_as_of = inputs.get("valuation_as_of")
    if manifest.get("valuation_as_of") != valuation_as_of or stored.get("valuation_as_of") != valuation_as_of:
        raise CaseServiceError("valuation_as_of drift across canonical files / 정식 파일 간 기준일 불일치")
    if inputs.get("currency") != draft.get("currency") or stored.get("currency") != draft.get("currency"):
        raise CaseServiceError("currency drift from reviewed Draft / 검토 Draft 통화 불일치")


def validate_case(case_id: str, root: Path | None = None) -> dict[str, Any]:
    """Validate execution contract without silently filling inputs / 입력 자동보완 없이 사례 검증."""
    repo = root.resolve() if root else find_repo_root()
    entry = _case_entry(case_id, repo)
    directory = _case_dir(entry, repo)
    required = ["case_inputs.json", "evidence_manifest.json", "valuation_result.json", "REPORT.md"]
    if entry.get("adapter") is not None:
        required.extend(["SOURCE_PACKAGE.json", "evidence_reviewed.json"])
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
    adapter = entry.get("adapter")
    if adapter is None:
        expected_prefix = "reference-equity-fcff" if model == "equity_fcff" else "reference-venture-probability"
        if not str(inputs.get("model_version", "")).startswith(expected_prefix):
            raise CaseServiceError("model version does not match registry route / 모델 버전-라우터 불일치")
    else:
        _validate_reviewed_case(case_id, entry, directory, inputs, manifest, stored)

    return {
        "case_id": case_id,
        "valid": True,
        "model": model,
        "adapter": adapter,
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


def _tolerance(model: str, tolerance: float | None) -> float:
    allowed = DEFAULT_DRIFT_TOLERANCE[model] if tolerance is None else tolerance
    if allowed < 0:
        raise CaseServiceError("drift tolerance cannot be negative / 허용오차는 음수일 수 없습니다")
    return allowed


def _verify_against_stored(model: str, runtime: dict[str, Any], stored: dict[str, Any], tolerance: float | None) -> None:
    allowed = _tolerance(model, tolerance)
    if model == "equity_fcff":
        for name in ("BEAR", "BASE", "BULL"):
            expected = float(stored["scenario_results"][name]["current_intrinsic_value_per_share"])
            actual = float(runtime[name]["value_per_share"])
            if abs(actual - expected) > allowed:
                raise CaseServiceError(
                    f"runtime/stored drift for {name}: {actual} vs {expected}; 실행값과 정식 저장값 불일치"
                )
    else:
        expected = float(stored["probability_weighted"]["expected_present_value_per_share"])
        actual = float(runtime["expected_present_value_per_share"])
        if abs(actual - expected) > allowed:
            raise CaseServiceError(f"runtime/stored drift: {actual} vs {expected}; 실행값과 정식 저장값 불일치")


def _compare_runtime(actual: Any, expected: Any, allowed: float, path: str = "runtime") -> None:
    if isinstance(actual, bool) or isinstance(expected, bool):
        if actual != expected:
            raise CaseServiceError(f"reviewed runtime drift at {path} / 검토 runtime drift")
        return
    if isinstance(actual, Real) and isinstance(expected, Real):
        if abs(float(actual) - float(expected)) > allowed:
            raise CaseServiceError(
                f"reviewed runtime drift at {path}: {actual} vs {expected} / 검토 runtime 불일치"
            )
        return
    if isinstance(actual, dict) and isinstance(expected, dict):
        if set(actual) != set(expected):
            raise CaseServiceError(f"reviewed runtime keys drift at {path} / 검토 runtime 키 불일치")
        for key in actual:
            _compare_runtime(actual[key], expected[key], allowed, f"{path}.{key}")
        return
    if isinstance(actual, list) and isinstance(expected, list):
        if len(actual) != len(expected):
            raise CaseServiceError(f"reviewed runtime length drift at {path} / 검토 runtime 길이 불일치")
        for index, (left, right) in enumerate(zip(actual, expected)):
            _compare_runtime(left, right, allowed, f"{path}[{index}]")
        return
    if actual != expected:
        raise CaseServiceError(f"reviewed runtime drift at {path} / 검토 runtime 불일치")


def _verify_reviewed_against_stored(model: str, runtime: dict[str, Any], stored: dict[str, Any], tolerance: float | None) -> None:
    expected = stored.get("runtime")
    if not isinstance(expected, dict):
        raise CaseServiceError("stored reviewed runtime missing / 저장된 검토 runtime 누락")
    _compare_runtime(runtime, expected, _tolerance(model, tolerance))


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
    adapter = entry.get("adapter")
    if adapter is None:
        runtime = _run_equity(case) if entry["model"] == "equity_fcff" else _run_venture(case)
        _verify_against_stored(entry["model"], runtime, stored, tolerance)
        market_price = case["market"]["price"]
    else:
        _, _, runtime = normalize_reviewed_runtime(case["reviewed_draft"])
        _verify_reviewed_against_stored(entry["model"], runtime, stored, tolerance)
        market_price = case["reviewed_draft"]["market_price"]
    return {
        "case_id": case_id,
        "model": entry["model"],
        "adapter": adapter,
        "model_version": case["model_version"],
        "valuation_as_of": case["valuation_as_of"],
        "market_price": market_price,
        "grounded": True,
        "promotion_gate": validation["promotion_gate"],
        "drift_tolerance": DEFAULT_DRIFT_TOLERANCE[entry["model"]] if tolerance is None else tolerance,
        "runtime": runtime,
    }


def read_report(case_id: str, root: Path | None = None) -> str:
    repo = root.resolve() if root else find_repo_root()
    entry = _case_entry(case_id, repo)
    validate_case(case_id, repo)
    return (_case_dir(entry, repo) / "REPORT.md").read_text(encoding="utf-8")
