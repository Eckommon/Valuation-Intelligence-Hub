# Interest-Bearing Debt Evidence v0.1 / 이자부채 근거 v0.1

## Purpose / 목적

M19 creates debt only from explicit interest-bearing debt components. **Total liabilities are never relabeled as debt.** Missing components remain missing, conflicts block totals, and lease liabilities remain excluded until a separate policy is ratified.

M19는 명시적 이자부채 구성요소로만 debt를 구성합니다. **총부채를 debt로 재명명하지 않습니다.** 누락은 누락으로 유지하고, 충돌은 합계를 차단하며, 리스부채는 별도 정책 전까지 제외합니다.

## Core component ontology / 핵심 구성요소

```text
short_term_borrowings
current_portion_long_term_borrowings
long_term_borrowings
current_portion_bonds
bonds_noncurrent
```

## Source mappings / 원천 매핑

### OpenDART

M19 uses a separate debt mapping registry rather than mutating the M14 registry.

```text
short_term_borrowings
  ifrs-full_ShorttermBorrowings
  단기차입금

current_portion_long_term_borrowings
  ifrs-full_CurrentPortionOfLongtermBorrowings
  유동성장기차입금 / 유동성 장기차입금

long_term_borrowings
  ifrs-full_LongtermBorrowings
  장기차입금

current_portion_bonds
  ifrs-full_CurrentPortionOfBondsIssued
  유동성사채 / 유동성 사채

bonds_noncurrent
  ifrs-full_BondsIssued
  사채
```

Selection remains exact account ID first, then exact account-name fallback. No fuzzy matching.

### SEC CompanyFacts

M19 v0.1 intentionally supports only:

```text
short_term_borrowings → us-gaap:ShortTermBorrowings
```

Broad concepts such as `LongTermDebtCurrent` or `LongTermDebtNoncurrent` are not relabeled as narrow borrowing/bond components because that can mix instrument classes or create double counting.

## Isolated normalization / 분리된 정규화

M19 does not alter the M13/M14/M15 registries. Debt source candidates normalize into:

```text
debt-component-observation-v0.1
```

Every component is an `INSTANT` observation and preserves exact source concept/account lineage, entity, scope, unit, period identity, source candidate hash, and observation hash.

## Aggregation / 집계

Compatible observations must have exactly the same:

- entity ID
- financial scope/perimeter
- unit/currency
- complete INSTANT period identity

Coverage states:

```text
COMPLETE_CORE_COMPONENTS
PARTIAL_COMPONENTS
CONFLICT_BLOCKED
```

### Complete

All five components are explicitly evidenced with no conflict.

```text
known_component_sum = sum(all five)
interest_bearing_debt_value = known_component_sum
```

### Partial

At least one core component is absent.

```text
known_component_sum = sum(explicitly present components)
interest_bearing_debt_value = null
```

A missing component is never treated as zero.

### Conflict blocked

At least one same-component group contains different values at the same identity.

```text
known_component_sum = null
interest_bearing_debt_value = null
```

No conflicted debt total is exposed.

## Authority / 권위

```text
all NORMALIZED_FACT inputs
→ DERIVED_FACT

any NORMALIZED_FACT_CANDIDATE input
→ DERIVED_FACT_CANDIDATE
```

Equal-value duplicate evidence may select a reviewed representation for the component row, but the aggregate remains candidate if any input evidence was candidate.

## Draft boundary / Draft 경계

`eligible_for_draft_direct_bind=true` only when:

```text
coverage = COMPLETE_CORE_COMPONENTS
AND class = DERIVED_FACT
```

M19 does **not** apply debt to a Draft. A later mission must explicitly integrate eligible reviewed debt into the M16/M17 binding and approval pipeline.

## Lease policy / 리스 정책

M19 v0.1 records:

```text
lease_liabilities_included=false
lease_policy=EXCLUDED_PENDING_EXPLICIT_POLICY
```

Finance/operating lease debt treatment requires a separate, explicit accounting/valuation policy.

## CLI

```bash
vih debt-sec-extract sec-snapshot.json short_term_borrowings > debt-candidate.json
vih debt-dart-extract dart-snapshot.json long_term_borrowings > debt-candidate.json
vih debt-normalize debt-candidate.json > debt-observation.json
vih debt-component-validate debt-observation.json
vih debt-aggregate debt-observations.json > debt.json
vih debt-validate debt.json
```

## Web

```text
/debt
POST /api/debt/aggregate
POST /api/debt/validate
```

Web is calculate/validate only. No file write, Draft mutation, promotion, admission, or canonical write is available.
