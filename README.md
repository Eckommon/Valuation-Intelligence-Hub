# Valuation-Intelligence-Hub / 가치분석 인텔리전스 허브

> **Separate price from economic value, make assumptions explicit, and make valuation reproducible.**  
> **가격과 경제적 가치를 분리하고, 가정을 명시하며, 가치평가를 재현 가능하게 만든다.**

Valuation-Intelligence-Hub is a reproducible, evidence-grounded cross-asset valuation intelligence system connecting source evidence, normalization, governed derivation, Draft preparation, human review, and repository-controlled canonicalization.

## Core authority flow / 핵심 권위 흐름

```text
OFFICIAL / USER SOURCE
        ↓
IMMUTABLE SNAPSHOT / NOT CANONICAL
        ↓
EVIDENCE CANDIDATE / NOT CANONICAL
        ↓
NORMALIZED / DERIVED EVIDENCE / NOT CANONICAL
        ↓
GOVERNED BINDING CONTEXT / NOT CANONICAL
        ↓
DRAFT BINDING PROPOSAL / NOT CANONICAL
        ↓
HUMAN APPROVAL LOCK
        ↓
BOUND DRAFT RESULT / NOT CANONICAL
        ↓
DRAFT GOVERNANCE → PROMOTION → ADMISSION → guarded apply → PR/CI merge
        ↓
CANONICAL
```

Facts, calculations, derivations, binding contexts, proposals, and Draft application are intentionally separate authority states.

## Valuation kernel / 가치평가 커널

\[
FCFF = EBIT(1-T) + D\&A - CAPEX - \Delta NWC
\]

The Hub also supports reverse valuation and probability-weighted venture valuation. Existing company cases are versioned methodology references, not live investment recommendations.

## Install / 설치

```bash
python -m pip install -e ".[dev]"
```

## Governed capabilities / 거버넌스 기능

- M1–M12: valuation kernels, evidence governance, Draft/Candidate review, promotion/admission, guarded repository apply
- M13: immutable SEC CompanyFacts acquisition
- M14: immutable OpenDART financial-statement acquisition
- M15: period semantics, normalization, reconciliation, TTM
- M16: normalized-evidence → equity-FCFF Draft binding proposal v0.1
- M17: SHA-locked human approval + in-memory noncanonical Draft binding application
- M18: governed historical operating/net margin derivation separated from forecast assumptions
- M19: explicit interest-bearing-debt component evidence, normalization, completeness and aggregation
- M20: reviewed complete debt → `equity.debt` binding with human date assertion for unresolved report-stage dates
- M21: governed historical share-dilution reference evidence, explicitly separated from valuation-date fully diluted shares

## M20 — Reviewed debt → `equity.debt` binding

M20 connects only complete, reviewed M19 debt to the equity-FCFF Draft path.

```text
liabilities ≠ interest_bearing_debt
REPORT_STAGE_ONLY ≠ invented exact date
complete reviewed fresh debt → eligible for DIRECT_BIND
```

For `REPORT_STAGE_ONLY` debt, an explicit SHA-locked human date assertion is required. The debt-binding context independently recomputes freshness from `as_of` and the resolved period end. M20 preserves the original M16 v0.1 cash proposal path and adds a debt-aware v0.2 proposal that may replace only the `equity.debt` decision.

See [`docs/DEBT_DRAFT_BINDING.md`](docs/DEBT_DRAFT_BINDING.md).

## M21 — Historical dilution reference / 역사적 희석도 참조근거

M21 deliberately keeps historical EPS denominator evidence separate from valuation-date fully diluted shares.

```text
shares_outstanding != weighted_average_basic_shares
weighted_average_diluted_shares != valuation_date_fully_diluted_shares
historical_dilution_factor != valuation denominator
```

M21 v0.1 supports only exact SEC US-GAAP concepts:

```text
WeightedAverageNumberOfSharesOutstandingBasic
WeightedAverageNumberOfDilutedSharesOutstanding
```

Extraction requires an exact start/end period so quarterly and YTD 10-Q denominators cannot be conflated.

Normalized evidence remains duration-based and noncanonical. Historical dilution is derived only from exact same entity, unit, and full period identity:

```text
historical_dilution_factor
  = weighted_average_diluted_shares / weighted_average_basic_shares

historical_incremental_diluted_shares
  = weighted_average_diluted_shares - weighted_average_basic_shares
```

Every M21 derived result carries the fail-closed boundary:

