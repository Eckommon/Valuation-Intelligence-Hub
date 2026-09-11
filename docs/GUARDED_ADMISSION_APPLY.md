# Guarded Canonical Admission Apply / 정식 수용 안전 적용

## Purpose / 목적

M12 closes the operational gap between an M11 `CANONICAL_ADMISSION_PROPOSED` bundle and a repository working tree that is ready for a separately reviewed pull request.

M12는 M11 `CANONICAL_ADMISSION_PROPOSED` bundle과 별도 인간 검토 PR을 만들 수 있는 repository working tree 사이의 운영 간극을 닫습니다.

M12 does **not** create approval, open/merge a PR, or write directly to the default branch.

M12는 승인 생성, PR 자동 생성·병합, 기본 브랜치 직접 기록을 수행하지 않습니다.

## State transition / 상태 전이

```text
CANONICAL_ADMISSION_PROPOSED
        ↓ deterministic baseline-bound plan
REPOSITORY_CHANGE_PLANNED / canonical=false
        ↓ guarded local apply on admission/* branch/worktree
GUARDED_BRANCH_APPLIED / canonical=false
        ↓ human diff review + repository PR + full CI + merge
CANONICAL
```

`GUARDED_BRANCH_APPLIED` means the proposed canonical bytes exist only in an unmerged branch working tree. Repository canonical authority still belongs to merged `main`.

`GUARDED_BRANCH_APPLIED`는 제안 정식 bytes가 아직 병합되지 않은 branch working tree에 존재한다는 뜻입니다. 저장소의 정식 권위는 여전히 병합된 `main`에 있습니다.

## Deterministic repository plan / 결정론적 저장소 계획

`vih admission-plan` validates the M11 admission bundle and computes a plan containing:

- exact case ID and canonical target directory / 정확한 case ID·정식 대상경로
- M11 admission bundle SHA-256 / M11 수용 bundle SHA-256
- current `registry/cases.json` byte SHA-256 / 현재 registry 원본 bytes SHA-256
- exact post-change registry object and byte SHA-256 / 변경 후 registry 객체·bytes SHA-256
- every proposed canonical artifact path and SHA-256 / 모든 정식 제안 파일 경로·SHA-256
- branch safety policy / 브랜치 안전정책
- full plan SHA-256 / 전체 plan SHA-256

For the same admission bundle and identical registry baseline, the plan is byte-semantically deterministic.

동일한 수용 bundle과 동일 registry 기준선에서는 동일한 의미·해시의 계획이 생성됩니다.

## Optimistic concurrency / 낙관적 동시성

The plan records the exact registry bytes present when it was created. `admission-plan-validate` and `admission-apply` recompute that digest.

계획은 생성 시점의 registry 원본 bytes를 기록합니다. `admission-plan-validate`와 `admission-apply`는 해당 digest를 다시 계산합니다.

If any other work changes `registry/cases.json` after planning, application fails closed and the user must rebuild the plan against the new baseline.

계획 이후 다른 작업이 `registry/cases.json`을 변경하면 적용을 차단하고 새로운 기준선으로 계획을 다시 생성해야 합니다.

## Branch/worktree policy / 브랜치·워크트리 정책

Filesystem application is allowed only when the explicit target repository reports a symbolic Git HEAD under:

```text
admission/*
```

Blocked:

- `main`
- `master`
- any other branch prefix
- detached HEAD
- missing/invalid `.git` checkout marker

Regular checkouts and Git worktrees whose `.git` is a `gitdir:` file are supported.

일반 checkout과 `.git`이 `gitdir:` 파일인 Git worktree를 지원합니다.

## No overwrite / 덮어쓰기 금지

M12 v0.1 is new-case admission only.

Before a plan is generated or applied:

- case ID must not exist in the registry / registry에 동일 ID가 없어야 함
- target canonical case directory must not exist / 대상 정식 디렉터리가 없어야 함
- all repository paths must remain under the explicit target root / 모든 경로가 대상 root 내부여야 함
- path components that are symlinks are rejected / symlink 경로요소 차단

