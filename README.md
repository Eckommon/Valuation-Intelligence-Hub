# Valuation-Intelligence-Hub / 가치분석 인텔리전스 허브

> **Separate price from economic value, make assumptions explicit, and make valuation reproducible.**  
> **가격과 경제적 가치를 분리하고, 가정을 명시하며, 가치평가를 재현 가능하게 만든다.**

Valuation-Intelligence-Hub is a reproducible, evidence-grounded cross-asset valuation intelligence system connecting official/user evidence, period normalization, valuation kernels, review governance, and repository-controlled canonicalization.

## Principles / 원칙

- Facts ≠ assumptions / 사실 ≠ 가정
- Official source ≠ automatic canonical fact / 공식 출처 ≠ 자동 정식 사실
- Arithmetic ≠ authority promotion / 산술 ≠ 권위 승격
- Every material fact needs provenance / 모든 중요 사실은 출처 필요
- Repository canonical state > AI recollection / 저장소 정식 상태 > AI 기억
- Same versioned inputs + model ⇒ reproducible output / 동일 버전 입력·모델 ⇒ 재현 결과
- One kernel, multiple interfaces / 하나의 커널, 여러 인터페이스

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

## Reference valuation methods / 가치평가 방법

Operating-company FCFF:

\[
FCFF = EBIT(1-T) + D\&A - CAPEX - \Delta NWC
\]

The Hub also supports reverse valuation and probability-weighted venture valuation.

Reference cases: LS ELECTRIC, LS Eco Energy, and Jet.AI. These are versioned methodology references, not live investment recommendations or target prices.

## Install / 설치

```bash
python -m pip install -e ".[dev]"
```

## Canonical cases / 정식 사례

```bash
vih list
vih validate KR_010120_LS_ELECTRIC
vih run KR_229640_LS_ECO_ENERGY
vih report US_JTAI_JET_AI
```

## User Draft → Canonical / 사용자 Draft → 정식

```bash
vih draft-template equity_fcff > workspace/user_cases/my_company.json
vih draft-validate workspace/user_cases/my_company.json
vih draft-run workspace/user_cases/my_company.json

vih candidate-build workspace/user_cases/my_company.json > workspace/user_cases/candidate.json
vih candidate-validate workspace/user_cases/candidate.json
vih promotion-check workspace/user_cases/candidate.json

vih package-build workspace/user_cases/candidate.json \
  --case-id KR_EXAMPLE_COMPANY --name-en "Example Company" --name-ko "예시회사" \
  --asset-class public_equity > workspace/user_cases/package.json

vih admission-build workspace/user_cases/package.json > workspace/user_cases/admission.json
vih admission-validate workspace/user_cases/admission.json
```

M12 repository apply is restricted to explicit `admission/*` branches/worktrees and remains PR/CI/review gated.

## M13 — SEC CompanyFacts live evidence

```bash
vih sec-fetch 0000320193 \
  --user-agent "Valuation-Intelligence-Hub contact@example.com" \
  --output workspace/source_snapshots/AAPL-companyfacts.json
vih sec-snapshot-validate workspace/source_snapshots/AAPL-companyfacts.json
vih sec-extract workspace/source_snapshots/AAPL-companyfacts.json revenue
```

SEC responses are immutable noncanonical snapshots. Extracted facts remain unreviewed candidates.

## M14 — OpenDART financial evidence

```bash
vih dart-fetch 00126380 --bsns-year 2026 --reprt-code 11012 --fs-div CFS \
  --api-key <LOCAL_SECRET> --output workspace/source_snapshots/dart.json
vih dart-snapshot-validate workspace/source_snapshots/dart.json
vih dart-extract workspace/source_snapshots/dart.json revenue --statement-section IS
```

OpenDART controls include transport-only API keys, sanitized locators, exact request identity, CFS/OFS separation, statement-section boundaries, exact account mapping, immutable raw-body/snapshot hashes, and fail-closed conflicts.

## M15 — Financial evidence normalization + TTM

M15 converts raw SEC/OpenDART evidence candidates into period-aware observations without upgrading evidence authority.

```text
FACT           → NORMALIZED_FACT
FACT_CANDIDATE → NORMALIZED_FACT_CANDIDATE
```

Supported period kinds:

- `INSTANT`
- `DURATION_QUARTER`
- `DURATION_YTD`
- `DURATION_ANNUAL`
- `DURATION_TTM`

SEC 10-Q duration facts require explicit quarter/YTD declaration. OpenDART uses report code plus `CURRENT`/`CUMULATIVE` amount basis. Exact dates are not invented where only report-stage semantics exist.

CLI:

```bash
vih normalize-sec sec-candidate.json --period-kind DURATION_QUARTER
vih normalize-dart dart-candidate.json --amount-basis CURRENT
vih normalize-validate observation.json
vih ttm-four-quarters q1.json q2.json q3.json q4.json
vih ttm-annual-bridge prior-fy.json current-ytd.json prior-ytd.json
vih ttm-validate ttm.json
vih normalize-reconcile observation-a.json observation-b.json
```

TTM formulas:

```text
TTM = Q[-3] + Q[-2] + Q[-1] + Q[0]
TTM = PRIOR_FY + CURRENT_YTD - PRIOR_COMPARABLE_YTD
```

Metric, entity, financial scope, unit, fiscal continuity, and comparable YTD stage are enforced. Conflicts are never averaged.

See [`docs/FINANCIAL_NORMALIZATION.md`](docs/FINANCIAL_NORMALIZATION.md).

## Web product / Web 제품

```bash
vih web
```

Default: `http://127.0.0.1:8765`

```text
/source       — SEC snapshot validation + extraction
/dart-source  — OpenDART snapshot validation + extraction
/normalize    — financial normalization + TTM + reconciliation
```

These source/normalization surfaces are read-only. There is no browser-origin live-fetch, credential storage, normalization write, promotion, admission, or canonical-write endpoint.

## Milestones / 마일스톤

- [x] M1–M12 evidence governance, valuation kernels, product workflow, canonical admission/apply
- [x] M13 immutable SEC CompanyFacts acquisition
- [x] M14 immutable OpenDART financial-statement acquisition
- [ ] **M15 financial evidence normalization + period semantics + TTM — active finalization**
- [ ] governed normalized-evidence → model-input binding
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
- [`docs/M15_ACCEPTANCE.md`](docs/M15_ACCEPTANCE.md)
- [`docs/M15_IMPLEMENTATION_SUMMARY.md`](docs/M15_IMPLEMENTATION_SUMMARY.md)
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — canonical resume point / 정식 재개점
