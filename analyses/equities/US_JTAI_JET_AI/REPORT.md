# Jet.AI Reference Valuation / Jet.AI 기준 가치평가

## Status / 상태

`CANONICAL_REFERENCE_RESULT_V0_1` on the active M3 branch. This is a venture/option reference model, not a target price or investment recommendation.

활성 M3 브랜치의 `CANONICAL_REFERENCE_RESULT_V0_1`이다. 벤처·옵션형 기준 모델이며 목표주가 또는 투자권고가 아니다.

## Why conventional DCF is rejected / 왜 전통적 DCF를 사용하지 않는가

Jet.AI completed the spin-off of its fractional and jet-card business on July 13, 2026. Historical H1 2026 consolidated results still include that legacy perimeter. SEC Separation pro-forma financials show 2025 continuing-business revenue of about **$2.98m** and operating loss of about **$4.59m**. Therefore historical TTM revenue, reported net income, and conventional P/E are not economically comparable to the post-spin business.

Jet.AI는 2026년 7월 13일 fractional·jet-card 사업을 분리했다. 2026 H1 역사적 연결실적에는 해당 과거 사업범위가 여전히 포함된다. SEC Separation 프로포마 기준 2025 계속사업 매출은 약 **$2.98m**, 영업손실은 약 **$4.59m**이다. 따라서 역사적 TTM 매출·보고 순이익·전통 PER은 분리 후 사업과 경제적으로 직접 비교할 수 없다.

## Dilution and financing / 희석과 자금조달

The company raised about **$27.7m** of gross ATM equity proceeds in H1 2026. The current share snapshot is about **3.56m shares**, up roughly **230% QoQ**. June 30 cash of $10.61m was pre-spin consolidated cash, and $5.3m was transferred to SpinCo at closing. Cash is therefore not treated as a guaranteed equity-value floor.

회사는 2026 H1 ATM 주식발행으로 약 **$27.7m**를 조달했다. 현재 주식수 스냅샷은 약 **3.56m주**로 QoQ 약 **230% 증가**했다. 6월 30일 현금 $10.61m은 분리 전 연결 현금이며 종결 시 $5.3m이 SpinCo로 이전됐다. 따라서 현금을 보장된 자기자본가치 하한으로 간주하지 않는다.

## Five lenses / 5대 렌즈

| Lens / 렌즈 | Result / 결과 |
|---|---:|
| Market cap / 2025 pro-forma continuing sales | **1.53x** |
| Market cap / Operating income | **N/M — operating loss** |
| P/E | **N/M — normalized continuing operations loss-making** |
| P/FCF | **N/M — negative/core perimeter unstable** |
| Reverse valuation | **~2.20% Breakout probability required** with Survival fixed at 30% |

The reported trailing P/E is deliberately rejected because non-operating and pre-separation effects make it unsuitable for recurring owner economics.

보고 TTM PER은 비영업·분리 전 효과 때문에 반복 가능한 주주경제성을 나타내지 못하므로 의도적으로 사용하지 않는다.

## Probability-weighted venture model / 확률가중 벤처 모델

| Scenario | Probability | 2030 Revenue | EV/Sales | 2030 diluted shares | Terminal value/share | Present value/share |
|---|---:|---:|---:|---:|---:|---:|
| Failure | 60% | $0 | 0x | 15.0m | $0 | $0 |
| Survival | 30% | $50m | 2.0x | 12.0m | $7.50 | $2.423 |
| Breakout | 10% | $200m | 4.0x | 10.0m | $78.00 | $25.199 |

A **30% venture discount rate** is used as an explicit model-risk assumption, not as a falsely precise WACC.

**30% 벤처 할인율**을 사용하며 이는 정밀한 WACC로 가장하지 않는 명시적 모델위험 가정이다.

Probability-weighted present value/share / 확률가중 현재 주당가치:

**$3.247**

Snapshot market price / 스냅샷 시장가격:

**$1.28**

The model's probability-weighted value is above the market price, but this does **not** make Jet.AI a conventional undervaluation case. Most value comes from a small Breakout tail, and the result is extremely sensitive to success probability, future dilution, terminal multiple, and funding survival.

모델의 확률가중 가치는 시장가격보다 높지만 이를 전통적 저평가 사례로 해석해서는 안 된다. 가치의 상당 부분이 작은 Breakout 꼬리확률에서 발생하며 성공확률, 미래 희석, 종착 배수, 자금조달 생존 여부에 매우 민감하다.

## Conditional return distribution / 조건부 수익률 분포

From the $1.28 snapshot price to 2030 terminal per-share outcomes:

$1.28 스냅샷 가격에서 2030년 조건부 주당가치까지의 연환산 결과:

- Failure / 실패: **-100%**
- Survival / 생존: **+50.76% p.a.**
- Breakout / 돌파: **+159.69% p.a.**

The probability-weighted terminal payoff is $10.05/share, corresponding to a descriptive CAGR of about 61.36%. This is **not a deterministic expected IRR** and should not be presented as a forecast return.

확률가중 종착 지급액은 주당 $10.05이고 설명용 CAGR은 약 61.36%다. 이는 **결정론적 기대 IRR이 아니며** 전망수익률로 제시해서는 안 된다.

## Reverse probability / 역산 확률

Holding Survival probability at 30% and keeping all conditional valuations unchanged, the $1.28 market price requires only about **2.20% Breakout probability**, with the residual ~67.8% assigned to Failure.

Survival 확률을 30%로 고정하고 모든 조건부 가치가 동일하다고 하면 $1.28 시장가격을 맞추는 데 필요한 Breakout 확률은 약 **2.20%**이며 나머지 약 67.8%는 Failure다.

This is a market-implied probability diagnostic, not an empirical probability estimate.

이는 시장 내재 확률 진단이며 경험적 성공확률 추정치가 아니다.

## Transaction overlays / 거래 오버레이

- flyExclusive consideration: historical SpinCo distribution, excluded from ongoing JTAI value / 과거 SpinCo 분배가치로 현재 JTAI 가치에서 제외
- July 15 reverse-takeover LOI: **non-binding**, excluded from core expected value / 7월 15일 RTO LOI는 **비구속적**이므로 핵심 기대가치에서 제외
- StratGrid: $1.75m funded investment is retained as an actual current investment fact / StratGrid $1.75m 실제 투자사실은 보존

## Reference-case lesson / 기준 사례의 의미

Jet.AI demonstrates the Hub's model-selection rule: **do not force every asset into FCFF DCF**. For early-transition, financing-dependent, highly diluted companies, valuation should expose survival, dilution, probability, and optionality rather than hide them inside a single terminal-growth assumption.

Jet.AI는 Hub의 모델선택 원칙을 보여준다. **모든 자산에 FCFF DCF를 강제하지 않는다.** 사업전환 초기·자금조달 의존·고희석 기업에서는 생존, 희석, 확률, 옵션가치를 단일 영구성장률 안에 숨기지 않고 명시해야 한다.
