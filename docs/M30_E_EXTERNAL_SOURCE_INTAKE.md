# M30-E Immutable Non-SEC Source Intake / 비SEC 불변 원문 Intake

## Purpose / 목적

M27 market price, M24 WACC, and M25 terminal-growth anchors already require source publisher/type/tier/locator/SHA lineage. Before M30-E those fields could be assembled manually even when the underlying source bytes were not durably bound to them.

M30-E closes that ingress gap without adding an arbitrary network client:

```text
already-acquired UTF-8 source bytes
        ↓
external-source-snapshot-v0.1
        ↓
immutable body SHA + snapshot SHA
        ↓
snapshot-bound M27 / M24 / M25 builder
        ↓
existing downstream validator + human review boundary
```

M30-E does not fetch arbitrary URLs, handle cookies/authentication, parse arbitrary prose into facts, or promote evidence authority.

## Snapshot contract / Snapshot 계약

`external-source-snapshot-v0.1` records:

- publisher;
- source type;
- proposed tier `A/B/C/D`;
- absolute HTTPS source locator;
- timezone-aware capture timestamp;
- exact UTF-8 source text;
- UTF-8 byte length;
- body SHA-256;
- deterministic outer snapshot SHA-256.

The capture envelope explicitly records:

- `method = LOCAL_UTF8_INTAKE`;
- `network_fetch_performed = false`;
- `credentials_persisted = false`.

Request headers, cookies, API keys, authorization values, and other credentials are outside this durable contract.

## Locator safety / Locator 안전경계

The source locator must be an absolute HTTPS URL. The validator rejects:

- HTTP;
- missing hostname;
- embedded username/password;
- malformed ports;
- non-default ports other than 443.

The locator is provenance metadata. M30-E does not dereference it.

## Materialization / Materialization

Snapshot files can be materialized only under:

```text
workspace/source_snapshots/
```

The write path is:

- validate before write;
- no overwrite;
- exclusive file creation;
- restrictive file mode where supported;
- flush + fsync;
- cleanup on failed write.

This produces durable noncanonical evidence bytes, not canonical valuation state.

## Snapshot-bound downstream builders / Snapshot 결합 downstream builder

### M27 market price

The caller still supplies the economic claim:

- price;
- currency;
- entity/instrument identity;
- quote type;
- trading date;
- observation timestamp;
- valuation `as_of`.

But publisher/type/tier/locator/`source_snapshot_sha256` come only from the validated snapshot.

### M24 WACC source input

The caller still supplies:

- governed WACC metric;
- numeric value;
- unit;
- observed date;
- claim class.

Publisher/type/tier/locator/`source_sha256` are derived only from the snapshot.

### M25 terminal-growth anchor

The caller still supplies:

- governed anchor metric;
- numeric value;
- observed date;
- claim class.

Publisher/type/tier/locator/`source_sha256` are derived only from the snapshot.

## Authority boundary / 권위 경계

A valid external snapshot means only:

> these exact bytes and this declared provenance were sealed together at this snapshot SHA.

It does **not** prove the publisher declaration is externally true, does not prove that a numeric claim was correctly interpreted from the text, and does not make the claim a FACT.

Therefore:

- M27 still determines freshness and market-price human-review eligibility;
- M24/M25 still enforce their own metric/range/tier/review rules;
- source tier `D` remains non-reviewable wherever the downstream contract says so;
- human approval remains explicit;
- no Draft or registry state is written.

## Re-seal semantics / 재서명 의미

If someone edits a snapshot's declared publisher and recomputes the entire snapshot hash, that object is a **different snapshot**, not a cryptographically detectable edit of the original object. M30-E therefore does not make an unsupported external-attestation claim.

What M30-E does guarantee is stronger at the downstream boundary: once an M27/M24/M25 artifact is built from a selected snapshot, independent `*_against_snapshot` validators require its entire provenance projection to exactly match that snapshot. Changing publisher, source type, tier, locator, or source SHA and then recomputing the downstream artifact hash still fails the snapshot-bound validation.

## CLI / CLI

Additive M30 commands:

```text
external-source-snapshot-build
external-source-snapshot-validate
market-price-candidate-build-from-snapshot
wacc-source-build-from-snapshot
terminal-growth-anchor-build-from-snapshot
```

Historical manual M27/M24/M25 commands remain available for backward compatibility. M30 real-case execution should prefer the snapshot-bound path.

## Non-goals / 비목표

M30-E does not:

- perform generic HTTP fetching;
- store credentials;
- infer claim values from arbitrary text;
- generate reviewer identity or timestamps;
- perform human review;
- mutate Drafts;
- write `registry/cases.json`;
- create a canonical Ingredion case.
