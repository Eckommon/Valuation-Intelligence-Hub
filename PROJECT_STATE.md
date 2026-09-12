# Project State / 프로젝트 상태

> Canonical human-and-AI handoff. Repository-grounded state outranks chat or AI recollection.  
> 인간·AI 공통 정식 인계 문서. 저장소 근거 상태는 채팅·AI 기억보다 우선한다.

## Repository / 저장소

- `Eckommon/Valuation-Intelligence-Hub`
- Purpose: cross-asset, evidence-grounded valuation intelligence / 범자산 근거 기반 가치분석 인텔리전스

## Completed canonical baseline / 완료 기준선

| Milestone | Main commit | Issue |
|---|---|---:|
| M20 Reviewed debt → `equity.debt` | `236547512919b5d68e283b3431183f56f5fc845c` | #44 |
| M21 Historical dilution reference | `03af933835b8fbcf9ef4e6b3fd1b3db7603782fc` | #46 |
| M22 Valuation-date share bridge | `0a476cc9927b2d63164143447428f3e69b06051b` | #48 |
| M23 Complete share bridge → `equity.diluted_shares` | `58d963238992f562c89c8325b42046ae35ac71bf` | #50 |
| M24 Governed WACC → `scenario.wacc` | `ca85f04c1bd84c5189f78c81e2653cc4f65bccca` | #52 |
| M25 Governed terminal growth → `scenario.terminal_growth` | `0c0a7591a59f163fa34aba54fdeb6001fb9b7dc0` | #54 |
| M26 Integrated forecast → six-field atomic binding | `130363475139fe6ea30d00d615f387b440a23c71` | #56 |

Earlier M1–M19 milestones remain completed and regression-locked in repository history.

### Recent canonical CI / 최근 정식 CI

- M24 final PR CI `34693544084` → Python 3.11/3.12 success
- M24 post-merge main CI `34693990230` → Python 3.11/3.12 success
- M25 final PR CI `34694777238` → Python 3.11/3.12 success
- M25 post-merge main CI `34694840768` → Python 3.11/3.12 success
- M26 final PR CI `34708790304` → Python 3.11/3.12 success
- M26 post-merge main CI `34708847816` → Python 3.11/3.12 success

## Authority model / 권위모델

```text
SOURCE
  ↓
IMMUTABLE / SOURCE-LOCKED INPUT / NOT CANONICAL
  ↓
FACT_CANDIDATE / NORMALIZED FACT / ASSUMPTION_CANDIDATE
  ↓
HUMAN-REVIEWED FACT / GOVERNED CONTEXT / ASSUMPTION / NOT CANONICAL
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

Calculation never silently upgrades candidate authority. A reviewed FACT or ASSUMPTION is still noncanonical until repository governance completes.

계산은 candidate 권위를 자동 승격하지 않는다. 검토완료 FACT/ASSUMPTION도 저장소 거버넌스 완료 전에는 비정식이다.

## Active mission / 활성 미션

- Issue: `#58 [M27] Governed market-price fact + Draft binding`
- PR: `#59 M27 Governed market-price FACT + Draft binding`
- Branch: `mission/m27-market-price-binding-v01`
- Base main: `130363475139fe6ea30d00d615f387b440a23c71`
- Status: `ACTIVE_FINALIZATION`

## M27 mission / M27 미션

Govern a valuation-date as-traded market quote as a source-backed, freshness-controlled market `FACT`, then bind only a human-reviewed eligible package into top-level Draft `market_price`.

가치평가일 as-traded 시장가격을 출처·최신성이 통제된 시장 `FACT`로 거버넌스하고 인간 검토완료 적격 패키지만 Draft 최상위 `market_price`로 연결한다.

## M27 authority boundary / M27 권위경계

```text
quoted number without provenance != governed market-price FACT
historical adjusted price != valuation-date market price
FACT_CANDIDATE != FACT
reviewed FACT != canonical state
```

Market price is a market observation, not a valuation assumption.

## Market-price candidate / 시장가격 Candidate

`market-price-fact-candidate-v0.1` requires:

- positive price per share
- uppercase quote currency
- exact entity ID + financial scope
- instrument ID + symbol + venue
- security type `COMMON_EQUITY`
- explicit quote type: `OFFICIAL_CLOSE` or `LAST_TRADE`
- price basis `AS_TRADED_PER_SHARE`
- exact trading date
- timezone-aware quote observation timestamp
- valuation `as_of`
- source publisher/type/tier/locator
- source snapshot SHA-256
- explicit max-age freshness policy

Review eligibility requires:

```text
source tier ∈ {A, B}
AND
freshness = FRESH
```

Trading date after valuation `as_of` fails closed. Historical-price substitution and silent split adjustment are forbidden.

## Human review / 인간검토

`market-price-review-assertion-v0.1` locks:

- exact candidate SHA
- source snapshot SHA
- exact price / currency / instrument / venue / quote type
- trading date / quote timestamp / valuation `as_of`
- freshness policy/status
- reviewer
- timezone-aware approval timestamp
- review basis

Chronology is independently enforced:

```text
approved_at >= observed_at
approved_at.date >= valuation as_of
```

The first core checkpoint passed before this additional chronology hardening. A dedicated regression test now proves that re-signing the outer assertion cannot legitimize pre-observation approval.

Finalization yields:

