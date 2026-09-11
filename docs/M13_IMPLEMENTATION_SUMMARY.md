# M13 Implementation Summary / M13 구현 요약

M13 adds the first production live-source adapter while preserving the repository's existing evidence authority model.

## Added / 추가

- `src/valuation_hub/sec_live.py`
- `schemas/source_snapshot.schema.json`
- `tests/fixtures/sec_companyfacts_sample.json`
- `tests/test_sec_live.py`
- `tests/test_sec_interfaces.py`
- `workspace/source_snapshots/.gitkeep`
- SEC CLI commands
- read-only Web source inspector
- bilingual live-evidence documentation

## Authority boundary / 권위 경계

```text
official live source
→ immutable source snapshot / NOT CANONICAL
→ evidence candidate / UNREVIEWED / NOT CANONICAL
→ existing review/promotion/admission pipeline
→ canonical only after reviewed repository merge
```

No live source can bypass M9–M12 merely because it is authoritative.

공식 live source도 권위자료라는 이유만으로 M9–M12를 우회할 수 없다.
