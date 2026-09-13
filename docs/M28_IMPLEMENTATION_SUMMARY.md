# M28 Implementation Summary / M28 구현요약

## What M28 adds / M28 추가사항

M28 closes the final equity-FCFF material-field gap: `equity.minority_interest`.

```text
exact immutable source snapshot
→ minority-interest FACT_CANDIDATE
→ NORMALIZED_FACT_CANDIDATE
→ SHA-locked human review/date resolution
→ reviewed NORMALIZED_FACT
→ draft-binding-proposal-v0.8
→ human-approved noncanonical Draft result
```

## Exact source boundary / 정확한 출처경계

SEC:

```text
us-gaap:NonredeemableNoncontrollingInterest
```

OpenDART:

```text
CFS + BS + ifrs-full_NoncontrollingInterests
```

M28 does not derive minority interest from total equity, parent equity, or liabilities. It excludes redeemable NCI from the v0.1 SEC field boundary. Missing source evidence is not converted to zero; explicit reported zero remains valid.

## Date and freshness / 날짜·최신성

SEC instant facts retain the exact source period end. OpenDART report-stage-only evidence requires a human exact-date assertion. Review and package validators recompute date resolution, chronology, freshness, and integrity hashes.

Stale reviewed evidence is preserved as reviewed context but cannot become DIRECT_BIND eligible.

## v0.8 / v0.8

`draft-binding-proposal-v0.8` wraps validated v0.7 and replaces only `equity.minority_interest`. It embeds the full reviewed package and retains the complete v0.7 base proposal.

Validation independently proves:
- base is v0.7 and still valid;
- minority-interest package is reviewed and fresh;
- entity/scope/currency/as-of match;
- all non-minority decisions are unchanged;
- projected baseline and lineage hashes match;
- completeness and final proposal SHA recompute exactly.

## Apply / 적용

The successor binding-apply layer adds minority-interest support without weakening M24–M27 semantics. The input Draft remains immutable. Result validation reconstructs the approved mutation and retains M26's unique-diff-field integrity rule.

## Interfaces / 인터페이스

The installed console wrapper is `cli_entry_m28`, delegating all older commands through `cli_entry_m27`. The Web Lab at `/minority-interest` is preparation/validation only.

Machine-readable contracts:
- `schemas/minority_interest_candidate.schema.json`
- `schemas/minority_interest_observation.schema.json`
- `schemas/minority_interest_review_assertion.schema.json`
- `schemas/reviewed_minority_interest_fact.schema.json`
- `schemas/draft_binding_proposal_v08.schema.json`

## Regression hardening / 회귀 강화

Tests cover exact mappings, missing-vs-zero semantics, OpenDART human date resolution, re-signed mapping/date/freshness tampering, stale non-bindability, v0.7-only base requirement, single-field v0.8 replacement, Draft immutability, lineage preservation, additive CLI delegation, and Web no-write boundaries.
