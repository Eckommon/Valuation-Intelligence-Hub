# M30-R8M24-RD.4 — Fitch primary BBB issuer rating source

The 2026-09-14 valuation-as-of precedes the announced Tate & Lyle
acquisition, expected to close in the second half of 2027. Distinguish
the actual 2026 funded debt from forecast 2027 additional financing.

On **June 8, 2026**, official rating agency Fitch affirmed
Ingredion Incorporated's **BBB** long-term issuer default rating
and **BBB** senior unsecured long-term rating with Stable outlook
and short-term **F2**. It also described approximately
USD **4.4 billion** of *future incremental acquisition financing*,
not outstanding funded debt at 2026-06-30.

Official first-party source:
https://www.fitchratings.com/research/corporate-finance/fitch-affirms-ingredion-incorporated-idr-at-bbb-outlook-stable-08-06-2026

Independent S&P June 8, 2026 research also stated Ingredion's
senior unsecured rating was BBB, matching issuer credit rating:
https://www.spglobal.com/ratings/en/regulatory/article/-/view/type/HTML/id/3576456
However **S&P original is not captured or SHA-attested by RD.4**.
Do not substitute S&P marketing snippet for a local Fitch original
and do not claim S&P independent proof in the method JSON.

The official Federal Reserve Bank of St. Louis FRED/ICE U.S. BBB
corporate effective yield series **BAMLC0A4CBBBEY** observed on
September 14, 2026 is **5.90%**. See separate
[RD.3](M30_R8M24_FRED_BBB_INDEX_COMPARATOR.md).
Issuer rating BBB *matches index class*, but this does
**not** verify each Ingredion note's price/YTM, 2026 short
maturity refinancing, term, liquidity, rating outlook/future
acquisition leverage or after-tax cost.

## Original-source local capture — no password/paid source assumption

After tested PR merge and local latest main:

~~~powershell
cd C:\Valuation-Intelligence-Hub
git switch main
git pull --ff-only origin main
$raw = 'workspace\source_snapshots\INGR_Fitch_BBB_20260608_original.html'
if (!(Test-Path $raw)) {
  Invoke-WebRequest -Uri 'https://www.fitchratings.com/research/corporate-finance/fitch-affirms-ingredion-incorporated-idr-at-bbb-outlook-stable-08-06-2026' -OutFile $raw -ErrorAction Stop
}
python -m valuation_hub.ingr_wacc_fitch_rating --raw $raw --json
python -m valuation_hub.ingr_r8_m24_readiness --json
~~~

If Fitch requires login, blocks automated requests, or returns
a web challenge, **do not bypass it**. Local saved permitted
original HTML is acceptable if provenance can be verified.
The offline importer verifies the issuer, June 8 rating action,
short/long/senior grades, Stable outlook, future 2027 acquisition
context, official URL and original bytes/source SHA, then
stores original snapshot+method proof solely in ignored
user-local files. Tests include ONLY synthetic excerpt fixtures;
never commit licensed rating research or market index history.

The method is evidence-only and intentionally emits
`wacc_debt_source_input_created=false`,
`issued_refinancing_20260914_market_yield_observed=false`,
`human_review_completed=false` and retains status HOLD.

## Next valuation step

To advance from the actual **5/7**, source-lock the *actual*
Fitch BBB primary (and preferably independent S&P original),
licensed FRED BBB benchmark, and existing SEC Q2 4-note
schedule; compare 2026-09-14 funding tenor and 2026
refinancing and explicitly govern any index-based **ASSUMPTION**.
A rating and index-class match alone is **not an observed
company bond trading yield**. Don't infer individual bond
prices or a weighted maturity YTM by dividing the $1.640bn
aggregate Level2 estimated fair value across four notes.
Full pre-tax debt cost can only become source candidate after
the source-attested method, cash-flow/maturity policy and
review boundaries are established.

FY2025 SEC 10-K tax bridge user-local original verified; WACC
marginal tax still unselected under international deductibility
and US §163(j) conditions. ERP historical source availability
and Yahoo beta low explanatory power issues remain open.
