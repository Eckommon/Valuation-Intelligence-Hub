# Project State / 프로젝트 상태

> Canonical human-and-AI handoff. Repository-grounded state outranks chat or AI recollection.  
> 인간·AI 공통 정식 인계 문서. 저장소 근거 상태는 채팅·AI 기억보다 우선한다.

## Repository / 저장소

- `Eckommon/Valuation-Intelligence-Hub`
- Purpose: cross-asset, evidence-grounded valuation intelligence / 범자산 근거 기반 가치분석 인텔리전스

## Completed canonical baseline / 완료 기준선

| Milestone | Main commit | Issue |
|---|---|---:|
| M20 Reviewed debt → `equity.debt` | `236547512919b5d68e283b3431183f56f5fc845c` | #44 |
| M21 Historical dilution reference | `03af933835b8fbcf9ef4e6b3fd1b3db7603782fc` | #46 |
| M22 Valuation-date share bridge | `0a476cc9927b2d63164143447428f3e69b06051b` | #48 |
| M23 Complete share bridge → `equity.diluted_shares` | `58d963238992f562c89c8325b42046ae35ac71bf` | #50 |
| M24 Governed WACC → `scenario.wacc` | `ca85f04c1bd84c5189f78c81e2653cc4f65bccca` | #52 |
| M25 Governed terminal growth → `scenario.terminal_growth` | `0c0a7591a59f163fa34aba54fdeb6001fb9b7dc0` | #54 |
| M26 Integrated forecast → six-field atomic binding | `130363475139fe6ea30d00d615f387b440a23c71` | #56 |
| M27 Governed market price → `market_price` | `3a5f2742acd11756a78579e8fd8ba8709a267327` | #58 |
| M28 Governed minority interest → `equity.minority_interest` | `db5d8e835455de9e52bc656b1ddb4c352736768b` | #60 |

Earlier M1–M19 milestones remain completed and regression-locked in repository history.

### Recent canonical CI / 최근 정식 CI

- M24 final/post-merge: `34693544084` / `34693990230` → Python 3.11/3.12 success
- M25 final/post-merge: `34694777238` / `34694840768` → Python 3.11/3.12 success
- M26 final/post-merge: `34708790304` / `34708847816` → Python 3.11/3.12 success
- M27 final/post-merge: `34721632879` / `34721689531` → Python 3.11/3.12 success
- M28 final tested head `0af0a31899d2af71d0c07cad7ebac44385f18cfd`: `34748926438` → Python 3.11/3.12 success
- M28 post-merge main `db5d8e835455de9e52bc656b1ddb4c352736768b`: `34748992915` → Python 3.11/3.12 success

## Authority model / 권위모델

```text
SOURCE
  ↓
IMMUTABLE / SOURCE-LOCKED INPUT / NOT CANONICAL
  ↓
FACT_CANDIDATE / NORMALIZED FACT / ASSUMPTION_CANDIDATE
  ↓
HUMAN-REVIEWED FACT / NORMALIZED_FACT / DERIVED / ASSUMPTION / NOT CANONICAL
  ↓
BINDING PROPOSAL / NOT CANONICAL
  ↓
HUMAN APPROVAL LOCK / NOT CANONICAL
  ↓
BOUND DRAFT RESULT / NOT CANONICAL
  ↓
COMPLETE GOVERNED HANDOFF
  ↓
PROMOTION → ADMISSION → guarded apply → PR/CI merge
  ↓
CANONICAL
```

Calculation never silently upgrades authority. `DERIVED` is not `FACT`; reviewed state is not canonical state; a complete bound Draft is still noncanonical until the repository-governed promotion/admission lifecycle completes.

## Active mission / 활성 미션

- Issue: `#62 [M29] Complete governed equity handoff: bound Draft → promotion candidate`
- PR: `#63 M29 Complete governed equity handoff → promotion candidate v0.2`
- Branch: `mission/m29-complete-governed-equity-handoff-v01`
- Base main: `db5d8e835455de9e52bc656b1ddb4c352736768b`
- Status: `ACTIVE_FINALIZATION`
- Verified implementation checkpoint: `632136c2489d6f85c6c79407907170b86268749d`
- Checkpoint CI: `34790402787` → full Python 3.11/3.12 success

The branch head is intentionally mutable during documentation finalization. **Never use an embedded branch SHA in this document as merge authorization.** The only merge-authorizing SHA is the exact final PR #63 head recorded in the PR body after fresh final-head CI succeeds.

