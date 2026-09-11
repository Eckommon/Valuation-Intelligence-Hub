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

M16 final PR CI `34580879940` and post-merge `main` CI run `34580956086` have Python 3.11/3.12 jobs completed `success`.

Earlier M1–M11 milestones remain completed and regression-locked in repository history.

## Authority model / 권위모델

```text
SOURCE
  ↓
IMMUTABLE SNAPSHOT / NOT CANONICAL
  ↓
EVIDENCE CANDIDATE / NOT CANONICAL
  ↓
NORMALIZED OBSERVATION / TTM / NOT CANONICAL
  ↓
BINDING PROPOSAL / NOT CANONICAL
  ↓
HUMAN APPROVAL LOCK / NOT CANONICAL
  ↓
BOUND DRAFT RESULT / NOT CANONICAL
  ↓
DRAFT EVIDENCE GOVERNANCE + HUMAN REVIEW
  ↓
PROMOTION → ADMISSION → guarded repository apply → PR/CI merge
  ↓
CANONICAL
```

## Active mission / 활성 미션

- Issue: `#38 [M17] Human-approved binding application to noncanonical Draft`
- PR: `#39 M17 Human-approved noncanonical Draft binding apply`
- Branch: `mission/m17-human-approved-binding-apply-v01`
- Status: `ACTIVE_FINALIZATION`

## M17 objective / M17 목표

Apply only explicitly human-approved M16 `DIRECT_BIND` decisions to a valid noncanonical `equity_fcff` Draft while keeping the original Draft unchanged and preserving full auditability.

## Approval contract / 승인 계약

`binding-approval-v0.1` locks:

- reviewer
- timezone-aware approval timestamp
- exact M16 proposal SHA-256
- exact target Draft-before SHA-256
- target entity ID + financial scope
- exact approved field list
- approval SHA-256

Proposal/Draft/identity/field/reviewer/timestamp mutation invalidates approval.

## Apply boundary / 적용경계

- only current `DIRECT_BIND` fields can be approved/applied
- v0.1 therefore applies only eligible `equity.cash`
- target Draft must validate as `draft-case-v0.1 / equity_fcff`
- Draft currency must match proposal monetary unit
- target entity/scope assertion must equal proposal identity
- input Draft object is deep-copied and never mutated
- no filesystem Draft overwrite
- no canonical write

## Bound result / 바인딩 결과

`bound-draft-result-v0.1` contains:

- full M16 binding proposal
- full human approval
- Draft before + SHA-256
- exact applied diffs
- Draft after + SHA-256
- unresolved binding matrix
- full result SHA-256

Each diff records field, before/after values, source metric, and source observation SHA-256.

Result remains `canonical=false` and the resulting Draft must pass existing Draft validation.

## Interfaces / 인터페이스

CLI:

```text
binding-approval-build
binding-approval-validate
binding-apply
bound-draft-validate
```

Web:

```text
/binding-apply
POST /api/binding-apply/approval-build
POST /api/binding-apply/approval-validate
POST /api/binding-apply/apply
POST /api/binding-apply/result-validate
```

Web apply is in-memory JSON transformation only. No filesystem/canonical mutation endpoint exists.

## Files / 파일

- `src/valuation_hub/binding_apply.py`
- `schemas/binding_approval.schema.json`
- `schemas/bound_draft_result.schema.json`
- `src/valuation_hub/web_binding_apply.py`
- `tests/test_binding_apply.py`
- `tests/test_m17_interfaces.py`
- `docs/BINDING_APPLICATION.md`
- `docs/M17_ACCEPTANCE.md`
- `docs/M17_IMPLEMENTATION_SUMMARY.md`

## Grounding authority / 근거화 권위

1. merged `main` files and decisions
2. `PROJECT_STATE.md` + active Issue/PR/branch
3. immutable snapshot → normalized observation → binding proposal → approval → bound-result SHA lineage
4. current chat
5. AI recollection

## Exact resume point / 정확한 재개점

Run fresh Python 3.11/3.12 CI on the final PR #39 head. Merge only if approval locking, DIRECT_BIND-only apply, entity/scope/currency guards, input-Draft nonmutation, diff/source lineage, standalone result validation, CLI/Web no-file-write boundaries, and all M1–M17 regressions pass. Then verify post-merge `main` CI and Issue #38 closure.

After M17, prioritize governed derivation adapters for semantically non-identical but derivable model inputs (e.g. interest-bearing debt and diluted shares) rather than automatically generating forecast assumptions from historical facts.
