# M30-R6 — Disclosure-limited diluted-share assumption / 공시제약 희석주식 가정

## Purpose / 목적

M30-R6 is a **fallback assumption path**, not a relaxation of M22/M30-R4 exact dilution governance.

Priority remains:

```text
exact current-share base
  → exact six-category R4 coverage
  → COMPLETE reviewed M22 bridge
```

Only when the exact R4 path is a clean disclosure-insufficiency `HOLD` may R6 evaluate whether a separately typed valuation assumption is sufficiently bounded to use in a later assumption-aware successor.

R6 never converts historical diluted EPS shares into a fact and never labels the result `DERIVED_FACT`.

## Trigger / 발동조건

R6 requires all of the following:

- fresh reviewed current-common-share base;
- R4/R4.1 decision = `HOLD_INCOMPLETE_DILUTION_COVERAGE`;
- at least one `BLOCKED_DEPENDENCY`;
- no `UNKNOWN_CONFLICT`;
- reviewed M21 historical dilution evidence;
- historical diluted-share period within explicit freshness policy;
- source-bound conservative upper-envelope components;
- valuation `as_of` identity consistency.

If R4 is exact-ready, the fallback is rejected because the exact path outranks R6.

## Selected assumption / 선택 가정

```text
exact_present_floor
  = current common shares
  + exact R4 PRESENT adjustments

selected diluted-share assumption
  = max(
      latest issuer diluted weighted-average share anchor,
      exact_present_floor
    )
```

The historical denominator remains duration evidence. The `max` rule is a conservative selection policy, not authority conversion.

## Conservative upper envelope / 보수적 상단 envelope

R6 accepts source-bound components with explicit roles:

- `ANCHOR_OUTSTANDING_AWARDS`
- `SUBSEQUENT_GROSS_GRANT`
- `PERFORMANCE_MAX_UPLIFT`
- `DISCLOSURE_LAG_BUFFER` — must use `PRO_RATA_GROSS_GRANT_RUN_RATE_V01` with explicit observed grants, observed days and lag days; arbitrary plug values are rejected.

The upper envelope is:

```text
upper diluted shares
  = current common shares
  + Σ explicit conservative envelope components
```

No netting is performed. Exercises, vesting, cancellations, forfeitures, or settlements that would reduce dilution are intentionally not subtracted unless the envelope itself is rebuilt from stronger evidence. A disclosure-lag buffer is not chosen to satisfy the materiality threshold; it must mechanically reproduce from source-backed gross grant run-rate inputs.

This makes the upper side conservative but explicitly **not exact**.

## Materiality gate / 중요성 게이트

Default:

```text
relative_upper_spread
  = upper / selected - 1

materiality_threshold = 5%
```

If the spread exceeds the threshold:

`HOLD_DISCLOSURE_LIMITED_DILUTION_MATERIALITY`

No assumption package can be finalized.

If the spread is within the threshold:

`APPROVE_DISCLOSURE_LIMITED_DILUTION_ASSUMPTION`

The final package is class:

`ASSUMPTION`

not `FACT`, not `DERIVED_FACT`.

## Real Ingredion motivation / 실기업 근거

Current exact R4.1 HOLD:

- inventory SHA `bb8242c126fcd0c91c0a3aedd8aac26640c8b3ad829a59823eb861762270a4b2`
- adjudication SHA `48545fdeb713af826bd39d1fc2b22a5bb6dde10474d3a6ccac0174370d790d86`

Unresolved:
- option strike distribution;
- payout-weighted performance awards;
- director/deferred equity.

Issuer evidence also reports for 2026 Q2:
- weighted-average basic shares: 63.3M;
- weighted-average diluted shares: 63.9M;
- historical incremental dilution: 0.6M;
- approximately 0.8M share-based awards excluded from diluted EPS as anti-dilutive.

The 2026 proxy reports at 2025-12-31:
- 2,177,904 total securities reflected in the equity-compensation plan table;
- 151,570 PSUs at 100% vesting assumption;
- 510,000 RSUs;
- 35,694 phantom units in non-approved-plan accounts.

2026 Q2 separately reports:
- 215k employee RSU grants;
- 116k performance-share grants.

These facts can support a conservative envelope, but they do not become an exact valuation-date fully diluted share count by implication.

## Authority / 권위

Adjudicator:

`AI_DISCLOSURE_LIMITED_DILUTION_ADJUDICATOR_V01`

Final package:

`disclosure-limited-diluted-share-assumption-v0.1`

Binding boundary:

```text
eligible_for_assumption_aware_successor = true
eligible_for_m22_derived_fact_direct_bind = false
```

A later explicit successor is required before this assumption may enter a Draft. M30-R6 does not mutate Drafts, registry, admission state, or canonical cases.

## CLI

```text
dilution-assumption-evidence-build
dilution-assumption-evidence-validate
dilution-assumption-adjudicate
dilution-assumption-adjudication-validate
dilution-assumption-finalize
dilution-assumption-package-validate
```
