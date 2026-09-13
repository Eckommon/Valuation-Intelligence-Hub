# Minority-Interest FACT Binding / 비지배지분 FACT 바인딩

## Purpose / 목적

M28 closes the final equity-FCFF material-field gap by governing valuation-date noncontrolling/minority interest as a source-backed balance-sheet fact and binding only a reviewed, fresh, eligible package into `equity.minority_interest`.

M28은 가치평가일 비지배지분을 출처기반 재무상태표 사실로 거버넌스하고, 검토완료·최신·적격 패키지만 `equity.minority_interest`에 연결한다.

## Semantic boundary / 의미경계

```text
total equity != minority interest
parent-attributable equity != minority interest
liabilities != minority interest
missing evidence != zero minority interest
minority-interest FACT != analyst assumption
```

Explicit zero is valid evidence. Missing evidence is not zero.

명시적 0은 유효한 근거지만, 근거 누락은 0이 아니다.

## Exact source adapters / 정확한 source adapter

M28 does not modify the historical M13/M14 metric registries. It reads their immutable snapshots through isolated adapters.

M28은 기존 M13/M14 metric registry를 변경하지 않고 immutable snapshot 위 별도 adapter를 사용한다.

### SEC

```text
us-gaap:NonredeemableNoncontrollingInterest
```

- consolidated scope only
- exact instant fact only
- USD CompanyFacts unit path
- allowed filing forms are explicitly bounded
- equal-precedence conflicting values fail closed
- redeemable NCI is outside the v0.1 field boundary

### OpenDART

```text
ifrs-full_NoncontrollingInterests
```

- `CFS` only
- balance-sheet (`BS`) row only
- exact account ID only
- `thstrm_amount` only
- missing or conflicting rows fail closed

## Evidence lifecycle / 근거 수명주기

```text
immutable SEC/OpenDART snapshot
        ↓
minority-interest-candidate-v0.1
FACT_CANDIDATE
        ↓
minority-interest-observation-v0.1
NORMALIZED_FACT_CANDIDATE
        ↓
minority-interest-review-assertion-v0.1
SHA-locked human review
        ↓
reviewed-minority-interest-fact-v0.1
NORMALIZED_FACT / canonical=false
        ↓
draft-binding-proposal-v0.8
        ↓
M17-family binding approval/apply
        ↓
noncanonical bound Draft result
```

Calculation and normalization never upgrade authority by themselves.

## Date semantics / 날짜 의미론

SEC exact instant evidence uses `SOURCE_EXACT`; a human date assertion is forbidden.

OpenDART financial-statement snapshots expose report-stage semantics rather than a guaranteed exact calendar period end. Therefore `REPORT_STAGE_ONLY` requires a separate timezone-aware, SHA-locked human `resolved_period_end` assertion. The exact date is not invented automatically.

Freshness is independently recomputed from:

```text
resolved_period_end
valuation as_of
max_age_days
```

A period end after `as_of` fails closed. A stale reviewed package remains visible but is not binding-eligible.

## v0.8 binding / v0.8 바인딩

M28 accepts only a validated `draft-binding-proposal-v0.7` base and may replace exactly one material-field decision:

```text
equity.minority_interest
```

Every other v0.7 decision must remain unchanged. Exact compatibility is required for entity ID, consolidated financial scope, currency, and valuation `as_of`.

The v0.8 proposal preserves:

```text
minority-interest package SHA
normalized observation SHA
source snapshot SHA
human review assertion SHA
resolved period end + date-resolution method
```

## Apply / 적용

Human binding approval remains mandatory. Applying M28 changes only:

```text
draft["equity"]["minority_interest"]
```

The input Draft remains unchanged; only a noncanonical in-memory result is produced. Applied diff lineage is independently validated, and the M26 unique-diff-field guard remains active.

## Interfaces / 인터페이스

CLI/Web are preparation and validation surfaces. They do not directly write Draft files, promote evidence, admit canonical state, or write canonical repository records.

```text
vih minority-sec-extract
vih minority-dart-extract
vih minority-candidate-validate
vih minority-normalize
vih minority-observation-validate
vih minority-review-build
vih minority-review-validate
vih minority-finalize
vih minority-validate
vih binding-build-with-minority-interest
vih binding-validate
```

Web:

```text
/minority-interest
/api/minority-interest/*
```
