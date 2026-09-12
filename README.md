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
NORMALIZED OBSERVATION / TTM / NOT CANONICAL
        ↓
GOVERNED DERIVED EVIDENCE / NOT CANONICAL
        ↓
DRAFT BINDING PROPOSAL / NOT CANONICAL
        ↓
HUMAN APPROVAL LOCK
        ↓
BOUND DRAFT RESULT / NOT CANONICAL
        ↓
DRAFT EVIDENCE GOVERNANCE + HUMAN REVIEW
        ↓
PROMOTION → ADMISSION → guarded branch apply → PR/CI merge
        ↓
CANONICAL
```

Facts, calculations, derivations, binding proposals, and Draft application are intentionally separate authority states.

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
- M16: normalized-evidence → equity-FCFF Draft binding proposal
- M17: SHA-locked human approval + in-memory noncanonical Draft binding application
- M18: governed historical operating/net margin derivation, explicitly separated from forecast assumptions

## M19 — Governed interest-bearing debt components

M19 creates interest-bearing debt only from explicit component evidence.

```text
liabilities ≠ interest_bearing_debt
missing ≠ zero
```

Core v0.1 components:

```text
short_term_borrowings
current_portion_long_term_borrowings
long_term_borrowings
current_portion_bonds
bonds_noncurrent
```

### Source mapping / 원천 매핑

M19 uses a **separate debt source registry** so M13/M14 registries remain unchanged.

OpenDART supports all five components with exact IFRS account IDs and exact Korean account-name fallback. SEC CompanyFacts v0.1 intentionally supports only exact `us-gaap:ShortTermBorrowings`; broad `LongTermDebt*` concepts are not forced into narrower borrowing/bond categories.

### Isolated normalization / 분리 정규화

Debt source candidates normalize into:

```text
debt-component-observation-v0.1
```

Each observation is `INSTANT`, `canonical=false`, SHA-locked, and preserves exact source concept/account lineage.

### Aggregation coverage / 집계 coverage

```text
COMPLETE_CORE_COMPONENTS
PARTIAL_COMPONENTS
CONFLICT_BLOCKED
```

- **Complete:** all five explicit components, no conflict → final debt value exists.
- **Partial:** `known_component_sum` is visible, but final debt value remains `null`.
- **Conflict:** both known sum and final debt value remain `null`.

Authority never upgrades by summation:

```text
all NORMALIZED_FACT inputs → DERIVED_FACT
any candidate input         → DERIVED_FACT_CANDIDATE
```

Only `COMPLETE_CORE_COMPONENTS + DERIVED_FACT` is marked eligible for a **future** governed Draft binding. M19 itself does not mutate a Draft.

Lease liabilities remain explicitly excluded pending a separate policy.

### CLI

```bash
vih debt-sec-extract sec-snapshot.json short_term_borrowings
vih debt-dart-extract dart-snapshot.json long_term_borrowings
vih debt-normalize debt-candidate.json
vih debt-component-validate debt-observation.json
vih debt-aggregate debt-observations.json
vih debt-validate debt.json
```

### Web

```text
/debt
POST /api/debt/aggregate
POST /api/debt/validate
```

Web is calculate/validate only; it has no Draft mutation or canonical-write path.

See [`docs/INTEREST_BEARING_DEBT.md`](docs/INTEREST_BEARING_DEBT.md).

## Key semantic guardrails / 핵심 의미 안전장치

```text
liabilities        ≠ debt
shares_outstanding ≠ diluted_shares
historical revenue ≠ forecast revenue
historical margin  ≠ forecast margin
missing component  ≠ zero
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
/debt          — governed interest-bearing debt aggregation
```

## Milestones / 마일스톤

- [x] M1–M12 valuation/evidence governance + canonical admission/apply
- [x] M13 immutable SEC acquisition
- [x] M14 immutable OpenDART acquisition
- [x] M15 financial normalization + TTM
- [x] M16 governed evidence → Draft binding proposal
- [x] M17 human-approved noncanonical Draft binding application
- [x] M18 governed derived financial evidence + historical margins
- [ ] **M19 governed interest-bearing debt components + aggregation — active finalization**
- [ ] governed reviewed-debt → Draft binding integration
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
- [`docs/M19_ACCEPTANCE.md`](docs/M19_ACCEPTANCE.md)
- [`docs/M19_IMPLEMENTATION_SUMMARY.md`](docs/M19_IMPLEMENTATION_SUMMARY.md)
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — canonical resume point / 정식 재개점
