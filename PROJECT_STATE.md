# Project State / 프로젝트 상태

> Canonical human-and-AI handoff. Repository-grounded state outranks chat or AI recollection.  
> 인간·AI 공통 정식 인계 문서. 저장소 근거 상태는 채팅·AI 기억보다 우선한다.

## Repository / 저장소

- `Eckommon/Valuation-Intelligence-Hub`
- Purpose: cross-asset, evidence-grounded valuation intelligence / 범자산 근거 기반 가치분석 인텔리전스

## Completed canonical baseline / 완료 기준선

| Milestone | Main commit | Issue |
|---|---|---:|
| M12 Guarded admission apply | `a40e92c196c39b40172711f38f7231f5e8812d52` | #26 |
| M13 Immutable SEC live evidence | `372b8b0b26307730c3e91afea97c979b59906042` | #28 |
| M14 Immutable OpenDART financial evidence | `1fff272cc583ec294226f5f530ebe483c2957fb5` | #30 |
| M15 Financial normalization + TTM | `a99a6f24fa6736b01b270a2eeeb4592e8b673563` | #32 |
| M16 Governed evidence → Draft binding proposal | `fbaf90bab04a877ba6afaaa035a4e99e9ef085a0` | #34 |
| M17 Human-approved noncanonical Draft binding apply | `ef68c2549bef842ef417d401140b49c88af209b5` | #38 |
| M18 Governed derived financial evidence + historical margins | `fb33cfbf401ab9c2e36ccd831bd059c8951214ba` | #40 |
| M19 Governed interest-bearing debt components + aggregation | `5b2ab53b0c83632abae187f12e1a682ecc254b77` | #42 |
| M20 Reviewed debt → `equity.debt` binding | `236547512919b5d68e283b3431183f56f5fc845c` | #44 |
| M21 Governed historical dilution reference | `03af933835b8fbcf9ef4e6b3fd1b3db7603782fc` | #46 |

M21 final PR CI `34690797078` and post-merge `main` CI `34690857449` completed `success` on Python 3.11/3.12.

Earlier M1–M11 milestones remain completed and regression-locked in repository history.

## Authority model / 권위모델

```text
SOURCE
  ↓
IMMUTABLE SNAPSHOT / NOT CANONICAL
  ↓
EVIDENCE CANDIDATE / NOT CANONICAL
  ↓
NORMALIZED / DERIVED EVIDENCE / NOT CANONICAL
  ↓
GOVERNED CONTEXT / NOT CANONICAL
  ↓
BINDING PROPOSAL / NOT CANONICAL
  ↓
HUMAN APPROVAL LOCK / NOT CANONICAL
  ↓
BOUND DRAFT RESULT / NOT CANONICAL
  ↓
DRAFT GOVERNANCE → PROMOTION → ADMISSION → guarded apply → PR/CI merge
  ↓
CANONICAL
```

Source acquisition, normalization, derivation, coverage assertion, binding preparation, and Draft application never upgrade evidence authority by themselves.

## Active mission / 활성 미션

- Issue: `#48 [M22] Valuation-date common-share base + diluted-share bridge foundation`
- PR: `#49 M22 Valuation-date common-share base + diluted-share bridge foundation`
- Branch: `mission/m22-valuation-share-bridge-v01`
- Base main: `03af933835b8fbcf9ef4e6b3fd1b3db7603782fc`
- Status: `ACTIVE_FINALIZATION`

### M22 CI history / M22 CI 이력

- Core tested head `2e4ec06e79bbd8279d1b7d4cd0a9adc12910f008`
- Core CI `34691138178`: Python 3.11/3.12 `success`

A fresh final-head CI is required after CLI/Web, schemas, docs, README, and PROJECT_STATE changes. Only that exact final-head run may authorize merge.

## M22 semantic boundary / M22 의미경계

```text
current_common_shares != fully_diluted_shares
weighted_average_diluted_shares != current_common_shares
historical_dilution_factor != automatic current dilution adjustment
missing dilution category != zero
```

M22 builds the evidence bridge toward `equity.diluted_shares`; M22 itself does not mutate a Draft or directly bind that field.

## SEC current-share base / SEC 현재주식수 기준

M22 v0.1 uses an isolated exact mapping:

```text
dei:EntityCommonStockSharesOutstanding
```

M13 and M21 registries remain unchanged.

The point-in-time pipeline is:

```text
SEC immutable snapshot
  ↓
current-common-shares-candidate-v0.1
  ↓
current-common-shares-observation-v0.1
  ↓
valuation-share-base-context-v0.1
```

Rules:
- exact `INSTANT` date only
- `shares` unit only
- equal-precedence distinct values fail closed
- candidate authority is preserved
- only reviewed `NORMALIZED_FACT` may enter valuation share-base context
- context freshness is independently recomputed from source date, `as_of`, and max-age policy
- stale evidence remains visible but cannot support complete reviewed coverage

## Explicit dilution adjustments / 명시적 희석조정

