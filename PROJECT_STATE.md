# Project State / 프로젝트 상태

> Canonical human-and-AI handoff. Repository-grounded state outranks chat or AI recollection.  
> 인간·AI 공통 정식 인계 문서. 저장소 근거 상태는 채팅·AI 기억보다 우선한다.

## 2026-10-27 LOOP-001 — outcome-based goal delivery contract / 목표 재정렬

**User local output on main `b92e77ee0e1ab3c210f2f409b6989d0989235189`:**
`ingr_r8_m24_readiness --json` genuinely reconfirmed **5/7 source
candidates**, status `HOLD_REAL_INGR_M24_WACC_INPUT_GAPS`;
`pre_tax_cost_of_debt` and `tax_rate` remain missing.
No reviewed WACC, 13/13 bound Draft, real Ingredion canonical admission,
or user-verified product outcome. 2026-09-14 as-of/AS_REPORTED unchanged.

**P0 release repair:** PR #174 offline SEC original-context audit merged
to main `b0eaafab69f972c16174cf5cb61475f1ac9e4554`
after full exact-head Python 3.11/3.12 CI PASS. This fixes the
previous `No module named valuation_hub.ingr_r8_m24_evidence_audit`
cause (branch-only PR), but the **audit has not been executed on the user's
gitignored original SEC files**. Do not report source-audit PASS yet.

**Strategic assessment:** Strong kernels, evidence and governance contracts
exist, but the north-star **real end-to-end** valuation and multi-asset
portability are not proved. The work focus moves from M-number/code output
to real outcome gates. `docs/GOAL_DELIVERY_LOOP.md`, `AGENTS.md`,
`governance/goal_delivery_plan.json` and offline
`python -m valuation_hub.goal_delivery_check --json`
are the enduring iteration contract, not financial approval.

**Next critical path:** (1) receive user-local audit result without
private identifiers; (2) independently source 2026-09-14 issuer-/tenor-
appropriate financing cost and jurisdiction/cash-interest-deductibility
method, then review low-explanatory-power beta and retrospective ERP
timing; (3) complete actual 13/13 FCFF Draft, scenario/sensitivity,
independent rerun, guarded admission; (4) second issuer, product usability,
then non-equity. The 2027 Tate & Lyle financing remains a separate
forward scenario, not June-2026 funded debt.

## Repository / 저장소

- Repository: `Eckommon/Valuation-Intelligence-Hub`
- Active parent: Issue **#66**
- Real Ingredion execution: Issue **#79**
- Target case: `US_INGR_INGREDION`
- Company: Ingredion Incorporated / NYSE: INGR / SEC CIK `0001046257`

No synthetic fixture may be admitted to `registry/cases.json` to claim real-case completion.

## 2026-10-23 AUDIT.1 — post-FRED timeout offline original-source checkpoint / 외부접속 없이 증빙 감사

User last supplied a genuine clean `main@b92e77ee0e1ab3c210f2f409b6989d0989235189`
M24 WACC readiness JSON, again **5/7** unreviewed source
candidates. Final two source inputs still
`pre_tax_cost_of_debt=MISSING_SOURCE_INPUT` and
`tax_rate=MISSING_SOURCE_INPUT`. User's FRED
`Invoke-WebRequest` timed out after 30 seconds and no FRED or
Fitch local original file was created; this is a source-collection
blocker, **not** a Git sync failure.

**M30-R8M24-AUDIT.1** (issue #79; implementation source
`ingr_r8_m24_evidence_audit.py`) is a new strictly offline
immutable original-source audit. It cross-checks the verified user-local
SEC Q2 2026 4-note schedule against original SHA
`bb03a79c2ab289873e5cfe6cc299ba52d9659dda5594d224b6dce844a6bbf167`
and note proof SHA `6158a891e2cc91d1466672c92a24c9141af2fe180a8735869b3cbe97b6f48997`,
plus verified SEC FY2025 10-K original body SHA
`f932b04e0bf99ad80ea19326b724d553368cac6c6dad2ab64c1512154cd1aa1b`
and tax method proof SHA
`c3d83e6a3c59236b1a18c1fc5cd3fa513605d6de0cf0c81c6131c291593a5594`,
then runs existing M24 readiness source validation. Output is
an ignored local independent risk/exception ledger with
**5/7 HOLD, no rate inputs or approval**, not a market data importer.

**Review warnings preserved:** Yahoo INGR beta 0.342231910459605,
157 weekly pairs, R² 0.07067663798658909 (low-power);
price-only no dividends; NYU September ERP Oct-retrospective
availability unproven and author reference 4.75% RF vs Sep14
4.97% RF; market equity 40-day share count lag; Q2 long-term
Level2/short-term carrying debt market-value proxy.
Finance **scenario split**: 2026-09-14 AS_REPORTED standalone
(with upcoming Oct 2026 3.2% notes refinancing) versus
2027 Tate & Lyle combination future incremental capital.
Neither 2025 effective tax 24.4%, U.S. 21% statutory
nor historic coupons create a marginal tax or issuer YTM.

**Local next action:** Pull main and execute
`python -m valuation_hub.ingr_r8_m24_evidence_audit --json`
offline, without FRED/Fitch access, alongside existing
`ingr_r8_m24_readiness --json`. See
`docs/M30_R8M24_OFFLINE_EVIDENCE_BOUNDARY_AUDIT.md`.
An audit ERROR on altered/missing original or a genuinely
advanced 6/7 stage must be investigated, not bypassed.
No reviewed WACC, no Draft v04, 13/13, canonical case,
or human approval.

## 2026-10-18 RD.4 primary 2026 pre-as-of Ingredion issuer BBB rating / 신용등급 진전

**First-party rated-borrower evidence discovered**: Fitch Ratings
June 8, 2026, official
https://www.fitchratings.com/research/corporate-finance/fitch-affirms-ingredion-incorporated-idr-at-bbb-outlook-stable-08-06-2026:
Ingredion Long-Term IDR **BBB**, senior unsecured long-term
**BBB**, short-term **F2**, Outlook **Stable**; pending
Tate & Lyle acquisition expected in second half 2027 requires
around **USD4.4bn future incremental borrowing** (not
June30 2026 funded debt). S&P June 8, 2026 primary also
reports same BBB senior unsecured class at
https://www.spglobal.com/ratings/en/regulatory/article/-/view/type/HTML/id/3576456 .
Fitch issuer's BBB credit **rating class** thus matches the FRED
Sep14 BBB-index yield 5.90% documented in RD.3, but not the
issuer instrument-specific YTM, liquidity, maturity/refinance
premium or projected acquisition capital structure.

**Issue #172 / RD.4:** independently ingest official Fitch
June 8 original HTML under ignored workspace and emit SHA-bound
rating/context proof only; preserves no WACC debt source input.
S&P original not yet SHA-attested. See
`docs/M30_R8M24_FITCH_20260608_RATING_INTAKE.md`.
If blocked by publisher login/challenge, stop and preserve
HOLD — no bypass or fabricated original.

