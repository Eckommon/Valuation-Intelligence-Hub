# Valuation-Intelligence-Hub / 가치분석 인텔리전스 허브

> **Separate price from economic value, make assumptions explicit, and make valuation reproducible.**  
> **가격과 경제적 가치를 분리하고, 가정을 명시하며, 가치평가를 재현 가능하게 만든다.**

Valuation-Intelligence-Hub is a reproducible, evidence-grounded valuation system that converts market price, financial statements, business economics, uncertainty, and scenario assumptions into **intrinsic value, market-implied expectations, expected return, and decision-relevant risk**.

Valuation-Intelligence-Hub는 시장가격, 재무제표, 사업경제성, 불확실성, 시나리오 가정을 **내재가치, 시장 내재 기대, 기대수익률, 의사결정 관련 위험**으로 변환하는 재현 가능하고 근거 중심의 가치분석 시스템입니다.

## What this repository is / 이 저장소의 정체성

This is **not** merely a stock screener, target-price generator, or DCF calculator. Public equities are the first reference domain. The long-term objective is a common valuation kernel with asset-specific adapters for public and private companies, startups, real estate, infrastructure, projects, IP, and other economic assets.

이 저장소는 단순한 종목 스크리너, 목표주가 생성기, DCF 계산기가 아닙니다. 상장주식은 첫 번째 기준 도메인일 뿐이며, 장기적으로는 상장·비상장기업, 스타트업, 부동산, 인프라, 프로젝트, IP 등 다양한 경제적 자산을 공통 가치평가 커널과 자산별 어댑터로 분석하는 것을 목표로 합니다.

## Canonical analytical flow / 표준 분석 흐름

```text
OBJECT / 분석대상
  ↓
MARKET VALUE / 시장가치
  ↓
EVIDENCE & FINANCIAL FACTS / 근거·재무사실
  ↓
NORMALIZATION / 정규화
  ↓
BUSINESS ECONOMICS / 사업경제성
  ↓
CASH-FLOW ENGINE / 현금흐름 엔진
  ↓
COST OF CAPITAL / 자본비용
  ↓
INTRINSIC VALUATION / 내재가치평가
  ↓
BEAR · BASE · BULL / 시나리오
  ↓
REVERSE VALUATION / 역산 가치평가
  ↓
PROBABILITY & RISK / 확률·위험
  ↓
EXPECTED RETURN / 기대수익률
  ↓
THESIS · INVALIDATORS · DECISION / 논리·무효화조건·판단
```

## Core valuation lenses / 핵심 가치평가 렌즈

The first public-equity adapter standardizes five initial lenses before full intrinsic valuation:

첫 상장기업 어댑터는 본격적인 내재가치평가 전에 다음 5개 렌즈를 표준화합니다.

1. **Market Cap / Revenue (P/S) / 시가총액 ÷ 매출**
2. **Market Cap or EV / EBIT / 시가총액 또는 EV ÷ 영업이익**
3. **P/E / PER**
4. **P/FCF / 시가총액 ÷ 잉여현금흐름**
5. **Reverse DCF / 역산 DCF** — what future economics are required by the current price? / 현재 가격이 요구하는 미래 경제성은 무엇인가?

## FCFF kernel / FCFF 커널

For operating-company DCF, the canonical cash-flow identity is:

영업기업 DCF의 표준 현금흐름 공식은 다음과 같습니다.

\[
FCFF = EBIT(1-T) + D\&A - CAPEX - \Delta NWC
\]

Growth must be reconciled with reinvestment and ROIC rather than entered as an isolated narrative assumption.

성장률은 독립적인 서사 가정으로 입력하지 않고 재투자와 ROIC와의 관계를 통해 일관성을 점검합니다.

## Seven core engines / 7대 핵심 엔진

1. **Evidence Engine / 근거 엔진** — provenance, period, unit, source quality / 출처·기간·단위·근거품질
2. **Normalization Engine / 정규화 엔진** — accounting facts → economic facts / 회계사실 → 경제적 사실
3. **Valuation Kernel / 가치평가 커널** — FCFF/FCFE/DCF/EV-to-equity and future methods / 핵심 가치평가 계산
4. **Scenario Engine / 시나리오 엔진** — coherent Bear/Base/Bull and sensitivity / 일관된 3대 시나리오·민감도
5. **Reverse Valuation Engine / 역산 가치평가 엔진** — market-implied growth, margin, reinvestment, value / 시장 내재 기대 역산
6. **Risk & Probability Engine / 위험·확률 엔진** — dilution, leverage, probability weighting, model risk / 희석·레버리지·확률·모델위험
7. **Decision Layer / 판단 레이어** — intrinsic value, expected IRR, margin of safety, thesis, invalidators / 내재가치·IRR·안전마진·논리·무효화조건

## Foundational rules / 기반 원칙

