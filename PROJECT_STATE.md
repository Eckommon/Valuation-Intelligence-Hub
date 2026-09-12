# Project State / 프로젝트 상태

> Canonical human-and-AI handoff. Repository-grounded state outranks chat or AI recollection.  
> 인간·AI 공통 정식 인계 문서. 저장소 근거 상태는 채팅·AI 기억보다 우선한다.

## Repository / 저장소

- `Eckommon/Valuation-Intelligence-Hub`
- Purpose: cross-asset, evidence-grounded valuation intelligence / 범자산 근거 기반 가치분석 인텔리전스

## Completed canonical baseline / 완료 기준선

| Milestone | Main commit | Issue |
|---|---|---:|
| M12 Guarded admission apply | `a40e92c196c39b40172711f38f7231f5e8812d52` | #26 |
| M13 Immutable SEC live evidence | `372b8b0b26307730c3e91afea97c979b59906042` | #28 |
| M14 Immutable OpenDART financial evidence | `1fff272cc583ec294226f5f530ebe483c2957fb5` | #30 |
| M15 Financial normalization + TTM | `a99a6f24fa6736b01b270a2eeeb4592e8b673563` | #32 |
| M16 Governed evidence → Draft binding proposal | `fbaf90bab04a877ba6afaaa035a4e99e9ef085a0` | #34 |
| M17 Human-approved noncanonical Draft binding apply | `ef68c2549bef842ef417d401140b49c88af209b5` | #38 |
| M18 Governed derived financial evidence + historical margins | `fb33cfbf401ab9c2e36ccd831bd059c8951214ba` | #40 |
| M19 Governed interest-bearing debt components + aggregation | `5b2ab53b0c83632abae187f12e1a682ecc254b77` | #42 |
| M20 Reviewed debt → `equity.debt` binding | `236547512919b5d68e283b3431183f56f5fc845c` | #44 |
| M21 Governed historical dilution reference | `03af933835b8fbcf9ef4e6b3fd1b3db7603782fc` | #46 |
| M22 Valuation-date common-share base + diluted-share bridge | `0a476cc9927b2d63164143447428f3e69b06051b` | #48 |
| M23 Complete reviewed share bridge → `equity.diluted_shares` | `58d963238992f562c89c8325b42046ae35ac71bf` | #50 |
| M24 Governed WACC assumption → `scenario.wacc` | `ca85f04c1bd84c5189f78c81e2653cc4f65bccca` | #52 |
| M25 Governed terminal growth → `scenario.terminal_growth` | `0c0a7591a59f163fa34aba54fdeb6001fb9b7dc0` | #54 |

M24 final PR CI `34693544084` and post-merge main CI `34693990230` passed Python 3.11/3.12.

M25 final PR CI `34694777238` and post-merge main CI `34694840768` passed Python 3.11/3.12. Issue #54 is completed.

Earlier milestones remain completed and regression-locked in repository history.

## Authority model / 권위모델

```text
SOURCE
  ↓
IMMUTABLE / SOURCE-LOCKED INPUT / NOT CANONICAL
  ↓
FACT / NORMALIZED FACT / ASSUMPTION_CANDIDATE
  ↓
GOVERNED CONTEXT or HUMAN-REVIEWED ASSUMPTION / NOT CANONICAL
  ↓
BINDING PROPOSAL / NOT CANONICAL
  ↓
HUMAN APPROVAL LOCK / NOT CANONICAL
  ↓
BOUND DRAFT RESULT / NOT CANONICAL
  ↓
DRAFT GOVERNANCE → PROMOTION → ADMISSION → guarded apply → PR/CI merge
  ↓
CANONICAL
```

Calculation never silently upgrades `ASSUMPTION_CANDIDATE` to `ASSUMPTION`, nor `ASSUMPTION` to `FACT`.

## Active mission / 활성 미션

- Issue: `#56 [M26] Integrated forecast-scenario assumption package + atomic Draft binding`
- PR: `#57 M26 Integrated forecast package + atomic Draft binding`
- Branch: `mission/m26-integrated-forecast-binding-v01`
- Base main: `0c0a7591a59f163fa34aba54fdeb6001fb9b7dc0`
- Status: `ACTIVE_FINALIZATION`

