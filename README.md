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
GOVERNED CONTEXT / NOT CANONICAL
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

Calculations never upgrade evidence authority by themselves.

## Valuation kernel / 가치평가 커널

\[
FCFF = EBIT(1-T) + D\&A - CAPEX - \Delta NWC
\]

The Hub also supports reverse valuation and probability-weighted venture valuation. Company cases are versioned methodology references, not live investment recommendations.

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
- M17: SHA-locked human approval + noncanonical Draft binding application
- M18: governed historical operating/net margin derivation
- M19: explicit interest-bearing-debt components and aggregation
- M20: reviewed complete debt → `equity.debt` binding with human date assertion where needed
- M21: governed historical share-dilution reference evidence
- M22: valuation-date current-common-share base + explicit diluted-share bridge foundation

## M20 — Reviewed debt binding

```text
liabilities ≠ interest_bearing_debt
REPORT_STAGE_ONLY ≠ invented exact date
complete reviewed fresh debt → eligible for DIRECT_BIND
```

M20 preserves M16 v0.1 cash semantics and adds a debt-aware v0.2 proposal. OpenDART report-stage-only dates require a separate human SHA lock. See [`docs/DEBT_DRAFT_BINDING.md`](docs/DEBT_DRAFT_BINDING.md).

## M21 — Historical dilution reference / 역사적 희석도 참조근거

```text
shares_outstanding != weighted_average_basic_shares
weighted_average_diluted_shares != valuation_date_fully_diluted_shares
historical_dilution_factor != valuation denominator
```

M21 accepts exact SEC weighted-average basic/diluted EPS denominator concepts with exact start/end periods. Its result is historical reference only:

```text
historical_only = true
valuation_date_direct_bind = false
forecast_direct_bind = false
shares_outstanding_substitution = false
```

See [`docs/SHARE_DILUTION_REFERENCE.md`](docs/SHARE_DILUTION_REFERENCE.md).

## M22 — Valuation-date share base + diluted-share bridge / 가치평가일 주식기준 + 희석주식 Bridge

M22 separates the point-in-time common-share base from explicit dilution adjustments and from the final valuation denominator.

```text
current_common_shares != fully_diluted_shares
weighted_average_diluted_shares != current_common_shares
historical_dilution_factor != automatic current dilution adjustment
missing dilution category != zero
```

### Current common-share base

M22 v0.1 uses only exact SEC:

```text
dei:EntityCommonStockSharesOutstanding
```

The normalized observation is exact-date `INSTANT` evidence. Only reviewed evidence can enter `valuation-share-base-context-v0.1`, whose freshness is independently recomputed from source date and `as_of`.

### Explicit adjustment ledger

Supported structural categories:

```text
options_treasury_stock_method
rsu_restricted_stock
warrants
convertibles_if_converted
contingent_shares
other_explicit
```

Each adjustment has an explicit source SHA, typed category, share amount, authority class, and its own integrity hash. Calculation never upgrades a candidate adjustment to reviewed authority.

### Coverage gate

```text
BASE_ONLY
PARTIAL_DILUTION_COVERAGE
COMPLETE_REVIEWED_DILUTION_COVERAGE
CONFLICT_BLOCKED
```

A candidate total may be calculated from the base plus selected explicit adjustments, but only **complete + reviewed + fresh + human coverage assertion** can be marked eligible for a future `equity.diluted_shares` binding integration.

Missing categories are never zero-imputed. Conflicting adjustment IDs hide the candidate total. M21 historical dilution may be attached as reference only and can never generate a current adjustment automatically.

M22 does **not** itself mutate a Draft or bind `equity.diluted_shares`; that remains a later governed integration step.

See [`docs/VALUATION_SHARE_BRIDGE.md`](docs/VALUATION_SHARE_BRIDGE.md).

## Key semantic guardrails / 핵심 의미 안전장치

```text
liabilities                         ≠ debt
shares_outstanding                  ≠ diluted_shares
current_common_shares               ≠ fully_diluted_shares
weighted_average_diluted_shares     ≠ current_common_shares
historical_dilution_factor          ≠ current dilution adjustment
missing dilution category           ≠ zero
historical revenue                  ≠ forecast revenue
historical margin                   ≠ forecast margin
REPORT_STAGE_ONLY                   ≠ exact date
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
/shares        — valuation-date common-share base + diluted-share bridge
```

M22 `/shares` and `/api/shares/*` are calculate/validate only; no Draft or canonical write path exists.

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
- [x] M21 governed historical dilution reference evidence
- [ ] **M22 valuation-date common-share base + diluted-share bridge foundation — active finalization**
- [ ] complete reviewed M22 bridge → `equity.diluted_shares` binding integration
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
- [`docs/VALUATION_SHARE_BRIDGE.md`](docs/VALUATION_SHARE_BRIDGE.md)
- [`docs/M20_ACCEPTANCE.md`](docs/M20_ACCEPTANCE.md)
- [`docs/M21_ACCEPTANCE.md`](docs/M21_ACCEPTANCE.md)
- [`docs/M22_ACCEPTANCE.md`](docs/M22_ACCEPTANCE.md)
- [`docs/M22_IMPLEMENTATION_SUMMARY.md`](docs/M22_IMPLEMENTATION_SUMMARY.md)
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — canonical resume point / 정식 재개점
