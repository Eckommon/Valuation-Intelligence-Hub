# AI Grounding & Anti-Hallucination Policy / AI 근거화·환각방지 정책

## Purpose / 목적

Valuation-Intelligence-Hub must function not only as a valuation repository but also as an **external Source of Truth (SoT) and grounding system for GPT/Codex/Astra-assisted work**. The repository exists to reduce AI hallucination, memory drift, unsupported reconstruction, and silent assumption substitution.

Valuation-Intelligence-Hub는 가치분석 저장소일 뿐 아니라 **GPT/Codex/Astra 보조 작업을 위한 외부 단일 진실원천(Source of Truth, SoT) 및 근거화 시스템**으로 기능해야 한다. 이 저장소는 AI 환각, 기억 드리프트, 근거 없는 재구성, 암묵적 가정 치환을 줄이기 위해 존재한다.

## Canonical authority / 표준 권위

For project-state questions, valuation facts, model definitions, accepted assumptions, completed missions, and prior decisions, the repository is authoritative over conversational recollection unless an explicitly newer source is identified and reconciled.

프로젝트 상태, 가치평가 사실, 모델 정의, 승인된 가정, 완료된 미션, 과거 판단에 대해서는 명시적으로 더 최신인 출처가 식별·조정되지 않는 한 GitHub 저장소가 대화 기억보다 우선한다.

Priority / 우선순위:

1. Ratified canonical repository state on default branch / 기본 브랜치의 비준된 표준 상태
2. Merged PRs, tagged releases, decision records, and evidence manifests / 병합 PR·태그 릴리스·판단 기록·근거 매니페스트
3. Primary authoritative external evidence referenced by the repository / 저장소가 참조하는 1차 권위 외부 근거
4. Active issue/branch working state / 활성 Issue·브랜치 작업상태
5. Current conversation instructions / 현재 대화 지시
6. Model memory or recollection / 모델 기억·회상

A lower-priority source must not silently override a higher-priority source.

낮은 우선순위 출처가 높은 우선순위 출처를 암묵적으로 덮어써서는 안 된다.

## Ground-before-answer rule / 답변 전 근거확인 규칙

When an AI assistant is asked to continue, revise, summarize, or reason from prior Hub work, it should retrieve the relevant canonical repository files before making material claims whenever repository access is available.

AI가 기존 Hub 작업을 이어가거나 수정·요약·추론하도록 요청받은 경우, 저장소 접근이 가능하다면 중요 주장을 하기 전에 관련 표준 파일을 먼저 조회해야 한다.

The assistant must not rely on remembered numerical values, previous conversational calculations, branch names, mission status, or accepted assumptions when those can be verified from the repository.

저장소에서 검증 가능한 수치, 이전 대화 계산, 브랜치명, 미션 상태, 승인 가정을 기억에 의존해서 사용해서는 안 된다.

## Claim classes / 주장 분류

Every material analytical statement should be representable as one of:

모든 중요 분석 주장은 다음 중 하나로 표현 가능해야 한다.

- `FACT` — directly observed and sourced / 직접 관측·출처화된 사실
- `NORMALIZED_FACT` — sourced fact transformed by a documented normalization rule / 문서화된 정규화 규칙으로 변환된 사실
- `ASSUMPTION` — explicit model assumption / 명시적 모델 가정
- `DERIVED` — deterministic calculation from versioned inputs / 버전 입력에서 결정론적으로 계산된 값
- `INTERPRETATION` — analytical judgement based on facts and outputs / 사실·산출물 기반 분석적 해석
- `UNKNOWN` — unresolved or insufficiently supported / 미해결 또는 근거 불충분

AI-generated language must not upgrade `ASSUMPTION`, `INTERPRETATION`, or `UNKNOWN` into `FACT`.

AI 생성 문장이 `ASSUMPTION`, `INTERPRETATION`, `UNKNOWN`을 `FACT`로 승격해서는 안 된다.

## Fail-closed behavior / Fail-closed 동작

If a material fact is absent, conflicting, stale, or provenance-incomplete, the correct state is `UNKNOWN`, `HOLD`, or an explicit qualification—not a plausible estimate presented as fact.

중요 사실이 누락·충돌·노후화되었거나 출처가 불완전하면 올바른 상태는 `UNKNOWN`, `HOLD`, 또는 명시적 단서이며, 그럴듯한 추정치를 사실처럼 제시하는 것이 아니다.

Examples / 예시:

