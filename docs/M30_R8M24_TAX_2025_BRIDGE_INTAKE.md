# M30-R8M24-TAX.2 — Ingredion FY2025 tax statutory/ETR bridge / 연결기업 세율구조 증빙

## SEC original: a historic fact, NOT marginal WACC tax / SEC 자료와 적용범위

SEC FY2025 10-K filed **2026-02-17**, period ended 2025-12-31:
https://www.sec.gov/Archives/edgar/data/1046257/000162828026008603/ingr-20251231.htm

The tax reconciliation includes historical **U.S. federal statutory 21.0% / $204m** and **worldwide company accounting ETR 24.4% / $238m**. It separately identifies a state/local +0.7 percentage-point effect, foreign tax credits, foreign country differences (Mexico, Germany, Colombia and others), and tax reconciliation items. The differential is NOT an incremental, cash-realized 2026-09-14 interest tax shield. TAX.1 previously identified 2026 Q2 GAAP ETR 33.7% and adjusted 27.2% and annual 2026 projected effective-rate ranges; these are not automatically WACC rates either.

US IRC §163(j) can limit annual business interest expense deductions relative to business interest income, 30% of adjusted taxable income and applicable floor-plan financing interest (subject to exceptions). Official IRS Form 8990 guidance:
https://www.irs.gov/instructions/i8990

This is an external *legal-method reference*, NOT a locally SHA-captured source or evidence of Ingredion's incremental deductible cash interest, foreign debt booking or taxable income forecasts.

## Windows original-source intake / 로컬 원본 검증

After merged CI-confirmed main:

~~~powershell
cd C:\Valuation-Intelligence-Hub
git switch main
git pull --ff-only origin main
$raw = 'workspace\source_snapshots\INGR_2025_SEC_10K_original.html'
if (!(Test-Path $raw)) {
    if (-not $env:SEC_USER_AGENT) {
        throw 'SEC_USER_AGENT: set an authentic email privately in the local shell'
    }
    Invoke-WebRequest -Uri 'https://www.sec.gov/Archives/edgar/data/1046257/000162828026008603/ingr-20251231.htm' -Headers @{ 'User-Agent' = $env:SEC_USER_AGENT } -OutFile $raw -ErrorAction Stop
}
python -m valuation_hub.ingr_wacc_tax_bridge_10k --raw $raw --json
python -m valuation_hub.ingr_r8_m24_readiness --json
~~~

Keep original byte body and SEC contact private. The importer checks the official issuer/period, unique 2025 tax table, 21.0%/$204m, 24.4%/$238m, +0.7pp state/local, and independent foreign country/foreign-tax-credit rows. It fails closed on any contradictory/ambiguous original text or duplicate materialization. Two immutable source/proof JSON files are written to gitignored workspace. No WACC tax source input is generated.

## Missing tax-shield conditions / 세후차입비용 근거상 조건

A case-specific policy still must establish where *incremental debt interest* is incurred and deducted, the actual applicable marginal statutory/state/foreign rates as-of 2026-09-14, §163(j) limitation and 2026 rule applicability, corresponding foreign limits, taxable income/interest carryforward, and cash shield realization. Source and method review should then establish a scenario-aligned consolidated incremental tax shield without fake reviewer identity.

TAX.2 **always** returns selected_2026_wacc_marginal_cash_tax_rate=null, wacc_tax_source_input_created=false, and human_review_completed=false. Last measured real source readiness stays **5/7**, with pre_tax_cost_of_debt and tax_rate missing. Neither 21.0% US statutory nor 24.4% 2025 global ETR is eligible as an automatic final tax_rate. The NYU ERP as-of publication caveat and the Yahoo beta low-R²/price-only caveat remain open.
