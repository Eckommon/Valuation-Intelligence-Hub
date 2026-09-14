# M30-B Real Source Preflight v0.2 / 실기업 Source Preflight v0.2

## Resume condition / 재개조건

M30-B starts only after M30-P1 canonical closure:

- merge/main: `11182eeab7e60a90e6ddc140ca05f45e93af7e40`
- Issue #68: completed
- post-merge CI `34795834240`: Python 3.11/3.12 success

## Why a successor / successor 이유

M30-A v0.1 correctly recorded the historical architectural blocker `M19_SEC_COMPLETE_DEBT_PROFILE_UNAVAILABLE`. That historical result must not be rewritten after the fact.

M30-B therefore nests the exact v0.1 artifact and creates `real-equity-source-preflight-v0.2`.

## Debt state transition / debt 상태전이

```text
M30-A
historical SEC five-component path unavailable
        ↓
M30-P1 canonical prerequisite
exact aggregate-debt successor exists
        ↓
M30-B probes actual captured M13 snapshot
        ├─ exact concept missing/conflicting
        │      → HOLD / SEC_EXACT_AGGREGATE_DEBT_UNAVAILABLE
        └─ exact candidate available
               → architectural blocker resolved
               → CONTINUE_TO_HUMAN_DEBT_SEMANTIC_REVIEW
```

An available candidate is not a reviewed fact and does not authorize binding.

## Exact concept / 정확 concept

Only:

`us-gaap:DebtLongtermAndShorttermCombinedAmount`

No total-liabilities fallback and no inferred zero are permitted.

## Preserved evidence / 보존근거

v0.2 preserves:

- entire v0.1 preflight
- v0.1 preflight SHA
- target identity
- cash/share/NCI probes
- v0.1 historical debt capability record
- the canonical M30-P1 resolution commit
- exact successor candidate source identity, snapshot/body SHA and candidate SHA

## Human boundary / 인간 경계

The following remain mandatory:

- `automatic_approval_forbidden = true`
- `canonical_write = false`
- `debt_semantic_review_required = true`
- `debt_semantic_review_may_be_inferred = false`

M30-B stops before semantic approval. Real review must use the separately SHA-locked M30-P1 review lifecycle.

## Non-goal / 비목표

This slice does not capture live SEC bytes by itself, create a reviewed debt profile, bind a Draft, promote a case, or write `registry/cases.json`. It only moves the parent M30 source-contract preflight from an obsolete architectural HOLD to the correct next governed boundary.