# Valuation-Intelligence-Hub / 가치분석 인텔리전스 허브

> **Separate price from economic value, make assumptions explicit, and make valuation reproducible.**  
> **가격과 경제적 가치를 분리하고, 가정을 명시하며, 가치평가를 재현 가능하게 만든다.**

Valuation-Intelligence-Hub is a reproducible, evidence-grounded cross-asset valuation intelligence system connecting source evidence, normalization, governed facts and assumptions, Draft preparation, human review, valuation execution, and repository-controlled canonicalization.

Valuation-Intelligence-Hub는 출처근거·정규화·거버넌스 FACT/ASSUMPTION·Draft·인간검토·가치평가 실행·저장소 정식화를 하나의 재현 가능한 범자산 가치분석 흐름으로 연결한다.

## Core authority flow / 핵심 권위 흐름

```text
OFFICIAL / USER SOURCE
        ↓
IMMUTABLE / SOURCE-LOCKED INPUT / NOT CANONICAL
        ↓
FACT_CANDIDATE / NORMALIZED FACT / ASSUMPTION_CANDIDATE
        ↓
HUMAN-REVIEWED FACT / GOVERNED CONTEXT / ASSUMPTION
        ↓
DRAFT BINDING PROPOSAL / NOT CANONICAL
        ↓
HUMAN APPROVAL LOCK
        ↓
BOUND DRAFT RESULT / NOT CANONICAL
        ↓
COMPLETE GOVERNED HANDOFF
        ↓
PROMOTION → ADMISSION → guarded apply → PR/CI merge
        ↓
CANONICAL
```

Deterministic calculation never upgrades authority by itself. `FACT`, `NORMALIZED_FACT`, `DERIVED`, `ASSUMPTION`, human review, Draft binding, promotion, admission, and canonical repository state remain distinct.

결정론적 계산만으로 권위가 승격되지 않는다. `FACT`, `NORMALIZED_FACT`, `DERIVED`, `ASSUMPTION`, 인간검토, Draft 바인딩, 승격·수용, canonical 저장소 상태는 분리된다.

## Valuation kernel / 가치평가 커널

\[
FCFF = EBIT(1-T) + D\&A - CAPEX - \Delta NWC
\]

\[
WACC = \frac{E}{D+E}R_e + \frac{D}{D+E}R_d(1-T)
\]

\[
TV = \frac{FCFF_{n+1}}{WACC-g}, \qquad g < WACC
\]

The Hub also supports reverse valuation and probability-weighted venture valuation. Company cases are methodology references, not live investment recommendations.

## Install / 설치

```bash
python -m pip install -e ".[dev]"
```

## Governed capabilities / 거버넌스 기능

- M1–M12: valuation kernels, evidence governance, Draft/Candidate review, promotion/admission, guarded repository apply
- M13: immutable SEC CompanyFacts acquisition
- M14: immutable OpenDART financial-statement acquisition
- M15: period semantics, normalization, reconciliation, TTM
- M16: normalized evidence → equity-FCFF Draft binding proposal v0.1
- M17: SHA-locked human approval + noncanonical Draft binding application
- M18: governed historical operating/net margin derivation
- M19: explicit interest-bearing-debt components and aggregation
- M20: reviewed complete debt → `equity.debt` binding
- M21: governed historical dilution-reference evidence
- M22: valuation-date common-share base + explicit diluted-share bridge
- M23: complete reviewed fresh share bridge → `equity.diluted_shares` binding
- M24: sourced WACC components → reviewed valuation `ASSUMPTION` → `scenario.wacc` binding
- M25: reviewed WACC + long-run macro anchors → reviewed terminal-growth `ASSUMPTION` → `scenario.terminal_growth` binding
- M26: six FCFF forecast inputs → one reviewed integrated scenario `ASSUMPTION` → atomic forecast binding
- M27: exact as-traded market quote → reviewed market `FACT` → top-level `market_price` binding
- M28: exact consolidated noncontrolling-interest evidence → reviewed `NORMALIZED_FACT` → `equity.minority_interest` binding
- M29: complete human-approved 13/13 M28 bound Draft → authority-preserving `promotion-candidate-v0.2` → existing promotion/admission/guarded-plan pipeline

## Key semantic guardrails / 핵심 의미 안전장치

```text
liabilities                         ≠ debt
shares_outstanding                  ≠ diluted_shares
current_common_shares               ≠ fully_diluted_shares
historical dilution factor          ≠ automatic current dilution
historical revenue                  ≠ forecast revenue
historical margin                   ≠ forecast margin
calculated WACC                     ≠ reviewed WACC assumption
macro growth anchor                 ≠ terminal-growth fact
calculated forecast                 ≠ forecast authority
quoted number without provenance    ≠ governed market-price fact
historical adjusted price           ≠ valuation-date market price
total equity                        ≠ minority interest
missing minority-interest evidence  ≠ zero minority interest
DERIVED                             ≠ FACT
complete bound Draft                ≠ canonical case
FACT_CANDIDATE                      ≠ FACT
ASSUMPTION_CANDIDATE                ≠ ASSUMPTION
reviewed FACT / ASSUMPTION          ≠ canonical state
```