Existing canonical cases cannot be updated or replaced through this applicator.

## Ordered transactional apply / 순서형 트랜잭션 적용

The filesystem does not provide one atomic transaction across an entire directory tree plus an independent registry file. M12 therefore uses a fail-safe ordering rather than claiming impossible full crash atomicity.

파일시스템은 여러 case 파일과 독립 registry 파일을 하나의 원자적 트랜잭션으로 제공하지 않습니다. M12는 완전한 crash atomicity를 주장하지 않고 fail-safe 순서를 사용합니다.

```text
1. Revalidate plan + admission + registry baseline
2. Verify admission/* branch/worktree
3. Stage all exact case artifact bytes in a temporary sibling directory
4. Verify every staged SHA-256
5. Stage exact post-change registry bytes
6. Atomically rename staged case directory into its final path
7. Atomically replace registry file LAST
8. Verify applied bytes
9. Run validate_case → run_case → evidence_view → preview_case
10. On caught failure: restore original registry + remove newly created case directory
```

The registry is published last, so normal failures never leave a registry entry pointing to incomplete case files.

registry를 마지막에 공개하므로 일반적인 실패에서는 registry가 불완전한 case 파일을 가리키지 않습니다.

A process/OS crash in the narrow interval after the case-directory rename but before registry replacement could leave an **unregistered orphan directory**. Such a directory has no canonical authority because the registry was not changed, and subsequent M12 planning fails rather than overwriting it. This is intentionally fail-safe.

case 디렉터리 rename 이후 registry 교체 전의 매우 좁은 구간에서 프로세스·OS가 강제 종료되면 **미등록 orphan 디렉터리**가 남을 수 있습니다. registry가 변경되지 않았으므로 정식 권위가 없고 이후 M12도 이를 덮어쓰지 않고 차단합니다.

## Post-apply validation / 적용 후 검증

Before M12 reports success, the newly staged branch case must pass:

```text
validate_case
→ run_case
→ evidence_view
→ preview_case
```

The runtime must exactly reproduce the M11 admission runtime within the adapter contract, evidence must remain read-only, and preview must remain `PREVIEW_NOT_CANONICAL`.

## CLI / CLI

Prepare a dedicated branch or worktree first:

```bash
git switch -c admission/KR_EXAMPLE_COMPANY
```

Build plan:

```bash
vih admission-plan admission.json \
  --target-repo . > change-plan.json
```

Validate current baseline:

```bash
vih admission-plan-validate change-plan.json admission.json \
  --target-repo .
```

Apply exact bytes:

```bash
vih admission-apply change-plan.json admission.json \
  --target-repo .
```

Then inspect the Git diff, run full tests, and open a normal reviewed PR. M12 does not perform those GitHub actions automatically.

그 다음 Git diff를 검토하고 전체 테스트를 실행한 뒤 일반 인간 검토 PR을 생성합니다. M12 자체는 GitHub PR 작업을 자동 수행하지 않습니다.

## Web / Web

The Web PR Preparation Lab is intentionally read-only:

```text
/pr-prep
POST /api/pr-prep/plan
POST /api/pr-prep/validate
```

There is deliberately **no** `/api/pr-prep/apply` endpoint.

의도적으로 `/api/pr-prep/apply` endpoint는 존재하지 않습니다.

## Authority boundary / 권위 경계

A successful M12 apply changes only an unmerged branch working tree. It does not change the canonical repository state. Canonical authority changes only when the exact branch diff passes repository CI and human review and is merged through the governed PR process.

M12 apply 성공은 병합 전 branch working tree만 변경합니다. 정식 저장소 권위는 정확한 diff가 저장소 CI와 인간 검토를 통과해 거버넌스 PR로 병합될 때만 변경됩니다.