문서 최종화 중 branch head는 변경될 수 있다. **이 문서 내부의 branch SHA를 병합 승인값으로 사용하지 않는다.** 병합 승인 SHA는 최종 문서 head에 대한 새 CI가 성공한 뒤 PR #63 body에 기록한 exact final head뿐이다.

## M29 mission / M29 미션

Eliminate manual reclassification between a complete M28 bound equity-FCFF Draft and the historical M9–M12 promotion/admission pipeline, while preserving the exact governed authority, values, human approvals, applied diffs, and nested SHA lineage already established by M20–M28.

완전한 M28 bound equity-FCFF Draft와 기존 M9–M12 승격·수용 흐름 사이의 수동 재분류를 제거하되 M20–M28이 확립한 정확한 권위·값·인간승인·applied diff·nested SHA lineage를 그대로 보존한다.

```text
complete M28 v0.8 bound result
        ↓
promotion-candidate-v0.2
        ↓
human promotion review + review_scope_sha256
        ↓
promotion-package-v0.1
        ↓
M29 admission dispatcher
        ↓
M29 guarded repository-plan dispatcher
        ↓
separate admission/* PR + full CI + human review + merge
```

## Complete-result boundary / 완전결과 경계

M29 accepts only an independently validated M28 result satisfying all of:

```text
proposal schema          = draft-binding-proposal-v0.8
material decisions       = 13/13 DIRECT_BIND
human approved fields    = exactly 13/13
applied diffs             = exactly 13/13, unique
unresolved matrix         = []
draft_after               = valid equity_fcff Draft
canonical                 = false
result/proposal lineage   = independently recomputable
```

Partial approval, a missing/duplicate diff, an older proposal version, nested lineage tampering, or outer-SHA re-signing fails closed.

## Authority inheritance / 권위 상속

M29 does not re-decide authority. Exact classes are:

```text
market_price               → FACT
equity.cash                → NORMALIZED_FACT
equity.minority_interest   → NORMALIZED_FACT
equity.debt                → DERIVED
equity.diluted_shares      → DERIVED
scenario WACC paths        → ASSUMPTION
terminal-growth paths      → ASSUMPTION
six forecast-input paths   → ASSUMPTION
```

Debt and diluted shares must never be upgraded to `FACT` or `NORMALIZED_FACT`.

## Evidence catalog / 근거 catalog

M29 receives exactly five observed claims for market price, cash, minority interest, debt, and diluted shares. The catalog supplies M9-compatible descriptive evidence metadata but cannot change any bound value, authority class, valuation `as_of`, proposal decision, applied diff, or exact lineage.

All five observed fields require source tier A/B/C. Tier D is forbidden even for the two `DERIVED` fields.

Every material numeric Draft path is deterministically projected through the historical M9 material-path enumeration. Every path must appear exactly once; no material `UNKNOWN` state is allowed.

## Review lock / 검토 잠금

`promotion-candidate-v0.2` embeds:

```text
exact M28 draft_after
complete source bound result
source bound-result SHA
input_governance projection
five observed evidence claims
human review object
```

Promotion requires explicit `APPROVE`, reviewer identity, rationale, timezone-aware `reviewed_at`, and exact `review_scope_sha256`. The scope includes the embedded source result, so nested mutation invalidates the approval even if an outer object is re-signed.

## M10–M12 compatibility / M10–M12 호환

Historical v0.1 behavior remains delegated unchanged.

M10:
- `promotion-package-v0.1` remains the package contract.
- promotion checking dispatches to v0.1 or v0.2 candidate semantics.

M11-compatible M29 admission:
- `SOURCE_PACKAGE.json` preserves the exact reviewed v0.2 package, exact raw M28 `draft_after`, and complete governance/lineage.
- `case_inputs.json` uses only the deterministic normalized view of that same Draft required by the historical canonical adapter.
- the historical canonical equity profile `BEAR / BASE / BULL` remains mandatory.
- values, authority classes, evidence claims, and source lineage are not reconstructed or re-governed.

M12-compatible M29 plan:
- reuses target collision and registry collision checks;
- locks the current registry SHA and planned registry SHA;
- verifies every artifact hash and safe path;
- retains `admission/*` branch policy and blocks `main`/`master` direct application;
- deterministically reconstructs the plan.

Actual canonical file application remains outside M29 as a separate guarded repository operation.

## Interfaces / 인터페이스

Installed CLI entrypoint:

```text
vih = valuation_hub.cli_entry_m29:main
```

