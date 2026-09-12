# Valuation-Intelligence-Hub / 가치분석 인텔리전스 허브

> **Separate price from economic value, make assumptions explicit, and make valuation reproducible.**  
> **가격과 경제적 가치를 분리하고, 가정을 명시하며, 가치평가를 재현 가능하게 만든다.**

Valuation-Intelligence-Hub is a reproducible, evidence-grounded cross-asset valuation intelligence system connecting source evidence, normalization, governed derivation, explicit valuation assumptions, Draft preparation, human review, and repository-controlled canonicalization.

## Core authority flow / 핵심 권위 흐름

```text
OFFICIAL / USER SOURCE
        ↓
IMMUTABLE / SOURCE-LOCKED INPUT / NOT CANONICAL
        ↓
FACT / NORMALIZED FACT / ASSUMPTION_CANDIDATE
        ↓
HUMAN-REVIEWED GOVERNED CONTEXT / ASSUMPTION
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

Deterministic calculation never upgrades authority by itself. Facts, assumptions, review decisions, Draft binding, and canonical repository state remain distinct.

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
- M26: six FCFF forecast inputs → one reviewed integrated scenario `ASSUMPTION` → atomic forecast Draft binding

## Share semantics / 주식수 의미계약

```text
shares_outstanding != diluted_shares
current_common_shares != fully_diluted_shares
weighted_average_diluted_shares != valuation_date_fully_diluted_shares
historical_dilution_factor != automatic current dilution adjustment
missing dilution category != zero
candidate bridge total != binding authority
```

M21 keeps historical EPS denominators reference-only. M22 builds the valuation-date common-share base and explicit dilution adjustments. M23 permits only a complete, reviewed, fresh M22 bridge to replace `equity.diluted_shares`.

See:
- [`docs/SHARE_DILUTION_REFERENCE.md`](docs/SHARE_DILUTION_REFERENCE.md)
- [`docs/VALUATION_SHARE_BRIDGE.md`](docs/VALUATION_SHARE_BRIDGE.md)
- [`docs/SHARE_DRAFT_BINDING.md`](docs/SHARE_DRAFT_BINDING.md)

## M24 — Governed WACC assumption / 거버넌스 WACC 가정

WACC is a **valuation assumption**, not a historical fact.

```text
7 explicit sourced components
        ↓
ASSUMPTION_CANDIDATE
        ↓
SHA-locked human WACC review
        ↓
reviewed ASSUMPTION
        ↓
draft-binding-proposal-v0.4
        ↓
scenario.wacc DIRECT_BIND
```

Required components are risk-free rate, ERP, levered beta, pre-tax cost of debt, equity market value, debt market value, and tax rate. Validators independently recompute CAPM cost of equity, after-tax debt cost, capital weights, freshness, authority, and final WACC.

M24 may replace only `scenario.wacc`, and the target scenario set must exactly equal the full Draft scenario set.

See [`docs/WACC_ASSUMPTION_BINDING.md`](docs/WACC_ASSUMPTION_BINDING.md).

## M25 — Governed terminal-growth assumption / 거버넌스 영구성장률 가정

Terminal growth is also a valuation `ASSUMPTION`.

```text
reviewed M24 WACC package
        +
long_run_inflation + long_run_real_growth
        +
explicit scenario g + rationale
        ↓
ASSUMPTION_CANDIDATE → human review → ASSUMPTION
        ↓
draft-binding-proposal-v0.5
        ↓
scenario.terminal_growth DIRECT_BIND
```

Nominal macro ceiling:

```text
nominal_growth_anchor = (1 + inflation) × (1 + real_growth) - 1
```

M25 enforces:

```text
g > -1
g < reviewed WACC
g <= nominal_growth_anchor
```

The terminal-growth package must depend on the exact reviewed WACC package already embedded in v0.4. Terminal growth may be applied only when that WACC is already in the Draft or is approved together.

See [`docs/TERMINAL_GROWTH_ASSUMPTION_BINDING.md`](docs/TERMINAL_GROWTH_ASSUMPTION_BINDING.md).

## M26 — Integrated FCFF forecast / 통합 FCFF Forecast

M26 treats the six explicit forecast-year inputs as **one atomic valuation-assumption block**:

```text
scenario.years.revenue
scenario.years.ebit_margin
scenario.years.tax_rate
scenario.years.depreciation_amortization
scenario.years.capex
scenario.years.delta_nwc
```

```text
explicit scenario rows + rationale
        ↓
ASSUMPTION_CANDIDATE
        ↓
independent EBIT / NOPAT / FCFF diagnostics
        ↓
SHA-locked human review
        ↓
reviewed ASSUMPTION
        ↓
draft-binding-proposal-v0.6
        ↓
