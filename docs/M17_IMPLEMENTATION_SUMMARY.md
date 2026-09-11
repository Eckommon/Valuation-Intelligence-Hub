# M17 Implementation Summary / M17 구현요약

## Delivered / 구현

- `src/valuation_hub/binding_apply.py`
  - SHA-locked human approval
  - proposal/Draft/identity/currency validation
  - DIRECT_BIND-only application
  - deep-copy nonmutation
  - exact before/after/source-hash diffs
  - standalone bound-result validation
- schemas:
  - `schemas/binding_approval.schema.json`
  - `schemas/bound_draft_result.schema.json`
- CLI:
  - `binding-approval-build`
  - `binding-approval-validate`
  - `binding-apply`
  - `bound-draft-validate`
- Web:
  - `/binding-apply`
  - approval build/validate
  - in-memory apply
  - result validate
- tests:
  - `tests/test_binding_apply.py`
  - `tests/test_m17_interfaces.py`

## Safety boundary / 안전경계

M17 creates no canonical state and does not overwrite Draft files. It applies only explicitly human-approved M16 DIRECT_BIND fields to an in-memory deep copy of a validated noncanonical Draft.

## Next architectural gap / 다음 구조적 간극

After M17, the evidence-to-Draft transport path is structurally closed for exact direct bindings. The next high-value problem is governed **derivation adapters** for semantically non-identical but derivable inputs (for example interest-bearing debt, diluted shares, normalized operating margins, reinvestment metrics), with explicit formulas, source requirements, authority propagation, and human review. Forecast assumptions should remain a separate layer rather than being auto-generated from historical facts.
