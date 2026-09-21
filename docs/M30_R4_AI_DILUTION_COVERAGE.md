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

Treasury-stock-method adjustments use the same formula **per strike tranche**:

```text
incremental shares
  = Σ [tranche outstanding × max(0, market price - tranche strike) / market price]
```

A weighted-average exercise price is **not** a complete option-strike distribution. Applying `max(0, market - weighted_average_strike)` to a multi-strike portfolio can incorrectly erase dilution from lower-strike in-the-money options.

Therefore:

- `TREASURY_STOCK_METHOD_TRANCHES_V01` requires explicit strike tranches whose outstanding counts reconcile to the declared total;
- legacy `TREASURY_STOCK_METHOD_AGGREGATE_V01` is permitted only when source evidence explicitly proves one homogeneous exercise price;
- a filing that reports only total outstanding options plus weighted-average exercise price must remain `BLOCKED_DEPENDENCY` for valuation-date TSM.

M30-R4 requires a **fresh reviewed, source-bound M27 market-price package with the same entity and valuation `as_of`** before a TSM category may be `PRESENT`.

Without both market price and strike-distribution evidence, the correct state is `BLOCKED_DEPENDENCY`; no EPS dilution number, historical price, or weighted-average-strike shortcut may substitute.

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


## M30-R4.1 falsification / R4.1 반증

Real Ingredion execution exposed why the distribution rule is necessary. At 2026-06-30 the issuer reported 1.242 million options outstanding, weighted-average exercise price USD 105.61, **and positive aggregate intrinsic value of USD 3 million**. The positive intrinsic value proves that some options were in the money even though an aggregate average strike can sit above a later market price.

The first real HOLD artifact that treated the whole population as one option at USD 105.61 is therefore historical execution evidence only and must not be used for final dilution authority. The real Ingredion option category must remain blocked until complete strike-tranche/distribution evidence is obtained.
