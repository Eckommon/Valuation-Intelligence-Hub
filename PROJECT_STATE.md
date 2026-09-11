# Project State / 프로젝트 상태

> Canonical human-and-AI handoff. Repository-grounded state outranks chat or AI recollection.
>
> 인간·AI 공통 정식 인계 문서. 저장소 근거 상태는 채팅·AI 기억보다 우선한다.

## Repository identity / 저장소 식별

- Repository / 저장소: `Eckommon/Valuation-Intelligence-Hub`
- Purpose / 목적: Cross-asset, evidence-grounded valuation intelligence system / 범자산 근거 기반 가치분석 인텔리전스 시스템
- Product strategy / 제품 전략: Web-first hybrid; one shared valuation/evidence kernel / 웹 우선 하이브리드; 단일 공통 가치·근거 커널
- Documentation / 문서: English + Korean bilingual / 영한문 병기

## Canonical baseline / 정식 기준선

- Bootstrap v0.1: `1d9881bcffb2499fdb72204070d058ef86676841`
- M1 Evidence grounding + normalization: `e3a11259c0e248f055ee16466e08ccfef2a4d13e` — #1 `COMPLETED`
- M2 Scenario + reverse valuation: `2b6d7522e7d847673a7310b9e7f4346cd26cb59e` — #2 `COMPLETED`
- M3 Evidence-grounded reference cases: `5c39c6a1857a5b4aeffa9782399e24bcbd77c0ae` — #3 `COMPLETED`
- M4 Executable registry + CLI: `db14a21bb706f4f3cd74f5a33d88ca5937249aa5` — #8 `COMPLETED`
- M5 Web MVP: `5867363d26d4efa57e5fb92d4861de9bfbf00d7f` — #12 `COMPLETED`
- M6 Interactive preview + evidence browser: `caf7576c1a2c13916449d445f5badc3a29712d36` — #14 `COMPLETED`
- M7 Product UX + visualization: `243cea0233031088fac8edb0362971326840b858` — #16 `COMPLETED`
- M8 User Draft workflow: `899271709ef3c49d431e0fce716eff48d0b22370` — #18 `COMPLETED`
- M9 Reviewed Draft→Candidate promotion protocol: `3e2d0a58b13c6e90ae6e665db72dc2683d5fad3f` — #20 `COMPLETED`

M9 post-merge `main` CI run `34565725629` completed `success` on Python 3.11/3.12.

M9 병합 후 `main` CI run `34565725629`은 Python 3.11/3.12에서 `success` 완료했다.

## Canonical product capability / 정식 제품 기능

- Three regression-locked reference cases / 3개 회귀 잠금 기준 사례
- Shared FCFF and venture-probability kernels / 공통 FCFF·벤처 확률가중 커널
- Versioned registry + `case_service` runtime/canonical drift checks / 버전 레지스트리 + 실행값 drift 검증
- CLI and local Web product / CLI·로컬 Web 제품
- Evidence browser and scenario preview / 근거 탐색·시나리오 preview
- Product valuation visualization / 가치 시각화
- User Draft Lab: `DRAFT_USER_SUPPLIED / NOT_CANONICAL / USER_SUPPLIED_UNVERIFIED`
- M9 Promotion Review: `CANDIDATE_REVIEW → HUMAN REVIEW + SHA-256 LOCK → REVIEW_APPROVED_READY_FOR_PR`

M9 never assigns `CANONICAL`. It proves only that a reviewed candidate is ready for the next governed repository transition.

M9은 `CANONICAL`을 부여하지 않고 검토 Candidate가 다음 저장소 거버넌스 전이에 준비되었는지만 증명한다.

## Active mission / 활성 미션

- Issue: `#22 [M10] Deterministic reviewed promotion package staging / 검토 완료 승격 패키지 결정론적 스테이징`
- Branch: `mission/m10-promotion-package-staging-v01`
- Status: `ACTIVE_IMPLEMENTATION`

