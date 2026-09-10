# Foundation / 기반 원칙

## Mission / 미션

Valuation-Intelligence-Hub is a reproducible, evidence-grounded system for separating **price** from **economic value** across asset classes. It converts market observations, accounting facts, business economics, uncertainty, and explicit assumptions into intrinsic value, market-implied expectations, expected return, and decision-relevant risk.

Valuation-Intelligence-Hub는 자산군 전반에서 **가격(price)**과 **경제적 가치(economic value)**를 분리하여 분석하기 위한 재현 가능하고 근거 중심의 시스템이다. 시장 관측치, 회계 사실, 사업경제성, 불확실성, 명시적 가정을 내재가치, 시장 내재 기대, 기대수익률, 의사결정 관련 위험으로 변환한다.

The Hub also serves as an **external Source of Truth (SoT) and grounding layer for AI-assisted analysis**, reducing hallucination, memory drift, unsupported reconstruction, and silent assumption substitution. Canonical repository state takes precedence over model recollection unless newer evidence is explicitly identified and reconciled.

Hub는 또한 **AI 보조 분석을 위한 외부 단일 진실원천(Source of Truth, SoT) 및 근거화 레이어**로 기능하여 AI 환각, 기억 드리프트, 근거 없는 재구성, 암묵적 가정 치환을 줄인다. 명시적으로 더 최신인 근거가 식별·조정되지 않는 한 표준 저장소 상태가 모델 기억보다 우선한다.

See `docs/AI_GROUNDING_POLICY.md`. / `docs/AI_GROUNDING_POLICY.md`를 참조한다.

## Scope / 범위

The Hub is not a stock screener and not a single DCF calculator. Public equities are the first reference adapter, not the end-state.

Hub는 종목 스크리너도 단일 DCF 계산기도 아니다. 상장주식은 첫 번째 기준 어댑터일 뿐 최종 범위가 아니다.

Target asset classes / 목표 자산군:

- Public equity / 상장기업
- Private company / 비상장기업
- Startup and venture / 스타트업·벤처
- Real estate / 부동산
- Infrastructure / 인프라
- Project finance / 프로젝트 파이낸스
- IP and technology assets / 지식재산·기술자산
- Other cash-generating or option-like assets / 기타 현금창출형·옵션형 자산

## Core question / 핵심 질문

The Hub should answer not only **“What is this asset worth?”** but also:

Hub는 단순히 **“이 자산의 가치는 얼마인가?”**뿐 아니라 다음 질문에 답해야 한다.

1. What facts support the valuation? / 어떤 사실이 가치평가를 뒷받침하는가?
2. Which assumptions drive the result? / 어떤 가정이 결과를 좌우하는가?
3. What future economics are implied by the current market price? / 현재 시장가격은 어떤 미래 경제성을 내재하는가?
4. How does value change under coherent Bear/Base/Bull scenarios? / 일관된 Bear/Base/Bull 시나리오에서 가치는 어떻게 변하는가?
5. What expected return is implied from price to value? / 현재 가격에서 가치까지의 기대수익률은 얼마인가?
6. What would invalidate the investment thesis? / 어떤 사건이나 지표가 투자 논리를 무효화하는가?
7. Can every material claim be traced to durable evidence or an explicit assumption? / 모든 중요 주장을 영구 근거나 명시적 가정까지 추적할 수 있는가?

## Non-negotiable principles / 비타협 원칙

### 1. Facts and assumptions are separate / 사실과 가정의 분리
Observed facts, normalized facts, forecasts, and analyst judgement must never be silently mixed.

관측 사실, 정규화 사실, 전망치, 분석가 판단은 암묵적으로 혼합해서는 안 된다.

### 2. Every material fact has provenance / 중요 사실은 모두 출처를 가진다
A number without period, unit, source, and as-of date is not analysis-grade input.

기간, 단위, 출처, 기준일이 없는 수치는 분석급 입력으로 인정하지 않는다.

### 3. Repository-grounded AI / 저장소 근거 기반 AI
For project state, accepted assumptions, model definitions, prior decisions, and canonical valuation facts, AI assistants must retrieve and use repository state rather than rely on conversational memory when repository access is available.

프로젝트 상태, 승인 가정, 모델 정의, 과거 판단, 표준 가치평가 사실에 대해서는 저장소 접근이 가능할 때 AI가 대화 기억에 의존하지 않고 저장소 상태를 조회·사용해야 한다.

### 4. Fail closed on unsupported material claims / 근거 없는 중요 주장 Fail-closed
Missing, conflicting, stale, or provenance-incomplete material inputs remain `UNKNOWN`, `HOLD`, or explicitly qualified. Plausibility is not evidence.

누락·충돌·노후화되었거나 출처가 불완전한 중요 입력은 `UNKNOWN`, `HOLD`, 또는 명시적 단서 상태로 남긴다. 그럴듯함은 근거가 아니다.

### 5. Growth must reconcile with reinvestment / 성장은 재투자와 일치해야 한다
Long-run growth cannot be modeled independently from ROIC, CAPEX, depreciation, and working-capital requirements.

장기 성장률은 ROIC, CAPEX, 감가상각, 운전자본 요구와 독립적으로 가정해서는 안 된다.

