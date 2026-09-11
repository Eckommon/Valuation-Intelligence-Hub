# M17 Acceptance / M17 완료조건

M17 is complete only when all conditions pass on the final PR head and again after merge to `main`.

1. Approval locks reviewer, timestamp, proposal SHA, Draft-before SHA, target identity/scope, and approved field set.
2. Proposal or Draft mutation invalidates approval.
3. Entity, financial-scope, or currency mismatch fails closed.
4. Only current `DIRECT_BIND` fields may be approved/applied.
5. Non-direct fields remain impossible to apply even if named explicitly.
6. Input Draft remains unchanged; output is a deterministic new JSON result.
7. Applied diffs contain exact before/after values and source observation SHA-256.
8. Result embeds proposal, approval, Draft before/after, unresolved matrix, and SHA locks.
9. Result remains `canonical=false` and resulting Draft passes existing Draft validation.
10. CLI/Web expose no filesystem Draft overwrite or canonical-write path.
11. Apply without a valid human approval fails closed.
12. M1–M16 regressions remain green.
13. Full Python 3.11/3.12 CI passes on final PR head.
14. Post-merge `main` CI passes before Issue #38 is complete.
