# Scenario & Reverse Valuation Policy / 시나리오·역산 가치평가 정책

## Purpose / 목적

Scenario analysis must represent coherent economic states, not arbitrary single-variable tweaks. Reverse valuation must identify what the current price requires the asset to become, while clearly separating solved implications from analyst assumptions.

시나리오 분석은 임의의 단일변수 조정이 아니라 경제적으로 일관된 상태를 표현해야 한다. 역산 가치평가는 현재 가격이 정당화되기 위해 자산이 어떤 경제성을 가져야 하는지 식별하되, 역산 결과와 분석가 가정을 명확히 분리해야 한다.

## Scenario classes / 시나리오 구분

The default public-equity scenario set is:

기본 상장기업 시나리오는 다음과 같다.

- `BEAR` — adverse but plausible operating and financing conditions / 불리하지만 현실 가능한 영업·금융 조건
- `BASE` — central evidence-consistent case / 근거와 일치하는 중심 시나리오
- `BULL` — favorable but economically coherent case / 유리하지만 경제적으로 일관된 시나리오
- `MARKET_IMPLIED` — solved state required by observed market price / 관측 시장가격이 요구하는 역산 상태

`MARKET_IMPLIED` is never a recommendation and is never silently treated as an analyst forecast.

`MARKET_IMPLIED`는 투자추천이 아니며 분석가 전망으로 암묵 승격하지 않는다.

## Coupled scenario drivers / 연동 시나리오 변수

Material scenarios SHOULD jointly address:

중요 시나리오는 원칙적으로 다음 변수를 함께 다룬다.

- revenue growth / 매출 성장률
- operating margin / 영업이익률
- tax / 세율
- CAPEX and depreciation / CAPEX와 감가상각
- working-capital intensity / 운전자본 집약도
- ROIC and reinvestment / ROIC와 재투자
- WACC / WACC
- terminal growth / 영구성장률
- dilution when material / 중요 시 희석
- asset-specific risk drivers / 자산별 핵심 위험변수

A scenario that assumes higher growth while simultaneously assuming implausibly lower reinvestment requires explicit economic justification.

더 높은 성장을 가정하면서 비현실적으로 낮은 재투자를 동시에 가정하려면 명시적 경제적 근거가 필요하다.

## DCF invariants / DCF 불변조건

- `terminal_growth < WACC` must hold / `영구성장률 < WACC` 필수
- diluted shares must be positive / 희석주식수 양수
- periods must be ordered and unique / 예측기간 순서·중복 금지
- currencies must be normalized before aggregation / 합산 전 통화 정규화
- scenario output must be reproducible from versioned inputs / 버전 입력으로 결과 재현 가능

Invalid states fail closed rather than being clipped or silently repaired.

비정상 상태는 임의 보정하지 않고 fail-closed한다.

## Reverse valuation / 역산 가치평가

Reverse valuation MAY solve for variables such as:

역산 가치평가는 다음 변수를 역산할 수 있다.

- required terminal growth / 요구 영구성장률
- required revenue scale or CAGR / 요구 매출규모·CAGR
- required EBIT margin / 요구 EBIT margin
- required FCFF / 요구 FCFF
- implied ROIC/reinvestment combination / 내재 ROIC·재투자 조합
- implied dilution tolerance / 내재 허용 희석수준

Every reverse output MUST identify which variables were held constant and which variable was solved.

모든 역산 결과는 어떤 변수를 고정하고 어떤 변수를 역산했는지 밝혀야 한다.

## Sensitivity / 민감도

Sensitivity grids are diagnostic, not probability distributions. A WACC × terminal-growth table shows model dependence; it does not indicate that every cell is equally likely.

민감도 표는 진단 도구이지 확률분포가 아니다. WACC × 영구성장률 표는 모델 의존성을 보여주며 각 셀이 동일 확률이라는 뜻이 아니다.

## Expected return / 기대수익률

Scenario value and expected return are distinct concepts. IRR or annualized return should be calculated from current price to a clearly defined future equity value and horizon, with dividends, dilution, and distributions handled explicitly when material.

시나리오 가치와 기대수익률은 별도 개념이다. IRR 또는 연환산수익률은 현재가격에서 명확한 미래 자기자본가치와 기간을 기준으로 계산하며 중요 시 배당·희석·분배를 명시적으로 처리한다.

## Probability weighting / 확률가중

Probability-weighted expected value is especially relevant for venture, binary, project-development, regulatory, or option-like assets. Scenario values must remain visible separately from the probability-weighted aggregate.

확률가중 기대가치는 벤처·이진사건·프로젝트 개발·규제·옵션형 자산에서 특히 중요하다. 시나리오별 가치는 확률가중 합계와 별도로 유지해야 한다.
