# M30-D Acceptance / M30-D 완료기준

## Functional / 기능

- [x] `real-equity-readiness-manifest-v0.1` is noncanonical and SHA-locked.
- [x] Exact M16/M29 13 material fields are projected without rename or reclassification.
- [x] Field authority is fixed as FACT / NORMALIZED_FACT / DERIVED / ASSUMPTION.
- [x] Readiness states distinguish source, human review, dependency, and blocking boundaries.
- [x] M24 seven WACC source inputs are explicit DAG nodes.
- [x] M25 two macro anchors and reviewed-WACC dependency are explicit DAG nodes.
- [x] M26 six forecast fields share one atomic reviewed forecast package prerequisite.

## M30-B projection / M30-B 투영

- [x] Embedded M30-B v0.2 input is independently validated.
- [x] No preflight produces `REAL_SEC_PREFLIGHT_NOT_SUPPLIED`; no source readiness is invented.
- [x] Cash/share/NCI/debt candidate presence advances only to `AWAITING_HUMAN_REVIEW`.
- [x] Missing exact aggregate debt remains `AWAITING_REAL_SOURCE` and preserves the source blocker.
- [x] Registry collision blocks all 13 fields.

## Integrity / 무결성

- [x] Exact 13-field order/coverage validation.
- [x] Unique prerequisite node IDs.
- [x] Unknown DAG dependency rejection.
- [x] Cycle rejection.
- [x] Deterministic target + embedded-preflight reconstruction.
- [x] Re-sealed field-state tamper rejection.
- [x] SHA-256 validation.

## Human / canonical boundary / 인간·정식 경계

- [x] No SEC network call in readiness build.
- [x] No `SEC_USER_AGENT` required.
- [x] No reviewer identity or review timestamp generated.
- [x] No automatic approval.
- [x] No Draft mutation.
- [x] No registry write.
- [x] No canonical write.

## Interface / 인터페이스

- [x] `real-equity-readiness-build`
- [x] `real-equity-readiness-validate`
- [x] Commands are additive under `cli_entry_m30`; prior M29 command delegation remains unchanged.
- [x] Validation is read-only.

## Merge gates / 병합 게이트

- [ ] exact final-head Python 3.11 CI success
- [ ] exact final-head Python 3.12 CI success
- [ ] PR records exact tested SHA + CI run
- [ ] merge uses exact `expected_head_sha`
- [ ] Issue #73 completed
- [ ] post-merge main Python 3.11/3.12 CI success

M30-D completion does not close parent Issue #66 and does not authorize a canonical Ingredion case.
