# M30-R8M24-BETA.Y — alternate Yahoo v8 original chart JSON

## 2026-10-16 actual provider failure / 실증 장애

The user's real Stooq INGR.US and ^SPX downloads returned
DOCTYPE HTML with a JavaScript browser verification challenge,
not CSV. The existing importer correctly failed with an OHLCV
CSV-header mismatch. Do not run CAPTCHA/proof-of-work solvers,
relabel HTML as CSV, or fabricate any prices. Actual WACC
source readiness remains 4/7.

Yahoo Finance chart v8 daily JSON is an alternate **unofficial**
publicly accessible API (availability, rate limits and licensing
may change). It is a DIFFERENT provider with independent original
source SHA and JSON-specific checks. The two fixed URL endpoints
below cover 2023-09-14 through 2026-09-14 inclusive:

INGR:
https://query1.finance.yahoo.com/v8/finance/chart/INGR?period1=1694649600&period2=1789430400&interval=1d

S&P500 price-only index ^GSPC:
https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?period1=1694649600&period2=1789430400&interval=1d

The adapter requires exact USD INGR and ^GSPC identities,
unaltered provider JSON, 500+ daily original closes per source,
125+ common-week returns, proper valuation-date 2026-09-14
last close, unique UTC dates, reconstruction of OLS slope/alpha/R²,
SHA-locked two source snapshots and original return-pair trace.
HTML/captcha/auth/rate errors, stale/future/duplicated/missing
data and insufficient observations fail closed.

**Price-only historical closes are not cash-dividend-adjusted total
returns.** Yahoo's retrospective data/metadata do not prove
historical availability as-of Sep 14 or the corporate-action
adjustment convention. Company CAPM beta is an unreviewed
ASSUMPTION, not a verified final WACC.

## Local original capture (PowerShell)

After CI-approved PR merge and git pull:

~~~powershell
git switch main
git pull --ff-only origin main
$dir = 'workspace\source_snapshots'
$ingr = Join-Path $dir 'INGR_yahoo_v8_20230914_20260914_original.json'
$spx = Join-Path $dir 'GSPC_yahoo_v8_20230914_20260914_original.json'
$headers = @{ 'User-Agent' = 'Valuation-Intelligence-Hub research/1.0'; 'Accept' = 'application/json' }
if (!(Test-Path $ingr)) {
    Invoke-WebRequest -Uri 'https://query1.finance.yahoo.com/v8/finance/chart/INGR?period1=1694649600&period2=1789430400&interval=1d' -Headers $headers -OutFile $ingr -ErrorAction Stop
}
if (!(Test-Path $spx)) {
    Invoke-WebRequest -Uri 'https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?period1=1694649600&period2=1789430400&interval=1d' -Headers $headers -OutFile $spx -ErrorAction Stop
}
Get-Content $ingr -TotalCount 1
Get-Content $spx -TotalCount 1
python -m valuation_hub.ingr_wacc_yahoo_chart_beta --issuer $ingr --market $spx --json
python -m valuation_hub.ingr_r8_m24_readiness --json
~~~

If Yahoo returns 401, 429, HTML or unavailable daily history,
stop, preserve the actual error and do not upgrade readiness.
Do not buy any service or share credentials. Stooq HTML can
remain under its original Stooq filename; this importer uses
only the distinct Yahoo JSON filenames and never overwrites it.

A real success may move 4/7 to at most 5/7 unreviewed source
candidates. Distinct Stooq/Yahoo beta values simultaneously
imported must cause conflicting-input HOLD until reviewed.
Forward issuer bond yield and WACC marginal tax are still missing;
2026Q2 SEC bond schedule and historic coupons are not YTM.
