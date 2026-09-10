# LS ELECTRIC Reference Valuation / LS ELECTRIC 기준 가치평가

## Status / 상태

**CANONICAL_REFERENCE_RESULT_V0_1**

This report is a reproducible reference case for the Hub methodology. It is not a price forecast or investment recommendation.

본 보고서는 Hub 방법론의 재현 가능한 기준 사례이며 주가 예측이나 투자권고가 아니다.

## 1. Evidence state / 근거 상태

- Valuation date / 가치평가 기준일: `2026-09-10`
- Market price / 시장가격: `KRW 206,000`
- Diluted/economic shares / 희석·경제적 주식수: `148.82 million`
- Evidence promotion gate / 근거 승격 게이트: `PASS_MATERIAL_INPUTS_RECONCILED`
- Model / 모델: `reference-equity-fcff-v0.1`

The case uses reconciled market, financial and cost-of-capital evidence bundles. Facts, normalized facts, assumptions and derived outputs remain distinct.

본 사례는 조정된 시장·재무·자본비용 근거 묶음을 사용한다. 사실, 정규화 사실, 가정, 파생 산출물은 서로 분리한다.

## 2. Historical economic context / 과거 경제성 맥락

Canonical inputs retain FY2025 official revenue, operating income and net income, 2026 Q2 official revenue/operating income/order backlog, the 5-for-1 stock split, and reconciled current market/capital-structure data.

정식 입력에는 FY2025 공식 매출·영업이익·순이익, 2026 Q2 공식 매출·영업이익·수주잔고, 5:1 주식분할, 조정된 현재 시장·자본구조 데이터가 포함된다.

The model does not extrapolate recent negative free cash flow mechanically. Working-capital absorption is explicitly separated from CAPEX and forecast through operating NWC ratios.

최근 음의 잉여현금흐름을 기계적으로 영구화하지 않는다. 운전자본 현금흡수는 CAPEX와 분리하고 영업운전자본 비율을 통해 전망한다.

## 3. Scenario design / 시나리오 설계

Bear/Base/Bull jointly vary revenue, EBIT margin, CAPEX intensity, NWC efficiency, WACC, terminal growth and future net debt. They are conditional economic states, not assigned probabilities.

Bear/Base/Bull은 매출, EBIT margin, CAPEX 강도, 운전자본 효율, WACC, 영구성장률, 미래 순부채를 함께 변화시킨 조건부 경제상태이며 확률값이 아니다.

| Scenario / 시나리오 | 2030 Revenue / 매출 | 2030 EBIT Margin | WACC | Terminal g |
|---|---:|---:|---:|---:|
| Bear | KRW 8.13tn | 10.0% | 14.0% | 2.0% |
| Base | KRW 10.39tn | 13.2% | 12.6% | 2.5% |
| Bull | KRW 12.39tn | 15.5% | 10.5% | 3.0% |

## 4. FCFF results / FCFF 결과

| Scenario | 2026 FCFF | 2027 FCFF | 2028 FCFF | 2029 FCFF | 2030 FCFF |
|---|---:|---:|---:|---:|---:|
| Bear | -78.9bn | 233.8bn | 370.6bn | 439.0bn | 490.2bn |
| Base | -3.2bn | 344.4bn | 572.8bn | 764.6bn | 913.5bn |
| Bull | 92.3bn | 465.2bn | 738.8bn | 1,087.4bn | 1,299.6bn |

The pattern is economically important: even strong earnings growth can coexist with weak early FCFF while growth consumes CAPEX and working capital.

경제적으로 중요한 점은 강한 이익성장과 초기의 약한 FCFF가 동시에 존재할 수 있다는 것이다. 성장 과정에서 CAPEX와 운전자본이 현금을 흡수하기 때문이다.

## 5. Intrinsic value and 2030 terminal equity value / 내재가치와 2030 말 자기자본가치

| Scenario | Current intrinsic value/share / 현재 내재가치 | 2030 terminal value/share / 2030 말 가치 | Annualized return from KRW 206,000 / 연환산수익률 |
|---|---:|---:|---:|
| Bear | KRW 13,705 | KRW 21,281 | -40.97% |
| Base | KRW 41,475 | KRW 58,265 | -25.42% |
| Bull | KRW 88,458 | KRW 118,589 | -12.03% |