## M24–M26 governed valuation assumptions / M24–M26 가치평가 가정 거버넌스

### WACC
Seven explicit sourced components are combined under a fixed methodology, independently recomputed, and human-reviewed. WACC remains an `ASSUMPTION`, never a historical fact. See [`docs/WACC_ASSUMPTION_BINDING.md`](docs/WACC_ASSUMPTION_BINDING.md).

### Terminal growth
Terminal growth is reviewed against exact WACC lineage and explicit long-run macro anchors. `g < WACC` remains a hard invariant. See [`docs/TERMINAL_GROWTH_ASSUMPTION_BINDING.md`](docs/TERMINAL_GROWTH_ASSUMPTION_BINDING.md).

### Integrated forecast
M26 governs revenue, EBIT margin, tax rate, D&A, CAPEX, and ΔNWC as one atomic scenario assumption block. Partial approval is forbidden. See [`docs/FORECAST_SCENARIO_ASSUMPTION_BINDING.md`](docs/FORECAST_SCENARIO_ASSUMPTION_BINDING.md).

## M27 — Governed valuation-date market price / 거버넌스 가치평가일 시장가격

Market price is an observed market `FACT`, not a valuation assumption. M27 requires a source-backed as-traded quote, freshness control, exact instrument/venue/quote identity, SHA-locked human review, and exact entity/scope/currency/as-of compatibility. It accepts only v0.6 and replaces only `market_price` in v0.7.

See [`docs/MARKET_PRICE_FACT_BINDING.md`](docs/MARKET_PRICE_FACT_BINDING.md).

## M28 — Governed minority interest / 거버넌스 비지배지분

M28 closes the final equity-FCFF material-field gap.

```text
immutable exact source
  ↓
FACT_CANDIDATE
  ↓
NORMALIZED_FACT_CANDIDATE
  ↓
SHA-locked human review / date resolution
  ↓
reviewed NORMALIZED_FACT
  ↓
draft-binding-proposal-v0.8
  ↓
equity.minority_interest DIRECT_BIND
```

Exact v0.1 source boundaries:

```text
SEC:      us-gaap:NonredeemableNoncontrollingInterest
OpenDART: CFS + BS + ifrs-full_NoncontrollingInterests
```

M28 never derives minority interest from total equity or liabilities. Redeemable NCI is outside the SEC v0.1 field boundary. Missing source evidence fails closed; explicit reported zero remains valid evidence.

SEC exact instant dates use `SOURCE_EXACT`. OpenDART `REPORT_STAGE_ONLY` evidence requires a separate human exact-date assertion. Freshness is independently recomputed, and stale reviewed evidence cannot bind.

v0.8 accepts only validated v0.7 and may replace only `equity.minority_interest`. All earlier material-field decisions remain unchanged. Human approval is still required and the source Draft remains immutable.

See [`docs/MINORITY_INTEREST_FACT_BINDING.md`](docs/MINORITY_INTEREST_FACT_BINDING.md).

## M29 — Complete governed equity handoff / 완전 거버넌스 Equity 인계

M29 removes the largest remaining manual duplication between a fully governed Draft and the historical promotion/admission pipeline.

```text
complete M28 bound Draft result
  = 13/13 DIRECT_BIND
  = 13/13 human-approved
  = 13/13 unique applied diffs
  = unresolved []
        ↓
promotion-candidate-v0.2
        ↓
human promotion review + review_scope_sha256
        ↓
promotion-package-v0.1
        ↓
M29 admission dispatcher
        ↓
M29 guarded repository-plan dispatcher
```

Authority is inherited, not reinvented:

| Input | Class |
|---|---|
| `market_price` | `FACT` |
| `equity.cash` | `NORMALIZED_FACT` |
| `equity.minority_interest` | `NORMALIZED_FACT` |
| `equity.debt` | `DERIVED` |
| `equity.diluted_shares` | `DERIVED` |
| WACC / terminal growth / forecast inputs | `ASSUMPTION` |

The five observed fields require an explicit A/B/C-tier evidence catalog whose values, classes, valuation date, and exact proposal/applied-diff lineage must match the embedded M28 result. Tier D is blocked even for `DERIVED` inputs. Every material numeric path is covered exactly once and no `UNKNOWN` may remain.

The v0.2 candidate preserves the exact M28 `draft_after`. For canonical admission, `SOURCE_PACKAGE.json` retains that exact source package while `case_inputs.json` uses only the deterministic normalized view required by the existing equity adapter. The historical `BEAR / BASE / BULL` canonical profile is not weakened.

