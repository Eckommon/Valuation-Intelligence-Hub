# M30-P1 Reviewed SEC Aggregate Debt Successor / 검토형 SEC Aggregate Debt Successor

## Purpose / 목적

M30-A exposed a real U.S.-equity blocker: historical M19 requires five explicit debt components to reach `COMPLETE_CORE_COMPONENTS`, while the original SEC path supports only `short_term_borrowings`.

M30-P1 resolves that blocker **without weakening or reinterpreting M19/M20**. It adds a separate successor path for the exact SEC CompanyFacts concept:

`us-gaap:DebtLongtermAndShorttermCombinedAmount`

The historical five-component path remains valid and unchanged.

## Authority lifecycle / 권위 수명주기

```text
immutable M13 SEC CompanyFacts snapshot
        ↓
exact aggregate-debt fact
        ↓
FACT_CANDIDATE
        ↓ deterministic normalization
NORMALIZED_FACT_CANDIDATE
        ↓ explicit human semantic review + SHA scope lock
NORMALIZED_FACT reviewed profile
        ↓ deterministic projection
DERIVED_FACT debt binding context
        ↓
draft-binding-proposal-v0.2-sec-aggregate-debt
        ↓
M23 → M24 → M25 → M26 → M27 → M28
        ↓
human binding approval / apply
        ↓
M29 promotion handoff
```

No step writes canonical state.

## Exact-source rule / 정확 출처 규칙

The extractor has no concept fallback. It accepts only `us-gaap:DebtLongtermAndShorttermCombinedAmount` in an immutable SEC snapshot and preserves:

- snapshot SHA-256
- response-body SHA-256
- taxonomy and concept
- filing accession
- filing form and filed date
- exact period end
- value and unit

Missing concept is not zero. Equal-precedence conflicting values are blocked.

## Semantic boundary / 의미경계

The aggregate number is not automatically equivalent to the project's historical debt boundary. A human reviewer must explicitly establish from the issuer filing that the selected value is appropriate under the project policy.

The reviewed profile therefore fixes:

```text
total_liabilities_used     = false
missing_as_zero            = false
lease_liabilities_included = false
basis = EXPLICIT_FILING_RECONCILIATION_EXCLUDES_LEASE_LIABILITIES
```

`liabilities != debt`. Total liabilities, inferred zeros, label-only mappings, and unsupported subtraction are prohibited.

## Human-review boundary / 인간검토 경계

AI may extract, normalize, validate, hash, compare, and prepare the review scope. AI must not manufacture the semantic approval.

The review assertion SHA-locks the exact normalized observation and filing accession. Post-review changes to the source value, exact concept identity, semantic boundary, observation lineage, or review scope fail validation even when an outer object is re-hashed.

## Successor compatibility / successor 호환성

The M20 successor does **not** claim `COMPLETE_CORE_COMPONENTS`. Instead it records the actual reviewed SEC profile used through:

- `source_debt_profile_sha256`
- `review_assertion_sha256`
- `source_debt_sha256`
- `source_context_sha256`

`debt_draft_binding.validate_binding_proposal_any()` dispatches the successor explicitly and delegates all historical v0.1/v0.2 behavior unchanged.

The integration regression proves that the successor can traverse M23–M28, receive all-13 human binding approval, apply all 13 fields with no unresolved matrix, and reach M29 promotion readiness.

## Non-goals / 비목표

M30-P1 does not:

- admit Ingredion or any other company to `registry/cases.json`;
- fabricate a real SEC snapshot;
- automatically approve debt semantics;
- replace the legacy component path;
- write a canonical case;
- bypass promotion/admission/guarded repository-plan governance.

## Real-case consequence / 실기업 경로에 대한 효과

After M30-P1 becomes canonical, M30 may re-run the real-case preflight using this successor instead of returning the architectural blocker `M19_SEC_COMPLETE_DEBT_PROFILE_UNAVAILABLE` when the exact SEC concept is available. Actual source capture and human semantic review remain separate runtime gates.