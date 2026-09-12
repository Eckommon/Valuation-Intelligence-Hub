# M24 Acceptance / M24 완료계약

## Mission

Create a governed WACC assumption package and bind only a reviewed, fresh, provenance-complete package to `scenario.wacc`, while preserving the distinction between source facts, deterministic calculation, analyst assumption, human review, Draft binding, and canonical repository state.

## Acceptance checklist

- [x] WACC is modeled as an assumption, never promoted to historical `FACT`/`NORMALIZED_FACT`.
- [x] `ASSUMPTION_CANDIDATE` and reviewed `ASSUMPTION` are distinct authority states.
- [x] Exactly seven required source components are explicit; no required component is silently defaulted.
- [x] Source records preserve value/unit/date/publisher/type/tier/locator/source SHA.
- [x] Fixed metric-specific freshness policy is independently recomputed.
- [x] Future-dated inputs fail closed.
- [x] Stale required inputs cannot enter human review.
- [x] Tier D required inputs cannot enter human review.
- [x] CAPM cost of equity is independently recomputed.
- [x] After-tax debt cost is independently recomputed.
- [x] Equity/debt market-value weights are independently recomputed.
- [x] WACC weights sum to one within strict tolerance.
- [x] Final WACC must fit Draft-valid range `0 < wacc <= 0.99`.
- [x] Missing/nonfinite arithmetic fields fail closed even if the candidate SHA is recomputed.
- [x] Human review assertion locks candidate SHA, method, as-of, scenarios, reviewer, approval time, and review basis.
- [x] Human review cannot predate valuation `as_of`.
- [x] Reviewed package embeds and revalidates the full candidate and review assertion.
- [x] `draft-binding-proposal-v0.4` wraps a validated v0.1/v0.2/v0.3 proposal.
- [x] v0.4 replaces only `scenario.wacc`.
- [x] v0.4 policy is reconstructed exactly; re-signing a weakened policy fails validation.
- [x] Entity, financial scope, capital currency, and `as_of` must match the base proposal.
- [x] Existing cash/debt/diluted-share decisions remain unchanged.
- [x] WACC proposal context preserves package SHA + review assertion SHA + scenario names.
- [x] M17 approval can approve WACC only when `scenario.wacc` is DIRECT_BIND.
- [x] WACC target scenario set must equal the Draft's entire scenario set exactly.
- [x] Apply records scenario-by-scenario before/after WACC values.
- [x] Input Draft remains unchanged.
- [x] Bound Draft result remains noncanonical.
- [x] Additive CLI wrapper preserves prior M1-M23 command dispatch.
- [x] Web `/wacc` is calculate/validate only with no apply/write/canonical route.
- [x] Five M24 JSON Schemas exist.
- [x] Initial core CI `34693139601` passed Python 3.11/3.12 on head `50722f589c5dc62cfe140540514c64fd85ca38ff`.
- [x] Hardened core CI `34693273291` passed Python 3.11/3.12 on head `c34fc9232aca459920727ce3502334c14fd940f2`.
- [x] Interface/schema CI `34693425090` passed Python 3.11/3.12 on head `df5882ab31204aea98cc31e05eae3942ba2a619f`.
- [ ] Final-head Python 3.11 CI success recorded.
- [ ] Final-head Python 3.12 CI success recorded.
- [ ] PR merged from exact tested head SHA.
- [ ] Issue #52 closed as completed.
- [ ] Post-merge `main` CI success recorded.

## Merge gate

Do not merge if WACC can become binding-eligible with stale/Tier-D/missing inputs, if arithmetic is trusted rather than recomputed, if review lineage can be re-signed around, if v0.4 changes a non-WACC decision, if scenario coverage is partial, if the input Draft is mutated, or if M24 exposes a direct write/canonicalization path.
