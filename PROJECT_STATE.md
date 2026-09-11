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
- M1 Evidence grounding + public-equity normalization: `e3a11259c0e248f055ee16466e08ccfef2a4d13e` — Issue #1 `COMPLETED`
- M2 Scenario + reverse valuation engines: `2b6d7522e7d847673a7310b9e7f4346cd26cb59e` — Issue #2 `COMPLETED`
- M3 Evidence-grounded reference cases: `5c39c6a1857a5b4aeffa9782399e24bcbd77c0ae` — Issue #3 `COMPLETED`
- M4 Executable case runner + CLI: `db14a21bb706f4f3cd74f5a33d88ca5937249aa5` — Issue #8 `COMPLETED`

M4 main-branch CI run `34551597634` completed successfully on the configured Python 3.11/3.12 matrix.

M4 `main` CI run `34551597634`은 설정된 Python 3.11/3.12 matrix에서 성공 완료했다.

## Canonical executable layer / 정식 실행형 계층

M4 established:

M4에서 다음을 확립했다.

- `registry/cases.json` — versioned case registry / 버전 사례 레지스트리
- `src/valuation_hub/case_service.py` — shared application service / 공통 애플리케이션 서비스
- `src/valuation_hub/cli.py` — executable `vih` CLI / 실행형 `vih` CLI
- `vih list`, `validate`, `run`, `report`
- runtime-to-canonical drift validation / 런타임-정식결과 drift 검증
- fail-closed unknown/malformed/non-PASS/unsupported behavior / 미등록·오류·미통과·미지원 fail-closed

All three canonical reference cases are executable through the shared service contract:

세 정식 기준 사례는 모두 공통 서비스 계약으로 실행 가능하다.

1. `KR_010120_LS_ELECTRIC` — `equity_fcff`
2. `KR_229640_LS_ECO_ENERGY` — `equity_fcff`
3. `US_JTAI_JET_AI` — `venture_probability`

## Active mission / 활성 미션

- Issue: `#12 [M5] Read-oriented Web Application MVP / 읽기 중심 Web 애플리케이션 MVP`
- Branch: `mission/m5-web-app-mvp-v01`
- Status: `ACTIVE_IMPLEMENTATION`

## Current M5 implementation / 현재 M5 구현

### Thin Web adapter / 얇은 Web 어댑터

- `src/valuation_hub/web.py`
- Standard-library local HTTP server / 표준 라이브러리 로컬 HTTP 서버
- Web layer calls `case_service`; valuation formulas are not duplicated / Web은 `case_service`를 호출하며 가치평가 공식 복제 금지
- Default bind: `127.0.0.1:8765` / 기본 바인드

### Web routes / Web 경로

- `GET /` — dashboard / 대시보드
- `GET /case/<case_id>` — case detail / 사례 상세
- `GET /healthz` — health / 상태확인
- `GET /api/cases` — JSON case list / JSON 사례목록
- `GET /api/cases/<case_id>` — grounded JSON case view / 근거화 JSON 사례보기

### CLI extension / CLI 확장

- `vih web`
- `vih web --host 127.0.0.1 --port 8765`

### Tests / 테스트

- `tests/test_web.py` — dashboard, detail rendering, HTTP endpoints, unknown-case fail-closed / 대시보드·상세·HTTP·미등록 fail-closed
- `tests/test_cli_web.py` — CLI-to-Web adapter dispatch / CLI→Web 어댑터 디스패치

### Documentation / 문서

- `docs/WEB_MVP.md` — M5 architecture, local execution, routes, scope and security limits / M5 아키텍처·로컬 실행·경로·범위·보안 제한

## Grounding authority / 근거화 권위

1. `main` canonical files and merged decisions / `main` 정식 파일·병합 결정
2. This `PROJECT_STATE.md` and active mission records / 본 상태파일·활성 미션 기록
3. Active Issue/PR/branch contents / 활성 Issue·PR·브랜치 내용
4. Primary evidence manifests / 1차 근거 매니페스트
5. Current chat / 현재 대화
6. AI memory / AI 기억

If repository state conflicts with AI recollection, repository state wins unless newer primary evidence requires explicit reconciliation.

저장소 상태와 AI 기억이 충돌하면 더 최신 1차자료에 의한 명시적 조정이 필요한 경우를 제외하고 저장소 상태가 우선한다.

## Product end-state / 제품 최종 목표

The final product remains Web-first hybrid. The browser experience is the primary interface for non-developers; CLI/local execution remains the deterministic private/batch/automation path. Future hosted Web, API, and optional desktop shell must reuse the same registry, evidence gates, case service and valuation kernels.

최종 제품은 웹 우선 하이브리드다. 비개발자의 주 인터페이스는 브라우저이며 CLI·로컬 실행은 결정론적 비공개·대량·자동화 경로다. 향후 호스팅 Web, API, 선택적 데스크톱 셸은 동일 레지스트리·근거게이트·case service·가치평가 커널을 재사용해야 한다.

## Exact resume point / 정확한 재개점

Validate M5 with the full Python 3.11/3.12 CI suite. Inspect and fix any Web/CLI integration failures. Open the M5 pull request and merge only after dashboard/detail/API views reproduce grounded canonical case values and unknown cases fail closed. After M5 merge, close Issue #12 and define the next mission around interactive scenario controls and evidence browsing without introducing live-data ingestion or write-back prematurely.

Python 3.11/3.12 전체 CI로 M5를 검증한다. Web·CLI 통합 실패가 있으면 수정한다. 대시보드·상세·API가 근거화 정식 사례값을 재현하고 미등록 사례가 fail-closed하는 경우에만 M5 PR을 병합한다. M5 병합 후 Issue #12를 종료하고, 실시간 데이터 수집·write-back을 성급히 도입하지 않은 상태에서 인터랙티브 시나리오 조작과 근거 탐색을 다음 미션으로 정의한다.
