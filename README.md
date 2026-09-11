# Valuation-Intelligence-Hub / 가치분석 인텔리전스 허브

> **Separate price from economic value, make assumptions explicit, and make valuation reproducible.**  
> **가격과 경제적 가치를 분리하고, 가정을 명시하며, 가치평가를 재현 가능하게 만든다.**

Valuation-Intelligence-Hub is a reproducible, evidence-grounded **cross-asset valuation intelligence system** that converts market price, financial statements, business economics, uncertainty, and explicit assumptions into intrinsic value, market-implied expectations, expected return, and decision-relevant risk.

Valuation-Intelligence-Hub는 시장가격, 재무제표, 사업경제성, 불확실성, 명시적 가정을 내재가치, 시장 내재 기대, 기대수익률, 의사결정 관련 위험으로 변환하는 재현 가능하고 근거 중심의 **범자산 가치분석 인텔리전스 시스템**입니다.

## Core principles / 핵심 원칙

- **Facts ≠ assumptions / 사실 ≠ 가정**
- **Every material fact needs provenance / 모든 중요 사실은 출처를 가져야 함**
- **Repository canonical state > AI recollection / 저장소 정식 상태 > AI 기억**
- **Growth must reconcile with reinvestment / 성장은 재투자와 일치해야 함**
- **Choose the model for the asset / 자산에 맞는 모델 선택**
- **Uncertainty must be modeled / 불확실성은 모델링**
- **Same versioned inputs + same model ⇒ reproducible output / 동일 버전 입력·모델 ⇒ 재현 가능한 결과**
- **Runtime drift from canonical results is an error / 실행값의 정식 결과 drift는 오류**
- **Draft ≠ Candidate ≠ Staged package ≠ Canonical / Draft ≠ Candidate ≠ 스테이징 패키지 ≠ 정식**
- **Human-reviewed state cannot survive reviewed-scope mutation / 검토범위 변경 시 인간 승인 무효**
- **One kernel, multiple interfaces / 하나의 커널, 여러 인터페이스**

## Canonical analytical flow / 표준 분석 흐름

```text
OBJECT
  ↓
MARKET VALUE
  ↓
EVIDENCE & FACTS
  ↓
NORMALIZATION
  ↓
BUSINESS ECONOMICS
  ↓
VALUATION KERNEL
  ↓
SCENARIO / APPROPRIATE OUTCOME MODEL
  ↓
REVERSE VALUATION
  ↓
PROBABILITY & RISK
  ↓
EXPECTED RETURN
  ↓
THESIS · INVALIDATORS · DECISION
```

## Evidence-grounded AI / GitHub 기반 AI 환각 방지

The repository is the canonical grounding layer for GPT, Codex, Astra, and future agents. Material claims are classified as:

이 저장소는 GPT, Codex, Astra 및 향후 AI 에이전트의 정식 근거화 계층입니다. 중요 주장은 다음과 같이 분류합니다.

`FACT / NORMALIZED_FACT / ASSUMPTION / DERIVED / INTERPRETATION / UNKNOWN`

Missing, conflicting, stale, or unsupported material inputs fail closed instead of being silently invented or promoted.

누락·충돌·노후·미지원 중요 입력은 암묵적으로 생성·승격하지 않고 fail-closed합니다.

## Valuation methods / 가치평가 방법

### Operating-company FCFF / 영업기업 FCFF

\[
FCFF = EBIT(1-T) + D\&A - CAPEX - \Delta NWC
\]

### Reverse valuation / 역산 가치평가

The Hub can work backward from market price to the operating economics required to justify that price.

Hub는 시장가격에서 역으로 출발해 그 가격을 정당화하는 데 필요한 사업경제성을 계산합니다.

### Model selection / 모델 선택

One DCF is not forced onto every asset. Option-like or financing-dependent assets can use probability-weighted venture logic; future adapters may use project, real-estate, asset-based, or real-option methods.

모든 자산에 하나의 DCF를 강제하지 않습니다. 옵션형·자금조달 의존 자산에는 확률가중 벤처 논리를 사용하며 향후 프로젝트·부동산·자산가치·실물옵션 어댑터로 확장할 수 있습니다.

## Validated reference cases / 검증 기준 사례

