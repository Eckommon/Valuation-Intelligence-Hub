# Valuation-Intelligence-Hub / 가치분석 인텔리전스 허브

> **Separate price from economic value, make assumptions explicit, and make valuation reproducible.**  
> **가격과 경제적 가치를 분리하고, 가정을 명시하며, 가치평가를 재현 가능하게 만든다.**

Valuation-Intelligence-Hub is a reproducible, evidence-grounded **cross-asset valuation intelligence system** that turns market price, financial statements, business economics, uncertainty, and explicit assumptions into intrinsic value, market-implied expectations, expected return, and decision-relevant risk.

Valuation-Intelligence-Hub는 시장가격·재무제표·사업경제성·불확실성·명시적 가정을 내재가치, 시장 내재 기대, 기대수익률, 의사결정 위험으로 변환하는 재현 가능하고 근거 중심의 **범자산 가치분석 인텔리전스 시스템**입니다.

## Core principles / 핵심 원칙

- **Facts ≠ assumptions / 사실 ≠ 가정**
- **Official source ≠ automatic canonical fact / 공식 출처 ≠ 자동 정식 사실**
- **Every material fact needs provenance / 모든 중요 사실은 출처 필요**
- **Repository canonical state > AI recollection / 저장소 정식 상태 > AI 기억**
- **Growth must reconcile with reinvestment / 성장은 재투자와 일치**
- **Choose the model for the asset / 자산에 맞는 모델 선택**
- **Uncertainty must be modeled / 불확실성은 모델링**
- **Same versioned inputs + same model ⇒ reproducible output / 동일 버전 입력·모델 ⇒ 재현 결과**
- **Draft ≠ Candidate ≠ Staged package ≠ Admission proposal ≠ Branch apply ≠ Canonical**
- **Human-reviewed state cannot survive reviewed-scope mutation / 검토범위 변경 시 승인 무효**
- **One kernel, multiple interfaces / 하나의 커널, 여러 인터페이스**

## Valuation methods / 가치평가 방법

### Operating-company FCFF / 영업기업 FCFF

\[
FCFF = EBIT(1-T) + D\&A - CAPEX - \Delta NWC
\]

### Reverse valuation / 역산 가치평가

The Hub can work backward from market price to the operating economics required to justify that price.

Hub는 시장가격에서 역으로 출발하여 그 가격을 정당화하는 데 필요한 사업경제성을 계산합니다.

### Model selection / 모델 선택

One DCF is not forced onto every asset. Option-like or financing-dependent assets can use probability-weighted venture logic; the architecture is designed to add project, real-estate, asset-based, real-option, and other adapters.

모든 자산에 하나의 DCF를 강제하지 않습니다. 옵션형·자금조달 의존 자산에는 확률가중 벤처 논리를 사용할 수 있고, 프로젝트·부동산·자산가치·실물옵션 등으로 확장하도록 설계합니다.

## Validated reference cases / 검증 기준 사례

| Case / 사례 | Model / 모델 | Reference classification / 기준 분류 |
|---|---|---|
| [`LS ELECTRIC`](analyses/equities/KR_010120_LS_ELECTRIC/) | FCFF Bear/Base/Bull | `MARKET_PRICE_ABOVE_MODELED_BULL` |
| [`LS Eco Energy / LS에코에너지`](analyses/equities/KR_229640_LS_ECO_ENERGY/) | FCFF Bear/Base/Bull | `MARKET_PRICE_BETWEEN_MODELED_BASE_AND_BULL` |
| [`Jet.AI`](analyses/equities/US_JTAI_JET_AI/) | Probability-weighted venture / 확률가중 벤처 | option-like / very high model risk |

These are versioned methodology references, **not live investment recommendations or target prices**.

이 결과는 버전 관리된 방법론 기준 결과이며 **실시간 투자권고·목표주가가 아닙니다**.

## Install and canonical execution / 설치·정식 실행

```bash
python -m pip install -e ".[dev]"

vih list
vih validate KR_010120_LS_ELECTRIC
vih run KR_229640_LS_ECO_ENERGY
vih report US_JTAI_JET_AI
```

## Product Web / 제품 Web

```bash
vih web
```

Default / 기본: `http://127.0.0.1:8765`

The local-first Web product includes canonical dashboards, valuation visualization, evidence browsing, scenario preview, Draft Lab, Promotion Review, Promotion Package, Canonical Admission, PR Preparation, and the M13 SEC Source Snapshot Inspector.

로컬 우선 Web 제품은 정식 대시보드, 가치 시각화, 근거 탐색, 시나리오 preview, Draft, 승격 검토, 승격 패키지, 정식 수용, PR 준비, M13 SEC Source Snapshot 검사기를 제공합니다.

