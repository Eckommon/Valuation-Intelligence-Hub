# M15 Acceptance / M15 완료조건

M15 is complete only when all conditions below pass on the final PR head and again after merge to `main`.

1. SEC period classification is deterministic and ambiguous 10-Q duration semantics fail closed.
2. OpenDART `CURRENT` and `CUMULATIVE` semantics are explicit and never conflated.
3. `FACT`/`FACT_CANDIDATE` authority propagates to `NORMALIZED_FACT`/`NORMALIZED_FACT_CANDIDATE` without promotion-by-arithmetic.
4. Observation SHA-256 detects mutation of value, period, lineage, authority, or identity.
5. Four-quarter TTM requires four contiguous quarters with matching metric/entity/scope/unit.
6. Annual-bridge TTM requires comparable fiscal years and identical YTD report stages.
7. TTM SHA-256 locks transform formula, components, result, and input observation hashes.
8. Same-period reconciliation never averages conflicts; conflicting values fail closed as `UNKNOWN_CONFLICT`.
9. CLI exposes normalization, validation, TTM, and reconciliation without canonical writes.
10. Web `/normalize` is calculate-only, rejects credential-bearing payloads, and exposes no live-fetch/write route.
11. SEC M13 and OpenDART M14 behavior remain regression-identical.
12. Full Python 3.11/3.12 CI passes all M1–M15 tests on the final PR head.
13. PR is mergeable and merged only against the tested head SHA.
14. Post-merge `main` CI passes before Issue #32 is considered closed.
