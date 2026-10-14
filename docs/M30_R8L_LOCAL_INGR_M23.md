# M30-R8L — real user-local Ingredion M23 execution

## Purpose

Take the **actual approved** Ingredion R8 proof, a reviewed `cash`
`NORMALIZED_FACT`, and a reviewed exact SEC aggregate-debt context to build:

1. `draft-binding-proposal-v0.2-sec-aggregate-debt` (cash + interest-bearing debt);
2. `draft-binding-proposal-v0.3` (R6 dilution `ASSUMPTION`), reusing the exact
   existing R8 proof and source ancestry.

Both outputs are **noncanonical proposals**, not real Draft mutation, promotion
or admission.

## Local execution

On a clean user-local checkout containing M30-R8L:

```powershell
python -m valuation_hub.ingr_r8_m23_execution --json
```

Optional explicit input overrides:

```powershell
python -m valuation_hub.ingr_r8_m23_execution --repo-root C:\Valuation-Intelligence-Hub --artifact-root C:\Valuation-Intelligence-Hub\workspace --proof C:\Valuation-Intelligence-Hub\workspace\execution_artifacts\US_INGR_INGREDION\run_20261013T160243244215Z\r8_binding_proof.json --json
```

The runner checks the clean Git worktree, M30-R8 ancestry, and **independently
revalidates the complete R8 proof** (SHA
`8abc7cf93fd3e2bf93422e915ab4fe5c6ebad2faef34a0a2f7596038eda55cc9`).

It searches only existing local `workspace/**/*.json` for:

| Required source | Real SHA | Authority |
|---|---|---|
| M30-R3 AI-reviewed cash observation | `c4c7cc9768835cd4ada7129f1ca33d6f7cf9b08a795e08d0085639f90d4551ec` | `NORMALIZED_FACT`, USD 948m, Q2 2026 |
| SEC aggregate-debt binding context | `1339821cb11c66482cfcbff66838ea6bdd42d32ebabcd32927e6839e6fa1286a` | reviewed `DERIVED_FACT`, USD 1,783m |
| Alternative reviewed debt profile | `b5fb0cbaa9758b2d772452ce00e3d3139af9aef7dd6e6b35a38db85b031d36e3` | context is deterministically rebuilt, exact SHA required |

If the source files do not exist, status is `NEED_REAL_M23_SOURCE_ARTIFACTS`
with the exact missing SHA. An existing R8 proof cannot recreate historical
cash or debt evidence from hashes. If the exact sources are present but SEC
financial-scope claims differ, the runner fails closed as
`HOLD_FINANCIAL_SCOPE_RECONCILIATION_REQUIRED` instead.

Only after successful source and scope reconciliation can the runner write two noncanonical JSON
proposals under a new gitignored
`workspace/execution_artifacts/US_INGR_INGREDION/r8_m23_*/`
folder and returns their exact SHA lineage, preserving the selected
63,900,000 diluted shares as **`ASSUMPTION`**, not `DERIVED`.

## Confirmed real financial-scope blocker

The canonical SEC observation normalizer emits `financial_scope=AS_REPORTED`
for cash, and M22/R6 current shares are also `AS_REPORTED`. The separate
M30 reviewed SEC aggregate-debt contract explicitly emits
`financial_scope=CFS`.

**The scopes are not interchangeable without a governed bridge.** If the
exact reviewed cash and debt artifacts are found, the current runner
returns `HOLD_FINANCIAL_SCOPE_RECONCILIATION_REQUIRED` with:

- R6 diluted shares: `AS_REPORTED`
- SEC normalized cash: `AS_REPORTED`
- SEC reviewed aggregate debt: `CFS`

No M23 v0.2/v0.3 proposal may be emitted under this unresolved mismatch.
Next required work is an independently validated and source-bound
scope-reconciliation claim tying the cash and SEC aggregate debt to the same
Ingredion 2026 Q2 filing/statement boundary, preserving original source SHAs
and classes. Neither reinterpret a cash observation's scope nor silently
rewrite the debt context to claim identity.

## Explicit exclusion

A successful M23 proposal does **not** mean M24 WACC, M25 terminal-growth,
M26 six-field forecast, M27 market price, M28 noncontrolling-interest or M29
13/13 admission has been run on the real Ingredion case. Each remains an
independent governed step.
