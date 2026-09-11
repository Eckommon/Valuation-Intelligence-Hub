# M12 Acceptance Contract / M12 완료조건

M12 may merge only when the final pull-request head satisfies every invariant below on Python 3.11 and 3.12.

M12는 최종 pull-request head가 Python 3.11·3.12에서 아래 불변조건을 모두 만족할 때만 병합한다.

1. **Deterministic plan / 결정론적 계획** — same valid M11 admission bundle + identical registry bytes produces the same repository change plan and plan SHA-256.
2. **Optimistic concurrency / 낙관적 동시성** — any registry byte change after planning invalidates the plan before filesystem application.
3. **Explicit safe branch / 명시적 안전 브랜치** — apply requires symbolic `admission/*`; `main`, `master`, other branches, detached HEAD, or invalid Git context fail closed.
4. **Worktree support / Worktree 지원** — standard `.git` directories and Git worktree `gitdir:` markers resolve the admission branch correctly.
5. **New-case only / 신규 사례 전용** — existing registry IDs or target canonical directories are never overwritten.
6. **Path safety / 경로 안전성** — traversal and symlink escape are rejected before writes.
7. **Exact bytes / 정확한 bytes** — every applied case artifact matches the M11 SHA-256 and the applied registry matches the planned post-change SHA-256.
8. **Publish registry last / registry 마지막 공개** — complete case artifacts are staged first; the registry is replaced only after artifact verification.
9. **Caught-failure rollback / 예외 롤백** — post-write validation failure restores original registry bytes and removes the newly created case directory.
10. **Full read-path validation / 전체 읽기경로 검증** — successful apply passes `validate_case → run_case → evidence_view → preview_case` and reproduces the M11 runtime.
11. **Web remains read-only / Web 읽기전용** — Web provides plan/validate only and no PR-prep apply endpoint.
12. **Legacy regression / 기존 회귀** — all M1–M11 behavior remains green.
13. **Authority boundary / 권위 경계** — `GUARDED_BRANCH_APPLIED` remains `canonical=false`; only a later reviewed repository merge can change canonical authority.

## Crash-consistency statement / 강제종료 일관성

M12 does not claim a filesystem capability that does not exist. A directory tree and an independent registry file cannot be committed as one portable OS-level atomic transaction.

M12는 존재하지 않는 파일시스템 기능을 주장하지 않는다. 디렉터리 트리와 독립 registry 파일을 하나의 이식 가능한 OS 원자 트랜잭션으로 커밋할 수는 없다.

The safe ordering guarantees that the registry is never intentionally published before complete case files. Caught failures roll back. A process/OS crash in the narrow interval after final case-directory rename and before registry replacement may leave an unregistered orphan directory; it has no canonical authority and the no-overwrite rule blocks silent reuse.

안전 순서는 완전한 case 파일보다 registry가 먼저 공개되지 않도록 보장한다. 포착된 예외는 롤백한다. 최종 case 디렉터리 rename 이후 registry 교체 전 강제종료 시 미등록 orphan 디렉터리가 남을 수 있지만 정식 권위가 없고 no-overwrite 규칙이 암묵적 재사용을 차단한다.
