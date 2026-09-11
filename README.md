# Valuation-Intelligence-Hub / 가치분석 인텔리전스 허브

> **Separate price from economic value, make assumptions explicit, and make valuation reproducible.**  
> **가격과 경제적 가치를 분리하고, 가정을 명시하며, 가치평가를 재현 가능하게 만든다.**

Valuation-Intelligence-Hub is a reproducible, evidence-grounded **cross-asset valuation intelligence system** that turns market price, financial statements, business economics, uncertainty, and explicit assumptions into intrinsic value, market-implied expectations, expected return, and decision-relevant risk.

Valuation-Intelligence-Hub는 시장가격·재무제표·사업경제성·불확실성·명시적 가정을 내재가치, 시장 내재 기대, 기대수익률, 의사결정 위험으로 변환하는 재현 가능하고 근거 중심의 **범자산 가치분석 인텔리전스 시스템**입니다.

## Core principles / 핵심 원칙

- **Facts ≠ assumptions / 사실 ≠ 가정**
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

The local-first Web product includes canonical dashboards, valuation visualization, evidence browsing, scenario preview, Draft Lab, Promotion Review, Promotion Package, Canonical Admission, and M12 PR Preparation.

로컬 우선 Web 제품은 정식 대시보드, 가치 시각화, 근거 탐색, 시나리오 preview, Draft, 승격 검토, 승격 패키지, 정식 수용, M12 PR 준비 랩을 제공합니다.

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
          ↓ deterministic registry-baseline-bound plan
