# Project State / 프로젝트 상태

> Canonical human-and-AI handoff. Repository-grounded state outranks chat or AI recollection.  
> 인간·AI 공통 정식 인계 문서. 저장소 근거 상태는 채팅·AI 기억보다 우선한다.

## Repository / 저장소

- `Eckommon/Valuation-Intelligence-Hub`
- Purpose: cross-asset, evidence-grounded valuation intelligence / 범자산 근거 기반 가치분석 인텔리전스
- Documentation: English + Korean bilingual / 영한문 병기

## Completed canonical baseline / 완료 기준선

| Milestone | Main commit | Issue |
|---|---|---:|
| M1 Evidence grounding + normalization | `e3a11259c0e248f055ee16466e08ccfef2a4d13e` | #1 |
| M2 Scenario + reverse valuation | `2b6d7522e7d847673a7310b9e7f4346cd26cb59e` | #2 |
| M3 Reference cases | `5c39c6a1857a5b4aeffa9782399e24bcbd77c0ae` | #3 |
| M4 Registry + CLI | `db14a21bb706f4f3cd74f5a33d88ca5937249aa5` | #8 |
| M5 Web MVP | `5867363d26d4efa57e5fb92d4861de9bfbf00d7f` | #12 |
| M6 Interactive preview + evidence | `caf7576c1a2c13916449d445f5badc3a29712d36` | #14 |
| M7 Product UX | `243cea0233031088fac8edb0362971326840b858` | #16 |
| M8 User Draft | `899271709ef3c49d431e0fce716eff48d0b22370` | #18 |
| M9 Reviewed promotion | `3e2d0a58b13c6e90ae6e665db72dc2683d5fad3f` | #20 |
| M10 Promotion package | `951e6be93a2d98db3e71c7e9f77bc06b90516dd2` | #22 |
| M11 Reviewed-Draft canonical admission | `243f941b2f323ac5fdca31b86e13966950156114` | #24 |
| M12 Guarded admission apply | `a40e92c196c39b40172711f38f7231f5e8812d52` | #26 |
| M13 Immutable SEC live evidence | `372b8b0b26307730c3e91afea97c979b59906042` | #28 |
| M14 Immutable OpenDART financial evidence | `1fff272cc583ec294226f5f530ebe483c2957fb5` | #30 |
| M15 Financial evidence normalization + TTM | `a99a6f24fa6736b01b270a2eeeb4592e8b673563` | #32 |

M15 final PR CI `34580046404` and post-merge `main` CI `34580118315` completed `success` on Python 3.11/3.12.

## Authority model / 권위모델

```text
SOURCE
  ↓
IMMUTABLE SNAPSHOT / NOT CANONICAL
  ↓
EVIDENCE CANDIDATE / NOT CANONICAL
  ↓
NORMALIZED OBSERVATION / TTM / NOT CANONICAL
  ↓
DRAFT BINDING PROPOSAL / NOT CANONICAL
  ↓
DRAFT + EVIDENCE GOVERNANCE
  ↓
HUMAN REVIEW → PACKAGE → ADMISSION → guarded branch apply → PR/CI merge
  ↓
CANONICAL
```

Neither arithmetic nor a binding proposal upgrades evidence authority.

산술과 바인딩 제안은 근거 권위를 승격하지 않는다.

## Active mission / 활성 미션

- Issue: `#34 [M16] Governed normalized-evidence → Draft binding proposal`
- PR: `#37 M16 Governed evidence → Draft binding proposal`
- Branch: `mission/m16-evidence-draft-binding-v01`
- Status: `ACTIVE_FINALIZATION`
- Core checkpoint head: `000aba154af381c4e29b707e8ffecc24e166f822`
- Core checkpoint CI: `34580452455` — Python 3.11/3.12 `success`

## M16 objective / M16 목표

Classify normalized financial evidence against all 13 material `equity_fcff` Draft inputs without mutating a Draft or confusing facts with assumptions.

정규화 재무근거를 13개 `equity_fcff` 핵심 Draft 입력과 비교·분류하되 Draft를 변경하거나 사실과 가정을 혼동하지 않는다.

## Semantic non-equivalence / 의미 비동일성

Regression-blocked:

```text
liabilities        ≠ debt
shares_outstanding ≠ diluted_shares
historical/TTM revenue ≠ forecast revenue
historical operating evidence ≠ forecast EBIT margin
historical tax evidence ≠ forecast tax assumption
```

## Binding states / 바인딩 상태

- `DIRECT_BIND`
- `REFERENCE_ONLY`
- `NEEDS_DERIVATION`
- `NEEDS_ASSUMPTION`
- `MISSING_REQUIRED`
- `CONFLICT_BLOCKED`
- `STALE_BLOCKED`

Every proposal classifies exactly 13 material Draft fields.

## Direct-binding boundary / 직접바인딩 경계

M16 v0.1 permits only:

```text
NORMALIZED_FACT
+ cash
+ INSTANT
+ EXACT date precision
+ FRESH under explicit as_of/max_age policy
→ equity.cash
```

`NORMALIZED_FACT_CANDIDATE` cannot direct-bind. Report-stage-only date precision cannot receive automatic freshness approval.

## Identity, freshness, conflicts / 식별·최신성·충돌

- one entity + one financial scope per proposal
- one monetary unit across monetary observations
- explicit `as_of` + `max_age_days`
- future-dated evidence fails closed
- unknown exact date precision is surfaced
- differing same-metric observations conflict-block until upstream reconciliation
- no averaging

## Integrity / 무결성

- source observation SHA-256 list recorded
- complete proposal locked by `proposal_sha256`
- policy/context/decision/identity mutation fails validation
- proposal always `canonical=false`

## Interfaces / 인터페이스

CLI:

```text
binding-build observations.json --as-of YYYY-MM-DD [--max-age-days N]
binding-validate proposal.json
```

Web:

```text
/binding
POST /api/binding/build
POST /api/binding/validate
```

There is deliberately no binding apply, Draft mutation, file write, promotion, admission, or canonical-write endpoint.

## Files / 파일

- `src/valuation_hub/draft_binding.py`
- `schemas/draft_binding_proposal.schema.json`
- `src/valuation_hub/web_binding.py`
- `tests/test_draft_binding.py`
- `tests/test_m16_interfaces.py`
- `docs/DRAFT_BINDING.md`
- `docs/M16_ACCEPTANCE.md`

## Grounding authority / 근거화 권위

1. merged `main` files and decisions
2. `PROJECT_STATE.md` + active Issue/PR/branch
3. immutable source snapshots + normalized/TTM/binding SHA lineage
4. current chat
5. AI recollection

## Exact resume point / 정확한 재개점

Run a fresh full Python 3.11/3.12 CI on the final PR #37 head after all M16 interfaces/docs are committed. Merge only if semantic non-equivalence guards, candidate-authority blocking, freshness/identity/conflict controls, proposal SHA integrity, CLI/Web proposal-only boundaries, and all M1–M16 regressions pass. Then verify post-merge `main` CI and Issue #34 closure.

If M16 closes cleanly, the next mission should be an explicit **human-approved binding application to a noncanonical Draft**, applying only SHA-locked `DIRECT_BIND` decisions while leaving derivations/assumptions unresolved and auditable. It must remain separate from canonical admission.