all-six-or-none Draft binding
```

All scenarios must use the same ordered future-year set. M26 does not silently create, delete, or reorder Draft years. Historical facts and deterministic diagnostics may inform review but never become forecast authority automatically.

모든 시나리오는 동일한 미래 연도집합을 사용해야 하며 M26은 Draft의 연도를 암묵적으로 생성·삭제·재정렬하지 않는다. 과거 사실과 진단계산은 검토를 보조할 뿐 Forecast 권위를 자동 생성하지 않는다.

M26 accepts only a validated v0.5 base and replaces exactly the six forecast decisions. WACC, terminal growth, cash, debt, diluted shares, conflicts, and all other base decisions remain unchanged.

### Atomic result integrity / 원자적 결과 무결성

Bound-result validation requires:

```text
unique(applied_diff.field)
AND
set(applied_diff.field) == set(approved_fields)
```

This prevents a re-signed result from repeating one valid diff while omitting another approved field.

See [`docs/FORECAST_SCENARIO_ASSUMPTION_BINDING.md`](docs/FORECAST_SCENARIO_ASSUMPTION_BINDING.md).

## Key semantic guardrails / 핵심 의미 안전장치

```text
liabilities                         ≠ debt
REPORT_STAGE_ONLY                   ≠ exact date
historical margin                   ≠ forecast margin
historical revenue                  ≠ forecast revenue
calculated WACC                     ≠ reviewed WACC assumption
reviewed WACC assumption            ≠ historical fact
macro growth anchor                 ≠ terminal-growth fact
selected terminal growth            ≠ reviewed terminal-growth assumption
calculated EBIT/NOPAT/FCFF          ≠ forecast authority
ASSUMPTION_CANDIDATE                ≠ ASSUMPTION
stale/Tier-D required input         ≠ review eligible
g >= WACC                           ≠ valid Gordon terminal state
g > nominal macro anchor            ≠ v0.1 review eligible
partial scenario targeting          ≠ governed scenario binding
partial six-field forecast approval ≠ governed forecast binding
```

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
```

`/wacc`, `/terminal-growth`, and `/forecast` are calculate/validate preparation surfaces. They expose no direct Draft apply, file write, promotion, admission, or canonical-write endpoint.

## M26 CLI / M26 CLI

M26 uses an additive wrapper. All M1–M25 commands delegate unchanged to the previous dispatcher.

```text
forecast-candidate-build
forecast-candidate-validate
forecast-review-build
forecast-review-validate
forecast-finalize
forecast-validate
binding-build-with-forecast
binding-validate
```

Existing M17 `binding-approval-*`, `binding-apply`, and `bound-draft-validate` commands continue to provide the human approval/apply stage.

## Milestones / 마일스톤

- [x] M1–M12 valuation/evidence governance + canonical admission/apply
- [x] M13 immutable SEC acquisition
- [x] M14 immutable OpenDART acquisition
- [x] M15 financial normalization + TTM
- [x] M16 governed evidence → Draft binding proposal
- [x] M17 human-approved noncanonical Draft binding application
- [x] M18 governed derived financial evidence + historical margins
- [x] M19 governed interest-bearing debt components + aggregation
- [x] M20 reviewed debt → `equity.debt` binding
- [x] M21 governed historical dilution reference
- [x] M22 valuation-date common-share base + diluted-share bridge
- [x] M23 complete reviewed bridge → `equity.diluted_shares` binding
- [x] M24 governed WACC assumption → `scenario.wacc` binding
- [x] M25 governed terminal-growth assumption → `scenario.terminal_growth` binding
- [ ] **M26 integrated forecast scenario package → six-field atomic Draft binding — active finalization**
- [ ] remaining `market_price` / `equity.minority_interest` material gaps
- [ ] first non-equity valuation adapter

## Canonical documentation / 정식 문서

- [`docs/EVIDENCE_POLICY.md`](docs/EVIDENCE_POLICY.md)
- [`docs/USER_DRAFTS.md`](docs/USER_DRAFTS.md)
- [`docs/PROMOTION_PROTOCOL.md`](docs/PROMOTION_PROTOCOL.md)
- [`docs/CANONICAL_ADMISSION.md`](docs/CANONICAL_ADMISSION.md)
- [`docs/GUARDED_ADMISSION_APPLY.md`](docs/GUARDED_ADMISSION_APPLY.md)
- [`docs/LIVE_EVIDENCE_SEC.md`](docs/LIVE_EVIDENCE_SEC.md)
- [`docs/LIVE_EVIDENCE_OPENDART.md`](docs/LIVE_EVIDENCE_OPENDART.md)
- [`docs/FINANCIAL_NORMALIZATION.md`](docs/FINANCIAL_NORMALIZATION.md)
- [`docs/DRAFT_BINDING.md`](docs/DRAFT_BINDING.md)
- [`docs/BINDING_APPLICATION.md`](docs/BINDING_APPLICATION.md)
- [`docs/INTEREST_BEARING_DEBT.md`](docs/INTEREST_BEARING_DEBT.md)
- [`docs/DEBT_DRAFT_BINDING.md`](docs/DEBT_DRAFT_BINDING.md)
- [`docs/SHARE_DILUTION_REFERENCE.md`](docs/SHARE_DILUTION_REFERENCE.md)
- [`docs/VALUATION_SHARE_BRIDGE.md`](docs/VALUATION_SHARE_BRIDGE.md)
- [`docs/SHARE_DRAFT_BINDING.md`](docs/SHARE_DRAFT_BINDING.md)
- [`docs/WACC_ASSUMPTION_BINDING.md`](docs/WACC_ASSUMPTION_BINDING.md)
- [`docs/TERMINAL_GROWTH_ASSUMPTION_BINDING.md`](docs/TERMINAL_GROWTH_ASSUMPTION_BINDING.md)
- [`docs/FORECAST_SCENARIO_ASSUMPTION_BINDING.md`](docs/FORECAST_SCENARIO_ASSUMPTION_BINDING.md)
- [`docs/M24_ACCEPTANCE.md`](docs/M24_ACCEPTANCE.md)
- [`docs/M25_ACCEPTANCE.md`](docs/M25_ACCEPTANCE.md)
- [`docs/M26_ACCEPTANCE.md`](docs/M26_ACCEPTANCE.md)
- [`docs/M26_IMPLEMENTATION_SUMMARY.md`](docs/M26_IMPLEMENTATION_SUMMARY.md)
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — canonical resume point / 정식 재개점