### 6. Price prediction is not the objective / 주가 예측 자체가 목적이 아니다
The primary objective is **expectation decomposition**: identify what the current price requires the business to become.

핵심 목적은 **기대 분해(expectation decomposition)**이다. 현재 가격이 정당화되기 위해 사업이 어떤 모습이 되어야 하는지 식별한다.

### 7. Model must fit the asset / 자산에 맞는 모델을 선택한다
Do not force FCFF DCF onto pre-revenue ventures, real estate, or option-like assets when probability-weighted, asset-based, project, or real-option methods are more suitable.

매출 전 벤처, 부동산, 옵션형 자산에 FCFF DCF를 억지로 적용하지 않는다. 확률가중, 자산가치, 프로젝트, 실물옵션 방식이 더 적합하면 그 모델을 사용한다.

### 8. Uncertainty is modeled, not hidden / 불확실성은 숨기지 않고 모델링한다
At minimum, scenario analysis and sensitivity analysis are required for material valuations.

중요 가치평가에는 최소한 시나리오 분석과 민감도 분석이 필요하다.

### 9. Outputs are reproducible and auditable / 결과는 재현·감사가 가능해야 한다
Given the same versioned facts, assumptions, and model version, another analyst should be able to reproduce the same result.

동일한 버전의 사실·가정·모델을 사용하면 다른 분석가도 동일한 결과를 재현할 수 있어야 한다.

### 10. Canonical promotion requires validation / 표준 승격에는 검증이 필요하다
AI-generated calculations or narrative do not become canonical solely because they appear plausible. Canonical promotion requires versioned inputs, compliant provenance, explicit assumptions, reproducible calculations, validation checks, and repository-recorded acceptance.

AI 생성 계산이나 서술은 그럴듯하다는 이유만으로 표준 상태가 되지 않는다. 표준 승격에는 버전 입력, 출처정책 준수, 명시적 가정, 재현 가능한 계산, 검증 체크, 저장소 승인 기록이 필요하다.

## Canonical analysis flow / 표준 분석 흐름

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
  ↓
CANONICAL PROMOTION / 표준 승격
```

## Core engines / 핵심 엔진

1. **Evidence Engine / 근거 엔진** — provenance, period, unit, source quality.
2. **Normalization Engine / 정규화 엔진** — accounting-to-economic conversion.
3. **Valuation Kernel / 가치평가 커널** — FCFF/FCFE/DCF/EV-to-equity and future valuation methods.
4. **Scenario Engine / 시나리오 엔진** — economically coherent Bear/Base/Bull cases and sensitivity.
5. **Reverse Valuation Engine / 역산 가치평가 엔진** — solve for market-implied growth, margins, reinvestment, or terminal economics.
6. **Risk & Probability Engine / 위험·확률 엔진** — dilution, leverage, concentration, probability weighting, model risk.
7. **Decision Layer / 판단 레이어** — intrinsic value, market-implied case, expected IRR, margin of safety, thesis and invalidators.
8. **AI Grounding Layer / AI 근거화 레이어** — canonical authority, session recovery, contradiction detection, claim classification, fail-closed controls.

## Bilingual documentation rule / 영한문 병기 원칙

User-facing canonical documentation must be bilingual in English and Korean. English defines interoperable technical terminology; Korean provides equally authoritative interpretation. Code identifiers remain English unless a compelling interoperability reason exists.

사용자 대상 정식 문서는 영어와 한국어를 병기한다. 영어는 상호운용 가능한 기술 용어를 정의하고, 한국어는 동등한 권위의 해석을 제공한다. 코드 식별자는 특별한 상호운용 사유가 없는 한 영어를 사용한다.

## Initial reference cases / 초기 기준 사례

The first three public-equity reference cases intentionally cover different valuation regimes:

초기 세 개 상장기업 기준 사례는 서로 다른 가치평가 체계를 의도적으로 포괄한다.

- **LS ELECTRIC** — high-quality growth with strong market-implied expectations / 고품질 성장기업과 높은 시장 내재 기대
- **LS Eco Energy** — conventional growth DCF with reinvestment and margin questions / 재투자·마진 변수가 중요한 전통적 성장 DCF
- **Jet.AI** — venture/option-like valuation with dilution and probability weighting / 희석·확률가중이 중요한 벤처·옵션형 가치평가

## Definition of done for v0.1 / v0.1 완료 정의

v0.1 foundation is complete when the repository contains:

v0.1 기반 구축은 다음을 갖추면 완료로 본다.

- Canonical bilingual methodology / 표준 영한문 방법론
- Versioned machine-readable schemas / 버전 관리 가능한 기계 판독 스키마
- A minimal tested valuation kernel / 최소 검증 가치평가 커널
- Scenario and reverse-valuation interfaces / 시나리오·역산 가치평가 인터페이스
- Evidence/provenance requirements / 근거·출처 요구사항
- AI grounding and anti-hallucination policy / AI 근거화·환각방지 정책
- Three public-equity reference-case skeletons / 세 개 상장기업 기준 사례 골격
- Clear extension boundary for non-equity asset adapters / 비주식 자산 어댑터 확장 경계