M29 commands/intercepts:

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

All non-M29 commands delegate through `cli_entry_m28` and the predecessor chain.

Web:

```text
/equity-handoff
/api/equity-handoff/catalog-claim
/api/equity-handoff/build
/api/equity-handoff/assess
/api/equity-handoff/validate
/api/equity-handoff/check
```

Explicit Web boundary:

```text
NO AUTO APPROVAL
NO FILE WRITE
NO ADMISSION APPLY
NO CANONICAL WRITE
```

## M29 CI history / M29 CI 이력

- Core implementation checkpoint: CI `34789595564` → Python 3.11/3.12 success.
- M10–M12 integration checkpoint after canonical `BEAR / BASE / BULL` and exact-source/normalized-view separation: CI `34790170693` → Python 3.11/3.12 success.
- Successor-interface correction checkpoint `632136c2489d6f85c6c79407907170b86268749d`: CI `34790402787` → Python 3.11/3.12 success.
- Documentation finalization then adds the M29 methodology, acceptance, implementation summary, README update, and this state handoff.
- A **fresh exact final-head Python 3.11/3.12 CI** is mandatory after the documentation-complete head is formed.

## M29 files / M29 파일

Core:
- `src/valuation_hub/promotion_m29.py`
- `src/valuation_hub/admission_m29.py`
- `src/valuation_hub/admission_apply_m29.py`
- `src/valuation_hub/cli_entry_m29.py`
- `src/valuation_hub/web_complete_equity_handoff.py`
- `src/valuation_hub/promotion_package.py` — promotion-check dispatcher only

Schema:
- `schemas/promotion_candidate_v02.schema.json`

Tests:
- `tests/test_m29_complete_equity_handoff.py`
- `tests/test_m29_promotion_admission_integration.py`
- `tests/test_m29_interfaces.py`
- successor-chain updates in `tests/test_m26_interfaces.py`, `tests/test_m27_interfaces.py`, `tests/test_m28_interfaces.py`

Docs:
- `docs/COMPLETE_GOVERNED_EQUITY_HANDOFF.md`
- `docs/M29_ACCEPTANCE.md`
- `docs/M29_IMPLEMENTATION_SUMMARY.md`
- `README.md`
- `PROJECT_STATE.md`

## Grounding authority / 근거화 권위

1. merged `main` files and completed Issue/PR decisions
2. current active Issue #62 / PR #63 / branch state
3. `PROJECT_STATE.md` and exact M29 docs
4. source M28 result SHA → v0.2 candidate/review-scope SHA → promotion-package SHA → admission bundle SHA → repository-plan SHA
5. current chat
6. AI recollection

## Exact resume point / 정확한 재개점

1. Resolve the exact current PR #63 head after the M29 docs/README/PROJECT_STATE finalization commits.
2. Run/verify fresh full CI on that **exact head** for Python 3.11 and 3.12.
3. Fix only real failures; never weaken the 13/13, authority, lineage, human-review, adapter, or no-write contracts.
4. Update PR #63 body with the exact final tested SHA, CI run, final M29 architecture, and `Closes #62`.
5. Re-read PR #63 head and merge only with the same `expected_head_sha`.
6. Confirm Issue #62 is completed.
7. Re-ground merged `main` and verify post-merge Python 3.11/3.12 CI.
8. Do **not** begin M30 until step 7 is green.

Merge only if all remain green:

- complete M28 v0.8 source gate and exact source-result revalidation
- 13/13 DIRECT_BIND + 13/13 approval + 13/13 unique applied diffs + unresolved=[]
- exact M28 `draft_after` preserved in v0.2 candidate and source package
- fixed authority inheritance including `DERIVED` debt/diluted shares
- exactly five A/B/C-tier observed evidence claims and no Tier D
- exact value/class/as-of/proposal-decision/applied-diff lineage
- full material numeric-path coverage and no `UNKNOWN`
- SHA-locked explicit human promotion review
- v0.1 backward compatibility
- exact SOURCE_PACKAGE vs deterministic canonical normalized-view separation
- historical `BEAR / BASE / BULL` canonical adapter contract
- deterministic M29 admission and guarded M12-style plan
- additive M26 → M27 → M28 → M29 CLI successor chain
- Web no-auto-approval/no-write/no-admission-apply/no-canonical-write boundary
- all M1–M28 regressions

After M29 canonical closure, reassess the next mission from the merged product state. Do not assume M30 before the M29 merge and post-merge CI are durable.
