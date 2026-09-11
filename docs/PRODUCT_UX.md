# Product UX + Visualization / 제품 UX + 시각화

## Objective / 목표

M7 turns the local Web application into a clearer decision surface while preserving the same grounded services and kernels. Visualization is an interpretation layer over computed results, never a second valuation implementation.

M7은 동일한 근거화 서비스·커널을 유지하면서 로컬 Web 애플리케이션을 더 명확한 의사결정 화면으로 개선한다. 시각화는 계산된 결과 위의 해석·표현 계층이며 두 번째 가치평가 구현이 아니다.

## Canonical vs preview / 정식 vs 미리보기

The UI must visually distinguish:

UI는 다음 두 상태를 시각적으로 구분해야 한다.

- **CANONICAL / 정식** — evidence-gated, versioned, regression-locked results / 근거게이트·버전·회귀잠금 결과
- **PREVIEW · NOT CANONICAL / 비정식** — temporary user experiment, never persisted or promoted automatically / 일시적 사용자 실험, 영속화·자동승격 금지

## Equity visualization / 상장기업 시각화

Equity FCFF pages show:

상장기업 FCFF 화면은 다음을 표시한다.

1. market price versus Bear/Base/Bull value per share / 시장가격 vs Bear·Base·Bull 주당가치
2. explicit FCFF forecast trend for Bear/Base/Bull / 3대 시나리오 명시기간 FCFF 추세
3. exact numeric tables underneath charts / 차트 아래 정확한 수치표

Charts consume `case_service` runtime results. / 차트는 `case_service` 런타임 결과만 소비한다.

## Venture visualization / 벤처 시각화

Venture/option pages show:

벤처·옵션 화면은 다음을 표시한다.

- market price / 시장가격
- probability-weighted expected present value / 확률가중 기대 현재가치
- conditional scenario present values / 조건부 시나리오 현재가치
- scenario probabilities in labels / 라벨의 시나리오 확률

The chart does not imply that conditional breakout value is an expected value. / 대성공 조건부 가치를 기대가치처럼 표현해서는 안 된다.

## Scenario Lab / 시나리오 랩

Preview execution now provides a concise result summary:

preview 실행은 간결한 결과 요약을 제공한다.

- preview value / preview 가치
- canonical market price / 정식 시장가격
- percentage gap / 괴리율
- expandable JSON diagnostics / 펼칠 수 있는 JSON 진단

The raw JSON remains available for auditability, but it is no longer the only presentation.

감사가능성을 위해 원시 JSON을 유지하지만 더 이상 유일한 표현방식은 아니다.

## Evidence UX / 근거 UX

Evidence pages provide classification-count controls for:

근거 화면은 다음 분류 카운트·필터를 제공한다.

`FACT / NORMALIZED_FACT / ASSUMPTION / DERIVED / INTERPRETATION / UNKNOWN`

Filtering is client-side display behavior only and never changes evidence state.

필터링은 클라이언트 표시 동작일 뿐 근거 상태를 변경하지 않는다.

## Technology constraints / 기술 제약

M7 intentionally uses dependency-free HTML/CSS/SVG and small browser JavaScript. No frontend build system is introduced yet.

M7은 의도적으로 외부의존 없는 HTML·CSS·SVG와 소규모 브라우저 JavaScript를 사용한다. 아직 별도 프론트엔드 빌드 시스템을 도입하지 않는다.

The production command `vih web` is routed to `web_product.py`, which layers UX over the stable M6 `web.py` API/preview handler. This isolates presentation evolution from the grounded HTTP contract.

제품 실행명령 `vih web`은 `web_product.py`로 라우팅하며, 안정된 M6 `web.py` API·preview handler 위에 UX를 추가한다. 이를 통해 근거화 HTTP 계약과 표현 계층의 진화를 분리한다.

## Future transition / 향후 전환

A heavier frontend framework should be considered only when interactive complexity, hosted deployment, accessibility requirements, or component reuse clearly exceed the maintainability of the current thin adapter.

인터랙티브 복잡성, 호스팅 배포, 접근성 요구, 컴포넌트 재사용이 현재 얇은 어댑터의 유지보수성을 명확히 넘어설 때만 더 무거운 프론트엔드 프레임워크를 검토한다.
