# M18 Implementation Summary / 구현 요약

## Delivered / 구현

- `src/valuation_hub/derived_financial.py`
  - historical operating margin
  - historical net-income margin
  - authority propagation
  - compatibility guards
  - SHA-256 integrity validation
- `schemas/derived_financial_evidence.schema.json`
- CLI
  - `derive-operating-margin`
  - `derive-net-margin`
  - `derived-validate`
- Web
  - `/derived`
  - `POST /api/derived/calculate`
  - `POST /api/derived/validate`
- tests
  - `tests/test_derived_financial.py`
  - `tests/test_m18_interfaces.py`

## Safety boundary / 안전경계

M18 only derives historical ratios from already normalized evidence with exactly matching entity, financial scope, monetary unit, and period identity.

It does not derive debt from liabilities, diluted shares from shares outstanding, or any forecast assumption from historical values.

Every output remains noncanonical and explicitly blocks forecast direct binding.

## Resume implication / 다음 단계 의미

The next derivation milestone should expand only when a semantically exact component model exists. The highest-value candidate is interest-bearing debt assembled from explicit debt components, **not** total liabilities. Diluted shares likewise requires a separate security/dilution evidence contract rather than reusing basic shares outstanding.
