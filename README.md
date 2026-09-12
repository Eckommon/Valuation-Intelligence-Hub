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
DRAFT GOVERNANCE → PROMOTION → ADMISSION → guarded apply → PR/CI merge
        ↓
CANONICAL
```

Deterministic calculation never upgrades authority by itself. `FACT`, `ASSUMPTION`, human review, Draft binding, and canonical repository state remain distinct.

결정론적 계산만으로 권위가 승격되지 않는다. `FACT`, `ASSUMPTION`, 인간검토, Draft 바인딩, canonical 저장소 상태는 분리된다.

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

## Key semantic guardrails / 핵심 의미 안전장치

```text
liabilities                         ≠ debt
shares_outstanding                  ≠ diluted_shares
current_common_shares               ≠ fully_diluted_shares
weighted_average_diluted_shares     ≠ valuation-date fully diluted shares
historical dilution factor          ≠ automatic current dilution
historical revenue                  ≠ forecast revenue
historical margin                   ≠ forecast margin
calculated WACC                     ≠ reviewed WACC assumption
macro growth anchor                 ≠ terminal-growth fact
calculated EBIT/NOPAT/FCFF          ≠ forecast authority
quoted number without provenance    ≠ governed market-price fact
historical adjusted price           ≠ valuation-date market price
FACT_CANDIDATE                      ≠ FACT
ASSUMPTION_CANDIDATE                ≠ ASSUMPTION
reviewed FACT / ASSUMPTION          ≠ canonical state
```

## M24–M26 governed valuation assumptions / M24–M26 가치평가 가정 거버넌스

### WACC

Seven explicit sourced components are combined under a fixed methodology, independently recomputed, and then human-reviewed. WACC remains an `ASSUMPTION`, never a historical fact.

See [`docs/WACC_ASSUMPTION_BINDING.md`](docs/WACC_ASSUMPTION_BINDING.md).

### Terminal growth

Terminal growth is reviewed against the exact WACC lineage and explicit long-run inflation/real-growth anchors.

```text
g > -1
g < reviewed WACC
g <= nominal macro anchor
```

See [`docs/TERMINAL_GROWTH_ASSUMPTION_BINDING.md`](docs/TERMINAL_GROWTH_ASSUMPTION_BINDING.md).

### Integrated forecast

M26 governs these six fields as one atomic assumption block:

```text
scenario.years.revenue
scenario.years.ebit_margin
scenario.years.tax_rate
scenario.years.depreciation_amortization
scenario.years.capex
scenario.years.delta_nwc
```

Partial approval is forbidden. Bound-result validation also requires unique diff fields exactly equal to approved fields.

See [`docs/FORECAST_SCENARIO_ASSUMPTION_BINDING.md`](docs/FORECAST_SCENARIO_ASSUMPTION_BINDING.md).

## M27 — Governed valuation-date market price / 거버넌스 가치평가일 시장가격

Market price is an observed market `FACT`, not a valuation assumption.

```text
source-backed exact as-traded quote
        ↓
FACT_CANDIDATE
        ↓
SHA-locked human review
        ↓
reviewed noncanonical FACT
        ↓
draft-binding-proposal-v0.7
        ↓
market_price DIRECT_BIND
```

v0.1 requires explicit:

- positive price per share
- quote currency
- exact trading date
- timezone-aware quote timestamp
- instrument ID + symbol
- venue
- `OFFICIAL_CLOSE` or `LAST_TRADE`
- `AS_TRADED_PER_SHARE` price basis
- valuation `as_of`
- Tier A/B source provenance and source snapshot SHA for review eligibility

Freshness is recomputed from trading date. A trading date after `as_of`, stale quote, unsupported quote type, lower source tier, currency mismatch, identity mismatch, or as-of mismatch fails closed.

Human review must occur **after the quote observation**:

```text
approved_at >= observed_at
```

Historical price substitution and silent split adjustment are forbidden in M27 v0.1.

M27 accepts only a validated v0.6 proposal and may replace only the top-level:

```text
market_price
```

All cash, debt, diluted-share, WACC, terminal-growth, and forecast decisions remain unchanged.

See [`docs/MARKET_PRICE_FACT_BINDING.md`](docs/MARKET_PRICE_FACT_BINDING.md).

## Web product / Web 제품

```bash
vih web
```

Default: `http://127.0.0.1:8765`

```text
/source           — SEC source inspection
/dart-source      — OpenDART source inspection
/normalize        — financial normalization + TTM
/binding          — evidence → Draft binding proposal
/binding-apply    — human approval + in-memory Draft binding
/derived          — governed historical derived evidence
/debt             — governed debt aggregation + binding preparation
/dilution         — historical dilution reference
/shares           — valuation-date common-share base + diluted-share bridge
/share-binding    — complete share bridge → v0.3 proposal
/wacc             — governed WACC candidate/review/v0.4 preparation
/terminal-growth  — governed terminal-growth candidate/review/v0.5 preparation
/forecast         — integrated forecast candidate/review/v0.6 preparation
/market-price     — market FACT candidate/review/v0.7 preparation
```

M27 `/market-price` and `/api/market-price/*` are preparation/validation surfaces only. No direct Draft apply, file write, promotion, admission, or canonical-write endpoint is exposed there.

## M27 CLI / M27 CLI

`vih` now enters through the additive M27 dispatcher. All M1–M26 commands delegate unchanged.

```text
market-price-candidate-build
market-price-candidate-validate
market-price-review-build
market-price-review-validate
market-price-finalize
market-price-validate
binding-build-with-market-price
binding-validate
```

Existing human approval/apply commands remain the only Draft application stage.

## Milestones / 마일스톤

- [x] M1–M23 evidence/Draft/share/debt governance foundation
- [x] M24 governed WACC assumption → `scenario.wacc`
- [x] M25 governed terminal growth → `scenario.terminal_growth`
- [x] M26 integrated six-field forecast assumption → atomic Draft binding
- [ ] **M27 governed market-price FACT → `market_price` binding — active finalization**
- [ ] `equity.minority_interest` remaining material-field governance
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

Current milestone:
- [`docs/M27_ACCEPTANCE.md`](docs/M27_ACCEPTANCE.md)
- [`docs/M27_IMPLEMENTATION_SUMMARY.md`](docs/M27_IMPLEMENTATION_SUMMARY.md)
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — canonical resume point / 정식 재개점
