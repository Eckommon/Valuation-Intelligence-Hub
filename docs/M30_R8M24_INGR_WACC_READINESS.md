# M30-R8M24 — real Ingredion WACC source readiness after proven M23

## Real accepted anchor

User-local command `python -m valuation_hub.ingr_r8_m23_execution --json` returned
`REAL_INGR_M23_R6_ASSUMPTION_READY` on `main@9c6558c66898d4f342741fc25901e2b5899941ff`.

- M23 scoped SEC debt v0.2 SHA: `42b8d691a3617235d52179bb56340ba0a7f2fca055a8b608f8eda5c44eb6d378`
- M23 R6 v0.3 SHA: `5017a832d68f7a013829f4bc86679f0bcd8f40480f6954bd4443e6ae6400c472`
- SEC scope bridge SHA: `f0d711a4faa4947603b4e41e200915e0ac029147dfd8ee7c2a12ad45e2463f13`
- 63,900,000 shares class **ASSUMPTION**.

The M23 bytes are **local**, not reconstructed from the reported SHA.

## Source inventory / fail-closed next gate

A governed reviewed WACC assumption must incorporate **exactly seven**
as-of `2026-09-14` source components:

| Metric | Required unit | Max days old |
|---|---|---:|
| `risk_free_rate` | decimal | 30 |
| `equity_risk_premium` | decimal | 90 |
| `levered_beta` | ratio | 180 |
| `pre_tax_cost_of_debt` | decimal | 180 |
| `equity_market_value` | USD | 30 |
| `debt_market_value` | USD | 550 |
| `tax_rate` | decimal | 550 |

The source-input schema requires observed-on date, claim class, publisher,
source type, Tier A/B/C, locator, source SHA, and correctly typed units.
The M24 human-reviewed package also requires an explicit real reviewer,
approval timestamp, review basis, full CAPM/market-capital-weight calculation
and exact scenario set. There is **no generic default** for any of these.

Current M24 readiness preflight:

```powershell
git status --short
git fetch origin main
git switch main
git pull --ff-only origin main
python -m valuation_hub.ingr_r8_m24_readiness --json
```

It validates the **actual** source-embedded M23 v0.3 and exact v0.2 ancestor
before inspecting user-local `workspace/**/*.json` for typed M24 source inputs
and supporting immutable snapshots. It reports missing, conflicting, stale,
future-dated, Tier D, unsigned source bytes and other fail-closed gaps in
a deterministic seven-row evidence inventory. It writes a noncanonical
`wacc_source_readiness.json` under a timestamped gitignored output folder.

An authenticated source SHA and locator establish provenance **only**.
They do not by themselves attest the numeric risk-free rate, CAPM premium,
beta, or tax treatment. The preflight **never** invents a value, builds
a human approval, finalizes a reviewed WACC, or applies the v0.4 Draft binding.
Even when all seven source-input candidates are present and fresh, its
strongest status is `REAL_INGR_M24_WACC_SOURCE_CANDIDATES_READY_FOR_REVIEW`,
with `human_review_completed=false` and `draft_v04_created=false`.

This code does not fetch new public or paid market data and does not authorize
the M29 case or any financial recommendation.
