# M15 Implementation Summary / M15 구현요약

## Delivered / 구현

- `src/valuation_hub/financial_normalization.py`
  - SEC candidate normalization
  - OpenDART candidate normalization
  - normalized observation validation
  - four-quarter TTM
  - annual-bridge TTM
  - same-period reconciliation
  - deterministic SHA-256 locking
- `schemas/financial_observation.schema.json`
- `schemas/financial_ttm.schema.json`
- thin CLI commands through `valuation_hub.cli_entry`
- read-only Web Normalization Lab through `valuation_hub.web_normalization`
- regression/invariant tests in `tests/test_financial_normalization.py`
- CLI/Web boundary tests in `tests/test_m15_interfaces.py`

## Safety boundaries / 안전경계

M15 does not fetch live data, persist normalized results, mutate Draft/Candidate state, promote evidence, or write canonical repository state. Existing M13/M14 source adapters remain the only live-evidence ingress paths in this phase.

M15는 live data 수집, 정규화 결과 영속화, Draft/Candidate 상태변경, 근거 승격, 정식 저장소 기록을 수행하지 않는다.

## Semantic rules / 의미규칙

- SEC 10-Q duration candidates require explicit quarter/YTD declaration.
- OpenDART report code and amount basis determine quarter/YTD/annual semantics.
- no calendar dates are invented for OpenDART rows that expose report-stage identity only.
- TTM compatibility requires same metric/entity/financial scope/unit.
- conflicts never average.
- arithmetic preserves the weakest input authority.

## Next architectural gap / 다음 구조적 간극

After M15, the highest-value next step is not another raw-source adapter. It is a governed **evidence-to-model binding layer** that maps reviewed/normalized financial observations into valuation Draft inputs with explicit mapping, completeness, staleness, and override rules while preserving human review before canonical admission.
