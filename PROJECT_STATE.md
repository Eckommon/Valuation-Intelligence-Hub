# Project State / 프로젝트 상태

> Canonical human-and-AI handoff. Repository-grounded state outranks chat or AI recollection.  
> 인간·AI 공통 정식 인계 문서. 저장소 근거 상태는 채팅·AI 기억보다 우선한다.

## Repository / 저장소

- Repository: `Eckommon/Valuation-Intelligence-Hub`
- Active parent: Issue **#66**
- Real Ingredion execution: Issue **#79**
- Target case: `US_INGR_INGREDION`
- Company: Ingredion Incorporated / NYSE: INGR / SEC CIK `0001046257`

No synthetic fixture may be admitted to `registry/cases.json` to claim real-case completion.

## Current runtime-canonical baseline / 현재 runtime 정식 기준선

Latest runtime-changing canonical main:

`4f8a9c988ee20ddf33585e8810db312821f43698`

This is **M30-R5 — evidence-first AI market-price authority**.

State-only descendants that only reconcile documentation do not change runtime behavior; the runtime baseline remains the SHA above until another runtime PR merges.

Installed `vih` enters through:

`valuation_hub.cli_entry_m30r5:main`

and delegates unchanged through:

`M30-R5 → M30-R4 → M30-R3 → M30-R2 → M30-R1 → M30 → M29 → ...`

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

## M30-R5 market-price contract / 시장가격 계약

R5 is canonical, but the **real INGR market-price FACT has not yet been materialized locally**.

External research cross-check currently agrees on:
- ticker: INGR
- venue: NYSE
- valuation/trading date: 2026-09-14
- close: USD 98.63

This research result is not repository authority by itself.

R5 requires:

```text
already-acquired UTF-8 source bytes
  → M30-E immutable snapshot
  → M27 market-price candidate
  → exact snapshot↔candidate provenance validation
  → exact quote excerpt
  → Tier-B independent corroborating snapshot
  → contradiction search
  → AI_MARKET_PRICE_ADJUDICATOR_V01
  → existing reviewed-market-price-fact-v0.1
```

Primary snapshot must identify symbol, venue, currency, and closing-price semantics. Material contradiction fails closed.

## Exact resume point / 정확한 재개점

Runtime baseline:

`4f8a9c988ee20ddf33585e8810db312821f43698`

Next work is **real source execution**, not another architecture slice:

1. sync user-local main to the current canonical repository state;
2. refresh editable install so `vih` points to `cli_entry_m30r5`;
3. acquire two independent source texts for INGR 2026-09-14 close;
4. materialize and validate both M30-E snapshots under gitignored `workspace/source_snapshots/**`;
5. build the M27 candidate at USD 98.63;
6. build/validate M30-R5 AI evidence;
7. AI adjudicate/finalize/validate the reviewed market-price FACT;
8. feed that FACT to M30-R4 options TSM;
9. resolve RSU / contingent-performance / warrants / convertibles / other-explicit categories;
10. obtain reviewed `equity.diluted_shares`;
11. continue WACC → terminal growth → six-field forecast → complete M28/M29 handoff;
12. only then perform guarded real-case admission.

Do not begin a non-equity adapter during M30.

## Remaining M30 acceptance / 잔여 완료조건

- [x] real SEC source capture / preflight / readiness
- [x] debt evidence-first AI authority and real debt execution
- [x] cash AI-reviewed authority
- [x] current common share base AI-reviewed authority
- [x] explicit-zero NCI AI-reviewed authority
- [x] six-category AI dilution governance
- [x] AI market-price authority successor
- [ ] real INGR immutable market-price source snapshots
- [ ] real INGR reviewed market-price FACT
- [ ] real INGR complete six-category dilution coverage
- [ ] real `equity.diluted_shares`
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
