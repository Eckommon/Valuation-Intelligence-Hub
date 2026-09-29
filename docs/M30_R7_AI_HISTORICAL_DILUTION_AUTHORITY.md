# M30-R7 — Evidence-first AI authority for M21 historical dilution

## Purpose

M21 extracts SEC weighted-average basic and diluted EPS denominators as historical duration evidence. The legacy M21 extractor intentionally leaves both observations at candidate authority, which means a real issuer pair cannot become the reviewed DERIVED_FACT historical anchor required by M30-R6 without an explicit authority successor.

M30-R7 adds that successor without weakening the M21 semantic boundary.

## Authority flow

    exact SEC CompanyFacts snapshot
      ↓
    weighted-average basic candidate
    weighted-average diluted candidate
      ↓
    exact normalized candidate observations
      ↓
    R7 evidence packet
      - exact concepts
      - exact candidate→observation reproduction
      - same entity / duration period / filing / source snapshot
      - basic > 0
      - diluted >= basic
      - explicit contradiction search
      - historical-only boundary
      ↓
    AI adjudication
      - AI_HISTORICAL_DILUTION_ADJUDICATOR_V01
      ↓
    reviewed basic NORMALIZED_FACT
    reviewed diluted NORMALIZED_FACT
      ↓
    existing M21 derive_historical_dilution()
      ↓
    historical-dilution-evidence-v0.1 / DERIVED_FACT
      ↓
    self-contained R7 authority package
      ↓
    eligible as M30-R6 historical anchor

## Fail-closed rules

R7 rejects:

- a candidate or observation already manually promoted to FACT;
- candidate→observation reproduction mismatch;
- entity mismatch;
- duration-period mismatch;
- filing identity mismatch;
- source snapshot/body mismatch;
- non-Tier-A SEC evidence;
- multiple equal-precedence SEC facts;
- basic shares <= 0;
- diluted shares below basic shares;
- any required criterion not explicitly true;
- material contradiction;
- adjudication timestamp before the filing date;
- any tampering with reviewed observations, derived arithmetic, or package lineage.

## Semantic boundary

R7 does **not** convert historical weighted-average diluted EPS shares into valuation-date fully diluted shares.

The nested M21 artifact continues to enforce:

- historical_only = true
- valuation_date_direct_bind = false
- forecast_direct_bind = false
- shares_outstanding_substitution = false

The R7 package additionally records:

- fully_diluted_shares_substitution = false
- r6_anchor_eligible = true

This means the historical diluted denominator may serve as a conservative R6 selection anchor, but not as M22 exact diluted-share authority.

## M30-R6 integration

M30-R6 now accepts either:

1. the legacy reviewed M21 DERIVED_FACT input; or
2. a fully validated ai-reviewed-historical-dilution-package-v0.1.

For R7 packages, R6 validates the entire embedded authority chain before reading the nested historical diluted-share value. R6 lineage locks the R7 package SHA rather than trusting a manually edited DERIVED_FACT label.

## Real Ingredion target

2026 Q2 historical issuer denominators:

- basic weighted-average shares: 63.3 million
- diluted weighted-average shares: 63.9 million
- historical incremental diluted shares: 0.6 million

These are historical quarter averages, not September 14, 2026 point-in-time diluted shares.

Once the user-local gitignored candidate and observation artifacts are passed through R7, the resulting package can satisfy the historical-input authority gate in M30-R6. The remaining R6 dilution value stays typed ASSUMPTION under the disclosure-limited materiality policy.

## CLI

The additive vih surface provides:

- historical-dilution-ai-evidence-build
- historical-dilution-ai-evidence-validate
- historical-dilution-ai-adjudicate
- historical-dilution-ai-adjudication-validate
- historical-dilution-ai-finalize
- historical-dilution-ai-package-validate

No command mutates Drafts, registry, admission state, or a canonical case.
