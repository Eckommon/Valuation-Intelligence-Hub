# M21 Implementation Summary / M21 구현 요약

## Scope

M21 implements governed historical share-dilution reference evidence for SEC issuers while keeping valuation-date fully diluted shares unresolved.

## Added core

- `src/valuation_hub/share_dilution.py`
  - isolated SEC source mapping
  - exact start/end extraction
  - candidate validation
  - duration normalization
  - historical dilution derivation
  - authority propagation
  - SHA-256 integrity
  - non-binding semantic boundary

## Added interfaces

- CLI commands:
  - `dilution-sec-extract`
  - `dilution-normalize`
  - `dilution-observation-validate`
  - `dilution-derive`
  - `dilution-validate`
- Web:
  - `/dilution`
  - calculate/validate only

## Added schemas

- `schemas/share_dilution_observation.schema.json`
- `schemas/historical_dilution_evidence.schema.json`

## Added tests

- `tests/test_share_dilution.py`
- `tests/test_m21_interfaces.py`

The test contract covers exact SEC concept mapping, source-registry isolation, period separation, authority propagation, arithmetic validation, semantic non-binding boundaries, and no-write interfaces.

## Key model decision

The system intentionally distinguishes historical EPS denominator dilution from a valuation denominator:

```text
historical weighted-average diluted shares
    ↓
historical dilution factor/reference
    ✕
NOT valuation-date fully diluted shares
```

This prevents the common but material valuation error of inserting a period-weighted EPS denominator directly into per-share intrinsic-value calculations.

## Remaining problem after M21

`equity.diluted_shares` is still unresolved. A future mission should build a valuation-date share bridge from explicit evidence such as current common shares plus instrument-level dilution from options, RSUs, warrants, convertibles, contingent shares, treasury-stock-method effects, and other issuer-specific instruments. That future bridge must remain distinct from historical EPS denominator evidence.