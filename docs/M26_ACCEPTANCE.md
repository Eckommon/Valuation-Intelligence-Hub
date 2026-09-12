# M26 Acceptance / M26 완료계약

## Mission / 미션

Govern the six explicit FCFF forecast-year inputs as one coherent, human-reviewed scenario package and bind them atomically into the equity-FCFF Draft.

명시기간 FCFF의 여섯 미래 입력을 하나의 일관된 인간검토 시나리오 패키지로 거버넌스하고 equity-FCFF Draft에 원자적으로 바인딩한다.

## Acceptance checklist / 완료 체크리스트

- [x] Forecast rows remain `ASSUMPTION_CANDIDATE` until human review.
- [x] Reviewed package is `ASSUMPTION`, never FACT/NORMALIZED_FACT.
- [x] Scenario names are explicit, canonicalized, and unique.
- [x] Every scenario has an explicit rationale.
- [x] All scenarios use one identical strictly ascending future-year set.
- [x] Every forecast year is after the valuation `as_of` year.
- [x] Every row contains revenue, EBIT margin, tax, D&A, CAPEX, and ΔNWC.
- [x] Numeric guards fail closed and reject non-finite values.
- [x] EBIT/NOPAT/FCFF diagnostics are independently recomputed.
- [x] Diagnostic tampering is rejected after outer SHA re-signing.
- [x] Human review locks candidate SHA, forecast-block SHA, methodology, identity, currency, as-of, scenario set, year set, reviewer, timestamp, and basis.
- [x] Approval cannot predate valuation `as_of`.
- [x] Reviewed package embeds and independently revalidates candidate + assertion.
- [x] `draft-binding-proposal-v0.6` accepts only validated v0.5 base.
- [x] Forecast package entity/scope/currency/as-of must match the base proposal.
- [x] Forecast scenario set must equal the v0.5 terminal-growth scenario set.
- [x] v0.6 replaces exactly six `scenario.years.*` material decisions.
- [x] WACC, terminal growth, cash, debt, diluted shares, conflicts, and other base decisions remain unchanged.
- [x] v0.6 policy is reconstructed exactly; policy weakening + outer re-sign fails.
- [x] Forecast baseline projection is reconstructed exactly; projection tamper + outer re-sign fails.
- [x] M17 forecast approval is all-six-or-none.
- [x] Draft scenario and ordered year sets must exactly match the reviewed package.
- [x] Applied diffs preserve package SHA, forecast-block SHA, review assertion SHA, scenario names, forecast years, and component.
- [x] Bound-result validator requires unique diff fields exactly equal to approved fields.
- [x] Duplicate-diff / omitted-approved-field re-signing exploit is regression-blocked.
- [x] Input Draft remains unchanged; result remains `canonical=false`.
- [x] CLI is additive and older M1–M25 commands delegate unchanged.
- [x] Web is calculate/validate preparation only; no Draft/file/canonical write route.
- [x] M1–M25 regressions remain required.
- [ ] Final-head Python 3.11 CI success recorded.
- [ ] Final-head Python 3.12 CI success recorded.
- [ ] PR merged from exact tested head SHA.
- [ ] Issue #56 closed as completed.
- [ ] Post-merge `main` Python 3.11/3.12 CI success recorded.

## Merge gate / 병합 게이트

Do not merge if any path can partially approve/apply the six forecast fields, silently create/reorder years, derive forecast authority from historical facts or diagnostics, weaken the v0.6 policy through outer re-signing, omit an approved diff, or mutate canonical state from an M26 preparation surface.

여섯 Forecast 필드의 부분 승인·적용, 연도 암묵 생성·재정렬, 과거사실/진단값에서 Forecast 권위 자동생성, outer 재서명에 의한 v0.6 정책 약화, 승인 diff 누락, M26 준비화면에서 canonical state 변경이 가능한 경우 병합하지 않는다.
