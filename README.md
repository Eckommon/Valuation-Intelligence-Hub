# Valuation-Intelligence-Hub / 가치분석 인텔리전스 허브

> **Separate price from economic value, make assumptions explicit, and make valuation reproducible.**  
> **가격과 경제적 가치를 분리하고, 가정을 명시하며, 가치평가를 재현 가능하게 만든다.**

Valuation-Intelligence-Hub is a reproducible, evidence-grounded **cross-asset valuation intelligence system** that converts market price, financial statements, business economics, uncertainty, and explicit assumptions into intrinsic value, market-implied expectations, expected return, and decision-relevant risk.

Valuation-Intelligence-Hub는 시장가격, 재무제표, 사업경제성, 불확실성, 명시적 가정을 내재가치, 시장 내재 기대, 기대수익률, 의사결정 관련 위험으로 변환하는 재현 가능하고 근거 중심의 **범자산 가치분석 인텔리전스 시스템**입니다.

## What this repository is / 이 저장소의 정체성

This is **not** merely a stock screener, target-price generator, or one-model DCF calculator. Public equities are the first validated domain. The long-term objective is a common valuation architecture with asset-specific adapters for public and private companies, startups, real estate, infrastructure, projects, IP/technology, and other economic assets.

이 저장소는 단순한 종목 스크리너, 목표주가 생성기, 단일 모델 DCF 계산기가 아닙니다. 상장기업은 첫 번째 검증 도메인일 뿐이며, 장기적으로는 상장·비상장기업, 스타트업, 부동산, 인프라, 프로젝트, IP·기술 등 다양한 경제적 자산을 공통 가치분석 아키텍처와 자산별 어댑터로 분석하는 것을 목표로 합니다.

## Core questions / 핵심 질문

The Hub is designed to answer:

Hub는 다음 질문에 답하도록 설계됩니다.

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
BEAR · BASE · BULL or APPROPRIATE OUTCOME MODEL / 시나리오·적합 결과모델
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

The repository is also the canonical grounding layer for GPT, Codex, Astra, and future AI agents working on the project. Repository-grounded state outranks model recollection.

이 저장소는 GPT, Codex, Astra 및 향후 AI 에이전트의 정식 근거화 계층이기도 합니다. 저장소의 정식 상태는 모델의 기억보다 높은 권위를 가집니다.

Material claims are classified as:

중요 주장은 다음과 같이 구분합니다.

`FACT / NORMALIZED_FACT / ASSUMPTION / DERIVED / INTERPRETATION / UNKNOWN`

Missing, conflicting, stale, or unsupported material inputs fail closed instead of being silently invented or promoted.

누락·충돌·노후·미지원 중요 입력은 암묵적으로 생성하거나 승격하지 않고 fail-closed합니다.

See / 상세 문서:

- [`docs/AI_GROUNDING_POLICY.md`](docs/AI_GROUNDING_POLICY.md)
- [`docs/EVIDENCE_POLICY.md`](docs/EVIDENCE_POLICY.md)
- [`PROJECT_STATE.md`](PROJECT_STATE.md)

## Valuation methods / 가치평가 방법

### Operating-company FCFF / 영업기업 FCFF

\[
FCFF = EBIT(1-T) + D\&A - CAPEX - \Delta NWC
\]

Growth is reconciled with reinvestment, working capital, margins, and capital efficiency rather than being treated as a free narrative input.

성장률은 독립적인 서사 가정으로 두지 않고 재투자, 운전자본, 마진, 자본효율과 함께 일관성을 검증합니다.

### Reverse valuation / 역산 가치평가

The Hub also works from market price backward to the operating economics required to justify that price.

Hub는 시장가격에서 역으로 출발하여 그 가격을 정당화하는 데 필요한 사업경제성을 계산합니다.

### Model selection / 모델 선택

