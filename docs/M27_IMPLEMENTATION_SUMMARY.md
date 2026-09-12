# M27 Implementation Summary / M27 구현요약

## Scope / 범위

M27 closes the governed path for the top-level equity-FCFF `market_price` material field.

```text
source-backed as-traded quote
  ↓
market-price-fact-candidate-v0.1
  ↓
market-price-review-assertion-v0.1
  ↓
reviewed-market-price-fact-v0.1
  ↓
draft-binding-proposal-v0.7
  ↓
existing binding-approval-v0.1
  ↓
noncanonical bound Draft result
```

## Core files / 핵심 파일

- `src/valuation_hub/market_price.py`
- `src/valuation_hub/market_price_draft_binding.py`
- `src/valuation_hub/binding_apply_m27.py`
- `src/valuation_hub/cli_entry_m27.py`
- `src/valuation_hub/web_market_price.py`

## Contracts / 계약

Market-price candidate:
- source-backed exact quote identity
- Tier A/B review eligibility
- independently recomputed freshness
- explicit `AS_TRADED_PER_SHARE` boundary
- no historical substitution or split adjustment

Human review:
- exact candidate/source lock
- timezone-aware approval
- `approved_at >= observed_at`
- exact review basis

Reviewed package:
- class `FACT`
- still `canonical=false`
- binding eligibility only after valid candidate + assertion revalidation

v0.7 proposal:
- base must be valid M26 v0.6
- only `market_price` decision changes
- exact entity/scope/currency/as-of match
- nested market-price package remains fully embedded and validated

Apply:
- top-level Draft `market_price` only
- quote/package/source/review lineage in diff
- original Draft immutable
- M26 unique applied-diff-field integrity check preserved

## Hardening / 강화

Core checkpoint:
- head `c26790fa8e81e37b0fdffd9c772a978809202c6f`
- CI `34709265076`: Python 3.11/3.12 success

A chronology review found that a same-day human assertion could theoretically predate the quote observation while still satisfying the older date-only gate. M27 now independently requires:

```text
approved_at >= observed_at
```

and includes both direct-build and re-signed-forgery regression tests.

Hardened checkpoint:
- head `6329f48f9f0233134d70dcd564f3c6362b050717`
- CI `34721348673`: Python 3.11/3.12 success

## Interfaces / 인터페이스

`pyproject.toml` now points the installed `vih` command to `valuation_hub.cli_entry_m27:main`.

M27 commands are intercepted additively; older commands delegate to the M26 dispatcher.

Web route:
- `/market-price`
- `/api/market-price/*`

The Web layer performs preparation/validation only.

## Schemas / 스키마

- `schemas/market_price_fact_candidate.schema.json`
- `schemas/market_price_review_assertion.schema.json`
- `schemas/reviewed_market_price_fact.schema.json`
- `schemas/draft_binding_proposal_v07.schema.json`

## Remaining merge procedure / 잔여 병합절차

1. Run fresh full Python 3.11/3.12 CI on the exact final documentation/head commit.
2. Update PR #59 with exact tested head + CI run.
3. Merge with `expected_head_sha`.
4. Confirm Issue #58 closes as completed.
5. Verify post-merge `main` Python 3.11/3.12 CI.
6. Re-ground latest main before selecting the next material gap.
