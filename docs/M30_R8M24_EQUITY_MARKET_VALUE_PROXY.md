# M30-R8M24-EQV — 2026-09-14 INGR equity market value source proxy

## Verified dated public facts

- NYSE:INGR 2026-09-14 **unadjusted daily CLOSE $98.63 USD**:
  https://stockanalysis.com/stocks/ingr/history/
  Independent crosscheck: https://ca.finance.yahoo.com/quote/INGR/history/
- SEC Q2 Form 10-Q, explicitly **63,063,979 shares outstanding on 2026-08-05**:
  https://www.sec.gov/Archives/edgar/data/1046257/000162828026054722/ingr-20260630.htm
  This user's original immutable SEC Tier A external snapshot SHA:
  `f61f33b0e27403ab56882d8cc1daa3a66571e9452fc5d8012268f39ab098b0f9`.
- Historical reported shares are **40 days older** than valuation as-of 2026-09-14.

The mechanical product is **$6,220,000,248.77**. It is a *lagged-common-shares
ASSUMPTION market-capitalization proxy*, not a September 14 equity MV FACT.
Never substitute the separate 63,900,000 diluted-share R6 ASSUMPTION or
historical weighted-average shares for common shares outstanding.

## User-local offline original source capture after canonical merge

PowerShell from clean C:\Valuation-Intelligence-Hub:

    git status --short
    git fetch origin main
    git switch main
    git pull --ff-only origin main
    $price = 'workspace\source_snapshots\INGR_history_price_20260914.html'
    curl.exe --fail --location --compressed 'https://stockanalysis.com/stocks/ingr/history/' --output $price
    $sec = 'workspace\source_snapshots\INGR_2026Q2_10Q_dilution_snapshot_20260914.json'
    python -m valuation_hub.ingr_wacc_equity_market_value --price-raw $price --sec-snapshot $sec --json
    python -m valuation_hub.ingr_r8_m24_readiness --json

Only if a readable historical table contains unique Date 2026-09-14 and
unadjusted Close 98.63 can the importer proceed. Adjusted Close, adjacent
dates or a current-day quote cannot be substituted. The exact SEC snapshot
must independently validate issuer/CIK, filed cover August 5 share count,
Q2 filing identity, raw body and source SHA.

If the price HTML is dynamically rendered or no historical table is
contained in the downloaded original, this importer **fails closed**;
an alternate independently documented price data adapter would be needed.

One WACC source-input record with metric equity_market_value, USD,
observed-on 2026-09-14, claim_class ASSUMPTION, Tier B price source
and an extra source-bound market-cap proxy proof are written to gitignored
workspace/source_snapshots. The proof includes both original source SHA
references and an explicit 40-day temporal gap.

Updated M24 readiness **rejects price-only market cap** and separately
validates the price and SEC snapshot against the method proof. If both
capture steps genuinely pass, WACC readiness can move 1/7 → 2/7 source
input candidates, but market cap remains an **unreviewed ASSUMPTION**.
Investor/reviewer still must decide whether to accept 40-day share-count
carryforward, or obtain a better as-of common-share count, before any
reviewed WACC candidate/package or Draft bind.

No real-market artifacts, fabricated reviewer, approval or registry
admission are embedded in this PR.