## Governed user-to-canonical flow / 사용자→정식 거버넌스 흐름

```text
M13 LIVE OFFICIAL SOURCE
          ↓ immutable snapshot + hash lock
     SOURCE_SNAPSHOT_CAPTURED / NOT_CANONICAL
          ↓ deterministic extraction
     EVIDENCE_CANDIDATE_UNREVIEWED / NOT_CANONICAL
          ↓ explicit binding/review in existing governance
M8  DRAFT_USER_SUPPLIED / USER_SUPPLIED_UNVERIFIED
          ↓
M9  CANDIDATE_REVIEW
          ↓ evidence governance + human SHA-256 review lock
     REVIEW_APPROVED_READY_FOR_PR
          ↓
M10 PROMOTION_PACKAGE_STAGED / NOT_CANONICAL
          ↓
M11 CANONICAL_ADMISSION_PROPOSED / bundle canonical=false
          ↓
M12 REPOSITORY_CHANGE_PLANNED / canonical=false
          ↓ guarded local apply on admission/* branch/worktree
     GUARDED_BRANCH_APPLIED / canonical=false
          ↓ human diff review + repository PR + full CI + merge
     CANONICAL
```

Each state is deliberately distinct. Mathematical validity, official-source provenance, evidence admissibility, human review, package integrity, repository planning, branch application, and canonical authority are not collapsed into one step.

각 상태는 의도적으로 분리됩니다. 수학적 유효성, 공식출처, 근거 적격성, 인간 검토, 패키지 무결성, 저장소 계획, 브랜치 적용, 정식 권위를 하나의 단계로 합치지 않습니다.

## M8–M12 — Governed promotion and admission / 검토·승격·수용

The existing user-to-canonical pipeline remains intact:

- M8: user Draft + shared-kernel validation / 사용자 Draft
- M9: evidence-governed Candidate + human SHA-256 review lock / 근거 거버넌스 + 인간검토
- M10: deterministic tamper-evident promotion package / 결정론적 승격 패키지
- M11: versioned reviewed-Draft canonical adapter + admission proposal / 정식 adapter + 수용제안
- M12: deterministic repository plan + guarded `admission/*` branch apply / 저장소 계획 + 안전 브랜치 적용

Important M12 commands:

```bash
vih admission-plan workspace/user_cases/admission.json --target-repo . > workspace/user_cases/change-plan.json
vih admission-plan-validate workspace/user_cases/change-plan.json workspace/user_cases/admission.json --target-repo .
vih admission-apply workspace/user_cases/change-plan.json workspace/user_cases/admission.json --target-repo .
```

Filesystem apply is allowed only on symbolic Git branches matching `admission/*`; `main`, `master`, other branch prefixes, detached HEAD, registry drift, path collision, and symlink escape fail closed.

See [`docs/PROMOTION_PROTOCOL.md`](docs/PROMOTION_PROTOCOL.md), [`docs/PROMOTION_PACKAGE.md`](docs/PROMOTION_PACKAGE.md), [`docs/CANONICAL_ADMISSION.md`](docs/CANONICAL_ADMISSION.md), and [`docs/GUARDED_ADMISSION_APPLY.md`](docs/GUARDED_ADMISSION_APPLY.md).

## M13 — Immutable live evidence + SEC CompanyFacts / 불변 live 근거 + SEC CompanyFacts

M13 introduces the first production live-source adapter:

```text
sec-companyfacts-v0.1
```

The adapter constructs the official CompanyFacts locator from a normalized CIK and captures the exact UTF-8 response body into a noncanonical source snapshot.

Adapter는 정규화 CIK에서 공식 CompanyFacts locator를 구성하고 정확한 UTF-8 응답 원문을 비정식 source snapshot으로 보존합니다.

### Live fetch / Live 수집

```bash
vih sec-fetch 0000320193 \
  --user-agent "Valuation-Intelligence-Hub contact@example.com" \
  --output workspace/source_snapshots/AAPL-companyfacts.json
```

The transport is HTTPS/host bounded, uses an identifying SEC User-Agent, applies a conservative local request interval, bounds timeout/response size, validates JSON/UTF-8, and never stores the User-Agent text in the snapshot.

전송계층은 HTTPS·host 제한, 식별 User-Agent, 보수적 rate 제한, timeout·응답크기 제한, JSON·UTF-8 검증을 적용하며 User-Agent 문자열 자체는 snapshot에 저장하지 않습니다.

### Snapshot validation / Snapshot 검증

```bash
vih sec-snapshot-validate workspace/source_snapshots/AAPL-companyfacts.json
```

Snapshot validation rechecks CIK identity, raw-body size/SHA-256, metadata, and full snapshot SHA-256. Snapshot materialization is restricted to `workspace/source_snapshots/` and refuses overwrite.

