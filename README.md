# Valuation-Intelligence-Hub / 가치분석 인텔리전스 허브

> **Separate price from economic value, make assumptions explicit, and make valuation reproducible.**  
> **가격과 경제적 가치를 분리하고, 가정을 명시하며, 가치평가를 재현 가능하게 만든다.**

Valuation-Intelligence-Hub is a reproducible, evidence-grounded valuation intelligence system connecting source evidence, normalization, governed facts and assumptions, typed evidence-first analytical adjudication, Draft preparation, valuation execution, promotion/admission, and repository-controlled canonicalization.

Valuation-Intelligence-Hub는 출처근거·정규화·거버넌스 FACT/ASSUMPTION·근거우선 분석 판단·Draft·가치평가 실행·승격/수용·저장소 정식화를 하나의 재현 가능한 흐름으로 연결한다. 인간 승인은 모든 내부 분석에 일률적으로 요구하지 않으며, 자금·계약·규제제출·계정권한 등 외부 구속효과가 있는 경계에 집중한다.

## Core authority flow / 핵심 권위 흐름

```text
OFFICIAL / USER / EXTERNAL SOURCE
        ↓
IMMUTABLE OR SOURCE-LOCKED INPUT / NOT CANONICAL
        ↓
FACT_CANDIDATE / NORMALIZED FACT / ASSUMPTION_CANDIDATE
        ↓
EVIDENCE-FIRST GOVERNED REVIEW
  (typed AI analytical authority; human where externally binding)
        ↓
GOVERNED FACT / CONTEXT / ASSUMPTION
        ↓
DRAFT BINDING PROPOSAL / NOT CANONICAL
        ↓
GOVERNED APPROVAL / AUTHORITY LOCK
        ↓
BOUND DRAFT RESULT / NOT CANONICAL
        ↓
COMPLETE GOVERNED HANDOFF
        ↓
PROMOTION → ADMISSION → GUARDED APPLY → PR/CI MERGE
        ↓
CANONICAL
```

Deterministic calculation never upgrades authority by itself. `FACT`, `NORMALIZED_FACT`, `DERIVED`, `ASSUMPTION`, human review, Draft binding, promotion, admission, and canonical repository state remain distinct.

## Install / 설치

```bash
python -m pip install -e ".[dev]"
```

## Governed capability map / 거버넌스 기능 지도

- M1–M12: valuation kernels, evidence governance, Draft/Candidate review, promotion/admission, guarded repository apply
- M13: immutable SEC CompanyFacts acquisition
- M14: immutable OpenDART acquisition
- M15: period semantics, normalization, reconciliation, TTM
- M16–M17: normalized evidence → Draft proposal → SHA-locked human approval/application
- M18: governed historical operating/net margin derivation
- M19–M20: debt components, aggregation, reviewed debt → `equity.debt`
- M21–M23: dilution evidence, valuation-date share bridge, reviewed `equity.diluted_shares`
- M24: seven sourced WACC components → reviewed `ASSUMPTION` → `scenario.wacc`
- M25: reviewed WACC + macro anchors → reviewed terminal-growth `ASSUMPTION`
- M26: six FCFF forecast inputs → one atomic reviewed forecast block
- M27: source-backed valuation-date market quote → reviewed `FACT` → `market_price`
- M28: exact noncontrolling-interest evidence → reviewed `NORMALIZED_FACT` → `equity.minority_interest`
- M29: complete 13/13 M28 bound Draft → `promotion-candidate-v0.2` → promotion/admission/guarded plan
- M30-A/B: first-real-case source preflight and exact aggregate-debt successor path
- M30-C: runtime-safe SEC capture interface with runtime-only `SEC_USER_AGENT`
- M30-D: deterministic 13-field readiness manifest + prerequisite DAG
- M30-E: immutable non-SEC source intake + snapshot-bound M27/M24/M25 provenance builders
- M30-R1: additive CLI exposure of the SEC aggregate-debt review lifecycle
- M30-R2/R2.1/R2.2: evidence-first AI analytical authority, AI debt adjudication CLI, reviewer-type provenance truth
- M30-R3: AI authority for SEC cash, current common shares, and explicit-zero NCI
- M30-R4: six-category evidence-first dilution coverage and fully diluted-share bridge
- M30-R5: dual-source-capable evidence-first AI market-price authority
- M30-R4.1: strike-distribution-safe TSM; weighted-average strike cannot stand in for a multi-strike option portfolio

