# Project State / 프로젝트 상태

> Canonical human-and-AI handoff. Repository-grounded state outranks chat or AI recollection.  
> 인간·AI 공통 정식 인계 문서. 저장소 근거 상태는 채팅·AI 기억보다 우선한다.

## Repository / 저장소

- `Eckommon/Valuation-Intelligence-Hub`
- Purpose: reproducible, evidence-grounded cross-asset valuation intelligence / 재현 가능한 근거 기반 범자산 가치분석 인텔리전스

## Current canonical main / 현재 정식 main

`e4207f0d9077208881f2a63317861e6f39fa8158`

This main includes M1–M29 plus M30-A through M30-E. The current active parent mission is Issue **#66**, the first real complete-governed equity canonical case using **Ingredion Incorporated (NYSE: INGR, SEC CIK 0001046257)**.

현재 main은 M1–M29와 M30-A~M30-E를 포함한다. 활성 부모 미션은 Issue **#66**, 첫 실기업 완전 거버넌스 Equity 정식 사례이며 대상은 **Ingredion Incorporated (NYSE: INGR, SEC CIK 0001046257)**이다.

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

Earlier M1–M19 milestones remain completed and regression-locked in repository history.

## M29 canonical closure / M29 정식 종결

M29 is **COMPLETE**.

- final tested PR head: `a666d00d45431914fd98deb08f5b336f3c28eeef`
- final-head CI: `34791253465` → Python 3.11/3.12 success
- PR #63 merged using exact `expected_head_sha`
- merge/main: `97dc84d8e9a09b5bd9c6864137a537037baac4f6`
- Issue #62 completed
- post-merge CI: `34791345455` → Python 3.11/3.12 success

Complete governed equity handoff:

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
M29 admission dispatcher
        ↓
M29 guarded repository-plan dispatcher
        ↓