M29 prepares and validates admission artifacts and the guarded repository plan, but it does not perform canonical writes. Actual canonicalization still requires the separate `admission/*` PR, full CI, human review, and merge.

See [`docs/COMPLETE_GOVERNED_EQUITY_HANDOFF.md`](docs/COMPLETE_GOVERNED_EQUITY_HANDOFF.md).

## Web product / Web 제품

```bash
vih web
```

Default: `http://127.0.0.1:8765`

```text
/source             — SEC source inspection
/dart-source        — OpenDART source inspection
/normalize          — financial normalization + TTM
/binding            — evidence → Draft binding proposal
/binding-apply      — human approval + in-memory Draft binding
/derived            — governed historical derived evidence
/debt               — governed debt aggregation + binding preparation
/dilution           — historical dilution reference
/shares             — valuation-date common-share base + diluted-share bridge
/share-binding      — complete share bridge → v0.3 proposal
/wacc               — governed WACC candidate/review/v0.4 preparation
/terminal-growth    — terminal-growth candidate/review/v0.5 preparation
/forecast           — integrated forecast candidate/review/v0.6 preparation
/market-price       — market FACT candidate/review/v0.7 preparation
/minority-interest  — minority-interest FACT candidate/review/v0.8 preparation
/equity-handoff     — complete 13/13 governed Draft → promotion-candidate-v0.2 preparation
```

Preparation Labs expose no automatic approval or canonical write. The M29 handoff surface explicitly exposes **NO AUTO APPROVAL · NO FILE WRITE · NO ADMISSION APPLY · NO CANONICAL WRITE**.

## M29 CLI / M29 CLI

`vih` enters through additive `cli_entry_m29`; all predecessor commands delegate through `cli_entry_m28` and the earlier wrapper chain.

```text
complete-handoff-catalog-claim
complete-handoff-build
complete-handoff-assess
candidate-validate
promotion-check
admission-build
admission-validate
admission-plan
admission-plan-validate
web
```

M29's admission commands are successor-aware dispatchers: historical v0.1 behavior remains delegated while v0.2 receives the complete governed handoff path.

## Milestones / 마일스톤

- [x] M1–M23 evidence/Draft/share/debt governance foundation
- [x] M24 governed WACC assumption → `scenario.wacc`
- [x] M25 governed terminal growth → `scenario.terminal_growth`
- [x] M26 integrated six-field forecast assumption → atomic Draft binding
- [x] M27 governed market-price FACT → `market_price`
- [x] M28 governed minority-interest `NORMALIZED_FACT` → `equity.minority_interest`
- [ ] **M29 complete governed equity handoff → promotion/admission bridge — active finalization**
- [ ] first canonical case admitted through the complete M29 handoff
- [ ] first non-equity valuation adapter

## Canonical documentation / 정식 문서

Core governance:
- [`docs/EVIDENCE_POLICY.md`](docs/EVIDENCE_POLICY.md)
- [`docs/USER_DRAFTS.md`](docs/USER_DRAFTS.md)
- [`docs/PROMOTION_PROTOCOL.md`](docs/PROMOTION_PROTOCOL.md)
- [`docs/CANONICAL_ADMISSION.md`](docs/CANONICAL_ADMISSION.md)
- [`docs/GUARDED_ADMISSION_APPLY.md`](docs/GUARDED_ADMISSION_APPLY.md)

Material-input governance:
- [`docs/DEBT_DRAFT_BINDING.md`](docs/DEBT_DRAFT_BINDING.md)
- [`docs/VALUATION_SHARE_BRIDGE.md`](docs/VALUATION_SHARE_BRIDGE.md)
- [`docs/SHARE_DRAFT_BINDING.md`](docs/SHARE_DRAFT_BINDING.md)
- [`docs/WACC_ASSUMPTION_BINDING.md`](docs/WACC_ASSUMPTION_BINDING.md)
- [`docs/TERMINAL_GROWTH_ASSUMPTION_BINDING.md`](docs/TERMINAL_GROWTH_ASSUMPTION_BINDING.md)
- [`docs/FORECAST_SCENARIO_ASSUMPTION_BINDING.md`](docs/FORECAST_SCENARIO_ASSUMPTION_BINDING.md)
- [`docs/MARKET_PRICE_FACT_BINDING.md`](docs/MARKET_PRICE_FACT_BINDING.md)
- [`docs/MINORITY_INTEREST_FACT_BINDING.md`](docs/MINORITY_INTEREST_FACT_BINDING.md)

Complete governed handoff:
- [`docs/COMPLETE_GOVERNED_EQUITY_HANDOFF.md`](docs/COMPLETE_GOVERNED_EQUITY_HANDOFF.md)
- [`docs/M29_ACCEPTANCE.md`](docs/M29_ACCEPTANCE.md)
- [`docs/M29_IMPLEMENTATION_SUMMARY.md`](docs/M29_IMPLEMENTATION_SUMMARY.md)
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — canonical resume point / 정식 재개점
