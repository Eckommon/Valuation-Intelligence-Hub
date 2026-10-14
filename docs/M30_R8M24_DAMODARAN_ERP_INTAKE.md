# M30-R8M24-ERP — NYU Damodaran Sep 1, 2026 implied ERP source candidate

## Date and source

Real Ingredion valuation as-of 2026-09-14, currently **2/7** verified
unreviewed M24 source inputs: 2026-09-14 Treasury 10-year 4.97% FACT
and 40-day-lagged common share market value $6,220,000,248.77 ASSUMPTION.

Primary methodological author source:
https://pages.stern.nyu.edu/~adamodar/New_Home_Page/home.htm

Author's published **September 1, 2026** implied U.S. ERP headline:
**4.14%** trailing twelve month **with adjusted payout**; other
payout/model variants **4.09%** trailing cash, **6.05%** 10-year
average CF yield, **3.80%** net cash yield, **3.56%** normalized
earnings/payout. The author uses a September 1 reference U.S.
Treasury risk-free **4.75%**, which is **22 bp below** the
September 14 official 10y rate **4.97%** used by this valuation.

This method's adoption is strictly an **ASSUMPTION** pending a reviewer
decision. It is neither a U.S. equity premium historical FACT nor a
free choice to add 4.14% to arbitrary risk-free rates without
acknowledging the model's original Treasury-date and payout method.

## Offline source capture after canonical merge

In clean C:\Valuation-Intelligence-Hub PowerShell:

    git status --short
    git fetch origin main
    git switch main
    git pull --ff-only origin main
    $raw = 'workspace\source_snapshots\NYU_Damodaran_ERP_20260901.html'
    curl.exe --fail --location --compressed 'https://pages.stern.nyu.edu/~adamodar/New_Home_Page/home.htm' --output $raw
    python -m valuation_hub.ingr_wacc_damodaran_erp --raw $raw --json
    python -m valuation_hub.ingr_r8_m24_readiness --json

The original NYU home page is **live and mutable**. It may have rolled
forward to October 1, 2026 or another month, in which case the exact
September 1 headline/method cannot be proved from that page, so the
importer must FAIL CLOSED. It never substitutes a previous-month or
alternative ERP headline. A dated archived/downloaded author dataset
would require separately verified immutable source parsing and date
logic, not manual insertion of 4.14%.

If it passes, three noncanonical user-local files are written under
gitignored workspace/source_snapshots: immutable author HTML snapshot;
typed WACC source input `equity_risk_premium=0.0414` with
`claim_class=ASSUMPTION`, Tier B, observed_on=2026-09-01; and a
date/payout/alternative-model/Treasury-reference method proof.

M24 readiness now additionally requires **all three objects**, validates
the original snapshot URL/body SHA, WACC input SHA and independent
reconstruction of the 4.14% dated methodological proof before ERP can
count as a fresh source candidate. A standalone 4.14% input remains
`ERP_EXPLICIT_MODEL_METHOD_PROOF_MISSING`. At most the real readiness
could move 2/7 -> 3/7. `human_review_completed` stays false.

The remaining four sources levered beta, pretax cost of debt, debt MV
and tax treatment remain HOLD. No fake human reviewer, approved WACC,
Draft v0.4, M29 case promotion or admission is permitted.
