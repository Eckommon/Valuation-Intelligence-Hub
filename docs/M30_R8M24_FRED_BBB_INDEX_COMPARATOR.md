# M30-R8M24-RD.3 — FRED/ICE BBB yield as comparator ONLY / 시장 비교지표

## Source semantics / 출처 범위

Official Federal Reserve Bank of St. Louis FRED licensed
**ICE BofA BBB US Corporate Index Effective Yield**, series
**BAMLC0A4CBBBEY**, percent per annum, daily close:
https://fred.stlouisfed.org/data/BAMLC0A4CBBBEY

The official historical table reports **2026-09-14: 5.90%**
and preceding trading day **2026-09-11: 5.89%**. This is a
U.S. dollar denominated **BBB rated corporate bond index effective
yield**, NOT Ingredion's individual bond quote, outstanding credit
rating, bond-funding refinancing cost or tenor-weighted issuer
borrowing yield. September 14 index *observation* does not prove
the precise FRED public posting/release time on September 14.

**License boundary:** ICE BofA index data published on FRED
are proprietary ICE data subject to internal-use-only restrictions.
DO NOT commit, publish, email, embed or redistribute downloaded
original HTML and daily series to public GitHub, docs, CI artifacts,
or otherwise. Keep exact original HTML solely under user-local
gitignored source_snapshots. Test data are **synthetic**, not index
redistribution. Comply with source terms before non-internal
commercial usage.

A genuine as-of issuer cost of debt additionally requires
actual date-scoped individual issuer market prices/YTMs and
CUSIP/ISIN, or a **governed explicitly assumed** term+credit
proxy with source-proven rating or historical interest coverage
and maturity/amount weighting. This benchmark must NOT be
automatic `pre_tax_cost_of_debt` (or 6/7 input), because
Ingredion's credit rating and its four outstanding 2026/2030/
2037/2050 maturities are not proven to match the BBB index's
duration/risk. The impending October 2026 refinancing requires
independent market rate and capital-structure policy.

## Local capture / 로컬 실증

After CI green and merged main, on user Windows PowerShell:

~~~powershell
cd C:\Valuation-Intelligence-Hub
git switch main
git pull --ff-only origin main
$raw = 'workspace\source_snapshots\FRED_ICE_BBB_20260914_original.html'
if (!(Test-Path $raw)) {
  Invoke-WebRequest -Uri 'https://fred.stlouisfed.org/data/BAMLC0A4CBBBEY' -OutFile $raw -ErrorAction Stop
}
python -m valuation_hub.ingr_wacc_fred_bbb_comparator --raw $raw --json
python -m valuation_hub.ingr_r8_m24_readiness --json
~~~

If FRED blocks download, source layout changes, as-of date is
missing, numerical index observation contradicts the expected
value, or HTML is otherwise unverified, the importer refuses
source proof. **Do not edit FRED original, inject hardcoded values,
evade authentication, or reinterpret 5.90% as an INGR quote.**
If identical data were previously captured, do not overwrite them.

## Actual source status / 현재 실기업 상태

Most recent actual user Windows run validated 2025 SEC original
tax bridge from original body SHA-256
`f932b04e0bf99ad80ea19326b724d553368cac6c6dad2ab64c1512154cd1aa1b`,
snapshot SHA
`eb36a3dfede4b45e040dfcc5ae4b7e55caeb6b2a9cde6e3135dbcab6d52b6d08`,
tax method SHA
`c3d83e6a3c59236b1a18c1fc5cd3fa513605d6de0cf0c81c6131c291593a5594`.
Historical federal statutory 21.0%, global ETR 24.4%;
no 2026-09-14 WACC marginal cash tax selected.

Last actual M24 readiness **5/7**, missing issuer forward
`pre_tax_cost_of_debt` and marginal `tax_rate`, WACC HOLD.
The beta is 157-week INGR/^GSPC price-only OLS 0.34223 with
R² 0.07068 (not a total-return β; historical availability
unproven); September implied ERP is sourced retrospectively
from NYU October publication. No WACC approved, Draft,
13/13 or canonical real INGR case.
