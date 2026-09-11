# Valuation-Intelligence-Hub / 가치분석 인텔리전스 허브

> **Separate price from economic value, make assumptions explicit, and make valuation reproducible.**  
> **가격과 경제적 가치를 분리하고, 가정을 명시하며, 가치평가를 재현 가능하게 만든다.**

Valuation-Intelligence-Hub is a reproducible, evidence-grounded **cross-asset valuation intelligence system** that converts market price, financial statements, business economics, uncertainty, and explicit assumptions into intrinsic value, market-implied expectations, expected return, and decision-relevant risk.

Valuation-Intelligence-Hub는 시장가격, 재무제표, 사업경제성, 불확실성, 명시적 가정을 내재가치, 시장 내재 기대, 기대수익률, 의사결정 관련 위험으로 변환하는 재현 가능하고 근거 중심의 **범자산 가치분석 인텔리전스 시스템**입니다.

## What this repository is / 이 저장소의 정체성

This is **not** merely a stock screener, target-price generator, or one-model DCF calculator. Public equities are the first validated domain. The long-term objective is one common valuation architecture with asset-specific adapters for public/private companies, startups, real estate, infrastructure, projects, IP/technology, and other economic assets.

이 저장소는 단순 종목 스크리너, 목표주가 생성기, 단일 DCF 계산기가 아닙니다. 상장기업은 첫 검증 도메인일 뿐이며 장기적으로는 상장·비상장기업, 스타트업, 부동산, 인프라, 프로젝트, IP·기술 등 다양한 경제자산을 하나의 공통 가치분석 아키텍처와 자산별 어댑터로 분석하는 것을 목표로 합니다.

## Core questions / 핵심 질문

1. **What is the asset worth? / 이 자산의 경제적 가치는 얼마인가?**
2. **What facts support the valuation? / 어떤 사실이 가치평가를 뒷받침하는가?**
3. **Which assumptions drive the result? / 어떤 가정이 결과를 좌우하는가?**
4. **What future economics are implied by the current price? / 현재 가격은 어떤 미래 경제성을 요구하는가?**
5. **How does value change across coherent scenarios? / 일관된 시나리오에서 가치는 어떻게 달라지는가?**
6. **What would invalidate the thesis? / 어떤 조건이 분석 논리를 무효화하는가?**

## Canonical analytical flow / 표준 분석 흐름

```text
OBJECT / 분석대상
  ↓
MARKET VALUE / 시장가치
  ↓
EVIDENCE & FACTS / 근거·사실
  ↓
NORMALIZATION / 정규화
  ↓
BUSINESS ECONOMICS / 사업경제성
  ↓
VALUATION KERNEL / 가치평가 커널
  ↓
SCENARIO / APPROPRIATE OUTCOME MODEL / 시나리오·적합 결과모델
  ↓
REVERSE VALUATION / 역산 가치평가
  ↓
PROBABILITY & RISK / 확률·위험
  ↓
EXPECTED RETURN / 기대수익률
  ↓
THESIS · INVALIDATORS · DECISION / 논리·무효화조건·판단
```

## Evidence-grounded AI / GitHub 기반 AI 환각 방지

The repository is the canonical grounding layer for GPT, Codex, Astra, and future agents working on the project. Repository-grounded state outranks model recollection.

이 저장소는 GPT, Codex, Astra 및 향후 AI 에이전트의 정식 근거화 계층입니다. 저장소의 정식 상태는 모델의 기억보다 높은 권위를 가집니다.

Material claims are classified as:

`FACT / NORMALIZED_FACT / ASSUMPTION / DERIVED / INTERPRETATION / UNKNOWN`

Missing, conflicting, stale, or unsupported material inputs fail closed instead of being silently invented or promoted.

누락·충돌·노후·미지원 중요 입력은 암묵적으로 생성하거나 승격하지 않고 fail-closed합니다.

## Valuation methods / 가치평가 방법

### Operating-company FCFF / 영업기업 FCFF

\[
FCFF = EBIT(1-T) + D\&A - CAPEX - \Delta NWC
\]

Growth is reconciled with reinvestment, working capital, margins, and capital efficiency rather than treated as a free narrative input.

