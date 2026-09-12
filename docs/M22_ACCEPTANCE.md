# M22 Acceptance / M22 완료계약

## Mission

Build a governed valuation-date common-share base and explicit diluted-share bridge foundation without silently promoting current shares, historical EPS denominators, historical dilution factors, or missing adjustment categories into a fully diluted valuation denominator.

## Acceptance checklist

- [x] Exact `dei:EntityCommonStockSharesOutstanding` mapping only.
- [x] M13 and M21 source registries remain unchanged.
- [x] Equal-precedence conflicting current-share values fail closed.
- [x] Current-share observation is exact-date `INSTANT`, noncanonical, authority-preserving, and SHA-locked.
- [x] Only reviewed current-share facts can enter a valuation share-base context.
- [x] Base-context freshness is independently recomputable from `as_of` and the source instant date.
- [x] Current common shares are explicitly not fully diluted shares.
- [x] Dilution adjustments are explicit, typed, nonnegative, source-linked evidence objects.
- [x] Candidate adjustments remain candidate authority until separately reviewed.
- [x] M21 historical dilution is reference-only and cannot auto-create an adjustment.
- [x] Missing dilution categories are never imputed as zero.
- [x] Human complete-coverage assertion locks the fresh base, reviewed adjustment set, reviewer, approval time, coverage basis, and all supported category reviews.
- [x] Bridge coverage states are explicit: BASE_ONLY / PARTIAL / COMPLETE / CONFLICT.
- [x] Duplicate adjustment IDs with distinct evidence are conflict-blocked and hide candidate totals.
- [x] Bridge embeds full nested source objects and revalidates them independently of the outer SHA.
- [x] BASE_ONLY/PARTIAL/CONFLICT cannot become future-direct-bind eligible.
- [x] Only complete + reviewed + fresh may be marked eligible for a future direct-bind integration.
- [x] CLI/Web are calculate/validate only; no Draft or canonical write path exists.
- [x] M1-M21 regressions remain required.
- [ ] Final-head Python 3.11 CI success recorded.
- [ ] Final-head Python 3.12 CI success recorded.
- [ ] PR merged from exact tested head SHA.
- [ ] Post-merge `main` CI success recorded.

## Merge gate

Do not merge if any path can equate current common shares with fully diluted shares, infer current dilution from M21 historical factors, treat omitted categories as zero without explicit human coverage review, upgrade candidate authority by arithmetic, or bypass nested source/assertion validation.