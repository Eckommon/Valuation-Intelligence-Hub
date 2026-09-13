# M28 Acceptance / M28 완료계약

## Mission / 미션

Close the final remaining equity-FCFF material-input gap with governed minority-interest FACT evidence and v0.8 Draft binding.

거버넌스 비지배지분 FACT와 v0.8 Draft 바인딩으로 equity-FCFF 중요입력의 마지막 공백을 닫는다.

## Acceptance checklist / 완료조건

- [x] M13 SEC and M14 OpenDART historical registries remain unchanged.
- [x] SEC adapter uses exact `us-gaap:NonredeemableNoncontrollingInterest` only.
- [x] OpenDART adapter uses exact `ifrs-full_NoncontrollingInterests` CFS balance-sheet account only.
- [x] Missing concept/account fails closed and is never interpreted as zero.
- [x] Explicit zero is preserved as valid evidence.
- [x] Equal-precedence source conflict fails closed.
- [x] Candidate and reviewed `NORMALIZED_FACT` authority states remain separate.
- [x] SEC exact date cannot be overridden by human assertion.
- [x] OpenDART `REPORT_STAGE_ONLY` requires SHA-locked human exact-date assertion.
- [x] Freshness is independently recomputed and stale package is non-bindable.
- [x] Nested candidate, observation, review assertion, package, and source SHA lineage is independently validated.
- [x] Re-signing an outer SHA cannot legitimize source mapping, date, or freshness tampering.
- [x] v0.8 accepts only validated v0.7 base proposal.
- [x] v0.8 may replace only `equity.minority_interest`.
- [x] Exact entity/scope/currency/as-of compatibility is required.
- [x] Existing market price, cash, debt, diluted shares, WACC, terminal growth, and six forecast-field decisions remain unchanged.
- [x] Human approval remains mandatory for apply.
- [x] Apply changes only `draft.equity.minority_interest` in the noncanonical result.
- [x] Input Draft remains immutable.
- [x] Applied diff preserves package/observation/snapshot/review lineage.
- [x] M26 unique-diff-field result-integrity protection remains active.
- [x] CLI successor delegation keeps M1-M27 commands intact.
- [x] Web/CLI preparation surfaces expose no direct file/canonical write.
- [ ] Exact final-head Python 3.11 CI success recorded.
- [ ] Exact final-head Python 3.12 CI success recorded.
- [ ] PR merged from exact tested head SHA.
- [ ] Issue #60 completed.
- [ ] Post-merge `main` Python 3.11/3.12 CI success recorded.

## Merge gate / 병합 게이트

Do not merge if any path can infer zero from missing evidence, accept a non-exact source mapping, bypass nested lineage validation, bind stale evidence, mutate a field other than `equity.minority_interest`, or bypass human approval.
