# Project State / 프로젝트 상태

> Canonical human-and-AI handoff. Repository-grounded state outranks chat or AI recollection.  
> 인간·AI 공통 정식 인계 문서. 저장소 근거 상태는 채팅·AI 기억보다 우선한다.

## Repository / 저장소

- `Eckommon/Valuation-Intelligence-Hub`
- Purpose: reproducible, evidence-grounded cross-asset valuation intelligence / 재현 가능한 근거 기반 범자산 가치분석 인텔리전스

## Current runtime-canonical baseline / 현재 runtime 정식 기준선

M30-R1 is canonical on:

`main@210095f9ee491fa8a561273a744b6fd194fd9adc`

This merge contains M1–M29, M30-A/P1/B/C/D/E/S, the real-Ingredion execution state through M30-D, and the additive M30-R1 aggregate-debt CLI surface.

State-only descendants created solely to reconcile this document do not change runtime behavior; `210095f9ee491fa8a561273a744b6fd194fd9adc` remains the runtime baseline until a later runtime PR merges.

Active missions:
- Parent M30: Issue **#66**
- Real execution: Issue **#79**
- M30-R1 runtime child: Issue **#80 — COMPLETE**
- M30-R1 state reconciliation: Issue **#82**

Target:

```text
Ingredion Incorporated
Ticker: INGR
Venue: NYSE
SEC CIK: 0001046257
Case ID: US_INGR_INGREDION
```

No synthetic fixture may be inserted into `registry/cases.json` to claim real-case success.

## Canonical milestone lineage / 정식 마일스톤 계보

| Milestone | Main commit | Issue |
|---|---|---:|
| M20 Reviewed debt → `equity.debt` | `236547512919b5d68e283b3431183f56f5fc845c` | #44 |
| M21 Historical dilution reference | `03af933835b8fbcf9ef4e6b3fd1b3db7603782fc` | #46 |
| M22 Valuation-date share bridge | `0a476cc9927b2d63164143447428f3e69b06051b` | #48 |
| M23 Complete share bridge → `equity.diluted_shares` | `58d963238992f562c89c8325b42046ae35ac71bf` | #50 |
| M24 Governed WACC → `scenario.wacc` | `ca85f04c1bd84c5189f78c81e2653cc4f65bccca` | #52 |
| M25 Governed terminal growth | `0c0a7591a59f163fa34aba54fdeb6001fb9b7dc0` | #54 |
| M26 Integrated six-field forecast | `130363475139fe6ea30d00d615f387b440a23c71` | #56 |
| M27 Governed market price | `3a5f2742acd11756a78579e8fd8ba8709a267327` | #58 |
| M28 Governed minority interest | `db5d8e835455de9e52bc656b1ddb4c352736768b` | #60 |
| M29 Complete governed equity handoff | `97dc84d8e9a09b5bd9c6864137a537037baac4f6` | #62 |
| M30-A Real-case source preflight | `2034075db50bedb4feb9ec69000f3e1f789c4234` | #66 |
| M30-P1 Exact SEC aggregate-debt successor | `11182eeab7e60a90e6ddc140ca05f45e93af7e40` | #68 |
| M30-B Real-source preflight v0.2 | `a970d74b85e44e617dd604cc829637caaf65420e` | #66 |
| M30-C Runtime-safe SEC capture | `30609979d0d06040e7eeec276b8233796bfa48af` | #71 |
| M30-D 13-field readiness DAG | `fab223354c759e8b961949e8ff85e43d5bbb2ab8` | #73 |
| M30-E Immutable non-SEC source ingress | `e4207f0d9077208881f2a63317861e6f39fa8158` | #75 |
| M30-S Canonical M30 state reconciliation | `5217462cc17937d9684374b363cc7472c8164d4a` | #77 |
| M30-R1 Governed aggregate-debt CLI | `210095f9ee491fa8a561273a744b6fd194fd9adc` | #80 |

Earlier M1–M19 milestones remain completed and regression-locked in repository history.

## M29 canonical handoff contract / M29 정식 인계 계약

M29 is complete and defines the eventual real-case admission path:

```text
complete M28 v0.8 bound result
  = 13/13 DIRECT_BIND
  = 13/13 human-approved
  = 13/13 unique applied diffs
  = unresolved []
        ↓
promotion-candidate-v0.2
        ↓
explicit human promotion review
        ↓
promotion-package-v0.1
        ↓
admission bundle
        ↓
guarded repository plan
        ↓
separate admission/* PR + CI + human review + exact-head merge
        ↓
CANONICAL CASE
```