성장률은 독립적 서사 가정이 아니라 재투자, 운전자본, 마진, 자본효율과 함께 일관성을 검증합니다.

### Reverse valuation / 역산 가치평가

The Hub can work from market price backward to the operating economics required to justify that price.

Hub는 시장가격에서 역으로 출발해 그 가격을 정당화하는 데 필요한 사업경제성을 계산합니다.

### Model selection / 모델 선택

One DCF is not forced onto every asset. Option-like or financing-dependent assets can use probability-weighted venture logic; future adapters may use project, real-estate, asset-based, or real-option methods.

모든 자산에 하나의 DCF를 강제하지 않습니다. 옵션형·자금조달 의존 자산에는 확률가중 벤처 논리를 사용하고 향후 프로젝트·부동산·자산가치·실물옵션 어댑터를 확장할 수 있습니다.

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

Machine-readable output / 기계판독 출력:

```bash
vih --json run KR_010120_LS_ELECTRIC
```

## Product Web / 제품 Web

```bash
vih web
```

Default / 기본: `http://127.0.0.1:8765`

The local-first Web product includes canonical case dashboards, valuation visualization, evidence browsing, scenario preview, user Draft analysis, and M9 promotion review.

로컬 우선 Web 제품은 정식 사례 대시보드, 가치 시각화, 근거 탐색, 시나리오 preview, 사용자 Draft 분석, M9 승격 검토를 제공합니다.

## User Draft workflow / 사용자 Draft 흐름

All user-created/imported cases begin as:

```text
DRAFT_USER_SUPPLIED / NOT_CANONICAL / USER_SUPPLIED_UNVERIFIED
```

```bash
vih draft-template equity_fcff > workspace/user_cases/my_company.json
vih draft-validate workspace/user_cases/my_company.json
vih draft-run workspace/user_cases/my_company.json
```

Draft execution uses the same valuation kernels as canonical cases but does not auto-register or write canonical state.

Draft는 정식 사례와 같은 가치평가 커널을 사용하지만 정식 상태를 자동 등록·기록하지 않습니다.

See / 상세: [`docs/USER_DRAFTS.md`](docs/USER_DRAFTS.md)

## Reviewed promotion workflow / 검토 기반 승격 흐름 — M9

```text
DRAFT_USER_SUPPLIED
        ↓
CANDIDATE_REVIEW
        ↓ evidence + input governance
HUMAN REVIEW + SHA-256 SCOPE LOCK
        ↓
REVIEW_APPROVED_READY_FOR_PR
        ↓ separate reviewed PR + CI + merge
CANONICAL
```

M9 deliberately stops at `REVIEW_APPROVED_READY_FOR_PR`. It cannot directly write canonical analysis files or insert a case into `registry/cases.json`.

M9은 의도적으로 `REVIEW_APPROVED_READY_FOR_PR`에서 멈춥니다. 정식 분석 파일을 직접 기록하거나 `registry/cases.json`에 사례를 삽입할 수 없습니다.

```bash
vih candidate-build workspace/user_cases/my_company.json > workspace/user_cases/my_candidate.json
vih candidate-validate workspace/user_cases/my_candidate.json
# Human reviews the exact candidate scope and records APPROVE + returned SHA-256.
vih promotion-check workspace/user_cases/my_candidate.json
```

Promotion controls include:

- every material numeric input is explicitly governed / 모든 중요 숫자 입력 명시적 거버넌스
- observed values cannot be reclassified as assumptions to evade evidence / 관측값의 가정 분류 우회 차단
- FACT/NORMALIZED_FACT requires linked evidence / 사실·정규화사실 연결 근거 필수
- evidence values must reconcile with model inputs / 근거값·모델입력 조정 필수
- stale/conflicting/unsupported evidence fails closed / 노후·충돌·미지원 근거 차단
- human review is SHA-256 scope-locked / 인간 검토범위 SHA-256 잠금
- post-review mutation invalidates approval / 검토 후 변경 시 승인 무효화

See / 상세: [`docs/PROMOTION_PROTOCOL.md`](docs/PROMOTION_PROTOCOL.md)

## Product architecture / 제품 아키텍처

