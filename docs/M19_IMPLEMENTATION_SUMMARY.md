# M19 Implementation Summary / M19 구현 요약

## Delivered / 구현

- isolated source mappings in `src/valuation_hub/debt_components.py`
- SEC exact `ShortTermBorrowings` support only
- OpenDART exact five-component BS mappings
- isolated `debt-component-observation-v0.1` normalization
- governed `interest-bearing-debt-evidence-v0.1` aggregation
- complete / partial / conflict coverage semantics
- full input lineage + source concept/account details + SHA-256 integrity
- CLI source extraction, normalization, component validation, aggregation, aggregate validation
- read-only `/debt` Web Lab
- regression tests preserving M13/M14 registries

## Key safety decisions / 핵심 안전판단

- `liabilities ≠ debt`
- broad SEC `LongTermDebt*` concepts are not forced into narrow component categories
- missing components are never zero
- conflict blocks every numeric debt total
- equal duplicate candidate evidence still keeps aggregate authority candidate
- lease liabilities are excluded until a separate policy exists
- M19 does not mutate a Draft

## Next logical mission / 다음 논리적 미션

After M19 closes, integrate only `COMPLETE_CORE_COMPONENTS + DERIVED_FACT` debt evidence into the governed M16/M17 binding proposal and human-approval flow. Partial, conflict-blocked, or candidate debt must remain non-bindable.
