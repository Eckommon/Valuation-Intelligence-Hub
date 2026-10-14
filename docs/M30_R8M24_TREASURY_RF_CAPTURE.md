# M30-R8M24-RF — dated US Treasury 10-year source intake

## Real reference

Official U.S. Treasury nominal par yield curve dated September 14, 2026:
https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?field_tdr_date_value_month=202609&type=daily_treasury_yield_curve

Exactly Date=09/14/2026 and column 10 YR = 4.97%,
so the WACC source candidate is decimal 0.0497.
Independent Federal Reserve H.15/FRED confirmation:
https://fred.stlouisfed.org/series/DGS10

## Offline user-local intake (after canonical code promotion)

Run in PowerShell from the clean local repository:

    git fetch origin main
    git switch main
    git pull --ff-only origin main
    $raw = 'workspace\source_snapshots\UST_daily_nominal_202609.html'
    curl.exe --fail --location --compressed 'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?field_tdr_date_value_month=202609&type=daily_treasury_yield_curve' --output $raw
    python -m valuation_hub.ingr_wacc_treasury_source --raw $raw --json
    python -m valuation_hub.ingr_r8_m24_readiness --json

The importer accepts already captured UTF-8 HTML or downloaded official CSV.
It rejects missing/multiple September 14 rows, wrong maturity columns,
incorrect value, corrupted/untrusted input, and any inaccessible source.
Exact header, date, original cell and immutable snapshot SHA are required.

## Authority and results

Only a source-level FACT candidate for risk_free_rate is created.
The original raw bytes stay under gitignored workspace/source_snapshots.
The date-and-column proof and snapshot plus WACC input are written
separately to gitignored workspace; no real-source SHA is invented.
No automatic reviewer, reviewed WACC package, v0.4 Draft or admission.
When valid this may move local readiness from 0/7 to 1/7 candidates.

Remaining ERP, levered beta, marginal debt cost, market-valued equity
and debt and appropriate valuation tax rate all require separate
evidence and method decisions. INGR 2026-09-14 stock close is USD 98.63,
but translating that to capital-weight equity MV needs dated share count.
The 63.9m R6 diluted share ASSUMPTION is not common shares outstanding FACT.
Historical 2026H1 effective tax 29.5% is not automatically marginal WACC tax.

Issues #138 and #140 continue to track real evidence and human review.