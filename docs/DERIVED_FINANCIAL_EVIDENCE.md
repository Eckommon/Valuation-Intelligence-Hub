# Derived Financial Evidence v0.1 / 파생재무근거 v0.1

## Purpose / 목적

M18 introduces a governed layer for arithmetic relationships that are **historically exact and semantically explicit**. It does not create forecast assumptions and it does not upgrade evidence authority.

M18은 **역사적으로 정확하고 의미가 명시적인 산술관계**만 파생하는 거버넌스 계층입니다. 미래 가정을 만들거나 근거 권위를 승격하지 않습니다.

## Supported derivations / 지원 파생식

```text
historical_operating_margin = operating_income / revenue
historical_net_income_margin = net_income / revenue
```

The denominator must be nonzero.

## Compatibility contract / 호환성 계약

The two source observations must already be valid `financial-observation-v0.1` objects and must have exactly matching:

- entity ID
- financial scope/perimeter
- source monetary unit
- complete normalized period identity

No currency conversion, period bridging, entity mapping, or perimeter mapping occurs in M18.

## Authority propagation / 권위 전파

```text
NORMALIZED_FACT + NORMALIZED_FACT
→ DERIVED_FACT

any NORMALIZED_FACT_CANDIDATE input
→ DERIVED_FACT_CANDIDATE
```

All outputs remain:

```text
canonical=false
```

Arithmetic never turns a candidate into a reviewed fact.

## Semantic boundary / 의미경계

Every result carries:

```json
{
  "historical_only": true,
  "forecast_direct_bind": false
}
```

Therefore:

```text
historical_operating_margin ≠ forecast ebit_margin
historical_net_income_margin ≠ forecast profit assumption
```

M16 continues to reject derived historical evidence as a direct forecast-binding input.

## Integrity / 무결성

`derived-financial-evidence-v0.1` records:

- derivation rule and exact formula
- numerator/denominator metrics and values
- source monetary unit
- exact source observation SHA-256 hashes
- propagated source authority classes
- entity/scope/period identity
- deterministic `derived_sha256`

Any mutation of arithmetic, lineage, identity, authority, or semantic boundary invalidates the derived SHA.

## CLI

```bash
vih derive-operating-margin operating-income.json revenue.json > operating-margin.json
vih derive-net-margin net-income.json revenue.json > net-margin.json
vih derived-validate operating-margin.json
```

## Web

```text
/derived
POST /api/derived/calculate
POST /api/derived/validate
```

The Web layer is calculate/validate only. It has no file-write, Draft-apply, promotion, admission, or canonical-write endpoint.

## Explicit non-goals / 명시적 비목표

M18 v0.1 does **not** perform:

- `liabilities → debt`
- `shares_outstanding → diluted_shares`
- forecast margin generation
- tax-rate forecasting
- currency conversion
- cross-period averaging
- automatic Draft mutation

These require separate governed contracts.