## Key semantic guardrails / 핵심 의미 안전장치

```text
liabilities                         ≠ debt
shares_outstanding                  ≠ diluted_shares
current_common_shares               ≠ fully_diluted_shares
historical dilution factor          ≠ automatic current dilution
weighted-average exercise price     ≠ option strike distribution / portfolio TSM
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
source snapshot                     ≠ reviewed fact
complete bound Draft                ≠ canonical case
FACT_CANDIDATE                      ≠ FACT
ASSUMPTION_CANDIDATE                ≠ ASSUMPTION
reviewed FACT / ASSUMPTION          ≠ canonical state
```

## M29 complete governed handoff / 완전 거버넌스 Equity 인계

M29 defines the complete equity-FCFF bridge:

```text
complete M28 bound Draft result
  = 13/13 DIRECT_BIND
  = 13/13 human-approved
  = 13/13 unique applied diffs
  = unresolved []
        ↓
promotion-candidate-v0.2
        ↓
explicit human promotion review + review_scope_sha256
        ↓
promotion-package-v0.1
        ↓
M29 admission dispatcher
        ↓
M29 guarded repository-plan dispatcher
        ↓
separate admission/* PR + CI + human review + merge
        ↓
CANONICAL CASE
```

Authority mapping:

| Input | Class |
|---|---|
| `market_price` | `FACT` |
| `equity.cash` | `NORMALIZED_FACT` |
| `equity.minority_interest` | `NORMALIZED_FACT` |
| `equity.debt` | `DERIVED` |
| `equity.diluted_shares` | `DERIVED` |
| WACC / terminal growth / forecast inputs | `ASSUMPTION` |

M29 canonical closure:

```text
final tested head: a666d00d45431914fd98deb08f5b336f3c28eeef
final-head CI:     34791253465
merge/main:        97dc84d8e9a09b5bd9c6864137a537037baac4f6
post-merge CI:     34791345455
```

See [`docs/COMPLETE_GOVERNED_EQUITY_HANDOFF.md`](docs/COMPLETE_GOVERNED_EQUITY_HANDOFF.md).

## M30 — First real complete-governed equity case / 첫 실기업 완전 거버넌스 사례

The active parent mission is Issue **#66**. Real execution is Issue **#79**.

```text
Ingredion Incorporated
NYSE: INGR
SEC CIK: 0001046257
Target case ID: US_INGR_INGREDION
```

### Current runtime baseline

`main@aadc8fef8ff3ecb20ad71cbd90809c4e95b69c1f`

Latest runtime slice: **M30-R4.1 — strike-distribution-safe TSM correction**, after M30-R5 market-price authority.

Recent canonical sequence:

| Slice | Canonical main | Post-merge CI |
|---|---|---|
| M30-R2.2 debt reviewer-type truth | `61ab850e58626a6c5ac69abfdb276ac63bc385f9` | `35184077583` |
| M30-R3 SEC observed-field AI authority | `ec92bb4ef5fba2c005004d7b1214cd6a3f3e60a0` | `35247619398` |
| M30-R4 AI dilution coverage | `5bd1d92a9733621393bbada4f301876180647829` | `35256710738` |
| M30-R5 AI market-price authority | `4f8a9c988ee20ddf33585e8810db312821f43698` | `35283190462` |
| M30-R4.1 strike-safe TSM | `aadc8fef8ff3ecb20ad71cbd90809c4e95b69c1f` | `35555025332` |

### Real Ingredion fields already governed

- debt: USD **1.783B**, AI-reviewed and binding-context eligible;
- cash: USD **948M**, AI-reviewed `NORMALIZED_FACT`;
- current common shares: **63,063,979**, AI-reviewed and `FRESH` as the M22 base;
- minority interest: explicit USD **0**, AI-reviewed and eligible.

Current common shares remain **not** fully diluted shares.

### Active next boundary

The real INGR market-price FACT is now governed:

- 2026-09-14 official close: **USD 98.63**
- reviewed package SHA: `607808de5224a84072427a18100e4933600fa4bad84057f9ffae0a7e436b7e9a`
- `review_authority=AI`

