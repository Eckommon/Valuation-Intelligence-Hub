# M30-D Real-Case Readiness Manifest / 실기업 준비도 Manifest

## Purpose / 목적

M30-D turns the remaining M30 workflow into a deterministic machine-readable plan before protected live-source credentials are supplied.

M30-D는 보호된 live-source 실행정보를 입력하기 전에 남은 M30 절차를 결정론적 machine-readable plan으로 변환한다.

It **does not** claim the real Ingredion case is ready. It identifies exactly why each governed input is not ready yet and what prerequisite must happen next.

## Exact material-field contract / 정확한 13필드 계약

The manifest inherits the existing M16 material-field tuple without modification:

1. `market_price`
2. `equity.diluted_shares`
3. `equity.debt`
4. `equity.cash`
5. `equity.minority_interest`
6. `scenario.wacc`
7. `scenario.terminal_growth`
8. `scenario.years.revenue`
9. `scenario.years.ebit_margin`
10. `scenario.years.tax_rate`
11. `scenario.years.depreciation_amortization`
12. `scenario.years.capex`
13. `scenario.years.delta_nwc`

No field is added, omitted, renamed, or manually reclassified.

## Authority / 권위

- `market_price` → `FACT`
- cash / minority interest → `NORMALIZED_FACT`
- diluted shares / debt → `DERIVED`
- WACC / terminal growth / six forecast fields → `ASSUMPTION`

Readiness is not authority promotion. A source candidate can move a field from `AWAITING_REAL_SOURCE` to `AWAITING_HUMAN_REVIEW`, but never directly to `READY`.

## Readiness states / 준비도 상태

- `READY` — governed prerequisite already satisfies the relevant boundary.
- `AWAITING_REAL_SOURCE` — authoritative source bytes/input are still required.
- `AWAITING_HUMAN_REVIEW` — source/candidate exists, but an explicit governed human action remains.
- `AWAITING_DEPENDENCY` — another governed artifact must be completed first.
- `BLOCKED` — a fail-closed blocker such as canonical registry collision prevents continuation.

## Prerequisite DAG / 선행조건 DAG

### Observed / derived equity inputs

```text
M13 SEC snapshot → M30-B preflight
                   ├─ cash candidate → reviewed normalized cash
                   ├─ shares candidate → reviewed diluted-share bridge
                   ├─ exact aggregate debt candidate → M30-P1 human semantic review → debt binding context
                   └─ exact NCI candidate → M28 human review

valuation-date price source → M27 reviewed market-price FACT
```

### M24 WACC

Exactly seven sourced inputs are represented:

- risk-free rate
- equity risk premium
- levered beta
- pre-tax cost of debt
- equity market value
- debt market value
- tax rate

```text
7 sourced inputs → WACC candidate → explicit human review → reviewed WACC ASSUMPTION
```

### M25 terminal growth

Exactly two source-backed macro anchors are represented:

- long-run inflation
- long-run real growth

```text
reviewed WACC + 2 macro anchors
        → terminal-growth candidate
        → explicit human review
        → reviewed terminal-growth ASSUMPTION
```

### M26 forecast

The six forecast fields remain one atomic governed block:

```text
explicit analyst scenario/year assumptions
        → integrated forecast candidate
        → explicit human review
        → reviewed forecast ASSUMPTION package
        → six forecast DIRECT_BIND decisions together
```

## Optional M30-B projection / 선택적 M30-B 투영

If no M30-B v0.2 preflight is supplied, the manifest records `REAL_SEC_PREFLIGHT_NOT_SUPPLIED` and remains source-waiting.

If a preflight is supplied, it is independently validated before projection. Candidate existence is used only to distinguish source-waiting from human-review-waiting. The full preflight is embedded for deterministic reconstruction.

A registry collision blocks all 13 material fields. A missing exact aggregate-debt concept keeps `equity.debt` in `AWAITING_REAL_SOURCE`. An available aggregate-debt candidate moves debt only to `AWAITING_HUMAN_REVIEW` because M30-P1 semantic review remains mandatory.

## Integrity / 무결성

The validator enforces:

- exact 13-field order and coverage;
- fixed field authority map;
- fixed field → prerequisite mapping;
- unique DAG node IDs;
- no unknown dependencies;
- no dependency cycles;
- deterministic reconstruction from target + embedded preflight;
- SHA-256 seal;
- no inferred review state.

## Non-goals / 비목표

M30-D does not:

- call SEC;
- require `SEC_USER_AGENT`;
- create source claims;
- fabricate reviewer identity or timestamp;
- approve debt semantics;
- mutate a Draft;
- write `registry/cases.json`;
- create an Ingredion canonical case.

The result remains noncanonical planning/readiness state only.
