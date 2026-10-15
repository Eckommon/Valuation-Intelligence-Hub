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

## M30-R8M24-ERP.1 — source-month compatibility repair

Real Windows execution on `main@dd5d062decfcc1ddc3baf5a0917fabdd4d03896a`
downloaded 17,069 bytes of author HTML, but the original exact
`Implied ERP on September 1, 2026` headline could not be extracted.
That error alone does not show which month the downloaded page actually
contains, or prove the 4.14% value has disappeared.

The repaired importer supports **two and only two** source-anchored routes:

1. Exact September 1, 2026 current-month headline with 4.14%
   adjusted-payout, all four alternative figures and 4.75% author
   model Treasury reference.
2. Exact October 1, 2026 current-month headline **plus its explicit
   `Implied ERP in previous month` panel**, with that panel matching
   the same 4.14%, four alternatives and 4.75%. The October heading
   establishes that the previous month is September; the actual
   previous-month panel establishes the values. November or any later
   month, an unspecified previous month, missing panel, duplicates, and
   contradictory model values always FAIL CLOSED.

Use this local *non-promoting* diagnostic first, on the same downloaded
file from the user's previous execution:

```powershell
$raw = 'workspace\source_snapshots\NYU_Damodaran_ERP_20260901.html'
python -m valuation_hub.ingr_wacc_damodaran_erp --raw $raw --diagnose --json
```

It reports original body SHA, original HTML byte count, dated current
headlines and prior-month-panel count, **without creating any WACC object**.

Then attempt original-source extraction only after confirming the page:
```powershell
python -m valuation_hub.ingr_wacc_damodaran_erp --raw $raw --json
python -m valuation_hub.ingr_r8_m24_readiness --json
```

The resulting evidence includes the source extraction route, the
separately observed original source date and 22bp risk-free mismatch.
A **later capture of a past-month author panel is retrospective
corroboration, not proof that it was made available as of Sep 14**.
`historical_availability_asof_proven=false`, and genuine human review
is still required to decide if a retrospective author-model source is
acceptable. Even a successful source capture is not a WACC approval.

If neither exact route exists, the result remains HOLD at 2/7.
The official NYU monthly spreadsheet can be separately inspected at
https://pages.stern.nyu.edu/~adamodar/pc/implprem/ERPbymonth.xlsx ;
its historical ERP column must NOT automatically be treated as the
same adjusted-payout 4.14% method without independent column mapping.


## M30-R8M24-ERP.2 — exact-model inline HTML boundary repair (#148)

The **real user-local** 17,069-byte original author HTML diagnostic reports
October 1, 2026, one prior-month label, original SHA-256
755ad4d972431c7852bc0a723630d86cbfc84b14febb259858d1938458c0e0c7.
Nevertheless the preceding parser failed before matching the dated adjusted
payout model: NYU exactly one dated current ERP headline required.

The synthetic regression for ERP.2 covers **markup-split text nodes** which
can insert whitespace before a percent sign, around a comma, inside model
labels, or before the author's Treasury reference. The parser now checks
**one and only one original dated current headline independently** of
the adjusted payout match, and exactly one October prior-month label;
shadow duplicates remain errors. Numeric 4.14%, all four September
alternatives and author's 4.75% model Treasury rate remain strict.
Source bytes/SHA are never normalized or replaced by synthetic HTML.
This is a *plausible* repair, not proof that actual user-local HTML parses.

After merging tested ERP.2, on **clean canonical main** in Windows PowerShell:


```powershell
git switch main
git pull --ff-only origin main
$raw = 'workspace\source_snapshots\NYU_Damodaran_ERP_20260901.html'
python -m valuation_hub.ingr_wacc_damodaran_erp --raw $raw --diagnose --json
python -m valuation_hub.ingr_wacc_damodaran_erp --raw $raw --json
python -m valuation_hub.ingr_r8_m24_readiness --json
```

Observe current_adjusted_payout_model_count and
previous_month_adjusted_payout_model_count: they should each be exactly
one for a structurally compatible October author page. Check the original
raw SHA matches the recorded input file; the source is not replaced by
the live website or a synthetic fixture. If extraction still returns ERROR,
retain the 2/7 WACC HOLD and inspect the original HTML locally rather
than copying expected 4.14% as a fake source input.

If it succeeds, only count a *source candidate* (potentially 3/7),
still with ASSUMPTION, source_is_retrospective_asof=true,
historical_availability_asof_proven=false, human_review_completed=false.
The remaining four WACC inputs and final approval are separately blocked.


## ERP.3 — original Oct 1 HTML source diagnostic and method-independent October date anchor

**Actual, not synthetic, 2026-10-15 user-local result** at
`main@041379c4f2ef42344725d108b1c05e65d55690c1`:

- original NYU HTML: 17,069 bytes; SHA-256
  `755ad4d972431c7852bc0a723630d86cbfc84b14febb259858d1938458c0e0c7`;
- exactly one current heading dated **October 1, 2026**, exactly
  one explicit previous-month panel;
- previous-month adjusted-payout label matches once;
- October current **full adjusted-payout label matches zero times**;
- importer FAIL CLOSED with
  `NYU dated current adjusted-payout model missing/ambiguous`.

The previous failure was caused by gating retrieval of a **September
historical previous-month model** on parsing the **unrelated October
current-month payout label**. ERP.3 separates these two evidentiary
claims:

1. Precisely one October 1, 2026 author current date headline,
   itself anchored to the source-author's October **4.20%** current
   numeric value (allowing only HTML-derived whitespace inside 4.20%).
2. Precisely one prior-month panel containing **September 1** adjusted
   payout 4.14%, all four expected alternative-model figures, author
   reference Treasury 4.75%, and exact original page bytes/SHA.

The October adjusted payout **method label is not required** to
date September's distinct previous-month claim. The October numeric
4.20 anchor, however, is required; a contradictory current value,
duplicate headings, unsupported November roll-forward, wrong
September rate/method or modified source bytes fail closed.

Direct September 1 current headlines still require an exact full
September adjusted-payout model. Both routes remain ASSUMPTION and
retrospective historical availability is NOT established by October
capture. October route remains
`historical_availability_asof_proven=false`.
No synthetic HTML is accepted as a real-case original.

After the tested ERP.3 merge, retry **the identical existing source
file**, not a current re-download:

```powershell
git switch main
git pull --ff-only origin main
$raw = 'workspace\source_snapshots\NYU_Damodaran_ERP_20260901.html'
python -m valuation_hub.ingr_wacc_damodaran_erp --raw $raw --diagnose --json
python -m valuation_hub.ingr_wacc_damodaran_erp --raw $raw --json
python -m valuation_hub.ingr_r8_m24_readiness --json
```


The diagnostic now emits
`october_current_4_20_numeric_anchor_count` plus a bounded
`current_headline_visible_excerpt`. If the October value anchor
count is not exactly 1, or any later method proof fails, **retain 2/7**
and inspect that bounded public text. Never hand-insert 4.14% to
bypass source SHA. Captures are named by original raw body SHA so
repeated identical bytes cannot silently create duplicate WACC inputs.

SEC original capture requires a distinct, user-owned runtime-only
`SEC_USER_AGENT` with a genuine contact email. Missing it
does **not** alter or invalidate the NYU original; no SEC snapshot
exists until the SEC download and importer are independently successful.
