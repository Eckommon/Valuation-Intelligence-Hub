# M18 Acceptance / M18 완료조건

M18 is complete only if all conditions below pass on the final PR head.

1. `operating_income / revenue` deterministically produces `historical_operating_margin`.
2. `net_income / revenue` deterministically produces `historical_net_income_margin`.
3. Entity, financial scope, source unit, and full normalized period identity must match exactly.
4. Zero revenue fails closed.
5. `NORMALIZED_FACT` inputs produce `DERIVED_FACT`; any candidate input produces `DERIVED_FACT_CANDIDATE`.
6. All outputs remain `canonical=false`.
7. Exact source observation hashes, values, formula, and propagated authority are preserved.
8. Arithmetic, lineage, identity, authority, or semantic-boundary tampering is detected by validation/SHA-256.
9. Every result is explicitly `historical_only=true` and `forecast_direct_bind=false`.
10. M16 cannot treat a derived historical ratio as a forecast `DIRECT_BIND` input.
11. CLI and Web surfaces are calculate/validate only, with no file-write, Draft mutation, promotion, admission, or canonical-write path.
12. M1–M17 behavior remains regression-identical.
13. Full Python 3.11/3.12 CI passes on the final PR head and after merge to `main`.
