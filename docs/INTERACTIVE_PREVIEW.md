# Interactive Preview + Evidence Browser / 인터랙티브 미리보기 + 근거 탐색

## Purpose / 목적

M6 adds an interactive analysis surface without weakening canonical grounding. Users may inspect evidence and experiment with assumptions, but preview results are always isolated from canonical repository state.

M6는 정식 근거화를 약화하지 않고 인터랙티브 분석 화면을 추가한다. 사용자는 근거를 탐색하고 가정을 실험할 수 있지만 preview 결과는 항상 정식 저장소 상태와 격리된다.

> **PREVIEW / NOT CANONICAL**  
> **미리보기 / 정식 결과 아님**

## Evidence browser / 근거 탐색

Routes / 경로:

```text
GET /case/<case_id>/evidence
GET /api/cases/<case_id>/evidence
```

The view exposes claim classification, metric, value, period/as-of, publisher, source tier and locator when available.

화면은 가능한 경우 주장분류, 지표, 값, 기간·기준일, 발행자, 출처등급, 원문 위치를 노출한다.

Canonical claim classes remain:

정식 주장분류는 다음을 유지한다.

`FACT / NORMALIZED_FACT / ASSUMPTION / DERIVED / INTERPRETATION / UNKNOWN`

Evidence browsing is read-only. / 근거 탐색은 읽기 전용이다.

## Sandbox preview / 샌드박스 미리보기

Endpoint / 엔드포인트:

```text
POST /api/cases/<case_id>/preview
```

The request is evaluated in memory and discarded after the response. No case file is written.

요청은 메모리에서 계산 후 응답과 함께 소멸하며 사례 파일을 기록하지 않는다.

### FCFF cases / FCFF 사례

Supported preview controls / 지원 조작:

- source scenario: Bear/Base/Bull / 기준 시나리오
- WACC / WACC
- terminal growth / 영구성장률
- proportional revenue scale / 매출 비례배율
- EBIT-margin delta / EBIT 마진 증감
- CAPEX-to-sales delta / CAPEX/매출 비율 증감
- NWC-to-sales delta / NWC/매출 비율 증감

The preview continues to use `run_fcff_scenario`; the Web/service layer does not contain an alternate DCF formula.

preview는 계속 `run_fcff_scenario`를 사용하며 Web·서비스 계층에 별도 DCF 공식을 두지 않는다.

### Venture/option cases / 벤처·옵션 사례

Supported controls / 지원 조작:

- explicit scenario probabilities / 명시적 시나리오 확률
- terminal-revenue scale / 종착 매출 배율
- EV/Sales multiple scale / EV/Sales 배수 조정
- dilution scale / 희석 배율

The probabilities must sum to 1.0 and are passed to the shared venture kernel.

확률합은 1.0이어야 하며 공통 Venture 커널로 전달한다.

## Fail-closed constraints / Fail-closed 제약

Preview rejects, among other invalid states:

preview는 다음 비정상 상태 등을 차단한다.

- terminal growth >= WACC / 영구성장률 ≥ WACC
- non-finite numeric inputs / 비유한 숫자
- probability sum != 1 / 확률합 불일치
- unsafe extreme preview scales / 안전한도 초과 배율
- negative CAPEX or NWC ratios after override / 조정 후 CAPEX·NWC 비율 음수
- unknown or unsupported cases / 미등록·미지원 사례

## Canonical immutability / 정식 상태 불변

Preview does not update:

preview는 다음 파일을 갱신하지 않는다.

- `case_inputs.json`
- `valuation_result.json`
- evidence bundles/manifests / 근거 묶음·매니페스트
- registry / 레지스트리

Tests hash canonical files before and after preview execution and require unchanged bytes.

테스트는 preview 전후 정식 파일 해시가 동일함을 요구한다.

## Product meaning / 제품적 의미

M6 separates two concepts that must never be confused:

M6는 반드시 구분해야 할 두 개념을 분리한다.

1. **Canonical valuation / 정식 가치평가** — versioned, evidence-gated, regression-locked / 버전·근거게이트·회귀잠금
2. **Interactive preview / 인터랙티브 미리보기** — user experiment, temporary, non-canonical / 사용자 실험·일시적·비정식

A future write-back workflow, if implemented, must require a separate reviewed promotion process rather than converting preview output directly into canonical assumptions.

향후 write-back을 구현하더라도 preview 결과를 직접 정식 가정으로 바꾸지 않고 별도 검토·승격 절차를 거쳐야 한다.
