# M30-P1 Implementation Summary / 구현 요약

## Problem / 문제

M30-A proved that the original U.S. SEC debt route cannot satisfy historical M19 five-component completeness without inventing data. M30-P1 therefore adds a separate, reviewed exact-aggregate successor rather than relaxing M19.

## Runtime changes / 런타임 변경

### `src/valuation_hub/sec_aggregate_debt.py`

Implements:

1. exact SEC aggregate-debt candidate extraction;
2. deterministic normalization;
3. explicit human semantic review assertion;
4. reviewed `NORMALIZED_FACT` profile;
5. fresh/stale evaluated `DERIVED_FACT` debt binding context.

The accepted SEC identity is exactly:

`us-gaap:DebtLongtermAndShorttermCombinedAmount`

No fallback taxonomy or concept is used.

### `src/valuation_hub/debt_draft_binding_m30.py`

Adds `draft-binding-proposal-v0.2-sec-aggregate-debt`. It projects the reviewed SEC profile into `equity.debt` while preserving profile/review/context SHA lineage and leaving all other v0.1 decisions unchanged.

### `src/valuation_hub/debt_draft_binding.py`

Adds a lazy explicit dispatcher for the M30 successor. Historical v0.1/v0.2 validation behavior is delegated unchanged.

## Regression coverage / 회귀 검증

`tests/test_m30_sec_aggregate_debt_successor.py` proves:

- exact extraction and review lifecycle;
- missing concept blocking;
- equal-precedence conflict blocking;
- re-signed exact-concept tamper blocking;
- re-signed semantic-boundary tamper blocking;
- M20 successor creation;
- M23 → M28 wrapper compatibility;
- complete 13-field human approval and application;
- empty unresolved matrix;
- correct `equity.debt` application;
- M29 `promotion_ready=true`.

The first integration run exposed a test-dispatch error: the v0.8 result was incorrectly sent directly to the M26 validator. The test was corrected to use the M28 latest dispatcher. No production relaxation was made.

Implementation checkpoint:

- head: `a75ef1944ff5ff5d79c99ecf56edf18cb9905683`
- CI: `34795493944`
- Python 3.11: success
- Python 3.12: success

## Schema contract / 스키마 계약

M30-P1 adds explicit schemas for:

- SEC aggregate-debt candidate
- normalized observation
- human review assertion
- reviewed debt profile
- SEC aggregate debt binding context
- successor Draft binding proposal

## Governance result / 거버넌스 결과

M30-P1 resolves an architectural prerequisite only. It does not itself prove a real-company canonical valuation. The parent M30 mission must still capture real source bytes, obtain required human review, complete the M20–M29 lifecycle, create an admission plan, and merge a separate canonical-case PR.