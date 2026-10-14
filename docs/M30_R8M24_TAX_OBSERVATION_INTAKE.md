# M30-R8M24-TAX.1 — source-bound tax observations, not WACC tax approval

## Official source

SEC 8-K accession 0001628280-26-052104, filed **2026-08-04**,
Exhibit 99 (Ingredion 2026-Q2 earnings release):
https://www.sec.gov/Archives/edgar/data/1046257/000162828026052104/ingr-20260630xexx99.htm

The source predates the **2026-09-14** real Ingredion valuation as-of.

The release distinguishes these four tax-rate classes:

| Class | Period / semantics | Published value |
|---|---|---|
| GAAP effective tax rate | Q2 2026 actual | 33.7% |
| Adjusted non-GAAP effective tax rate | Q2 2026 adjusted actual | 27.2% |
| GAAP effective tax rate guidance | Full-year 2026 expected | 27.4%–28.9% |
| Adjusted non-GAAP effective tax rate guidance | Full-year 2026 expected | 26.0%–27.5% |

The GAAP Q2 ETR was affected by the Pakistan divestiture and
Mexican-peso movement. Management's annual guidance excludes certain
acquisition integration and restructuring costs. A non-GAAP adjusted
ETR is **not, by itself, a marginal statutory/cash tax rate applied to
new incremental interest expense**.

As a result TAX.1 **must not** generate any M24
wacc-source-input-v0.1 for tax_rate. It creates a separately SHA-bound
context/evidence proof with
HOLD_WACC_MARGINAL_TAX_METHODOLOGY_NOT_EVIDENCED.

## Windows local original-source capture

From clean canonical main after merge, with valid identifying
SEC_USER_AGENT set privately as required by Issue #79:

```powershell
git switch main
git pull --ff-only origin main
if (-not $env:SEC_USER_AGENT) { throw 'Set SEC_USER_AGENT in the local runtime, not CLI arguments' }
$raw = 'workspace\source_snapshots\INGR_2026Q2_SEC_8K_EX99_original.html'
Invoke-WebRequest -Uri 'https://www.sec.gov/Archives/edgar/data/1046257/000162828026052104/ingr-20260630xexx99.htm' -Headers @{ 'User-Agent' = $env:SEC_USER_AGENT } -OutFile $raw
python -m valuation_hub.ingr_wacc_tax_evidence --raw $raw --json
python -m valuation_hub.ingr_r8_m24_readiness --json
```


The original HTML must remain unmodified. The importer refuses
unexpected values, duplicated claims, missing source rationale,
post-dated/nonmatching URL, or already captured raw bytes. This
creates only two noncanonical files under gitignored workspace:
an immutable source snapshot and source-derived tax method proof.

A standalone 26%, 27%, 27.5%, company ETR, US statutory 21% or
arbitrarily selected range midpoint **must never** silently become
scenario.wacc tax. Subsequent selection of an appropriate marginal
rate requires source-bound jurisdiction/income mix, deductibility,
forward tax regime, reviewable dated method and explicit scenario
policy. The remaining levered beta and forward pre-tax debt cost
are separate HOLD inputs. All seven M24 inputs plus approvals are
required before Draft v0.4 or case admission.
