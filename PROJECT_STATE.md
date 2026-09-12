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

M23 final PR CI `34692745133` and post-merge `main` CI `34692789399` passed on Python 3.11/3.12. Issue #50 is completed.

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

- Issue: `#52 [M24] Governed WACC assumption package + scenario.wacc binding`
- PR: `#53 M24 Governed WACC assumption + scenario.wacc binding`
- Branch: `mission/m24-wacc-assumption-binding-v01`
- Base main: `58d963238992f562c89c8325b42046ae35ac71bf`
- Status: `ACTIVE_FINALIZATION`

## M24 CI history / M24 CI 이력

- Initial core head: `50722f589c5dc62cfe140540514c64fd85ca38ff`
  - CI `34693139601`: Python 3.11/3.12 `success`
- Hardened core head: `c34fc9232aca459920727ce3502334c14fd940f2`
  - CI `34693273291`: Python 3.11/3.12 `success`
- Interface/schema head: `df5882ab31204aea98cc31e05eae3942ba2a619f`
  - CI `34693425090`: Python 3.11/3.12 `success`

A fresh final-head CI is required after M24 docs/README/PROJECT_STATE changes. Only that exact tested head may authorize merge.

## M24 authority boundary / M24 권위경계

```text
source facts != WACC fact
calculated WACC != reviewed valuation assumption
ASSUMPTION_CANDIDATE != ASSUMPTION
reviewed ASSUMPTION != canonical state
```

WACC remains a valuation assumption because source selection, beta/ERP/debt-cost choice, capital structure basis, tax treatment, valuation date, and scenario targeting involve explicit methodology choices.

## Required WACC components / 필수 WACC 구성요소

Canonical v0.1 order:

```text
risk_free_rate
equity_risk_premium
levered_beta
pre_tax_cost_of_debt
equity_market_value
debt_market_value
tax_rate
```

Every component preserves value/unit, observed date, claim class, publisher, source type/tier, locator, source SHA, and input SHA.

No required component is silently supplied or zero-imputed. Debt market value may explicitly equal zero; equity market value must be positive.

## WACC calculation / WACC 계산

Methodology:

```text
wacc-capm-market-weights-v0.1
```

```text
cost_of_equity = rf + beta × ERP
after_tax_cost_of_debt = Rd × (1 - T)
weight_equity = E / (D + E)
weight_debt = D / (D + E)
WACC = weight_equity × cost_of_equity
     + weight_debt × after_tax_cost_of_debt
```

Validators independently reconstruct every calculated field, require finite values, verify capital weights, and require final `0 < WACC <= 0.99`. Missing/nonfinite calculation fields fail even if the outer candidate SHA is recomputed.

## Freshness / 최신성

Fixed v0.1 max ages:

```text
risk_free_rate        30
ERP                   90
levered_beta         180
pre_tax_cost_of_debt 180
equity_market_value   30
debt_market_value    550
tax_rate             550
```

Future-dated source inputs fail closed. Stale required inputs and Tier-D required inputs make `eligible_for_human_review=false`.

## Human WACC review / 인간 WACC 검토

A `wacc-review-assertion-v0.1` separately locks:

- exact candidate SHA
- methodology version
- valuation `as_of`
- target `scenario_names`
- reviewer
- timezone-aware `approved_at`
- review basis
- assertion SHA

Approval cannot predate valuation `as_of`.

Finalization yields:

```text
reviewed-wacc-assumption-v0.1
class = ASSUMPTION
binding_eligibility = REVIEWED_WACC_ASSUMPTION
```

The complete candidate and assertion remain embedded and independently revalidated.

## v0.4 binding / v0.4 바인딩

```text
validated v0.1/v0.2/v0.3 proposal
        +
reviewed WACC ASSUMPTION
        ↓
draft-binding-proposal-v0.4
```

M24 may replace only:

```text
scenario.wacc
```

Every other matrix entry must remain byte/semantic-equivalent to the embedded base proposal.

Exact compatibility gates:

- entity ID
- financial scope
- capital currency
- `as_of`
- reviewed package validity

