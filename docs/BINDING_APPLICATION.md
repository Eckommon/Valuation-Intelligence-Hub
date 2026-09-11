# Human-approved Draft Binding Application / 인간승인 Draft 바인딩 적용

## Purpose / 목적

M17 applies only explicitly human-approved M16 `DIRECT_BIND` decisions to an existing noncanonical equity-FCFF Draft. It creates a new in-memory audited Draft result and never overwrites a Draft file or creates canonical state.

## State flow / 상태 흐름

```text
M16 BINDING PROPOSAL / NOT CANONICAL
        ↓
HUMAN APPROVAL LOCK / NOT CANONICAL
        ↓
IN-MEMORY BOUND DRAFT RESULT / NOT CANONICAL
        ↓
existing Draft evidence governance + review
```

## Approval lock / 승인 잠금

`binding-approval-v0.1` locks:

- reviewer
- timezone-aware approval timestamp
- exact M16 `proposal_sha256`
- exact target Draft-before SHA-256
- asserted target entity ID and financial scope
- exact approved field set
- complete approval SHA-256

Changing the proposal, target Draft, identity, approved fields, reviewer, or timestamp invalidates approval.

## Apply boundary / 적용 경계

Only M16 decisions currently marked `DIRECT_BIND` can be approved or applied. In v0.1 this means only eligible `equity.cash` bindings.

The target Draft must:

- validate as `draft-case-v0.1`
- use model `equity_fcff`
- have currency equal to the M16 proposal monetary unit
- be explicitly asserted to the same entity and financial scope as the proposal

No reference-only, derivation, assumption, missing, conflict, or stale decision can be applied.

## Result / 결과

`bound-draft-result-v0.1` embeds:

- complete binding proposal
- complete human approval
- complete Draft before application
- Draft-before SHA-256
- exact applied diff list
- complete Draft after application
- Draft-after SHA-256
- unresolved binding matrix
- complete result SHA-256

Each applied diff records:

```text
field
before
before → after
source metric
source observation SHA-256
```

The result is independently revalidatable and remains `canonical=false`.

## Non-mutation rule / 비변경 원칙

Application uses deep copies. The input Draft object is never mutated. CLI and Web return JSON only and expose no filesystem overwrite endpoint.

## CLI

```bash
vih binding-approval-build binding.json draft.json \
  --reviewer "Reviewer" \
  --target-entity-id DART_CORP:00126380 \
  --target-financial-scope CFS \
  --approved-field equity.cash \
  --approved-at 2026-09-11T17:50:00+09:00 > approval.json

vih binding-approval-validate approval.json binding.json draft.json
vih binding-apply binding.json draft.json approval.json > bound-result.json
vih bound-draft-validate bound-result.json
```

## Web

```text
/binding-apply
POST /api/binding-apply/approval-build
POST /api/binding-apply/approval-validate
POST /api/binding-apply/apply
POST /api/binding-apply/result-validate
```

The Web apply endpoint performs only in-memory transformation and returns JSON. It does not write files or canonical state.
