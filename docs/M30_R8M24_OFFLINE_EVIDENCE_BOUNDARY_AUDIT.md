# M30-R8M24-AUDIT.1 — Offline actual SEC/WACC evidence-boundary checkpoint

## Objective / 목적

FRED website maintenance, throttling or Fitch publisher access limits
must not push the workflow toward fabricating an issuer bond YTM,
an issuer debt rate, a marginal cash-tax rate, or artificial 6/7
readiness. This **offline and source-locked audit** replays the
locally obtained SEC original evidence and M24 readiness contract
without any external website/data provider access.

As-of: **2026-09-14**, issuer **SEC CIK 0001046257**,
financial scope **AS_REPORTED USD**, no canonical case admission.

### What is independently checked / 검증 범위

1. Prior verified real SEC Q2 2026 original body SHA
   `bb03a79c2ab289873e5cfe6cc299ba52d9659dda5594d224b6dce844a6bbf167`,
   original Note 6 tranche-inventory proof SHA
   `6158a891e2cc91d1466672c92a24c9141af2fe180a8735869b3cbe97b6f48997`.
   The snapshot/underlying text and reconstructed 4 senior-note
   schedule are checked again with the canonical SEC parser,
   but **no 2026-09-14 market YTM was measured**.
2. Actual source-verified FY2025 SEC 10-K original body SHA
   `f932b04e0bf99ad80ea19326b724d553368cac6c6dad2ab64c1512154cd1aa1b`,
   method proof SHA
   `c3d83e6a3c59236b1a18c1fc5cd3fa513605d6de0cf0c81c6131c291593a5594`.
   Exact SEC 21% US statutory, 24.4% global historical ETR,
   state/foreign tax bridge checked again. **Not** incremental
   cash tax savings on 2026 debt.
3. Existing `ingr_r8_m24_readiness` (same M23 source SHA and
   original WACC evidence validators): exact **5/7**,
   0.342231910459605 Yahoo price-only beta from 157 matched weeks,
   R² 0.07067663798658909, NYU historical ERP point-in-time
   availability **not proven**, ERP author RF 4.75% versus
   Sep14 Treasury RF 4.97%, debt/equity proxies unreviewed.
4. **Fail closed** if the real secured source/body/method proof
   changed, there is a missing old snapshot/proof, a rate was
   admitted, approval has been asserted or any source readiness
   contract changed. Output is an **audit ledger**,
   not the original market evidence.

### Scope separation / 시나리오 경계

- **2026-09-14 standalone**: SEC 2026Q2 existing funded debt
  inventory and the Oct 1, 2026 note refinancing policy.
  SEC carrying/debt fair-value proxy is NOT yield to maturity.
- **2027 Tate & Lyle combination**: future scenario, not a fact
  of the 2026Q2 balance sheet. Future financing requires explicit
  terms and valuation assumptions (no mixing into old debt).
- Source context or BBB credit class alone is not an observed
  Sep14 INGR issuer coupon-adjusted bond YTM and not equivalent
  to a maturity-weighted pretax credit funding curve.
- Annual tax ETR, U.S. federal statutory rate and interest
  shield under US §163(j)/foreign deductibility are distinct.
- FRED/ICE licensed data are not accessed or redistributed by
  this audit; Fitch/S&P ratings not forged.

### Windows PowerShell / 로컬 실행

On a clean updated `main` and with the previously generated,
**unmodified** source files in `workspace/source_snapshots`:

~~~powershell
cd C:\Valuation-Intelligence-Hub
git switch main
git pull --ff-only origin main

python -m valuation_hub.ingr_r8_m24_evidence_audit --json

# Optional: existing canonical WACC source status, still HOLD
python -m valuation_hub.ingr_r8_m24_readiness --json
~~~

No additional download, paid API, FRED/Fitch access, passwords,
synthetic market prices or human reviewer is needed. The audit
produces a uniquely named **gitignored** report
`workspace/execution_artifacts/US_INGR_INGREDION/r8_m24_offline_audit_.../evidence_boundary_audit.json`.
It also runs the normal M24 preflight, which writes its own
gitignored `wacc_source_readiness.json`.

**Expected for the user's actual last run:** evidence-only
`PASS_ORIGINAL_CONTEXT_AUDIT_AND_HOLD_TWO_WACC_RATE_INPUTS`,
`current_source_candidates=5`, `unresolved_rate_inputs`
`pre_tax_cost_of_debt` and `tax_rate`.
The new audit reports original SHA/snapshot/method
proof metadata, risk flags, and independent standalone/future
combination scenario gates. **Not** 6/7, **not** reviewed WACC,
**not** Draft v04 or case admission.

If any original is missing/tampered, or new source is genuinely
collected causing 6/7 or 7/7, this stage returns ERROR intentionally.
Do not coerce the readiness count back to 5 or edit original
snapshots. Advance to a new evidence/proposal contract with the
new source's exact real SHA and appropriate scenario.
