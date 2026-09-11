"""User-supplied draft-case service / 사용자 제공 Draft 사례 서비스.

Drafts are intentionally separate from canonical cases. They are validated and
executed in memory through shared kernels, but never registered, promoted, or
written into canonical analysis directories by this module.

Draft는 정식 사례와 의도적으로 분리된다. 공통 커널을 통해 메모리에서 검증·실행하지만
본 모듈은 Draft를 정식 레지스트리에 등록·승격하거나 정식 분석 디렉터리에 기록하지 않는다.
"""

from __future__ import annotations

import copy
import json
from math import isfinite
from pathlib import Path
from typing import Any

from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.scenario import ForecastYear, ScenarioDefinition, run_fcff_scenario
from valuation_hub.venture import VentureScenario, probability_weighted_venture_value

DRAFT_SCHEMA_VERSION = "draft-case-v0.1"
DRAFT_STATUS = "DRAFT_USER_SUPPLIED"
MAX_SCENARIOS = 12
MAX_FORECAST_YEARS = 30


def _finite(value: Any, name: str, *, minimum: float | None = None, maximum: float | None = None, exclusive_minimum: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
        raise CaseServiceError(f"{name} must be a finite number / {name}는 유한 숫자여야 합니다")
    number = float(value)
    if minimum is not None and (number <= minimum if exclusive_minimum else number < minimum):
        op = ">" if exclusive_minimum else ">="
        raise CaseServiceError(f"{name} must be {op} {minimum} / {name} 범위 오류")
    if maximum is not None and number > maximum:
        raise CaseServiceError(f"{name} must be <= {maximum} / {name} 범위 오류")
    return number


def _draft_header(payload: dict[str, Any]) -> tuple[str, str, float]:
    if not isinstance(payload, dict):
        raise CaseServiceError("draft must be a JSON object / Draft는 JSON 객체여야 합니다")
    if payload.get("schema_version") != DRAFT_SCHEMA_VERSION:
        raise CaseServiceError(f"unsupported draft schema / 미지원 Draft 스키마: {payload.get('schema_version')}")
    if payload.get("status") != DRAFT_STATUS:
        raise CaseServiceError(f"draft status must be {DRAFT_STATUS} / Draft 상태 오류")
    model = payload.get("model")
    if model not in {"equity_fcff", "venture_probability"}:
        raise CaseServiceError(f"unsupported draft model / 미지원 Draft 모델: {model}")
    name = payload.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 160:
        raise CaseServiceError("draft name is required and must be <=160 chars / Draft 이름 오류")
    currency = payload.get("currency")
    if not isinstance(currency, str) or not 3 <= len(currency) <= 8:
        raise CaseServiceError("currency must be a short string / 통화 코드 오류")
    market = _finite(payload.get("market_price"), "market_price", minimum=0)
    return str(model), currency, market


def _validate_equity(payload: dict[str, Any]) -> dict[str, Any]:
    equity = payload.get("equity")
    if not isinstance(equity, dict):
        raise CaseServiceError("equity object required / equity 객체가 필요합니다")
    diluted_shares = _finite(equity.get("diluted_shares"), "diluted_shares", minimum=0, exclusive_minimum=True)
    debt = _finite(equity.get("debt", 0), "debt", minimum=0)
    cash = _finite(equity.get("cash", 0), "cash", minimum=0)
    minority = _finite(equity.get("minority_interest", 0), "minority_interest", minimum=0)
    scenarios = equity.get("scenarios")
    if not isinstance(scenarios, dict) or not scenarios or len(scenarios) > MAX_SCENARIOS:
        raise CaseServiceError("equity.scenarios must contain 1..12 scenarios / equity.scenarios 개수 오류")

    normalized: dict[str, Any] = {}
    for raw_name, scenario in scenarios.items():
        name = str(raw_name).strip().upper()
        if not name or not isinstance(scenario, dict):
            raise CaseServiceError("scenario name/object invalid / 시나리오 이름·객체 오류")
        wacc = _finite(scenario.get("wacc"), f"{name}.wacc", minimum=0, maximum=0.99, exclusive_minimum=True)
        growth = _finite(scenario.get("terminal_growth"), f"{name}.terminal_growth")
        if growth >= wacc:
            raise CaseServiceError(f"{name}: terminal growth must be lower than WACC / 영구성장률은 WACC보다 낮아야 합니다")
        years = scenario.get("years")
        if not isinstance(years, list) or not 1 <= len(years) <= MAX_FORECAST_YEARS:
            raise CaseServiceError(f"{name}.years must contain 1..{MAX_FORECAST_YEARS} rows / 전망연도 개수 오류")
        seen: set[int] = set()
        rows: list[dict[str, Any]] = []
        for index, row in enumerate(years):
            if not isinstance(row, dict):
                raise CaseServiceError(f"{name}.years[{index}] must be an object / 연도행 객체 오류")
            year = row.get("year")
            if isinstance(year, bool) or not isinstance(year, int) or year in seen:
                raise CaseServiceError(f"{name}: forecast years must be unique integers / 전망연도는 고유 정수여야 합니다")
            seen.add(year)
            revenue = _finite(row.get("revenue"), f"{name}.{year}.revenue", minimum=0)
            margin = _finite(row.get("ebit_margin"), f"{name}.{year}.ebit_margin", minimum=-1, maximum=1)
            tax = _finite(row.get("tax_rate"), f"{name}.{year}.tax_rate", minimum=0, maximum=0.99)
            da = _finite(row.get("depreciation_amortization"), f"{name}.{year}.depreciation_amortization")
            capex = _finite(row.get("capex"), f"{name}.{year}.capex", minimum=0)
            delta_nwc = _finite(row.get("delta_nwc"), f"{name}.{year}.delta_nwc")
            rows.append({"year": year, "revenue": revenue, "ebit_margin": margin, "tax_rate": tax, "depreciation_amortization": da, "capex": capex, "delta_nwc": delta_nwc})
        if [row["year"] for row in rows] != sorted(row["year"] for row in rows):
            raise CaseServiceError(f"{name}: forecast years must be ascending / 전망연도는 오름차순이어야 합니다")
        normalized[name] = {"wacc": wacc, "terminal_growth": growth, "years": rows}
    return {"diluted_shares": diluted_shares, "debt": debt, "cash": cash, "minority_interest": minority, "scenarios": normalized}


def _validate_venture(payload: dict[str, Any]) -> dict[str, Any]:
    venture = payload.get("venture")
    if not isinstance(venture, dict):
        raise CaseServiceError("venture object required / venture 객체가 필요합니다")
    years = _finite(venture.get("holding_period_years"), "holding_period_years", minimum=0, exclusive_minimum=True)
    scenarios = venture.get("scenarios")
    if not isinstance(scenarios, list) or not 1 <= len(scenarios) <= MAX_SCENARIOS:
        raise CaseServiceError("venture.scenarios must contain 1..12 scenarios / venture.scenarios 개수 오류")
    rows: list[dict[str, Any]] = []
    names: set[str] = set()
    total_probability = 0.0
    for index, row in enumerate(scenarios):
        if not isinstance(row, dict):
            raise CaseServiceError(f"venture.scenarios[{index}] must be an object / 벤처 시나리오 객체 오류")
        name = str(row.get("name", "")).strip().upper()
        if not name or name in names:
            raise CaseServiceError("venture scenario names must be unique / 벤처 시나리오 이름 중복")
        names.add(name)
        probability = _finite(row.get("probability"), f"{name}.probability", minimum=0, maximum=1)
        total_probability += probability
        rows.append({
            "name": name,
            "probability": probability,
            "terminal_revenue": _finite(row.get("terminal_revenue"), f"{name}.terminal_revenue", minimum=0),
            "ev_to_sales": _finite(row.get("ev_to_sales"), f"{name}.ev_to_sales", minimum=0),
            "terminal_net_debt": _finite(row.get("terminal_net_debt"), f"{name}.terminal_net_debt"),
            "diluted_shares": _finite(row.get("diluted_shares"), f"{name}.diluted_shares", minimum=0, exclusive_minimum=True),
            "discount_rate": _finite(row.get("discount_rate"), f"{name}.discount_rate", minimum=0, maximum=0.99),
            "recovery_equity_value": _finite(row.get("recovery_equity_value", 0), f"{name}.recovery_equity_value", minimum=0),
        })
    if abs(total_probability - 1.0) > 1e-9:
        raise CaseServiceError(f"venture probabilities must sum to 1.0 / 벤처 확률합 오류: {total_probability}")
    return {"holding_period_years": years, "scenarios": rows}


def validate_draft(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize a user Draft without promoting it / Draft 검증·정규화."""
    model, currency, market_price = _draft_header(payload)
    normalized: dict[str, Any] = {
        "schema_version": DRAFT_SCHEMA_VERSION,
        "status": DRAFT_STATUS,
        "canonical": False,
        "name": payload["name"].strip(),
        "model": model,
        "currency": currency.upper(),
        "market_price": market_price,
        "notes": str(payload.get("notes", "")),
    }
    if model == "equity_fcff":
        normalized["equity"] = _validate_equity(payload)
    else:
        normalized["venture"] = _validate_venture(payload)
    return normalized


def run_draft(payload: dict[str, Any]) -> dict[str, Any]:
    """Execute a validated Draft through shared kernels / 공통커널 Draft 실행."""
    draft = validate_draft(payload)
    if draft["model"] == "equity_fcff":
        equity = draft["equity"]
        outputs: dict[str, Any] = {}
        for name, scenario in equity["scenarios"].items():
            forecast = [ForecastYear(**row) for row in scenario["years"]]
            definition = ScenarioDefinition(
                name=f"DRAFT_{name}",
                wacc=scenario["wacc"],
                terminal_growth=scenario["terminal_growth"],
                diluted_shares=equity["diluted_shares"],
                debt=equity["debt"],
                cash=equity["cash"],
                minority_interest=equity["minority_interest"],
            )
            result = run_fcff_scenario(definition, forecast)
            outputs[name] = {
                "value_per_share": result.value_per_share,
                "enterprise_value": result.enterprise_value,
                "equity_value": result.equity_value,
                "forecast_fcff": list(result.forecast_fcff),
            }
        runtime: dict[str, Any] = {"scenarios": outputs}
    else:
        venture = draft["venture"]
        scenarios = [VentureScenario(**row) for row in venture["scenarios"]]
        result = probability_weighted_venture_value(scenarios, venture["holding_period_years"])
        runtime = {
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
    return {
        "status": DRAFT_STATUS,
        "canonical": False,
        "grounding": "USER_SUPPLIED_UNVERIFIED",
        "warning_en": "Draft inputs are user-supplied and have not passed the repository evidence-promotion gate.",
        "warning_ko": "Draft 입력은 사용자 제공값이며 저장소 근거승격 게이트를 통과하지 않았습니다.",
        "name": draft["name"],
        "model": draft["model"],
        "currency": draft["currency"],
        "market_price": draft["market_price"],
        "runtime": runtime,
    }


def load_draft_file(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CaseServiceError(f"draft file not found / Draft 파일 없음: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CaseServiceError(f"invalid draft JSON / Draft JSON 오류: {exc}") from exc
    return payload


def template(model: str, root: Path | None = None) -> dict[str, Any]:
    repo = root.resolve() if root else find_repo_root()
    mapping = {"equity_fcff": "draft_equity_fcff.json", "venture_probability": "draft_venture_probability.json"}
    if model not in mapping:
        raise CaseServiceError(f"unsupported draft template model / 미지원 Draft 템플릿 모델: {model}")
    path = repo / "templates" / mapping[model]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CaseServiceError(f"draft template unavailable / Draft 템플릿 오류: {model}") from exc
    return copy.deepcopy(payload)
