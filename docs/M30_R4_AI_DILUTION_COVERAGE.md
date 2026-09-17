# M30-R4 — Evidence-first AI dilution coverage / 근거 우선 AI 희석 커버리지

## Purpose / 목적

M30-R4 extends the internal evidence-first AI authority model to the M22 valuation-date diluted-share bridge.

It does **not** equate current common shares with fully diluted shares, and it does **not** reuse historical weighted-average diluted EPS shares as a point-in-time valuation share count.

```text
reviewed current common shares
  → fresh M22 share-base context
  → six-category dilution evidence inventory
  → explicit contradiction search
  → typed AI adjudication
  → reviewed numeric dilution adjustments (PRESENT only)
  → COMPLETE six-category coverage assertion
  → existing M22 diluted-share bridge
```

Incomplete evidence is a durable `HOLD_INCOMPLETE_DILUTION_COVERAGE`, not an error to bypass.

## Six mandatory categories / 필수 6개 범주

Every inventory must contain exactly once:

1. `options_treasury_stock_method`
2. `rsu_restricted_stock`
3. `warrants`
4. `convertibles_if_converted`
5. `contingent_shares`
6. `other_explicit`

Each category must be one of:

- `PRESENT`
- `ABSENT_SUPPORTED`
- `BLOCKED_DEPENDENCY`
- `UNKNOWN_CONFLICT`

Missing category evidence is never interpreted as absence or zero.

## Point-in-time semantic boundary / 시점 의미경계

M21 historical diluted-EPS evidence remains reference-only:

```text
weighted-average diluted EPS shares
  != valuation-date fully diluted shares
```

A `PRESENT` adjustment must be tied to explicit point-in-time evidence and a supported calculation method. Historical weighted-average EPS dilution cannot be supplied as a valuation-date adjustment.

## Options and warrants TSM / 옵션·워런트 TSM

Treasury-stock-method adjustments use:

```text
incremental shares = outstanding instruments × max(0, market price - exercise price) / market price
```

M30-R4 requires a **fresh reviewed, source-bound M27 market-price package with the same entity and valuation `as_of`** before a TSM category may be `PRESENT`.

Without it, the correct state is `BLOCKED_DEPENDENCY`; no EPS dilution number or historical price may substitute.

## AI authority / AI 권위

The adjudicator is always explicit:

```text
AI_DILUTION_ADJUDICATOR_V01
review_authority = AI
policy = EVIDENCE_FIRST_DILUTION_COVERAGE_V01
```

No human reviewer identity is inferred or fabricated.

The existing M22 human path remains unchanged. When AI coverage is complete, M30-R4 projects typed AI authority into the existing M22 reviewed-adjustment and coverage-assertion contracts so all downstream M22 validators are reused rather than bypassed.

## Complete-coverage rule / 완전 커버리지 규칙

`COMPLETE_REVIEWED_DILUTION_COVERAGE` is possible only when:

- all six categories are explicitly present in the inventory;
- every category is `PRESENT` or `ABSENT_SUPPORTED`;
- every `PRESENT` category has a reproducible numeric calculation;
- every source is SHA-bound;
- contradiction search was explicitly performed;
- no material contradiction remains;
- the base share context is fresh;
- all reviewed adjustments validate as M22 `NORMALIZED_FACT`;
- the M22 bridge validator independently reproduces the result.

Any `BLOCKED_DEPENDENCY` or `UNKNOWN_CONFLICT` prevents finalization.

## Real Ingredion execution state / 실기업 Ingredion 실행상태

Canonical M30-R3 execution established:

- current common shares: `63,063,979` as of 2026-08-05;
- share-base context as of 2026-09-14: `FRESH`;
- `fully_diluted_shares=false` and `direct_bind_to_diluted_shares=false` remain locked.

Issuer filing evidence currently identifies:

- stock options outstanding at 2026-06-30;
- employee RSUs outstanding at 2026-06-30;
- performance-share awards whose payout depends on performance conditions;
- director/deferred share-based arrangements that require explicit coverage review.

The 2026 Q2 EPS disclosure also contains historical weighted-average dilution. That disclosure is useful only as a contradiction/reference check and is not a valuation-date adjustment.

Before the real Ingredion inventory can become COMPLETE, at least the following must be resolved with source-bound evidence:

- valuation-date market price for TSM;
- point-in-time performance/contingent award coverage;
- point-in-time director/deferred equity coverage;
- affirmative evidence for any `ABSENT_SUPPORTED` warrant/convertible categories.

## CLI / CLI

```text
dilution-ai-inventory-build
dilution-ai-inventory-validate
dilution-ai-adjudicate
dilution-ai-adjudication-validate
dilution-ai-finalize
dilution-ai-package-validate
```

The CLI is calculate/validate-only. It does not write Drafts, mutate the registry, or admit a canonical case.
