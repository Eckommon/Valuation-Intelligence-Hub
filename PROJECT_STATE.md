# Project State / 프로젝트 상태

> Canonical human-and-AI handoff. Repository-grounded state outranks chat or AI recollection.  
> 인간·AI 공통 정식 인계 문서. 저장소 근거 상태는 채팅·AI 기억보다 우선한다.

## Repository / 저장소

- `Eckommon/Valuation-Intelligence-Hub`
- Purpose: cross-asset, evidence-grounded valuation intelligence / 범자산 근거 기반 가치분석 인텔리전스

## Completed canonical baseline / 완료 기준선

| Milestone | Main commit | Issue |
|---|---|---:|
| M12 Guarded admission apply | `a40e92c196c39b40172711f38f7231f5e8812d52` | #26 |
| M13 Immutable SEC live evidence | `372b8b0b26307730c3e91afea97c979b59906042` | #28 |
| M14 Immutable OpenDART financial evidence | `1fff272cc583ec294226f5f530ebe483c2957fb5` | #30 |
| M15 Financial normalization + TTM | `a99a6f24fa6736b01b270a2eeeb4592e8b673563` | #32 |
| M16 Governed evidence → Draft binding proposal | `fbaf90bab04a877ba6afaaa035a4e99e9ef085a0` | #34 |
| M17 Human-approved noncanonical Draft binding apply | `ef68c2549bef842ef417d401140b49c88af209b5` | #38 |
| M18 Governed derived financial evidence + historical margins | `fb33cfbf401ab9c2e36ccd831bd059c8951214ba` | #40 |
| M19 Governed interest-bearing debt components + aggregation | `5b2ab53b0c83632abae187f12e1a682ecc254b77` | #42 |

M19 final PR CI `34673236672` and post-merge `main` CI `34673285798` completed `success` on Python 3.11/3.12.

Earlier M1–M11 milestones remain completed and regression-locked in repository history.

## Authority model / 권위모델

```text
SOURCE
  ↓
IMMUTABLE SNAPSHOT / NOT CANONICAL
  ↓
EVIDENCE CANDIDATE / NOT CANONICAL
  ↓
NORMALIZED / DERIVED EVIDENCE / NOT CANONICAL
  ↓
GOVERNED BINDING CONTEXT / NOT CANONICAL
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

Source acquisition, normalization, derivation, date assertion, binding preparation, and Draft application never upgrade evidence authority by themselves.

## Active mission / 활성 미션

- Issue: `#44 [M20] Reviewed debt → equity.debt binding + date assertion`
- PR: `#45 M20 Reviewed debt → equity.debt binding + date assertion`
- Branch: `mission/m20-debt-draft-binding-v01`
- Base main: `5b2ab53b0c83632abae187f12e1a682ecc254b77`
- Status: `ACTIVE_FINALIZATION`

### M20 diagnostic CI history / M20 진단 CI 이력

Checkpoint run `34688393668` failed with **261 passed / 1 failed**. The single failure was the M19 Web regression contract `LIABILITIES ≠ DEBT · CALCULATE ONLY`, which M20 had replaced while extending the UI. Core debt/date/binding logic was not the failing contract. M20 restored the exact M19 phrase and appended the new human-date/no-write semantics.

The failed checkpoint is retained as diagnostic evidence and is not a merge gate. Only a fresh final-head Python 3.11/3.12 success can authorize merge.

## M20 objective / M20 목표

Connect only complete, reviewed M19 interest-bearing debt to the existing equity-FCFF Draft path as `equity.debt`, while preserving M16 v0.1 and M17 cash behavior.

## Date assertion / 날짜승인

For source debt with:

```text
date_precision = EXACT
```

M20 uses the exact source period end and forbids assertion-based override.

For:

```text
date_precision = REPORT_STAGE_ONLY
end = null
```

M20 requires noncanonical `debt-date-assertion-v0.1` locking:

