# M30-E Acceptance / 완료조건

## Mission / 미션

M30-E closes the non-SEC provenance-ingress gap that remained after M30-D. It binds already-acquired UTF-8 market/macro source bytes to immutable noncanonical snapshots and requires M27/M24/M25 source-backed artifacts to derive provenance from those snapshots rather than from independently hand-assembled metadata.

M30-E는 이미 확보된 비SEC 시장·거시 원문 bytes를 불변 비정식 snapshot에 결합하고, M27/M24/M25 산출물이 publisher/type/tier/locator/SHA를 snapshot에서만 파생하도록 하여 provenance 수동조립 공백을 닫는다.

## Acceptance checklist / 완료 체크리스트

- [x] `external-source-snapshot-v0.1` builder exists.
- [x] independent snapshot validator recomputes exact UTF-8 body size/hash and outer snapshot hash.
- [x] source locator must be absolute HTTPS.
- [x] embedded username/password are rejected.
- [x] unsafe/non-default authority ports are rejected.
- [x] durable envelope contains no request headers, cookies, API keys, authorization fields, or persisted credentials.
- [x] capture method is fixed to local UTF-8 intake and records `network_fetch_performed=false`.
- [x] materialization is confined to `workspace/source_snapshots`.
- [x] materialization is exclusive/no-overwrite and fsyncs the written file.
- [x] M27 market-price candidate can be built from a validated snapshot with provenance injected only from that snapshot.
- [x] M24 WACC source input can be built from a validated snapshot with provenance injected only from that snapshot.
- [x] M25 terminal-growth anchor can be built from a validated snapshot with provenance injected only from that snapshot.
- [x] provenance override arguments are rejected by source-bound builders.
- [x] downstream source-tier/freshness/reviewability policy remains authoritative; snapshot presence does not promote authority.
- [x] independent `artifact ↔ snapshot` validators reject downstream publisher/type/tier/locator/SHA divergence even if the downstream artifact is re-sealed.
- [x] snapshot semantics are documented correctly: the snapshot proves internal byte/provenance integrity of the selected envelope, not external truth of publisher identity or claim semantics.
- [x] additive M30 CLI exposes snapshot build/validate and snapshot-bound M27/M24/M25 builders.
- [x] historical/manual M27/M24/M25 commands remain backward compatible.
- [x] no arbitrary network fetcher, no reviewer fabrication, no human approval, no Draft mutation, no registry write, and no canonical case write are introduced.
- [x] JSON schema exists.
- [x] bilingual methodology documentation exists.
- [x] core and CLI regression tests exist.
- [ ] exact final-head Python 3.11/3.12 CI succeeds.
- [ ] PR records exact tested SHA and CI run.
- [ ] merge uses exact `expected_head_sha`.
- [ ] Issue #75 is completed.
- [ ] post-merge main Python 3.11/3.12 CI succeeds.

## Non-goals / 비목표

M30-E does not fetch arbitrary URLs, authenticate to external providers, parse arbitrary text into economic claims, decide source truthfulness, create reviewer identity/timestamps, perform human approval, bind the Ingredion Draft, or add the Ingredion case to `registry/cases.json`.

## Parent mission boundary / 부모 미션 경계

Parent Issue #66 remains open after M30-E. Only after this ingress is canonical should M30 proceed to real Ingredion source execution and explicit human-review gates.