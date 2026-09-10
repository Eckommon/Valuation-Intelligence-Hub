# Project State / 프로젝트 상태

> This file is the canonical human-and-AI session handoff for the active repository state. It must describe only repository-grounded state and must not depend on chat memory.
>
> 본 파일은 활성 저장소 상태에 대한 인간·AI 공통 정식 인계 문서이다. 저장소 근거만 기술하며 채팅 기억에 의존해서는 안 된다.

## Repository identity / 저장소 식별

- Repository / 저장소: `Eckommon/Valuation-Intelligence-Hub`
- Purpose / 목적: Cross-asset, evidence-grounded valuation intelligence system / 범자산 근거 기반 가치분석 인텔리전스 시스템
- Documentation rule / 문서 원칙: English + Korean bilingual canonical documentation / 정식 문서 영한문 병기

## Canonical baseline / 정식 기준선

### Bootstrap v0.1 / Bootstrap v0.1

Merged to `main` via:

`1d9881bcffb2499fdb72204070d058ef86676841`

Established Foundation, Methodology, AI Grounding Policy, valuation-case schema, tested valuation primitives, CI-ready repository structure, and three public-equity reference-case skeletons.

Foundation, Methodology, AI Grounding Policy, 가치평가 사례 스키마, 검증 가치평가 원시함수, CI 준비 구조, 세 개 상장기업 기준 사례 골격을 확립했다.

### M1 Evidence grounding + public-equity normalization / M1 근거화 + 상장기업 정규화

Merged to `main` via:

`e3a11259c0e248f055ee16466e08ccfef2a4d13e`

M1 established:

M1은 다음을 확립했다.

- bilingual evidence/provenance policy / 영한문 근거·출처 정책
- machine-readable evidence schema / 기계 판독 근거 스키마
- fail-closed canonical evidence-promotion gate / fail-closed 정식 근거 승격 게이트
- public-equity normalization primitives / 상장기업 정규화 원시함수
- Python 3.11/3.12 GitHub Actions CI / Python 3.11/3.12 GitHub Actions CI
- executable product end-state / 사용자 실행형 제품 최종 목표

Issue `#1` is `COMPLETED`.

Issue `#1`은 `COMPLETED` 상태다.

## Active mission / 활성 미션

- Issue: `#2 [M2] Scenario + reverse valuation engines / 시나리오 + 역산 가치평가 엔진`
- Branch: `mission/m2-scenario-reverse-valuation-v01`
- Status: `ACTIVE`

### Implemented on active branch / 활성 브랜치 구현 내역

- `src/valuation_hub/scenario.py` — explicit-period FCFF scenario runner and sensitivity grid / 명시기간 FCFF 시나리오 실행기·민감도 표
- `src/valuation_hub/reverse.py` — deterministic bisection solver, terminal-growth and revenue-scale reverse valuation / 결정론적 이분법 솔버, 영구성장·매출스케일 역산
- `tests/test_scenario_reverse.py` — scenario and reverse regression tests / 시나리오·역산 회귀 테스트
- `docs/SCENARIO_REVERSE_POLICY.md` — bilingual scenario/reverse-valuation governance / 영한문 시나리오·역산 가치평가 정책
- `PROJECT_STATE.md` — updated canonical handoff / 정식 인계 갱신

## Grounding authority / 근거화 권위

For project-state recovery, use this order:

프로젝트 상태 복구 시 다음 순서를 사용한다.

1. `main` canonical files and merged decisions / `main` 정식 파일·병합 결정
2. This `PROJECT_STATE.md` and active mission records / 본 상태파일·활성 미션 기록
3. Active Issue/PR/branch contents / 활성 Issue·PR·브랜치 내용
4. Primary evidence manifests for target cases / 대상 사례 1차 근거 매니페스트
5. Current chat / 현재 대화
6. AI memory / AI 기억

If repository state and AI recollection disagree, repository state wins unless a newer primary source requires explicit reconciliation.

저장소 상태와 AI 기억이 다르면 더 최신의 1차자료에 의한 명시적 조정이 필요한 경우를 제외하고 저장소 상태가 우선한다.

## Product end-state / 제품 최종 목표

The project must eventually deliver a user-executable valuation tool, not only documentation or libraries. The intended path is shared kernel → stable case format → CLI → user-friendly Web UI → optional API/automation, all using the same valuation kernel.

프로젝트는 최종적으로 문서나 라이브러리뿐 아니라 사용자가 직접 실행할 수 있는 가치분석 도구를 제공해야 한다. 동일 가치평가 커널을 공유하며 커널 → 안정적 사례 포맷 → CLI → 사용자 친화 Web UI → 선택적 API·자동화 순으로 발전한다.

## Exact resume point / 정확한 재개점

Complete M2 by validating the scenario and reverse-valuation implementation under CI, opening and reviewing the M2 pull request, and verifying Issue #2 acceptance criteria. Do not canonicalize the three numerical reference cases until M2 is merged.

CI에서 시나리오·역산 가치평가 구현을 검증하고 M2 PR을 개설·검토하며 Issue #2 완료조건을 확인해 M2를 완료한다. M2 병합 전에는 세 기준 사례 수치 결과를 정식 승격하지 않는다.
