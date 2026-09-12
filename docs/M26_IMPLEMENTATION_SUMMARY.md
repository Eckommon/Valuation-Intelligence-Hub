# M26 Implementation Summary / M26 구현 요약

## Result / 결과

M26 implements one governed integrated FCFF forecast block instead of six independent forecast-field pipelines.

M26는 여섯 Forecast 필드를 각각 분리하지 않고 하나의 거버넌스된 통합 FCFF Forecast 블록으로 구현한다.

## New core / 신규 Core

- `src/valuation_hub/forecast_assumption.py`
  - candidate normalization
  - scenario/year-set invariants
  - numeric guards
  - EBIT/NOPAT/FCFF diagnostics
  - SHA-locked human review
  - reviewed `ASSUMPTION` package
- `src/valuation_hub/forecast_draft_binding.py`
  - v0.5-only base requirement
  - v0.6 enrichment
  - exactly six forecast decisions replaced
  - exact policy/baseline/lineage reconstruction
- `src/valuation_hub/binding_apply.py`
  - all-six-or-none approval
  - exact Draft scenario/year compatibility
  - scenario/year/component diff mapping
  - exact approved-field ↔ applied-diff field-set integrity gate

## Interfaces / 인터페이스

- `src/valuation_hub/cli_entry_m26.py`
- `src/valuation_hub/web_forecast.py`
- `pyproject.toml` routes `vih` through the additive M26 wrapper

Older commands delegate to M25 unchanged. M26 Web is preparation-only and has no Draft/file/canonical write endpoint.

기존 명령은 M25에 그대로 위임되며 M26 Web은 준비용으로만 작동한다.

## Schemas / 스키마

- `schemas/forecast_scenario_assumption_candidate.schema.json`
- `schemas/forecast_scenario_review_assertion.schema.json`
- `schemas/reviewed_forecast_scenario_assumption.schema.json`
- `schemas/draft_binding_proposal_v06.schema.json`

## Tests / 테스트

- `tests/test_m26_integrated_forecast_binding.py`
- `tests/test_m26_result_diff_hardening.py`
- `tests/test_m26_hardening.py`
- `tests/test_m26_interfaces.py`

Covered behavior includes candidate arithmetic, authority separation, common future-year sets, numeric guards, nested tamper detection, exact v0.5→v0.6 enrichment, all-six-or-none approval, Draft immutability, exact target sets, diff lineage, additive CLI delegation, Web no-write behavior, and outer-SHA re-signing hardening.

## Security hardening discovered during implementation / 구현 중 발견된 강화사항

A pre-hardening result validator checked only `len(applied_diffs) == len(approved_fields)`. A deliberately forged result could repeat one sequentially valid diff and omit another approved field while re-sealing the outer result hash.

기존 result validator는 diff 개수만 확인했기 때문에 하나의 유효 diff를 반복하고 다른 승인필드 적용을 누락한 뒤 outer hash를 재봉인할 여지가 있었다.

M26 now enforces:

```text
unique(applied_diff.field)
AND
set(applied_diff.field) == set(approved_fields)
```

The exploit fixture was first committed as a failing regression test, then turned green by the production guard.

공격 재현 테스트를 먼저 실패 상태로 고정한 뒤 production guard로 green 전환했다.

## CI checkpoints / CI 체크포인트

- initial core head `06dacd6806b32b1b9d168e6bc63497303866f049`
  - CI `34708138491`: Python 3.11/3.12 `success`
- exploit reproduction test-only head `2b30bbfe0372e51358a42b6d3df03c60a3699220`
  - CI `34708359543`: expected `failure`
- hardened core + re-signing tests head `1e225fccea82ba14d404d808fbedeffac6fb3f42`
  - CI `34708455989`: Python 3.11/3.12 `success`
- interface/schema head `ad6fcf8b5107f33b7d69c21b5a69ff6acdb21c86`
  - CI `34708632795`: Python 3.11/3.12 `success`

A fresh final-head CI is still required after documentation and canonical handoff updates.

문서 및 정식 handoff 반영 후 exact final-head CI를 새로 통과해야 한다.
