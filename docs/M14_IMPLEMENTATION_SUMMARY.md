# M14 Implementation Summary / M14 구현 요약

M14 adds OpenDART as the second production live evidence adapter while preserving M13's immutable-snapshot authority boundary.

## Added / 추가

- `src/valuation_hub/dart_live.py`
- `src/valuation_hub/cli_entry.py`
- `src/valuation_hub/web_sources.py`
- `schemas/dart_source_snapshot.schema.json`
- `tests/fixtures/opendart_financials_sample.json`
- `tests/test_dart_live.py`
- `tests/test_dart_interfaces.py`
- `docs/LIVE_EVIDENCE_OPENDART.md`
- `docs/M14_ACCEPTANCE.md`

## Preserved / 보존

- M13 SEC source-snapshot behavior
- M1–M12 valuation/promotion/admission behavior
- existing `valuation_hub.cli` parser and command contracts
- no browser live fetch
- no automatic canonical write

## Authority boundary / 권위 경계

```text
OpenDART official API
→ immutable DART snapshot / NOT CANONICAL
→ exact-row evidence candidate / UNREVIEWED / NOT CANONICAL
→ existing evidence governance + human review
→ M9–M12 promotion/admission
→ canonical only after reviewed merge
```

The API key is intentionally absent from every durable artifact.

API key는 모든 durable artifact에서 의도적으로 배제된다.
