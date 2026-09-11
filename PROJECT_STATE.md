# Project State / 프로젝트 상태

> Canonical human-and-AI handoff. Repository-grounded state outranks chat or AI recollection.  
> 인간·AI 공통 정식 인계 문서. 저장소 근거 상태는 채팅·AI 기억보다 우선한다.

## Repository identity / 저장소 식별

- Repository: `Eckommon/Valuation-Intelligence-Hub`
- Purpose: cross-asset, evidence-grounded valuation intelligence system / 범자산 근거 기반 가치분석 인텔리전스 시스템
- Product strategy: Web-first hybrid, one shared valuation/evidence kernel / 웹 우선 하이브리드, 단일 공통 가치·근거 커널
- Documentation: English + Korean bilingual / 영한문 병기

## Canonical baseline / 정식 기준선

- Bootstrap: `1d9881bcffb2499fdb72204070d058ef86676841`
- M1 Evidence grounding + normalization: `e3a11259c0e248f055ee16466e08ccfef2a4d13e` — #1 `COMPLETED`
- M2 Scenario + reverse valuation: `2b6d7522e7d847673a7310b9e7f4346cd26cb59e` — #2 `COMPLETED`
- M3 Evidence-grounded reference cases: `5c39c6a1857a5b4aeffa9782399e24bcbd77c0ae` — #3 `COMPLETED`
- M4 Executable registry + CLI: `db14a21bb706f4f3cd74f5a33d88ca5937249aa5` — #8 `COMPLETED`
- M5 Web MVP: `5867363d26d4efa57e5fb92d4861de9bfbf00d7f` — #12 `COMPLETED`
- M6 Interactive preview + evidence browser: `caf7576c1a2c13916449d445f5badc3a29712d36` — #14 `COMPLETED`
- M7 Product UX + visualization: `243cea0233031088fac8edb0362971326840b858` — #16 `COMPLETED`
- M8 User Draft workflow: `899271709ef3c49d431e0fce716eff48d0b22370` — #18 `COMPLETED`
- M9 Reviewed promotion protocol: `3e2d0a58b13c6e90ae6e665db72dc2683d5fad3f` — #20 `COMPLETED`
- M10 Deterministic promotion package staging: `951e6be93a2d98db3e71c7e9f77bc06b90516dd2` — #22 `COMPLETED`
- M11 Reviewed-Draft canonical adapter + admission: `243f941b2f323ac5fdca31b86e13966950156114` — #24 `COMPLETED`

M11 post-merge `main` CI run `34567565614` completed `success` on Python 3.11/3.12.

M11 병합 후 `main` CI run `34567565614`은 Python 3.11/3.12에서 `success` 완료했다.

## Canonical product capability / 정식 제품 기능

The merged product now provides:

- three regression-locked reference cases / 3개 회귀 잠금 기준 사례
- shared FCFF + venture-probability kernels / 공통 FCFF + 벤처 확률가중 커널
- versioned registry, CLI, local Web UI, evidence browser, scenario preview / 버전 레지스트리·CLI·Web·근거탐색·preview
- M8 user Draft workflow / 사용자 Draft
- M9 evidence-governed Candidate + human SHA-256 review lock / 근거 거버넌스 Candidate + 인간검토 해시 잠금
- M10 deterministic tamper-evident promotion package / 결정론적 변조탐지 승격 패키지
- M11 versioned reviewed-Draft canonical adapters + deterministic admission bundle / 버전 검토 Draft 정식 adapter + 결정론적 수용 bundle

M11 can produce exact proposed canonical bytes but intentionally does not place them into a Git working tree.

M11은 정확한 정식 제안 bytes를 생성할 수 있지만 Git working tree에는 의도적으로 직접 기록하지 않는다.

## Active mission / 활성 미션

- Issue: `#26 [M12] Guarded canonical admission applicator + PR-ready change plan / 정식 수용 안전 적용기 + PR 준비 변경계획`
- Branch: `mission/m12-guarded-admission-applicator-v01`
- PR: `#27 M12 Guarded canonical admission applicator + PR-ready plan / 정식 수용 안전 적용기`
- Status: `ACTIVE_FINALIZATION`
- First PR CI: run `34568018613` — Python 3.11/3.12 `success`

## M12 objective / M12 목표

Close the remaining manual-copy gap between a valid M11 admission bundle and a PR-ready working tree without creating a path that can silently modify canonical `main`.

유효한 M11 admission bundle과 PR 준비 working tree 사이의 수작업 복사 간극을 닫되 정식 `main`을 암묵적으로 변경하는 경로는 만들지 않는다.

```text
CANONICAL_ADMISSION_PROPOSED
        ↓ deterministic registry-baseline-bound plan
REPOSITORY_CHANGE_PLANNED / canonical=false
        ↓ explicit guarded apply on admission/* branch/worktree
GUARDED_BRANCH_APPLIED / canonical=false
        ↓ human diff review + PR + full CI + merge
CANONICAL
```

## M12 repository change plan / 저장소 변경계획

