# M21 Acceptance / M21 완료계약

## Mission

Create governed historical dilution-reference evidence while preserving the boundary between EPS duration denominators and valuation-date fully diluted shares.

## Acceptance checklist

- [x] M13 SEC metric registry remains unchanged.
- [x] Only exact SEC `WeightedAverageNumberOfSharesOutstandingBasic` and `WeightedAverageNumberOfDilutedSharesOutstanding` concepts are supported.
- [x] Extraction requires explicit start/end dates and prevents quarter/YTD conflation.
- [x] Candidate and normalized observation objects remain `canonical=false` and SHA-locked.
- [x] Normalized observations are duration evidence with exact dates.
- [x] Historical derivation requires exact entity, unit, and full period identity.
- [x] `basic > 0` and `diluted >= basic` are fail-closed arithmetic rules.
- [x] Candidate authority propagates; arithmetic never upgrades authority.
- [x] Derived output recomputes factor and incremental shares during validation.
- [x] Derived output explicitly sets `historical_only=true`.
- [x] `valuation_date_direct_bind=false` and `forecast_direct_bind=false` are mandatory.
- [x] `shares_outstanding_substitution=false` is mandatory.
- [x] M16/M20 `equity.diluted_shares` remains unresolved.
- [x] CLI supports extract/normalize/observation-validate/derive/derived-validate.
- [x] Web dilution surface is calculate/validate only and has no Draft/canonical write path.
- [x] Observation and derived-evidence JSON Schemas exist.
- [x] M1-M20 regression suite remains required.
- [ ] Final-head Python 3.11 CI success recorded.
- [ ] Final-head Python 3.12 CI success recorded.
- [ ] PR merged from the exact tested head SHA.
- [ ] Post-merge `main` CI success recorded.

## Merge gate

Do not merge if any test or review shows that a duration-weighted EPS denominator can be treated as valuation-date fully diluted shares, that source authority is upgraded by calculation, or that an M21 interface can mutate a Draft or canonical repository state.