# M30-R8SCOPE — Tier-A scope reconciliation and guarded M23 handoff

## Real activation

The user-local execution on canonical main `dba8f8f60b6c08dfe84b4cd3d3ecb1e327f14b17` returned
`HOLD_FINANCIAL_SCOPE_RECONCILIATION_REQUIRED` with all three exact
source SHA checks passing:

- AI-reviewed cash `c4c7cc9768835cd4ada7129f1ca33d6f7cf9b08a795e08d0085639f90d4551ec` (USD 948m, `AS_REPORTED`)
- AI-reviewed SEC aggregate debt `1339821cb11c66482cfcbff66838ea6bdd42d32ebabcd32927e6839e6fa1286a` (USD 1,783m, `CFS`)
- source-embedded R8 proof `8abc7cf93fd3e2bf93422e915ab4fe5c6ebad2faef34a0a2f7596038eda55cc9` (63.9m, `ASSUMPTION`).

## Source-bound proof

Only the **existing, immutable** SEC 2026-Q2 10-Q Tier-A external snapshot,
SHA `f61f33b0e27403ab56882d8cc1daa3a66571e9452fc5d8012268f39ab098b0f9`, may bridge the two original scope labels. Exact SEC accession:
`0001628280-26-054722`.

The algorithm requires the unmodified:
1. cash observation with matching Q2 SEC accession, instant 2026-06-30, and USD 948m;
2. AI-reviewed debt context/profile with matching Q2 accession and USD 1,783m;
3. R8 proof with original `ASSUMPTION` share class;
4. Tier-A issuer filing raw body, SHA, locator, consolidated balance sheet, cash $948m, financing note 6, $1,742m long-term + $41m short-term = $1,783m total debt.

It emits an independently reconstructible `sec-consolidated-scope-reconciliation-v0.1`
with a **RULE_BASED_SOURCE_RECONCILIATION** authority. This is an auditable
deterministic policy review, **not a fabricated human reviewer** and not a claim
that `AS_REPORTED == CFS` for other issuers or filings.

Original cash and debt contexts and their SHA/scope/class are never rewritten.
A new `draft-binding-proposal-v0.2-sec-debt-scoped-r8` route projects reviewed
CFS debt into the valuation proposal whose identity derives from original
`AS_REPORTED` cash. The full proof and source context remain nested and
validated. M23 independently builds an R6 v0.3 with diluted shares still
`ASSUMPTION`.

## Real local execution after canonical code promotion

```powershell
git status --short
git fetch origin main
git switch main
git pull --ff-only origin main
python -m valuation_hub.ingr_r8_m23_execution --json
```

Expected possible outcomes:
- `NEED_REAL_M23_SOURCE_ARTIFACTS`: exact locally reviewed cash/debt missing;
- `NEED_SEC_SCOPE_SOURCE_SNAPSHOT`: exact Tier-A source Q2 snapshot missing;
- `ERROR`: source/filer/amount/period/SHA contradiction (fail closed);
- `REAL_INGR_M23_R6_ASSUMPTION_READY`: exact proof, source, scope and both
  noncanonical M23 proposal contracts have independently passed.

The last outcome is **not** a complete Draft, human Draft approval, M29
promotion, registry admission or investment recommendation. The next
fully governed work is M24 WACC, M25 terminal growth, M26 forecasts,
M27 market-price authority, M28 minority interest, then M29 13/13 review
and controlled admission.

## Validation boundary

Python 3.11/3.12 CI must cover positive source-bound scoped M23,
missing raw snapshot, malformed source SHA, wrong accession,
illegitimate source-scope relabel, and incorrect R6 share class.
Historical exact M22 and R6 routes remain untouched.
