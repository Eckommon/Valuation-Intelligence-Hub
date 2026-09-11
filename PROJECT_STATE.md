# Project State / 프로젝트 상태

> Canonical human-and-AI handoff. Repository-grounded state outranks chat or AI recollection.
>
> 인간·AI 공통 정식 인계 문서. 저장소 근거 상태는 채팅·AI 기억보다 우선한다.

## Repository identity / 저장소 식별

- Repository / 저장소: `Eckommon/Valuation-Intelligence-Hub`
- Purpose / 목적: Cross-asset, evidence-grounded valuation intelligence system / 범자산 근거 기반 가치분석 인텔리전스 시스템
- Documentation / 문서: English + Korean bilingual / 영한문 병기
- Product strategy / 제품 전략: **Web-first hybrid** — Web UI primary, CLI/local secondary, one shared kernel / **웹 우선 하이브리드** — Web UI 주 인터페이스, CLI·로컬 보조, 단일 공통 커널

## Canonical baseline / 정식 기준선

- Bootstrap v0.1: `1d9881bcffb2499fdb72204070d058ef86676841`
- M1 Evidence grounding + public-equity normalization: `e3a11259c0e248f055ee16466e08ccfef2a4d13e` — #1 `COMPLETED`
- M2 Scenario + reverse valuation: `2b6d7522e7d847673a7310b9e7f4346cd26cb59e` — #2 `COMPLETED`
- M3 Evidence-grounded reference cases: `5c39c6a1857a5b4aeffa9782399e24bcbd77c0ae` — #3 `COMPLETED`
- M4 Executable case runner + CLI: `db14a21bb706f4f3cd74f5a33d88ca5937249aa5` — #8 `COMPLETED`
- M5 Read-oriented Web Application MVP: `5867363d26d4efa57e5fb92d4861de9bfbf00d7f` — #12 `COMPLETED`
- M6 Interactive preview + evidence browser: `caf7576c1a2c13916449d445f5badc3a29712d36` — #14 `COMPLETED`

M6 PR and post-merge main CI passed on Python 3.11/3.12. Main CI run `34552290097` = `completed/success`.

M6 PR 및 병합 후 main CI는 Python 3.11/3.12에서 통과했다. main CI run `34552290097` = `completed/success`.

## Canonical product capability / 정식 제품 기능

- versioned case registry + grounded `case_service` / 버전 사례 레지스트리 + 근거화 case service
- CLI: `vih list`, `validate`, `run`, `report`, `web`
- local-first Web dashboard/detail/API / 로컬 우선 Web 대시보드·상세·API
- evidence browser / 근거 탐색
- in-memory `PREVIEW_NOT_CANONICAL` scenario sandbox / 메모리 기반 비정식 시나리오 샌드박스
- strict fail-closed constraints and canonical-byte immutability tests / 엄격 fail-closed·정식파일 byte 불변성 테스트

## Active mission / 활성 미션

- Issue: `#16 [M7] Product UX + valuation visualization / 제품 UX + 가치평가 시각화`
- Branch: `mission/m7-product-ux-visualization-v01`
- Status: `ACTIVE_IMPLEMENTATION`

## Current M7 implementation / 현재 M7 구현

### Visualization components / 시각화 컴포넌트

- `src/valuation_hub/visualization.py`
- dependency-free HTML/SVG / 외부의존 없는 HTML·SVG
- equity market-vs-Bear/Base/Bull chart / 시장가 vs 3대 시나리오
- FCFF forecast trend / FCFF 전망 추세
- venture probability/outcome chart / 벤처 확률·결과
- evidence classification summary / 근거 분류 요약

Visualization consumes computed runtime output and owns no valuation formula.

시각화는 계산 완료 런타임 결과만 소비하며 가치평가 공식을 소유하지 않는다.

### Product Web adapter / 제품 Web 어댑터

- `src/valuation_hub/web_product.py`
- layers product UX over the stable M6 Web/API handler / 안정된 M6 Web/API handler 위 제품 UX 계층
- clear `CANONICAL / 정식` versus `PREVIEW · NOT CANONICAL / 비정식` states
- responsive case hero, status cards and information hierarchy / 반응형 사례 헤더·상태카드·정보계층
- preview value/market/gap summary cards plus expandable JSON diagnostics / preview 가치·시장·괴리 요약 + JSON 진단
- evidence classification filters / 근거 분류 필터

`vih web` now routes to `web_product.serve` while inherited M6 APIs and preview contracts remain available.

`vih web`은 이제 `web_product.serve`로 라우팅하며 기존 M6 API·preview 계약은 그대로 유지한다.

### Tests / 테스트

- `tests/test_visualization.py`
- `tests/test_web_product.py`
- all previous M1–M6 tests remain mandatory / 기존 M1–M6 테스트 계속 필수

### Documentation / 문서

- `docs/PRODUCT_UX.md`

## Grounding authority / 근거화 권위

1. `main` canonical files and merged decisions / `main` 정식 파일·병합 결정
2. `PROJECT_STATE.md` and active mission / 상태파일·활성 미션
3. active Issue/PR/branch / 활성 Issue·PR·브랜치
4. primary evidence manifests / 1차 근거 매니페스트
5. current chat / 현재 대화
6. AI memory / AI 기억

Repository state wins over AI recollection unless newer primary evidence requires explicit reconciliation.

더 최신 1차자료의 명시적 조정이 필요한 경우를 제외하고 저장소 상태가 AI 기억보다 우선한다.

## Product end-state / 제품 최종 목표

The final product remains Web-first hybrid. Product UX must make value, evidence, uncertainty and market-implied expectations understandable without hiding model risk or turning preview experiments into canonical facts.

최종 제품은 웹 우선 하이브리드다. 제품 UX는 모델위험을 숨기거나 preview 실험을 정식 사실로 바꾸지 않으면서 가치·근거·불확실성·시장 내재 기대를 이해하기 쉽게 보여야 한다.

## Exact resume point / 정확한 재개점

Open the M7 PR and run the full Python 3.11/3.12 CI matrix. Fix any visualization, product-handler, or inherited Web regression. Merge only if `vih web` serves the product adapter, canonical calculations remain unchanged, enhanced case/evidence pages expose grounded runtime values, and all M1–M7 tests pass. After M7, prioritize a stable user-created case/import workflow before live-data automation or canonical write-back.

M7 PR을 개설하고 Python 3.11/3.12 전체 CI를 실행한다. 시각화·제품 handler·기존 Web 회귀 실패를 수정한다. `vih web`이 제품 어댑터를 제공하고 정식 계산이 불변이며 개선된 사례·근거 화면이 근거화 런타임값을 노출하고 M1–M7 전체 테스트가 통과할 때만 병합한다. M7 이후에는 실시간 데이터 자동화·정식 write-back보다 안정적인 사용자 사례 생성·가져오기 흐름을 우선한다.
