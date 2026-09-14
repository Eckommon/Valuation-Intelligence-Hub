# M30-P1 Acceptance / 완료조건

## Functional / 기능

- [x] exact `us-gaap:DebtLongtermAndShorttermCombinedAmount` extraction from M13 SEC snapshot lineage
- [x] missing concept fails closed; explicit numeric zero remains a valid numeric fact
- [x] exact instant date, form, accession, filed date, snapshot SHA, and body SHA preserved
- [x] normalized candidate remains `NORMALIZED_FACT_CANDIDATE`
- [x] explicit human semantic review assertion with exact scope SHA
- [x] reviewed profile becomes `NORMALIZED_FACT` only after review
- [x] deterministic M20-compatible `DERIVED_FACT` binding context
- [x] successor proposal is `draft-binding-proposal-v0.2-sec-aggregate-debt`
- [x] successor never claims historical `COMPLETE_CORE_COMPONENTS`
- [x] total-liabilities substitution prohibited
- [x] missing-as-zero prohibited
- [x] lease-liability exclusion requires explicit filing reconciliation

## Integrity / 무결성

- [x] exact concept identity tamper fails even after outer re-hash
- [x] reviewed semantic-boundary tamper fails even after profile re-hash
- [x] equal-precedence conflicting SEC facts fail closed
- [x] stale debt context cannot become `DIRECT_BIND`
- [x] profile SHA + review assertion SHA + context SHA remain in downstream lineage
- [x] historical M19/M20 validators/builders remain backward compatible

## End-to-end compatibility / 종단간 호환성

- [x] successor passes M23 diluted-share wrapper
- [x] successor passes M24 WACC wrapper
- [x] successor passes M25 terminal-growth wrapper
- [x] successor passes M26 six-field atomic forecast wrapper
- [x] successor passes M27 market-price wrapper
- [x] successor passes M28 minority-interest wrapper
- [x] complete M28 result reaches 13/13 `DIRECT_BIND`
- [x] human binding approval covers 13/13 material fields
- [x] application produces 13 unique diffs and `unresolved=[]`
- [x] `equity.debt` receives the reviewed SEC aggregate-debt value
- [x] M29 complete candidate reaches `promotion_ready=true`

## Repository contract / 저장소 계약

- [x] candidate JSON Schema
- [x] normalized observation JSON Schema
- [x] review assertion JSON Schema
- [x] reviewed profile JSON Schema
- [x] SEC aggregate debt binding-context JSON Schema
- [x] successor binding-proposal JSON Schema
- [x] bilingual methodology / implementation documentation
- [x] exact-head Python 3.11/3.12 CI success at implementation checkpoint `a75ef1944ff5ff5d79c99ecf56edf18cb9905683`, run `34795493944`
- [ ] final docs/schema head Python 3.11/3.12 CI success
- [ ] PR #69 merged using exact tested head
- [ ] Issue #68 completed
- [ ] post-merge `main` Python 3.11/3.12 CI success

## Canonical-write boundary / 정식 쓰기 경계

M30-P1 is infrastructure only. It MUST NOT add a real or synthetic case to `registry/cases.json`. The parent M30 real-case mission resumes only after the final merge and post-merge CI gates above are green.