## M10 design decision / M10 설계 결정

The M8 generic equity Draft and the legacy M3 reference-equity input format are **not losslessly equivalent**:

M8 일반 equity Draft와 기존 M3 reference-equity 입력포맷은 **손실 없이 동등하지 않다**.

- M8 Draft: absolute forecast D&A, CAPEX, ΔNWC / 전망 절대값
- legacy reference equity: revenue-linked D&A/CAPEX ratios + opening core NWC + NWC-to-sales / 매출연동 비율·opening NWC 방식

Therefore M10 MUST NOT fabricate missing structure or coerce reviewed Drafts into legacy `case_inputs.json`. It preserves reviewed economics exactly and declares the canonical adapter still required.

따라서 M10은 누락 구조를 발명하거나 검토 Draft를 기존 `case_inputs.json`으로 억지 변환하지 않는다. 검토 경제값을 그대로 보존하고 향후 필요한 canonical adapter를 명시한다.

## M10 state / M10 상태

```text
REVIEW_APPROVED_READY_FOR_PR
        ↓
PROMOTION_PACKAGE_STAGED / NOT_CANONICAL
        ↓ reviewed package + explicit canonical adapter
SEPARATE GOVERNED PR
        ↓ full CI + human review + merge
CANONICAL
```

M10 itself stops at `PROMOTION_PACKAGE_STAGED`.

M10 자체는 `PROMOTION_PACKAGE_STAGED`에서 멈춘다.

## Current M10 implementation / 현재 M10 구현

### Package schema / 패키지 스키마

- `schemas/promotion_package.schema.json`
- version: `promotion-package-v0.1`
- fixed state: `PROMOTION_PACKAGE_STAGED`
- fixed canonical flag: `false`

### Package service / 패키지 서비스

- `src/valuation_hub/promotion_package.py`
- `build_promotion_package()` — approved Candidate → deterministic package / 승인 Candidate → 결정론적 패키지
- `validate_promotion_package()` — hashes, review provenance, semantics, shared-kernel result checks / 해시·검토출처·의미·공통커널 결과 검증
- `materialize_promotion_package()` — explicit noncanonical filesystem output only / 명시적 비정식 파일 출력만 허용
- `validate_materialized_package()` — PACKAGE.json + materialized bytes verification / 패키지·파일 bytes 검증

### Deterministic artifacts / 결정론적 산출물

1. `reviewed_candidate.json` — exact M9 approved Candidate / M9 승인 Candidate 원문
2. `reviewed_case_payload.json` — identity + preserved Draft + adapter requirement / 식별·보존 Draft·adapter 요구
3. `evidence_bundle.json` — input governance + evidence / 입력 거버넌스·근거
4. `staged_valuation_result.json` — shared Draft-kernel recomputation / 공통 Draft 커널 재계산
5. `REGISTRY_PROPOSAL.json` — blocked proposal only / 차단된 제안 전용
6. `REPORT.md` — deterministic bilingual review summary / 결정론적 영한문 검토보고

Each artifact and the full package have SHA-256 digests.

모든 산출물과 전체 패키지는 SHA-256 digest를 가진다.

### Canonical compatibility guard / 정식 호환성 가드

Every package declares:

`NOT_EXECUTABLE_UNTIL_CANONICAL_ADAPTER`

Required adapters:

- equity Draft → `reviewed-draft-equity-fcff-v0.1`
- venture Draft → `reviewed-draft-venture-probability-v0.1`

`REGISTRY_PROPOSAL.json` remains `registration_blocked=true`; it is not directly insertable canonical state.

`REGISTRY_PROPOSAL.json`은 `registration_blocked=true`이며 정식상태에 직접 삽입할 수 없다.

### Collision and path safety / 충돌·경로 안전

