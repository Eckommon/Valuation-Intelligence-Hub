# M20 Implementation Summary / M20 구현요약

## Objective / 목표

Safely bridge M19 complete reviewed interest-bearing debt into the existing M16/M17 equity-FCFF Draft path as `equity.debt`, without inventing dates or weakening the older cash-only contract.

## Implemented / 구현

- `src/valuation_hub/debt_binding.py`
  - `debt-date-assertion-v0.1`
  - `debt-binding-context-v0.1`
  - EXACT source-date use
  - REPORT_STAGE_ONLY human date assertion
  - freshness + binding eligibility
- `src/valuation_hub/debt_draft_binding.py`
  - debt-aware `draft-binding-proposal-v0.2`
  - embeds complete v0.1 proposal and debt context
  - changes only `equity.debt` relative to v0.1
- `src/valuation_hub/binding_apply.py`
  - preserves v0.1 cash path
  - extends approval/apply/reconstruction to `equity.debt`
  - debt diff lineage includes context/debt/date-assertion SHA
- `src/valuation_hub/cli_entry.py`
  - date assertion/context commands
  - `binding-build-with-debt`
  - v0.1/v0.2 proposal validation dispatch
- `src/valuation_hub/web_debt.py`
  - calculate/validate-only M20 preparation endpoints
  - preserves M19 `LIABILITIES ≠ DEBT · CALCULATE ONLY` UI contract
- schemas for assertion, context, and v0.2 proposal
- unit, integration, CLI and Web regression tests

## Deliberate compatibility decisions / 의도적 호환성 결정

M20 does **not** modify the original M16 `build_binding_proposal()` semantics. Existing callers still receive `draft-binding-proposal-v0.1`, where debt is unresolved and cash may be DIRECT_BIND.

Debt-aware callers use a separate v0.2 builder. This creates a narrow, auditable compatibility seam instead of silently changing historical behavior.

M20 also reuses `binding-approval-v0.1`; human approval semantics do not fork merely because a second safe material field becomes available.

## Diagnostic history / 진단이력

One checkpoint CI failed after the M20 Web Lab replaced the exact M19 UI contract string `LIABILITIES ≠ DEBT · CALCULATE ONLY`. Core logic tests were green; the failure identified a compatibility contract. M20 restored the original phrase and appended the new human-date/no-write semantics instead of replacing it.

This failed run is diagnostic evidence and is not a merge gate. Only a fresh final-head Python 3.11/3.12 success may authorize merge.