- schema: `schemas/repository_change_plan.schema.json`
- service: `src/valuation_hub/admission_apply.py`
- plan state: `REPOSITORY_CHANGE_PLANNED`
- plan flag: `canonical=false`
- binds exact M11 admission bundle SHA-256 / 정확한 M11 bundle 해시 결합
- captures current `registry/cases.json` byte SHA-256 / 현재 registry bytes 기준선
- computes exact post-change registry object + SHA-256 / 변경 후 registry 객체·해시
- enumerates exact canonical artifact paths + SHA-256 / 정확한 정식 산출물 경로·해시
- full plan is SHA-256 locked / 전체 plan 해시 잠금

A plan is valid only while the target registry bytes remain exactly equal to the planned baseline. Registry drift requires a new plan.

계획은 대상 registry bytes가 계획 기준선과 정확히 같을 때만 유효하다. registry drift가 있으면 계획을 다시 생성해야 한다.

## Guarded apply boundary / 안전 적용 경계

M12 filesystem apply requires an explicit target checkout/worktree whose symbolic Git branch is:

```text
admission/*
```

Fail-closed:

- `main` / `master`
- any other branch prefix / 다른 브랜치
- detached HEAD
- missing/invalid Git checkout marker
- existing registry case ID
- existing target canonical directory
- path traversal or symlink escape
- admission/plan/hash drift
- registry baseline drift

M12 v0.1 is new-case admission only; it cannot replace or update an existing canonical case.

M12 v0.1은 신규 사례 수용 전용이며 기존 정식 사례를 교체·수정할 수 없다.

## Ordered transactional apply / 순서형 트랜잭션 적용

M12 does not claim impossible multi-file crash atomicity. It uses a fail-safe order:

```text
validate plan + admission + baseline
→ stage all case artifact bytes
→ verify artifact SHA-256
→ stage post-change registry bytes
→ rename complete case directory into final path
→ replace registry LAST
→ verify applied bytes
→ validate_case → run_case → evidence_view → preview_case
```

Caught failures restore the original registry and remove the newly created case directory. If an OS/process crash occurs in the narrow interval after the directory rename but before registry replacement, an unregistered orphan directory may remain; it has no canonical authority and future M12 planning refuses to overwrite it.

일반 예외는 registry 원본과 신규 case 디렉터리를 롤백한다. 디렉터리 rename 후 registry 교체 전 강제종료 시 미등록 orphan 디렉터리가 남을 수 있으나 registry 권위가 없으며 이후 M12가 이를 덮어쓰지 않고 차단한다.

## Interfaces / 인터페이스

CLI:

```bash
vih admission-plan <admission.json> --target-repo <checkout> > change-plan.json
vih admission-plan-validate <change-plan.json> <admission.json> --target-repo <checkout>
vih admission-apply <change-plan.json> <admission.json> --target-repo <checkout>
```

Web PR Preparation Lab:

```text
/pr-prep
POST /api/pr-prep/plan
POST /api/pr-prep/validate
```

There is deliberately no Web apply endpoint. / Web apply endpoint는 의도적으로 존재하지 않는다.

## M12 tests / M12 테스트

`tests/test_admission_apply.py` and `tests/test_prprep_interfaces.py` cover:

- deterministic plan/hash / 결정론적 plan·해시
- registry optimistic-concurrency drift rejection / registry drift 차단
- main/master/other branch + detached HEAD rejection / 위험 브랜치·detached HEAD 차단
- normal checkout + Git worktree branch detection / 일반 checkout·worktree 감지
- canonical target collision rejection / 정식 대상 충돌 차단
- path/symlink escape rejection / 경로·symlink 탈출 차단
- exact equity and venture branch application / equity·venture 정확 적용
- post-apply `validate_case → run_case → evidence_view → preview_case` / 적용 후 전체 검증
- forced post-apply failure rollback / 강제 실패 롤백
- tampered plan/admission rejection / 변조 계획·bundle 차단
- CLI command contract / CLI 계약
- Web plan-only/no-apply boundary / Web 계획전용 경계

## Documentation / 문서

- `docs/CANONICAL_ADMISSION.md`
- `docs/GUARDED_ADMISSION_APPLY.md`
- `schemas/repository_change_plan.schema.json`

## Grounding authority / 근거화 권위

1. merged `main` canonical files and decisions / 병합 `main` 정식 파일·결정
2. `PROJECT_STATE.md` + active Issue/PR/branch / 상태파일 + 활성 Issue·PR·브랜치
3. source packages, admission bundles, repository plans / 원천 package·수용 bundle·저장소 계획
4. current chat / 현재 대화
5. AI recollection / AI 기억

Repository state wins over AI recollection unless newer primary evidence requires explicit reconciliation.

## Exact resume point / 정확한 재개점

Finalize README/M12 documentation, run a fresh full Python 3.11/3.12 CI on the final PR head, inspect PR mergeability, and merge #27 only if all M1–M12 regressions pass. After merge, verify the `main` push CI and close #26 through the merged PR. The next mission should move from governance plumbing to product value: live evidence/data ingestion with source adapters, while preserving the M9–M12 evidence/promotion/admission boundaries.

README와 M12 문서를 최종화하고 최종 PR head에서 Python 3.11/3.12 전체 CI를 다시 실행한다. M1–M12 전체 회귀가 통과할 때만 #27을 병합하고 이후 `main` push CI와 #26 종료를 확인한다. 다음 미션은 거버넌스 배관보다 제품가치로 이동하여, M9–M12 근거·승격·수용 경계를 보존한 실시간 evidence/data ingestion source adapter를 추진하는 것이 적절하다.