## M26 mission / M26 미션

Govern the six explicit FCFF forecast-year material inputs as one coherent human-reviewed assumption package and bind them atomically into the equity-FCFF Draft.

명시기간 FCFF의 여섯 미래 중요입력을 하나의 일관된 인간검토 가정패키지로 거버넌스하고 equity-FCFF Draft에 원자적으로 바인딩한다.

Atomic fields:

```text
scenario.years.revenue
scenario.years.ebit_margin
scenario.years.tax_rate
scenario.years.depreciation_amortization
scenario.years.capex
scenario.years.delta_nwc
```

## M26 authority boundary / M26 권위경계

```text
historical fact != forecast assumption
historical trend != automatic forecast
calculated EBIT/NOPAT/FCFF != forecast authority
ASSUMPTION_CANDIDATE != ASSUMPTION
reviewed ASSUMPTION != canonical state
```

Forecast diagnostics are review aids only.

Forecast 진단값은 검토 보조값일 뿐 authority를 생성하지 않는다.

## Forecast candidate / Forecast Candidate

`forecast-scenario-assumption-candidate-v0.1` requires:

- explicit unique scenario names
- explicit scenario rationale
- one identical strictly ascending future-year set across all scenarios
- every forecast year strictly after the valuation `as_of` year
- complete six-component rows
- exact entity / financial scope / capital currency / `as_of`

Numeric gates:

```text
revenue >= 0
-1 <= ebit_margin <= 1
0 <= tax_rate < 1
D&A >= 0
CAPEX >= 0
ΔNWC finite; negative allowed
```

For each scenario/year the validator independently recomputes EBIT, NOPAT, FCFF, and revenue-growth diagnostics.

## Human review / 인간검토

`forecast-scenario-review-assertion-v0.1` locks:

- exact candidate SHA
- exact forecast-block SHA
- methodology version
- entity / scope / currency / `as_of`
- exact scenario set
- exact ordered forecast-year set
- reviewer
- timezone-aware approval timestamp
- review basis

Approval cannot predate valuation `as_of`.

Finalization yields:

```text
reviewed-forecast-scenario-assumption-v0.1
class = ASSUMPTION
binding_eligibility = REVIEWED_INTEGRATED_FORECAST_ASSUMPTION
canonical = false
```

## v0.6 binding / v0.6 바인딩

```text
validated draft-binding-proposal-v0.5
        +
reviewed integrated forecast ASSUMPTION
        ↓
draft-binding-proposal-v0.6
```

M26 accepts **only** validated v0.5 as its base.

The forecast package must exactly match base entity, financial scope, capital currency, valuation `as_of`, and the v0.5 terminal-growth scenario set.

v0.6 replaces exactly the six forecast-year decisions. Every other base decision remains unchanged, including:

```text
scenario.wacc
scenario.terminal_growth
equity.cash
equity.debt
equity.diluted_shares
```

The v0.6 validator reconstructs exact policy, baseline projection, six decisions, completeness, package lineage, and final SHA.

## Atomic apply / 원자적 적용

M17 approval/apply now enforces:

```text
if any forecast field is approved:
    all six forecast fields must be approved
```

The target Draft must already contain the exact scenario set and the exact ordered forecast-year set for every scenario. M26 v0.1 does not silently create, remove, or reorder scenario/year rows.

Each component diff records scenario/year before→after values and preserves:

```text
source_forecast_package_sha256
forecast_block_sha256
review_assertion_sha256
scenario_names
forecast_years
forecast_component
```

The input Draft remains unchanged. The result remains noncanonical.

## Result-integrity hardening / 결과 무결성 강화

During M26 review a generic bound-result validation gap was discovered.

Pre-hardening, the validator required only:

```text
len(applied_diffs) == len(approved_fields)
```

A re-signed forged result could repeat one sequentially valid diff and omit another approved field.

M26 now requires:

```text
all applied diff fields are unique
AND
set(applied_diff.field) == set(approved_fields)
```

Red→green evidence:

- exploit reproduction test-only head `2b30bbfe0372e51358a42b6d3df03c60a3699220`
  - CI `34708359543`: expected `failure`
- production guard + hardening tests
  - later hardened CI is green

## M26 CI history / M26 CI 이력