The current bottleneck is `equity.diluted_shares`, not market price.

R4.1 requires tranche-safe option TSM. Ingredion publicly reports total options plus weighted-average exercise price, but that is insufficient to reconstruct a multi-strike portfolio. The current real dilution state is therefore:

```text
options_treasury_stock_method = BLOCKED_DEPENDENCY
rsu_restricted_stock          = PRESENT (534,000)
warrants                      = ABSENT_SUPPORTED
convertibles_if_converted     = ABSENT_SUPPORTED
contingent_shares             = BLOCKED_DEPENDENCY
other_explicit                = BLOCKED_DEPENDENCY
```

The three unresolved evidence gaps are option strike distribution, point-in-time payout-weighted performance awards, and point-in-time director/deferred equity. Historical diluted-EPS averages and weighted-average option strike shortcuts may not substitute for those missing valuation-date facts.

### Authority policy

Internal accounting/valuation interpretation may be AI-approved only after exact provenance, semantic criteria, cross-check and contradiction search succeed. Human approval is reserved for externally binding/irreversible actions such as funds movement, paid commitments, contracts/legal attestations, regulatory submissions, credentials/accounts/permissions, or secret disclosure.

No synthetic fixture may be inserted into `registry/cases.json` to claim completion.

## M30-R5 CLI / 현재 top-level CLI

Installed `vih` enters through `valuation_hub.cli_entry_m30r5` and delegates older commands unchanged.

R5 adds:

```text
market-price-ai-evidence-build
market-price-ai-evidence-validate
market-price-ai-adjudicate
market-price-ai-adjudication-validate
market-price-ai-finalize
market-price-ai-package-validate
```

R4 adds:

```text
dilution-ai-inventory-build
dilution-ai-inventory-validate
dilution-ai-adjudicate
dilution-ai-adjudication-validate
dilution-ai-finalize
dilution-ai-package-validate
```

M30/M30-R1/R2/R3 source, debt, SEC-observed-field and readiness commands remain available through delegation.

See `PROJECT_STATE.md` for exact real-case SHA lineage and the current resume point.

## Web product / Web 제품

```bash
vih web
```

Default: `http://127.0.0.1:8765`

Representative preparation surfaces:

```text
/source             — SEC source inspection
/dart-source        — OpenDART source inspection
/normalize          — financial normalization + TTM
/binding            — evidence → Draft binding proposal
/debt               — governed debt aggregation
/shares             — valuation-date share bridge
/wacc               — governed WACC preparation
/terminal-growth    — terminal-growth preparation
/forecast           — integrated forecast preparation
/market-price       — market-price FACT preparation
/minority-interest  — NCI preparation
/equity-handoff     — complete 13/13 Draft → promotion-candidate preparation
```

Preparation surfaces do not auto-approve or perform canonical repository writes.

## Milestones / 마일스톤

- [x] M1–M23 evidence/Draft/share/debt governance foundation
- [x] M24–M28 complete material-input governance
- [x] M29 complete governed equity handoff
- [x] M30-A~E + M30-S real-case architecture/source-ingress/state preparation
- [x] real Ingredion SEC source capture, M30-B preflight, and M30-D readiness validation
- [ ] complete remaining evidence-first source/assumption gates, including an explicit resolution of public dilution-data insufficiency
- [ ] **first real Ingredion canonical case through complete M29 handoff**
- [ ] first non-equity valuation adapter

Do not begin the non-equity adapter before M30 real-case proof unless a new repository-grounded architectural blocker requires it.

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

Complete handoff and M30:
- [`docs/COMPLETE_GOVERNED_EQUITY_HANDOFF.md`](docs/COMPLETE_GOVERNED_EQUITY_HANDOFF.md)
- [`docs/M30_D_REAL_CASE_READINESS.md`](docs/M30_D_REAL_CASE_READINESS.md)
- [`docs/M30_E_EXTERNAL_SOURCE_INTAKE.md`](docs/M30_E_EXTERNAL_SOURCE_INTAKE.md)
- [`docs/M30_R1_SEC_AGGREGATE_DEBT_CLI.md`](docs/M30_R1_SEC_AGGREGATE_DEBT_CLI.md)
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — canonical resume point / 정식 재개점
