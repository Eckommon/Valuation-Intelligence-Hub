"""Interactive read-only analysis services / 인터랙티브 읽기 전용 분석 서비스.

M6 adds evidence browsing and NON-CANONICAL scenario previews. The module reads
versioned case artifacts and routes previews into the existing valuation kernels.
It never writes case files and never promotes preview assumptions.

M6는 근거 탐색과 비정식 시나리오 미리보기를 제공한다. 버전 관리 사례를 읽고
기존 가치평가 커널로 preview를 라우팅하며 사례 파일을 수정하거나 preview 가정을
정식 상태로 승격하지 않는다.
"""

from __future__ import annotations

import json
from math import isfinite
from pathlib import Path
from typing import Any

from valuation_hub.case_service import CaseServiceError, find_repo_root, list_cases, validate_case
from valuation_hub.scenario import ForecastYear, ScenarioDefinition, run_fcff_scenario
from valuation_hub.venture import VentureScenario, probability_weighted_venture_value


MAX_REVENUE_SCALE = 5.0
MAX_ABS_MARGIN_DELTA = 0.10
MAX_ABS_RATIO_DELTA = 0.10


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CaseServiceError(f"required file missing / 필수 파일 누락: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CaseServiceError(f"invalid JSON / JSON 오류: {path}: {exc}") from exc


def _entry(case_id: str, root: Path) -> dict[str, Any]:
    for item in list_cases(root):
        if item["case_id"] == case_id:
            return item
    raise CaseServiceError(f"unknown case / 알 수 없는 사례: {case_id}")


def _case_dir(case_id: str, root: Path) -> tuple[dict[str, Any], Path]:
    entry = _entry(case_id, root)
    path = (root / entry["path"]).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise CaseServiceError("case path escapes repository root / 사례 경로가 저장소 밖입니다") from exc
    return entry, path


def evidence_view(case_id: str, root: Path | None = None) -> dict[str, Any]:
    """Collect canonical evidence claims without changing them / 정식 근거 주장 조회."""
    repo = root.resolve() if root else find_repo_root()
    validation = validate_case(case_id, repo)
    entry, directory = _case_dir(case_id, repo)
    manifest = _read_json(directory / "evidence_manifest.json")

    bundle_names = manifest.get("canonical_bundles") or []
    claims: list[dict[str, Any]] = []
    bundles: list[dict[str, Any]] = []
    for name in bundle_names:
        if not isinstance(name, str) or "/" in name or "\\" in name:
            raise CaseServiceError("invalid evidence bundle path / 근거 묶음 경로 오류")
        payload = _read_json(directory / name)
        if payload.get("case_id") != case_id:
            raise CaseServiceError(f"evidence case_id mismatch / 근거 case_id 불일치: {name}")
        bundle_claims = payload.get("claims", [])
        if not isinstance(bundle_claims, list):
            raise CaseServiceError(f"evidence claims malformed / 근거 claims 오류: {name}")
        claims.extend(bundle_claims)
        bundles.append({"file": name, "bundle": payload.get("bundle"), "claim_count": len(bundle_claims)})

    counts: dict[str, int] = {}
    for claim in claims:
        classification = str(claim.get("class", "UNKNOWN"))
        counts[classification] = counts.get(classification, 0) + 1

    return {
        "case_id": case_id,
        "display_name_en": entry["display_name_en"],
        "display_name_ko": entry["display_name_ko"],
        "promotion_gate": validation["promotion_gate"],
        "evidence_status": manifest.get("status"),
        "bundles": bundles,
        "classification_counts": counts,
        "claims": claims,
        "read_only": True,
    }


def _finite_number(payload: dict[str, Any], name: str, default: float) -> float:
    value = payload.get(name, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
        raise CaseServiceError(f"{name} must be a finite number / {name}는 유한 숫자여야 합니다")
    return float(value)


def _preview_equity(case: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    scenario_name = str(overrides.get("scenario", "BASE")).upper()
    if scenario_name not in ("BEAR", "BASE", "BULL"):
        raise CaseServiceError("scenario must be BEAR/BASE/BULL / 시나리오 값 오류")
    scenario = case["scenarios"][scenario_name]

    wacc = _finite_number(overrides, "wacc", float(scenario["wacc"]))
    terminal_growth = _finite_number(overrides, "terminal_growth", float(scenario["terminal_growth"]))
    revenue_scale = _finite_number(overrides, "revenue_scale", 1.0)
    margin_delta = _finite_number(overrides, "ebit_margin_delta", 0.0)
    capex_delta = _finite_number(overrides, "capex_to_sales_delta", 0.0)
    nwc_delta = _finite_number(overrides, "nwc_to_sales_delta", 0.0)

    if not 0 < wacc < 1:
        raise CaseServiceError("WACC must be in (0,1) / WACC 범위 오류")
    if terminal_growth >= wacc:
        raise CaseServiceError("terminal growth must be lower than WACC / 영구성장률은 WACC보다 낮아야 합니다")
    if not 0 < revenue_scale <= MAX_REVENUE_SCALE:
        raise CaseServiceError(f"revenue_scale must be in (0,{MAX_REVENUE_SCALE}] / 매출 배율 범위 오류")
    if abs(margin_delta) > MAX_ABS_MARGIN_DELTA:
        raise CaseServiceError("EBIT margin delta exceeds sandbox limit / EBIT 마진 변경폭이 한도를 초과합니다")
    if abs(capex_delta) > MAX_ABS_RATIO_DELTA or abs(nwc_delta) > MAX_ABS_RATIO_DELTA:
        raise CaseServiceError("CAPEX/NWC ratio delta exceeds sandbox limit / CAPEX·NWC 변경폭 한도 초과")

    prior_nwc = float(case["opening_core_nwc"]["value"])
    forecast: list[ForecastYear] = []
    preview_rows: list[dict[str, Any]] = []
    for item in scenario["years"]:
        revenue = float(item["revenue"]) * revenue_scale
        margin = float(item["ebit_margin"]) + margin_delta
        capex_ratio = float(item["capex_to_sales"]) + capex_delta
        nwc_ratio = float(item["nwc_to_sales"]) + nwc_delta
        if not -0.5 <= margin <= 0.5:
            raise CaseServiceError("preview EBIT margin outside safe range / preview EBIT 마진 안전범위 초과")
        if capex_ratio < 0 or nwc_ratio < 0:
            raise CaseServiceError("CAPEX/NWC ratios cannot be negative / CAPEX·NWC 비율은 음수 불가")
        current_nwc = revenue * nwc_ratio
        forecast.append(
            ForecastYear(
                year=int(item["year"]),
                revenue=revenue,
                ebit_margin=margin,
                tax_rate=float(item["tax_rate"]),
                depreciation_amortization=revenue * float(item["da_to_sales"]),
                capex=revenue * capex_ratio,
                delta_nwc=current_nwc - prior_nwc,
            )
        )
        preview_rows.append({
            "year": int(item["year"]), "revenue": revenue, "ebit_margin": margin,
            "capex_to_sales": capex_ratio, "nwc_to_sales": nwc_ratio,
        })
        prior_nwc = current_nwc

    definition = ScenarioDefinition(
        name=f"PREVIEW_{scenario_name}",
        wacc=wacc,
        terminal_growth=terminal_growth,
        diluted_shares=float(case["market"]["diluted_shares"]),
        debt=float(scenario["future_net_debt"]),
        cash=0.0,
        minority_interest=float(scenario["future_minority_interest"]),
    )
    result = run_fcff_scenario(definition, forecast)
    return {
        "preview_type": "equity_fcff",
        "source_scenario": scenario_name,
        "value_per_share": result.value_per_share,
        "enterprise_value": result.enterprise_value,
        "equity_value": result.equity_value,
        "forecast_fcff": list(result.forecast_fcff),
        "assumptions": {
            "wacc": wacc, "terminal_growth": terminal_growth, "revenue_scale": revenue_scale,
            "ebit_margin_delta": margin_delta, "capex_to_sales_delta": capex_delta,
            "nwc_to_sales_delta": nwc_delta,
        },
        "forecast_preview": preview_rows,
    }


def _preview_venture(case: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    probabilities = overrides.get("probabilities", {})
    if probabilities is None:
        probabilities = {}
    if not isinstance(probabilities, dict):
        raise CaseServiceError("probabilities must be an object / probabilities는 객체여야 합니다")
    revenue_scale = _finite_number(overrides, "revenue_scale", 1.0)
    multiple_scale = _finite_number(overrides, "multiple_scale", 1.0)
    dilution_scale = _finite_number(overrides, "dilution_scale", 1.0)
    if not 0 < revenue_scale <= 5 or not 0 < multiple_scale <= 3 or not 0.25 <= dilution_scale <= 4:
        raise CaseServiceError("venture preview scale outside safe range / 벤처 preview 배율 안전범위 초과")

    scenarios: list[VentureScenario] = []
    resolved_probabilities: dict[str, float] = {}
    for item in case["scenarios"]:
        name = str(item["name"])
        probability = probabilities.get(name, item["probability"])
        if isinstance(probability, bool) or not isinstance(probability, (int, float)) or not isfinite(float(probability)):
            raise CaseServiceError(f"invalid probability / 확률 오류: {name}")
        p = float(probability)
        resolved_probabilities[name] = p
        scenarios.append(
            VentureScenario(
                name=name,
                probability=p,
                terminal_revenue=float(item["terminal_revenue"]) * revenue_scale,
                ev_to_sales=float(item["ev_to_sales"]) * multiple_scale,
                terminal_net_debt=float(item["terminal_net_debt"]),
                diluted_shares=float(item["diluted_shares"]) * dilution_scale,
                discount_rate=float(item["discount_rate"]),
                recovery_equity_value=float(item.get("recovery_equity_value", 0.0)),
            )
        )
    try:
        result = probability_weighted_venture_value(scenarios, float(case["holding_period_years"]))
    except ValueError as exc:
        raise CaseServiceError(f"venture preview invalid / 벤처 preview 오류: {exc}") from exc
    return {
        "preview_type": "venture_probability",
        "expected_present_value_per_share": result.expected_present_value_per_share,
        "assumptions": {
            "probabilities": resolved_probabilities, "revenue_scale": revenue_scale,
            "multiple_scale": multiple_scale, "dilution_scale": dilution_scale,
        },
        "scenarios": {
            r.name: {
                "probability": r.probability,
                "terminal_value_per_share": r.terminal_value_per_share,
                "present_value_per_share": r.present_value_per_share,
                "weighted_present_value_per_share": r.probability_weighted_present_value_per_share,
            }
            for r in result.scenario_results
        },
    }


def preview_case(case_id: str, overrides: dict[str, Any], root: Path | None = None) -> dict[str, Any]:
    """Run non-persistent preview through shared kernels / 공통커널 비영구 preview 실행."""
    if not isinstance(overrides, dict):
        raise CaseServiceError("preview payload must be an object / preview payload는 객체여야 합니다")
    repo = root.resolve() if root else find_repo_root()
    validation = validate_case(case_id, repo)
    entry, directory = _case_dir(case_id, repo)
    case = _read_json(directory / "case_inputs.json")
    if entry["model"] == "equity_fcff":
        preview = _preview_equity(case, overrides)
    elif entry["model"] == "venture_probability":
        preview = _preview_venture(case, overrides)
    else:
        raise CaseServiceError(f"preview unsupported model / preview 미지원 모델: {entry['model']}")
    return {
        "case_id": case_id,
        "canonical": False,
        "status": "PREVIEW_NOT_CANONICAL",
        "promotion_gate": validation["promotion_gate"],
        "model": entry["model"],
        "valuation_as_of": case["valuation_as_of"],
        "market_price": case["market"]["price"],
        "preview": preview,
    }