- reviewer
- timezone-aware approval timestamp
- exact M19 `debt_sha256`
- target entity + financial scope
- complete original period identity
- asserted exact period-end date
- human review basis
- assertion SHA-256

The system does not infer or synthesize the exact date.

## Binding context / 바인딩 context

`debt-binding-context-v0.1` accepts only M19 debt that is:

```text
COMPLETE_CORE_COMPONENTS
+ DERIVED_FACT
+ eligible_for_draft_direct_bind=true
```

It resolves the exact period end, calculates age versus `as_of`, and records `FRESH` or `STALE_BLOCKED`.

Partial, conflict-blocked, and candidate debt cannot enter this context.

## Binding proposal v0.2 / 바인딩 제안 v0.2

The original M16 `build_binding_proposal()` remains unchanged and continues to produce `draft-binding-proposal-v0.1`.

M20 adds `draft-binding-proposal-v0.2`, which:

- embeds the complete base v0.1 proposal
- embeds the complete M20 debt-binding context
- requires entity/scope/unit compatibility
- replaces **only** the `equity.debt` decision
- makes fresh eligible debt `DIRECT_BIND`
- makes stale debt `STALE_BLOCKED`
- preserves all non-debt v0.1 decisions exactly
- SHA-locks the full proposal

## M17 integration / M17 통합

Existing `binding-approval-v0.1` is reused. M20 extends the application implementation to support `equity.debt` when and only when v0.2 marks it `DIRECT_BIND`.

Debt applied-diff lineage records:

```text
source_context_sha256
source_debt_sha256
date_assertion_sha256  # null for source EXACT debt
```

The input Draft remains unchanged and the bound result remains `canonical=false`.

## Interfaces / 인터페이스

CLI additions:

```text
debt-date-assertion-build
debt-date-assertion-validate
debt-binding-context-build
debt-binding-context-validate
binding-build-with-debt
```

Existing approval/apply commands are reused.

Web calculate/validate preparation endpoints:

```text
POST /api/debt/date-assertion-build
POST /api/debt/date-assertion-validate
POST /api/debt/binding-context-build
POST /api/debt/binding-context-validate
POST /api/debt/binding-proposal-build
POST /api/debt/binding-proposal-validate
```

No Draft-file write, promotion, admission, or canonical-write M20 endpoint exists.

## M20 files / M20 파일

- `src/valuation_hub/debt_binding.py`
- `src/valuation_hub/debt_draft_binding.py`
- `src/valuation_hub/binding_apply.py`
- `src/valuation_hub/cli_entry.py`
- `src/valuation_hub/web_debt.py`
- `schemas/debt_date_assertion.schema.json`
- `schemas/debt_binding_context.schema.json`
- `schemas/draft_binding_proposal_v02.schema.json`
- `tests/test_debt_binding.py`
- `tests/test_m20_binding.py`
- `tests/test_m20_interfaces.py`
- `docs/DEBT_DRAFT_BINDING.md`
- `docs/M20_ACCEPTANCE.md`
- `docs/M20_IMPLEMENTATION_SUMMARY.md`

## Grounding authority / 근거화 권위

1. merged `main` files and decisions
2. `PROJECT_STATE.md` + active Issue/PR/branch
3. M19 debt SHA → M20 date assertion/context SHA → proposal SHA → approval SHA → bound-result SHA lineage
4. current chat
5. AI recollection

## Exact resume point / 정확한 재개점

Run fresh Python 3.11/3.12 CI on the final PR #45 head. Merge only if M16 v0.1 cash compatibility, M19 Web contract compatibility, date assertion locking, complete/reviewed/fresh debt eligibility, stale/partial/conflict/candidate blocking, entity/scope/unit guards, debt-aware v0.2 proposal integrity, M17 debt approval/apply lineage, no-write CLI/Web boundaries, and all M1–M20 regressions pass.

After merge, verify Issue #44 closure and post-merge `main` CI before declaring M20 canonical. The next likely priority after a clean M20 close is governed diluted-share evidence/derivation because `shares_outstanding ≠ diluted_shares` remains unresolved.
