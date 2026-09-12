# M20 Acceptance / M20 완료조건

M20 is complete only when every item below is demonstrated by tests and final Python 3.11/3.12 CI.

1. Existing M16 `draft-binding-proposal-v0.1` behavior remains regression-compatible.
2. Existing cash `DIRECT_BIND` and cash-only M17 approval/apply remain regression-compatible.
3. Complete reviewed M19 debt with a fresh `EXACT` period end can become `equity.debt = DIRECT_BIND`.
4. `REPORT_STAGE_ONLY` debt cannot resolve freshness without a SHA-locked human `debt-date-assertion-v0.1`.
5. A date assertion locks reviewer, approval time, source debt SHA, entity/scope, source period, asserted end date, and review basis.
6. Source debt or assertion mutation fails validation.
7. `PARTIAL_COMPONENTS`, `CONFLICT_BLOCKED`, and `DERIVED_FACT_CANDIDATE` cannot enter a binding-ready debt context.
8. Stale complete reviewed debt becomes `STALE_BLOCKED`, not `DIRECT_BIND`.
9. Entity, financial scope, or monetary-unit mismatch between financial observations and debt context fails closed.
10. `draft-binding-proposal-v0.2` embeds and validates the full debt binding context and base v0.1 proposal.
11. M20 changes only the `equity.debt` classification relative to the embedded v0.1 proposal.
12. M17 can explicitly approve/apply `equity.debt`, preserving context/debt/date-assertion lineage.
13. Input Draft remains unchanged and result remains `canonical=false`.
14. CLI/Web provide calculate/validate/preparation only; no Draft-file or canonical write route exists.
15. All M1–M19 regressions remain green.
16. Final PR and post-merge main Python 3.11/3.12 CI complete `success`.
