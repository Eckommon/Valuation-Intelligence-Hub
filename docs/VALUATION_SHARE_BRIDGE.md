# Valuation-Date Share Base + Diluted-Share Bridge / 가치평가일 주식기준 + 희석주식 Bridge

## Purpose / 목적

M22 builds a governed point-in-time common-share base and an explicit bridge toward fully diluted shares. It does not equate current common shares, historical EPS denominators, or historical dilution ratios with a valuation-date fully diluted denominator.

## Core semantic boundary / 핵심 의미경계

```text
current_common_shares != fully_diluted_shares
weighted_average_diluted_shares != current_common_shares
historical_dilution_factor != automatic current dilution adjustment
missing dilution category != zero
```

## SEC point-in-time base / SEC 시점 보통주 기준수

M22 v0.1 accepts only the exact DEI concept:

```text
dei:EntityCommonStockSharesOutstanding
```

The source mapping is isolated from M13 and M21 registries. Extraction requires an exact instant date and preserves accession, form, filed date, source snapshot/body hashes, and candidate authority.

Normalized output:

```text
current-common-shares-observation-v0.1
```

It is always:
- `INSTANT`
- exact-date
- noncanonical
- authority-preserving
- SHA-locked
- semantically marked as current common shares only

## Valuation share-base context / 가치평가 주식기준 context

Only a reviewed `NORMALIZED_FACT` observation can enter:

```text
valuation-share-base-context-v0.1
```

The context stores explicit `as_of` and `max_age_days`. Validation independently recomputes freshness from the source instant date. A stale base may remain visible but cannot support complete dilution coverage.

The context explicitly carries:

```text
current_common_shares_base = true
fully_diluted_shares = false
direct_bind_to_diluted_shares = false
```

## Explicit dilution adjustments / 명시적 희석조정

Each adjustment is a separate `dilution-adjustment-v0.1` object with:
- unique adjustment ID
- typed category
- nonnegative share amount
- explicit source SHA
- source description
- authority class
- adjustment SHA

Supported structural categories:

```text
options_treasury_stock_method
rsu_restricted_stock
warrants
convertibles_if_converted
contingent_shares
other_explicit
```

The builder creates candidate authority. Review must be explicit; calculation never upgrades evidence authority.

## Coverage assertion / Coverage 승인

A bridge may be declared complete only through a separate human, SHA-locked:

```text
dilution-coverage-assertion-v0.1
```

The assertion requires:
- fresh base context
- reviewed adjustment facts only
- reviewer
- timezone-aware approval time
- explicit coverage basis
- explicit review of all supported dilution categories
- exact base-context SHA
- exact adjustment SHA set

An empty adjustment list may still be complete only if the human coverage assertion explicitly records that all supported categories were reviewed and none require an adjustment. Missing categories are never silently treated as zero.

## Bridge / Bridge

Output:

```text
diluted-share-bridge-v0.1
```

Coverage states:

```text
BASE_ONLY
PARTIAL_DILUTION_COVERAGE
COMPLETE_REVIEWED_DILUTION_COVERAGE
CONFLICT_BLOCKED
```

Arithmetic:

```text
candidate_fully_diluted_shares
  = current_common_shares_base
  + sum(explicit selected adjustments)
```

This number is a **candidate calculation**. It becomes future-binding eligible only when:

```text
COMPLETE_REVIEWED_DILUTION_COVERAGE
+ FRESH base
+ all selected adjustments reviewed
+ valid human coverage assertion
```

`BASE_ONLY`, `PARTIAL_DILUTION_COVERAGE`, and `CONFLICT_BLOCKED` are never future-direct-bind eligible.

## Conflict rule / 충돌규칙

Multiple different adjustment objects using the same `adjustment_id` are treated as a conflict. In `CONFLICT_BLOCKED`, the bridge hides `candidate_fully_diluted_shares` instead of presenting a misleading total.

## M21 historical dilution relationship / M21 역사적 희석도 관계

M21 historical dilution evidence may be attached to M22 as reference context only:

```text
reference_only = true
auto_adjustment_created = false
```

The historical dilution factor never creates, scales, or estimates a current-period adjustment automatically.

## Nested validation / 중첩 검증

M22 embeds full source objects in the bridge:
- full base context
- all input adjustments
- reconciled adjustments
- complete coverage assertion when present
- full M21 historical reference when present

The bridge validator revalidates these nested objects and recomputes reconciliation, conflict state, arithmetic, coverage, authority, and eligibility. Re-signing only the outer bridge hash cannot legitimize a modified nested approval or source object.

## CLI

```text
share-sec-extract
share-normalize
share-observation-validate
share-base-context-build
share-base-context-validate
share-adjustment-build
share-adjustment-validate
share-coverage-assertion-build
share-coverage-assertion-validate
share-bridge-build
share-bridge-validate
```

## Web

```text
/shares
```

The `/shares` surface and `/api/shares/*` endpoints are calculate/validate only. They do not write Draft files, promote evidence, admit canonical state, or mutate repository state.

## What M22 does not yet do / M22가 아직 하지 않는 것

M22 does not directly write `equity.diluted_shares` into a Draft. A later milestone should integrate **only a complete, reviewed, fresh M22 bridge** into the existing M16/M17/M20 human-approved binding path.