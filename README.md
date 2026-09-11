# Valuation-Intelligence-Hub / 가치분석 인텔리전스 허브

> **Separate price from economic value, make assumptions explicit, and make valuation reproducible.**  
> **가격과 경제적 가치를 분리하고, 가정을 명시하며, 가치평가를 재현 가능하게 만든다.**

Valuation-Intelligence-Hub is a reproducible, evidence-grounded cross-asset valuation intelligence system connecting source evidence, financial normalization, valuation Draft preparation, human review, and repository-controlled canonicalization.

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
DRAFT BINDING PROPOSAL / NOT CANONICAL
        ↓
HUMAN APPROVAL LOCK
        ↓
BOUND DRAFT RESULT / NOT CANONICAL
        ↓
DRAFT EVIDENCE GOVERNANCE + HUMAN REVIEW
        ↓
PROMOTION PACKAGE → ADMISSION → guarded branch apply → PR/CI merge
        ↓
CANONICAL
```

Facts, calculations, binding proposals, and Draft application are intentionally separate authority states.

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

## Existing governed capabilities / 기존 거버넌스 기능

- M1–M12: valuation kernels, evidence governance, Draft/Candidate review, deterministic promotion/admission, guarded `admission/*` repository apply
- M13: immutable SEC CompanyFacts source acquisition
- M14: immutable OpenDART financial-statement acquisition
- M15: period semantics, financial normalization, reconciliation, TTM
- M16: normalized-evidence → equity-FCFF Draft binding proposal

## M17 — Human-approved noncanonical Draft binding application

M17 takes an M16 binding proposal and an existing valid `equity_fcff` Draft, requires an explicit SHA-locked human approval, and returns a **new in-memory Draft result**. It does not overwrite the input Draft and does not create canonical state.

### Approval lock / 승인 잠금

`binding-approval-v0.1` binds:

- reviewer
- timezone-aware approval timestamp
- exact M16 proposal SHA-256
- exact target Draft-before SHA-256
- asserted entity ID + financial scope
- exact approved DIRECT_BIND field list
- approval SHA-256

Changing any locked element invalidates approval.

### Apply boundary / 적용 경계

Only M16 `DIRECT_BIND` decisions can be approved/applied. In v0.1 this currently means eligible `equity.cash` only.

The target Draft must match the proposal's monetary unit and explicitly asserted entity/scope. `REFERENCE_ONLY`, `NEEDS_DERIVATION`, `NEEDS_ASSUMPTION`, missing, stale, or conflict fields cannot be applied.

### CLI

```bash
vih binding-approval-build binding.json draft.json \
  --reviewer "Reviewer" \
  --target-entity-id DART_CORP:00126380 \
  --target-financial-scope CFS \
  --approved-field equity.cash \
  --approved-at 2026-09-11T17:50:00+09:00 > approval.json

vih binding-approval-validate approval.json binding.json draft.json
vih binding-apply binding.json draft.json approval.json > bound-result.json
vih bound-draft-validate bound-result.json
```

`bound-draft-result-v0.1` embeds the proposal, approval, Draft before/after, exact applied diffs with source observation hashes, unresolved binding matrix, and result SHA-256. It remains `canonical=false`.

See [`docs/BINDING_APPLICATION.md`](docs/BINDING_APPLICATION.md).

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
```

The M17 Web apply endpoint returns JSON only. It has no filesystem Draft overwrite, promotion, admission, or canonical-write operation.

## Key semantic guardrails / 핵심 의미 안전장치

```text
liabilities        ≠ debt
shares_outstanding ≠ diluted_shares
historical/TTM revenue ≠ forecast revenue
```

The system prefers explicit unresolved states and human assumptions over invented mappings.

## Milestones / 마일스톤

- [x] M1–M12 valuation/evidence governance + canonical admission/apply
- [x] M13 immutable SEC acquisition
- [x] M14 immutable OpenDART acquisition
- [x] M15 financial normalization + TTM
- [x] M16 governed evidence → Draft binding proposal
- [ ] **M17 human-approved binding application to noncanonical Draft — active finalization**
- [ ] governed derivation adapters for semantically derivable model inputs
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
- [`docs/M17_ACCEPTANCE.md`](docs/M17_ACCEPTANCE.md)
- [`docs/M17_IMPLEMENTATION_SUMMARY.md`](docs/M17_IMPLEMENTATION_SUMMARY.md)
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — canonical resume point / 정식 재개점
