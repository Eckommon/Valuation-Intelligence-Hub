# M30-R8M24-DMV — real Ingredion Q2 2026 debt market value

## Source, economics, and authority

Target: Ingredion Incorporated, CIK 0001046257; valuation as-of
**2026-09-14**. The primary official SEC Form 10-Q, reporting period
**2026-06-30**, was **filed 2026-08-07**, and thus was available
before valuation as-of.

SEC official original:
https://www.sec.gov/Archives/edgar/data/1046257/000162828026054722/ingr-20260630.htm

Source interpretation is deliberately **not** a reported total market-value
FACT. SEC Note 5 has **long-term debt Level 2 fair value $1,640 million**
(June 30 2026; December 2025 comparator $1,649 million), estimated
from major dealer quotations. It explicitly says short-term borrowings'
carrying values **approximate** fair values.

Note 6 separately reports total long-term debt carrying **$1,742 million**,
short-term borrowings carrying **$41 million**, and total carrying
**$1,783 million** (June 30 2026). The acquisition Bridge/DDTL
facilities were **undrawn** as of June 30, and their commitments are
never included as funding/debt in this calculation.

Explicit assumption calculation, USD millions:

    long-term fair value              1640
    short-term fair value proxy       + 41
    --------------------------------------
    total debt market-value proxy     1681
    total debt carrying amount        1783
    market-value discount              102

The 41 million element is a short-term **book approximates market**
methodology choice. Hence resulting WACC source class is **ASSUMPTION**,
Tier A *source*, observed_on=2026-06-30, **not FACT**, not DERIVED
and never preapproved WACC. The value is USD **1,681,000,000**.

## Offline exact-source capture on Windows

Run from a clean, up-to-date canonical repository. Do not paste your
identifying SEC contact email in GitHub issues, snapshots, or chat.
Configure the runtime-only **SEC_USER_AGENT** securely locally, as
specified in M30 Issue #79; don't pass it as a command-line option.

```powershell
git switch main
git pull --ff-only origin main
$raw = 'workspace\source_snapshots\INGR_2026Q2_SEC_10Q_original.html'
if (-not $env:SEC_USER_AGENT) { throw 'SEC_USER_AGENT is required in the local runtime' }
Invoke-WebRequest -Uri 'https://www.sec.gov/Archives/edgar/data/1046257/000162828026054722/ingr-20260630.htm' -Headers @{ 'User-Agent' = $env:SEC_USER_AGENT } -OutFile $raw
python -m valuation_hub.ingr_wacc_debt_market_value --raw $raw --diagnose --json
python -m valuation_hub.ingr_wacc_debt_market_value --raw $raw --json
python -m valuation_hub.ingr_r8_m24_readiness --json
```


Do not replace the downloaded original with reformatted/synthetic text.
The importer checks the exact SEC URL, source SHA, note boundaries,
Q2 2026 versus December 2025 columns, Level-2 row, short-term
approximation language, carrying-value reconciliation and undrawn
financing exclusions; SHA-locks both WACC input and method proof. It
writes **three noncanonical files** to gitignored workspace/source_snapshots.

If original HTML differs from the strict recognized contract, it
returns ERROR and readiness remains HOLD. It is **not** permissible
to substitute a remembered $1.681bn number or manually create a
fake source proof.

A successful original-file run may advance that *one source candidate*
from MISSING to FRESH; a source candidate is **not an approved WACC**.

## Tax scope separated

The August 4, 2026 Q2 press release at
https://www.sec.gov/Archives/edgar/data/1046257/000162828026052104/ingr-20260630xexx99.htm
reports second-quarter GAAP effective tax 33.7%, adjusted ETR 27.2%,
annual expected GAAP 27.4–28.9%, and adjusted 26.0–27.5%.
These are **not necessarily marginal cash tax rates** used in after-tax
cost of debt. Preserve as candidate observations, not an unreviewed
choice of a single tax_rate. No arbitrary midpoint, 21% federal
statutory shortcut, or shifted valuation date is allowed.

Next: source-bind distinct tax treatments and pretax debt cost,
independently of this debt market-value method. No approval,
13/13 handoff, or canonical admission is claimed here.
