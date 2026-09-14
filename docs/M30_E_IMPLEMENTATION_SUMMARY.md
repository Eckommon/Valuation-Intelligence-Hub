# M30-E Implementation Summary / 구현 요약

M30-E adds a generic immutable local-byte intake for non-SEC market/macro evidence while preserving the authority boundaries established by M24, M25, and M27.

## Added / 추가

- `src/valuation_hub/external_source.py`
- `schemas/external_source_snapshot_v01.schema.json`
- M30 CLI routes for external snapshot build/validate
- M30 CLI routes for snapshot-bound market-price, WACC, and terminal-growth source builders
- `tests/test_m30e_external_source.py`
- `tests/test_m30e_cli.py`
- `docs/M30_E_EXTERNAL_SOURCE_INTAKE.md`
- `docs/M30_E_ACCEPTANCE.md`

## Core flow / 핵심 흐름

```text
already-acquired external UTF-8 bytes
→ external-source-snapshot-v0.1 / NOT CANONICAL
→ body SHA + snapshot SHA validation
→ snapshot-bound M27/M24/M25 source artifact
→ existing downstream validation and human-review lifecycle
→ canonical only through the existing governed promotion/admission path
```

The snapshot does **not** certify that a publisher identity or economic claim is externally true. It creates an internally consistent immutable envelope that binds selected source text to the provenance metadata used downstream.

snapshot은 publisher identity나 경제적 claim의 외부 진실성을 인증하지 않는다. 선택된 원문과 downstream provenance metadata가 서로 분리되지 않도록 내부적으로 일관된 불변 envelope를 만든다.

## Safety / 안전경계

- no arbitrary URL fetch
- HTTPS locator required
- no embedded credentials
- no headers/cookies/auth/API keys persisted
- local UTF-8 intake only
- output restricted to `workspace/source_snapshots`
- no overwrite
- no automatic authority promotion
- no automatic human review
- no Draft or registry/canonical write

## Provenance lock / provenance 잠금

Source-bound builders reject independent provenance override arguments. Independent validators compare downstream artifacts back to the selected snapshot so publisher/type/tier/locator/SHA divergence fails closed even if the downstream artifact has been re-hashed.

## Compatibility / 호환성

M30-E is additive. Historical M27/M24/M25 manual source-building commands remain available for backward compatibility, while the M30 real-case path uses snapshot-bound builders for provenance integrity.