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

M14 post-merge `main` CI run `34575650004` completed `success` on Python 3.11/3.12.

## Canonical authority model / 정식 권위모델

```text
OFFICIAL / USER SOURCE
        ↓
IMMUTABLE SOURCE SNAPSHOT / NOT CANONICAL
        ↓
UNREVIEWED EVIDENCE CANDIDATE / NOT CANONICAL
        ↓
PERIOD NORMALIZATION / TTM / NOT CANONICAL
        ↓
DRAFT + EVIDENCE GOVERNANCE
        ↓
HUMAN SHA-256 REVIEW LOCK
        ↓
PROMOTION PACKAGE → ADMISSION PROPOSAL
        ↓
GUARDED admission/* BRANCH APPLY
        ↓
PR + FULL CI + REVIEWED MERGE
        ↓
CANONICAL
```

Normalization and arithmetic never upgrade evidence authority.

정규화와 산술은 근거 권위를 승격하지 않는다.

## Active mission / 활성 미션

- Issue: `#32 [M15] Financial evidence normalization + period semantics + TTM transforms`
- PR: `#33 M15 Financial evidence normalization + TTM`
- Branch: `mission/m15-financial-normalization-v01`
- Status: `ACTIVE_FINALIZATION`
- Kernel checkpoint CI run `34576216890`: Python 3.11/3.12 `success`
- CLI/Web checkpoint head: `f050a68badbfbf080379c4e4e968ee26ac40177e`

## M15 kernel / M15 커널

Primary service:

```text
src/valuation_hub/financial_normalization.py
```

Schemas:

```text
schemas/financial_observation.schema.json
schemas/financial_ttm.schema.json
```

Authority propagation:

```text
FACT           → NORMALIZED_FACT
FACT_CANDIDATE → NORMALIZED_FACT_CANDIDATE
```

All normalized observations and TTM results remain `canonical=false`.

## Period semantics / 기간 의미

Supported kinds:

- `INSTANT`
- `DURATION_QUARTER`
- `DURATION_YTD`
- `DURATION_ANNUAL`
- `DURATION_TTM`

SEC controls:

- instant metrics cannot have duration start;
- 10-K duration is annual only inside bounded duration checks;
- 10-Q duration requires explicit quarter/YTD declaration;
- value magnitude is never used to guess period semantics.

OpenDART controls:

- BS current amount → instant;
- nonannual IS/CIS current amount → quarter;
- nonannual IS/CIS cumulative amount → YTD;
- annual IS/CIS current amount → annual;
- report-stage identity is preserved;
- exact dates are not invented when OpenDART supplies only report semantics.

## TTM / TTM

```text
TTM = Q[-3] + Q[-2] + Q[-1] + Q[0]
TTM = PRIOR_FY + CURRENT_YTD - PRIOR_COMPARABLE_YTD
```

Compatibility guards require the same metric, entity, financial scope, and unit. Four-quarter inputs must be contiguous. Annual bridge requires comparable fiscal years and identical YTD stages.

Every transform records exact component values and input observation SHA-256 lineage.

## Reconciliation / 조정

Same-period observations must represent identical metric/entity/scope/unit/period identity. Equal values reconcile deterministically, preferring reviewed `NORMALIZED_FACT`; conflicting values fail closed as `UNKNOWN_CONFLICT`. No averaging is allowed.

## Interfaces / 인터페이스

CLI:

```text
normalize-sec
normalize-dart
normalize-validate
ttm-four-quarters
ttm-annual-bridge
ttm-validate
normalize-reconcile
```

Web:

```text
/normalize
POST /api/normalize/one
POST /api/normalize/validate
POST /api/normalize/ttm-four
POST /api/normalize/ttm-bridge
POST /api/normalize/reconcile
POST /api/normalize/ttm-validate
```

The Web layer is calculate-only. It has no live-fetch, file-write, promotion, admission, or canonical-write endpoint and rejects credential-bearing payloads.

## Tests / 테스트

- `tests/test_financial_normalization.py`
- `tests/test_m15_interfaces.py`

Coverage includes:

- authority propagation
- SEC ambiguous 10-Q fail-closed behavior
- OpenDART current/cumulative semantics
- observation hash tamper detection
- quarter continuity and compatibility
- annual-bridge stage guards
- conflict blocking
- CLI TTM execution
- Web read-only boundaries
- Web credential rejection

## Documentation / 문서

- `docs/FINANCIAL_NORMALIZATION.md`
- `docs/M15_ACCEPTANCE.md`
- `docs/M15_IMPLEMENTATION_SUMMARY.md`

## Grounding authority / 근거화 권위

1. merged `main` files and decisions
2. `PROJECT_STATE.md` + active Issue/PR/branch
3. immutable source snapshots + normalized observation/TTM lineage
4. current chat
5. AI recollection

## Exact resume point / 정확한 재개점

Run a fresh full Python 3.11/3.12 CI on the final PR #33 head after all M15 docs/interfaces are committed. Merge #33 only if period semantics, authority propagation, hash integrity, TTM compatibility, reconciliation conflict blocking, CLI/Web read-only boundaries, M13/M14 source behavior, and all M1–M15 regressions pass. After merge, verify the `main` push CI and Issue #32 closure.

If M15 closes cleanly, the next mission should be **governed normalized-evidence → valuation-model input binding**, not another raw-source adapter. It should define explicit mappings from reviewed normalized observations into Draft material inputs, completeness/staleness gates, source/perimeter compatibility, override provenance, and human review before any canonical admission.
