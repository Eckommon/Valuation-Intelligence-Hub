# Goal-driven delivery loop / 목표 중심 반복 실행 규약

## North star / 최종 기준

Deliver an auditable, reproducible and usable valuation system that explains value versus price, material business drivers, market-implied expectations, uncertainty, scenario returns and invalidation conditions. Select a model suited to the asset rather than forcing every asset into equity FCFF. Source of truth: `docs/FOUNDATION.md`.

**One real end-to-end case before another abstraction wave.** Ingredion is the initial real-equity acceptance case, not a benchmark where fake or stale market values may fill gaps. Afterwards demonstrate portability to a second issuer, a usable decision workflow, and at least one non-equity model adapter.

## Evidence-based gap assessment — 2026-10-27

| Goal gate | Repository evidence | Current classification | Necessary independent proof |
|---|---|---|---|
| Reproducible model kernels | `src/valuation_hub/core.py`, `scenario.py`, `reverse.py`, `venture.py`; three cases in `registry/cases.json` | CODE_IMPLEMENTED | Execute and reconcile a real contemporary valuation, scenarios and sensitivity |
| Provenance and authority boundaries | M1–M29 modules and tests; `docs/EVIDENCE_POLICY.md` | CODE_IMPLEMENTED | Independent original-source and calculation reconciliation |
| First actual complete governed company | `US_INGR_INGREDION` issue #66/#79; M24 user run | REAL_EVIDENCE_HOLD | 7/7 date-aligned source candidates, reviewed choices, full 13/13, admission and rerun |
| Working user-facing interface | `vih web` and preparation routes | IMPLEMENTED_UNVALIDATED | Manual E2E workflows, errors, user feedback, usable output |
| Reusable equity workflow | Issuer-specific M30-R8 path | UNPROVEN_GENERALIZATION | Second independent issuer without new hardcoded valuation path |
| Multi-asset valuation product | Venture probability model in equity case registry; no non-equity canonical adapter | NOT_YET_PROVEN | Non-equity adapter with asset-appropriate model and real evidence |

No completion percentage is inferred from number of files or test cases. The first real company is not in the canonical registry.

## One-loop protocol / 매 작업 반복

1. **Observe:** verify exact main SHA, merged/open PRs, Python 3.11/3.12 CI, latest original user execution, as-of date, evidence hashes, and current `governance/goal_delivery_plan.json`.
2. **Diagnose:** compare the north star against real acceptance gates. Rank risks by blocking importance, value to final product, evidence feasibility and cost. One critical-path blocker per iteration.
3. **Propose:** state the smallest causal change, rejected alternatives, expected user-visible outcome, acceptance criteria, regression risks, and required sources/permissions.
4. **Preflight:** verify the proposal actually removes or narrows that blocker, can be tested without false financial observations, respects original-source copyrights/private contact fields, and leaves authority boundaries intact.
5. **Implement:** scoped PR; no unrelated changes. Maintain deterministic fixtures and stable prior APIs or document migration.
6. **Verify:** exact-head unit/adversarial tests on Python 3.11/3.12; negative tests for false approval, fabricated rates, wrong as-of, path escapes, mismatched SHA. Check the product-level requirement, not only the local implementation.
7. **Release:** review files/CI, merge the exact tested head, confirm main contains the runnable module, check post-merge CI. Do not tell a Windows user to run a branch-only module.
8. **Observe real effect:** user-local data checks where original is gitignored; label missing execution as PENDING. Never upgrade 5/7 or a historical model merely because a new parser exists.
9. **Record and repeat:** prepend dated main SHA, proof, actual status, risk, next action, and owner to `PROJECT_STATE.md`; update the plan manifest. Stop or change priority if the original hypothesis fails.

A blocked provider call is evidence of a blocked provider call, not proof that the input is impossible or available. Bounded alternatives must be source-compatible; no anti-bot bypass, paid datasets without user authorization, fabricated market values, or silent post-as-of hindsight.

## Promotion and value-delivery gates / 통과 조건

| Gate | Pass standard | What does NOT pass |
|---|---|---|
| CODE | Feature on canonical main, exact-head and post-merge CI passing | Open PR or green branch CI alone |
| SOURCE | Original publisher bytes and parsed metric, identity, date, units, hash/proof validated | Snapshot URL/SHA without value reconciliation |
| METHOD | Point-in-time consistency, economic meaning, limitations and contradictory alternatives reviewed | A convenient quote, historical coupon or effective-tax headline |
| MODEL | All material inputs with explicit assumption authority, coherent scenario/sensitivity, reproduced output | Numeric WACC on missing evidence or unreviewed proxy |
| PRODUCT | User can reproduce, inspect and explain results including blockers | Route exists or synthetic API test passes |
| EXPANSION | Second issuer and non-equity path work without hidden issuer assumptions | More M-numbered implementation files |

A human decision is required before external binding side effects. Analytical decisions use evidence-first internal review subject to the existing authority policy; never manufacture a reviewer, signature, approval timestamp or canonical claim.

## Prioritized delivery sequence / 우선순위

- **P0 release hygiene:** merge/review tested offline source audit, verify module exists on main; obtain user's *separate* real local audit result. Until that local result arrives, mark LOCAL_RUN_PENDING.
- **P1 first real case:** source- and date-align `pre_tax_cost_of_debt` and marginal `tax_rate`; method challenge beta (price-only, R²≈0.071), retrospective ERP availability and 22bp RF convention; keep future Tate & Lyle financing separate from Sept-2026 as-reported debt.
- **P2 first accepted case:** terminal growth, coherent six-field annual forecast, full 13/13 governed Draft, independent scenario/sensitivity and reverse valuation, promotion/admission only after exact authority checks.
- **P3 usable product:** end-to-end CLI/Web functional acceptance for analysts; understandable economic explanations, safe errors, repeatable export, no private data leaks.
- **P4 portability:** second company of different profile with no hardcoded method path; document necessary generalization.
- **P5 breadth:** one truly non-equity real asset adapter selected by evidence/model suitability.

Do not advance to P5 because P1/P2 are difficult. Honest HOLD is better than artificial completion, but it should lead to a bounded next experiment rather than endless duplicate documentation.

## Mandatory iteration record / 반복 종료 기록

Every mission PR or follow-up record must provide:

- Objective and exact blocker; what changes for a real user
- Main baseline SHA, PR head SHA, exact CI URLs/status, merge SHA and post-merge CI
- Source availability and financial input truth level (synthetic/test, user-reported, verified, reviewed, canonical)
- Acceptance evidence, counterexamples, unresolved risks, rollback/fail-closed result
- Next single highest-priority mission, owner, external dependencies and STOP condition

**Run:** `python -m valuation_hub.goal_delivery_check --json` from an installed repo or `PYTHONPATH=src python -m valuation_hub.goal_delivery_check --json`. This validates the stored plan's structure and code references; it explicitly does **not** verify real market source bytes, approve a valuation or complete the project.