- safe case ID regex: `^[A-Z0-9][A-Z0-9_]{2,79}$`
- existing canonical case IDs rejected / 기존 정식 case ID 거부
- M10 is new-case staging only / M10은 신규사례 스테이징 전용
- repository-internal materialization allowed only below `workspace/promotion_packages/` / 저장소 내부 출력경로 제한
- `/workspace/promotion_packages/**` Git-ignored except `.gitkeep`
- no write to `analyses/` or `registry/` / 정식 경로 write 금지

### CLI / CLI

- `vih package-build <approved-candidate> --case-id ... --name-en ... --name-ko ... --asset-class ...`
- optional `--output-dir` for explicit materialization / 명시적 materialization 선택
- `vih package-validate <package-json-or-directory>`

Without `--output-dir`, package build emits JSON and performs no filesystem write.

`--output-dir`가 없으면 JSON만 출력하고 파일시스템을 기록하지 않는다.

### Web / Web

- `src/valuation_hub/web_package.py`
- `/package` — Promotion Package Lab / 승격 패키지 랩
- `POST /api/package/build`
- `POST /api/package/validate`
- Web path is memory-only; server-side materialization intentionally excluded / Web은 메모리 전용·서버파일 기록 제외
- inherits `/promotion`, `/draft`, canonical cases, evidence, previews / 이전 제품경로 상속

### Tests / 테스트

- `tests/test_promotion_package.py`
- `tests/test_cli_package.py`
- `tests/test_web_package.py`

Required invariants / 필수 불변조건:

- same approved Candidate + identity → identical package and SHA-256 / 동일 입력→동일 패키지·해시
- non-approved or post-review-mutated Candidate fails closed / 미승인·검토후변경 차단
- unsafe/traversal and canonical ID collisions fail closed / 위험경로·정식 ID 충돌 차단
- reviewed Draft preserved exactly / 검토 Draft 정확 보존
- staged valuation reproduces shared Draft kernel / staged 가치 공통커널 재현
- artifact/package mutation detected / 산출물·패키지 변조 탐지
- registry proposal remains blocked / 레지스트리 제안 차단 유지
- canonical registry/evidence/results byte-identical / 정식 상태 byte 불변

### Documentation / 문서

- `docs/PROMOTION_PACKAGE.md`

## Grounding authority / 근거화 권위

1. `main` canonical files and merged decisions / `main` 정식 파일·병합 결정
2. this `PROJECT_STATE.md` + active Issue/PR/branch / 본 상태파일 + 활성 Issue/PR/branch
3. primary evidence manifests / 1차 근거 매니페스트
4. current chat / 현재 대화
5. AI recollection / AI 기억

Repository state wins over AI recollection unless newer primary evidence requires explicit reconciliation.

더 최신 1차자료의 명시적 조정이 필요한 경우를 제외하고 저장소 상태가 AI 기억보다 우선한다.

## Exact resume point / 정확한 재개점

Finish M10 by synchronizing README, opening the M10 PR, and running the full Python 3.11/3.12 CI suite. Fix failures using preserved diagnostics. Merge only if deterministic package/hash tests, path/collision guards, CLI/Web integration, materialized-byte verification, shared-kernel reproduction, and all M1–M10 regressions pass while canonical files remain unchanged. After M10 merge, close #22 and define M11 around the explicit versioned `reviewed-draft-*` canonical adapter and package-admission contract; M11 must prove that reviewed economics are preserved before any registry admission.

README를 동기화하고 M10 PR을 개설한 뒤 Python 3.11/3.12 전체 CI를 실행한다. 보존 진단을 근거로 실패를 수정한다. 결정론적 패키지·해시, 경로·충돌 가드, CLI·Web 통합, materialized bytes 검증, 공통커널 재현 및 M1–M10 회귀가 모두 통과하고 정식 파일이 불변일 때만 병합한다. M10 병합 후 #22를 종료하고 명시적 버전 `reviewed-draft-*` canonical adapter 및 package-admission 계약을 M11로 정의한다. 레지스트리 수용 전 검토 경제값 보존을 증명해야 한다.
