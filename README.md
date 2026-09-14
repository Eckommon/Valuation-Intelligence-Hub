# Valuation-Intelligence-Hub / 가치분석 인텔리전스 허브

> **Separate price from economic value, make assumptions explicit, and make valuation reproducible.**  
> **가격과 경제적 가치를 분리하고, 가정을 명시하며, 가치평가를 재현 가능하게 만든다.**

Valuation-Intelligence-Hub is a reproducible, evidence-grounded valuation intelligence system connecting source evidence, normalization, governed facts and assumptions, Draft preparation, human review, valuation execution, promotion/admission, and repository-controlled canonicalization.

Valuation-Intelligence-Hub는 출처근거·정규화·거버넌스 FACT/ASSUMPTION·Draft·인간검토·가치평가 실행·승격/수용·저장소 정식화를 하나의 재현 가능한 흐름으로 연결한다.

## Core authority flow / 핵심 권위 흐름

```text
OFFICIAL / USER / EXTERNAL SOURCE
        ↓
IMMUTABLE OR SOURCE-LOCKED INPUT / NOT CANONICAL
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

The active parent mission is Issue **#66**. Target:

```text
Ingredion Incorporated
NYSE: INGR
SEC CIK: 0001046257
Target case ID: US_INGR_INGREDION
```

M30 exists to prove the full M13–M29 lifecycle on real company evidence before expanding valuation breadth.

### Canonical preparation completed

| Slice | Purpose | Canonical main |
|---|---|---|
| M30-A | real-case source-contract preflight | `2034075db50bedb4feb9ec69000f3e1f789c4234` |
| M30-P1 | exact SEC aggregate-debt successor | `11182eeab7e60a90e6ddc140ca05f45e93af7e40` |
| M30-B | real source preflight v0.2 | `a970d74b85e44e617dd604cc829637caaf65420e` |
| M30-C | runtime-safe SEC capture | `30609979d0d06040e7eeec276b8233796bfa48af` |
| M30-D | 13-field readiness manifest + DAG | `fab223354c759e8b961949e8ff85e43d5bbb2ab8` |
| M30-E | immutable non-SEC source ingress | `e4207f0d9077208881f2a63317861e6f39fa8158` |

### Protected SEC runtime boundary

Real SEC CompanyFacts capture requires an identifying fair-access User-Agent containing a contact email. The value is accepted **only** through the runtime environment variable:

```text
SEC_USER_AGENT
```

It must not be invented by AI, inferred from GitHub metadata, committed to the repository, or persisted in a snapshot.

### M30 real execution sequence

```text
real SEC CompanyFacts capture
→ immutable M13 snapshot validation
→ M30-B real source preflight
→ M30-D 13-field readiness manifest
→ explicit review of cash / shares / NCI / aggregate debt paths
→ M30-E immutable non-SEC snapshots for market/macro sources
→ M24/M25/M26/M27/M28 explicit human-review gates
→ complete M28 v0.8 13/13 bound result
→ M29 promotion/admission/guarded plan
→ admission/* branch
→ CI + human review + exact-head merge
→ one real Ingredion canonical case
```

No synthetic fixture may be inserted into `registry/cases.json` to claim end-to-end success.

## M30 CLI / 현재 top-level CLI

Installed `vih` enters through additive `valuation_hub.cli_entry_m30`. Commands not owned by M30 delegate through M29 and the historical wrapper chain.

M30-specific commands include:

```text
sec-companyfacts-fetch
sec-source-snapshot-validate
real-equity-preflight-v2
real-equity-readiness-build
real-equity-readiness-validate
external-source-snapshot-build
external-source-snapshot-validate
market-price-candidate-build-from-snapshot
wacc-source-build-from-snapshot
terminal-growth-anchor-build-from-snapshot
```

Historical M1–M29 commands remain delegated and regression-locked.

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
- [x] M30-A~E real-case architecture and source-ingress preparation
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
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — canonical resume point / 정식 재개점