- Initial core head `06dacd6806b32b1b9d168e6bc63497303866f049`
  - CI `34708138491`: Python 3.11/3.12 `success`
- Exploit reproduction test-only head `2b30bbfe0372e51358a42b6d3df03c60a3699220`
  - CI `34708359543`: expected `failure`
- Hardened core + re-signing head `1e225fccea82ba14d404d808fbedeffac6fb3f42`
  - CI `34708455989`: Python 3.11/3.12 `success`
- Interface/schema head `ad6fcf8b5107f33b7d69c21b5a69ff6acdb21c86`
  - CI `34708632795`: Python 3.11/3.12 `success`

A fresh final-head CI is required after the documentation/README/PROJECT_STATE handoff. Only that exact tested head may authorize merge.

## Interfaces / 인터페이스

M26 CLI is additive through `src/valuation_hub/cli_entry_m26.py`. All older M1–M25 commands delegate to the M25 dispatcher.

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

Web:

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

M26 Web is calculate/validate preparation only. It has no Draft-apply, file-write, promotion, admission, or canonical-write endpoint.

## M26 files / M26 파일

- `src/valuation_hub/forecast_assumption.py`
- `src/valuation_hub/forecast_draft_binding.py`
- `src/valuation_hub/binding_apply.py`
- `src/valuation_hub/cli_entry_m26.py`
- `src/valuation_hub/web_forecast.py`
- `schemas/forecast_scenario_assumption_candidate.schema.json`
- `schemas/forecast_scenario_review_assertion.schema.json`
- `schemas/reviewed_forecast_scenario_assumption.schema.json`
- `schemas/draft_binding_proposal_v06.schema.json`
- `tests/test_m26_integrated_forecast_binding.py`
- `tests/test_m26_result_diff_hardening.py`
- `tests/test_m26_hardening.py`
- `tests/test_m26_interfaces.py`
- `docs/FORECAST_SCENARIO_ASSUMPTION_BINDING.md`
- `docs/M26_ACCEPTANCE.md`
- `docs/M26_IMPLEMENTATION_SUMMARY.md`

## Grounding authority / 근거화 권위

1. merged `main` files and decisions
2. `PROJECT_STATE.md` + active Issue/PR/branch
3. M25 v0.5 proposal SHA → forecast candidate/block SHA → review assertion SHA → reviewed forecast package SHA → v0.6 proposal SHA → M17 approval/result SHA
4. current chat
5. AI recollection

## Remaining material gaps after M26 / M26 이후 잔여 중요입력

Once M26 is canonical, the M16 material-field matrix will have governed paths for cash, debt, diluted shares, WACC, terminal growth, and all six explicit forecast inputs.

M26 정식화 이후 cash, debt, diluted shares, WACC, terminal growth, 여섯 Forecast 입력은 모두 거버넌스 경로를 갖는다.

Remaining likely material gaps:

```text
market_price
equity.minority_interest
```

Do not start either until M26 is merged and latest `main` is re-grounded.

M26 병합 및 최신 main 재근거화 전에는 다음 미션을 시작하지 않는다.

## Exact resume point / 정확한 재개점

Run fresh full Python 3.11/3.12 CI on the exact current PR #57 head after this handoff update.

Merge only if all remain green:

- forecast candidate authority separation
- exact common future-year set
- complete six-component rows and numeric guards
- diagnostic independent recomputation
- human review SHA lock
- nested candidate/assertion tamper blocking
- v0.5-only base requirement
- exact scenario/entity/scope/currency/as-of compatibility
- v0.6 exact policy reconstruction
- only six forecast decisions replaced
- all-six-or-none approval
- exact Draft scenario/year target sets
- unique applied diff fields exactly equal to approved fields
- scenario/year/component diff reconstruction
- source Draft immutability
- additive CLI delegation
- Web no-write boundary
- all M1–M25 regressions

After final-head CI passes, update PR #57 with the exact tested SHA/run, merge using `expected_head_sha`, confirm Issue #56 closes as completed, and verify post-merge `main` Python 3.11/3.12 CI before declaring M26 canonical.

After M26 closes, re-ground latest `main` and select the next mission from the remaining material gaps rather than assuming the next step from chat memory.
