# Project State / 프로젝트 상태

> Canonical human-and-AI handoff. Repository-grounded state outranks chat or AI recollection.  
> 인간·AI 공통 정식 인계 문서. 저장소 근거 상태는 채팅·AI 기억보다 우선한다.

## Repository / 저장소

- `Eckommon/Valuation-Intelligence-Hub`
- Purpose: cross-asset, evidence-grounded valuation intelligence / 범자산 근거 기반 가치분석 인텔리전스

## Canonical baseline / 정식 기준선

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
| **M29 Complete governed equity handoff** | **`97dc84d8e9a09b5bd9c6864137a537037baac4f6`** | **#62** |

Earlier M1–M19 milestones remain completed and regression-locked in repository history.

## M29 canonical closure / M29 정식 종결

M29 is **COMPLETE**.

- final tested PR head: `a666d00d45431914fd98deb08f5b336f3c28eeef`
- final-head CI: `34791253465` → Python 3.11/3.12 success
- PR: `#63` merged using exact `expected_head_sha`
- merge/main: `97dc84d8e9a09b5bd9c6864137a537037baac4f6`
- Issue `#62`: completed
- post-merge main CI: `34791345455` → Python 3.11/3.12 success

The complete equity-FCFF handoff is now:

```text
complete M28 v0.8 bound result
  = 13/13 DIRECT_BIND
  = 13/13 human-approved
  = 13/13 unique applied diffs
  = unresolved []
        ↓
promotion-candidate-v0.2
        ↓
explicit human promotion review + review_scope_sha256
        ↓
promotion-package-v0.1
        ↓
M29 admission dispatcher
        ↓
M29 guarded repository-plan dispatcher
        ↓
separate admission/* PR + CI + human review + merge
        ↓
CANONICAL CASE
```

## Authority model / 권위모델

```text
market_price               → FACT
equity.cash                → NORMALIZED_FACT
equity.minority_interest   → NORMALIZED_FACT
equity.debt                → DERIVED
equity.diluted_shares      → DERIVED
scenario WACC              → ASSUMPTION
terminal growth            → ASSUMPTION
six forecast inputs        → ASSUMPTION
```

Authority is inherited, never silently upgraded. `DERIVED != FACT`. A complete bound Draft is not canonical until the separately governed promotion/admission/repository merge completes.

## M29 invariants / M29 불변조건

- source result must independently validate as M28 v0.8
- all 13 material fields must be `DIRECT_BIND`
- human binding approval must cover exactly all 13 fields
- applied diffs must cover each field exactly once
- unresolved matrix must be empty
- v0.2 candidate Draft must equal exact M28 `draft_after`
- five observed fields require A/B/C-tier evidence catalog; Tier D is forbidden
- catalog cannot alter value, authority class, `as_of`, decision, diff, or SHA lineage
- every material numeric path is covered exactly once; no `UNKNOWN`
- explicit promotion review + exact SHA scope lock remains mandatory
- `SOURCE_PACKAGE.json` preserves exact reviewed v0.2 package and raw M28 Draft
- canonical `case_inputs.json` may use only the deterministic normalized view required by the existing adapter
- canonical equity adapter keeps the historical `BEAR / BASE / BULL` requirement
- actual canonical write remains a separate `admission/*` repository operation
- Web handoff remains `NO AUTO APPROVAL / NO FILE WRITE / NO ADMISSION APPLY / NO CANONICAL WRITE`

## Existing canonical case registry / 기존 정식 사례 registry

`registry/cases.json` currently contains three historical canonical cases:

- `KR_010120_LS_ELECTRIC` — `equity_fcff`
- `KR_229640_LS_ECO_ENERGY` — `equity_fcff`
- `US_JTAI_JET_AI` — `venture_probability`

These cases predate the complete M29 handoff. M29 integration tests prove the entire promotion → admission → guarded-plan contract with a noncanonical test identity, but **no real company case has yet been admitted through the complete M29 path**.

## Product decision after M29 / M29 이후 제품 판단

The next implementation priority is **not** a non-equity adapter. Breadth before a real end-to-end proof would leave the most important product risk unresolved.

The next priority is the first real complete-governed equity canonical case. That mission must prove that a real company can traverse the full evidence-to-canonical lifecycle without synthetic fixtures, hidden manual reclassification, or direct registry/file writes.

Preferred sequence:

```text
1. select one collision-free real public-equity target
2. acquire/lock real source evidence
3. construct and review all governed M20–M28 inputs
4. obtain complete M28 v0.8 bound result
5. build/review promotion-candidate-v0.2
6. build promotion package + admission bundle + guarded plan
7. apply only on admission/* branch
8. run full CI and human review
9. merge and verify post-merge main
10. only then evaluate product UX expansion or first non-equity adapter
```

A synthetic fixture must never be admitted to `registry/cases.json` merely to claim success.

## Current state-only reconciliation / 현재 상태 정합화

- Issue: `#64 [M29-C] Canonical closure state reconciliation`
- Branch: `state/m29-canonical-closure-v01`
- Base main: `97dc84d8e9a09b5bd9c6864137a537037baac4f6`
- Scope: documentation/state only
- Runtime/schema/valuation/admission behavior changes: **NONE**

This state-only reconciliation must receive full Python 3.11/3.12 CI, merge through its own PR, close Issue #64, and receive post-merge main CI before the next implementation issue is opened.

## Exact resume point / 정확한 재개점

1. Complete Issue #64 state-only reconciliation.
2. Verify exact state-PR head Python 3.11/3.12 CI.
3. Merge only from the tested head using `expected_head_sha`.
4. Confirm Issue #64 completed and post-merge `main` CI green.
5. Re-ground the resulting main.
6. Open the next implementation mission for the **first real complete-governed equity canonical case**.
7. Do not start a non-equity adapter before that real-case proof unless repository evidence shows the real-case path is blocked by an architectural prerequisite.

## Grounding authority / 근거화 권위

1. merged `main` files and completed Issue/PR decisions
2. `PROJECT_STATE.md` and current active Issue/PR/branch
3. exact source/result/candidate/package/admission/plan SHA lineage
4. current chat
5. AI recollection
