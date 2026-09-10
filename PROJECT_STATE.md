# Project State / 프로젝트 상태

> This file is the canonical human-and-AI session handoff for the active repository state. It must describe only repository-grounded state and must not depend on chat memory.
>
> 본 파일은 활성 저장소 상태에 대한 인간·AI 공통 정식 인계 문서이다. 저장소 근거만 기술하며 채팅 기억에 의존해서는 안 된다.

## Repository identity / 저장소 식별

- Repository / 저장소: `Eckommon/Valuation-Intelligence-Hub`
- Purpose / 목적: Cross-asset, evidence-grounded valuation intelligence system / 범자산 근거 기반 가치분석 인텔리전스 시스템
- Documentation rule / 문서 원칙: English + Korean bilingual canonical documentation / 정식 문서 영한문 병기

## Canonical baseline / 정식 기준선

Bootstrap v0.1 was merged to `main` via merge commit:

Bootstrap v0.1은 다음 merge commit으로 `main`에 병합되었다.

`1d9881bcffb2499fdb72204070d058ef86676841`

The baseline establishes Foundation, Methodology, AI Grounding Policy, valuation-case schema, tested core valuation primitives, and three public-equity reference-case skeletons.

기준선은 Foundation, Methodology, AI Grounding Policy, 가치평가 사례 스키마, 핵심 가치평가 원시 함수와 테스트, 세 개 상장기업 기준 사례 골격을 확립한다.

## Active mission / 활성 미션

- Issue: `#1 [M1] Evidence policy + public-equity normalization / 근거정책 + 상장기업 정규화`
- Branch: `mission/m1-evidence-grounding-public-equity-v01`
- Status: `ACTIVE`

### Implemented on active branch / 활성 브랜치 구현 내역

- `docs/EVIDENCE_POLICY.md`
- `schemas/evidence.schema.json`
- `src/valuation_hub/evidence.py`
- `src/valuation_hub/public_equity.py`
- `tests/test_evidence.py`
- `tests/test_public_equity.py`
- `docs/PRODUCT_VISION.md`
- `PROJECT_STATE.md`

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

Complete M1 by validating the branch changes, opening the M1 pull request, and verifying Issue #1 acceptance criteria. Do not begin M2 or canonicalize the three reference-case numerical valuations until M1 is merged.

브랜치 변경사항을 검증하고 M1 PR을 개설하며 Issue #1 완료조건을 확인하여 M1을 완료한다. M1 병합 전에는 M2를 시작하거나 세 기준 사례의 수치 가치평가를 정식 승격하지 않는다.