The product direction is **Web-first hybrid**.

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

Web, CLI, and API adapters must reuse shared kernels, evidence gates, schemas, and service contracts. Interface layers must not create alternate valuation formulas.

Web, CLI, API 어댑터는 공통 커널·근거게이트·스키마·서비스 계약을 재사용해야 하며 인터페이스 계층은 별도 가치평가 공식을 만들 수 없습니다.

## Repository architecture / 저장소 구조

```text
Valuation-Intelligence-Hub/
├── docs/                  # Governance, methodology, execution / 거버넌스·방법론·실행
├── schemas/               # Versioned contracts / 버전 관리 계약
├── templates/             # User Draft templates / 사용자 Draft 템플릿
├── registry/              # Canonical executable case registry / 정식 실행 사례 레지스트리
├── src/valuation_hub/     # Kernels + services + adapters / 커널·서비스·어댑터
├── tests/                 # Invariants, regression, integration / 불변·회귀·통합 테스트
├── workspace/             # Local user workspace guidance / 로컬 사용자 작업공간 안내
└── analyses/              # Canonical evidence, inputs, results, reports / 정식 근거·입력·결과·보고서
    └── equities/
```

## Core principles / 핵심 원칙

- **Facts ≠ assumptions / 사실 ≠ 가정**
- **Every material fact needs provenance / 모든 중요 사실은 출처를 가져야 함**
- **Repository canonical state > AI recollection / 저장소 정식 상태 > AI 기억**
- **Growth must reconcile with reinvestment / 성장은 재투자와 일치해야 함**
- **Choose the model for the asset / 자산에 맞는 모델 선택**
- **Uncertainty must be modeled / 불확실성은 모델링**
- **Same versioned inputs + same model ⇒ reproducible output / 동일 버전 입력·모델 ⇒ 재현 가능한 결과**
- **Runtime drift from canonical results is an error / 실행값의 정식 결과 drift는 오류**
- **Draft ≠ Candidate ≠ Canonical / Draft ≠ Candidate ≠ 정식**
- **Human-reviewed promotion cannot survive reviewed-scope mutation / 검토범위 변경 시 인간 승인 무효**
- **One kernel, multiple interfaces / 하나의 커널, 여러 인터페이스**

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
- [ ] Reviewed Draft→Candidate→Canonical promotion protocol / 검토 기반 승격 프로토콜 — **M9 active / 진행 중**
- [ ] Deterministic reviewed-PR materialization / 검토 PR용 결정론적 materialization
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
- [`docs/WEB_MVP.md`](docs/WEB_MVP.md)
- [`docs/INTERACTIVE_PREVIEW.md`](docs/INTERACTIVE_PREVIEW.md)
- [`docs/PRODUCT_UX.md`](docs/PRODUCT_UX.md)
- [`docs/USER_DRAFTS.md`](docs/USER_DRAFTS.md)
- [`docs/PROMOTION_PROTOCOL.md`](docs/PROMOTION_PROTOCOL.md)
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — exact repository-grounded resume point / 저장소 기반 정확한 재개점

## Language policy / 언어 원칙

Canonical user-facing documentation is bilingual in English and Korean. English preserves interoperable technical vocabulary; Korean is an equally authoritative interpretation. Code identifiers remain English unless interoperability requires otherwise.

정식 사용자 대상 문서는 영어와 한국어를 병기합니다. 영어는 기술용어의 상호운용성을 유지하고 한국어는 동등한 권위의 해석을 제공합니다. 코드 식별자는 특별한 사유가 없으면 영어를 사용합니다.

## Current status / 현재 상태

**M9 — Reviewed Draft→Candidate→Canonical promotion protocol / 검토 기반 승격 프로토콜 — ACTIVE**

M8 is canonical on `main`. M9 is implementing explicit input governance, evidence reconciliation, SHA-256 human-review scope locking, and PR-readiness verification without automatic canonical write-back.

M8은 `main`의 정식 상태입니다. M9은 정식 자동 write-back 없이 명시적 입력 거버넌스, 근거 조정, SHA-256 인간 검토범위 잠금, PR 준비도 검증을 구현하고 있습니다.