`dilution-adjustment-v0.1` separates current-share base from instrument-level dilution evidence.

Supported structural categories:

```text
options_treasury_stock_method
rsu_restricted_stock
warrants
convertibles_if_converted
contingent_shares
other_explicit
```

Every adjustment carries:
- unique adjustment ID
- category
- nonnegative share amount
- source SHA
- source description
- authority class
- adjustment SHA

The builder creates candidate authority. Arithmetic never promotes it to reviewed authority.

## Human coverage assertion / 인간 coverage 승인

`dilution-coverage-assertion-v0.1` may declare complete coverage only when:
- base context is fresh
- all included adjustments are reviewed facts
- all supported categories are explicitly reviewed
- reviewer and timezone-aware approval time are present
- coverage basis is explicit
- exact base-context and adjustment hashes are locked

An empty adjustment set can become complete only through this explicit all-category human review. Missing categories are not silently treated as zero.

## Diluted-share bridge / 희석주식 bridge

Output:

```text
diluted-share-bridge-v0.1
```

Coverage states:

```text
BASE_ONLY
PARTIAL_DILUTION_COVERAGE
COMPLETE_REVIEWED_DILUTION_COVERAGE
CONFLICT_BLOCKED
```

Arithmetic for non-conflict states:

```text
candidate_fully_diluted_shares
  = current_common_shares_base
  + sum(explicit selected adjustments)
```

A candidate total is not authority. Future binding eligibility requires:

```text
COMPLETE_REVIEWED_DILUTION_COVERAGE
+ FRESH base
+ all selected adjustments reviewed
+ valid coverage assertion
```

Duplicate adjustment IDs with different evidence produce `CONFLICT_BLOCKED` and hide the candidate total.

## M21 relationship / M21 관계

Full M21 historical dilution evidence may be embedded only as reference:

```text
reference_only = true
auto_adjustment_created = false
```

Historical dilution never estimates or creates a current adjustment automatically.

## Nested validation / 중첩 검증

The M22 bridge embeds and revalidates:
- full base context
- all input adjustments
- selected adjustments
- full coverage assertion when present
- full M21 historical reference when present

Validator logic recomputes reconciliation, conflicts, arithmetic, coverage, authority, and future-binding eligibility. Re-sealing only the outer bridge SHA cannot legitimize a modified nested source or approval object.

## Interfaces / 인터페이스

CLI:

```text
share-sec-extract
share-normalize
share-observation-validate
share-base-context-build
share-base-context-validate
share-adjustment-build
share-adjustment-validate
share-coverage-assertion-build
share-coverage-assertion-validate
share-bridge-build
share-bridge-validate
```

Web:

```text
/shares
/api/shares/*
```

M22 interfaces are calculate/validate only. No Draft-file write, promotion, admission, or canonical-write M22 route exists.

## M22 files / M22 파일

- `src/valuation_hub/valuation_shares.py`
- `src/valuation_hub/web_valuation_shares.py`
- `src/valuation_hub/cli_entry.py`
- `schemas/current_common_shares_observation.schema.json`
- `schemas/valuation_share_base_context.schema.json`
- `schemas/dilution_adjustment.schema.json`
- `schemas/dilution_coverage_assertion.schema.json`
- `schemas/diluted_share_bridge.schema.json`
- `tests/test_m22_valuation_shares.py`
- `tests/test_m22_interfaces.py`
- `docs/VALUATION_SHARE_BRIDGE.md`
- `docs/M22_ACCEPTANCE.md`
- `docs/M22_IMPLEMENTATION_SUMMARY.md`

## Grounding authority / 근거화 권위

1. merged `main` files and decisions
2. `PROJECT_STATE.md` + active Issue/PR/branch
3. SEC snapshot → current-share observation → base-context SHA → adjustment evidence → coverage assertion → bridge SHA lineage
4. M21 historical evidence only as reference
5. current chat
6. AI recollection

## Exact resume point / 정확한 재개점

Run fresh full Python 3.11/3.12 CI on the final PR #49 head after all interface/schema/docs/state changes.

Merge only if all remain green:
- M13/M21 registry isolation
- exact DEI current-share mapping
- exact instant semantics and equal-precedence conflict blocking
- reviewed-only base-context admission
- independently recomputable freshness
- explicit adjustment authority and source lineage
- no historical-factor auto-adjustment
- no missing-category-as-zero inference
- complete coverage assertion lock
- BASE_ONLY/PARTIAL/CONFLICT non-bindability
- nested source/assertion revalidation
- CLI/Web no-write boundaries
- all M1–M22 regressions

After merge, verify Issue #48 closure and post-merge `main` CI before declaring M22 canonical.

If M22 closes cleanly, the next mission should integrate **only complete, reviewed, fresh M22 bridges** into M16/M17/M20 as `equity.diluted_shares`, while keeping BASE_ONLY/PARTIAL/CONFLICT/stale/candidate bridges non-bindable.