The v0.4 policy itself is reconstructed exactly; an attacker cannot weaken `direct_bind_requires`, recompute the outer proposal SHA, and pass validation.

## Scenario target gate / 시나리오 대상 게이트

A WACC package contains explicit `scenario_names`.

When `scenario.wacc` is approved through M17, that set must equal the complete scenario set in the target Draft. Partial scenario binding is prohibited in v0.1.

Applied diff form:

```text
before = {scenario_name: old_wacc, ...}
after  = {scenario_name: reviewed_wacc, ...}
```

and preserves:

```text
source_package_sha256
review_assertion_sha256
scenario_names
```

The source Draft object remains unchanged and the result remains noncanonical.

## Interfaces / 인터페이스

M24 CLI is additive. The new wrapper intercepts only M24 commands plus v0.4-aware `binding-validate` and `web`; every older command delegates to the M23 dispatcher.

CLI:

```text
wacc-source-build
wacc-source-validate
wacc-candidate-build
wacc-candidate-validate
wacc-review-build
wacc-review-validate
wacc-finalize
wacc-validate
binding-build-with-wacc
binding-validate
```

Web:

```text
/wacc
/api/wacc/candidate-build
/api/wacc/candidate-validate
/api/wacc/review-build
/api/wacc/review-validate
/api/wacc/finalize
/api/wacc/validate
/api/wacc/binding-build
/api/wacc/binding-validate
```

The M24 Web layer has no Draft-apply, file-write, promotion, admission, or canonical-write endpoint.

## M24 files / M24 파일

- `src/valuation_hub/wacc_assumption.py`
- `src/valuation_hub/wacc_draft_binding.py`
- `src/valuation_hub/binding_apply.py`
- `src/valuation_hub/cli_entry_m24.py`
- `src/valuation_hub/web_wacc.py`
- `schemas/wacc_source_input.schema.json`
- `schemas/wacc_assumption_candidate.schema.json`
- `schemas/wacc_review_assertion.schema.json`
- `schemas/reviewed_wacc_assumption.schema.json`
- `schemas/draft_binding_proposal_v04.schema.json`
- `tests/test_m24_wacc_binding.py`
- `tests/test_m24_hardening.py`
- `tests/test_m24_interfaces.py`
- `docs/WACC_ASSUMPTION_BINDING.md`
- `docs/M24_ACCEPTANCE.md`
- `docs/M24_IMPLEMENTATION_SUMMARY.md`

## Grounding authority / 근거화 권위

1. merged `main` files and decisions
2. `PROJECT_STATE.md` + active Issue/PR/branch
3. source-input SHA → candidate SHA → review assertion SHA → reviewed package SHA → v0.4 proposal SHA → M17 approval/result SHA
4. current chat
5. AI recollection

## Exact resume point / 정확한 재개점

Run a fresh full Python 3.11/3.12 CI on the exact current PR #53 head after this handoff update.

Merge only if all remain green:

- source provenance/integrity validation
- metric-specific freshness recomputation
- stale/Tier-D review blocking
- CAPM/debt-cost/weight/WACC arithmetic recomputation
- re-signing hardening
- candidate/reviewed-assumption authority separation
- human review lineage lock
- v0.4 exact policy reconstruction
- only `scenario.wacc` replacement
- entity/scope/currency/as-of compatibility
- exact full-Draft scenario target set at M17 approval/apply
- WACC scenario-by-scenario diff reconstruction
- source Draft immutability
- existing cash/debt/diluted-share apply regression compatibility
- additive CLI delegation
- Web no-write boundary
- all M1-M24 regressions

After final-head CI passes, update PR #53 with exact tested SHA/run, merge with `expected_head_sha`, confirm Issue #52 closes as completed, and verify post-merge `main` Python 3.11/3.12 CI before declaring M24 canonical.

If M24 closes cleanly, re-evaluate the remaining `MATERIAL_FIELDS`. The likely next high-value assumption is `scenario.terminal_growth`, but select it only after the canonical matrix is re-grounded after M24 merge.
