# M30-R1 Governed SEC Aggregate-Debt CLI / 실기업 SEC Aggregate Debt 검토 CLI

## Purpose / 목적

M30-R1 exposes the already-canonical M30-P1 SEC aggregate-debt successor through the installed `vih` command surface so the first real-company execution can remain reproducible and auditable.

This change does **not** change debt semantics. It only exposes the existing runtime functions through an additive CLI wrapper.

## Authority lifecycle / 권위 수명주기

```text
immutable SEC CompanyFacts snapshot
  -> sec-aggregate-debt-extract
  -> FACT_CANDIDATE
  -> sec-aggregate-debt-normalize
  -> NORMALIZED_FACT_CANDIDATE
  -> explicit human semantic review
  -> reviewed NORMALIZED_FACT profile
  -> debt binding context (DERIVED_FACT)
  -> successor binding proposal
```

The pre-review extraction/normalization stages may run without human approval. The review assertion may only be created after a real human reviewer explicitly supplies the required review state.

## Commands / 명령

- `sec-aggregate-debt-extract`
- `sec-aggregate-debt-candidate-validate`
- `sec-aggregate-debt-normalize`
- `sec-aggregate-debt-observation-validate`
- `sec-aggregate-debt-review-build`
- `sec-aggregate-debt-review-validate`
- `sec-aggregate-debt-finalize`
- `sec-aggregate-debt-profile-validate`
- `sec-aggregate-debt-context-build`
- `sec-aggregate-debt-context-validate`
- `binding-sec-aggregate-debt-build`
- `binding-sec-aggregate-debt-validate`

All other commands delegate unchanged to the M30 dispatcher and therefore to the historical CLI chain.

## Human-review boundary / 인간검토 경계

`sec-aggregate-debt-review-build` requires all of these explicitly:

- `--reviewer`
- `--reviewed-at` with timezone
- `--review-basis`
- `--source-basis-locator`
- `--semantic-scope-decision`

The semantic decision must be exactly:

`EXPLICIT_FILING_RECONCILIATION_EXCLUDES_LEASE_LIABILITIES`

There is no default reviewer, timestamp, review basis, filing locator, or semantic approval. The CLI does not infer approval from the SEC fact itself.

## Fail-closed semantic policy / 실패폐쇄 의미정책

The existing M30-P1 policy remains unchanged:

```text
total_liabilities_used     = false
missing_as_zero            = false
lease_liabilities_included = false
basis = EXPLICIT_FILING_RECONCILIATION_EXCLUDES_LEASE_LIABILITIES
```

A wrong semantic decision, timezone-naive review timestamp, SHA mismatch, stale context, changed source fact, or changed filing lineage fails validation.

## Installed entry point / 설치 진입점

`pyproject.toml` routes `vih` through `valuation_hub.cli_entry_m30r1:main`. After pulling a commit that changes this entry point, an existing local editable installation should be refreshed:

```powershell
python -m pip install -e ".[dev]"
```

## Real Ingredion resume point / Ingredion 실제 실행 재개점

After M30-R1 is merged and the local checkout is updated, the real M30-R execution should first run only the pre-review debt stages:

1. extract the exact `us-gaap:DebtLongtermAndShorttermCombinedAmount` candidate from the existing hash-locked Ingredion snapshot;
2. validate the candidate;
3. normalize it;
4. validate the normalized observation;
5. stop before `sec-aggregate-debt-review-build` until the actual human semantic review of the issuer filing has been performed.

M30-R1 itself performs no Draft mutation, registry write, canonical admission, or fabricated human approval.
