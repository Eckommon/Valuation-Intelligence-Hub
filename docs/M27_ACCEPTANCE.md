# M27 Acceptance / M27 완료계약

## Mission

Govern an exact valuation-date market-price observation as a source-backed fresh market `FACT`, then bind only a human-reviewed eligible package into `market_price` through the existing noncanonical Draft approval/apply flow.

## Acceptance checklist

- [x] Market price remains `FACT`, never `ASSUMPTION`.
- [x] `FACT_CANDIDATE` and reviewed `FACT` authority are distinct.
- [x] Positive as-traded price, currency, entity/scope, instrument, symbol, venue, quote type, trading date, quote timestamp and valuation `as_of` are explicit.
- [x] Only `OFFICIAL_CLOSE` and `LAST_TRADE` are supported in v0.1.
- [x] Price basis is explicitly `AS_TRADED_PER_SHARE`.
- [x] Tier A/B source provenance and source snapshot SHA are required for review eligibility.
- [x] Trading date after valuation `as_of` fails closed.
- [x] Freshness is independently recomputed from trading date and explicit max-age policy.
- [x] Stale quotes cannot become review-eligible.
- [x] Historical-price substitution and silent split adjustment are forbidden.
- [x] Human review locks candidate/source/quote identity/freshness/reviewer/time/basis.
- [x] Human approval cannot predate quote observation.
- [x] Outer re-signing cannot bypass nested candidate/review chronology validation.
- [x] `draft-binding-proposal-v0.7` accepts only validated v0.6 base.
- [x] v0.7 replaces only `market_price`.
- [x] Entity/scope/currency/as-of compatibility is exact.
- [x] Cash/debt/diluted shares/WACC/terminal growth/all forecast decisions remain unchanged.
- [x] M17 apply changes only top-level Draft `market_price` when that field is approved.
- [x] Applied diff preserves package/source-snapshot/review/quote lineage.
- [x] M26 unique-diff-field and all-six forecast atomicity protections remain preserved.
- [x] Input Draft remains unchanged and result remains noncanonical.
- [x] CLI is additive and older M1–M26 commands delegate unchanged.
- [x] Web is preparation/validation only; no Draft or canonical write path.
- [x] Machine-readable schemas exist for candidate, review assertion, reviewed FACT, and v0.7 proposal.
- [ ] Final-head Python 3.11 CI success recorded.
- [ ] Final-head Python 3.12 CI success recorded.
- [ ] PR merged from exact tested head SHA.
- [ ] Issue #58 closes as completed.
- [ ] Post-merge `main` Python 3.11/3.12 CI success recorded.

## Merge gate

Do not merge if any path can bind an unreviewed/stale/Tier-C-or-D quote, infer a quote type or corporate-action transform, approve a quote before it was observed, mutate any v0.6 material decision other than `market_price`, bypass M26 result-integrity hardening, or expose direct Draft/canonical write through M27 Web preparation routes.
