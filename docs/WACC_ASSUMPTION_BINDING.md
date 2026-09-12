# Governed WACC Assumption Binding / 거버넌스 WACC 가정 바인딩

## Purpose / 목적

M24 makes `scenario.wacc` reproducible and reviewable without pretending that WACC is a historical fact.

```text
source inputs
  ↓
ASSUMPTION_CANDIDATE
  ↓
SHA-locked human review assertion
  ↓
reviewed ASSUMPTION
  ↓
draft-binding-proposal-v0.4
  ↓
existing M17 human binding approval
  ↓
noncanonical Draft result
```

## Authority rule / 권위규칙

```text
source facts != WACC fact
calculated WACC != reviewed valuation assumption
ASSUMPTION_CANDIDATE != ASSUMPTION
```

Arithmetic is deterministic, but the choice of beta, ERP, debt cost, capital weights, tax rate, dates, source quality, and scenario targets remains a valuation methodology decision. Therefore M24 never labels WACC `FACT` or `NORMALIZED_FACT`.

## Required source inputs / 필수 원천입력

Exactly seven components are required in canonical v0.1 order:

1. `risk_free_rate`
2. `equity_risk_premium`
3. `levered_beta`
4. `pre_tax_cost_of_debt`
5. `equity_market_value`
6. `debt_market_value`
7. `tax_rate`

Each source-input record preserves:

- claim class (`FACT`, `NORMALIZED_FACT`, or `ASSUMPTION`)
- value and unit
- observation date
- publisher
- source type
- source tier
- locator
- source SHA-256
- input SHA-256

No required input is defaulted or zero-imputed. Debt market value may explicitly be zero; equity market value must be positive.

## Fixed v0.1 freshness policy / v0.1 고정 최신성 정책

| Metric | Max age |
|---|---:|
| risk-free rate | 30 days |
| ERP | 90 days |
| levered beta | 180 days |
| pre-tax cost of debt | 180 days |
| equity market value | 30 days |
| debt market value | 550 days |
| tax rate | 550 days |

A future-dated observation fails closed. A stale required input may remain in a candidate, but the candidate is not eligible for human review.

Tier D is exploratory only and blocks human-review eligibility. Tiers A/B/C are reviewable in v0.1.

## Methodology / 방법론

Methodology version:

```text
wacc-capm-market-weights-v0.1
```

Formula:

```text
cost_of_equity = risk_free_rate + levered_beta × equity_risk_premium

after_tax_cost_of_debt = pre_tax_cost_of_debt × (1 - tax_rate)

weight_equity = equity_market_value / (equity_market_value + debt_market_value)
weight_debt   = debt_market_value   / (equity_market_value + debt_market_value)

WACC = weight_equity × cost_of_equity
     + weight_debt × after_tax_cost_of_debt
```

Validators independently recompute all five calculated fields and the final WACC. Missing/nonfinite calculation fields fail even if an outer SHA is recomputed.

## Human review / 인간검토

A candidate can be reviewed only when:

```text
all_required_inputs_present = true
all_inputs_fresh = true
all_source_tiers_reviewable = true
eligible_for_human_review = true
```

The separate `wacc-review-assertion-v0.1` locks:

- exact candidate SHA
- methodology version
- valuation `as_of`
- target scenario names
- reviewer
- timezone-aware approval timestamp
- review basis
- assertion SHA

Approval cannot predate valuation `as_of`.

Finalization produces `reviewed-wacc-assumption-v0.1` with:

```text
class = ASSUMPTION
binding_eligibility.eligible = true
```

The full candidate and full review assertion remain embedded and are revalidated.

## Scenario targeting / 시나리오 대상

One reviewed WACC value is applied to the package's explicit `scenario_names`.

At M17 approval time, the package scenario set must equal the Draft's entire scenario set exactly. Subset application is intentionally prohibited in v0.1 so an apparently DIRECT_BIND `scenario.wacc` field can never leave unreviewed scenario WACCs behind.

## v0.4 binding / v0.4 바인딩

M24 wraps an already validated v0.1, v0.2, or v0.3 proposal:

```text
validated base proposal
        +
reviewed WACC ASSUMPTION
        ↓
draft-binding-proposal-v0.4
```

M24 may replace only:

```text
scenario.wacc
```

Every other decision must be identical to the embedded base proposal.

The projected context and DIRECT_BIND decision preserve:

```text
source_package_sha256
review_assertion_sha256
scenario_names
```

## M17 apply / M17 적용

The existing `binding-approval-v0.1` contract is reused.

When `scenario.wacc` is approved, the applied diff records scenario-by-scenario before/after mappings, for example:

```json
{
  "field": "scenario.wacc",
  "before": {"BASE": 0.10},
  "after": {"BASE": 0.084},
  "source_package_sha256": "...",
  "review_assertion_sha256": "...",
  "scenario_names": ["BASE"]
}
```

The original Draft object remains unchanged. The result remains noncanonical.

## CLI / CLI

M24 adds an additive CLI wrapper. Existing M1-M23 commands delegate unchanged to the prior dispatcher.

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

`binding-validate` now validates v0.1 through v0.4.

## Web / Web

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

The Web surface is calculate/validate preparation only. It has no Draft-apply, file-write, promotion, admission, or canonical-write endpoint.
