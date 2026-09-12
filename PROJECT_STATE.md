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

M17 final PR CI `34581540617` and post-merge `main` CI `34581620038` completed with Python 3.11/3.12 jobs `success`.

Earlier M1–M11 milestones remain completed and regression-locked in repository history.

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
GOVERNED DERIVED EVIDENCE / NOT CANONICAL
  ↓
BINDING PROPOSAL / NOT CANONICAL
  ↓
HUMAN APPROVAL LOCK / NOT CANONICAL
  ↓
BOUND DRAFT RESULT / NOT CANONICAL
  ↓
DRAFT EVIDENCE GOVERNANCE + HUMAN REVIEW
  ↓
PROMOTION → ADMISSION → guarded repository apply → PR/CI merge
  ↓
CANONICAL
```

Arithmetic, derivation, and Draft application never upgrade evidence authority.

## Active mission / 활성 미션

- Issue: `#40 [M18] Governed derived financial evidence + historical margins`
- PR: `#41 M18 Governed derived financial evidence + historical margins`
- Branch: `mission/m18-derived-financial-evidence-v01`
- Status: `ACTIVE_FINALIZATION`
- Core checkpoint head: `257b1556a84d3f5948fc84b78f12315b948e5197`
- Core checkpoint CI: `34672327071` — Python 3.11/3.12 `success`

## M18 objective / M18 목표

Derive only historical arithmetic relationships whose semantics are exact. M18 v0.1 supports historical operating margin and historical net-income margin and keeps them distinct from forecast assumptions.

의미가 정확한 역사적 산술관계만 파생한다. M18 v0.1은 역사적 영업마진·순이익률을 지원하며 미래 가정과 분리한다.

## Derivations / 파생식

```text
historical_operating_margin = operating_income / revenue
historical_net_income_margin = net_income / revenue
```

Revenue must be nonzero.

## Compatibility / 호환성

Source observations must be valid normalized observations and exactly match on:

- entity ID
- financial scope/perimeter
- source monetary unit
- complete normalized period identity

No currency conversion, cross-period bridging, entity mapping, or perimeter mapping is performed.

## Authority propagation / 권위 전파

```text
NORMALIZED_FACT + NORMALIZED_FACT
→ DERIVED_FACT

any NORMALIZED_FACT_CANDIDATE input
→ DERIVED_FACT_CANDIDATE
```

Every result remains `canonical=false`.

## Semantic boundary / 의미경계

Each result is locked with:

```text
historical_only=true
forecast_direct_bind=false
```

Therefore historical derived ratios cannot become forecast `ebit_margin`, forecast tax assumptions, or any other forecast input by direct binding.

## Integrity / 무결성

`derived-financial-evidence-v0.1` records:

- derivation rule and exact formula
- numerator/denominator metric and values
- source observation SHA-256 hashes
- propagated source authority classes
- entity/scope/period identity
- deterministic `derived_sha256`

Arithmetic, lineage, identity, authority, or semantic-boundary mutation fails validation.

## Interfaces / 인터페이스

CLI:

```text
derive-operating-margin
derive-net-margin
derived-validate
```

Web:

```text
/derived
POST /api/derived/calculate
POST /api/derived/validate
```

CLI/Web are calculate/validate only. No normalized-source mutation, Draft mutation, file write, promotion, admission, or canonical-write route exists.

## Files / 파일

- `src/valuation_hub/derived_financial.py`
- `schemas/derived_financial_evidence.schema.json`
- `src/valuation_hub/web_derived.py`
- `tests/test_derived_financial.py`
- `tests/test_m18_interfaces.py`
- `docs/DERIVED_FINANCIAL_EVIDENCE.md`
- `docs/M18_ACCEPTANCE.md`
- `docs/M18_IMPLEMENTATION_SUMMARY.md`

## Grounding authority / 근거화 권위

1. merged `main` files and decisions
2. `PROJECT_STATE.md` + active Issue/PR/branch
3. source snapshot → normalized observation → derived evidence → binding/approval SHA lineage
4. current chat
5. AI recollection

## Exact resume point / 정확한 재개점

Run fresh full Python 3.11/3.12 CI on the final PR #41 head. Merge only if arithmetic correctness, authority propagation, exact entity/scope/unit/period compatibility, zero-revenue blocking, SHA tamper detection, historical-only/forecast-direct-bind boundary, CLI/Web calculate-only behavior, and all M1–M18 regressions pass. Then verify post-merge `main` CI and Issue #40 closure.

After M18, the next priority should be **governed interest-bearing debt evidence/components**, not `liabilities → debt`. The next mission should define explicit short-term borrowings, current maturities, long-term borrowings/bonds/lease-liability inclusion policy, source account identity, same-date/perimeter aggregation, completeness states, and a noncanonical derived debt result before any Draft direct binding is considered.
