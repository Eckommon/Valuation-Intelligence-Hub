# Project State / 프로젝트 상태

> Canonical human-and-AI handoff. Repository-grounded state outranks chat or AI recollection.  
> 인간·AI 공통 정식 인계 문서. 저장소 근거 상태는 채팅·AI 기억보다 우선한다.

## Repository / 저장소

- `Eckommon/Valuation-Intelligence-Hub`
- Purpose: reproducible, evidence-grounded cross-asset valuation intelligence / 재현 가능한 근거 기반 범자산 가치분석 인텔리전스

## Canonical baseline for active M30 execution / 활성 M30 실행 정식 기준선

The exact merged baseline from which the current real-company execution and M30-R1 child fix began is:

`main@5217462cc17937d9684374b363cc7472c8164d4a`

That main includes M1–M29, M30-A through M30-E, and M30-S canonical state reconciliation. The active parent mission is Issue **#66** and the active real-execution mission is Issue **#79**.

Current target:

```text
Ingredion Incorporated
Ticker: INGR
Venue: NYSE
SEC CIK: 0001046257
Case ID target: US_INGR_INGREDION
```

No synthetic fixture may be inserted into `registry/cases.json` to claim real-case success.

## Canonical milestone baseline / 정식 마일스톤 기준선

| Milestone | Main commit | Issue |
|---|---|---:|
| M20 Reviewed debt → `equity.debt` | `236547512919b5d68e283b3431183f56f5fc845c` | #44 |
| M21 Historical dilution reference | `03af933835b8fbcf9ef4e6b3fd1b3db7603782fc` | #46 |
| M22 Valuation-date share bridge | `0a476cc9927b2d63164143447428f3e69b06051b` | #48 |
| M23 Complete share bridge → `equity.diluted_shares` | `58d963238992f562c89c8325b42046ae35ac71bf` | #50 |
| M24 Governed WACC → `scenario.wacc` | `ca85f04c1bd84c5189f78c81e2653cc4f65bccca` | #52 |
| M25 Governed terminal growth → `scenario.terminal_growth` | `0c0a7591a59f163fa34aba54fdeb6001fb9b7dc0` | #54 |
| M26 Integrated forecast → six-field atomic binding | `130363475139fe6ea30d00d615f387b440a23c71` | #56 |
| M27 Governed market price → `market_price` | `3a5f2742acd11756a78579e8fd8ba8709a267327` | #58 |
| M28 Governed minority interest → `equity.minority_interest` | `db5d8e835455de9e52bc656b1ddb4c352736768b` | #60 |
| M29 Complete governed equity handoff | `97dc84d8e9a09b5bd9c6864137a537037baac4f6` | #62 |
| M30-A Real-case source preflight | `2034075db50bedb4feb9ec69000f3e1f789c4234` | #66 |
| M30-P1 Exact SEC aggregate-debt successor | `11182eeab7e60a90e6ddc140ca05f45e93af7e40` | #68 |
| M30-B Real-source preflight v0.2 | `a970d74b85e44e617dd604cc829637caaf65420e` | #66 |
| M30-C Runtime-safe SEC capture | `30609979d0d06040e7eeec276b8233796bfa48af` | #71 |
| M30-D 13-field readiness DAG | `fab223354c759e8b961949e8ff85e43d5bbb2ab8` | #73 |
| M30-E Immutable non-SEC source ingress | `e4207f0d9077208881f2a63317861e6f39fa8158` | #75 |
| M30-S Canonical M30 state reconciliation | `5217462cc17937d9684374b363cc7472c8164d4a` | #77 |

Earlier M1–M19 milestones remain completed and regression-locked in repository history.

## M29 canonical closure / M29 정식 종결

M29 is **COMPLETE**.

- final tested PR head: `a666d00d45431914fd98deb08f5b336f3c28eeef`
- final-head CI: `34791253465` → Python 3.11/3.12 success
- PR #63 merged using exact `expected_head_sha`
- merge/main: `97dc84d8e9a09b5bd9c6864137a537037baac4f6`
- Issue #62 completed
- post-merge CI: `34791345455` → Python 3.11/3.12 success

Required complete governed equity handoff remains:

```text
complete M28 v0.8 bound result
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
M29 admission bundle
        ↓
M29 guarded repository plan
        ↓
separate admission/* PR + CI + human review + merge
        ↓
CANONICAL CASE
```