Under this v0.1 reference model, the market price is above even the modeled Bull intrinsic value.

본 v0.1 기준모델에서는 시장가격이 모델링된 Bull 내재가치보다도 높다.

## 6. Base sensitivity / Base 민감도

Value per share / 주당가치:

| WACC \ g | 1.5% | 2.0% | 2.5% | 3.0% | 3.5% |
|---|---:|---:|---:|---:|---:|
| 10.5% | 49,891 | 52,582 | 55,609 | 59,041 | 62,962 |
| 11.5% | 43,627 | 45,717 | 48,040 | 50,636 | 53,556 |
| 12.6% | 38,069 | 39,692 | **41,475** | 43,444 | 45,630 |
| 13.5% | 34,299 | 35,639 | 37,101 | 38,702 | 40,464 |
| 14.5% | 30,740 | 31,839 | 33,030 | 34,324 | 35,735 |

This table demonstrates model sensitivity but does not make the market price disappear: even the low-WACC/high-g corner remains materially below KRW 206,000.

민감도 표는 모델의 할인율·영구성장률 민감도를 보여주지만 현재 시장가격과의 간극을 제거하지는 못한다. 가장 낮은 WACC·높은 g 조합도 206,000원보다 현저히 낮다.

## 7. Reverse DCF / 역산 DCF

Holding Base margins, WACC and terminal growth fixed, the current engine requires approximately **4.62x** proportional scaling of revenue and revenue-linked D&A/CAPEX/Delta-NWC to match the KRW 206,000 market price.

Base 마진, WACC, 영구성장률을 고정하면 현재 엔진에서 206,000원의 시장가격을 맞추기 위해 매출과 매출 연동 D&A/CAPEX/Delta-NWC를 약 **4.62배** 비례 확대해야 한다.

Applied mechanically to the Base 2030 revenue, this corresponds to approximately **KRW 47.94tn** of 2030 revenue. This is deliberately labeled a **stress diagnostic**, not a forecast.

Base 2030 매출에 기계적으로 적용하면 약 **47.94조원**의 2030 매출에 해당한다. 이는 의도적으로 **스트레스 진단**으로 분류하며 전망치가 아니다.

## 8. Interpretation / 해석

### Business quality / 기업의 질

The evidence supports a strong growth-quality business with material order backlog and improving profitability.

근거자료는 유의미한 수주잔고와 수익성 개선을 가진 강한 성장·품질 기업을 지지한다.

### Valuation / 가치평가

The v0.1 FCFF framework indicates that current market price embeds economics stronger than the modeled Bull scenario.

v0.1 FCFF 프레임워크에서는 현재 시장가격이 모델링된 Bull 시나리오보다 더 강한 경제성을 내재한다.

### Decision discipline / 판단 규율

The Hub therefore separates three statements that must not be conflated:

Hub는 다음 세 문장을 혼합하지 않는다.

1. **LS ELECTRIC can be a high-quality company. / LS ELECTRIC은 고품질 기업일 수 있다.**
2. **Its business can continue to grow rapidly. / 사업은 빠르게 성장할 수 있다.**
3. **Its current market price can still require exceptionally demanding future economics. / 동시에 현재 가격은 매우 높은 미래 경제성을 요구할 수 있다.**

This separation between business quality, intrinsic value and investment attractiveness is a core Hub principle.

기업의 질, 내재가치, 투자매력도의 분리는 Hub의 핵심 원칙이다.

## 9. Reproducibility / 재현성

Canonical files / 정식 파일:

- `evidence_manifest.json`
- `evidence_market.json`
- `evidence_financials.json`
- `evidence_cost_of_capital.json`
- `case_inputs.json`
- `valuation_result.json`

A future model revision must preserve prior versions or explicitly document why assumptions, evidence or model logic changed.

향후 모델 개정은 이전 버전을 보존하거나 근거·가정·모델 논리가 변경된 이유를 명시해야 한다.
