# M30-R8M24-RD.1 — source-bound senior-note inventory (not a yield)

## What real SEC documents do, and do not, establish

The user's original Ingredion (CIK 0001046257) 2026-Q2 SEC 10-Q
filing was available as-of 2026-09-14 and has been validated from
**actual user-local bytes** already in the separate debt-market-value
slice, original body SHA-256:

`bb03a79c2ab289873e5cfe6cc299ba52d9659dda5594d224b6dce844a6bbf167`

The SEC Note 6 *reported carrying amounts*, USD millions, are:

| Fixed notes | Maturity | 2026-06-30 carrying | 2025-12-31 carrying |
|---|---|---:|---:|
| 2.900% | 2030-06-01 | 597 | 597 |
| 3.200% | 2026-10-01 | 500 | 499 |
| 3.900% | 2050-06-01 | 392 | 392 |
| 6.625% | 2037-04-15 | 253 | 253 |
| **Long-term debt** | | **1,742** | **1,742** |
| Short-term debt | | 41 | 48 |
| **Total carrying debt** | | **1,783** | **1,790** |

The 3.2% note is due in October 2026 but was reported as
*long-term* due to the issuer's explicit intent and ability to
refinance it on a long-term basis. June 30 pending Tate & Lyle
acquisition **Bridge and DDTL facilities were undrawn** and are
excluded from June 30 funded debt.

The accounting carrying amounts are **not verified face principal**,
and the four coupons are historical contractual coupon rates, **not
2026-09-14 forward market yields**. SEC Note 5 reports a single
**$1,640m aggregate** long-term debt fair value based on Level-2
dealer quotes, NOT four individual bond quotes. A homogeneous YTM
cannot be inferred uniquely from the total fair value: four maturity
points, principal amortization, accrued interest and acquisition
financing can change forward cost of debt materially.

Thus RD.1 produces a **context-only** method proof with
`pretax_debt_rate_selected=null` and
`wacc_debt_input_created=false`.
It **cannot** raise the WACC readiness for
`pre_tax_cost_of_debt`.

Primary official source:
https://www.sec.gov/Archives/edgar/data/1046257/000162828026054722/ingr-20260630.htm

## Execute using the **already existing local original snapshot**

On a clean, up-to-date main branch in PowerShell:

```powershell
git switch main
git pull --ff-only origin main
$source = 'workspace\source_snapshots\INGR_Q2_debt_market_value_bb03a79c2ab28987_snapshot.json'
python -m valuation_hub.ingr_wacc_debt_bond_terms --snapshot $source --json
python -m valuation_hub.ingr_r8_m24_readiness --json
```


No SEC user-agent, new paid service, new data download or identifying
information is required to use the previously captured and SHA-locked
source; do not delete or reformat it. The tool validates its official
SEC URL/source tier and **exact previously verified raw body SHA** and
parses the full Note 6 from the immutable raw snapshot. It writes only
one gitignored proof JSON, never another debt-rate source input.

## Next work: issuer market yields / 전진형 시장수익률

To use this inventory in a true **forward** debt cost, acquire
market-price/YTM evidence from 2026-09-14 or earlier, e.g. dated
FINRA/TRACE transactions for INGR's four notes. For each quote,
require issuer identifier, CUSIP/ISIN, coupon frequency, principal
rather than book carrying, maturity, trade/settlement date, price
(clean/dirty distinction), accrued interest, day count and yield
calculation. Weighting must be by chosen market value and tenor
policy, and separately analyze near-term October 2026 refinancing
and undrawn acquisition financing. Dated coupon averages, debt
discount ratios, or January 2026 sector pretax cost 5.07% cannot
silently serve as a September 14 issuer-specific forward borrowing
yield.

The unresolved WACC source fields remain
`levered_beta` (new beta original-price importer in #160,
pending user original CSV), `pre_tax_cost_of_debt` and
`tax_rate`. No WACC approval, Draft, 13/13 handoff or
canonical real Ingredion case is claimed.
