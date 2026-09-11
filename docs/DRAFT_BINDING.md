# Governed Normalized-Evidence → Draft Binding / 정규화 근거 → Draft 바인딩

## Purpose / 목적

M16 bridges reviewed/normalized financial evidence into equity-FCFF Draft preparation without silently converting facts into assumptions or mapping semantically different concepts.

M16은 검토·정규화된 재무근거를 equity-FCFF Draft 준비와 연결하되, 사실을 가정으로 바꾸거나 의미가 다른 개념을 자동 대응하지 않는다.

## Proposal-only boundary / 제안 전용 경계

`draft-binding-proposal-v0.1` is always `canonical=false`. M16 does not mutate a Draft, write a file, promote evidence, or write canonical repository state.

```text
NORMALIZED EVIDENCE
       ↓
BINDING PROPOSAL / NOT CANONICAL
       ↓
HUMAN REVIEW / FUTURE EXPLICIT APPLY PHASE
```

There is intentionally no M16 apply operation.

## Semantic equivalence rule / 의미 동일성 규칙

`DIRECT_BIND` requires exact semantic equivalence. Similar-looking accounting values are not interchangeable.

Explicitly blocked:

```text
liabilities       ≠ debt
shares_outstanding ≠ diluted_shares
historical/TTM revenue ≠ forecast revenue
historical operating margin ≠ forecast EBIT margin
historical tax rate ≠ forecast tax rate
```

## Binding states / 바인딩 상태

- `DIRECT_BIND` — exact semantic identity, reviewed authority, compatible period, fresh evidence
- `REFERENCE_ONLY` — useful evidence context but unsafe to bind automatically
- `NEEDS_DERIVATION` — requires an explicit governed transformation
- `NEEDS_ASSUMPTION` — requires analyst/model assumption
- `MISSING_REQUIRED` — required Draft input lacks admissible evidence
- `CONFLICT_BLOCKED` — multiple unreconciled observations block use
- `STALE_BLOCKED` — exact-dated evidence exceeds freshness policy

## v0.1 direct binding / v0.1 직접 바인딩

M16 v0.1 is intentionally conservative. The only eligible direct binding is:

```text
reviewed NORMALIZED_FACT
+ metric = cash
+ period.kind = INSTANT
+ date_precision = EXACT
+ freshness = FRESH
→ equity.cash
```

`NORMALIZED_FACT_CANDIDATE` cannot direct-bind.

OpenDART observations with report-stage-only date precision remain reference-only for automatic freshness approval because M16 does not invent dates.

## Equity-FCFF completeness matrix / 완전성 matrix

Every proposal classifies exactly these 13 material inputs:

1. `market_price`
2. `equity.diluted_shares`
3. `equity.debt`
4. `equity.cash`
5. `equity.minority_interest`
6. `scenario.wacc`
7. `scenario.terminal_growth`
8. `scenario.years.revenue`
9. `scenario.years.ebit_margin`
10. `scenario.years.tax_rate`
11. `scenario.years.depreciation_amortization`
12. `scenario.years.capex`
13. `scenario.years.delta_nwc`

The system prefers an explicit unresolved state over an invented value.

## Freshness / 최신성

Proposal construction requires an explicit `as_of` date and a versioned `max_age_days` policy. Exact-date observations receive a deterministic age. Evidence dated after `as_of` fails closed. Report-stage-only observations return `UNKNOWN_DATE_PRECISION` and cannot receive automatic fresh approval.

## Identity and conflict controls / 식별·충돌 통제

All observations in one v0.1 proposal must share:

- entity identity
- financial scope/perimeter
- monetary unit for monetary metrics

Multiple differing observations for the same metric are treated as unresolved conflict until reconciled upstream. M16 never averages them.

## Integrity / 무결성

The proposal records exact source observation SHA-256 values and locks the complete proposal with `proposal_sha256`. Any policy, context, decision, identity, or completeness mutation invalidates validation.

## CLI

```bash
vih binding-build observations.json --as-of 2026-09-11 --max-age-days 550 > binding.json
vih binding-validate binding.json
```

`observations.json` is a non-empty JSON array of M15 normalized observations.

## Web

```text
/binding
POST /api/binding/build
POST /api/binding/validate
```

The Web surface is proposal-only. There is no `/api/binding/apply`, Draft mutation, file write, promotion, admission, or canonical-write endpoint.
