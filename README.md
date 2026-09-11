# Valuation-Intelligence-Hub / 가치분석 인텔리전스 허브

> **Separate price from economic value, make assumptions explicit, and make valuation reproducible.**  
> **가격과 경제적 가치를 분리하고, 가정을 명시하며, 가치평가를 재현 가능하게 만든다.**

Valuation-Intelligence-Hub is a reproducible, evidence-grounded cross-asset valuation intelligence system connecting official/user evidence, period normalization, valuation kernels, review governance, and repository-controlled canonicalization.

## Principles / 원칙

- Facts ≠ assumptions / 사실 ≠ 가정
- Official source ≠ automatic canonical fact / 공식 출처 ≠ 자동 정식 사실
- Arithmetic ≠ authority promotion / 산술 ≠ 권위 승격
- Similar accounting labels ≠ semantic equivalence / 유사 회계항목 ≠ 의미 동일성
- Every material fact needs provenance / 모든 중요 사실은 출처 필요
- Repository canonical state > AI recollection / 저장소 정식 상태 > AI 기억
- Same versioned inputs + model ⇒ reproducible output / 동일 버전 입력·모델 ⇒ 재현 결과

## Authority flow / 권위 흐름

```text
OFFICIAL / USER SOURCE
        ↓
IMMUTABLE SOURCE SNAPSHOT / NOT CANONICAL
        ↓
UNREVIEWED EVIDENCE CANDIDATE / NOT CANONICAL
        ↓
PERIOD NORMALIZATION / TTM / NOT CANONICAL
        ↓
DRAFT BINDING PROPOSAL / NOT CANONICAL
        ↓
DRAFT + EVIDENCE GOVERNANCE
        ↓
HUMAN SHA-256 REVIEW LOCK
        ↓
PROMOTION PACKAGE → ADMISSION PROPOSAL
        ↓
GUARDED admission/* APPLY
        ↓
PR + FULL CI + REVIEWED MERGE
        ↓
CANONICAL
```

## Valuation methods / 가치평가 방법

Operating-company FCFF:

\[
FCFF = EBIT(1-T) + D\&A - CAPEX - \Delta NWC
\]

The Hub also supports reverse valuation and probability-weighted venture valuation. Reference cases include LS ELECTRIC, LS Eco Energy, and Jet.AI; these are versioned methodology references, not live investment recommendations.

## Install / 설치

```bash
python -m pip install -e ".[dev]"
```

## Canonical execution / 정식 실행

```bash
vih list
vih validate KR_010120_LS_ELECTRIC
vih run KR_229640_LS_ECO_ENERGY
vih report US_JTAI_JET_AI
```

## User Draft → Canonical / 사용자 Draft → 정식

The governed workflow remains Draft → evidence-governed Candidate → human review → deterministic package → admission proposal → guarded `admission/*` apply → PR/CI/reviewed merge.

## M13 — SEC CompanyFacts live evidence

```bash
vih sec-fetch 0000320193 --user-agent "Valuation-Intelligence-Hub contact@example.com" \
  --output workspace/source_snapshots/AAPL-companyfacts.json
vih sec-snapshot-validate workspace/source_snapshots/AAPL-companyfacts.json
vih sec-extract workspace/source_snapshots/AAPL-companyfacts.json revenue
```

SEC responses are immutable noncanonical snapshots; extracted values remain unreviewed evidence candidates.

## M14 — OpenDART financial evidence

```bash
vih dart-fetch 00126380 --bsns-year 2026 --reprt-code 11012 --fs-div CFS \
  --api-key <LOCAL_SECRET> --output workspace/source_snapshots/dart.json
vih dart-snapshot-validate workspace/source_snapshots/dart.json
vih dart-extract workspace/source_snapshots/dart.json revenue --statement-section IS
```

API keys are transport-only. Persistent locators are sanitized, CFS/OFS and statement-section boundaries are explicit, account matching is exact, and conflicts fail closed.

## M15 — Financial evidence normalization + TTM

```text
FACT           → NORMALIZED_FACT
FACT_CANDIDATE → NORMALIZED_FACT_CANDIDATE
```

Period kinds: `INSTANT`, `DURATION_QUARTER`, `DURATION_YTD`, `DURATION_ANNUAL`, `DURATION_TTM`.

