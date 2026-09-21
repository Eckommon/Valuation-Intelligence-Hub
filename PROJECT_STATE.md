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

`aadc8fef8ff3ecb20ad71cbd90809c4e95b69c1f`

This is **M30-R4.1 — strike-distribution-safe treasury-stock-method correction**, layered after M30-R5 market-price authority.

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
| M30-R4.1 strike-distribution-safe TSM | #100 / #101 | `aadc8fef8ff3ecb20ad71cbd90809c4e95b69c1f` | `35555025332` | complete |

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

## Real M30-R5 market-price execution / 실시장가격 실행

The real INGR market-price FACT is now source-bound and reviewed.

```text
ticker / venue       = INGR / NYSE
trading_date         = 2026-09-14
price                = USD 98.63
quote_type           = OFFICIAL_CLOSE
review_authority     = AI
package_sha256       = 607808de5224a84072427a18100e4933600fa4bad84057f9ffae0a7e436b7e9a
validator            = PASS_AI_REVIEWED_MARKET_PRICE_VALIDATION
```

Independent immutable snapshots:
- Investing.com: `8d889e4faa4232793d653fb1fed82582d22b570bf485afac9e1c378bef10324f`
- ChartExchange: `9e19415685779b8794c93fce9a50f772fcff8776d253688574fc6d9893f440da`
- StockAnalysis: `e30e991451c271d94b906fc5120203ad591c0b1f4b1a9756e4b0fc42496fc57c`

Market price is no longer a blocker.

## Real M30-R4 dilution execution and R4.1 correction / 실제 희석 실행·수정

First real HOLD execution captured and validated Tier-A issuer sources:

- 2026 Q2 10-Q snapshot: `f61f33b0e27403ab56882d8cc1daa3a66571e9452fc5d8012268f39ab098b0f9`
- 2025 10-K snapshot: `8be63bfbdfd16e77973b37ee7fce94f5131fedd443c01b234962e929c1e7835e`
- 2026 director-compensation exhibit snapshot: `45104cf9b7625ee851d5a87188a9ae8fb13fc9183a68529ca21c36ee104d1dce`

Initial HOLD artifact:
- inventory SHA: `fda95dfb56cc40e287a043f4947a6006c0da4fa183e36a135029da6e22a7b86d`
- adjudication SHA: `818a15b58fd97e627585e315f8f0d3c2db1e677ca8d309f0e264610a304972a1`
- decision: `HOLD_INCOMPLETE_DILUTION_COVERAGE`

Its overall HOLD remains useful historical execution evidence, but its original option adjustment of zero is **superseded for final authority**.

R4.1 falsified the aggregate weighted-average-strike shortcut:

```text
weighted_average_exercise_price != complete strike distribution
portfolio TSM = Σ tranche-level TSM
```

Canonical R4.1 rule:
- `TREASURY_STOCK_METHOD_TRANCHES_V01` requires explicit strike tranches whose counts reconcile to total outstanding instruments;
- aggregate TSM is allowed only when one homogeneous exercise price is explicitly supported;
- total options + weighted-average exercise price alone must fail closed.

Real current six-category status:

| Category | Current state | Evidence status |
|---|---|---|
| options_treasury_stock_method | BLOCKED_DEPENDENCY | complete valuation-date strike distribution unavailable |
| rsu_restricted_stock | PRESENT | 534,000 employee RSUs |
| warrants | ABSENT_SUPPORTED | full 10-Q + 10-K search returned zero warrant hits |
| convertibles_if_converted | ABSENT_SUPPORTED | full 10-Q + 10-K search returned zero convertible hits |
| contingent_shares | BLOCKED_DEPENDENCY | no complete point-in-time payout-weighted performance-award count |
| other_explicit | BLOCKED_DEPENDENCY | no complete 2026-09-14 director/deferred-equity aggregate |

Therefore `equity.diluted_shares` remains unresolved. Do not run `dilution-ai-finalize` from the original two-blocker inventory.

## Exact resume point / 정확한 재개점

Runtime baseline:

`aadc8fef8ff3ecb20ad71cbd90809c4e95b69c1f`

Next exact work:

1. regenerate the real R4 inventory under R4.1 using the already-captured local issuer snapshots and reviewed market-price/share-base packages;
2. expected corrected state is a durable **three-blocker HOLD**:
   - option strike distribution,
   - payout-weighted performance-award count,
   - director/deferred-equity point-in-time count;
3. do not finalize `equity.diluted_shares` from incomplete public evidence;
4. determine whether exact public reconstruction is possible or whether M30 requires a separately governed **bounded/materiality-aware dilution estimate** successor;
5. only after dilution authority is resolved, continue WACC → terminal growth → six-field forecast → M28/M29.

The project must not silently weaken exactness. If public filing granularity prevents exact reconstruction, the repository must represent that uncertainty explicitly rather than fabricate a point estimate.

## Remaining M30 acceptance / 잔여 완료조건

- [x] real SEC source capture / preflight / readiness
- [x] debt evidence-first AI authority and real debt execution
- [x] cash AI-reviewed authority
- [x] current common share base AI-reviewed authority
- [x] explicit-zero NCI AI-reviewed authority
- [x] six-category AI dilution governance
- [x] AI market-price authority successor
- [x] real INGR immutable market-price source snapshots
- [x] real INGR reviewed market-price FACT
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