One DCF is not forced onto every asset. Early-stage, option-like, financing-dependent assets may use probability-weighted venture logic; future adapters may use project, real-estate, asset-based, or real-option methods when economically appropriate.

모든 자산에 하나의 DCF를 강제하지 않습니다. 초기·옵션형·자금조달 의존 자산에는 확률가중 벤처 논리를 사용할 수 있으며, 향후 자산 특성에 따라 프로젝트·부동산·자산가치·실물옵션 등의 어댑터를 적용합니다.

## Validated reference cases / 검증 기준 사례

M3 established three evidence-grounded and regression-locked reference cases.

M3에서 세 개의 근거 기반·회귀 잠금 기준 사례를 확립했습니다.

| Case / 사례 | Model / 모델 | Reference classification / 기준 분류 |
|---|---|---|
| [`LS ELECTRIC`](analyses/equities/KR_010120_LS_ELECTRIC/) | FCFF Bear/Base/Bull | `MARKET_PRICE_ABOVE_MODELED_BULL` |
| [`LS Eco Energy / LS에코에너지`](analyses/equities/KR_229640_LS_ECO_ENERGY/) | FCFF Bear/Base/Bull | `MARKET_PRICE_BETWEEN_MODELED_BASE_AND_BULL` |
| [`Jet.AI`](analyses/equities/US_JTAI_JET_AI/) | Probability-weighted venture / 확률가중 벤처 | `OPTION_LIKE_EXPECTED_VALUE_ABOVE_MARKET_WITH_EXTREME_MODEL_RISK` |

These are versioned methodology reference results, **not investment recommendations or live target prices**.

이 결과는 버전 관리된 방법론 기준 결과이며 **투자권고나 실시간 목표주가가 아닙니다**.

## Executable layer / 실행형 계층 — M4

M4 introduces the first executable product layer. A versioned registry and shared case service route each case into the existing tested kernels and verify runtime output against canonical stored results.

M4는 첫 실행형 제품 계층을 도입합니다. 버전 관리 레지스트리와 공통 사례 서비스가 각 사례를 기존 검증 커널로 라우팅하고 런타임 결과를 정식 저장결과와 비교합니다.

### Install for local repository use / 로컬 저장소 실행 설치

```bash
python -m pip install -e ".[dev]"
```

### CLI / CLI 명령

```bash
vih list
vih validate KR_010120_LS_ELECTRIC
vih run KR_229640_LS_ECO_ENERGY
vih report US_JTAI_JET_AI
```

Machine-readable output / 기계 판독 출력:

```bash
vih --json run KR_010120_LS_ELECTRIC
```

The CLI does not contain its own valuation formulas. It calls the same service and kernels that the future Web UI will use.

CLI는 자체 가치평가 공식을 가지지 않습니다. 향후 Web UI와 동일한 서비스·커널을 호출합니다.

See / 사용법:

- [`docs/EXECUTION.md`](docs/EXECUTION.md)
- [`registry/cases.json`](registry/cases.json)

## Product architecture / 제품 아키텍처

The product direction is **Web-first hybrid**.

제품 방향은 **웹 우선 하이브리드(Web-first hybrid)**입니다.

```text
                     Shared Valuation Kernels
                     공통 가치평가 커널
                              │
                     Shared Case Service
                     공통 사례 서비스
                              │
              ┌───────────────┼───────────────┐
              │               │               │
           Web UI            CLI             API
        일반사용자 중심   로컬·고급·대량    자동화·연결
```

- **Web UI** — primary human interface / 일반 사용자의 주 인터페이스
- **CLI/local** — reproducible, private, batch, automation workflows / 재현·비공개·대량·자동화 작업
- **API** — future programmatic integration / 향후 프로그램 연동
- **Desktop shell** — optional future wrapper, not a separate valuation implementation / 향후 선택적 래퍼이며 별도 가치평가 구현이 아님

## Repository architecture / 저장소 구조