M12 REPOSITORY_CHANGE_PLANNED / canonical=false
          ↓ guarded local apply on admission/* branch/worktree
     GUARDED_BRANCH_APPLIED / canonical=false
          ↓ human diff review + repository PR + full CI + merge
     CANONICAL
```

Each state is deliberately distinct. Mathematical validity, evidence admissibility, human review, package integrity, repository planning, branch application, and canonical authority are not collapsed into one step.

각 상태는 의도적으로 분리됩니다. 수학적 유효성, 근거 적격성, 인간 검토, 패키지 무결성, 저장소 계획, 브랜치 적용, 정식 권위를 하나의 단계로 합치지 않습니다.

## M8 — User Draft / 사용자 Draft

```bash
vih draft-template equity_fcff > workspace/user_cases/my_company.json
vih draft-validate workspace/user_cases/my_company.json
vih draft-run workspace/user_cases/my_company.json
```

Draft execution uses shared kernels but never auto-registers canonical state.  
See [`docs/USER_DRAFTS.md`](docs/USER_DRAFTS.md).

## M9 — Reviewed promotion / 검토 기반 승격

```bash
vih candidate-build workspace/user_cases/my_company.json > workspace/user_cases/my_candidate.json
vih candidate-validate workspace/user_cases/my_candidate.json
# Human reviews the exact scope and records APPROVE + returned SHA-256.
vih promotion-check workspace/user_cases/my_candidate.json
```

M9 requires explicit FACT/NORMALIZED_FACT/ASSUMPTION governance, evidence-value reconciliation, and SHA-256-locked human review.  
See [`docs/PROMOTION_PROTOCOL.md`](docs/PROMOTION_PROTOCOL.md).

## M10 — Deterministic promotion package / 결정론적 승격 패키지

```bash
vih package-build workspace/user_cases/my_candidate.json \
  --case-id KR_EXAMPLE_COMPANY \
  --name-en "Example Company" \
  --name-ko "예시회사" \
  --asset-class public_equity > workspace/user_cases/package.json

vih package-validate workspace/user_cases/package.json
```

M10 preserves the exact reviewed Draft instead of coercing absolute D&A/CAPEX/ΔNWC into the legacy reference-case ratio representation.  
See [`docs/PROMOTION_PACKAGE.md`](docs/PROMOTION_PACKAGE.md).

## M11 — Versioned reviewed-Draft canonical admission / 검토 Draft 정식 수용

Versioned adapters:

- `reviewed-draft-equity-fcff-v0.1`
- `reviewed-draft-venture-probability-v0.1`

```bash
vih admission-build workspace/user_cases/package.json > workspace/user_cases/admission.json
vih admission-validate workspace/user_cases/admission.json
```

The admission bundle remains `canonical=false`. It proposes exact canonical files and an explicit adapter registry entry. `valuation_as_of` is derived from governed market-price evidence.

수용 bundle 자체는 `canonical=false`이며 정확한 정식 제안 파일과 명시적 adapter registry 항목을 생성합니다. `valuation_as_of`는 거버넌스된 시장가격 근거에서 도출합니다.

See [`docs/CANONICAL_ADMISSION.md`](docs/CANONICAL_ADMISSION.md).

## M12 — Guarded admission apply + PR preparation / 안전 수용 적용 + PR 준비

M12 closes the last manual-copy gap without opening a path that can silently modify canonical `main`.

### 1. Prepare a dedicated branch/worktree / 전용 브랜치·워크트리 준비

```bash
git switch -c admission/KR_EXAMPLE_COMPANY
```

Filesystem apply is allowed only on symbolic Git branches matching `admission/*`. `main`, `master`, other branch prefixes, and detached HEAD fail closed.

파일 적용은 `admission/*` Git 브랜치에서만 허용됩니다. `main`, `master`, 다른 브랜치, detached HEAD는 차단됩니다.

### 2. Build a baseline-bound plan / 기준선 결합 계획 생성

```bash
vih admission-plan workspace/user_cases/admission.json \
  --target-repo . > workspace/user_cases/change-plan.json
```

The plan locks:

- M11 admission bundle SHA-256
- current `registry/cases.json` raw-byte SHA-256
- exact post-change registry SHA-256
- every proposed canonical artifact path + SHA-256
- full plan SHA-256

### 3. Revalidate before apply / 적용 전 재검증

```bash
vih admission-plan-validate \
  workspace/user_cases/change-plan.json \
  workspace/user_cases/admission.json \
  --target-repo .
```

If the registry changed after planning, the plan is stale and application is blocked.

계획 이후 registry가 변경되면 계획은 stale로 판정되어 적용이 차단됩니다.

### 4. Guardedly apply exact bytes / 정확한 bytes 안전 적용

```bash
vih admission-apply \
  workspace/user_cases/change-plan.json \
  workspace/user_cases/admission.json \
  --target-repo .
```

M12 stages all case artifacts, verifies their SHA-256, moves the complete case directory into place, replaces the registry **last**, verifies applied bytes, then runs:

```text
validate_case → run_case → evidence_view → preview_case
```

Caught failures roll back the original registry and newly created case directory. M12 does not claim impossible multi-file OS crash atomicity; a crash in the narrow pre-registry interval can at worst leave an **unregistered orphan directory**, which has no canonical authority and will not be overwritten automatically.

일반 예외는 원래 registry와 신규 case 디렉터리를 롤백합니다. 다중 파일에 대한 불가능한 완전한 OS crash atomicity를 주장하지 않으며, registry 공개 전 강제종료가 발생해도 최대 결과는 정식 권위가 없는 **미등록 orphan 디렉터리**입니다.

### Web PR Preparation / Web PR 준비

```text
/pr-prep
POST /api/pr-prep/plan
POST /api/pr-prep/validate
```

There is deliberately **no Web apply endpoint**. Browser workflows can inspect plans but cannot mutate the repository.

의도적으로 Web apply endpoint는 존재하지 않습니다. 브라우저에서는 계획을 검토할 수 있지만 저장소를 변경할 수 없습니다.

See [`docs/GUARDED_ADMISSION_APPLY.md`](docs/GUARDED_ADMISSION_APPLY.md).

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

Interface layers reuse shared kernels and evidence gates; they do not create alternate valuation formulas.

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
- [ ] Guarded admission applicator + PR-ready plan — **M12 active / 진행 중**
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
- [`docs/GUARDED_ADMISSION_APPLY.md`](docs/GUARDED_ADMISSION_APPLY.md)
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — exact repository-grounded resume point / 정확한 저장소 기반 재개점
