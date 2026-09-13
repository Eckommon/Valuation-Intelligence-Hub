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

Earlier M1–M19 milestones remain completed and regression-locked in repository history.

### Recent canonical CI / 최근 정식 CI

- M24 final/post-merge: `34693544084` / `34693990230` → Python 3.11/3.12 success
- M25 final/post-merge: `34694777238` / `34694840768` → Python 3.11/3.12 success
- M26 final/post-merge: `34708790304` / `34708847816` → Python 3.11/3.12 success
- M27 final/post-merge: `34721632879` / `34721689531` → Python 3.11/3.12 success

## Authority model / 권위모델

```text
SOURCE
  ↓
IMMUTABLE / SOURCE-LOCKED INPUT / NOT CANONICAL
  ↓
FACT_CANDIDATE / NORMALIZED FACT / ASSUMPTION_CANDIDATE
  ↓
HUMAN-REVIEWED FACT / GOVERNED CONTEXT / ASSUMPTION / NOT CANONICAL
  ↓
BINDING PROPOSAL / NOT CANONICAL
  ↓
HUMAN APPROVAL LOCK / NOT CANONICAL
  ↓
BOUND DRAFT RESULT / NOT CANONICAL
  ↓
DRAFT GOVERNANCE → PROMOTION → ADMISSION → guarded apply → PR/CI merge
  ↓
CANONICAL
```

Calculation never silently upgrades candidate authority. Reviewed FACT/ASSUMPTION remains noncanonical until repository governance completes.

## Active mission / 활성 미션

- Issue: `#60 [M28] Governed minority-interest FACT + Draft binding`
- PR: `#61 M28 Governed minority-interest FACT + Draft binding`
- Branch: `mission/m28-minority-interest-binding-v01`
- Base main: `3a5f2742acd11756a78579e8fd8ba8709a267327`
- Status: `ACTIVE_FINALIZATION`

## M28 mission / M28 미션

Close the final remaining equity-FCFF material-field gap by governing valuation-date noncontrolling/minority interest as source-backed balance-sheet evidence and binding only reviewed, fresh, eligible `NORMALIZED_FACT` into:

```text
equity.minority_interest
```

가치평가일 비지배지분을 출처기반 재무상태표 근거로 거버넌스하고 검토완료·최신·적격 `NORMALIZED_FACT`만 Draft에 연결한다.

## M28 semantic boundary / M28 의미경계

```text
total equity != minority interest
parent-attributable equity != minority interest
liabilities != minority interest
missing minority-interest evidence != zero
redeemable NCI != M28 v0.1 SEC field
minority-interest FACT != analyst assumption
```

Explicit source-reported zero is valid evidence. Missing evidence fails closed.

## Exact source architecture / 정확한 출처구조

M28 does not mutate M13/M14 historical registries. It uses isolated adapters over validated immutable source snapshots.

SEC v0.1 exact concept:

```text
us-gaap:NonredeemableNoncontrollingInterest
```

OpenDART v0.1 exact account:

```text
CFS + BS + ifrs-full_NoncontrollingInterests
```

No equity-difference derivation or label-only fallback is allowed.

## Evidence lifecycle / 근거 수명주기

```text
immutable SEC/OpenDART snapshot
        ↓
minority-interest-candidate-v0.1 / FACT_CANDIDATE
        ↓
minority-interest-observation-v0.1 / NORMALIZED_FACT_CANDIDATE
        ↓
minority-interest-review-assertion-v0.1
        ↓
reviewed-minority-interest-fact-v0.1 / NORMALIZED_FACT / canonical=false
        ↓
draft-binding-proposal-v0.8
        ↓
M17-family human binding approval/apply
        ↓
noncanonical bound Draft result
```

Nested candidate/observation/review/package hashes and source snapshot lineage are independently revalidated.

## Date and freshness / 날짜·최신성

- SEC instant facts: exact source period end, `SOURCE_EXACT`; human override forbidden.
- OpenDART: `REPORT_STAGE_ONLY`; separate SHA-locked human exact-date assertion required.
- resolved period end after valuation `as_of` fails closed.
- freshness is independently recomputed.
- stale reviewed package remains visible but cannot DIRECT_BIND.

## v0.8 binding / v0.8 바인딩

M28 accepts only validated M27 `draft-binding-proposal-v0.7`.

v0.8 may replace only:

```text
equity.minority_interest
```

Every other material-field decision from v0.7 must remain identical. Exact compatibility is required for entity ID, consolidated scope, currency, and valuation `as_of`.

