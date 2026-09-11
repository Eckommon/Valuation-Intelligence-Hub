# Valuation-Intelligence-Hub / 가치분석 인텔리전스 허브

> **Separate price from economic value, make assumptions explicit, and make valuation reproducible.**  
> **가격과 경제적 가치를 분리하고, 가정을 명시하며, 가치평가를 재현 가능하게 만든다.**

Valuation-Intelligence-Hub is a reproducible, evidence-grounded **cross-asset valuation intelligence system** that converts market price, financial statements, business economics, uncertainty, and explicit assumptions into intrinsic value, market-implied expectations, expected return, and decision-relevant risk.

Valuation-Intelligence-Hub는 시장가격·재무제표·사업경제성·불확실성·명시적 가정을 내재가치, 시장 내재 기대, 기대수익률, 의사결정 위험으로 변환하는 재현 가능하고 근거 중심의 **범자산 가치분석 인텔리전스 시스템**입니다.

## Core principles / 핵심 원칙

- **Facts ≠ assumptions / 사실 ≠ 가정**
- **Every material fact needs provenance / 모든 중요 사실은 출처를 가져야 함**
- **Repository canonical state > AI recollection / 저장소 정식 상태 > AI 기억**
- **Growth must reconcile with reinvestment / 성장은 재투자와 일치해야 함**
- **Choose the model for the asset / 자산에 맞는 모델 선택**
- **Uncertainty must be modeled / 불확실성은 모델링**
- **Same versioned inputs + same model ⇒ reproducible output / 동일 버전 입력·모델 ⇒ 재현 가능한 결과**
- **Runtime drift from canonical results is an error / 실행값의 정식 결과 drift는 오류**
- **Draft ≠ Candidate ≠ Staged package ≠ Admission proposal ≠ Canonical**
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

`FACT / NORMALIZED_FACT / ASSUMPTION / DERIVED / INTERPRETATION / UNKNOWN`

Missing, conflicting, stale, or unsupported material inputs fail closed instead of being silently invented or promoted.

이 저장소는 GPT, Codex, Astra 및 향후 AI 에이전트의 정식 근거화 계층입니다. 누락·충돌·노후·미지원 중요 입력은 암묵적으로 생성·승격하지 않고 fail-closed합니다.

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

The local-first Web product includes canonical dashboards, valuation visualization, evidence browsing, scenario preview, Draft Lab, Promotion Review, Promotion Package, and Canonical Admission labs.

로컬 우선 Web 제품은 정식 대시보드, 가치 시각화, 근거 탐색, 시나리오 preview, Draft 랩, 승격 검토, 승격 패키지, 정식 수용 랩을 제공합니다.

## Governed user-to-canonical flow / 사용자→정식 거버넌스 흐름

```text
M8  DRAFT_USER_SUPPLIED / USER_SUPPLIED_UNVERIFIED
          ↓
M9  CANDIDATE_REVIEW
          ↓ evidence governance + human SHA-256 review lock
     REVIEW_APPROVED_READY_FOR_PR
          ↓
M10 PROMOTION_PACKAGE_STAGED / NOT_CANONICAL
          ↓ deterministic tamper-evident package
M11 CANONICAL_ADMISSION_PROPOSED / bundle canonical=false
          ↓ exact repository PR + full CI + human review + merge
     CANONICAL
```

Each state is deliberately distinct. A mathematically valid Draft is not evidence-grounded; an evidence-grounded Candidate is not canonical; a staged package is not registry-executable; an admission bundle is only a proposal until its exact files are merged.

각 상태는 의도적으로 분리됩니다. 수학적으로 유효한 Draft는 근거화된 정식 사례가 아니며, 검토 Candidate·스테이징 패키지·수용 bundle 역시 정확한 저장소 병합 전에는 정식이 아닙니다.

## M8 — User Draft / 사용자 Draft

```bash
vih draft-template equity_fcff > workspace/user_cases/my_company.json
vih draft-validate workspace/user_cases/my_company.json
vih draft-run workspace/user_cases/my_company.json
```

Draft execution uses the same kernels but never auto-registers canonical state.

See [`docs/USER_DRAFTS.md`](docs/USER_DRAFTS.md).

## M9 — Reviewed promotion / 검토 기반 승격

```bash
vih candidate-build workspace/user_cases/my_company.json > workspace/user_cases/my_candidate.json
vih candidate-validate workspace/user_cases/my_candidate.json
# Human reviews exact scope and records APPROVE + returned SHA-256.
vih promotion-check workspace/user_cases/my_candidate.json
```

Controls include explicit FACT/NORMALIZED_FACT/ASSUMPTION bindings, evidence-value reconciliation, stale/conflict/Tier-D fail-closed behavior, observed-value evidence requirements, and post-review mutation invalidation.

