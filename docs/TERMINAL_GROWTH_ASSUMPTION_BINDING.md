# Governed Terminal-Growth Assumption + Draft Binding / 거버넌스 영구성장률 가정 + Draft 바인딩

## Purpose / 목적

M25 governs `scenario.terminal_growth` as a perpetual valuation assumption. It does **not** convert a macro forecast, historical growth rate, or deterministic calculation into a terminal-growth fact.

M25는 `scenario.terminal_growth`를 영구 가치평가 가정으로 관리한다. 거시 전망, 과거 성장률, 결정론적 계산을 영구성장률 사실로 승격하지 않는다.

```text
macro anchor != terminal-growth fact
selected g != reviewed valuation assumption
ASSUMPTION_CANDIDATE != ASSUMPTION
```

## Dependency on M24 WACC / M24 WACC 의존성

M25 requires a valid `reviewed-wacc-assumption-v0.1`. The complete M24 WACC package is embedded in the M25 candidate and independently revalidated.

M25는 유효한 `reviewed-wacc-assumption-v0.1`을 필수로 요구한다. M24 WACC 전체 패키지를 M25 candidate에 내장하고 독립적으로 재검증한다.

The WACC package used to review terminal growth must be the **same package by SHA lineage** as the WACC package embedded in the v0.4 base proposal.

영구성장률 검토에 사용한 WACC 패키지는 v0.4 base proposal이 내장한 WACC 패키지와 **SHA lineage 기준으로 동일**해야 한다.

## Macro anchor / 거시 Anchor

M25 v0.1 requires two explicit source-backed anchor inputs:

M25 v0.1은 다음 두 개의 명시적 출처연결 anchor 입력을 요구한다.

```text
long_run_inflation
long_run_real_growth
```

Each input preserves claim class, value, observation date, publisher, source type/tier, locator, source SHA, and input SHA.

각 입력은 claim class, 값, 관측일, 발행자, source type/tier, locator, source SHA, input SHA를 보존한다.

The nominal long-run ceiling is reconstructed as:

장기 명목 성장 상한은 다음과 같이 재계산한다.

```text
nominal_growth_anchor = (1 + long_run_inflation)
                      × (1 + long_run_real_growth)
                      - 1
```

This is a **ceiling anchor**, not an automatic terminal-growth generator.

이는 **상한 anchor**이며 영구성장률 자동 생성기가 아니다.

## Scenario-specific assumptions / 시나리오별 가정

Every target scenario must contain exactly one explicit `terminal_growth` value and rationale.

각 대상 시나리오는 정확히 하나의 명시적 `terminal_growth` 값과 rationale을 가져야 한다.

M25 independently enforces:

M25는 다음을 독립 검증한다.

```text
g > -1
g < reviewed WACC
g <= nominal_growth_anchor
```

Negative terminal growth is permitted when explicitly selected and reviewed. Positive growth above the macro nominal ceiling is blocked in v0.1.

명시적으로 선택·검토된 음의 영구성장률은 허용한다. 장기 명목 거시 상한을 초과하는 양의 성장률은 v0.1에서 차단한다.

## Authority lifecycle / 권위 생명주기

```text
source-backed macro anchors
        +
reviewed M24 WACC package
        +
explicit scenario g + rationale
        ↓
terminal-growth-assumption-candidate-v0.1
class = ASSUMPTION_CANDIDATE
        ↓
terminal-growth-review-assertion-v0.1
        ↓
reviewed-terminal-growth-assumption-v0.1
class = ASSUMPTION
        ↓
draft-binding-proposal-v0.5
```

Arithmetic never upgrades authority by itself.

계산만으로 권위가 승격되지 않는다.

## Human review / 인간검토

The review assertion locks:

검토승인은 다음을 잠근다.

- exact candidate SHA / 정확한 candidate SHA
- exact WACC package SHA / 정확한 WACC package SHA
- methodology version / 방법론 버전
- valuation `as_of` / 가치평가 기준일
- exact scenario set / 정확한 시나리오 집합
- every scenario growth value and rationale / 모든 시나리오 성장률과 rationale
- reviewer / 검토자
- timezone-aware approval time / 시간대 포함 승인시각
- review basis / 검토 근거

Approval cannot predate valuation `as_of`.

승인일은 가치평가 `as_of`보다 앞설 수 없다.

## v0.5 binding / v0.5 바인딩

`draft-binding-proposal-v0.5` accepts only a validated M24 v0.4 proposal.

`draft-binding-proposal-v0.5`는 검증된 M24 v0.4 proposal만 base로 허용한다.

M25 may replace only:

M25가 변경할 수 있는 필드는 오직 다음이다.

```text
scenario.terminal_growth
```

`scenario.wacc`, cash, debt, diluted shares, conflicts, and every other decision must remain equivalent to the embedded v0.4 proposal.

`scenario.wacc`, cash, debt, diluted shares, conflicts 및 다른 모든 판정은 내장된 v0.4 proposal과 동일해야 한다.

## Apply-time WACC dependency / 적용시점 WACC 의존성

Terminal growth is meaningful only relative to the WACC against which it was reviewed.

영구성장률은 검토 당시의 WACC와 결합될 때만 의미가 있다.

Therefore M25 requires one of two states before `scenario.terminal_growth` can be approved:

따라서 `scenario.terminal_growth` 승인 전 다음 둘 중 하나를 요구한다.

1. the target Draft already contains the exact reviewed WACC for every scenario; or  
   대상 Draft의 모든 시나리오가 이미 정확한 reviewed WACC를 보유하거나,
2. `scenario.wacc` is approved in the same binding approval.  
   동일 binding approval에서 `scenario.wacc`를 함께 승인한다.

A Draft carrying a different WACC cannot receive terminal growth alone.

다른 WACC를 가진 Draft에는 영구성장률만 단독 적용할 수 없다.

## Applied diff / 적용 Diff

Terminal growth is recorded scenario by scenario:

영구성장률은 시나리오별로 기록한다.

```text
before = {BASE: old_g, BULL: old_g, ...}
after  = {BASE: reviewed_g, BULL: reviewed_g, ...}
```

Lineage preserves:

lineage는 다음을 보존한다.

```text
source_terminal_growth_package_sha256
source_wacc_package_sha256
review_assertion_sha256
scenario_names
```

The input Draft remains unchanged. The result remains `canonical=false`.

입력 Draft는 변경되지 않으며 결과는 `canonical=false`로 유지된다.

## Interfaces / 인터페이스

CLI/Web preparation surfaces are calculate/validate only. They do not expose Draft apply, file write, promotion, admission, or canonical write.

CLI/Web 준비 인터페이스는 calculate/validate 전용이며 Draft apply, file write, promotion, admission, canonical write를 제공하지 않는다.

Web Lab:

```text
/terminal-growth
/api/terminal-growth/*
```

## Fail-closed summary / Fail-closed 요약

M25 blocks:

- missing macro anchors / 거시 anchor 누락
- stale or Tier-D required anchors / stale 또는 Tier-D 필수 anchor
- `g <= -1`
- `g >= reviewed WACC`
- `g > nominal_growth_anchor`
- missing scenario rationale / 시나리오 rationale 누락
- scenario-set mismatch / 시나리오 집합 불일치
- different WACC package lineage / 다른 WACC package lineage
- non-v0.4 base proposal / v0.4가 아닌 base proposal
- outer-SHA re-signing that changes nested calculation/policy/projection / 중첩 계산·정책·투영을 바꾼 outer-SHA 재서명
- terminal-growth-only apply when Draft WACC differs / Draft WACC가 다른 상태의 영구성장률 단독 적용
