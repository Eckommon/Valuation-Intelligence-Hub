# M29 Acceptance / M29 완료계약

## Mission / 미션

Bridge a complete, human-approved M28 v0.8 bound equity-FCFF Draft into the existing promotion → admission → guarded repository-change pipeline while preserving exact authority and source lineage.

완전한 인간승인 M28 v0.8 bound equity-FCFF Draft를 정확한 권위와 source lineage를 보존한 채 기존 승격 → 수용 → guarded 저장소 변경 흐름으로 연결한다.

## Acceptance checklist / 완료조건

- [x] Historical `promotion-candidate-v0.1` validation and review semantics remain delegated unchanged.
- [x] `promotion-candidate-v0.2` is additive and independently validates its embedded M28 source result.
- [x] M29 accepts only valid M28 `bound-draft-result-v0.1` with exact `draft-binding-proposal-v0.8` lineage.
- [x] All 13 material fields must be `DIRECT_BIND`.
- [x] Human binding approval must contain exactly all 13 material fields.
- [x] `applied_diffs` must contain every material field exactly once.
- [x] `unresolved_binding_matrix` must be exactly empty.
- [x] Candidate `draft` must equal the validated M28 `draft_after` exactly.
- [x] `market_price` remains `FACT`.
- [x] `equity.cash` and `equity.minority_interest` remain `NORMALIZED_FACT`.
- [x] `equity.debt` and `equity.diluted_shares` remain `DERIVED` and can never be silently relabeled as `FACT` or `NORMALIZED_FACT`.
- [x] WACC, terminal growth, and all six forecast inputs remain `ASSUMPTION` with non-empty governed rationale.
- [x] Material numeric-path enumeration reuses the historical M9 contract; every material numeric path is covered exactly once and no `UNKNOWN` remains.
- [x] The evidence catalog covers exactly the five observed material fields.
- [x] Catalog values, classes, valuation `as_of`, proposal decisions, applied diffs, and SHA lineage cannot drift from the complete M28 result.
- [x] Tier D cannot support any M29 observed material input, including `DERIVED` debt and diluted shares.
- [x] Re-signing an outer candidate cannot legitimize nested bound-result, catalog, governance, or lineage tampering.
- [x] Promotion requires explicit human `APPROVE`, reviewer, rationale, timezone-aware review time, and exact review-scope SHA lock.
- [x] M10 `promotion-package-v0.1` accepts v0.2 through backward-compatible promotion dispatch without changing historical package semantics.
- [x] M29 canonical admission preserves the exact reviewed source package and exact raw M28 `draft_after` in `SOURCE_PACKAGE.json`.
- [x] Canonical `case_inputs.json` uses only a deterministic normalized view of that same Draft and preserves the historical `BEAR / BASE / BULL` canonical-adapter requirement.
- [x] Admission validation deterministically reconstructs artifacts and checks package, candidate, evidence, governance, adapter, and runtime provenance.
- [x] M29 repository-plan build/validation reuses the M12 branch, collision, registry-baseline, artifact-hash, and deterministic-plan controls.
- [x] Actual canonical application remains a separate repository-governed `admission/*` operation.
- [x] CLI successor chain preserves M1–M28 commands and installs `vih = valuation_hub.cli_entry_m29:main`.
- [x] Web `/equity-handoff` and `/api/equity-handoff/*` remain preparation/validation only with no automatic approval, file write, admission apply, or canonical write.
- [x] M26/M27/M28 predecessor interface tests validate the successor chain rather than pinning obsolete terminal entrypoints.
- [x] Core M29 candidate, tamper, authority, interface, promotion-package, admission, and change-plan regressions are present.
- [x] Full Python 3.11/3.12 CI succeeded on implementation checkpoint `632136c2489d6f85c6c79407907170b86268749d` in run `34790402787`.

## Finalization gates / 최종화 게이트

The exact documentation-complete PR head must receive a fresh full Python 3.11/3.12 CI success before merge. PR #63 must record that exact tested head and CI run and contain `Closes #62`. Merge must use `expected_head_sha`; Issue #62 must close; then the resulting `main` merge commit must pass post-merge Python 3.11/3.12 CI. No M30 work starts before those gates are complete.

문서까지 포함한 정확한 PR 최종 head는 병합 전에 새로운 전체 Python 3.11/3.12 CI 성공을 받아야 한다. PR #63에는 정확한 tested head·CI run·`Closes #62`를 기록하고 `expected_head_sha`로 병합한다. 이후 Issue #62 종료와 병합된 `main`의 post-merge Python 3.11/3.12 CI 성공을 확인하기 전에는 M30 작업을 시작하지 않는다.

## Merge gate / 병합 게이트

Do not merge if any path can weaken the 13/13 complete-result requirement, alter inherited authority, accept Tier-D observed evidence, leave an `UNKNOWN` material input, bypass human review or scope locking, mutate the exact source Draft in the source package, weaken canonical-adapter requirements, or bypass the separately governed canonical admission/apply workflow.

13/13 완전결과 요구조건·상속 권위·Tier-D 차단·`UNKNOWN` 금지·인간검토/해시잠금·source package의 정확한 Draft 보존·canonical adapter 요구조건·별도 정식 admission/apply 거버넌스 중 하나라도 약화될 수 있으면 병합하지 않는다.