See [`docs/PROMOTION_PROTOCOL.md`](docs/PROMOTION_PROTOCOL.md).

## M10 — Deterministic promotion package / 결정론적 승격 패키지

M10 preserves the exact reviewed Draft instead of coercing it into legacy reference inputs.

```bash
vih package-build workspace/user_cases/my_candidate.json \
  --case-id KR_EXAMPLE_COMPANY \
  --name-en "Example Company" \
  --name-ko "예시회사" \
  --asset-class public_equity > workspace/user_cases/package.json

vih package-validate workspace/user_cases/package.json
```

Optional explicit noncanonical materialization is restricted to a safe workspace path:

```bash
vih package-build workspace/user_cases/my_candidate.json \
  --case-id KR_EXAMPLE_COMPANY \
  --name-en "Example Company" \
  --name-ko "예시회사" \
  --asset-class public_equity \
  --output-dir workspace/promotion_packages/KR_EXAMPLE_COMPANY
```

Every package declares the required reviewed-Draft canonical adapter and remains noncanonical.

See [`docs/PROMOTION_PACKAGE.md`](docs/PROMOTION_PACKAGE.md).

## M11 — Versioned reviewed-Draft canonical admission / 버전 검토 Draft 정식 수용

M11 introduces explicit adapters:

- `reviewed-draft-equity-fcff-v0.1`
- `reviewed-draft-venture-probability-v0.1`

Registry entries without an `adapter` keep the legacy reference route, so the existing three canonical cases remain unchanged.

`adapter`가 없는 registry 항목은 기존 reference 경로를 유지하므로 현재 3개 정식 사례의 실행계약은 변경되지 않습니다.

### Why a separate adapter exists / 별도 adapter가 필요한 이유

Generic equity Drafts store absolute D&A, CAPEX, and ΔNWC. Legacy reference cases rebuild those economics from revenue-linked ratios and opening NWC. The formats are not losslessly equivalent, so M11 embeds the exact reviewed Draft and routes it through the shared FCFF kernel without reverse-engineering legacy ratios.

일반 equity Draft는 D&A·CAPEX·ΔNWC 절대값을 저장하지만 기존 reference 사례는 매출연동 비율과 opening NWC에서 경제값을 재구축합니다. 두 형식은 무손실 동등하지 않으므로 M11은 검토 Draft를 그대로 내장해 공통 FCFF 커널로 실행합니다.

### Canonical compatibility profile v0.1 / 정식 호환 프로파일 v0.1

Generic Drafts may use arbitrary valid scenario names. Canonical admission v0.1 requires the scenario contract currently expected by the product UI:

- equity: exactly `BEAR / BASE / BULL`
- venture: exactly `FAILURE / SURVIVAL / BREAKOUT`

A valid M8/M10 case can therefore be blocked at M11 without modifying its data.

### Admission commands / 수용 명령

```bash
vih admission-build workspace/user_cases/package.json > workspace/user_cases/admission.json
vih admission-validate workspace/user_cases/admission.json
```

The admission bundle itself remains `canonical=false`. It proposes exact canonical files plus a registry entry containing the versioned `adapter`. `valuation_as_of` is derived from governed market-price evidence rather than manually supplied.

수용 bundle 자체는 `canonical=false`를 유지합니다. 정식 파일과 versioned `adapter`를 포함한 registry 항목을 제안하며 `valuation_as_of`는 시장가격 근거의 기준일에서 도출합니다.

The runtime provenance chain is revalidated at canonical read time:

```text
SOURCE_PACKAGE
→ approved Candidate SHA-256
→ human review-scope SHA-256
→ exact reviewed_draft
→ exact evidence + input_governance
→ adapter/model compatibility
→ shared-kernel recomputation
→ stored canonical runtime
```

Any mismatch blocks `validate_case()` and therefore blocks CLI/Web/API consumption.

See [`docs/CANONICAL_ADMISSION.md`](docs/CANONICAL_ADMISSION.md).

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
- [x] Executable registry + CLI — M4
- [x] Read-oriented Web MVP — M5
- [x] Interactive preview + evidence browser — M6
- [x] Product UX + valuation visualization — M7
- [x] User Draft workflow — M8
- [x] Reviewed Draft→Candidate promotion protocol — M9
- [x] Deterministic reviewed promotion-package staging — M10
- [ ] Versioned reviewed-Draft canonical adapter + admission — **M11 active / 진행 중**
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
- [`docs/CANONICAL_ADMISSION.md`](docs/CANONICAL_ADMISSION.md)
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — exact repository-grounded resume point / 정확한 저장소 기반 재개점