The proposal and applied diff preserve:

```text
minority-interest package SHA
normalized observation SHA
source snapshot SHA
review assertion SHA
resolved period end
date-resolution method
```

## Apply / 적용

Human binding approval remains mandatory. Apply changes only the in-memory result's `draft["equity"]["minority_interest"]`; the input Draft remains unchanged and the result remains noncanonical. M26 unique-diff-field result-integrity protection remains active.

## Interfaces / 인터페이스

Installed CLI entrypoint:

```text
vih = valuation_hub.cli_entry_m28:main
```

M28 commands:

```text
minority-sec-extract
minority-dart-extract
minority-candidate-validate
minority-normalize
minority-observation-validate
minority-review-build
minority-review-validate
minority-finalize
minority-validate
binding-build-with-minority-interest
binding-validate
```

All older commands delegate through `cli_entry_m27` and predecessor wrappers.

Web:

```text
/minority-interest
/api/minority-interest/*
```

M28 Web is preparation/validation only: no direct Draft apply, file write, promotion, admission, or canonical write.

## M28 CI history / M28 CI 이력

- Initial branch head `ddb5c7f7f74a30624a80072daacacc7500a2b899`
  - CI `34722357783`: corrective failure, 361 passed / 2 stale predecessor entrypoint tests failed.
- First successor-compatible correction `220069fa8db6cb7fee8a03b0eb1a9e317108b0d8`
  - CI `34748635300`: corrective failure, 362 passed / 1 remaining stale M27 entrypoint test failed.
- Full successor-compatible correction `b94de627313f1ff42bbe192b8294a75ee27df9bb`
  - CI `34748676308`: Python 3.11/3.12 success.
- Additional M28 integrity/interface/schema/docs hardening follows on the active branch.

A fresh exact final-head Python 3.11/3.12 CI is required after this handoff update. Only that exact tested head may authorize merge.

## M28 files / M28 파일

Core:
- `src/valuation_hub/minority_interest.py`
- `src/valuation_hub/minority_interest_draft_binding.py`
- `src/valuation_hub/binding_apply_m28.py`
- `src/valuation_hub/cli_entry_m28.py`
- `src/valuation_hub/web_minority_interest.py`

Schemas:
- `schemas/minority_interest_candidate.schema.json`
- `schemas/minority_interest_observation.schema.json`
- `schemas/minority_interest_review_assertion.schema.json`
- `schemas/reviewed_minority_interest_fact.schema.json`
- `schemas/draft_binding_proposal_v08.schema.json`

Tests/docs:
- `tests/test_m28_minority_interest_binding.py`
- `tests/test_m28_hardening.py`
- `tests/test_m28_interfaces.py`
- `docs/MINORITY_INTEREST_FACT_BINDING.md`
- `docs/M28_ACCEPTANCE.md`
- `docs/M28_IMPLEMENTATION_SUMMARY.md`

## Grounding authority / 근거화 권위

1. merged `main` files and completed Issue/PR decisions
2. `PROJECT_STATE.md` + active Issue/PR/branch
3. v0.7 proposal SHA → minority candidate/source snapshot → observation SHA → review assertion SHA → reviewed package SHA → v0.8 proposal SHA → binding approval/result SHA
4. current chat
5. AI recollection

## Exact resume point / 정확한 재개점

1. Verify fresh full CI on the exact current PR #61 head after README/docs/PROJECT_STATE updates.
2. Fix only real failures; do not weaken semantic/fail-closed contracts.
3. Update PR #61 body with the correct SEC concept and exact final tested SHA + CI run.
4. Merge using `expected_head_sha` only.
5. Confirm Issue #60 closes as completed.
6. Verify post-merge `main` Python 3.11/3.12 CI.
7. Re-ground latest main before selecting the next mission.

Merge only if all remain green:

- exact SEC/OpenDART mapping and isolated adapters
- missing ≠ zero; explicit zero preserved
- candidate/reviewed authority separation
- SEC exact date / OpenDART human date-resolution boundary
- freshness and stale non-bindability
- nested source/review/package tamper blocking
- v0.7-only base requirement
- exact entity/scope/currency/as-of compatibility
- only minority-interest decision replaced
- Draft immutability + exact diff lineage
- M26 unique-diff-field integrity guard
- additive CLI successor chain
- Web no-write boundary
- all M1–M27 regressions

After M28 canonical closure, the equity-FCFF material-field matrix should have governed paths for all material fields. Do not automatically add M29; reassess end-to-end case completion, product UX/reporting, and the first non-equity adapter against the product vision.
