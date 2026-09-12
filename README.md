# Valuation-Intelligence-Hub / 가치분석 인텔리전스 허브

> **Separate price from economic value, make assumptions explicit, and make valuation reproducible.**  
> **가격과 경제적 가치를 분리하고, 가정을 명시하며, 가치평가를 재현 가능하게 만든다.**

Valuation-Intelligence-Hub is a reproducible, evidence-grounded cross-asset valuation intelligence system connecting source evidence, normalization, governed derivation, explicit valuation assumptions, Draft preparation, human review, and repository-controlled canonicalization.

## Core authority flow / 핵심 권위 흐름

```text
OFFICIAL / USER SOURCE
        ↓
IMMUTABLE SNAPSHOT / NOT CANONICAL
        ↓
EVIDENCE / SOURCE INPUT / NOT CANONICAL
        ↓
NORMALIZED / DERIVED EVIDENCE or ASSUMPTION_CANDIDATE
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

Deterministic calculation does not automatically upgrade authority. Facts, assumptions, review decisions, Draft binding, and canonical repository state remain distinct.

## Valuation kernel / 가치평가 커널

\[
FCFF = EBIT(1-T) + D\&A - CAPEX - \Delta NWC
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

## M21–M23 share semantics / 주식수 의미계약

```text
shares_outstanding != diluted_shares
current_common_shares != fully_diluted_shares
weighted_average_diluted_shares != valuation_date_fully_diluted_shares
historical_dilution_factor != automatic current dilution adjustment
missing dilution category != zero
candidate bridge total != binding authority
```

M21 keeps historical EPS denominators reference-only. M22 builds the valuation-date common-share base and explicit dilution adjustments. M23 allows only a complete, reviewed, fresh M22 bridge to replace `equity.diluted_shares` in a v0.3 proposal while preserving all prior cash/debt decisions.

See:
- [`docs/SHARE_DILUTION_REFERENCE.md`](docs/SHARE_DILUTION_REFERENCE.md)
- [`docs/VALUATION_SHARE_BRIDGE.md`](docs/VALUATION_SHARE_BRIDGE.md)
- [`docs/SHARE_DRAFT_BINDING.md`](docs/SHARE_DRAFT_BINDING.md)

## M24 — Governed WACC assumption / 거버넌스 WACC 가정

WACC is deliberately modeled as a **valuation assumption**, not a historical fact.

```text
source facts / sourced assumptions
        ↓
ASSUMPTION_CANDIDATE
        ↓
SHA-locked human WACC review
        ↓
ASSUMPTION
        ↓
draft-binding-proposal-v0.4
        ↓
scenario.wacc DIRECT_BIND
```

### Required WACC inputs / 필수 입력

Canonical v0.1 uses exactly seven sourced components:

```text
risk_free_rate
equity_risk_premium
levered_beta
pre_tax_cost_of_debt
equity_market_value
debt_market_value
tax_rate
```

Each record carries claim class, value/unit, observation date, publisher, source type/tier, locator, source SHA, and its own integrity SHA.

### WACC method / WACC 방법론

```text
cost_of_equity = rf + beta × ERP
after_tax_cost_of_debt = Rd × (1 - T)
weight_equity = E / (D + E)
weight_debt = D / (D + E)
WACC = weight_equity × cost_of_equity
     + weight_debt × after_tax_cost_of_debt
```

Validators independently recompute every calculated field. Missing/nonfinite arithmetic cannot be legitimized by recomputing only the outer SHA.

### Freshness / 최신성

```text
risk-free rate       30 days
ERP                  90 days
levered beta        180 days
pre-tax debt cost   180 days
equity market value  30 days
debt market value   550 days
tax rate             550 days
```

Stale required inputs block review. Tier D is exploratory and cannot become a reviewed WACC package in v0.1.

### Human review / 인간검토

A separate `wacc-review-assertion-v0.1` locks the exact candidate SHA, methodology, valuation `as_of`, scenario targets, reviewer, approval timestamp, and review basis. Approval cannot predate valuation `as_of`.

Only the resulting `reviewed-wacc-assumption-v0.1` has:

```text
class = ASSUMPTION
binding_eligibility.eligible = true
```

### v0.4 binding / v0.4 바인딩

M24 wraps a validated v0.1, v0.2, or v0.3 proposal and may replace **only**:

```text
scenario.wacc
```

Every other cash/debt/diluted-share and unresolved decision must remain identical to the embedded base proposal.

At M17 approval time, the WACC package's `scenario_names` must exactly equal the Draft's full scenario set. Partial scenario overwrite is prohibited in v0.1.

Applied WACC diffs preserve:

```text
source_package_sha256
review_assertion_sha256
scenario_names
```

The source Draft remains unchanged; the bound result remains noncanonical.

See [`docs/WACC_ASSUMPTION_BINDING.md`](docs/WACC_ASSUMPTION_BINDING.md).

## Key semantic guardrails / 핵심 의미 안전장치

```text
liabilities                         ≠ debt
REPORT_STAGE_ONLY                   ≠ exact date
historical margin                   ≠ forecast margin
historical revenue                  ≠ forecast revenue
calculated WACC                     ≠ reviewed WACC assumption
reviewed WACC assumption            ≠ historical fact
ASSUMPTION_CANDIDATE                ≠ ASSUMPTION
stale/Tier-D WACC input             ≠ review eligible
partial scenario targeting          ≠ scenario.wacc DIRECT_BIND
```

## Web product / Web 제품

```bash
vih web
```

Default: `http://127.0.0.1:8765`

```text
/source         — SEC source inspection
/dart-source    — OpenDART source inspection
/normalize      — financial normalization + TTM
/binding        — evidence → Draft binding proposal
/binding-apply  — human approval + in-memory Draft binding
/derived        — governed historical derived evidence
/debt           — governed debt aggregation + binding preparation
/dilution       — historical dilution reference
/shares         — valuation-date common-share base + diluted-share bridge
/share-binding  — complete share bridge → v0.3 proposal
/wacc           — governed WACC candidate/review/v0.4 preparation
```

`/wacc` is calculate/validate only. It exposes no M24 Draft apply, file write, promotion, admission, or canonical-write endpoint.

## M24 CLI

M24 uses an additive wrapper: old M1–M23 commands delegate unchanged to the previous dispatcher.

```text
wacc-source-build
wacc-source-validate
wacc-candidate-build
wacc-candidate-validate
wacc-review-build
wacc-review-validate
wacc-finalize
wacc-validate
binding-build-with-wacc
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
- [ ] **M24 governed WACC assumption → `scenario.wacc` binding — active finalization**
- [ ] remaining equity-FCFF material assumptions/inputs
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
- [`docs/M23_ACCEPTANCE.md`](docs/M23_ACCEPTANCE.md)
- [`docs/M23_IMPLEMENTATION_SUMMARY.md`](docs/M23_IMPLEMENTATION_SUMMARY.md)
- [`docs/M24_ACCEPTANCE.md`](docs/M24_ACCEPTANCE.md)
- [`docs/M24_IMPLEMENTATION_SUMMARY.md`](docs/M24_IMPLEMENTATION_SUMMARY.md)
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — canonical resume point / 정식 재개점
