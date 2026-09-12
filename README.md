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

The Hub also supports reverse valuation and probability-weighted venture valuation. Existing LS ELECTRIC, LS Eco Energy, and Jet.AI cases are versioned methodology references, not live investment recommendations.

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

## M20 — Reviewed debt → `equity.debt` binding

M20 connects only **complete, reviewed M19 debt** to the equity-FCFF Draft path.

```text
liabilities ≠ interest_bearing_debt
REPORT_STAGE_ONLY ≠ invented exact date
complete reviewed fresh debt → eligible for DIRECT_BIND
```

### Date resolution / 날짜 해소

For debt whose source period is already `EXACT`, M20 uses the source period end directly and forbids a human assertion from overriding it.

For OpenDART-style `REPORT_STAGE_ONLY` debt, M20 requires a separate noncanonical `debt-date-assertion-v0.1`. It SHA-locks reviewer, approval timestamp, exact M19 debt hash, entity/scope, original period identity, asserted period-end date, and human review basis.

No assertion means no resolved exact date and therefore no binding-ready context.

### Binding context / 바인딩 context

`debt-binding-context-v0.1` is created only from:

```text
COMPLETE_CORE_COMPONENTS
+ DERIVED_FACT
+ M19 Draft-eligibility=true
```

Freshness is evaluated after exact date resolution. Fresh debt is eligible; stale debt remains `STALE_BLOCKED`.

Partial, conflict-blocked, or candidate debt is rejected before a binding context can be produced.

### Proposal compatibility / Proposal 호환성

The historical M16 `build_binding_proposal()` remains unchanged and still produces `draft-binding-proposal-v0.1`.

M20 adds `draft-binding-proposal-v0.2`, which embeds the complete v0.1 proposal and complete debt binding context, then changes **only** the `equity.debt` decision. Every other material-field decision must remain identical to v0.1.

This preserves old cash behavior while adding an auditable debt path.

### Human approval and apply / 인간 승인·적용

M20 reuses the existing M17 `binding-approval-v0.1` contract. When v0.2 marks `equity.debt` as `DIRECT_BIND`, a human may explicitly approve that field.

Debt applied-diff lineage preserves:

```text
debt binding context SHA-256
M19 source debt SHA-256
date assertion SHA-256 (when required)
```

The source Draft is never mutated; the output remains noncanonical and in-memory.

### CLI

```text
debt-date-assertion-build
debt-date-assertion-validate
debt-binding-context-build
debt-binding-context-validate
binding-build-with-debt
binding-validate
binding-approval-build
binding-approval-validate
binding-apply
bound-draft-validate
```

### Web

The `/debt` Lab remains calculate/validate-only and now includes M20 preparation endpoints:

```text
POST /api/debt/date-assertion-build
POST /api/debt/date-assertion-validate
POST /api/debt/binding-context-build
POST /api/debt/binding-context-validate
POST /api/debt/binding-proposal-build
POST /api/debt/binding-proposal-validate
```

There is no Draft-file write, admission, promotion, or canonical-write route.

See [`docs/DEBT_DRAFT_BINDING.md`](docs/DEBT_DRAFT_BINDING.md).

## Key semantic guardrails / 핵심 의미 안전장치

```text
liabilities             ≠ debt
shares_outstanding      ≠ diluted_shares
historical revenue      ≠ forecast revenue
historical margin       ≠ forecast margin
missing debt component  ≠ zero
REPORT_STAGE_ONLY       ≠ exact date
stale debt              ≠ DIRECT_BIND
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
- [ ] **M20 reviewed debt → `equity.debt` binding + human date assertion — active finalization**
- [ ] governed diluted-share evidence/derivation
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
- [`docs/M20_ACCEPTANCE.md`](docs/M20_ACCEPTANCE.md)
- [`docs/M20_IMPLEMENTATION_SUMMARY.md`](docs/M20_IMPLEMENTATION_SUMMARY.md)
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — canonical resume point / 정식 재개점
