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

M20 final PR CI `34688790288` and post-merge `main` CI `34688853460` completed `success` on Python 3.11/3.12.

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
GOVERNED BINDING CONTEXT / NOT CANONICAL
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

Source acquisition, normalization, derivation, date assertion, binding preparation, and Draft application never upgrade evidence authority by themselves.

## Active mission / 활성 미션

- Issue: `#46 [M21] Governed dilution reference evidence + valuation-share boundary`
- PR: `#47 M21 Governed dilution reference evidence + valuation-share boundary`
- Branch: `mission/m21-dilution-reference-v01`
- Base main: `236547512919b5d68e283b3431183f56f5fc845c`
- Status: `ACTIVE_FINALIZATION`

### M21 CI history / M21 CI 이력

- Core checkpoint head `6514684f9bf72ce146ed9d360d8ac2b73f1db2d6`
- Core checkpoint CI `34688999080`: Python 3.11/3.12 `success`
- Interface checkpoint head `9ae168d04f2a564125f95c6e698f896b8989f56d`
- Interface checkpoint CI `34689111081`: Python 3.11/3.12 `success`

A fresh final-head CI is still required after schemas/docs/state changes. Only that fresh final-head run may authorize merge.

## M21 core semantic boundary / M21 핵심 의미경계

```text
shares_outstanding != weighted_average_basic_shares
weighted_average_diluted_shares != valuation_date_fully_diluted_shares
historical_dilution_factor != valuation denominator
```

M21 does **not** resolve `equity.diluted_shares`. It creates historical dilution reference evidence only.

## Source mapping / 원천 매핑

M21 v0.1 uses an isolated SEC mapping and does not mutate the M13 source registry.

Exact US-GAAP concepts only:

```text
WeightedAverageNumberOfSharesOutstandingBasic
WeightedAverageNumberOfDilutedSharesOutstanding
```

Unit is `shares`. OpenDART is intentionally unsupported in v0.1 because denominator shares are not inferred from EPS or current shares.

## Period safety / 기간 안전성

SEC extraction requires explicit:

```text
period_start
period_end
```

Selection rule:

```text
EXACT_START_END_THEN_LATEST_FILED
```

This prevents quarterly and YTD 10-Q denominator facts with the same end date from being conflated.

Normalized observations are duration evidence:

```text
DURATION_QUARTER
DURATION_YTD
DURATION_ANNUAL
```

and always preserve exact start/end dates.

## Historical dilution derivation / 역사적 희석도 파생

For exact same entity, unit, and complete period identity:

```text
historical_dilution_factor
  = weighted_average_diluted_shares / weighted_average_basic_shares

historical_incremental_diluted_shares
  = weighted_average_diluted_shares - weighted_average_basic_shares
```

Rules:

- basic shares must be > 0
- diluted shares must be >= basic shares
- full period identity must match exactly
- candidate authority propagates
- arithmetic never upgrades authority
- validators recompute arithmetic from source values

## Mandatory non-binding flags / 필수 비바인딩 플래그

Every `historical-dilution-evidence-v0.1` result must carry:

```text
historical_only = true
valuation_date_direct_bind = false
forecast_direct_bind = false
shares_outstanding_substitution = false
```

Therefore M16/M20 `equity.diluted_shares` remains unresolved.

## Interfaces / 인터페이스

CLI:

```text
dilution-sec-extract
dilution-normalize
dilution-observation-validate
dilution-derive
dilution-validate
```

Web:

```text
/dilution
```

M21 interfaces are calculate/validate only. No Draft mutation, promotion, admission, or canonical-write M21 route exists.

## M21 files / M21 파일

- `src/valuation_hub/share_dilution.py`
- `src/valuation_hub/web_dilution.py`
- `src/valuation_hub/cli_entry.py`
- `schemas/share_dilution_observation.schema.json`
- `schemas/historical_dilution_evidence.schema.json`
- `tests/test_share_dilution.py`
- `tests/test_m21_interfaces.py`
- `docs/SHARE_DILUTION_REFERENCE.md`
- `docs/M21_ACCEPTANCE.md`
- `docs/M21_IMPLEMENTATION_SUMMARY.md`

## Grounding authority / 근거화 권위

1. merged `main` files and decisions
2. `PROJECT_STATE.md` + active Issue/PR/branch
3. SEC snapshot SHA → M21 candidate SHA → observation SHA → derived evidence SHA lineage
4. current chat
5. AI recollection

## Exact resume point / 정확한 재개점

Run a fresh full Python 3.11/3.12 CI on the final PR #47 head after schemas/docs/README/PROJECT_STATE are committed.

Merge only if all of the following remain green:

- M13 SEC registry non-mutation
- exact basic/diluted SEC concept mappings
- exact start/end period selection
- quarter/YTD/annual duration classification
- observation SHA integrity
- exact entity/unit/full-period derivation compatibility
- basic > 0 and diluted >= basic arithmetic guards
- candidate-authority propagation
- historical-only/non-binding semantic boundary
- `shares_outstanding` non-substitution
- CLI/Web no-write boundaries
- all M1–M21 regressions

After merge, verify Issue #46 closure and post-merge `main` CI before declaring M21 canonical.

If M21 closes cleanly, the next mission should be a separate **valuation-date fully diluted-share bridge** built from explicit current-share and instrument-level dilution evidence. Historical weighted-average EPS denominators must remain reference-only inputs to that future mission.