M29 closure evidence:
- tested head `a666d00d45431914fd98deb08f5b336f3c28eeef`
- CI `34791253465`
- merge/main `97dc84d8e9a09b5bd9c6864137a537037baac4f6`
- post-merge CI `34791345455`

## M30 preparation / M30 준비

M30-A/P1/B/C/D/E/S are complete.

- exact aggregate debt source concept: `us-gaap:DebtLongtermAndShorttermCombinedAmount`
- SEC User-Agent is accepted only from runtime `SEC_USER_AGENT` and is not persisted
- readiness contract covers exactly 13 material fields and a 31-node prerequisite DAG
- non-SEC M27/M24/M25 source bytes use immutable local UTF-8 intake and snapshot-bound provenance
- architecture preparation is no longer the blocker; the active work is real Ingredion execution

## M30-R real Ingredion execution / 실제 Ingredion 실행

Issue **#79** remains active.

### Real SEC source — PASS

```text
CIK:                  0001046257
snapshot_sha256:      57b61f2b535b446664a240228f00020b859052f384488441849da83f0ceebf32
body_sha256:          53e524af4fe360cdf8eed3ee3055c87ff7abae5eb7e2053ff291667f5fb90745
status:               PASS_SOURCE_SNAPSHOT_VALIDATION
user_agent_persisted: false
canonical:            false
```

Raw source remains user-local under gitignored `workspace/source_snapshots/**`.

### M30-B real preflight — PASS

```text
schema:              real-equity-source-preflight-v0.2
preflight_sha256:    69a458b319ecf89688e2e72439932afbb1057c9f3d1f4f6c8331402202af6773
status:              PASS_REAL_EQUITY_SOURCE_PREFLIGHT
blockers:            []
registry collision:  false
next_action:         CONTINUE_TO_HUMAN_DEBT_SEMANTIC_REVIEW
```

Real source candidates are proven for:
- cash
- current common shares
- minority interest, including explicit reported zero
- exact aggregate debt

Candidate existence does not imply review approval.

### M30-D real readiness — PASS

```text
schema:          real-equity-readiness-manifest-v0.1
manifest_sha256: 6066ef813b2466bdc525ea9ab2b6b9948068a0cb7b59b5630274885499647a40
status:          REAL_EQUITY_READINESS_EVALUATED
decision:        HOLD_AT_GOVERNED_BOUNDARIES
validation:      PASS_REAL_EQUITY_READINESS_MANIFEST_VALIDATION
blockers:        0
material fields: 13
DAG nodes:       31
```

Field states:

```text
AWAITING_HUMAN_REVIEW = 4
AWAITING_REAL_SOURCE  = 2
AWAITING_DEPENDENCY   = 7
```

Human-review boundary:
- `equity.cash`
- `equity.diluted_shares`
- `equity.debt`
- `equity.minority_interest`

Still awaiting real non-SEC source:
- `market_price`
- `scenario.wacc`

Terminal growth and the six forecast fields remain dependency-bound.

## M30-R1 governed debt CLI — CANONICAL COMPLETE

Real execution exposed that M30-P1's governed aggregate-debt lifecycle existed in Python but was not reachable through installed `vih`. Issue **#80** / PR **#81** fixed only this operability gap.

Canonical evidence:

```text
initial failing CI: 35004811782
  result: 427 passed / 4 failed
  cause: four stale interface tests hard-coded cli_entry_m30 as forever-latest
  M30-R1 lifecycle failures: 0

corrected intermediate head: eda067ad055e10d885d4f9e7c308847f0e3caebe
CI: 35005018129 → Python 3.11/3.12 success

final tested head: b06a816a93bec722e948030ff0d839a1e464f1f7
exact-head CI:    35005420900 → Python 3.11/3.12 success
expected-head PR: #81
merge/main:       210095f9ee491fa8a561273a744b6fd194fd9adc
post-merge CI:    35005558446 → Python 3.11/3.12 success
Issue #80:        completed
```

Installed `vih` now enters through `valuation_hub.cli_entry_m30r1` and delegates non-M30-R1 commands unchanged through `M30 → M29 → ...`.

New governed commands:

```text
sec-aggregate-debt-extract
sec-aggregate-debt-candidate-validate
sec-aggregate-debt-normalize
sec-aggregate-debt-observation-validate
sec-aggregate-debt-review-build
sec-aggregate-debt-review-validate
sec-aggregate-debt-finalize
sec-aggregate-debt-profile-validate
sec-aggregate-debt-context-build
sec-aggregate-debt-context-validate
binding-sec-aggregate-debt-build
binding-sec-aggregate-debt-validate
```

The core M30-P1 semantic contract was not relaxed.

## Authority model / 권위 모델

```text
market_price               → FACT
equity.cash                → NORMALIZED_FACT
equity.minority_interest   → NORMALIZED_FACT
equity.debt                → DERIVED
equity.diluted_shares      → DERIVED
scenario.wacc              → ASSUMPTION
scenario.terminal_growth   → ASSUMPTION
six forecast inputs        → ASSUMPTION
```

Authority is inherited, never silently upgraded. `DERIVED != FACT`; source snapshot != reviewed fact; complete bound Draft != canonical case.

## Protected runtime and human-review boundaries / 보호 실행·인간검토 경계

SEC live capture:
- AI must not invent or infer the identifying contact value;
- `SEC_USER_AGENT` is runtime-only;
- the value must not be committed or persisted.

Human review:
- no automatic approval;
- no inferred reviewer identity;
- no inferred timestamp;
- no invented review basis or source locator;
- no Draft/registry/canonical write merely because a candidate exists.

For the M30-P1 successor, the exact semantic decision is:

`EXPLICIT_FILING_RECONCILIATION_EXCLUDES_LEASE_LIABILITIES`

This decision may only be supplied after an actual human reviewer establishes the issuer-filing basis. AI must not infer it from the SEC CompanyFacts value.

## Remaining M30 acceptance / 잔여 M30 완료조건

- [x] real-case preflight contract
- [x] exact U.S. aggregate-debt successor
- [x] runtime-safe SEC capture
- [x] deterministic 13-field readiness DAG
- [x] immutable non-SEC source-ingress mechanism
- [x] real Ingredion SEC source captured and validated
- [x] registry non-collision proven
- [x] exact cash / shares / NCI / aggregate-debt candidates proven
- [x] real readiness manifest validated
- [x] M30-R1 aggregate-debt CLI repair merged and post-merge validated
- [ ] real debt semantic review by an actual human reviewer
- [ ] real cash / share / NCI review paths
- [ ] real valuation-date market-price source + review
- [ ] seven M24 WACC source inputs + review
- [ ] two M25 macro anchors + terminal-growth review
- [ ] M26 six-field atomic forecast block + review
- [ ] complete M28 v0.8 13/13 result with `unresolved=[]`
- [ ] deterministic M29 candidate/package/admission/guarded plan
- [ ] canonical apply only on `admission/*`
- [ ] final exact-head CI + expected-head merge
- [ ] registry gains exactly one real Ingredion case
- [ ] Issue #66 closes and final post-merge CI succeeds

Do not begin a non-equity adapter during M30.

## Existing canonical registry / 기존 정식 registry

- `KR_010120_LS_ELECTRIC` — `equity_fcff`
- `KR_229640_LS_ECO_ENERGY` — `equity_fcff`
- `US_JTAI_JET_AI` — `venture_probability`

None was admitted through this complete M30 real-company path.

## Exact resume point / 정확한 재개점

Runtime-canonical resume baseline:

`210095f9ee491fa8a561273a744b6fd194fd9adc`

Active work returns to Issue **#79**.

Next execution is **not** another architecture mission. On the user's local clone:

1. update local `main` to the current merged repository state;
2. refresh editable install because `pyproject.toml` now points `vih` to `cli_entry_m30r1`;
3. run real Ingredion `sec-aggregate-debt-extract` against the existing hash-locked SEC snapshot;
4. validate the candidate;
5. normalize the candidate;
6. validate the normalized observation;
7. **STOP before `sec-aggregate-debt-review-build`**.

Do not create a review assertion until an actual human reviewer supplies reviewer identity, timezone-aware review time, review basis, source-basis locator, and the exact semantic-scope decision.

Issue #82 is state-only; once merged, its resulting main commit is a documentation-only descendant of the runtime baseline above.

## Grounding authority / 근거화 권위

1. merged `main` files and completed Issue/PR decisions
2. `PROJECT_STATE.md` and current active Issue/PR/branch
3. exact source/result/candidate/package/admission/plan SHA lineage
4. current chat
5. AI recollection