```text
Valuation-Intelligence-Hub/
├── docs/                  # Governance, methodology, execution / 거버넌스·방법론·실행
├── schemas/               # Versioned contracts / 버전 관리 계약
├── registry/              # Executable case registry / 실행 사례 레지스트리
├── src/valuation_hub/     # Kernels + shared service + CLI / 커널·공통서비스·CLI
├── tests/                 # Invariants, regression, integration / 불변·회귀·통합 테스트
└── analyses/              # Evidence, inputs, results, reports / 근거·입력·결과·보고서
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
- **One kernel, multiple interfaces / 하나의 커널, 여러 인터페이스**

## Development milestones / 개발 마일스톤

- [x] Foundation + bilingual methodology / 기반 + 영한문 방법론
- [x] AI grounding and evidence policy / AI 근거화·근거정책
- [x] Public-equity normalization / 상장기업 정규화
- [x] FCFF scenario and sensitivity engine / FCFF 시나리오·민감도 엔진
- [x] Reverse valuation solver / 역산 가치평가 솔버
- [x] Dilution-aware venture probability engine / 희석 반영 벤처 확률가중 엔진
- [x] Three evidence-grounded reference cases / 3개 근거 기반 기준 사례
- [x] Python 3.11/3.12 CI + persistent diagnostics / CI + 진단 보존
- [ ] Executable case registry + CLI foundation / 실행 사례 레지스트리 + CLI 기반 — **M4 active / 진행 중**
- [ ] User-friendly Web application MVP / 사용자 친화 Web Application MVP
- [ ] Live evidence/data ingestion / 실시간 근거·데이터 수집
- [ ] First non-equity adapter / 첫 비주식 자산 어댑터

## Canonical documentation / 정식 문서

- [`docs/FOUNDATION.md`](docs/FOUNDATION.md) — mission, scope, principles / 미션·범위·원칙
- [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) — valuation methodology / 가치분석 방법론
- [`docs/EVIDENCE_POLICY.md`](docs/EVIDENCE_POLICY.md) — source and promotion policy / 출처·승격 정책
- [`docs/AI_GROUNDING_POLICY.md`](docs/AI_GROUNDING_POLICY.md) — AI anti-hallucination grounding / AI 환각 방지 근거화
- [`docs/SCENARIO_REVERSE_POLICY.md`](docs/SCENARIO_REVERSE_POLICY.md) — scenario and reverse governance / 시나리오·역산 거버넌스
- [`docs/PRODUCT_VISION.md`](docs/PRODUCT_VISION.md) — product end-state / 제품 최종상태
- [`docs/EXECUTION.md`](docs/EXECUTION.md) — executable interface / 실행형 인터페이스
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — exact repository-grounded resume point / 저장소 기반 정확한 재개점

## Language policy / 언어 원칙

Canonical user-facing documentation is bilingual in English and Korean. English preserves interoperable technical vocabulary; Korean is an equally authoritative interpretation. Code identifiers remain English unless interoperability requires otherwise.

정식 사용자 대상 문서는 영어와 한국어를 병기합니다. 영어는 기술용어의 상호운용성을 유지하고, 한국어는 동등한 권위의 해석을 제공합니다. 코드 식별자는 특별한 사유가 없으면 영어를 사용합니다.

## Current status / 현재 상태

**M4 — Executable case runner + CLI foundation / 실행형 사례 실행기 + CLI 기반 — ACTIVE**

The validated M3 valuation cases are canonical on `main`. M4 is productizing them through one shared execution contract. The next planned layer is a human-friendly Web application MVP over the same service, not a second valuation implementation.

검증된 M3 가치평가 사례는 `main`의 정식 상태입니다. M4는 하나의 공통 실행 계약을 통해 이를 제품화하고 있습니다. 다음 계획 계층은 별도 가치평가 구현이 아니라 동일 서비스 위의 사용자 친화 Web Application MVP입니다.