- **Facts ≠ assumptions / 사실 ≠ 가정**
- **Every material fact needs provenance / 모든 중요 사실은 출처를 가져야 함**
- **Growth must reconcile with reinvestment / 성장은 재투자와 일치해야 함**
- **Price prediction is secondary to expectation decomposition / 가격예측보다 시장 기대 분해가 우선**
- **Choose the model for the asset; do not force one DCF everywhere / 자산에 맞는 모델을 선택하고 DCF를 강제하지 않음**
- **Uncertainty must be modeled / 불확실성을 모델링함**
- **Same facts + assumptions + model version ⇒ same result / 동일 입력·모델 버전은 동일 결과를 재현해야 함**

See / 상세 문서:

- [`docs/FOUNDATION.md`](docs/FOUNDATION.md) — mission, scope, principles / 미션·범위·원칙
- [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) — canonical valuation method / 표준 가치분석 방법론
- [`schemas/valuation_case.schema.json`](schemas/valuation_case.schema.json) — machine-readable case contract / 기계 판독 사례 계약

## Initial reference cases / 초기 기준 사례

Three intentionally different public-equity cases bootstrap the methodology:

서로 다른 가치평가 체계를 대표하는 세 상장기업 사례로 방법론을 시작합니다.

- [`LS ELECTRIC`](analyses/equities/KR_010120_LS_ELECTRIC/) — quality growth + strong market-implied expectations / 고품질 성장 + 높은 시장 내재 기대
- [`LS Eco Energy / LS에코에너지`](analyses/equities/KR_229640_LS_ECO_ENERGY/) — growth DCF + reinvestment/margin interaction / 성장 DCF + 재투자·마진 상호작용
- [`Jet.AI`](analyses/equities/US_JTAI_JET_AI/) — venture/option-like + dilution + probability weighting / 벤처·옵션형 + 희석 + 확률가중

These are currently **reference-case skeletons**, not canonical recommendations. Exploratory figures must be re-sourced under the Hub evidence policy before becoming durable facts.

현재 세 사례는 **기준 사례 골격**이며 정식 투자추천이 아닙니다. 기존 탐색 수치는 Hub 근거정책에 따라 다시 출처화한 뒤에만 영구 사실로 승격됩니다.

## Repository layout / 저장소 구조

```text
Valuation-Intelligence-Hub/
├── docs/                 # Foundation and methodology / 기반·방법론
├── schemas/              # Versioned data contracts / 버전 관리 데이터 계약
├── src/valuation_hub/    # Shared valuation kernel / 공통 가치평가 커널
├── tests/                # Invariants and regression tests / 불변조건·회귀 테스트
└── analyses/             # Asset-specific inputs/results / 자산별 입력·결과
    └── equities/
```

The architecture will expand with adapters rather than duplicating valuation logic inside each analysis directory.

향후 구조는 각 분석 폴더에 계산 로직을 복제하지 않고 자산별 어댑터를 추가하는 방식으로 확장합니다.

## v0.1 roadmap / v0.1 로드맵

- [x] Bilingual foundation / 영한문 기반 원칙
- [x] Canonical methodology / 표준 방법론
- [x] Minimal FCFF/equity/IRR/probability kernel / 최소 가치평가 커널
- [x] Core invariants / 핵심 불변조건
- [x] Canonical valuation-case schema / 표준 사례 스키마
- [x] Three reference-case skeletons / 3개 기준 사례 골격
- [ ] Evidence/provenance policy and source-quality ladder / 근거정책·출처품질 체계
- [ ] Public-equity normalization adapter / 상장기업 정규화 어댑터
- [ ] Scenario engine / 시나리오 엔진
- [ ] Reverse-DCF solver / 역산 DCF 솔버
- [ ] Sensitivity engine / 민감도 엔진
- [ ] Re-source and reproduce LS ELECTRIC case / LS ELECTRIC 정식 재수집·재현
- [ ] Re-source and reproduce LS Eco Energy case / LS에코에너지 정식 재수집·재현
- [ ] Re-source and reproduce Jet.AI case / Jet.AI 정식 재수집·재현
- [ ] Add first non-equity adapter / 첫 비주식 자산 어댑터

## Language policy / 언어 원칙

Canonical user-facing documentation is bilingual in English and Korean. English preserves interoperable technical vocabulary; Korean is an equally authoritative interpretation. Code identifiers remain English unless interoperability requires otherwise.

정식 사용자 대상 문서는 영어와 한국어를 병기합니다. 영어는 기술용어의 상호운용성을 유지하고, 한국어는 동등한 권위의 해석을 제공합니다. 코드 식별자는 특별한 사유가 없으면 영어를 사용합니다.

## Status / 현재 상태

**Foundation bootstrap v0.1 — in progress / 기반 bootstrap v0.1 — 진행 중**

The repository currently establishes architecture and method boundaries. Production valuation results will be promoted only after evidence ingestion, normalization, model validation, and reproducibility checks.

현재 저장소는 아키텍처와 방법론 경계를 먼저 확립하고 있습니다. 실전 가치평가 결과는 근거 수집, 정규화, 모델 검증, 재현성 확인을 통과한 뒤 승격합니다.
