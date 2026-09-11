# M14 Acceptance Contract / M14 완료 계약

M14 may merge only if all conditions below hold.

1. OpenDART authentication key remains transport-only and never appears in persisted snapshots, sanitized locators, Web payloads, normal CLI output, or evidence candidates.
2. Request identity is deterministic: exact `corp_code`, `bsns_year`, `reprt_code`, `fs_div` against the official HTTPS endpoint.
3. HTTP 200 with non-`000` OpenDART API status fails closed.
4. Snapshot raw body and metadata are protected by body SHA-256 and full snapshot SHA-256.
5. Snapshot validation rechecks row request identity and detects metadata/raw-body mutation.
6. Evidence candidates remain `DART_EVIDENCE_CANDIDATE_UNREVIEWED / FACT_CANDIDATE / canonical=false`.
7. CFS/OFS and statement sections cannot be silently crossed.
8. Account selection uses explicit exact account-id/name rules; fuzzy matching is absent.
9. Equal-precedence conflicting values fail closed; blank current-period values are not converted to zero.
10. `thstrm_add_amount` is preserved but not automatically interpreted as TTM/YTD.
11. CLI supports `dart-fetch`, `dart-snapshot-validate`, and `dart-extract` while legacy commands continue to delegate unchanged.
12. Web supports snapshot validation/extraction only, has no API-key field, and has no browser-origin live-fetch route.
13. CI uses deterministic fixtures/injected transport and no external OpenDART network calls.
14. All M1–M14 tests pass on Python 3.11 and 3.12.

위 조건 중 하나라도 실패하면 M14는 완료로 간주하지 않는다.
