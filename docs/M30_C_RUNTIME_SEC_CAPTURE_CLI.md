# M30-C Runtime-safe SEC Capture CLI / 안전한 SEC 실데이터 수집 CLI

## Purpose / 목적

M30-C exposes the already-governed M13 SEC acquisition path and M30-B v0.2 preflight through the installed `vih` command without storing the identifying SEC User-Agent.

## Runtime secret boundary / 실행 입력 경계

The identifying value is read only from the environment variable:

```text
SEC_USER_AGENT
```

It must contain a contact email accepted by SEC fair-access policy. The value is:

- never accepted as a `vih` CLI argument;
- never committed to Git;
- never written into the M13 snapshot;
- represented in snapshot metadata only as `user_agent_provided=true`.

Do not substitute a fabricated address.

### PowerShell example / PowerShell 예시

Use your own contact address at runtime:

```powershell
$env:SEC_USER_AGENT = "Valuation-Intelligence-Hub your-contact@example.com"
```

The example address above is a placeholder, not a value to use unchanged.

## 1. Capture immutable CompanyFacts bytes / CompanyFacts 원문 수집

From the repository root:

```powershell
vih --json sec-companyfacts-fetch 0001046257 `
  --output workspace/source_snapshots/US_INGR_INGREDION_companyfacts_20260914.json
```

The command:

1. rejects output outside `workspace/source_snapshots` before credential lookup or network I/O;
2. reads `SEC_USER_AGENT` from the process environment;
3. calls the bounded M13 `capture_companyfacts_snapshot` path;
4. validates the resulting source snapshot;
5. writes with create-exclusive/no-overwrite semantics and mode `0600` where supported;
6. prints only materialization and hash metadata.

No canonical case state is changed.

## 2. Revalidate materialized source / 저장 snapshot 재검증

```powershell
vih --json sec-source-snapshot-validate `
  workspace/source_snapshots/US_INGR_INGREDION_companyfacts_20260914.json
```

Expected status:

```text
PASS_SOURCE_SNAPSHOT_VALIDATION
```

The body hash, snapshot hash, CIK, HTTPS source identity, timestamp and byte count are independently recomputed.

## 3. Run M30-B v0.2 / M30-B v0.2 실행

```powershell
vih --json real-equity-preflight-v2 `
  workspace/source_snapshots/US_INGR_INGREDION_companyfacts_20260914.json `
  --case-id US_INGR_INGREDION `
  --legal-name "Ingredion Incorporated" `
  --ticker INGR `
  --exchange NYSE `
  --cik 0001046257 `
  --financial-period-end 2026-06-30 `
  --valuation-as-of 2026-09-14 `
  --form 10-Q
```

If the exact cash, current-share, NCI, and SEC aggregate-debt candidates are present and no registry/identity blocker exists, the expected next action is:

```text
CONTINUE_TO_HUMAN_DEBT_SEMANTIC_REVIEW
```

That is **not** approval. The debt semantic review remains an explicit human SHA-locked M30-P1 action.

## Failure rules / 실패규칙

- missing `SEC_USER_AGENT` → fail before network I/O;
- malformed identifying User-Agent → fail before network I/O;
- output outside source-snapshot workspace → fail before credential lookup/network I/O;
- existing output path → no overwrite;
- non-200 / non-JSON / oversized / invalid UTF-8 SEC response → fail;
- CIK mismatch → fail;
- snapshot/body SHA mismatch → fail;
- exact aggregate-debt source missing or conflicting → M30-B HOLD;
- missing NCI is never interpreted as zero;
- no CLI command in M30-C creates human approval or canonical registry state.

## Compatibility / 호환성

`vih` now enters through `valuation_hub.cli_entry_m30:main`. Any command not owned by M30-C delegates unchanged to the M29 entrypoint and the historical CLI chain.