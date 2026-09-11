# M13 Acceptance Contract / M13 완료 계약

M13 may merge only if all of the following are true:

1. `sec-companyfacts-v0.1` constructs only the official SEC CompanyFacts locator from normalized CIK.
2. Live transport requires HTTPS, approved SEC hosts, identifying User-Agent, conservative rate limiting, bounded timeout/bytes, JSON and UTF-8.
3. User-Agent contents are not persisted in snapshots.
4. Source snapshots remain `canonical=false` and are locked by raw-body SHA-256 plus full snapshot SHA-256.
5. Snapshot validation reconciles requested CIK with payload CIK and detects body/metadata mutation.
6. Extraction remains `EVIDENCE_CANDIDATE_UNREVIEWED / FACT_CANDIDATE / canonical=false`.
7. Filing provenance includes taxonomy, concept, unit, accession, form, filed date and reporting period.
8. Concept fallback is explicit; equal-precedence conflicting values fail closed.
9. No TTM synthesis, normalization, automatic Draft binding, canonical write, or browser-origin live fetch exists in M13.
10. Snapshot materialization is workspace-only and refuses overwrite.
11. CI uses injected fixture transport and requires no external network.
12. All M1–M13 tests pass on Python 3.11 and 3.12.

병합 전 위 조건을 모두 만족해야 하며, 하나라도 실패하면 M13은 완료로 간주하지 않는다.