A future explicit indexed BBB **standalone** forward-debt
assumption must source-bind and govern issuer rating,
2026-09-14 index yield, actual four-note SEC inventory,
due Oct2026 refinancing, tenor mismatch and prospective 2027
acquisition; no treating 5.90% as an INGR observed bond quote.
**Actual WACC source readiness remains 5/7**, missing
pre_tax_cost_of_debt and tax_rate, despite verified tax
context and forward-market/rating comparators.

## 2026-10-18 SEC 2025 actual tax original + RD.3 market comparator / 최신 실증

**Last actually observed canonical Windows run**: main
`fa2cb655cfee54f5d9ef273d2b271852ade9d238`.
The user's **unaltered original SEC FY2025 10-K** passed TAX.2:

- original source body SHA:
  `f932b04e0bf99ad80ea19326b724d553368cac6c6dad2ab64c1512154cd1aa1b`;
- source snapshot:
  `eb36a3dfede4b45e040dfcc5ae4b7e55caeb6b2a9cde6e3135dbcab6d52b6d08`;
- tax-method proof:
  `c3d83e6a3c59236b1a18c1fc5cd3fa513605d6de0cf0c81c6131c291593a5594`;
- `REAL_INGR_2025_TAX_STATUTORY_EFFECTIVE_BRIDGE_CAPTURED_METHOD_HOLD`:
  historic 21.0% federal US statutory and 24.4% global FY2025
  effective; **no WACC marginal tax input**.

The real local M24 run separately reconfirmed **5/7** source
candidates, with beta **0.342231910459605**, 157 weekly aligned
Yahoo INGR/^GSPC *price-only* returns and R² **0.07067663798658909**
(low explanatory power reviewer triage). Missing exactly
`pre_tax_cost_of_debt` and `tax_rate`; status
`HOLD_REAL_INGR_M24_WACC_INPUT_GAPS`, human_review_completed=false,
reviewed_wacc_package=null, draft_v04_created=false.

