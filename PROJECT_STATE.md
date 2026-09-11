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
- M7 Product UX + valuation visualization: `243cea0233031088fac8edb0362971326840b858` — #16 `COMPLETED`

M7 PR and post-merge main CI passed on Python 3.11/3.12. Main CI run `34552658612` = `completed/success`.

M7 PR 및 병합 후 main CI는 Python 3.11/3.12에서 통과했다. main CI run `34552658612` = `completed/success`.

## Canonical product capability / 정식 제품 기능

- versioned case registry + grounded `case_service` / 버전 사례 레지스트리 + 근거화 case service
- CLI: `vih list`, `validate`, `run`, `report`, `web`
- local-first product Web UI with valuation visualization / 로컬 우선 제품 Web UI·가치 시각화
- evidence browser + classification filters / 근거 탐색·분류 필터
- canonical/preview visual separation / 정식·preview 시각 분리
- in-memory `PREVIEW_NOT_CANONICAL` scenario sandbox / 메모리 기반 비정식 시나리오 샌드박스
- strict fail-closed constraints and canonical-byte immutability tests / 엄격 fail-closed·정식파일 byte 불변성 테스트

## Active mission / 활성 미션

- Issue: `#18 [M8] User draft cases + safe import workflow / 사용자 Draft 사례 + 안전한 가져오기 흐름`
- Branch: `mission/m8-user-draft-import-v01`
- Status: `ACTIVE_IMPLEMENTATION`

## Current M8 implementation / 현재 M8 구현

### Draft contract / Draft 계약

- `schemas/draft_case.schema.json`
- Draft state is fixed as `DRAFT_USER_SUPPLIED / NOT_CANONICAL`
- supported draft models: `equity_fcff`, `venture_probability`

### Templates / 템플릿

- `templates/draft_equity_fcff.json`
- `templates/draft_venture_probability.json`
- all template values are examples, not canonical evidence / 템플릿 값은 예시이며 정식 근거가 아님

### Draft service / Draft 서비스

- `src/valuation_hub/draft_service.py`
- strict finite-number and economic validation / 엄격한 숫자·경제 검증
- FCFF Draft executes through shared `run_fcff_scenario` / 공통 FCFF 커널 실행
- Venture Draft executes through shared probability-weighted venture kernel / 공통 벤처 확률가중 커널 실행
- all results: `canonical=false`, `grounding=USER_SUPPLIED_UNVERIFIED`
- no registry/promotion/write-back path / 레지스트리·승격·write-back 경로 없음

### CLI / CLI

- `vih draft-template <equity_fcff|venture_probability>`
- `vih draft-validate <file>`
- `vih draft-run <file>`
- machine-readable `--json` remains available / 기계판독 `--json` 지원

### Web Draft Lab / Web Draft 랩

- `src/valuation_hub/web_draft.py`
- dashboard entry to `/draft` / 대시보드 진입점
- `GET /api/drafts/templates/<model>`
- `POST /api/drafts/validate`
- `POST /api/drafts/run`
- in-memory only; payload is not saved / 메모리 실행만 수행, payload 저장 없음
- `vih web` routes through the Draft-enabled product adapter / `vih web` Draft 지원 제품 어댑터 사용

### Local workspace / 로컬 작업공간

- `.gitignore` protects `/workspace/user_cases/**`
- `workspace/README.md`
- `workspace/user_cases/.gitkeep`
- Draft workspace Git exclusion is convenience, not a security boundary / Git 제외는 편의장치이며 보안경계가 아님

### Tests / 테스트

- `tests/test_draft_service.py`
- `tests/test_cli_draft.py`
- `tests/test_web_draft.py`
- canonical registry/case hashes must remain unchanged after Draft execution / Draft 실행 후 정식 레지스트리·사례 해시 불변
- all prior M1–M7 regressions remain mandatory / 기존 M1–M7 회귀테스트 계속 필수

### Documentation / 문서

- `docs/USER_DRAFTS.md`

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

The product remains Web-first hybrid. M8 introduces a safe user-input path but deliberately does not weaken the canonical evidence boundary. User calculations and canonical knowledge are separate states.

제품은 웹 우선 하이브리드를 유지한다. M8은 안전한 사용자 입력경로를 추가하지만 정식 근거 경계를 약화하지 않는다. 사용자 계산과 정식 지식은 별도 상태다.

## Exact resume point / 정확한 재개점

Open the M8 PR and run the full Python 3.11/3.12 CI matrix. Fix Draft validation, CLI, Web or inherited regression failures from preserved diagnostics. Merge only if both templates validate/run, invalid economics fail closed, Draft Web/CLI flows work, and canonical registry/evidence/result files remain byte-identical after Draft execution. After M8, design an explicit reviewed Draft→candidate→canonical promotion workflow before adding automated live-data ingestion.

M8 PR을 개설하고 Python 3.11/3.12 전체 CI를 실행한다. 보존된 진단을 근거로 Draft 검증·CLI·Web·기존 회귀 실패를 수정한다. 두 템플릿이 검증·실행되고 비정상 경제상태가 fail-closed하며 Draft Web·CLI가 작동하고 Draft 실행 후 정식 레지스트리·근거·결과 파일 bytes가 동일한 경우에만 병합한다. M8 이후에는 자동 실시간 데이터 수집보다 먼저 명시적 검토 기반 Draft→candidate→canonical 승격 절차를 설계한다.
