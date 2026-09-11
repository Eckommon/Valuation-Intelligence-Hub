# LS Eco Energy Reference Case / LS에코에너지 기준 사례

## Role in the Hub / Hub 내 역할

This case is the reference for a **conventional growth-company DCF where valuation depends on the interaction among revenue growth, margin expansion, working capital, and reinvestment efficiency**.

이 사례는 **매출성장, 마진확대, 운전자본, 재투자 효율의 상호작용에 가치가 좌우되는 전통적 성장기업 DCF**의 기준 사례다.

## Primary questions / 핵심 질문

- Is the current market price closer to Base or Bull economics? / 현재 시장가격은 Base와 Bull 중 어느 경제성에 더 가까운가?
- Can higher-value product mix expand EBIT margin without disproportionate reinvestment? / 고부가 제품 믹스가 과도한 재투자 없이 EBIT 마진을 확대할 수 있는가?
- How sensitive is value to working-capital intensity as revenue scales? / 매출 확대 시 운전자본 강도에 가치가 얼마나 민감한가?

## Required methods / 필수 방법

- Five valuation lenses / 5대 가치평가 렌즈
- FCFF DCF / FCFF DCF
- Bear/Base/Bull / 3대 시나리오
- WACC × terminal-growth sensitivity / WACC × 영구성장률 민감도
- Reverse DCF / 역산 DCF
- Expected IRR / 기대 IRR

## Canonical branch result / 활성 브랜치 기준 결과

`CANONICAL_REFERENCE_RESULT_V0_1`

Evidence gate / 근거 게이트: `PASS_MATERIAL_INPUTS_RECONCILED`

Snapshot market price / 스냅샷 시장가격: **KRW 47,900**

- Bear intrinsic value/share / Bear 내재가치: **KRW 4,445**
- Base intrinsic value/share / Base 내재가치: **KRW 27,326**
- Bull intrinsic value/share / Bull 내재가치: **KRW 57,748**
- Classification / 분류: `MARKET_PRICE_BETWEEN_MODELED_BASE_AND_BULL`

The result is regression-locked against the shared FCFF scenario engine. See `REPORT.md`, `case_inputs.json`, `valuation_result.json`, and the evidence bundles.

결과는 공통 FCFF 시나리오 엔진에 대해 회귀 잠금되어 있다. 상세 내용은 `REPORT.md`, `case_inputs.json`, `valuation_result.json`, evidence 파일을 참조한다.
