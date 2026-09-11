# Financial Evidence Normalization + TTM / 재무근거 정규화 + TTM

## Purpose / 목적

M15 converts already-captured SEC/OpenDART evidence into deterministic period-aware observations and reproducible TTM transforms. It is a transformation layer, not a source-ingestion, forecasting, review, or canonicalization shortcut.

M15는 이미 수집된 SEC/OpenDART 근거를 결정론적 기간정규화 observation과 재현 가능한 TTM으로 변환한다. source 수집·예측·검토·정식화 우회계층이 아니다.

## Authority propagation / 권위 전파

```text
FACT           → NORMALIZED_FACT
FACT_CANDIDATE → NORMALIZED_FACT_CANDIDATE
```

All M15 outputs remain `canonical=false`. Arithmetic cannot promote evidence authority.

## Period kinds / 기간종류

- `INSTANT`
- `DURATION_QUARTER`
- `DURATION_YTD`
- `DURATION_ANNUAL`
- `DURATION_TTM`
- `UNKNOWN_PERIOD` reserved for future explicitly-unusable observations

### SEC

- balance-sheet/instant metrics require no `start` date;
- 10-K duration metrics are annual only when duration is inside the safe annual range;
- 10-Q duration facts require explicit `DURATION_QUARTER` or `DURATION_YTD` declaration;
- the system never guesses quarter-vs-YTD from value magnitude.

### OpenDART

- BS current amount → `INSTANT`;
- nonannual IS/CIS `thstrm_amount` → `DURATION_QUARTER`;
- nonannual IS/CIS `thstrm_add_amount` → `DURATION_YTD`;
- annual IS/CIS current amount → `DURATION_ANNUAL`;
- OpenDART report-stage identity is preserved; exact calendar dates are not invented.

## TTM transforms / TTM 변환

### Four-quarter sum

```text
TTM = Q[-3] + Q[-2] + Q[-1] + Q[0]
```

Requires exactly four contiguous fiscal quarters with identical metric, entity, financial scope, and unit.

### Annual bridge

```text
TTM = PRIOR_FY + CURRENT_YTD - PRIOR_COMPARABLE_YTD
```

Current and prior YTD must use the same report stage (`Q1`, `H1`, or `Q3`) and comparable fiscal years.

## Reconciliation / 조정

Same-period observations may reconcile only when metric/entity/scope/unit and period identity are identical. Equal values reconcile deterministically, preferring `NORMALIZED_FACT` over `NORMALIZED_FACT_CANDIDATE`. Conflicting values fail closed as `UNKNOWN_CONFLICT`; values are never averaged.

## Hash contract / 해시 계약

Normalized observations and TTM results are SHA-256 locked over canonical JSON bytes excluding only their own hash field.

- observation: `observation_sha256`
- TTM result: `ttm_sha256`

Any value, period, authority, lineage, or transform mutation invalidates the hash.

## Interfaces / 인터페이스

CLI:

```bash
vih normalize-sec sec-candidate.json --period-kind DURATION_QUARTER
vih normalize-dart dart-candidate.json --amount-basis CURRENT
vih normalize-validate observation.json
vih ttm-four-quarters q1.json q2.json q3.json q4.json
vih ttm-annual-bridge prior-fy.json current-ytd.json prior-ytd.json
vih ttm-validate ttm.json
vih normalize-reconcile observation-a.json observation-b.json
```

Web:

```text
/normalize
POST /api/normalize/one
POST /api/normalize/validate
POST /api/normalize/ttm-four
POST /api/normalize/ttm-bridge
POST /api/normalize/reconcile
POST /api/normalize/ttm-validate
```

The Web surface is calculate-only. It has no live-fetch, filesystem-write, promotion, admission, or canonical-write endpoint and rejects credential-bearing payloads.

## Non-goals / 비목표

- no forecasting assumptions
- no currency conversion
- no automatic FCFF Draft population
- no automatic source-to-canonical promotion
- no fuzzy account mapping
- no silent conflict averaging
- no invented period dates
