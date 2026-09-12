# M19 Acceptance / M19 완료조건

M19 is complete only if the final PR head satisfies all conditions below.

1. M13 SEC and M14 OpenDART metric registries remain unchanged by M19 imports.
2. SEC v0.1 maps only exact `us-gaap:ShortTermBorrowings`; broad `LongTermDebt*` concepts are not relabeled as narrow components.
3. OpenDART maps all five core components using exact account IDs then exact Korean account-name fallback.
4. Debt candidates normalize into isolated `debt-component-observation-v0.1` INSTANT observations with source lineage and SHA-256.
5. Only the five explicit core component metrics may enter aggregation; `liabilities` is rejected.
6. Entity, financial scope, unit, and complete period identity must match exactly.
7. Missing components remain missing; partial coverage exposes only `known_component_sum` and no final debt value.
8. Conflicting same-component values produce `CONFLICT_BLOCKED` and expose no numeric total.
9. Equal duplicate values reconcile deterministically while any candidate input keeps aggregate authority candidate.
10. Complete reviewed five-component coverage alone is marked eligible for a future Draft direct binding.
11. Lease liabilities remain explicitly excluded pending a separate policy.
12. Component, input, conflict, coverage, semantic-boundary, and aggregate tampering is detected by validation/SHA-256.
13. CLI/Web are source-read/normalize/calculate/validate only and do not mutate Draft/canonical state.
14. M1–M18 behavior remains regression-identical.
15. Python 3.11/3.12 CI passes on final PR head and post-merge `main`.
