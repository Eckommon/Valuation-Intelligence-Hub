# M30-R8M24-BETA — two original sources; INGR price-return beta

## 2026-09-14 historical-data contract / 2026-09-14 자료계약

The actual Ingredion (SEC CIK 0001046257) WACC readiness is **4/7**.
The two unresolved numeric inputs are levered beta and forward pre-tax
debt cost; WACC marginal-tax method is a third unresolved input.

This implementation takes original Stooq daily **INGR.US** equity and
**^SPX** S&P 500 price-index OHLCV CSV (2023-09-14 through 2026-09-14),
retains the original bytes in immutable local Tier B snapshots, and
computes an explicitly unreviewed **price-return beta**:

- Pair common trading days; choose the *last common close* in each
  ISO week; require >=125 synchronized weekly returns and >=500 daily
  bars for each instrument.
- Weekly simple returns, OLS with an intercept:
  \`beta = sum((R_spx-mean_spx)*(R_ingr-mean_ingr)) /
  sum((R_spx-mean_spx)^2)\`.
- Preserve first/last observation, count, alpha, R², return-pair SHA
  and both independent source body/snapshot/input/proof SHAs.
- Reject post-as-of data, stale/missing final date, invalid/duplicate
  bars, out-of-window data, gaps >10 days, implausible extreme weekly
  moves, nonsensical prices, degenerate volatility, source mismatches.
- WACC \`levered_beta\` input is an **ASSUMPTION** only, never FACT,
  never a reviewed issuer CAPM rate or Draft binding.

**Critical methodology caveat**: Stooq closes and \`^SPX\` are
**price-only**, *not total returns*: INGR cash dividends are not
included. Retrospective downloads do not establish price
adjustment as it was known as of 2026-09-14. Later corporate-action
revisions, index weighting, stale market close, pricing licenses and
survivorship must be reviewed. The resulting beta is a reproducible
proxy, not automatically accepted as the final company-specific beta.
\`historical_adjustment_basis_verified=false\` and
\`historical_source_availability_asof_proven=false\` remain explicit.

## Source URLs and Windows local download / 원본 다운로드

Public Stooq daily CSV retrieval endpoints:
- INGR.US:
  https://stooq.com/q/d/l/?s=ingr.us&i=d&d1=20230914&d2=20260914
- ^SPX:
  https://stooq.com/q/d/l/?s=%5Espx&i=d&d1=20230914&d2=20260914

Stooq may require an API key/CAPTCHA or return an HTML rate-limit
page. Do not store such a key in this repo, pass it to the importer,
or silently treat HTML/errors as CSV. If the site requires credentials,
download the date-filtered daily **original CSVs using its website UI**
to the same local paths. Do not fabricate data or use synthetic test CSV.

From an up-to-date, clean local PowerShell main:

```powershell
git switch main
git pull --ff-only origin main
$dir = 'workspace\source_snapshots'
$ingr = Join-Path $dir 'INGR_US_20230914_20260914_stooq_original.csv'
$spx = Join-Path $dir 'SPX_20230914_20260914_stooq_original.csv'

if (!(Test-Path $ingr)) {
    Invoke-WebRequest -Uri 'https://stooq.com/q/d/l/?s=ingr.us&i=d&d1=20230914&d2=20260914' -OutFile $ingr -ErrorAction Stop
}
if (!(Test-Path $spx)) {
    Invoke-WebRequest -Uri 'https://stooq.com/q/d/l/?s=%5Espx&i=d&d1=20230914&d2=20260914' -OutFile $spx -ErrorAction Stop
}
Get-Content $ingr -TotalCount 2
Get-Content $spx -TotalCount 2
python -m valuation_hub.ingr_wacc_levered_beta --issuer $ingr --market $spx --json
python -m valuation_hub.ingr_r8_m24_readiness --json
```


If the site's CSV requires a logged-in download, manually save
the raw CSV under those filenames, without editing it or hiding the
ticker/date restrictions. This importer reads only, does not
perform network access and never stores any provider key.

The input locator is the declared date-scoped Stooq endpoint; the
two CSV bodies alone do not cryptographically attest that Stooq
authored them or their precise public availability on Sep 14. Do not
represent an unreviewed CSV as primary SEC data. The importer
fail-closes on any mismatched structure or discontinuities.
Potential readiness goes 4/7→**5/7** only after the user's actual
original-source run and separate source/semantic review.

## Industry comparison, not a company beta or debt cost

NYU Stern Aswath Damodaran **January 2026** Food Processing US:
78 firms; average levered beta **0.61**, unlevered 0.46,
industry D/E 43.73%, and industry pre-tax debt cost **5.07%**.
Official originals:
https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/Betas.html
https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/wacc.html

These are **industry references, not Ingredion values** and
the January 2026 beta is stale by the M24 180-day rule as of
2026-09-14. They never constitute beta proof, loan yields,
marginal tax, reviewed WACC, or an increment in real readiness.
Separate #154 follow-on should source Ingredion instrument-specific
forward market yields (not historic weighted-average coupon).
Keep original real 4/7 status until actual local evidence arrives.
