# M16 Acceptance / M16 완료조건

M16 is complete only when all conditions below pass on the final PR head and again after merge to `main`.

1. All 13 equity-FCFF material Draft inputs receive one explicit binding state.
2. `liabilities ≠ debt`, `shares_outstanding ≠ diluted_shares`, and historical/TTM revenue ≠ forecast revenue are regression-blocked.
3. `NORMALIZED_FACT_CANDIDATE` can never `DIRECT_BIND`.
4. v0.1 `DIRECT_BIND` is limited to reviewed, fresh, exact-date, `INSTANT` cash → `equity.cash`.
5. Entity, financial-scope, and monetary-unit conflicts fail closed.
6. Freshness policy is explicit and deterministic; future-dated evidence fails; unknown date precision is surfaced rather than invented.
7. Multiple differing observations for one metric are conflict-blocked until upstream reconciliation.
8. Proposal records exact observation hashes and is SHA-256 tamper-detecting.
9. CLI exposes build/validate only.
10. Web exposes `/binding` build/validate only and has no apply/Draft mutation/canonical-write route.
11. M1–M15 regressions remain unchanged.
12. Full Python 3.11/3.12 CI passes on the final PR head.
13. PR is merged only against the tested head SHA.
14. Post-merge `main` CI passes before Issue #34 is considered complete.
