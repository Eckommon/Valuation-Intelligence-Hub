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
- M8 User Draft cases + safe import: `899271709ef3c49d431e0fce716eff48d0b22370` — #18 `COMPLETED`

M8 post-merge `main` CI run `34553180936` completed successfully on Python 3.11/3.12.

M8 병합 후 `main` CI run `34553180936`은 Python 3.11/3.12에서 성공 완료했다.

## Canonical product capability / 정식 제품 기능

### Grounded canonical cases / 근거화 정식 사례

- versioned registry + shared `case_service` / 버전 레지스트리 + 공통 case service
- three regression-locked reference cases / 세 개 회귀 잠금 기준 사례
- FCFF and venture-probability kernels / FCFF·벤처 확률가중 커널
- runtime-to-canonical drift validation / 런타임-정식 결과 drift 검증

### Product interfaces / 제품 인터페이스

- CLI: canonical run/report, Draft workflow, Web launch / 정식 실행·보고, Draft 흐름, Web 실행
- local-first product Web UI / 로컬 우선 제품 Web UI
- valuation visualization / 가치 시각화
- evidence browser + classification filters / 근거 탐색·분류 필터
- in-memory `PREVIEW_NOT_CANONICAL` scenario sandbox / 비정식 시나리오 샌드박스
- user Draft Lab / 사용자 Draft 랩

### M8 Draft boundary / M8 Draft 경계

All user-authored/imported cases remain:

모든 사용자 작성·가져오기 사례는 다음 상태를 유지한다.

`DRAFT_USER_SUPPLIED / NOT_CANONICAL / USER_SUPPLIED_UNVERIFIED`

Draft execution uses shared kernels but never auto-registers or writes canonical analysis state.

Draft 실행은 공통 커널을 사용하지만 정식 레지스트리 등록·분석상태 기록을 자동 수행하지 않는다.

## Active mission / 활성 미션

- Issue: `#20 [M9] Reviewed Draft→Candidate→Canonical promotion protocol / 검토 기반 Draft→Candidate→Canonical 승격 프로토콜`
- Branch: `mission/m9-reviewed-promotion-protocol-v01`
- Status: `ACTIVE_IMPLEMENTATION`

## M9 state machine / M9 상태기계

```text
DRAFT_USER_SUPPLIED
        ↓
CANDIDATE_REVIEW
        ↓ evidence + input governance complete
HUMAN REVIEW + SHA-256 SCOPE LOCK
        ↓
REVIEW_APPROVED_READY_FOR_PR
        ↓ separate repository PR + CI + review + merge
CANONICAL
```

`CANONICAL` remains outside the M9 service boundary. M9 can only prove readiness for a separately reviewed repository PR.

`CANONICAL`은 M9 서비스 경계 밖에 있다. M9은 별도 인간 검토 저장소 PR 준비 상태까지만 증명할 수 있다.

## Current M9 implementation / 현재 M9 구현

### Candidate schema / Candidate 스키마

- `schemas/promotion_candidate.schema.json`
- schema version: `promotion-candidate-v0.1`
- fixed state: `CANDIDATE_REVIEW`
- fixed canonical flag: `false`

### Promotion service / 승격 서비스

- `src/valuation_hub/promotion.py`
- `build_candidate()` — deterministic Draft→candidate skeleton / 결정론적 Candidate 생성
- `assess_candidate()` — fail-closed governance/evidence assessment / fail-closed 거버넌스·근거 평가
- `validate_candidate()` — requires zero blockers / 차단요인 0 요구
- `review_scope_sha256()` — immutable review-scope digest / 불변 검토범위 해시
- `promotion_check()` — explicit human approval + matching hash → PR readiness only / 명시적 인간 승인·해시 일치 → PR 준비만 선언

### Material-input governance / 중요입력 거버넌스

Every material numeric model input is deterministically enumerated. Structural forecast `year` labels are excluded.

모든 중요 숫자 모델입력을 결정론적으로 전수열거하며 구조적 전망 `year` 표시는 제외한다.

Allowed binding classes / 허용 분류:

- `FACT`
- `NORMALIZED_FACT`
- `ASSUMPTION`

`UNKNOWN` skeleton bindings cannot pass the review gate.

`UNKNOWN` 상태의 skeleton binding은 검토게이트를 통과할 수 없다.

### Evidence controls / 근거 통제

- FACT/NORMALIZED_FACT require linked evidence / 사실·정규화사실은 연결 근거 필수
- linked evidence class must match binding class / 연결 근거 class 일치 필수
- linked evidence numeric value must reconcile with model input / 근거 숫자와 모델입력 일치 필수
- source publisher/locator/tier required / 출처 발행자·위치·등급 필수
- existing `evaluate_canonical_promotion` gate reused / 기존 정식 승격게이트 재사용
- stale/conflict/UNKNOWN/Tier-D fact failures remain fail-closed / 노후·충돌·UNKNOWN·Tier-D 사실 차단