| Case / 사례 | Model / 모델 | Reference classification / 기준 분류 |
|---|---|---|
| [`LS ELECTRIC`](analyses/equities/KR_010120_LS_ELECTRIC/) | FCFF Bear/Base/Bull | `MARKET_PRICE_ABOVE_MODELED_BULL` |
| [`LS Eco Energy / LS에코에너지`](analyses/equities/KR_229640_LS_ECO_ENERGY/) | FCFF Bear/Base/Bull | `MARKET_PRICE_BETWEEN_MODELED_BASE_AND_BULL` |
| [`Jet.AI`](analyses/equities/US_JTAI_JET_AI/) | Probability-weighted venture / 확률가중 벤처 | option-like / very high model risk |

These are versioned methodology reference results, **not investment recommendations or live target prices**.

이 결과는 버전 관리된 방법론 기준 결과이며 **투자권고나 실시간 목표주가가 아닙니다**.

## Install / 설치

```bash
python -m pip install -e ".[dev]"
```

## Canonical case execution / 정식 사례 실행

```bash
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

The local-first Web product includes canonical dashboards, valuation visualization, evidence browsing, scenario preview, the user Draft Lab, Promotion Review Lab, and M10 Promotion Package Lab.

로컬 우선 Web 제품은 정식 대시보드, 가치 시각화, 근거 탐색, 시나리오 preview, 사용자 Draft 랩, 승격 검토 랩, M10 승격 패키지 랩을 제공합니다.

## User Draft workflow / 사용자 Draft 흐름 — M8

Every user-created/imported case starts as:

```text
DRAFT_USER_SUPPLIED / NOT_CANONICAL / USER_SUPPLIED_UNVERIFIED
```

```bash
vih draft-template equity_fcff > workspace/user_cases/my_company.json
vih draft-validate workspace/user_cases/my_company.json
vih draft-run workspace/user_cases/my_company.json
```

See [`docs/USER_DRAFTS.md`](docs/USER_DRAFTS.md).

## Reviewed promotion workflow / 검토 기반 승격 흐름 — M9

```text
DRAFT_USER_SUPPLIED
        ↓
CANDIDATE_REVIEW
        ↓ evidence + input governance
HUMAN REVIEW + SHA-256 SCOPE LOCK
        ↓
REVIEW_APPROVED_READY_FOR_PR
```

M9 stops at PR readiness and never assigns canonical state.

M9은 PR 준비상태에서 멈추며 정식 상태를 직접 부여하지 않습니다.

```bash
vih candidate-build workspace/user_cases/my_company.json > workspace/user_cases/my_candidate.json
vih candidate-validate workspace/user_cases/my_candidate.json
# Human reviews the exact scope and records APPROVE + returned SHA-256.
vih promotion-check workspace/user_cases/my_candidate.json
```

See [`docs/PROMOTION_PROTOCOL.md`](docs/PROMOTION_PROTOCOL.md).

## Deterministic promotion package / 결정론적 승격 패키지 — M10

M10 converts an already human-approved M9 Candidate into deterministic, tamper-evident **review material**, not a canonical case.

M10은 이미 인간 승인된 M9 Candidate를 결정론적·변조탐지형 **검토 자료**로 변환하며 정식 사례로 만들지 않습니다.

```text
REVIEW_APPROVED_READY_FOR_PR
        ↓
PROMOTION_PACKAGE_STAGED / NOT_CANONICAL
        ↓
explicit reviewed-draft canonical adapter required
        ↓
SEPARATE GOVERNED PR + CI + HUMAN REVIEW + MERGE
        ↓
CANONICAL
```

### Why M10 does not fabricate legacy canonical inputs / 기존 입력을 억지 생성하지 않는 이유

M8 generic equity Drafts preserve forecast D&A, CAPEX, and ΔNWC as absolute values, while current reference-equity cases use revenue-linked ratios plus opening core NWC. Those formats are not losslessly equivalent.

M8 일반 equity Draft는 전망 D&A·CAPEX·ΔNWC 절대값을 보존하지만 현재 reference-equity 사례는 매출연동 비율과 opening core NWC를 사용합니다. 두 형식은 손실 없이 동등하지 않습니다.

Therefore every staged package declares:

```text
NOT_EXECUTABLE_UNTIL_CANONICAL_ADAPTER
```

Current required adapters:

- `equity_fcff` → `reviewed-draft-equity-fcff-v0.1`
- `venture_probability` → `reviewed-draft-venture-probability-v0.1`

### Package build / 패키지 생성

Build in-memory/JSON only:

```bash
vih package-build workspace/user_cases/my_candidate.json \
  --case-id KR_EXAMPLE_COMPANY \
  --name-en "Example Company" \
  --name-ko "예시회사" \
  --asset-class public_equity > workspace/user_cases/package.json
