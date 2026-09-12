# Governed Share-Dilution Reference Evidence / 거버넌스 희석주식 참조근거

## Purpose / 목적

M21 adds a governed historical dilution-reference layer for SEC filers. It deliberately does **not** solve valuation-date fully diluted shares.

M21은 SEC 공시기업의 역사적 희석도 참조근거 계층을 추가합니다. valuation-date 완전희석주식수를 직접 확정하는 단계가 아닙니다.

## Semantic boundary / 의미경계

```text
shares_outstanding != weighted_average_basic_shares
weighted_average_diluted_shares != valuation_date_fully_diluted_shares
historical_dilution_factor != valuation denominator
```

SEC weighted-average share counts are duration denominators used for EPS. They are useful evidence about historical dilution pressure, but they are not point-in-time fully diluted shares.

## Exact SEC concepts / 정확한 SEC concept

M21 v0.1 supports only:

```text
us-gaap:WeightedAverageNumberOfSharesOutstandingBasic
us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding
```

Unit must be `shares`. Source extraction is isolated from M13 and does not mutate the M13 registry.

OpenDART is intentionally unsupported in v0.1 because M21 does not infer denominator shares from EPS or current shares.

## Period safety / 기간 안전성

Extraction requires explicit `period_start` and `period_end`. The selection rule is:

```text
EXACT_START_END_THEN_LATEST_FILED
```

This prevents a 10-Q quarterly denominator from being mixed with a YTD denominator that shares the same period end.

Normalized period kinds are:

```text
DURATION_QUARTER
DURATION_YTD
DURATION_ANNUAL
```

All normalized observations preserve exact start/end dates and `date_precision=EXACT`.

## Authority flow / 권위 흐름

```text
SEC immutable snapshot
  ↓
share-dilution-candidate-v0.1
  ↓
share-dilution-observation-v0.1
  ↓
historical-dilution-evidence-v0.1
```

No step above is canonical. Arithmetic never upgrades authority.

```text
NORMALIZED_FACT + NORMALIZED_FACT
  → DERIVED_FACT

any NORMALIZED_FACT_CANDIDATE input
  → DERIVED_FACT_CANDIDATE
```

## Historical dilution derivation / 역사적 희석도 파생

For exact same entity, unit, and complete period identity:

```text
historical_dilution_factor
  = weighted_average_diluted_shares
    / weighted_average_basic_shares

historical_incremental_diluted_shares
  = weighted_average_diluted_shares
    - weighted_average_basic_shares
```

Validation requires:

- basic shares > 0
- diluted shares >= basic shares
- exact entity match
- exact unit match
- exact complete period match
- valid source observation SHA lineage

## Non-binding contract / 비바인딩 계약

Every derived M21 result carries:

```json
{
  "historical_only": true,
  "valuation_date_direct_bind": false,
  "forecast_direct_bind": false,
  "shares_outstanding_substitution": false
}
```

Therefore M21 does not change the M16/M20 state of `equity.diluted_shares`: it remains unresolved until a future valuation-date dilution policy is implemented.

## CLI

```bash
vih dilution-sec-extract snapshot.json weighted_average_basic_shares \
  --period-start 2026-04-01 --period-end 2026-06-30

vih dilution-normalize candidate.json
vih dilution-observation-validate observation.json
vih dilution-derive basic.json diluted.json
vih dilution-validate historical-dilution.json
```

## Web

```text
/dilution
```

The Web surface is read/calculate/validate only. It has no Draft mutation, promotion, admission, or canonical-write route.

## Schemas / 스키마

- `schemas/share_dilution_observation.schema.json`
- `schemas/historical_dilution_evidence.schema.json`

## What M21 does not do / M21이 하지 않는 것

M21 does not:

- substitute shares outstanding for diluted shares;
- treat weighted-average diluted shares as a valuation-date denominator;
- infer option/RSU/convertible dilution from EPS;
- forecast future dilution;
- mutate a Draft;
- create canonical valuation state.

A future milestone must model valuation-date fully diluted shares from explicit instrument-level or equivalently governed evidence.