```bash
vih normalize-sec sec-candidate.json --period-kind DURATION_QUARTER
vih normalize-dart dart-candidate.json --amount-basis CURRENT
vih ttm-four-quarters q1.json q2.json q3.json q4.json
vih ttm-annual-bridge prior-fy.json current-ytd.json prior-ytd.json
vih normalize-reconcile observation-a.json observation-b.json
```

TTM formulas:

```text
TTM = Q[-3] + Q[-2] + Q[-1] + Q[0]
TTM = PRIOR_FY + CURRENT_YTD - PRIOR_COMPARABLE_YTD
```

M15 never invents missing period semantics or averages conflicts.

## M16 — Governed evidence → Draft binding proposal

M16 classifies normalized financial evidence against the 13 material equity-FCFF Draft inputs without mutating a Draft.

Binding states:

- `DIRECT_BIND`
- `REFERENCE_ONLY`
- `NEEDS_DERIVATION`
- `NEEDS_ASSUMPTION`
- `MISSING_REQUIRED`
- `CONFLICT_BLOCKED`
- `STALE_BLOCKED`

Semantic equivalence is mandatory:

```text
liabilities        ≠ debt
shares_outstanding ≠ diluted_shares
historical/TTM revenue ≠ forecast revenue
```

v0.1 deliberately permits only one kind of `DIRECT_BIND`: reviewed `NORMALIZED_FACT` + fresh exact-date `INSTANT cash` → `equity.cash`. Candidate evidence and report-stage-only freshness remain reference-only.

```bash
vih binding-build observations.json --as-of 2026-09-11 --max-age-days 550 > binding.json
vih binding-validate binding.json
```

The proposal is SHA-256 locked and always `canonical=false`. M16 has no Draft apply operation.

See [`docs/DRAFT_BINDING.md`](docs/DRAFT_BINDING.md).

## Web product / Web 제품

```bash
vih web
```

Default: `http://127.0.0.1:8765`

```text
/source       — SEC snapshot validation + extraction
/dart-source  — OpenDART snapshot validation + extraction
/normalize    — financial normalization + TTM + reconciliation
/binding      — evidence → Draft binding proposal build + validation
```

These surfaces are read/compute/proposal-only. There is no browser-origin source fetch, credential storage, binding apply, Draft mutation, promotion, admission, or canonical-write endpoint in M16.

## Milestones / 마일스톤

- [x] M1–M12 evidence governance, valuation kernels, product workflow, canonical admission/apply
- [x] M13 immutable SEC CompanyFacts acquisition
- [x] M14 immutable OpenDART financial-statement acquisition
- [x] M15 financial evidence normalization + period semantics + TTM
- [ ] **M16 governed normalized-evidence → Draft binding proposal — active finalization**
- [ ] explicit human-approved binding application to a noncanonical Draft
- [ ] first non-equity valuation adapter

## Canonical documentation / 정식 문서

- [`docs/FOUNDATION.md`](docs/FOUNDATION.md)
- [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md)
- [`docs/EVIDENCE_POLICY.md`](docs/EVIDENCE_POLICY.md)
- [`docs/AI_GROUNDING_POLICY.md`](docs/AI_GROUNDING_POLICY.md)
- [`docs/USER_DRAFTS.md`](docs/USER_DRAFTS.md)
- [`docs/PROMOTION_PROTOCOL.md`](docs/PROMOTION_PROTOCOL.md)
- [`docs/PROMOTION_PACKAGE.md`](docs/PROMOTION_PACKAGE.md)
- [`docs/CANONICAL_ADMISSION.md`](docs/CANONICAL_ADMISSION.md)
- [`docs/GUARDED_ADMISSION_APPLY.md`](docs/GUARDED_ADMISSION_APPLY.md)
- [`docs/LIVE_EVIDENCE_SEC.md`](docs/LIVE_EVIDENCE_SEC.md)
- [`docs/LIVE_EVIDENCE_OPENDART.md`](docs/LIVE_EVIDENCE_OPENDART.md)
- [`docs/FINANCIAL_NORMALIZATION.md`](docs/FINANCIAL_NORMALIZATION.md)
- [`docs/DRAFT_BINDING.md`](docs/DRAFT_BINDING.md)
- [`docs/M16_ACCEPTANCE.md`](docs/M16_ACCEPTANCE.md)
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — canonical resume point / 정식 재개점