```

Explicit local materialization:

```bash
vih package-build workspace/user_cases/my_candidate.json \
  --case-id KR_EXAMPLE_COMPANY \
  --name-en "Example Company" \
  --name-ko "예시회사" \
  --asset-class public_equity \
  --output-dir workspace/promotion_packages/KR_EXAMPLE_COMPANY
```

Validate:

```bash
vih package-validate workspace/user_cases/package.json
vih package-validate workspace/promotion_packages/KR_EXAMPLE_COMPANY
```

M10 guarantees:

- exact approved Candidate preservation / 승인 Candidate 정확 보존
- shared-kernel valuation reproduction / 공통커널 가치 재현
- per-artifact + package SHA-256 / 산출물별·전체 SHA-256
- canonical case-ID collision rejection / 정식 case ID 충돌 거부
- repository-internal output only under `workspace/promotion_packages/` / 저장소 내부 출력경로 제한
- `REGISTRY_PROPOSAL.json` stays `registration_blocked=true` / 레지스트리 제안 차단 유지
- no `analyses/` or `registry/` write / 정식 경로 기록 없음

See [`docs/PROMOTION_PACKAGE.md`](docs/PROMOTION_PACKAGE.md).

## Product architecture / 제품 아키텍처

```text
                     Shared Valuation Kernels
                              │
                     Shared Application Services
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
       Web UI                CLI                 API
   일반사용자 중심      로컬·고급·대량        자동화·연결
```

Interface layers must reuse shared kernels/evidence gates and must not create alternate valuation formulas.

인터페이스 계층은 공통 커널·근거게이트를 재사용해야 하며 별도 가치평가 공식을 만들 수 없습니다.

## Repository architecture / 저장소 구조

```text
Valuation-Intelligence-Hub/
├── docs/                  # Governance, methodology, execution / 거버넌스·방법론·실행
├── schemas/               # Versioned contracts / 버전 관리 계약
├── templates/             # User Draft templates / 사용자 Draft 템플릿
├── registry/              # Canonical executable registry / 정식 실행 레지스트리
├── src/valuation_hub/     # Kernels + services + adapters / 커널·서비스·어댑터
├── tests/                 # Invariants, regression, integration / 불변·회귀·통합 테스트
├── workspace/
│   ├── user_cases/        # local Drafts / 로컬 Draft
│   └── promotion_packages/# local staged packages / 로컬 스테이징 패키지
└── analyses/              # Canonical evidence, inputs, results / 정식 근거·입력·결과
```

## Development milestones / 개발 마일스톤

- [x] Foundation + bilingual methodology / 기반 + 영한문 방법론
- [x] AI grounding and evidence policy / AI 근거화·근거정책
- [x] Public-equity normalization / 상장기업 정규화
- [x] FCFF scenario + reverse valuation / FCFF 시나리오 + 역산 가치평가
- [x] Dilution-aware venture probability engine / 희석 반영 벤처 확률가중 엔진
- [x] Three evidence-grounded reference cases / 3개 근거 기반 기준 사례
- [x] Executable registry + CLI / 실행 레지스트리 + CLI — M4
- [x] Read-oriented Web MVP / 읽기 중심 Web MVP — M5
- [x] Interactive preview + evidence browser / 인터랙티브 preview + 근거 탐색 — M6
- [x] Product UX + valuation visualization / 제품 UX + 가치 시각화 — M7
- [x] User Draft workflow / 사용자 Draft 흐름 — M8
- [x] Reviewed Draft→Candidate promotion protocol / 검토 기반 승격 프로토콜 — M9
- [ ] Deterministic reviewed promotion-package staging / 검토 완료 승격 패키지 스테이징 — **M10 active / 진행 중**
- [ ] Versioned reviewed-Draft canonical adapter + admission / 버전 검토 Draft 정식 adapter + 수용
- [ ] Live evidence/data ingestion / 실시간 근거·데이터 수집
- [ ] First non-equity adapter / 첫 비주식 자산 어댑터

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
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — exact repository-grounded resume point / 정확한 저장소 기반 재개점

## Current status / 현재 상태

**M10 — Deterministic reviewed promotion package staging / 검토 완료 승격 패키지 결정론적 스테이징 — ACTIVE**

M9 is canonical on `main`. M10 preserves reviewed economics without lossy conversion, creates deterministic hash-locked staging packages, and still refuses canonical write-back or registry admission.

M9은 `main`의 정식 상태입니다. M10은 검토 경제값을 손실 변환 없이 보존하고 결정론적 해시 잠금 스테이징 패키지를 생성하며 정식 write-back·레지스트리 수용은 계속 거부합니다.
