# Agent execution contract — Valuation-Intelligence-Hub

This repository's goal is NOT the number of modules, milestones, or passing tests. It is a reproducible, decision-useful valuation system that separates price from economic value across appropriate asset classes. Public equity is the first end-to-end proof, not the final scope.

## Required grounding at every continuation

1. Read `docs/FOUNDATION.md`, `docs/AI_GROUNDING_POLICY.md`, `docs/GOAL_DELIVERY_LOOP.md`, `governance/goal_delivery_plan.json`, and the newest top section of `PROJECT_STATE.md`.
2. Verify the live default-branch HEAD, working tree, outstanding PRs, exact CI results, and any user-local execution feedback. The repository outranks chat memory; local gitignored bytes are not available through GitHub.
3. Distinguish **implemented capability**, **CI on synthetic fixtures**, **user-reported original-source observation**, **independently verified inputs**, **reviewed model**, **canonical real case**, and **user-validated product**. Never collapse these statuses.
4. Choose ONE top-priority real goal blocker. Record a falsifiable hypothesis, smallest useful slice, acceptance/rejection conditions, expected evidence, and rollback/fail-closed behavior BEFORE implementation.
5. Prefer reuse, deletion of avoidable complexity, and real-case progress to additional governance layers. Avoid issuer-specific hardcoding in general engines; historical exact-SHA replay helpers may be issuer-specific if labeled.
6. Implement on a scoped branch and PR; test both Python 3.11 and 3.12 on the exact PR head. Review diff and tests; merge only after both pass, then verify merge HEAD and post-merge CI. A PR left open is **not installed** on `main`.
7. Recheck end-to-end outcome using REAL, time-aligned, source-locked data where applicable. CI proves code behavior, not source availability or valuation truth. Record the current validated limit and the next priority in `PROJECT_STATE.md` and `governance/goal_delivery_plan.json`.
8. If an input is blocked by paywalls, publisher access, private local data, or incomplete evidence, HOLD that input, record a bounded alternative, and advance only work whose evidence exists. Never bypass publisher challenges or invent data.
9. Stop for monetary spending, trades, contractual or legal/regulatory submissions, credentials/permissions, or other external binding acts without user authorization. Do not disclose a real SEC User-Agent email or licensed original data.

## Current critical path

First complete ONE genuine Ingredion `US_INGR_INGREDION` as-of 2026-09-14 end-to-end equity-FCFF case, with credible WACC, 13/13 governed fields, risk/sensitivity, independent rerun, and guarded admission. User's latest actual readiness is **5/7 unreviewed WACC source candidates**; cost of debt and marginal tax rate are missing. No reviewed WACC, full Draft, or canonical Ingredion case may be claimed. Afterward test a second issuer without bespoke code, validate user-facing workflow, then implement a genuine non-equity adapter.

The project-loop contract is a workflow guide and testable plan, **not an approval or a replacement for financial evidence**. If the plan is stale, update it with independent proof; never coerce evidence to fit the plan.
