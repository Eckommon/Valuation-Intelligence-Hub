# Jet.AI Reference Case / Jet.AI 기준 사례

## Role in the Hub / Hub 내 역할

This case is the reference for a **venture/option-like public company where dilution, financing, business-perimeter change, and probability-weighted outcomes dominate conventional earnings multiples**.

이 사례는 **희석, 자금조달, 사업범위 변경, 확률가중 결과가 전통적 이익배수보다 더 중요한 벤처·옵션형 상장기업**의 기준 사례다.

## Model selection / 모델 선택

`PROBABILITY_WEIGHTED_VENTURE_OPTION_MODEL`

Conventional reported P/E and historical FCFF extrapolation are rejected because the July 2026 spin-off created a business-perimeter discontinuity and the continuing business remains loss-making and financing-dependent.

2026년 7월 분할로 사업범위 단절이 발생했고 계속사업은 적자·자금조달 의존 상태이므로 보고 PER과 과거 FCFF 단순연장은 사용하지 않는다.

## Canonical branch result / 활성 브랜치 기준 결과

`CANONICAL_REFERENCE_RESULT_V0_1`

Evidence gate / 근거 게이트: `PASS_VENTURE_MODEL_INPUTS_RECONCILED`

Snapshot market price / 스냅샷 시장가격: **USD 1.28**

- Failure / 실패: **60%**, present value/share **$0**
- Survival / 생존: **30%**, present value/share **$2.423**
- Breakout / 돌파: **10%**, present value/share **$25.199**
- Probability-weighted present value/share / 확률가중 현재 주당가치: **$3.247**
- Reverse diagnostic / 역산 진단: Survival 30% 고정 시 시장가격이 요구하는 Breakout 확률 약 **2.20%**
- Model risk / 모델위험: **VERY_HIGH**

## Transaction treatment / 거래 처리

The flyExclusive consideration is historical distributed SpinCo value and is not re-added to ongoing JTAI. The July 15, 2026 reverse-takeover LOI is non-binding and remains an excluded optional overlay until definitive evidence changes its status.

flyExclusive 대가는 과거 SpinCo 분배가치이므로 현재 JTAI에 재합산하지 않는다. 2026년 7월 15일 RTO LOI는 비구속적이므로 확정 근거가 상태를 변경하기 전까지 제외된 옵션 오버레이로 유지한다.

## Primary questions / 핵심 질문

- Can the company survive funding needs without destructive dilution? / 파괴적 희석 없이 자금수요를 버틸 수 있는가?
- Can post-spin AI infrastructure reach a durable revenue base? / 분리 후 AI 인프라가 지속 가능한 매출 기반에 도달할 수 있는가?
- How much value depends on a low-probability Breakout tail? / 가치 중 작은 확률의 Breakout 꼬리에 얼마나 의존하는가?

See `REPORT.md`, `case_inputs.json`, `valuation_result.json`, and evidence bundles for the reproducible reference case.

재현 가능한 기준 사례는 `REPORT.md`, `case_inputs.json`, `valuation_result.json`, evidence 파일을 참조한다.
