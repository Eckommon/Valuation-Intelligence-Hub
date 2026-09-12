# M23 Implementation Summary / M23 구현 요약

## Result / 결과

M23 introduces `draft-binding-proposal-v0.3`, a share-aware enrichment layer that connects only complete, reviewed, fresh M22 diluted-share bridges to `equity.diluted_shares` while preserving prior M16/M20 decisions.

## Architecture / 구조

```text
M16 v0.1 proposal ─┐
                   ├─ validated base proposal
M20 v0.2 proposal ─┘
          +
M22 diluted-share-bridge-v0.1
          ↓
M23 draft-binding-proposal-v0.3
          ↓
M17 binding-approval-v0.1
          ↓
noncanonical bound Draft result
```

The implementation intentionally avoids rebuilding the base proposal. `equity.diluted_shares` is the only matrix entry M23 may replace.

## Core files / 핵심 파일

- `src/valuation_hub/share_draft_binding.py`
  - v0.3 builder
  - v0.3 validator
  - chained proposal validator for v0.1/v0.2/v0.3
- `src/valuation_hub/binding_apply.py`
  - existing M17 approval lock reused
  - `equity.diluted_shares` get/set support
  - share-bridge lineage validation and applied diff support
- `src/valuation_hub/web_share_binding.py`
  - read/calculate-only M23 Web Lab
- `src/valuation_hub/cli_entry.py`
  - `binding-build-with-diluted-shares`
  - v0.3-aware `binding-validate`
  - M23 Web wrapper becomes the top-level server while retaining prior handlers
- `schemas/draft_binding_proposal_v03.schema.json`
- `tests/test_m23_binding.py`
- `tests/test_m23_interfaces.py`

## Eligibility / 적격성

A bridge can bind only when M22 validation independently confirms:

```text
COMPLETE_REVIEWED_DILUTION_COVERAGE
DERIVED_FACT
fresh base
valid human coverage assertion
eligible_for_future_direct_bind = true
positive candidate_fully_diluted_shares
```

Identity, financial scope, and `as_of` must match the base proposal exactly.

## Preservation / 보존

M23 preserves:

- v0.1 cash decision semantics,
- v0.2 debt decision semantics,
- base proposal conflicts,
- source observation lineage,
- M17 proposal/Draft SHA approval lock,
- input Draft immutability,
- noncanonical apply result semantics.

## Share apply lineage / 희석주식 적용 lineage

The v0.3 proposal projection and M17 applied diff preserve:

```text
source_bridge_sha256
base_context_sha256
coverage_assertion_sha256
```

The validator re-derives expected context and diff lineage rather than trusting only an outer proposal/result SHA.

## Interfaces / 인터페이스

CLI:

```text
binding-build-with-diluted-shares
binding-validate
binding-approval-build
binding-approval-validate
binding-apply
bound-draft-validate
```

Web:

```text
/share-binding
/api/share-binding/build
/api/share-binding/validate
```

The M23 Web layer deliberately has no approval/apply or write endpoint.

## CI checkpoints / CI 체크포인트

- Core head: `1dc2fee8cb400ef642f7dd64460bb60956a88a29`
  - CI `34692432321`
  - Python 3.11/3.12 success
- Interface/schema head: `005a1dd58dae6a2a3162c6a2b06629860540fffd`
  - CI `34692614288`
  - Python 3.11/3.12 success

A fresh final-head CI after documentation and canonical handoff changes remains the merge gate.
