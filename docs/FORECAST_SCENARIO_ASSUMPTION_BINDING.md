# Integrated Forecast Scenario Assumption Binding / 통합 Forecast 시나리오 가정 바인딩

## Purpose / 목적

M26 governs the six explicit FCFF forecast-year inputs as one coherent valuation-assumption block and connects only a human-reviewed block to the Draft-binding path.

M26는 명시기간 FCFF를 구성하는 여섯 미래 입력을 하나의 일관된 가치평가 가정 블록으로 거버넌스하고, 인간 검토를 통과한 블록만 Draft 바인딩 경로에 연결한다.

## Authority boundary / 권위 경계

```text
historical fact != forecast assumption
historical trend != automatic forecast
calculated EBIT/NOPAT/FCFF != forecast authority
ASSUMPTION_CANDIDATE != ASSUMPTION
reviewed ASSUMPTION != canonical state
```

Forecast diagnostics are deterministic calculations for review. They never convert a forecast row into a fact.

Forecast 진단값은 검토를 위한 결정론적 계산이며 Forecast 행을 사실로 승격시키지 않는다.

## Atomic forecast block / 원자적 Forecast 블록

M26 governs exactly these six existing material fields together:

```text
scenario.years.revenue
scenario.years.ebit_margin
scenario.years.tax_rate
scenario.years.depreciation_amortization
scenario.years.capex
scenario.years.delta_nwc
```

Approval is **all-six-or-none**. Partial approval or partial application fails closed.

승인은 **6개 전부 또는 전혀 없음** 방식이다. 부분 승인·부분 적용은 fail-closed한다.

## Candidate / Candidate

`forecast-scenario-assumption-candidate-v0.1` requires:

- explicit unique scenario names / 명시적 고유 시나리오명
- explicit rationale for every scenario / 시나리오별 명시적 rationale
- one common, strictly ascending forecast-year set / 모든 시나리오가 공유하는 오름차순 Forecast 연도집합
- every year strictly after the valuation `as_of` year / 모든 Forecast 연도는 가치평가 기준연도 이후
- complete six-component rows / 6개 구성요소 완전행
- one entity, financial scope, capital currency, and valuation `as_of`

Numeric gates:

```text
revenue >= 0
-1 <= ebit_margin <= 1
0 <= tax_rate < 1
D&A >= 0
CAPEX >= 0
ΔNWC = finite number; negative allowed
```

The candidate remains:

```text
class = ASSUMPTION_CANDIDATE
canonical = false
```

## Diagnostics / 진단

For every scenario/year M26 independently recomputes:

```text
EBIT  = revenue × ebit_margin
NOPAT = EBIT × (1 - tax_rate)
FCFF  = EBIT(1-T) + D&A - CAPEX - ΔNWC
```

Revenue growth is also reported where a prior forecast year exists. Diagnostic tampering is detected even if an outer candidate SHA is recomputed.

이 진단값은 authority가 아니라 검토 보조값이며, outer SHA를 다시 계산해도 진단값 변조를 허용하지 않는다.

## Human review / 인간 검토

`forecast-scenario-review-assertion-v0.1` locks:

- exact candidate SHA
- exact forecast-block SHA
- methodology version
- entity / scope / currency / `as_of`
- exact scenario set
- exact common forecast-year set
- reviewer
- timezone-aware approval timestamp
- review basis

Approval cannot predate valuation `as_of`.

승인시각은 가치평가 `as_of`보다 앞설 수 없다.

Finalization yields:

```text
reviewed-forecast-scenario-assumption-v0.1
class = ASSUMPTION
binding_eligibility = REVIEWED_INTEGRATED_FORECAST_ASSUMPTION
canonical = false
```

The full candidate and review assertion remain embedded and independently revalidated.

## v0.6 binding / v0.6 바인딩

```text
validated draft-binding-proposal-v0.5
        +
reviewed integrated forecast ASSUMPTION
        ↓
draft-binding-proposal-v0.6
```

M26 accepts **only** a validated v0.5 base proposal. The forecast scenario set must exactly equal the terminal-growth scenario set already governed in v0.5.

M26은 검증된 v0.5만 base로 허용한다. Forecast 시나리오 집합은 v0.5에서 이미 거버넌스된 영구성장률 시나리오 집합과 정확히 같아야 한다.

v0.6 may replace only the six forecast-year material decisions. WACC, terminal growth, cash, debt, diluted shares, conflicts, and all other base decisions must remain equivalent to the embedded v0.5 proposal.

## Apply-time compatibility / 적용시점 호환성

Before approval/application, the target Draft must already contain:

- the exact same scenario set
- the exact same ordered forecast-year set in every scenario

M26 v0.1 does not create, delete, or reorder Draft scenario rows.

M26 v0.1은 Draft 시나리오 행을 생성·삭제·재정렬하지 않는다.

For every approved forecast component, the applied diff records scenario/year before→after values plus:

```text
source_forecast_package_sha256
forecast_block_sha256
review_assertion_sha256
scenario_names
forecast_years
forecast_component
```

The original Draft object remains unchanged; the output remains noncanonical.

## Result-integrity hardening / 결과 무결성 강화

M26 adds a generic bound-result invariant:

```text
set(applied_diff.field) == set(approved_fields)
AND every applied_diff.field is unique
```

This blocks a re-signed result from repeating one valid diff while omitting another approved field. The hardening was regression-tested with a deliberate red→green exploit fixture.

이를 통해 하나의 유효 diff를 반복하고 다른 승인필드의 실제 적용을 누락한 뒤 outer SHA를 재봉인하는 변조를 차단한다.

## Interfaces / 인터페이스

CLI is additive through `cli_entry_m26`. Older M1–M25 commands delegate unchanged.

M26 commands:

```text
forecast-candidate-build
forecast-candidate-validate
forecast-review-build
forecast-review-validate
forecast-finalize
forecast-validate
binding-build-with-forecast
binding-validate
```

Web preparation surface:

```text
/forecast
/api/forecast/candidate-build
/api/forecast/candidate-validate
/api/forecast/review-build
/api/forecast/review-validate
/api/forecast/finalize
/api/forecast/validate
/api/forecast/binding-build
/api/forecast/binding-validate
```

The M26 Web layer exposes no Draft apply, file write, promotion, admission, or canonical-write endpoint.

M26 Web 계층은 Draft 적용, 파일 쓰기, 승격, admission, canonical 쓰기 endpoint를 제공하지 않는다.
