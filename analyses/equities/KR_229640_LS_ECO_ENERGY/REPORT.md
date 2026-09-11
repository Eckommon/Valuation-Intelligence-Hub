# LS Eco Energy Reference Valuation / LS에코에너지 기준 가치평가

## Status / 상태

`CANONICAL_REFERENCE_RESULT_V0_1` on the active M3 branch. This is a reproducible model result, not an investment recommendation.

활성 M3 브랜치의 `CANONICAL_REFERENCE_RESULT_V0_1`이다. 재현 가능한 모델 결과이며 투자권고가 아니다.

## Snapshot / 스냅샷

- Valuation date / 가치평가기준일: **2026-09-10**
- Market price / 시장가격: **KRW 47,900**
- Diluted shares / 희석주식수: **30.62M**
- TTM revenue / TTM 매출: **KRW 1.11723tn**
- TTM EBIT / TTM EBIT: **KRW 73.207bn**
- TTM net income / TTM 순이익: **KRW 44.3bn**
- TTM FCF / TTM FCF: **KRW -2.627bn**
- TTM working-capital cash use / TTM 운전자본 현금사용: **KRW 64.217bn**

The latest negative FCF is not treated as a permanent business condition. The model reconstructs Delta-NWC from explicit NWC/sales paths because rapid growth absorbed substantial working capital.

최근 음수 FCF를 영구적인 사업상태로 간주하지 않는다. 고성장 과정에서 상당한 운전자본이 흡수됐으므로 모델은 명시적인 NWC/매출 경로에서 Delta-NWC를 다시 구축한다.

## Five lenses / 5대 렌즈

| Lens / 렌즈 | Result / 결과 |
|---|---:|
| Market cap / Sales | 1.31x |
| Market cap / EBIT | 20.03x |
| P/E | 33.11x |
| P/FCF | N/M — negative TTM FCF |
| Reverse DCF | Base cash economics require ~1.67x scale / Base 현금경제성 약 1.67배 필요 |

## Scenario valuation / 시나리오 가치평가

| Scenario | Current intrinsic value/share / 현재 내재가치 | 2030 terminal equity value/share / 2030 가치 | Annualized return from KRW 47,900 / 연환산 수익률 |
|---|---:|---:|---:|
| Bear | KRW **4,445** | KRW **8,231** | **-33.56%** |
| Base | KRW **27,326** | KRW **38,272** | **-5.08%** |
| Bull | KRW **57,748** | KRW **77,704** | **+11.89%** |

## Base economics / Base 경제성

The Base case starts from KRW 1.30tn 2026 revenue and reaches roughly KRW 1.95tn by 2030. EBIT margin rises from 7.3% to 9.0%, CAPEX/sales normalizes around 1.5%, and NWC/sales improves from 23.5% to 19.0%. Base WACC is 11.3% and terminal growth is 2.5%.

Base는 2026년 매출 1.30조원에서 출발해 2030년 약 1.95조원에 도달한다. EBIT margin은 7.3%에서 9.0%로 상승하고 CAPEX/매출은 약 1.5%로, NWC/매출은 23.5%에서 19.0%로 정상화한다. Base WACC는 11.3%, 영구성장률은 2.5%다.

## Reverse valuation / 역산 가치평가

At fixed Base margins, WACC and terminal growth, the model must scale Base revenue and revenue-linked D&A/CAPEX/Delta-NWC by approximately **1.6725x** to reach the snapshot market price. That mechanical scale maps Base 2030 revenue from KRW 1.95tn to about **KRW 3.27tn**.

Base 마진, WACC, 영구성장률을 고정하면 스냅샷 시장가격을 맞추기 위해 Base 매출과 매출 연동 D&A/CAPEX/Delta-NWC를 약 **1.6725배** 확대해야 한다. 기계적으로 환산하면 Base 2030 매출 약 1.95조원이 약 **3.27조원**이 된다.

This is an expectation diagnostic, not a revenue forecast.

이는 시장 내재 기대를 측정하는 진단값이지 매출 전망이 아니다.

## Interpretation / 해석

Unlike LS ELECTRIC, the snapshot price is not above the modeled Bull case. LS Eco Energy is therefore a useful reference case for a company where the investment question is genuinely **Base versus Bull** rather than **Bull versus Hyper-Bull**.

LS ELECTRIC과 달리 스냅샷 시장가격은 모델링된 Bull case를 넘지 않는다. 따라서 LS에코에너지는 **Bull 대 Hyper-Bull**이 아니라 실제로 **Base 대 Bull** 가능성을 판단하는 성장기업 기준 사례다.

The key observable variables are high-value cable and busduct mix, sustained EBIT-margin expansion, working-capital normalization, and whether new growth projects force CAPEX materially above modeled levels.

핵심 관찰변수는 고부가 케이블·버스덕트 믹스, EBIT margin의 지속 확대, 운전자본 정상화, 신규 성장사업으로 CAPEX가 모델 가정보다 크게 증가하는지 여부다.

## Provenance / 출처

All material inputs are versioned in `evidence_market.json`, `evidence_financials.json`, `evidence_cost_of_capital.json`, and `evidence_manifest.json`. Facts and assumptions remain separate.

모든 중요 입력은 해당 evidence 파일과 manifest에서 버전관리되며 사실과 가정을 분리한다.
