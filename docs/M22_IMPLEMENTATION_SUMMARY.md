# M22 Implementation Summary / M22 구현 요약

## Scope

M22 creates a governed valuation-date common-share base and a fail-closed bridge toward fully diluted shares.

## Core implementation

`src/valuation_hub/valuation_shares.py` adds:
- isolated exact SEC DEI common-share extraction;
- current-common-share candidate and reviewed instant observation;
- valuation share-base context with recomputable freshness;
- explicit typed dilution-adjustment evidence;
- SHA-locked human complete-coverage assertion;
- bridge reconciliation, arithmetic, coverage, authority and eligibility;
- full nested-source revalidation;
- M21 historical-dilution reference-only integration.

## Interface implementation

CLI adds:
- `share-sec-extract`
- `share-normalize`
- `share-observation-validate`
- `share-base-context-build`
- `share-base-context-validate`
- `share-adjustment-build`
- `share-adjustment-validate`
- `share-coverage-assertion-build`
- `share-coverage-assertion-validate`
- `share-bridge-build`
- `share-bridge-validate`

Web adds:
- `/shares`
- `/api/shares/*` calculate/validate endpoints

No M22 interface writes Draft or canonical state.

## Schemas

- `schemas/current_common_shares_observation.schema.json`
- `schemas/valuation_share_base_context.schema.json`
- `schemas/dilution_adjustment.schema.json`
- `schemas/dilution_coverage_assertion.schema.json`
- `schemas/diluted_share_bridge.schema.json`

## Tests

- `tests/test_m22_valuation_shares.py`
- `tests/test_m22_interfaces.py`

Tests cover exact SEC mapping, registry isolation, equal-precedence conflicts, reviewed-vs-candidate authority, independently recomputable freshness, stale bases, candidate and reviewed adjustments, complete human coverage, nested tamper detection, duplicate adjustment conflicts, no missing-as-zero, M21 reference-only behavior, CLI round-trip, and Web no-write presentation.

## Key architecture decision

M22 separates three different concepts that must not collapse into one field:

```text
historical EPS denominator evidence  (M21)
            !=
current common shares at a point in time  (M22 base)
            !=
fully diluted valuation denominator  (M22 complete bridge / future binding)
```

The bridge may calculate a candidate total before coverage is complete, but that calculation does not imply authority or direct-bind eligibility.

## Next boundary after M22

A subsequent milestone should extend the M16/M17/M20 binding path so **only** `COMPLETE_REVIEWED_DILUTION_COVERAGE + FRESH base + reviewed adjustment evidence` may replace the `equity.diluted_shares` classification. BASE_ONLY, PARTIAL, CONFLICT, stale, or candidate bridges must remain non-bindable.