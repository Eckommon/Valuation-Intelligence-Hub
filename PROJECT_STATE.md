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

M5 pull-request CI and post-merge main CI passed on Python 3.11/3.12. Main CI run: `34551943851` = `completed/success`.

M5 PR CI와 병합 후 main CI는 Python 3.11/3.12에서 통과했다. main CI run `34551943851` = `completed/success`.

## Canonical product capability / 정식 제품 기능

### M4 executable layer / M4 실행계층

- versioned registry / 버전 사례 레지스트리
- `case_service` shared application boundary / 공통 애플리케이션 서비스
- `vih list`, `validate`, `run`, `report`
- runtime/canonical drift validation / 실행값·정식값 drift 검증

### M5 Web MVP / M5 Web MVP

- `vih web`
- local-first default `127.0.0.1:8765`
- grounded case dashboard and details / 근거화 사례 대시보드·상세
- JSON case endpoints / JSON 사례 endpoint
- real HTTP integration tests / 실제 HTTP 통합테스트

## Active mission / 활성 미션

- Issue: `#14 [M6] Interactive scenario preview + evidence browser / 인터랙티브 시나리오 미리보기 + 근거 탐색`
- Branch: `mission/m6-interactive-preview-evidence-v01`
- Status: `ACTIVE_IMPLEMENTATION`

## Current M6 implementation / 현재 M6 구현

### Interactive service / 인터랙티브 서비스

- `src/valuation_hub/interactive.py`
- `evidence_view()` — canonical evidence aggregation / 정식 근거 집계
- `preview_case()` — in-memory, non-persistent scenario preview / 메모리 기반 비영구 시나리오 preview

Preview state is always:

preview 상태는 항상 다음과 같다.

`PREVIEW_NOT_CANONICAL`

### Evidence browser / 근거 탐색

- `GET /case/<case_id>/evidence`
- `GET /api/cases/<case_id>/evidence`
- claim class, metric, value, period/as-of, publisher, tier and locator exposure / 주장분류·지표·값·기간·발행자·등급·원문 위치 노출
- read-only / 읽기 전용

### Scenario preview / 시나리오 미리보기

- `POST /api/cases/<case_id>/preview`
- FCFF: source scenario, WACC, terminal growth, revenue scale, EBIT-margin delta, CAPEX/NWC ratio deltas
- Venture: explicit probabilities, revenue/multiple/dilution scales
- shared FCFF/Venture kernels only / 공통 FCFF·Venture 커널만 사용
- no write-back / write-back 없음

### Browser controls / 브라우저 조작

Case pages contain sandbox controls and call the preview endpoint with JavaScript. Preview output is visibly labeled `PREVIEW · NOT CANONICAL / 비정식`.

사례 화면은 샌드박스 조작 UI를 제공하고 JavaScript로 preview endpoint를 호출한다. 결과는 `PREVIEW · NOT CANONICAL / 비정식`으로 명확히 표시한다.

### M6 tests / M6 테스트

- `tests/test_interactive.py` — evidence, preview economics, fail-closed constraints, canonical-file hash immutability
- `tests/test_web_interactive.py` — evidence/preview HTTP integration and invalid-state errors
- existing M1–M5 regression tests remain required / 기존 M1–M5 회귀테스트 계속 필수

### Documentation / 문서

- `docs/INTERACTIVE_PREVIEW.md`

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

The final product remains Web-first hybrid. Canonical valuation and user experimentation are deliberately separated: canonical results are evidence-gated/versioned/regression-locked; previews are temporary and never auto-promoted.

최종 제품은 웹 우선 하이브리드다. 정식 가치평가와 사용자 실험을 의도적으로 분리한다. 정식 결과는 근거게이트·버전·회귀잠금 대상이고 preview는 일시적이며 자동승격하지 않는다.

## Exact resume point / 정확한 재개점

Open the M6 pull request and run the full Python 3.11/3.12 CI matrix. Fix failures using preserved diagnostics. Merge only if all prior canonical regressions remain green, evidence browsing works, invalid preview states fail closed, and preview execution leaves canonical case files byte-identical. After M6 merge, close #14 and define the next mission around product-quality UX and scenario visualization before adding live-data ingestion or canonical write-back.

M6 PR을 개설하고 Python 3.11/3.12 전체 CI를 실행한다. 진단 로그를 근거로 실패를 수정한다. 기존 정식 회귀테스트가 모두 유지되고 근거 탐색이 작동하며 잘못된 preview가 fail-closed하고 preview 후 정식 사례 파일 bytes가 동일한 경우에만 병합한다. M6 이후에는 실시간 데이터 수집·정식 write-back보다 먼저 제품급 UX와 시나리오 시각화를 다음 미션으로 정의한다.