- Missing diluted share count → do not finalize per-share value. / 희석주식수 부재 → 주당가치 확정 금지
- Conflicting CAPEX definitions → retain conflict until normalization is resolved. / CAPEX 정의 충돌 → 정규화 해결 전 충돌상태 유지
- Stale WACC market inputs → mark valuation as stale or refresh inputs. / WACC 시장입력 노후 → 가치평가 노후 표시 또는 입력 갱신
- Discontinued operations not normalized → do not compare historical margins as continuing operations. / 중단사업 미정규화 → 계속사업 마진으로 비교 금지

## Provenance minimum / 최소 출처요건

A material fact is analysis-grade only when the repository can identify, where applicable:

중요 사실은 가능한 경우 다음을 식별할 수 있어야 분석급으로 인정한다.

- metric / 지표
- value / 값
- unit and currency / 단위·통화
- period or as-of date / 기간·기준일
- source publisher / 출처 발행자
- source locator or URL / 출처 위치·URL
- retrieval or publication date / 조회·발행일
- transformation/normalization rule if any / 변환·정규화 규칙
- confidence or evidence quality / 신뢰도·근거품질

## Durable decision records / 영구 판단기록

Material methodology choices, assumption-policy changes, model-selection decisions, accepted exceptions, and terminal mission outcomes should be recorded durably in version control rather than existing only in chat.

중요 방법론 선택, 가정정책 변경, 모델선택 판단, 승인 예외, 미션 종결결과는 채팅에만 존재하지 않고 버전관리 안에 영구 기록되어야 한다.

Recommended records / 권장 기록:

- `docs/decisions/` for architecture and methodology decisions / 아키텍처·방법론 판단
- `analyses/.../evidence.*` for evidence manifests / 근거 매니페스트
- `analyses/.../assumptions.*` for explicit assumptions / 명시적 가정
- `analyses/.../result.*` for reproducible outputs / 재현 가능한 결과
- Issues and PRs for mission state and acceptance history / 미션 상태·승인 이력

## Reproducibility gate / 재현성 게이트

No AI-generated valuation result becomes canonical merely because it appears plausible or was stated confidently. Promotion to canonical status requires:

그럴듯하거나 자신 있게 제시되었다는 이유만으로 AI 생성 가치평가 결과가 표준 상태가 되지 않는다. 표준 승격에는 다음이 필요하다.

1. versioned inputs / 버전 입력
2. provenance-compliant material facts / 출처정책을 충족한 중요 사실
3. explicit assumptions / 명시적 가정
4. named model and model version / 모델명·모델버전
5. reproducible calculation / 재현 가능한 계산
6. validation/invariant checks / 검증·불변조건 체크
7. recorded acceptance through the repository workflow / 저장소 워크플로를 통한 승인 기록

## Session handoff contract / 세션 인계 계약

A new AI session should recover state from the repository rather than reconstructing state from chat memory. The minimum resume sequence is:

새 AI 세션은 채팅 기억에서 상태를 재구성하지 말고 저장소에서 상태를 복구해야 한다. 최소 재개 순서는 다음과 같다.

1. Read repository foundation and this policy. / 기반문서와 본 정책 확인
2. Read current README and relevant methodology. / 현재 README·관련 방법론 확인
3. Inspect open/merged Issue and PR state for the active mission. / 활성 미션의 Issue·PR 상태 확인
4. Read the target analysis manifest and latest canonical result. / 대상 분석 매니페스트·최신 표준 결과 확인
5. Identify the exact resume point before proposing new work. / 새 작업 제안 전 정확한 재개점 식별

## Contradiction handling / 충돌 처리

When conversational memory conflicts with repository state, the assistant must state the conflict and prefer the repository unless evidence establishes that the repository is outdated.

대화 기억과 저장소 상태가 충돌하면 AI는 충돌을 명시하고, 저장소가 오래되었다는 근거가 확인되지 않는 한 저장소를 우선한다.

Repository state must not be silently rewritten to match model memory.

모델 기억에 맞추기 위해 저장소 상태를 암묵적으로 다시 써서는 안 된다.

## Anti-hallucination objective / 환각방지 목표

The goal is not to claim that hallucination can be eliminated. The goal is to make unsupported claims **detectable, attributable, rejectable, and recoverable** through durable evidence and machine-checkable contracts.

목표는 환각을 완전히 제거할 수 있다고 주장하는 것이 아니다. 목표는 영구 근거와 기계검증 가능한 계약을 통해 근거 없는 주장을 **탐지 가능하고, 출처 추적 가능하며, 거부 가능하고, 복구 가능하게** 만드는 것이다.