### Evidence candidate extraction / 근거후보 추출

```bash
vih sec-extract workspace/source_snapshots/AAPL-companyfacts.json revenue
vih sec-extract workspace/source_snapshots/AAPL-companyfacts.json revenue --form 10-Q --period-end YYYY-MM-DD
```

Initial metric registry:

- `revenue`
- `operating_income`
- `net_income`
- `assets`
- `cash`
- `shares_outstanding`

Each result preserves taxonomy/concept/unit, accession, filing form/date, reporting period, source snapshot SHA-256, and body SHA-256. Concept fallback is explicit. Equal-precedence conflicting values fail closed. M13 does **not** synthesize TTM or automatically bind extracted values into a Draft/Candidate.

각 결과는 taxonomy/concept/unit, accession, filing form/date, 보고기간, snapshot/body SHA-256을 보존합니다. concept fallback은 명시적으로 표시되며 동일 우선순위 값 충돌은 fail-closed합니다. M13은 TTM을 합성하거나 Draft/Candidate에 자동 연결하지 않습니다.

### Web source inspector / Web 출처 검사

```text
/source
POST /api/source/validate
POST /api/source/extract
```

There is deliberately **no browser live-fetch endpoint** and no canonical-write endpoint. Web only inspects already captured snapshots.

브라우저 live-fetch 및 정식 write endpoint는 의도적으로 없습니다. Web은 이미 수집된 snapshot만 검사합니다.

See [`docs/LIVE_EVIDENCE_SEC.md`](docs/LIVE_EVIDENCE_SEC.md).

## Product architecture / 제품 아키텍처

```text
Official Sources
      │
Immutable Source Snapshots
      │
Unreviewed Evidence Candidates
      │
Evidence Governance + Human Review
      │
Shared Valuation Kernels
      │
Canonical Admission / Registry
      │
Web · CLI · API
```

Interfaces reuse shared kernels and evidence gates; they do not create alternate valuation formulas or alternate canonical truth paths.

## Development milestones / 개발 마일스톤

- [x] Foundation + bilingual methodology / 기반 + 영한문 방법론
- [x] Evidence grounding + public-equity normalization / 근거화 + 상장기업 정규화
- [x] FCFF scenario + reverse valuation / FCFF 시나리오 + 역산 가치평가
- [x] Dilution-aware venture probability engine / 희석 반영 벤처 확률가중 엔진
- [x] Three evidence-grounded reference cases / 근거 기반 기준 사례 3개
- [x] Executable registry + CLI — M4
- [x] Read-oriented Web MVP — M5
- [x] Interactive preview + evidence browser — M6
- [x] Product UX + valuation visualization — M7
- [x] User Draft workflow — M8
- [x] Reviewed Draft→Candidate promotion — M9
- [x] Deterministic reviewed promotion-package staging — M10
- [x] Versioned reviewed-Draft canonical adapter + admission — M11
- [x] Guarded admission applicator + PR-ready plan — M12
- [ ] Immutable live evidence acquisition + SEC CompanyFacts adapter — **M13 active / 진행 중**
- [ ] OpenDART source adapter / OpenDART 소스 adapter
- [ ] Financial normalization + TTM evidence transforms / 재무 정규화 + TTM 근거변환
- [ ] First non-equity valuation adapter / 첫 비주식 가치평가 adapter

## Canonical documentation / 정식 문서

- [`docs/FOUNDATION.md`](docs/FOUNDATION.md)
- [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md)
- [`docs/EVIDENCE_POLICY.md`](docs/EVIDENCE_POLICY.md)
- [`docs/AI_GROUNDING_POLICY.md`](docs/AI_GROUNDING_POLICY.md)
- [`docs/SCENARIO_REVERSE_POLICY.md`](docs/SCENARIO_REVERSE_POLICY.md)
- [`docs/PRODUCT_VISION.md`](docs/PRODUCT_VISION.md)
- [`docs/EXECUTION.md`](docs/EXECUTION.md)
- [`docs/USER_DRAFTS.md`](docs/USER_DRAFTS.md)
- [`docs/PROMOTION_PROTOCOL.md`](docs/PROMOTION_PROTOCOL.md)
- [`docs/PROMOTION_PACKAGE.md`](docs/PROMOTION_PACKAGE.md)
- [`docs/CANONICAL_ADMISSION.md`](docs/CANONICAL_ADMISSION.md)
- [`docs/GUARDED_ADMISSION_APPLY.md`](docs/GUARDED_ADMISSION_APPLY.md)
- [`docs/LIVE_EVIDENCE_SEC.md`](docs/LIVE_EVIDENCE_SEC.md)
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — exact repository-grounded resume point / 정확한 저장소 기반 재개점