## M30 preparation closure / M30 준비단계 종결

M30-A/P1/B/C/D/E/S are complete on the canonical baseline.

- M30-A: machine-readable real-case source-contract preflight
- M30-P1: exact `us-gaap:DebtLongtermAndShorttermCombinedAmount` successor; explicit semantic review mandatory
- M30-B: historical debt blocker resolved only when the exact aggregate-debt candidate exists
- M30-C: runtime-only `SEC_USER_AGENT`; no identifying User-Agent persisted
- M30-D: deterministic 13-material-field readiness manifest + 31-node prerequisite DAG
- M30-E: immutable local UTF-8 non-SEC source intake with snapshot-bound M27/M24/M25 provenance
- M30-S: repository state reconciliation at `5217462cc17937d9684374b363cc7472c8164d4a`

Architecture preparation is no longer the M30 bottleneck. The active work is real Ingredion execution.

## M30-R real Ingredion execution / 실제 Ingredion 실행

Issue **#79** is active.

### Real SEC capture — PASS

User-local runtime captured real SEC CompanyFacts under the protected M30-C path.

```text
CIK:                  0001046257
snapshot_sha256:      57b61f2b535b446664a240228f00020b859052f384488441849da83f0ceebf32
body_sha256:          53e524af4fe360cdf8eed3ee3055c87ff7abae5eb7e2053ff291667f5fb90745
status:               PASS_SOURCE_SNAPSHOT_VALIDATION
user_agent_persisted: false
canonical:            false
```

The raw snapshot remains user-local under gitignored `workspace/source_snapshots/**`.

### M30-B real-source preflight — PASS

```text
schema:            real-equity-source-preflight-v0.2
preflight_sha256:  69a458b319ecf89688e2e72439932afbb1057c9f3d1f4f6c8331402202af6773
status:            PASS_REAL_EQUITY_SOURCE_PREFLIGHT
blockers:          []
registry collision: false
next:              CONTINUE_TO_HUMAN_DEBT_SEMANTIC_REVIEW
```

Real source candidates are proven for:

- cash: exact SEC source candidate
- current common shares: exact SEC source candidate
- minority interest: exact SEC source candidate with explicit reported zero
- aggregate debt: exact `us-gaap:DebtLongtermAndShorttermCombinedAmount` candidate

The aggregate-debt candidate remains unreviewed. Source existence does not imply semantic approval.

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

Field-state counts:

```text
AWAITING_HUMAN_REVIEW = 4
AWAITING_REAL_SOURCE  = 2
AWAITING_DEPENDENCY   = 7
```

Human-review fields:
- `equity.cash`
- `equity.diluted_shares`
- `equity.debt`
- `equity.minority_interest`

Real-source fields still missing:
- `market_price`
- `scenario.wacc`

Terminal growth and six forecast fields remain dependency-bound.

## M30-R1 execution-discovered CLI repair / 실행 중 발견 CLI 보완

Real execution exposed one operability defect: M30-P1 had a governed Python lifecycle for exact SEC aggregate debt but the installed `vih` command surface did not expose it.

Child Issue **#80** and PR **#81** address only that runtime surface.

Branch:

`fix/m30-r1-sec-aggregate-debt-review-cli-v01`

The additive wrapper exposes:

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

All non-M30-R1 commands delegate unchanged through `M30 → M29 → ...`.

Human review remains fail-closed. `sec-aggregate-debt-review-build` requires explicit:

- reviewer identity
- timezone-aware reviewed-at timestamp
- review basis
- source-basis locator
- exact semantic-scope decision `EXPLICIT_FILING_RECONCILIATION_EXCLUDES_LEASE_LIABILITIES`

No reviewer state may be generated or inferred by AI.

### M30-R1 CI history

Initial PR head `a5cfa2c2b3a4c67a4666a5d74006746842d392a1` ran CI `35004811782`:

- 427 passed / 4 failed on both Python versions
- failures were only historical interface tests hard-coding `cli_entry_m30` as the forever-latest entrypoint
- no M30-R1 lifecycle test failed

Those interface tests were updated to verify the extended delegation chain `M30-R1 → M30 → M29 → ...`.

Subsequent exact head `eda067ad055e10d885d4f9e7c308847f0e3caebe` ran CI `35005018129`:

- Python 3.11: success
- Python 3.12: success

README/PROJECT_STATE reconciliation changes after that run require a new exact-head CI before PR #81 can merge.

## Authority model / 권위모델

```text
market_price               → FACT
equity.cash                → NORMALIZED_FACT
equity.minority_interest   → NORMALIZED_FACT
equity.debt                → DERIVED
equity.diluted_shares      → DERIVED
scenario WACC              → ASSUMPTION
terminal growth            → ASSUMPTION
six forecast inputs        → ASSUMPTION
```

Authority is inherited, never silently upgraded. `DERIVED != FACT`. A source snapshot is not a reviewed fact. A complete bound Draft is not canonical until separately governed promotion/admission/repository merge completes.

## Protected runtime and human-review boundaries / 보호 실행·인간검토 경계

SEC live capture requires an identifying fair-access User-Agent containing a contact email. It:

- must not be invented by AI;
- must not be inferred from GitHub/account metadata;
- must not be committed;
- must not be persisted in source snapshots;
- may be supplied only through runtime `SEC_USER_AGENT`.

Human review is equally explicit:

- no automatic approval;
- no inferred reviewer identity;
- no inferred review timestamp;
- no invented review rationale or source locator;
- no Draft/registry/canonical write merely because a candidate exists.

## Remaining M30 acceptance / 잔여 M30 완료조건

- [x] machine-readable real-case preflight contract
- [x] exact U.S. aggregate-debt successor
- [x] runtime-safe SEC capture interface
- [x] deterministic 13-field readiness manifest + prerequisite DAG
- [x] immutable non-SEC source-ingress mechanism
- [x] real Ingredion SEC CompanyFacts captured and validated
- [x] registry non-collision proven
- [x] exact cash / shares / NCI / aggregate-debt candidates proven
- [x] real 13-field readiness manifest validated
- [ ] M30-R1 CLI repair exact-head merge + post-merge CI
- [ ] real debt semantic review completed by an actual human reviewer
- [ ] real cash / share / NCI review paths completed
- [ ] real valuation-date market-price source captured/reviewed
- [ ] seven M24 WACC source inputs captured/reviewed
- [ ] two M25 long-run macro anchors + terminal-growth assumption reviewed
- [ ] M26 six-field atomic forecast block authored/reviewed
- [ ] complete M28 v0.8 result with 13/13 DIRECT_BIND + approvals + unique diffs + `unresolved=[]`
- [ ] deterministic M29 candidate/package/admission/guarded plan
- [ ] canonical application only on `admission/*`
- [ ] exact final-head Python 3.11/3.12 CI
- [ ] expected-head merge
- [ ] registry gains exactly one real Ingredion case
- [ ] Issue #66 closes and post-merge main CI succeeds

Do not begin a non-equity adapter during M30.

## Existing canonical registry / 기존 정식 registry

`registry/cases.json` currently contains historical canonical cases:

- `KR_010120_LS_ELECTRIC` — `equity_fcff`
- `KR_229640_LS_ECO_ENERGY` — `equity_fcff`
- `US_JTAI_JET_AI` — `venture_probability`

None was admitted through this complete M30 real-company path.

## Exact resume point / 정확한 재개점

At the time of this active branch state:

- canonical execution baseline: `main@5217462cc17937d9684374b363cc7472c8164d4a`
- active parent: Issue #66
- active execution: Issue #79
- execution-discovered child: Issue #80
- active PR: #81
- active branch: `fix/m30-r1-sec-aggregate-debt-review-cli-v01`
- latest code-tested head before state-doc reconciliation: `eda067ad055e10d885d4f9e7c308847f0e3caebe`
- latest successful code-head CI: `35005018129`

**Do not merge PR #81 until the final document-reconciled head receives exact-head Python 3.11/3.12 CI success.** After merge, immediately re-ground `main`, verify post-merge CI, and then resume Issue #79 at real Ingredion debt candidate extraction/normalization. Stop before human semantic-review assertion creation until a real human review is supplied.

## Grounding authority / 근거화 권위

1. merged `main` files and completed Issue/PR decisions
2. `PROJECT_STATE.md` and current active Issue/PR/branch
3. exact source/result/candidate/package/admission/plan SHA lineage
4. current chat
5. AI recollection