separate admission/* PR + CI + human review + merge
        ↓
CANONICAL CASE
```

## M30 parent mission / M30 부모 미션

Issue **#66** proves the M13–M29 system on one real, collision-free U.S. public-equity case before expanding asset-class breadth.

Target:

```text
Ingredion Incorporated
Ticker: INGR
Venue: NYSE
SEC CIK: 0001046257
Case ID target: US_INGR_INGREDION
```

No synthetic fixture may be inserted into `registry/cases.json` to claim success.

### M30-A — source-contract preflight foundation — COMPLETE

- PR #67
- final head `80cb0971e1d31cdf908b6c0fc76af3d209987d8f`
- CI `34793054730` success Python 3.11/3.12
- merge/main `2034075db50bedb4feb9ec69000f3e1f789c4234`
- post-merge CI `34793124445` success Python 3.11/3.12

### M30-P1 — reviewed SEC aggregate-debt successor — COMPLETE

- Issue #68 / PR #69
- final head `994979d9866ddf36d41128546a0a3368a39cb8c0`
- CI `34795763385` success Python 3.11/3.12
- merge/main `11182eeab7e60a90e6ddc140ca05f45e93af7e40`
- post-merge CI `34795834240` success Python 3.11/3.12
- exact source concept: `us-gaap:DebtLongtermAndShorttermCombinedAmount`
- human semantic review remains mandatory

### M30-B — real source preflight v0.2 — COMPLETE

- PR #70
- final head `d65e9ab1d52757b152118fb91f63802f24467fd4`
- CI `34796030718` success Python 3.11/3.12
- merge/main `a970d74b85e44e617dd604cc829637caaf65420e`
- post-merge CI `34796138064` success Python 3.11/3.12
- historical v0.1 preserved; exact aggregate-debt source probed fail-closed

### M30-C — runtime-safe SEC capture interface — COMPLETE

- Issue #71 / PR #72
- final head `8375d6dfec93b4413a2182304465437d5cd11ba0`
- CI `34797282518` success Python 3.11/3.12
- merge/main `30609979d0d06040e7eeec276b8233796bfa48af`
- post-merge CI `34797376116` success Python 3.11/3.12
- installed `vih` exposes runtime-safe SEC CompanyFacts capture, snapshot validation, and M30-B preflight
- identifying SEC User-Agent is runtime-only and is never committed or persisted

### M30-D — 13-field readiness manifest + prerequisite DAG — COMPLETE

- Issue #73 / PR #74
- final head `e79c6a8d7ca4f28f13eabc854b4e1b1fd54d0c36`
- CI `34797804807` success Python 3.11/3.12
- merge/main `fab223354c759e8b961949e8ff85e43d5bbb2ab8`
- post-merge CI `34797938544` success Python 3.11/3.12
- exact 13 material fields mapped to authority + prerequisites
- M24 seven WACC sources, M25 two macro anchors + reviewed WACC, M26 atomic six-field forecast block explicit
- readiness states distinguish real-source, human-review, dependency, ready, and blocked conditions

### M30-E — immutable non-SEC source ingress — COMPLETE

- Issue #75 / PR #76
- final head `8b081b3d90de5400b5f9579ec857783b6f307e52`
- CI `34820854174` success Python 3.11/3.12
- merge/main `e4207f0d9077208881f2a63317861e6f39fa8158`
- post-merge CI `34821022512` success Python 3.11/3.12
- `external-source-snapshot-v0.1` locks selected non-SEC UTF-8 source bytes + provenance metadata
- M27 market-price, M24 WACC source inputs, and M25 terminal-growth anchors can derive provenance only from the selected validated snapshot on the M30 path
- no arbitrary URL fetcher, credentials, reviewer fabrication, Draft mutation, registry write, or canonical write introduced

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

## M30 execution boundary / M30 실행 경계

The architectural preparation that can be completed without protected runtime input is now canonical through M30-E.

다음 단계는 architecture 확장이 아니라 **실제 Ingredion source execution**이다.

### Protected human-supplied runtime input

SEC live capture requires an identifying SEC fair-access User-Agent containing a contact email.

This value:

- must not be invented by AI;
- must not be inferred from GitHub account metadata;
- must not be committed to the repository;
- must not be persisted in source snapshots;
- may be supplied only at runtime through `SEC_USER_AGENT`.

### Execution sequence after runtime input is available

```text
1. capture real SEC CompanyFacts bytes with M30-C
2. validate immutable M13 snapshot
3. run M30-B v0.2 real-source preflight
4. run M30-D readiness manifest against that preflight
5. confirm exact cash / current shares / exact NCI / exact aggregate debt candidates
6. capture non-SEC source bytes through M30-E for market price / WACC / terminal-growth anchors as needed
7. stop at explicit human-review gates
8. create reviewed M20–M28 inputs only with real reviewer identity/time/basis
9. obtain complete M28 v0.8 bound result: 13/13 + unresolved=[]
10. build M29 candidate / promotion package / admission bundle / guarded plan
11. apply only on separate admission/* branch
12. full CI + human review + exact-head merge
13. verify registry gained exactly one real Ingredion case
14. verify post-merge main CI
```

## Remaining M30 acceptance / 잔여 M30 완료조건

- [x] machine-readable real-case preflight contract
- [x] U.S. aggregate-debt architectural prerequisite
- [x] exact aggregate-debt source probe
- [x] runtime-safe SEC capture interface
- [x] deterministic 13-field readiness manifest + prerequisite DAG
- [x] immutable non-SEC source ingress for M27/M24/M25 provenance
- [ ] real Ingredion SEC CompanyFacts bytes captured using protected runtime User-Agent
- [ ] target identity and registry non-collision proven against real bytes
- [ ] exact cash / current shares / exact NCI / exact aggregate-debt candidates proven
- [ ] complete real-source inventory for 13 material fields and support inputs
- [ ] all human-review gates completed with real reviewer state
- [ ] complete M28 v0.8 result with 13/13 DIRECT_BIND + approvals + diffs + unresolved=[]
- [ ] M29 candidate, package, admission bundle, and guarded plan deterministic
- [ ] canonical application only on `admission/*`
- [ ] exact final-head Python 3.11/3.12 CI
- [ ] exact-head merge
- [ ] registry gains exactly one real Ingredion case
- [ ] Issue #66 closes and post-merge main CI succeeds

Do not begin a non-equity adapter during M30.

## Existing canonical registry / 기존 정식 registry

`registry/cases.json` currently contains the historical canonical cases:

- `KR_010120_LS_ELECTRIC` — `equity_fcff`
- `KR_229640_LS_ECO_ENERGY` — `equity_fcff`
- `US_JTAI_JET_AI` — `venture_probability`

No real company has yet been admitted through the complete M29 path.

## Exact resume point / 정확한 재개점

Canonical code baseline before this state-only reconciliation:

`main@e4207f0d9077208881f2a63317861e6f39fa8158`

Active state-only mission:

- Issue #77 — M30 canonical state reconciliation
- branch `state/m30-canonical-reconciliation-v01`
- runtime/schema/valuation/admission behavior change: **NONE**

After Issue #77 receives exact-head CI, exact-head merge, and post-merge CI, re-ground main and continue Parent Issue #66 at the real-source execution boundary above.

## Grounding authority / 근거화 권위

1. merged `main` files and completed Issue/PR decisions
2. `PROJECT_STATE.md` and current active Issue/PR/branch
3. exact source/result/candidate/package/admission/plan SHA lineage
4. current chat
5. AI recollection
