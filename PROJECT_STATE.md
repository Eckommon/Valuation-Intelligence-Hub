# Project State / 프로젝트 상태

> This file is the canonical human-and-AI session handoff for the active repository state. It must describe only repository-grounded state and must not depend on chat memory.
>
> 본 파일은 활성 저장소 상태에 대한 인간·AI 공통 정식 인계 문서이다. 저장소 근거만 기술하며 채팅 기억에 의존해서는 안 된다.

## Repository identity / 저장소 식별

- Repository / 저장소: `Eckommon/Valuation-Intelligence-Hub`
- Purpose / 목적: Cross-asset, evidence-grounded valuation intelligence system / 범자산 근거 기반 가치분석 인텔리전스 시스템
- Documentation rule / 문서 원칙: English + Korean bilingual canonical documentation / 정식 문서 영한문 병기
- Product strategy / 제품 전략: **Web-first hybrid** — Web UI primary, CLI/local secondary, one shared kernel / **웹 우선 하이브리드** — Web UI 주 인터페이스, CLI·로컬 보조, 단일 공통 커널

## Canonical baseline / 정식 기준선

### Bootstrap v0.1
`1d9881bcffb2499fdb72204070d058ef86676841`

### M1 Evidence grounding + public-equity normalization / M1 근거화 + 상장기업 정규화
`e3a11259c0e248f055ee16466e08ccfef2a4d13e`
Issue `#1`: `COMPLETED`

### M2 Scenario + reverse valuation engines / M2 시나리오 + 역산 가치평가 엔진
`2b6d7522e7d847673a7310b9e7f4346cd26cb59e`
Issue `#2`: `COMPLETED`

### M3 Evidence-grounded reference cases / M3 근거 기반 기준 사례
Merged to `main` via / `main` 병합:

`5c39c6a1857a5b4aeffa9782399e24bcbd77c0ae`

Issue `#3`: `COMPLETED`

M3 established three regression-locked reference cases and the reusable dilution-aware venture probability kernel.

M3는 세 개의 회귀 잠금 기준 사례와 재사용 가능한 희석 반영 벤처 확률가중 커널을 확립했다.

- LS ELECTRIC — `MARKET_PRICE_ABOVE_MODELED_BULL`
- LS Eco Energy / LS에코에너지 — `MARKET_PRICE_BETWEEN_MODELED_BASE_AND_BULL`
- Jet.AI — `PROBABILITY_WEIGHTED_VENTURE_OPTION_MODEL`, model risk `VERY_HIGH`

The M3 CI suite passed on Python 3.11 and 3.12 before merge. CI now preserves pytest diagnostics as workflow artifacts.

M3 병합 전 Python 3.11/3.12 전체 CI가 통과했으며 CI는 pytest 진단을 workflow artifact로 보존한다.

## Active mission / 활성 미션

- Issue: `#8 [M4] Executable case runner + CLI foundation / 실행형 사례 실행기 + CLI 기반`
- Branch: `mission/m4-executable-runner-cli-v01`
- Status: `ACTIVE_IMPLEMENTATION`

## Current M4 implementation / 현재 M4 구현

### Versioned registry / 버전 관리 레지스트리

- `registry/cases.json`
- Registry version / 레지스트리 버전: `0.1`
- Registered cases / 등록 사례: 3
- Model routes / 모델 라우트: `equity_fcff`, `venture_probability`

### Shared application service / 공통 애플리케이션 서비스

- `src/valuation_hub/case_service.py`

The service layer:

서비스 계층은 다음을 수행한다.

1. locates and validates the versioned registry / 버전 레지스트리 탐색·검증
2. validates required case artifacts and evidence promotion gates / 필수 사례 산출물·근거 승격게이트 검증
3. routes to the existing FCFF or venture kernel / 기존 FCFF 또는 Venture 커널로 라우팅
4. recomputes valuation from versioned case inputs / 버전 입력에서 가치 재계산
5. compares runtime output with canonical stored result / 런타임 결과와 정식 저장결과 비교
6. fails closed on unknown, malformed, unsupported, non-PASS, or drifting cases / 미등록·오류·미지원·미통과·drift 사례 fail-closed

Default drift tolerance is model-specific:

모델별 기본 drift 허용오차:

- `equity_fcff`: `1.0` currency unit/share / 주당 통화단위 1.0
- `venture_probability`: `1e-6` currency unit/share / 주당 통화단위 1e-6

### CLI / 실행형 CLI

- `src/valuation_hub/cli.py`
- installed command / 설치 명령: `vih`
- module execution / 모듈 실행: `python -m valuation_hub.cli`

Commands / 명령:

- `vih list`
- `vih validate <case-id>`
- `vih run <case-id>`
- `vih report <case-id>`
- global `--json` option / 전역 `--json` 옵션

### Tests / 테스트

- `tests/test_case_service.py`
- `tests/test_cli.py`

The tests require all three M3 cases to validate and execute through the shared service layer while reproducing their regression-locked values.

테스트는 M3의 세 사례가 공통 서비스 계층을 통해 검증·실행되고 회귀 잠금 값을 재현하도록 요구한다.

### Documentation / 문서

- `docs/EXECUTION.md` — bilingual execution architecture, commands, failure guarantees, limitations / 영한문 실행 아키텍처·명령·실패보장·제한사항

## Grounding authority / 근거화 권위

1. `main` canonical files and merged decisions / `main` 정식 파일·병합 결정
2. This `PROJECT_STATE.md` and active mission records / 본 상태파일·활성 미션 기록
3. Active Issue/PR/branch contents / 활성 Issue·PR·브랜치 내용
4. Primary evidence manifests for target cases / 대상 사례 1차 근거 매니페스트
5. Current chat / 현재 대화
6. AI memory / AI 기억

If repository state and AI recollection disagree, repository state wins unless a newer primary source requires explicit reconciliation.

저장소 상태와 AI 기억이 다르면 더 최신의 1차자료에 의한 명시적 조정이 필요한 경우를 제외하고 저장소 상태가 우선한다.

## Product end-state / 제품 최종 목표

The project must deliver a **web-first hybrid valuation product**. Non-developers use a human-friendly Web UI; advanced/private/batch workflows use CLI/local execution. Web, CLI, API and any future desktop shell must use the same kernel, schemas, evidence gates, case registry and application-service contract.

프로젝트는 **웹 우선 하이브리드 가치분석 제품**을 제공해야 한다. 비개발자는 사용자 친화 Web UI를 사용하고 고급·비공개·대량 작업은 CLI·로컬 실행을 사용한다. Web, CLI, API, 향후 데스크톱 셸은 동일 커널·스키마·근거게이트·사례 레지스트리·애플리케이션 서비스 계약을 사용해야 한다.

## Exact resume point / 정확한 재개점

Finish M4 by synchronizing the repository README with the M3/M4 canonical state, opening the M4 pull request, and running the full Python 3.11/3.12 CI suite including CLI integration tests. Merge only after all registered cases validate and reproduce canonical outputs through `case_service`. After M4 merge, close Issue #8 and create M5 for a user-friendly read-oriented Web application MVP over the same service contract.

README를 M3/M4 정식 상태와 동기화하고 M4 PR을 개설한 뒤 CLI 통합테스트를 포함한 Python 3.11/3.12 전체 CI를 실행하여 M4를 완료한다. 모든 등록 사례가 `case_service`를 통해 정식 결과를 검증·재현할 때만 병합한다. M4 병합 후 Issue #8을 종료하고 동일 서비스 계약 위에 사용자 친화 읽기 중심 Web Application MVP를 구축하는 M5를 생성한다.
