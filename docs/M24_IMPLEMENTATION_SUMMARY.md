# M24 Implementation Summary / M24 구현 요약

## Result / 결과

M24 adds a governed WACC-assumption lifecycle and `draft-binding-proposal-v0.4` so a human-reviewed WACC can enter `scenario.wacc` without being misclassified as a historical fact.

## Authority chain / 권위사슬

```text
wacc-source-input-v0.1
        ↓
wacc-assumption-candidate-v0.1 / ASSUMPTION_CANDIDATE
        ↓
wacc-review-assertion-v0.1
        ↓
reviewed-wacc-assumption-v0.1 / ASSUMPTION
        ↓
draft-binding-proposal-v0.4
        ↓
binding-approval-v0.1
        ↓
bound-draft-result-v0.1 / NOT CANONICAL
```

## Core implementation / 핵심 구현

### `src/valuation_hub/wacc_assumption.py`

- seven required sourced components
- source claim class + Tier + locator + SHA provenance
- fixed per-metric freshness policy
- CAPM cost-of-equity calculation
- after-tax debt-cost calculation
- market-value capital weights
- strict independent arithmetic validation
- `ASSUMPTION_CANDIDATE` review-readiness gate
- SHA-locked human review assertion
- reviewed `ASSUMPTION` package
- nested revalidation and re-signing hardening

### `src/valuation_hub/wacc_draft_binding.py`

- v0.4 wrapper over validated v0.1/v0.2/v0.3 proposal
- only `scenario.wacc` replacement permitted
- entity/scope/currency/as-of compatibility
- exact v0.4 policy reconstruction
- embedded full reviewed WACC package
- package/review/scenario lineage projection
- v0.1→v0.4 validator chain

### `src/valuation_hub/binding_apply.py`

M17 approval contract remains `binding-approval-v0.1`.

M24 extends the apply engine to `scenario.wacc` with:

- exact Draft scenario-set matching
- scenario-by-scenario before/after mapping
- source package SHA
- WACC review assertion SHA
- scenario target lineage
- input Draft immutability

Existing cash, debt, and diluted-share paths retain their prior behavior.

## Additive interfaces / 추가형 인터페이스

### CLI

`src/valuation_hub/cli_entry_m24.py` intercepts only M24 commands, v0.4-aware `binding-validate`, and `web`. All earlier commands delegate to the prior M23 dispatcher.

### Web

`src/valuation_hub/web_wacc.py` extends the existing handler chain with:

```text
/wacc
/api/wacc/*
```

The surface is calculate/validate only; there is no M24 Draft-apply or write route.

## JSON Schemas / JSON 스키마

- `wacc_source_input.schema.json`
- `wacc_assumption_candidate.schema.json`
- `wacc_review_assertion.schema.json`
- `reviewed_wacc_assumption.schema.json`
- `draft_binding_proposal_v04.schema.json`

## Tests / 테스트

- `tests/test_m24_wacc_binding.py`
- `tests/test_m24_hardening.py`
- `tests/test_m24_interfaces.py`

Coverage includes:

- WACC arithmetic and capital weights
- stale/Tier-D review blocking
- candidate vs reviewed authority separation
- nested tamper detection
- missing/nonfinite arithmetic rejection
- v0.4 policy re-signing hardening
- base proposal preservation
- human-approved WACC apply
- exact scenario-set enforcement
- Draft immutability
- additive CLI dispatch
- Web no-write boundary

## CI checkpoints / CI 체크포인트

- Core head `50722f589c5dc62cfe140540514c64fd85ca38ff` → CI `34693139601` → Python 3.11/3.12 success
- Hardened core head `c34fc9232aca459920727ce3502334c14fd940f2` → CI `34693273291` → Python 3.11/3.12 success
- Interface/schema head `df5882ab31204aea98cc31e05eae3942ba2a619f` → CI `34693425090` → Python 3.11/3.12 success

A fresh final-head CI after README/PROJECT_STATE documentation changes remains the merge gate.
