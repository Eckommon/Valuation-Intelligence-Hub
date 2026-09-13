# M29 Implementation Summary / M29 구현요약

## What M29 adds / M29 추가사항

M29 converts the thirteen separately governed equity-FCFF material-input paths completed through M28 into one reproducible, review-locked handoff to the existing M9–M12 promotion/admission architecture.

M29는 M28까지 각각 거버넌스된 13개 equity-FCFF 중요입력 경로를 기존 M9–M12 승격·수용 구조로 전달하는 하나의 재현 가능하고 검토 잠금된 인계로 결합한다.

```text
M28 complete bound Draft
  ↓
promotion-candidate-v0.2
  ↓
human promotion review + review-scope SHA
  ↓
promotion-package-v0.1
  ↓
M29 admission dispatcher
  ↓
M29 guarded repository-plan dispatcher
  ↓
separate admission/* PR / CI / human review / merge
```

## Complete M28 gate / 완전 M28 게이트

`promotion_m29.py` reuses the M28 bound-result validator and then strengthens the entry gate to require exact v0.8, 13/13 `DIRECT_BIND`, exact 13-field approval, exact 13-field unique applied diffs, an empty unresolved matrix, a valid equity-FCFF `draft_after`, and recomputable result lineage.

`promotion_m29.py`는 M28 bound-result validator를 재사용한 뒤 정확한 v0.8·13/13 `DIRECT_BIND`·정확한 13필드 승인·13필드 unique applied diff·빈 unresolved matrix·유효한 equity-FCFF `draft_after`·재계산 가능한 result lineage를 추가로 강제한다.

## promotion-candidate-v0.2 / promotion-candidate-v0.2

The v0.2 candidate stores the exact source `draft_after`, the complete source bound result, its SHA, a deterministic material-path governance projection, exactly five observed evidence claims, and a human review object that starts `PENDING`.

v0.2 candidate는 정확한 source `draft_after`·전체 source bound result·그 SHA·결정론적 material-path governance 투영·정확히 5개의 관측근거 claim·`PENDING`으로 시작하는 인간검토 객체를 저장한다.

Observed authority is fixed as:

```text
market_price               FACT
equity.cash                NORMALIZED_FACT
equity.minority_interest   NORMALIZED_FACT
equity.debt                DERIVED
equity.diluted_shares      DERIVED
```

WACC, terminal growth, and six forecast-input paths remain `ASSUMPTION`. Tier D is blocked for all observed classes. Candidate validation reconstructs catalog values/classes/lineage and every material numeric path, so outer re-signing cannot hide nested tampering.

WACC·terminal growth·6개 forecast 입력 path는 `ASSUMPTION`을 유지한다. 모든 관측 class에 Tier D가 차단되며 candidate validator가 catalog 값·class·lineage·모든 중요 숫자 path를 재구축하므로 outer 재서명으로 nested tampering을 숨길 수 없다.

## Promotion review and package / 승격검토 및 패키지

M29 preserves the historical explicit review lock. Promotion requires `APPROVE`, reviewer, rationale, timezone-aware timestamp, and exact `review_scope_sha256`. The scope includes the source bound result, so any nested change invalidates the review.

M29는 기존 명시적 review lock을 보존한다. 승격에는 `APPROVE`·reviewer·rationale·시간대 포함 timestamp·정확한 `review_scope_sha256`이 필요하며 scope에 source bound result가 포함되어 nested 변경도 검토를 무효화한다.

`promotion_package.py` changes only its promotion-check dispatcher to the M29-compatible implementation. Historical v0.1 candidate/package semantics remain available unchanged.

`promotion_package.py`는 promotion-check dispatcher만 M29 호환 구현으로 전환한다. 역사적 v0.1 candidate/package 의미는 그대로 유지된다.

## Admission compatibility / 수용 호환

`admission_m29.py` is a successor dispatcher rather than a rewrite of M11. For v0.2 it validates the reviewed promotion package and preserves it exactly in `SOURCE_PACKAGE.json`.

`admission_m29.py`는 M11을 재작성하지 않는 successor dispatcher다. v0.2에서는 검토완료 promotion package를 검증하고 `SOURCE_PACKAGE.json`에 그대로 보존한다.

The source candidate continues to contain the exact M28 `draft_after`. Canonical case artifacts use the deterministic reviewed-Draft normalization required by the existing equity adapter, including the historical `BEAR / BASE / BULL` profile. This resolves adapter compatibility without mutating the source Draft or reconstructing governance.

Source candidate는 정확한 M28 `draft_after`를 계속 보존한다. Canonical case 산출물만 기존 equity adapter가 요구하는 결정론적 reviewed-Draft 정규화와 역사적 `BEAR / BASE / BULL` profile을 사용한다. 따라서 source Draft를 변조하거나 거버넌스를 재구축하지 않고 adapter 호환을 달성한다.

Admission validation deterministically rebuilds the bundle and verifies artifact hashes, package provenance, reviewed candidate SHA, review-scope SHA, evidence/governance identity, normalized Draft, adapter selection, and runtime.

## Guarded repository plan / Guarded 저장소 plan

`admission_apply_m29.py` reuses M12 constants and repository controls while dispatching admission validation through M29. It checks target collision, registry collision, exact current registry SHA, planned registry SHA, artifact hashes, safe paths, `admission/*` branch policy, and deterministic plan reconstruction.

`admission_apply_m29.py`는 M12의 상수와 repository 통제를 재사용하면서 admission 검증만 M29로 분기한다. 대상/registry 충돌·현재 registry SHA·계획 registry SHA·artifact hash·safe path·`admission/*` branch policy·결정론적 plan 재구축을 검증한다.

It builds and validates a plan only. Actual canonical write remains outside M29 and must occur through the separate guarded repository workflow.

M29 자체는 plan만 생성·검증하며 실제 canonical write는 별도의 guarded repository workflow에서만 수행된다.

## Interfaces / 인터페이스

Installed console entrypoint:

```text
vih = valuation_hub.cli_entry_m29:main
```

M29 intercepts:

```text
complete-handoff-catalog-claim
complete-handoff-build
complete-handoff-assess
candidate-validate
promotion-check
admission-build
admission-validate
admission-plan
admission-plan-validate
web
```

Other commands delegate through `cli_entry_m28` and the predecessor chain.

Web:

```text
/equity-handoff
/api/equity-handoff/catalog-claim
/api/equity-handoff/build
/api/equity-handoff/assess
/api/equity-handoff/validate
/api/equity-handoff/check
```

The Web Lab accepts no credentials and exposes no automatic approval, file write, admission apply, or canonical write.

## Machine-readable contract / 기계판독 계약

- `schemas/promotion_candidate_v02.schema.json`
- historical `promotion-package-v0.1`, M11 admission schema, and M12 plan schema remain the downstream contracts

## Regression hardening / 회귀 강화

M29 tests cover complete projection, partial approval rejection, `DERIVED` relabel blocking, Tier-D blocking, value/class/lineage tamper blocking, nested bound-result tamper blocking, review-scope locking, v0.1 delegation, promotion-package integration, canonical-admission normalization, deterministic change-plan integration, real CLI candidate build/validate, Web no-write behavior, and the M26 → M27 → M28 → M29 successor chain.

Implementation checkpoint `632136c2489d6f85c6c79407907170b86268749d` passed full Python 3.11/3.12 CI in run `34790402787`. A fresh CI run on the exact documentation-complete final head is still required before merge.
