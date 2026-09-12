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

## Valuation kernels / 가치평가 커널

Operating-company FCFF:

\[
FCFF = EBIT(1-T) + D\&A - CAPEX - \Delta NWC
\]

The Hub also supports reverse valuation and probability-weighted venture valuation. Existing LS ELECTRIC, LS Eco Energy, and Jet.AI cases are versioned methodology references, not live investment recommendations.

## Install / 설치

```bash
python -m pip install -e ".[dev]"
```

## Governed capabilities / 거버넌스 기능

- M1–M12: valuation kernels, evidence governance, Draft/Candidate review, deterministic promotion/admission, guarded repository apply
- M13: immutable SEC CompanyFacts source acquisition
- M14: immutable OpenDART financial-statement acquisition
- M15: period semantics, normalization, reconciliation, TTM
- M16: normalized-evidence → equity-FCFF Draft binding proposal
- M17: SHA-locked human approval + in-memory noncanonical Draft binding application

## M18 — Governed derived financial evidence

M18 derives only arithmetic relationships that are historically exact and semantically explicit.

Supported v0.1 formulas:

```text
historical_operating_margin = operating_income / revenue
historical_net_income_margin = net_income / revenue
```

Inputs must match exactly on:

- entity ID
- financial scope/perimeter
- source monetary unit
- complete normalized period identity

Authority propagation:

```text
NORMALIZED_FACT + NORMALIZED_FACT
→ DERIVED_FACT

any NORMALIZED_FACT_CANDIDATE input
→ DERIVED_FACT_CANDIDATE
```

Every derived result remains `canonical=false` and carries:

```text
historical_only=true
forecast_direct_bind=false
```

Therefore historical margins are evidence context, **not forecast assumptions**.

### CLI

```bash
vih derive-operating-margin operating-income.json revenue.json > operating-margin.json
vih derive-net-margin net-income.json revenue.json > net-margin.json
vih derived-validate operating-margin.json
```

### Web

```text
/derived
POST /api/derived/calculate
POST /api/derived/validate
```

M18 Web is calculate/validate only. It has no file-write, Draft mutation, promotion, admission, or canonical-write operation.

See [`docs/DERIVED_FINANCIAL_EVIDENCE.md`](docs/DERIVED_FINANCIAL_EVIDENCE.md).

## Key semantic guardrails / 핵심 의미 안전장치

```text
liabilities        ≠ debt
shares_outstanding ≠ diluted_shares
historical/TTM revenue ≠ forecast revenue
historical operating margin ≠ forecast EBIT margin
historical tax evidence ≠ forecast tax assumption
```

The system prefers explicit unresolved states and governed derivations over invented mappings.

## Web product / Web 제품

```bash
vih web
```

Default: `http://127.0.0.1:8765`

```text
/source        — SEC snapshot validation + extraction
/dart-source   — OpenDART snapshot validation + extraction
/normalize     — financial normalization + TTM + reconciliation
/binding       — evidence → Draft binding proposal
/binding-apply — human approval + in-memory Draft binding application
/derived       — historical governed derived evidence
```

## Milestones / 마일스톤

- [x] M1–M12 valuation/evidence governance + canonical admission/apply
- [x] M13 immutable SEC acquisition
- [x] M14 immutable OpenDART acquisition
- [x] M15 financial normalization + TTM
- [x] M16 governed evidence → Draft binding proposal
- [x] M17 human-approved binding application to noncanonical Draft
- [ ] **M18 governed derived financial evidence + historical margins — active finalization**
- [ ] governed interest-bearing-debt component derivation
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
- [`docs/M18_ACCEPTANCE.md`](docs/M18_ACCEPTANCE.md)
- [`docs/M18_IMPLEMENTATION_SUMMARY.md`](docs/M18_IMPLEMENTATION_SUMMARY.md)
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — canonical resume point / 정식 재개점
