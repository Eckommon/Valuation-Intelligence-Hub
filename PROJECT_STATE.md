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

M18 final PR CI `34672464437` and post-merge `main` CI `34672504185` completed `success` on Python 3.11/3.12.

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

Source acquisition, normalization, derivation, aggregation, and Draft application never upgrade evidence authority by themselves.

## Active mission / 활성 미션

- Issue: `#42 [M19] Governed interest-bearing debt components + aggregation`
- PR: `#43 M19 Governed interest-bearing debt components + aggregation`
- Branch: `mission/m19-interest-bearing-debt-v01`
- Status: `ACTIVE_FINALIZATION`

### CI history / CI 이력

- Initial checkpoint head `8eab1c9db148c94e2a58868696b88e18fe79b4cc`
- Initial checkpoint CI `34672809483`: **failure**
  - cause 1: import-time mutation of M13/M14 source registries violated their explicit registry regression contracts
  - cause 2: equal reviewed+candidate duplicate authority validation considered only selected rows rather than all input evidence
- Corrected isolated-pipeline head `c2e469367944ee3bc81f9fc6ce35973bd95c480c`
- Corrected core CI `34673035190`: Python 3.11/3.12 `success`

The failed checkpoint is preserved as diagnostic evidence; it is not a merge gate.

## M19 core semantic rule / M19 핵심 의미규칙

```text
liabilities ≠ interest_bearing_debt
missing ≠ zero
```

M19 uses an isolated source/normalization pipeline and does not mutate M13/M14/M15 registries.

## Core components / 핵심 구성요소

```text
short_term_borrowings
current_portion_long_term_borrowings
long_term_borrowings
current_portion_bonds
bonds_noncurrent
```

Lease liabilities are excluded pending an explicit future policy.

## Source mapping / 원천 매핑

### SEC

v0.1 only supports exact:

```text
us-gaap:ShortTermBorrowings
```

Broad `LongTermDebtCurrent` / `LongTermDebtNoncurrent` concepts are intentionally not relabeled as narrow components because that can mix instrument classes or double count.

### OpenDART

All five components use exact IFRS account IDs with exact Korean account-name fallback. No fuzzy matching.

## Isolated normalization / 분리 정규화

Source candidates normalize into:

```text
debt-component-observation-v0.1
```

Each observation is:

- `INSTANT`
- noncanonical
- authority-preserving
- source concept/account lineage preserving
- SHA-256 locked

## Aggregation / 집계

Output:

```text
interest-bearing-debt-evidence-v0.1
```

Compatibility requires exact same entity, financial scope, unit, and full period identity.

Coverage:

```text
COMPLETE_CORE_COMPONENTS
PARTIAL_COMPONENTS
CONFLICT_BLOCKED
```

Rules:

- Complete reviewed five-component coverage → final debt value + future binding eligibility.
- Partial coverage → `known_component_sum` only; final debt value is `null`.
- Conflict → known sum and final debt value are both `null`.
- Equal duplicate values select a reviewed representation if available, but any candidate input keeps aggregate authority candidate.
- Total liabilities are never used.
- Missing components are never imputed as zero.

## Interfaces / 인터페이스

CLI:

```text
debt-sec-extract
debt-dart-extract
debt-normalize
debt-component-validate
debt-aggregate
debt-validate
```

Web:

```text
/debt
POST /api/debt/aggregate
POST /api/debt/validate
```

Interfaces do not write Draft or canonical state.

## Files / 파일

- `src/valuation_hub/debt_components.py`
- `src/valuation_hub/web_debt.py`
- `schemas/debt_component_observation.schema.json`
- `schemas/interest_bearing_debt_evidence.schema.json`
- `tests/test_debt_components.py`
- `tests/test_m19_source_mapping.py`
- `tests/test_m19_interfaces.py`
- `docs/INTEREST_BEARING_DEBT.md`
- `docs/M19_ACCEPTANCE.md`
- `docs/M19_IMPLEMENTATION_SUMMARY.md`

## Grounding authority / 근거화 권위

1. merged `main` files and decisions
2. `PROJECT_STATE.md` + active Issue/PR/branch
3. source snapshot → isolated debt candidate → debt observation → aggregate SHA lineage
4. current chat
5. AI recollection

## Exact resume point / 정확한 재개점

Run a fresh full Python 3.11/3.12 CI on the final PR #43 head after all M19 interfaces/docs are committed. Merge only if M13/M14 registry non-mutation, exact debt source mappings, isolated component normalization, complete/partial/conflict arithmetic, candidate-authority propagation, liabilities/missing/lease semantic guards, SHA integrity, CLI/Web no-write boundaries, and all M1–M19 regressions pass. Then verify post-merge `main` CI and Issue #42 closure.

If M19 closes cleanly, the next mission should integrate **only complete reviewed M19 debt evidence** into M16/M17 as `equity.debt`. Partial, conflict-blocked, or candidate debt must remain non-bindable and must not alter a Draft.