**New RD.3 market comparison investigation:** Official
[FRED/ICE BBB US Corporate Index Effective Yield](https://fred.stlouisfed.org/data/BAMLC0A4CBBBEY)
series BAMLC0A4CBBBEY shows **2026-09-14 5.90%**, prior
2026-09-11 5.89%. It is a BBB index *benchmark*, not an INGR
bond yield; neither INGR's BBB credit rating nor tenor/term match
has been verified. FRED/ICE index data are proprietary and licensed
**for internal use only**. Work Issue #170 introduces a
**non-WACC-input** local-only evidence comparator intake; test
fixtures must be synthetic. The original index HTML is NOT
captured from the user's machine yet. No direct 6/7 claim.

Read `docs/M30_R8M24_FRED_BBB_INDEX_COMPARATOR.md` and
`docs/M30_R8M24_TAX_2025_BRIDGE_INTAKE.md` for the next exact
local source checks. To truly close #161, independently source
2026-09-14 INGR/issuer-term market prices or a source-backed
credit/rating/refinancing scenario with typed analytical review;
to close #168/#150/#152, substantiate *incremental 2026 cash
interest deductibility* by jurisdiction under relevant rules.
Original NYU ERP is retrospective October; no Sept14 release
availability attested, and author 4.75% RF vs valuation 4.97%.
Do not promote any unreviewed WACC or Draft.

## 2026-10-17 TAX.2 implementation successor / 세율 증빙 추가 단계

Tax statutory/effective rate separation implemented for FY2025 SEC
10-K (filed 2026-02-17; original source:
https://www.sec.gov/Archives/edgar/data/1046257/000162828026008603/ingr-20251231.htm).
**Issue #168 / PR #169** delivers an offline original-HTML
source-only intake that checks 2025 U.S. statutory **21.0%/$204m**
vs company historical global ETR **24.4%/$238m**, +0.7pp
state/local bridge and 2025 foreign tax/geography anchors. It writes
a user-local snapshot and separate proof by original body SHA.
It intentionally does **not** emit a `tax_rate` WACC input, approve
a cash tax shield, assume §163(j) deductibility, or assert that
FY2025 ETR equals the 2026-09-14 marginal rate.

**This code's 2025 10-K original has NOT yet been run on the user's
machine**. User may capture the source after merged main and run
`python -m valuation_hub.ingr_wacc_tax_bridge_10k --raw
workspace/source_snapshots/INGR_2025_SEC_10K_original.html --json`,
preserving source bytes and SEC contact privacy. Details:
`docs/M30_R8M24_TAX_2025_BRIDGE_INTAKE.md`.
The next true cash marginal tax method needs jurisdiction-specific
financing and income forecasts, applied §163(j) and foreign
deductibility, and scenario-specific incremental tax shield proof.
**Real 5/7 stays measured**; remaining tax_rate and
pre_tax_cost_of_debt remain HOLD. Financial market bonds may require
CUSIP-specific FINRA TRACE print/yield evidence; official bulk
Enhanced Historical TRACE is a separate paid/lagged offering,
not automatic free Sep-14 historical issuer YTM access.
Issue #161 tracks the yield evidence route.

## 2026-10-17 M30-R8M24 user-local original-source checkpoint — ACTUAL 5/7 / 실제 검증 최신 상태

**This checkpoint supersedes the earlier 4/7 and 2/7 notes below.**
User ran main at `0e5d99796d13f5c23f974c48d914e778ba7ac047` on Windows
and supplied full local no-secret JSON. The two former blockers were
resolved against the unchanged exact inputs, **not merely synthetic CI**.

- SEC Q2 2026 **original** body SHA
  `bb03a79c2ab289873e5cfe6cc299ba52d9659dda5594d224b6dce844a6bbf167`;
  existing snapshot SHA
  `f2b195c18e55ab579d9eb997017b9dc4327d7a6758fe19349d982d70e94007d6`;
  real Note 6 inventory proof SHA
  `6158a891e2cc91d1466672c92a24c9141af2fe180a8735869b3cbe97b6f48997`;
  **4 senior notes**, carrying long-term USD **1,742m**.
  `REAL_INGR_SEC_BOND_TERMS_CAPTURED_FORWARD_YIELD_HOLD`.
  No issuer 2026-09-14 bond YTM, no forward pretax debt rate,
  `wacc_debt_input_created=false`.
- Yahoo v8 original issuer body SHA
  `3eb0accd980d947ad80176edaa8b6188080122d83a04c86f0be162d9b6ba37cd`;
  Yahoo ^GSPC original body SHA
  `979d47fc367208c03ba89c70268ef3d01a09b8f9456199e2e2449970fe235307`;
  INGR source input SHA
  `3fa3ecf50a7c44c59197c61f890efeb0cd520defb8a8e96964e38e75b7d0ddf4`;
  two-source proof SHA
  `1f53a9bb6758c4d7718e5f650a62bb2b0e459ce4dde4df85a16a999b03fbbf91`;
  **price-only** 3-year weekly **157 paired returns**, OLS
  `beta=0.342231910459605`,
  `R²=0.07067663798658909` (approx **7.07%** of
  INGR sample weekly equity-price-return variance explained by this
  single S&P500 price-return regression). This is *not* a regression
  standard-error confidence interval, statistical validity proof, or
  total-return beta. The low R², missing dividends, possible vendor
  price adjustments and historical availability require explicit
  methodological review. Source `ASSUMPTION`, Tier B, not
  reviewed WACC.
- Actual M24 result **5/7 `FRESH_SOURCE_INPUT_CANDIDATE`**:
  rf 4.97%, ERP 4.14% (October author *retrospective* Sep1 values),
  beta as above, market equity proxy USD 6,220,000,248.77, debt-MV
  proxy USD 1,681m. **MISSING** only
  `pre_tax_cost_of_debt` and `tax_rate`.
- Overall status remains **`HOLD_REAL_INGR_M24_WACC_INPUT_GAPS`**;
  `human_review_completed=false`,
  `reviewed_wacc_package=null`,
  `draft_v04_created=false`. No real-case canonical
  promotion/admission, and no fake reviewer.
- Beta QA: the review-triage threshold `R² < 0.10` is
  explicit local **advisory only**, NOT a significance test,
  promotion grant or automatic source failure. 5/7 source score
  remains compatible with a low-quality unreviewed regression.
- Original NYU ERP snapshot still has
  `historical_availability_asof_proven=false` relative to
  **valuation as-of 2026-09-14**, and original author 4.75% RF differs
  from 4.97% same-date selected RF. Do not erase this risk.

**Next implement/execute:** (i) WACC 2026-09-14 issuer forward
`pre_tax_cost_of_debt` via actual dated bonds/term-matched
market yields and 2026 October refinancing assumptions, Issue #161;
(ii) jurisdiction-weighted marginal cash tax and U.S. IRC §163(j)
interest deductibility evidence (Issues #150/#152). The 2025 10-K
(filed 2026-02-17) documents **21% U.S. federal statutory** vs
**24.4% worldwide 2025 effective** tax; both are distinct from the
global WACC marginal interest shield. The SEC Q2 8-K effective ETR
source is context-only, not an approved tax WACC source.
See official 2025 10-K:
https://www.sec.gov/Archives/edgar/data/1046257/000162828026008603/ingr-20251231.htm
and IRS §163(j) Form 8990 instructions:
https://www.irs.gov/instructions/i8990.
No pre-tax issuer-specific bond YTM or deductible worldwide cash-tax
rate has been established by the local 5/7 run.


## 2026-10-16 M30-R8M24 historical source blockers and tested fixes / 실증 장애·수정

**Latest code merge (verify exact HEAD each turn):**
32c9ce833a21462c23e7fdfda3d308440be6bee3.

On clean prior main 4ce85bd74fa06a09ce6e2275fb48b3cfa9078b38
the real user-local run reported:

- SEC RD.1 maturity parser: ERROR "INGR 2.900% note/maturity
  missing or duplicate" on original user-local Q2 Form 10-Q
  (raw SHA bb03a79c2ab289873e5cfe6cc299ba52d9659dda5594d224b6dce844a6bbf167).
  The official SEC 10-Q DOES list the note: the code's exact
  Inline-XBRL HTML text-node whitespace assumption was too strict.
- INGR.US and ^SPX Stooq CSV downloads: both instead returned
  JavaScript browser verification HTML. The OHLCV importer
  correctly rejected them; do not run third-party challenge
  solvers, retry with invented token, or treat HTML as market data.
- M24 readiness remained exactly **4/7 actually verified**, missing
  levered_beta, pre_tax_cost_of_debt and marginal tax_rate.

**Fixed capabilities, not new observed market numbers:**

| Fix | GitHub | Final-head Python 3.11/3.12 CI | Authority |
|---|---|---|---|
| SEC exact coupon/dates with HTML node spacing, bounded non-promoting --diagnose | PR #164 → main 84f55ee26f3af60cbebf6437f5bd827187a983bd | run 38764614323 PASS/PASS | SEC original user-local re-execution **not yet confirmed**; no YTM |
| Yahoo v8 original two-source INGR/^GSPC daily chart JSON alternate beta route | PR #165 → main 32c9ce833a21462c23e7fdfda3d308440be6bee3 | run 38765181808 PASS/PASS | Yahoo original user-local JSON **not yet obtained**; no observed beta |

**Next execution** (all originals remain gitignored; no overwrite
or fabricated snapshot):

1. Pull latest main. Re-run exact already stored SEC source:
   python -m valuation_hub.ingr_wacc_debt_bond_terms
   --snapshot workspace/source_snapshots/INGR_Q2_debt_market_value_bb03a79c2ab28987_snapshot.json
   --json. If ERROR, rerun same command with --diagnose for
   bounded note-text excerpts and **do not edit the original**.
2. Read docs/M30_R8M24_YAHOO_CHART_BETA_INTAKE.md.
   Request independent original JSON from two date-scoped Yahoo v8
   chart URLs using PowerShell (INGR and ^GSPC), and run
   python -m valuation_hub.ingr_wacc_yahoo_chart_beta
   --issuer <original_JSON> --market <original_JSON> --json.
   The older Stooq challenge HTML files must never be passed.
   Yahoo API is unofficial and may rate-limit or demand auth.
   Any download blocked/short/wrong-schema fails closed.
3. Rerun python -m valuation_hub.ingr_r8_m24_readiness --json.
   Only *actual successful* original-source beta proof may raise
   4/7→5/7 unreviewed candidates. Bond inventory has no
   pre_tax_cost_of_debt input and changes readiness by zero.
4. Independently source contemporaneous issuer YTMs/credit spreads
   as of 2026-09-14 (Issue #161/#154) and WACC marginal cash-tax
   convention (Issue #150/#152). No coupon average, Level 2
   aggregate fair-value ratio or effective-tax guidance midpoint
   can replace either. Preserve ERP October retrospective source's
   availability caveat and 22bp model/valuation risk-free difference.

No source credentials, paid service, human approval, WACC package,
Draft v0.4, 13/13 or canonical real-case admission occurred here.

## 2026-10-16 M30-R8M24 beta/forward-debt historical beta/debt cursor / 다음 구현 재개점

Last merged executable implementation (verify GitHub main on each
resumption): `25aadb77893d38a459e41452d1201d9b5027e73a`.
This **does not supersede actual 4/7 source evidence** documented below.

| Mission | PR | Merge SHA | Final-head CI, Python 3.11/3.12 | Source readiness |
|---|---|---|---|---|
| M30-R8M24-BETA price-only INGR/^SPX 3y weekly OLS with dual immutable CSV SHA/proof | #160 | `a15eb8287642663f7b1314fddec1065af64eb576` | `38760693827` PASS/PASS | **NOT RUN ON REAL CSV**, 4/7 persists |
| M30-R8M24-RD.1 exact previously validated SEC four fixed senior-note maturity/coupon/carry inventory; forward yield HOLD | #162 | `25aadb77893d38a459e41452d1201d9b5027e73a` | `38762490748` PASS/PASS | source-only context; no \`pre_tax_cost_of_debt\` input |

**Actual next steps, not completion claims / 실제 다음 순서**

1. Read `docs/M30_R8M24_BETA_REGRESSION_INTAKE.md`;
   capture true daily **INGR.US** and **^SPX** Stooq CSV (date-scoped
   2023-09-14→2026-09-14) in gitignored workspace. Stooq may
   require API access/CAPTCHA; never fabricate a CSV or store a key.
   Run `python -m valuation_hub.ingr_wacc_levered_beta --issuer <ORIGINAL_CSV> --market <ORIGINAL_CSV> --json`.
   Price-only beta omits dividends and remains an ASSUMPTION;
   historical vendor adjustment/publication as-of is unproven.
   If actual source proof passes, potential **5/7 source candidates**
   only; still not a reviewed WACC.
2. Reuse the **existing actual** SEC original snapshot named
   `INGR_Q2_debt_market_value_bb03a79c2ab28987_snapshot.json`.
   Run `python -m valuation_hub.ingr_wacc_debt_bond_terms --snapshot workspace/source_snapshots/INGR_Q2_debt_market_value_bb03a79c2ab28987_snapshot.json --json`.
   It validates coupon/maturity rows for 2.9%/2030, 3.2%/2026,
   3.9%/2050 and 6.625%/2037; fiscal debt totals and undrawn Tate & Lyle
   acquisition funding; returns **no forward yield**.
3. Per #161/#154, obtain **issuer-specific market YTM or 2026-09-14
   dated comparable term-match credit-spread + UST**; prove coupon dates,
   principal/face vs reported carrying, accrual, call/redemption,
   refinancing and maturity/market-weight convention. Do NOT use the
   Q2 historical coupon average, Level2 aggregate fair value of
   1,640m or January 2026 industry 5.07% as a directly observed
   firm-specific forward debt cost.
4. Per #150/#152, distinguish company accounting effective tax from
   WACC marginal interest deductibility under applicable jurisdictions.
   The 2026 8-K tax proof does not generate \`tax_rate\`.
5. Rerun M24 readiness; preserve as-of 2026-09-14, 4/7 actually
   confirmed, source timing of October retrospective NYU September
   ERP unproven, author 4.75% RF vs valuation 4.97%.
   Only 7/7 plus governed review proceeds to M25/M26, M28 13/13,
   M29 and guarded admission.

No paid service authorization, external trade, human approval,
WACC package, Draft v0.4, or Ingredion registry canonicalization
occurred in this implementation.

## 2026-10-16 M30-R8M24 live original-source checkpoint / 실증 원본 재검증 완료

**THIS IS THE NEWEST REAL EXECUTION STATE**, superseding the earlier
2026-10-15 **2/7** checkpoint below. The user ran Windows PowerShell
on clean `main@1a9844eba17d936dba3d951b756ba8355e1c3ce5`
and supplied complete non-secret CLI JSON, including actual original
source snapshots, input/proof SHA digests, and the M24 readiness
manifest. All files remain user-local, gitignored. **Actual sourced
WACC readiness is now 4/7**, not merely a hypothetical outcome.

| Real WACC metric | 2026-09-14 source status | Semantics |
|---|---|---|
| `risk_free_rate` | `FRESH_SOURCE_INPUT_CANDIDATE` | FACT; 4.97% nominal UST 10Y; Tier A |
| `equity_risk_premium` | `FRESH_SOURCE_INPUT_CANDIDATE` | ASSUMPTION; 4.14%; Tier B; October 1 author **retrospective** previous-month section |
| `levered_beta` | `MISSING_SOURCE_INPUT` | Requires source-aligned levered-beta methodology |
| `pre_tax_cost_of_debt` | `MISSING_SOURCE_INPUT` | Requires forward-looking issuer debt yield / spread methodology |
| `equity_market_value` | `FRESH_SOURCE_INPUT_CANDIDATE` | ASSUMPTION; USD 6,220,000,248.77 using 40-day lagged Aug 5 shares; Tier B |
| `debt_market_value` | `FRESH_SOURCE_INPUT_CANDIDATE` | ASSUMPTION; USD 1,681,000,000; June 30 observed Level-2 long-term 1,640m + short-term carrying-as-FV 41m; Tier A |
| `tax_rate` | `MISSING_SOURCE_INPUT` | Marginal cash-tax method unresolved; published effective tax guidance is not a WACC input |

**Local evidence SHA identifiers (never paste identifying SEC User-Agent):**

- NYU September ERP: original 17,069-byte HTML body SHA
  `755ad4d972431c7852bc0a723630d86cbfc84b14febb259858d1938458c0e0c7`;
  snapshot `d40b61c2b52e5b25d8ed52f2343fc77167933bf13da22fde63776c229f6a5d99`;
  input `015c2e17b2062e402fe944c08888d6cc148819e0c0597efbb7f215438f53f66d`;
  proof `d6a1b996383d172c499bc9b22cdd53089837c847f8432fff3386fb8c9dd7c541`.
- Ingredion June 30 SEC Q2 debt MV: source body SHA
  `bb03a79c2ab289873e5cfe6cc299ba52d9659dda5594d224b6dce844a6bbf167`;
  snapshot `f2b195c18e55ab579d9eb997017b9dc4327d7a6758fe19349d982d70e94007d6`;
  input `bc35facac9203aa5d1001de8c0c1484f4c9efb56a4e07c3a5957585cb0872ed2`;
  proof `4c7c42515b5de8fd123abeff8a6462a7f112ffc0f885d459049406a90e136426`.
- Ingredion August 4 SEC 8-K tax context: source body SHA
  `da3b94266f9f3ef43a0d67e538e50ab13123e3d32d9b54c68e77c660fdb11468`;
  snapshot `9b9c61e450e746c7ee0104adde22a1bce51b963532d2b2c47e275814074abe42`;
  proof `1174776e912c86368c5b64bf299157a36c0cf6291dd57dc7bafc7ac23f022961`;
  context-only `REAL_INGR_TAX_OBSERVATIONS_CAPTURED_METHOD_HOLD`;
  **no WACC tax source input created**.

The runtime returned:
`status=HOLD_REAL_INGR_M24_WACC_INPUT_GAPS`,
`metrics_ready=4`,
`human_review_completed=false`,
`draft_v04_created=false`,
`reviewed_wacc_package=null`.

**Critical temporal/economic risk:** October retrospective NYU author page
proves the September **4.14% method** and underlying September
data were reported *later*, not that the source was available by the
**September 14** valuation as-of. The extraction explicitly reports
`historical_availability_asof_proven=false`, and the NYU author
original model risk-free **4.75%** differs from target Treasury **4.97%**
by **22 bps**. These are analytical-adjudication blockers independent of
source freshness. An after-date document cannot be treated as
contemporaneous merely because the observed-on month predates as-of.

**Next execution:** Prioritize Issue #154 for independent, time-aligned
**levered beta** and **forward pre-tax cost of debt**, and #150/#152 for
jurisdiction/deductibility-grounded **marginal cash-tax** selection.
Preserve existing immutable originals and avoid re-importing the
same source bytes; use original-source date and method proof.
Only after all 7/7, independent source date checks and governed AI/human
authority as appropriate, proceed to scenario WACC, M25/M26, Draft 13/13,
M29 and guarded canonical real-case admission. No claim of a completed
valuation or a reviewed WACC.

### SEC access costs and privacy / SEC 공시 무료 이용과 개인정보

The US SEC officially provides public EDGAR search/downloads free of
charge; declaring a genuine, user-owned email as the scripted
`User-Agent` contact **does not register a paid account or
create an EDGAR retrieval charge**. This contact is transmitted in
request headers to SEC; it is not a payment credential. Keep it in the
local PowerShell process/environment and outside GitHub, JSON
artifacts, issues, CI logs and chat. SEC automated fair-use rate is
currently **at most 10 requests per second**. Third-party premium
data services are separate from free SEC EDGAR.
Authoritative policy:
https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data


## 2026-10-15 M30-R8M24 checkpoint — historical 2-of-7 resume point / 과거 재개점

This section **supersedes the historical M30-R8 baseline below**. Always
verify the actual merged main SHA using GitHub/git before further
implementation. Last *feature* merged main:

`05146a65d34847364f7654879677fff4c253cef6`

Source-provenance and readiness slices completed through PR/CI:

| Slice | PR | Feature merge main | Python 3.11/3.12 final-head CI |
|---|---|---|---|
| NYU Damodaran Oct-page Sep ERP inline-markup strict parser | #149 | `43265fc565ab0b10eea2f93f910cbceeb90ab8ff` | `38609326752` PASS/PASS |
| SEC 2026Q2 long-term Level-2 debt FV + short-term debt FV proxy | #151 | `17e26305d75c92ad1c03d4ff0d3a56a4b186ea10` | `38653697205` PASS/PASS |
| SEC 2026Q2/2026 guidance tax ETR observation only | #153 | `3add8569b68869e59fa21f1f04185dbdc09be786` | `38654208754` PASS/PASS |
| ERP.3 October 4.20 numeric source anchor + independent Sep prior-month model | #157 | `05146a65d34847364f7654879677fff4c253cef6` | `38723026771` PASS/PASS |

**Real user-local Ingredion as-of 2026-09-14 WACC remains
`HOLD_REAL_INGR_M24_WACC_INPUT_GAPS`, with exactly **2/7 actually
confirmed** original inputs from the user's last run (risk-free UST 10y
4.97% and market-value-of-equity 40-day share-lag ASSUMPTION).
The real 17,069-byte NYU author HTML has its original SHA
`755ad4d972431c7852bc0a723630d86cbfc84b14febb259858d1938458c0e0c7`
and Oct 1 2026 heading + previous-month section. On original
`main@041379c4` Windows execution, the October current adjusted-payout
label did **not** match (count 0), whereas the explicit prior-month
adjusted-payout matched (count 1); the importer correctly returned
`NYU dated current adjusted-payout model missing/ambiguous`.
ERP.3 / PR #157 now binds the October current date + **4.20% value**
independently of the exact previous-month September 4.14% model,
all four alternatives and September author Treasury 4.75%.
**It still needs a real post-#157 original-source extraction rerun**. A source-attested 4.14% ERP is not a
reviewed WACC and retains the 22bp original author model Treasury vs
valuation-date risk-free convention.

The SEC 2026-06-30 debt market-value proxy is 1,640m disclosed
long-term debt Level 2 fair value + 41m short-term carrying ≈ FV
= **USD 1,681m ASSUMPTION** (vs 1,783m carrying), which **still
needs user-local exact original SEC HTML replay** after #151.
No snapshot SHA may be invented from web text or synthetic fixtures.

The SEC tax-ETR observation #153 records GAAP Q2 33.7%, adjusted Q2
27.2%, full-year GAAP range 27.4–28.9%, adjusted range 26.0–27.5%;
**not a WACC tax_rate**. It deliberately produces no tax WACC source
input and requires marginal-tax policy evidence.

### Immediate next execution (Windows user-local, gitignored data)

1. Confirm clean merged main; read `docs/M30_R8M24_DAMODARAN_ERP_INTAKE.md`
   and rerun existing October author raw HTML via
   `python -m valuation_hub.ingr_wacc_damodaran_erp --raw <LOCAL_HTML> --json`.
2. SEC source capture was **not run** in the last Windows attempt:
   it stopped at missing `SEC_USER_AGENT`. Set a *real personal contact*
   email only in the current PowerShell environment (never infer, commit,
   paste in chat, or pass on CLI). Capture SEC Q2 Form 10-Q locally.
   Follow `docs/M30_R8M24_DEBT_MARKET_VALUE_INTAKE.md` and run
   `python -m valuation_hub.ingr_wacc_debt_market_value --raw <LOCAL_HTML> --json`.
3. Capture SEC Aug 4 2026 8-K Exhibit 99 and run the
   **source-only** tax observation intake per
   `docs/M30_R8M24_TAX_OBSERVATION_INTAKE.md`.
4. Rerun `python -m valuation_hub.ingr_r8_m24_readiness --json`;
   verify all source/body/input/proof SHAs and candidate statuses.
   Source readiness **could** move 2/7→3/7→4/7 only after the
   original local source proofs validate. Never report such progress
   before it is actually observed.
5. Obtain evidence-driven **levered beta** and **forward pre-tax
   cost of debt** per Issue #154 and separately reviewed WACC marginal
   cash-tax convention per Issue #150/#152. No historical average
   borrowing rate or midpoint of management effective-tax guidance
   may silently substitute.
6. Only when all seven candidate inputs pass identity, as-of, freshness,
   provenance, exact method/scenario contract: proceed to governed
   WACC preparation/approval, then M25/M26, M28 13/13, M29,
   safeguarded `admission/*` PR/CI and canonical real case.

Parent Issues #66/#79 remain open. No fabricated approval, canonical
case, Draft v0.4, or registry mutation. The older M30-R8 historical
sections below preserve lineage but must not be treated as the latest
work cursor.

## Historical M30-R8 runtime baseline / 과거 runtime 기준선

Historical M30-R8 capability main (superseded by the resume checkpoint above):

`6a6409990c0f5612fb6489050cf26ab47263629d`

This is **M30-R8 (following M30-R7XL.2) — source-bound and assumption-aware R6 diluted-share Draft and M29 promotion support**. M30-R7XL.1 — fail-closed user-local Ingredion R7→R7X→R6 execution orchestration with deterministic M21 rehydration**, layered after M30-R7X. R8 does not change the R6 valuation formula. The installed `vih` entrypoint now delegates through M30-R8 to M30-R7 and older commands. Real local source execution remains `python -m valuation_hub.ingr_local_execution`. If the disposable M21 Q2 candidate/observation JSON is missing, the runner now re-extracts and re-normalizes it only from the exact locally validated immutable CompanyFacts snapshot SHA `57b61f2b535b446664a240228f00020b859052f384488441849da83f0ceebf32`; if that source snapshot is absent too, it fails closed with `NEED_SEC_COMPANYFACTS_SNAPSHOT`.

Installed `vih` enters through:

`valuation_hub.cli_entry_m30r8:main`

and delegates unchanged through:

`M30-R8 → M30-R7 → M30-R6 → M30-R5 → M30-R4 → M30-R3 → M30-R2 → M30-R1 → M30 → M29 → ...`

Repository state at this SHA is the canonical runtime baseline. Gitignored real-source working artifacts remain local and must not be reconstructed from hashes.

## Authority policy / 권위 정책

M30-R2 replaced the obsolete assumption that all analytical review requires a human.

Current policy:

```text
credible source evidence
  → exact provenance / identity / SHA lineage
  → semantic-fit criteria
  → cross-check / contradiction search
  → no material unresolved contradiction
  → typed AI analytical adjudication
```

Internal accounting, valuation, semantic interpretation, assumption preparation, repository governance, CI/PR/merge, and analytical canonical admission may be AI-governed when their evidence contracts pass.

Human approval remains mandatory for externally binding or irreversible actions, including:
- spending or committing funds / paid services;
- trading, payment, transfer, or real fund movement;
- contracts, legal attestations, regulatory/external submissions;
- credentials, accounts, permissions, or secret disclosure/change;
- other externally binding actions not already explicitly delegated.

No human identity may be fabricated. AI authority must be explicitly typed as AI.

## Recent canonical runtime lineage / 최근 정식 runtime 계보

| Slice | Issue / PR | Merge/main | Post-merge CI | Result |
|---|---|---|---|---|
| M30-R2 AI analytical authority | #84 / #85 | `f7ab190a32695b302e6bea67cc4647be2b106014` | `35181287106` | complete |
| M30-R2.1 AI debt evidence CLI | #86 / #87 | `ad41443753b1ce0c9f411743769ce66d9efa9618` | `35181524490` | complete |
| M30-R2.2 reviewer-type truth | #88 / #89 | `61ab850e58626a6c5ac69abfdb276ac63bc385f9` | `35184077583` | complete |
| M30-R3 SEC observed-field AI authority | #92 / #93 | `ec92bb4ef5fba2c005004d7b1214cd6a3f3e60a0` | `35247619398` | complete |
| M30-R4 AI dilution coverage | #94 / #95 | `5bd1d92a9733621393bbada4f301876180647829` | `35256710738` | complete |
| M30-R5 AI market-price authority | #96 / #97 | `4f8a9c988ee20ddf33585e8810db312821f43698` | `35283190462` | complete |
| M30-R4.1 strike-distribution-safe TSM | #100 / #101 | `aadc8fef8ff3ecb20ad71cbd90809c4e95b69c1f` | `35555025332` | complete |
| M30-R6 disclosure-limited dilution assumption | #104 / #105 | `749901e3234e441fabb4fdace298c5d779d35b7e` | `36526648339` | complete |
| M30-R6B category-level bounded dilution envelope | #106 / #107 | `1a9fa0d1a9d475ccf5c13f72722f81132031d496` | `36547591128` | complete |
| M30-R7 AI historical-dilution authority | #108 / #109 | `9829dc11758b243c4320bfd50588cc7bd600a17f` | `36549218203` | complete |
| M30-R7X source-bound R6 envelope ingress | #113 / #114 | `b951637a16698b2cae5ecdf6c51e7e7c5cb30636` | `36631518156` | complete |
| M30-R7XL local real-execution orchestration | #117 / #118 | `ef5c96a17b09f4de56137e2034f7fe8a6c4779e3` | `36653644257` | complete |
| M30-R7XL.1 deterministic M21 rehydration | #121 / #122 | `da6045ce7826310b771ea32cedd90753998502e4` | `36719117986` | complete |
| M30-R7XL.2 SEC inline-XBRL excerpt binding | #125 / #126 | `80298f47dd9a62fecfb5362e670a70be412be40b` | `38358522927` | complete |
| M30-R8 assumption-aware Draft/M29 successor | #112 / #127 | `6a6409990c0f5612fb6489050cf26ab47263629d` | `38498043228` | complete |

M30-R5 exact tested head:
- `a0389ce192e747258269757ec40a8d876ce9de5b`
- PR CI `35283056169`
- Python 3.11: **462 passed**
- Python 3.12: **462 passed**

Historical M1–M30-E/S/R1 remain regression-locked in repository history.

## Real Ingredion source baseline / 실기업 원문 기준선

Immutable SEC source:

```text
snapshot_sha256 = 57b61f2b535b446664a240228f00020b859052f384488441849da83f0ceebf32
body_sha256     = 53e524af4fe360cdf8eed3ee3055c87ff7abae5eb7e2053ff291667f5fb90745
status          = PASS_SOURCE_SNAPSHOT_VALIDATION
canonical       = false
```

M30-B preflight:
- SHA `69a458b319ecf89688e2e72439932afbb1057c9f3d1f4f6c8331402202af6773`
- `PASS_REAL_EQUITY_SOURCE_PREFLIGHT`
- blockers `[]`

M30-D readiness:
- SHA `6066ef813b2466bdc525ea9ab2b6b9948068a0cb7b59b5630274885499647a40`
- 13 material fields
- 31 DAG nodes
- historical initial decision `HOLD_AT_GOVERNED_BOUNDARIES`

That initial readiness manifest predates the R2–R5 authority migration and must not be read as the current field status.

## Real field execution / 실기업 필드 실행

### equity.debt — AI-governed path PASS

```text
value                   = USD 1,783,000,000
period_end              = 2026-06-30
SEC concept             = us-gaap:DebtLongtermAndShorttermCombinedAmount
observation_sha256      = 32027c57ac368fb115c06aa1a50152af353fefdc2dbb5b9fa834cc2ed2f6a2ad
AI evidence_sha256      = 0b2fd4fbc8b3d8f8c2faf6ce3cfeee6e92beafa0be45b7df1277f673183f820c
AI adjudication_sha256  = d8a7d94059e5affca895af09ae962bebfa94a5c341cd6ce72c795a61abbf233f
review assertion_sha256 = c5f465b9e88608f80e0bf31177a0ec7a99b571656b493de3ecdebd7fd1801832
reviewed profile_sha256 = b5fb0cbaa9758b2d772452ce00e3d3139af9aef7dd6e6b35a38db85b031d36e3
binding context_sha256  = 1339821cb11c66482cfcbff66838ea6bdd42d32ebabcd32927e6839e6fa1286a
review_authority        = AI
freshness               = FRESH
eligible                = true
```

Semantic decision:

`EXPLICIT_FILING_RECONCILIATION_EXCLUDES_LEASE_LIABILITIES`

The obsolete pre-R2.2 profile/context are superseded and must not be used.

### equity.cash — AI-reviewed PASS

```text
value                = USD 948,000,000
source observation   = 5603c65cb092f5d2ac49b67cc524da8e0d620561835baf8d4cc93afbf854363b
reviewed observation = c4c7cc9768835cd4ada7129f1ca33d6f7cf9b08a795e08d0085639f90d4551ec
class                = NORMALIZED_FACT
```

### current common shares — AI-reviewed base PASS

```text
value                = 63,063,979
source observation   = 7c54c10037edce452e4db03991e44440d24cd50e7a37a39e2efc90c9e1bee8f0
reviewed observation = 5624065ae34b4fb3d7adba25f865180b3efc9853f9ee2904875110c3e8e833f2
M22 base context     = 12ac21026b1a06756d0474e0ad2aec10bdd9391caf2ff03ca512c2cb3d8a0adc
freshness            = FRESH
```

Immutable semantic boundary:

```text
current_common_shares_base    = true
fully_diluted_shares          = false
direct_bind_to_diluted_shares = false
```

### equity.minority_interest — AI-reviewed PASS

```text
value            = explicit USD 0
source observation = 703f9f53859d8cef04fd207b604468735272c49d7955b7047ebe2304694cfa27
reviewed package = 92c741160fc4ea268cfda1eded5b2080afb622e7a0fd27f2fc40c41e9ab71331
eligible         = true
missing_is_zero  = false
```

## M30-R4 dilution contract / 희석 계약

`equity.diluted_shares` remains unresolved.

Exactly six categories are mandatory:

1. `options_treasury_stock_method`
2. `rsu_restricted_stock`
3. `warrants`
4. `convertibles_if_converted`
5. `contingent_shares`
6. `other_explicit`

Each must be explicitly:
- `PRESENT`
- `ABSENT_SUPPORTED`
- `BLOCKED_DEPENDENCY`
- `UNKNOWN_CONFLICT`

Missing evidence never becomes zero or absence.

Historical weighted-average diluted EPS shares are reference-only and may not become valuation-date fully diluted shares.

Options/warrants TSM requires a fresh source-bound reviewed market-price FACT.

## Real M30-R5 market-price execution / 실시장가격 실행

The real INGR market-price FACT is now source-bound and reviewed.

```text
ticker / venue       = INGR / NYSE
trading_date         = 2026-09-14
price                = USD 98.63
quote_type           = OFFICIAL_CLOSE
review_authority     = AI
package_sha256       = 607808de5224a84072427a18100e4933600fa4bad84057f9ffae0a7e436b7e9a
validator            = PASS_AI_REVIEWED_MARKET_PRICE_VALIDATION
```

Independent immutable snapshots:
- Investing.com: `8d889e4faa4232793d653fb1fed82582d22b570bf485afac9e1c378bef10324f`
- ChartExchange: `9e19415685779b8794c93fce9a50f772fcff8776d253688574fc6d9893f440da`
- StockAnalysis: `e30e991451c271d94b906fc5120203ad591c0b1f4b1a9756e4b0fc42496fc57c`

Market price is no longer a blocker.

## Real M30-R4 dilution execution and R4.1 correction / 실제 희석 실행·수정

First real HOLD execution captured and validated Tier-A issuer sources:

- 2026 Q2 10-Q snapshot: `f61f33b0e27403ab56882d8cc1daa3a66571e9452fc5d8012268f39ab098b0f9`
- 2025 10-K snapshot: `8be63bfbdfd16e77973b37ee7fce94f5131fedd443c01b234962e929c1e7835e`
- 2026 director-compensation exhibit snapshot: `45104cf9b7625ee851d5a87188a9ae8fb13fc9183a68529ca21c36ee104d1dce`

Initial HOLD artifact:
- inventory SHA: `fda95dfb56cc40e287a043f4947a6006c0da4fa183e36a135029da6e22a7b86d`
- adjudication SHA: `818a15b58fd97e627585e315f8f0d3c2db1e677ca8d309f0e264610a304972a1`
- decision: `HOLD_INCOMPLETE_DILUTION_COVERAGE`

Its overall HOLD remains useful historical execution evidence, but its original option adjustment of zero is **superseded for final authority**.

R4.1 falsified the aggregate weighted-average-strike shortcut:

```text
weighted_average_exercise_price != complete strike distribution
portfolio TSM = Σ tranche-level TSM
```

Canonical R4.1 rule:
- `TREASURY_STOCK_METHOD_TRANCHES_V01` requires explicit strike tranches whose counts reconcile to total outstanding instruments;
- aggregate TSM is allowed only when one homogeneous exercise price is explicitly supported;
- total options + weighted-average exercise price alone must fail closed.

Real current six-category status:

| Category | Current state | Evidence status |
|---|---|---|
| options_treasury_stock_method | BLOCKED_DEPENDENCY | complete valuation-date strike distribution unavailable |
| rsu_restricted_stock | PRESENT | 534,000 employee RSUs |
| warrants | ABSENT_SUPPORTED | full 10-Q + 10-K search returned zero warrant hits |
| convertibles_if_converted | ABSENT_SUPPORTED | full 10-Q + 10-K search returned zero convertible hits |
| contingent_shares | BLOCKED_DEPENDENCY | no complete point-in-time payout-weighted performance-award count |
| other_explicit | BLOCKED_DEPENDENCY | no complete 2026-09-14 director/deferred-equity aggregate |

Therefore `equity.diluted_shares` remains unresolved. Do not run `dilution-ai-finalize` from the original two-blocker inventory.

## M30-R6 / R6B / R7 dilution successors / 희석 후속 계약

Authoritative corrected R4.1 real HOLD:
- inventory SHA: `bb8242c126fcd0c91c0a3aedd8aac26640c8b3ad829a59823eb861762270a4b2`
- adjudication SHA: `48545fdeb713af826bd39d1fc2b22a5bb6dde10474d3a6ccac0174370d790d86`
- decision: `HOLD_INCOMPLETE_DILUTION_COVERAGE`
- blockers: exactly 3 — option strike distribution, payout-weighted performance awards, director/deferred-equity point-in-time aggregate.

M30-R6 establishes the conservative disclosure-limited dilution assumption path:
- exact R4 READY outranks fallback;
- UNKNOWN_CONFLICT cannot fallback;
- selected diluted-share output is `ASSUMPTION`, never FACT/DERIVED_FACT;
- default uncertainty materiality threshold is 5%;
- R6 output cannot direct-bind through M22 as an exact diluted-share fact.

M30-R6B adds a category-preserving analytical envelope:
- every M22 dilution category remains EXACT / BOUNDED / UNBOUNDED_DEPENDENCY;
- output class is `ANALYTICAL_RANGE`;
- a range can never become exact `equity.diluted_shares`;
- real-shaped conditional sensitivity currently spans 63,597,979 to 64,575,870 shares, with about 1.538% relative share uncertainty and about 1.514% maximum denominator-only per-share reduction;
- the director/deferred upper used in that research-shaped interval is explicitly `ASSUMPTION_CONDITIONAL`, not an issuer-reported valuation-date exact count.

M30-R7 closes the remaining historical-anchor authority gap:
- target Q2 weighted-average basic shares: 63.3M;
- target Q2 weighted-average diluted shares: 63.9M;
- historical incremental dilution: 0.6M;
- exact SEC candidate/normalized-observation reproduction, entity/period/filing/source-lineage checks, Tier-A evidence, contradiction search, and typed `AI_HISTORICAL_DILUTION_ADJUDICATOR_V01`;
- resulting historical dilution remains `DERIVED_FACT` with `historical_only=true` and `valuation_date_direct_bind=false`;
- R6 independently validates and SHA-locks the complete R7 authority package before consuming it.

M30-R7X closes the real-execution provenance gap for the R6 conservative upper envelope:
- real M30 envelope sources must be validated Tier-A `external-source-snapshot-v0.1` objects;
- each component claim is bound to an exact cited source excerpt, observed quantity, and unit multiplier;
- direct claims, performance uplift, and the pro-rata disclosure-lag buffer are independently reconciled before projection into the unchanged R6 component contract;
- the self-contained `source-bound-dilution-envelope-manifest-v0.1` embeds the referenced immutable source snapshots and can be supplied directly as R6 `upper_envelope` input;
- historical raw component arrays remain backward compatible, but the source-bound manifest is the preferred real M30 path.

## Real Ingredion R7/R7X/R6 execution — approved, assumption only

User-local validated execution under `main@80298f47dd9a62fecfb5362e670a70be412be40b`:

- `R7 package SHA` = `5411fb18b56e2b173a1d37fccd0c4d1ecb3bce105a5f8054d6e01df228e6be6d`
- `R7X source manifest SHA` = `1fa3b50977f15bbbb05894ba12576a5ac3190b0d33bf1cffb5003f9480d59a1d`
- `R6 evidence SHA` = `2c50fb9ee227b975dddee50ce881c20ed67f30459acffb3800636386aa270fe3`
- `R6 adjudication SHA` = `c09e6f4f972ddd14baea619dad81d5064e162745238bcc64ceea5c764ee90b57`
- `R6 approved package SHA` = `ae1e6612b67a56e568b9a9bcd6588c8765240a196ab395aa2dc86887b027e3af`
- class = **ASSUMPTION**, value = **63,900,000 shares**, upper relative spread = **3.2542%**, threshold = 5%.
- decision = `APPROVE_DISCLOSURE_LIMITED_DILUTION_ASSUMPTION`.

This authorizes the successor **not** a valuation-date `DERIVED` FACT. Input artifacts are still gitignored and must not be reconstructed from SHA alone.

## Exact resume point / 정확한 재개점

Latest merged runtime main:

`6a6409990c0f5612fb6489050cf26ab47263629d`

M30-R8 is now implemented, with a route-explicit M23 R6 assumption proposal and a noncanonical M28/M29 handoff that retains `ASSUMPTION`. The legacy exact M22/DERIVED route remains unchanged.

**Next work is the real user-local governed R8 case chain**, not more dilution architecture:

1. In the user-local repo, sync clean `main` and update editable installation after the new entrypoint;
2. take the exact existing real `r6_package.json`, `r7_package.json`, `r7x_envelope_manifest.json` and reviewed base/R4 context under gitignored workspace; use `vih r8-proof-build` and validate;
3. build M23's explicit R6 v0.3 route from a validated 2026-09-14 Ingredion v0.2 debt proposal, then carry it through the already-governed M24–M28 sourced WACC, terminal-growth, forecast, market-price, and minority-interest authorities;
4. build the R8 v0.9 proposal, then require explicit reviewer approval and noncanonical Draft application;
5. M29 must independently validate all 13 approved material fields and exactly four observed source claims for the R6 route; `equity.diluted_shares` must remain `ASSUMPTION` without an observed-claim link;
6. continue through separate promotion review, admission plan, guarded `admission/*` PR/CI and merge. **Do not admit a synthetic test fixture.**

If any required real WACC/macro/forecast evidence is unavailable, HOLD that field. No default assumptions, fake reviewer identity, R6B-range-to-point change or direct registry mutation.

## Remaining M30 acceptance / 잔여 완료조건

- [x] real SEC source capture / preflight / readiness
- [x] debt evidence-first AI authority and real debt execution
- [x] cash AI-reviewed authority
- [x] current common share base AI-reviewed authority
- [x] explicit-zero NCI AI-reviewed authority
- [x] six-category AI dilution governance
- [x] AI market-price authority successor
- [x] real INGR immutable market-price source snapshots
- [x] real INGR reviewed market-price FACT
- [x] source-bound Tier-A/excerpt ingress for the real R6 conservative upper envelope
- [x] real INGR R7 authority package + R7X source-bound envelope local execution
- [x] real INGR diluted-share assumption approved under R6 (R4 exact remains HOLD)
- [x] assumption-aware diluted-share Draft/handoff successor preserving `ASSUMPTION` authority when the R6 route is used (M30-R8)
- [ ] real `equity.diluted_shares` enters the governed Draft without authority relabeling
- [ ] seven M24 WACC source inputs + governed assumption
- [ ] M25 macro anchors + terminal-growth assumption
- [ ] M26 atomic six-field forecast block
- [ ] complete M28 13/13 bound result with unresolved=[]
- [ ] deterministic M29 promotion/admission/guarded plan
- [ ] separate `admission/*` application
- [ ] registry gains exactly one real Ingredion case
- [ ] final post-merge main CI and Issue #66 closure

## Existing canonical registry / 기존 정식 registry

- `KR_010120_LS_ELECTRIC`
- `KR_229640_LS_ECO_ENERGY`
- `US_JTAI_JET_AI`

None was admitted through this full M30 real-company path.

## Grounding authority / 근거화 권위

1. merged GitHub `main`, issue/PR state and exact CI evidence
2. immutable source/result/package SHA lineage
3. `PROJECT_STATE.md` + active execution issue
4. current chat
5. AI recollection