```text
reviewed-market-price-fact-v0.1
class = FACT
canonical = false
binding_eligibility = REVIEWED_FRESH_MARKET_PRICE_FACT
```

## v0.7 binding / v0.7 바인딩

```text
validated draft-binding-proposal-v0.6
        +
reviewed fresh market-price FACT
        ↓
draft-binding-proposal-v0.7
```

M27 accepts only validated v0.6 as its base.

Required exact compatibility:

- entity ID
- financial scope
- quote currency == base monetary unit / Draft currency
- market-price `as_of` == base proposal `as_of`

v0.7 replaces exactly:

```text
market_price
```

Every other base decision remains unchanged, including cash, debt, diluted shares, WACC, terminal growth, and all six forecast fields.

## Apply semantics / 적용 의미론

M27 extends the existing human binding-approval/apply path additively.

Applying `market_price` changes only the top-level Draft field and records:

```text
before
after
source_market_price_package_sha256
source_snapshot_sha256
review_assertion_sha256
trading_date
observed_at
venue
quote_type
```

The input Draft remains unchanged and the result remains noncanonical.

M26 result-integrity hardening remains enforced:

```text
all applied diff fields are unique
AND
set(applied_diff.field) == set(approved_fields)
```

## M27 CI history / M27 CI 이력

- Initial core head `c26790fa8e81e37b0fdffd9c772a978809202c6f`
  - CI `34709265076`: Python 3.11/3.12 success
- Quote-review chronology hardened head `6329f48f9f0233134d70dcd564f3c6362b050717`
  - CI `34721348673`: Python 3.11/3.12 success
- Interface/schema checkpoint follows the active branch after CLI entrypoint/schema changes.

A fresh final-head Python 3.11/3.12 CI is required after README/docs/PROJECT_STATE changes. Only that exact final tested head may authorize merge.

## Interfaces / 인터페이스

Installed CLI entrypoint:

```text
vih = valuation_hub.cli_entry_m27:main
```

M27 commands:

```text
market-price-candidate-build
market-price-candidate-validate
market-price-review-build
market-price-review-validate
market-price-finalize
market-price-validate
binding-build-with-market-price
binding-validate
```

All M1–M26 commands delegate unchanged to the M26 dispatcher.

Web:

```text
/market-price
/api/market-price/candidate-build
/api/market-price/candidate-validate
/api/market-price/review-build
/api/market-price/review-validate
/api/market-price/finalize
/api/market-price/validate
/api/market-price/binding-build
/api/market-price/binding-validate
```

M27 Web is preparation/validation only. It has no direct Draft-apply, file-write, promotion, admission, or canonical-write endpoint.

## M27 files / M27 파일

- `src/valuation_hub/market_price.py`
- `src/valuation_hub/market_price_draft_binding.py`
- `src/valuation_hub/binding_apply_m27.py`
- `src/valuation_hub/cli_entry_m27.py`
- `src/valuation_hub/web_market_price.py`
- `schemas/market_price_fact_candidate.schema.json`
- `schemas/market_price_review_assertion.schema.json`
- `schemas/reviewed_market_price_fact.schema.json`
- `schemas/draft_binding_proposal_v07.schema.json`
- `tests/test_m27_market_price_binding.py`
- `tests/test_m27_review_chronology_hardening.py`
- `tests/test_m27_interfaces.py`
- `docs/MARKET_PRICE_FACT_BINDING.md`
- `docs/M27_ACCEPTANCE.md`
- `docs/M27_IMPLEMENTATION_SUMMARY.md`

## Grounding authority / 근거화 권위

1. merged `main` files and completed Issue/PR decisions
2. `PROJECT_STATE.md` + active Issue/PR/branch
3. v0.6 proposal SHA → market-price candidate/source SHA → review assertion SHA → reviewed FACT package SHA → v0.7 proposal SHA → binding approval/result SHA
4. current chat
5. AI recollection

## Remaining material gap after M27 / M27 이후 잔여 중요입력

Once M27 is canonical, the M16 equity-FCFF material-field matrix will have governed paths for every material field except likely:

```text
equity.minority_interest
```

Do not start M28 until M27 is merged and latest `main` is re-grounded.

M27 병합 및 최신 main 재근거화 전에는 M28을 시작하지 않는다.

## Exact resume point / 정확한 재개점

1. Verify the interface/schema checkpoint CI on the current branch.
2. Run fresh full Python 3.11/3.12 CI on the exact final PR #59 head after this handoff update.
3. Update PR #59 with exact tested head + CI run.
4. Merge using `expected_head_sha` only.
5. Confirm Issue #58 closes as completed.
6. Verify post-merge `main` Python 3.11/3.12 CI.
7. Re-ground latest `main` before selecting M28.

Merge only if all remain green:

- FACT candidate/reviewed FACT authority separation
- exact quote identity and as-traded boundary
- Tier A/B + freshness review gate
- trading-date/as-of chronology
- approval-at/quote-observation chronology
- nested candidate/assertion tamper blocking
- v0.6-only base requirement
- exact entity/scope/currency/as-of compatibility
- only `market_price` decision replaced
- source/package/review/quote lineage
- top-level Draft market-price-only mutation
- source Draft immutability
- M26 unique-diff-field integrity guard
- additive CLI delegation
- Web no-write boundary
- all M1–M26 regressions