Observed values cannot be reclassified as assumptions to evade evidence. For `equity_fcff`, market price, diluted shares, debt, cash, and minority interest must be FACT/NORMALIZED_FACT. For `venture_probability`, market price must be FACT/NORMALIZED_FACT.

근거 요구를 회피하기 위해 관측값을 가정으로 낮출 수 없다. `equity_fcff`의 시장가격·희석주식수·부채·현금·비지배지분, `venture_probability`의 시장가격은 FACT/NORMALIZED_FACT여야 한다.

### Human review lock / 인간 검토 잠금

A successful candidate assessment returns the SHA-256 of the exact reviewed scope: Draft + input governance + evidence + candidate identity fields.

Candidate 검토 통과 시 Draft·입력거버넌스·근거·Candidate 식별필드 전체의 SHA-256 검토범위 해시를 반환한다.

`promotion_check()` additionally requires:

- `review.decision = APPROVE`
- non-empty human reviewer / 비어 있지 않은 검토자
- valid review timestamp / 유효한 검토시각
- non-empty rationale / 비어 있지 않은 검토근거
- exact `review.scope_sha256` match / 검토범위 해시 정확 일치

Any post-review mutation invalidates approval.

검토 후 변경은 승인을 무효화한다.

### CLI / CLI

- `vih candidate-build <draft-file>`
- `vih candidate-validate <candidate-file>`
- `vih promotion-check <candidate-file>`
- `--json` supported for machine-readable validation/check output / 검증·확인 기계판독 출력 지원

### Web Promotion Review Lab / Web 승격 검토 랩

- `src/valuation_hub/web_promotion.py`
- `/promotion` — Promotion Review Lab / 승격 검토 랩
- `POST /api/promotion/build`
- `POST /api/promotion/assess`
- `POST /api/promotion/check`
- inherits M8 `/draft` and all earlier canonical/product routes / M8 Draft와 이전 정식·제품 경로 상속
- no candidate persistence or canonical write-back / Candidate 영속화·정식 write-back 없음

### Tests / 테스트

- `tests/test_promotion.py`
- `tests/test_cli_promotion.py`
- `tests/test_web_promotion.py`

Required invariants include:

필수 불변조건:

- deterministic material-input enumeration / 중요입력 결정론적 전수열거
- missing/duplicate binding fail-closed / binding 누락·중복 차단
- evidence-value/model-value reconciliation / 근거값·모델값 조정
- observed-fact reclassification evasion blocked / 관측사실 가정 우회 차단
- stale/Tier-D evidence blocked through existing gate / 기존 게이트 기반 노후·Tier-D 차단
- post-review mutation invalidates SHA-256 approval / 검토 후 변경 시 승인 무효화
- promotion result remains `canonical=false` / 승격 준비 결과도 정식 아님
- canonical registry/evidence/results remain byte-identical / 정식 상태 byte 불변

### Documentation / 문서

- `docs/PROMOTION_PROTOCOL.md`

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

The product remains Web-first hybrid. Mathematical execution, user experimentation, evidence admissibility, human review, and canonical repository state are deliberately separate control states.

제품은 웹 우선 하이브리드를 유지한다. 수학적 실행, 사용자 실험, 근거 적격성, 인간 검토, 정식 저장소 상태는 의도적으로 서로 다른 통제 상태다.

## Exact resume point / 정확한 재개점

Open the M9 pull request and run the full Python 3.11/3.12 CI matrix. Fix promotion-service, CLI, Web, schema, or inherited regression failures using preserved diagnostics. Merge only if all M1–M9 tests pass, candidate review scope is hash-locked, observed facts cannot evade evidence, and promotion readiness never mutates or directly creates canonical state. After M9 merge, close #20 and define the next mission around deterministic promotion-package materialization for reviewed PRs, still without bypassing human review.

M9 PR을 개설하고 Python 3.11/3.12 전체 CI를 실행한다. 보존된 진단을 근거로 승격서비스·CLI·Web·스키마·기존 회귀 실패를 수정한다. M1–M9 전체 테스트가 통과하고 Candidate 검토범위가 해시 잠금되며 관측사실이 근거 요구를 우회할 수 없고 승격 준비가 정식 상태를 변경·직접 생성하지 않는 경우에만 병합한다. M9 병합 후 #20을 종료하고 인간 검토를 우회하지 않는 검토 PR용 결정론적 promotion-package materialization을 다음 미션으로 정의한다.
