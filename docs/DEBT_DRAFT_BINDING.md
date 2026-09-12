# Governed Debt → Draft Binding / 거버넌스 이자부채 → Draft 바인딩

M20 connects only complete, reviewed M19 interest-bearing-debt evidence to `equity.debt`. It extends the binding path without weakening the existing M16/M17 authority boundaries.

M20은 완전하고 검토완료된 M19 이자부채 근거만 `equity.debt`로 연결합니다. 기존 M16/M17 권위경계를 약화하지 않습니다.

## Authority flow / 권위 흐름

```text
M19 interest-bearing-debt-evidence-v0.1
        ↓ complete + DERIVED_FACT only
period date resolution
  ├─ EXACT → source date
  └─ REPORT_STAGE_ONLY → human debt-date-assertion-v0.1
        ↓
debt-binding-context-v0.1
        ↓ freshness evaluation
draft-binding-proposal-v0.2
        ↓ explicit M17 human approval
bound-draft-result-v0.1 / noncanonical
```

No stage creates canonical evidence automatically.

## Date policy / 날짜 정책

`EXACT` source debt uses its source period end directly. A date assertion cannot override it.

`REPORT_STAGE_ONLY` debt has no automatic exact date. M20 requires `debt-date-assertion-v0.1`, which locks:

- reviewer
- timezone-aware approval timestamp
- exact M19 `debt_sha256`
- entity + financial scope
- complete original source-period identity
- asserted exact period-end date
- human review basis
- assertion SHA-256

The assertion remains `canonical=false`.

## Debt binding eligibility / Debt 바인딩 적격성

A debt binding context can be constructed only from M19 evidence that is:

```text
coverage = COMPLETE_CORE_COMPONENTS
class = DERIVED_FACT
semantic_boundary.eligible_for_draft_direct_bind = true
```

Partial, conflict-blocked, or candidate debt fails before binding-context construction.

Freshness is evaluated after date resolution. Fresh debt may become `DIRECT_BIND`; stale debt becomes `STALE_BLOCKED`.

## Proposal compatibility / Proposal 호환성

The original `build_binding_proposal()` and `draft-binding-proposal-v0.1` remain unchanged.

M20 adds `build_binding_proposal_with_debt()` and `draft-binding-proposal-v0.2`. The v0.2 builder first creates a valid v0.1 proposal, then replaces **only** `equity.debt` classification. Every other material-field decision must exactly equal the embedded v0.1 proposal.

The v0.2 proposal embeds:

- complete base v0.1 proposal
- complete debt-binding context
- debt projection in baseline context
- source debt/context/date-assertion lineage
- proposal SHA-256

This makes v0.2 independently auditable without changing the historical v0.1 contract.

## M17 approval/application / M17 승인·적용

The existing `binding-approval-v0.1` remains the human approval object. M20 extends the apply implementation so `equity.debt` is supported when and only when the proposal classifies it `DIRECT_BIND`.

Debt applied diffs preserve:

- debt binding context SHA-256
- M19 source debt SHA-256
- date assertion SHA-256 when one was required

The original Draft is deep-copied and remains unchanged. The result is in-memory/noncanonical only.

## CLI

```text
debt-date-assertion-build
debt-date-assertion-validate
debt-binding-context-build
debt-binding-context-validate
binding-build-with-debt
binding-validate
binding-approval-build
binding-approval-validate
binding-apply
bound-draft-validate
```

## Web

The `/debt` lab additionally exposes calculate/validate-only endpoints:

```text
POST /api/debt/date-assertion-build
POST /api/debt/date-assertion-validate
POST /api/debt/binding-context-build
POST /api/debt/binding-context-validate
POST /api/debt/binding-proposal-build
POST /api/debt/binding-proposal-validate
```

There is no Draft-file write, promotion, admission, or canonical-write endpoint.

## Explicit prohibitions / 명시적 금지

```text
liabilities → debt                         forbidden
partial debt → final debt                 forbidden
candidate debt → DIRECT_BIND              forbidden
REPORT_STAGE_ONLY → invented exact date   forbidden
stale debt → DIRECT_BIND                  forbidden
M20 v0.2 → mutate old M16 v0.1 decisions forbidden except equity.debt
```
