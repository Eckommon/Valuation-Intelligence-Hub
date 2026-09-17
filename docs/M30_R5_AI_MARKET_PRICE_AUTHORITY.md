# M30-R5 — Evidence-first AI market-price authority / 근거 우선 AI 시장가격 권위

## Purpose / 목적

M30-R5 extends the M30 evidence-first AI authority model to the existing M27 valuation-date market-price fact while preserving the M27 reviewed market-price package used by downstream code.

The real Ingredion trigger is the valuation date `2026-09-14`. External research cross-checks the INGR close at USD `98.63`, but web visibility alone is not authority.

## Governed path / 거버넌스 경로

```text
already-acquired UTF-8 market source
  → M30-E immutable external-source snapshot
  → M27 market-price FACT_CANDIDATE
  → exact candidate↔snapshot provenance validation
  → exact quote excerpt visible in source bytes
  → independent corroboration when Tier B
  → explicit contradiction search
  → AI_MARKET_PRICE_ADJUDICATOR_V01
  → legacy-compatible M27 review assertion
  → existing reviewed-market-price-fact-v0.1 finalizer/validator
```

No Draft mutation, registry mutation, promotion, admission, or canonical case write occurs in this slice.

## Evidence rules / 근거 규칙

- primary candidate must be M27-reviewable Tier A or B and `FRESH`;
- v0.1 admits only `OFFICIAL_CLOSE`;
- the exact evidence excerpt must be a substring of the immutable snapshot;
- the excerpt must visibly contain the trading date and candidate price;
- the primary snapshot must identify the candidate symbol, venue and currency and contain closing-price semantics;
- Tier B requires at least one independently captured corroborating source identity;
- each corroborating snapshot must visibly support the same candidate trading date and price and identify the instrument/venue;
- material contradiction fails closed;
- AI authority is typed and never presented as a human identity.

## Compatibility / 호환성

The final package remains the existing M27 `reviewed-market-price-fact-v0.1` with `class=FACT`. M30-R5 adds a `review_authority` projection locking:

- `type = AI`
- `id = AI_MARKET_PRICE_ADJUDICATOR_V01`
- policy id
- evidence SHA
- adjudication SHA

The existing M27 finalizer and validator are reused rather than bypassed.

## CLI

```text
market-price-ai-evidence-build
market-price-ai-evidence-validate
market-price-ai-adjudicate
market-price-ai-adjudication-validate
market-price-ai-finalize
market-price-ai-package-validate
```

All commands are calculate/validate only.

## Ingredion next execution / 다음 실행

After canonical merge, the real execution sequence is:

1. capture/materialize two independent UTF-8 source snapshots for INGR 2026-09-14;
2. validate both immutable snapshots;
3. build the primary M27 candidate at USD 98.63;
4. build and validate AI evidence with exact source excerpts;
5. AI adjudicate and finalize the reviewed market-price FACT;
6. pass that FACT into M30-R4 options TSM;
7. continue the remaining six-category dilution coverage to `equity.diluted_shares`.

Historical weighted-average diluted EPS shares remain forbidden as a valuation-date substitute.