```text
historical_only = true
valuation_date_direct_bind = false
forecast_direct_bind = false
shares_outstanding_substitution = false
```

Therefore `equity.diluted_shares` remains unresolved after M21. A future milestone must build valuation-date fully diluted shares from explicit instrument-level or equivalently governed evidence.

### M21 CLI

```text
dilution-sec-extract
dilution-normalize
dilution-observation-validate
dilution-derive
dilution-validate
```

### M21 Web

```text
/dilution
```

The dilution surface is calculate/validate only. There is no Draft mutation, promotion, admission, or canonical-write route.

See [`docs/SHARE_DILUTION_REFERENCE.md`](docs/SHARE_DILUTION_REFERENCE.md).

## Key semantic guardrails / 핵심 의미 안전장치

```text
liabilities                         ≠ debt
shares_outstanding                  ≠ diluted_shares
weighted_average_diluted_shares    ≠ valuation_date_fully_diluted_shares
historical revenue                  ≠ forecast revenue
historical margin                   ≠ forecast margin
missing debt component              ≠ zero
REPORT_STAGE_ONLY                   ≠ exact date
stale debt                          ≠ DIRECT_BIND
```

## Web product / Web 제품

```bash
vih web
```

Default: `http://127.0.0.1:8765`

```text
/source        — SEC source inspection
/dart-source   — OpenDART source inspection
/normalize     — financial normalization + TTM
/binding       — evidence → Draft binding proposal
/binding-apply — human approval + in-memory Draft binding
/derived       — governed historical derived evidence
/debt          — governed debt aggregation + M20 binding preparation
/dilution      — governed historical dilution reference evidence
```

## Milestones / 마일스톤

- [x] M1–M12 valuation/evidence governance + canonical admission/apply
- [x] M13 immutable SEC acquisition
- [x] M14 immutable OpenDART acquisition
- [x] M15 financial normalization + TTM
- [x] M16 governed evidence → Draft binding proposal
- [x] M17 human-approved noncanonical Draft binding application
- [x] M18 governed derived financial evidence + historical margins
- [x] M19 governed interest-bearing debt components + aggregation
- [x] M20 reviewed debt → `equity.debt` binding + human date assertion
- [ ] **M21 governed historical dilution reference evidence — active finalization**
- [ ] valuation-date fully diluted-share bridge
- [ ] first non-equity valuation adapter

## Canonical documentation / 정식 문서

- [`docs/EVIDENCE_POLICY.md`](docs/EVIDENCE_POLICY.md)
- [`docs/USER_DRAFTS.md`](docs/USER_DRAFTS.md)
- [`docs/PROMOTION_PROTOCOL.md`](docs/PROMOTION_PROTOCOL.md)
- [`docs/CANONICAL_ADMISSION.md`](docs/CANONICAL_ADMISSION.md)
- [`docs/GUARDED_ADMISSION_APPLY.md`](docs/GUARDED_ADMISSION_APPLY.md)
- [`docs/LIVE_EVIDENCE_SEC.md`](docs/LIVE_EVIDENCE_SEC.md)
- [`docs/LIVE_EVIDENCE_OPENDART.md`](docs/LIVE_EVIDENCE_OPENDART.md)
- [`docs/FINANCIAL_NORMALIZATION.md`](docs/FINANCIAL_NORMALIZATION.md)
- [`docs/DRAFT_BINDING.md`](docs/DRAFT_BINDING.md)
- [`docs/BINDING_APPLICATION.md`](docs/BINDING_APPLICATION.md)
- [`docs/DERIVED_FINANCIAL_EVIDENCE.md`](docs/DERIVED_FINANCIAL_EVIDENCE.md)
- [`docs/INTEREST_BEARING_DEBT.md`](docs/INTEREST_BEARING_DEBT.md)
- [`docs/DEBT_DRAFT_BINDING.md`](docs/DEBT_DRAFT_BINDING.md)
- [`docs/SHARE_DILUTION_REFERENCE.md`](docs/SHARE_DILUTION_REFERENCE.md)
- [`docs/M20_ACCEPTANCE.md`](docs/M20_ACCEPTANCE.md)
- [`docs/M20_IMPLEMENTATION_SUMMARY.md`](docs/M20_IMPLEMENTATION_SUMMARY.md)
- [`docs/M21_ACCEPTANCE.md`](docs/M21_ACCEPTANCE.md)
- [`docs/M21_IMPLEMENTATION_SUMMARY.md`](docs/M21_IMPLEMENTATION_SUMMARY.md)
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — canonical resume point / 정식 재개점
