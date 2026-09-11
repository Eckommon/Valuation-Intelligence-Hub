# M16 Implementation Summary / M16 구현요약

## Delivered / 구현

- `src/valuation_hub/draft_binding.py`
  - 13-field equity-FCFF binding matrix
  - semantic-equivalence guards
  - authority propagation controls
  - explicit freshness/staleness evaluation
  - entity/scope/unit compatibility gates
  - same-metric conflict blocking
  - deterministic proposal SHA-256
- `schemas/draft_binding_proposal.schema.json`
- CLI proposal commands through `valuation_hub.cli_entry`
  - `binding-build`
  - `binding-validate`
- read-only Web Binding Lab through `valuation_hub.web_binding`
  - `/binding`
  - build/validate APIs only
- policy/invariant tests in `tests/test_draft_binding.py`
- CLI/Web boundary tests in `tests/test_m16_interfaces.py`

## Key safety decision / 핵심 안전판단

M16 deliberately refuses superficially convenient mappings that would change accounting meaning:

```text
liabilities ≠ debt
shares_outstanding ≠ diluted_shares
historical/TTM revenue ≠ forecast revenue
```

The system reports unresolved work instead of manufacturing a complete Draft.

## v0.1 DIRECT_BIND / v0.1 직접바인딩

Only reviewed, fresh, exact-date, `INSTANT` cash may propose a direct bind to `equity.cash`. All other material equity-FCFF fields remain reference, derivation, assumption, missing, conflict, or stale states unless future reviewed semantic adapters are introduced.

## Non-goals / 비목표

- no Draft mutation
- no automatic assumption generation
- no forecast generation
- no canonical write
- no evidence promotion
- no implicit entity mapping
- no conflict averaging

## Next architectural gap / 다음 구조적 간극

The next safe step is a separate human-approved binding-application phase that takes a SHA-locked proposal and a noncanonical Draft/template, applies only approved `DIRECT_BIND` fields, preserves unresolved fields, records an exact diff/provenance lock, and still does not create canonical state.
