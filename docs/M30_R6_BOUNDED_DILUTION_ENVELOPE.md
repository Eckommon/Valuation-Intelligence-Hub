# M30-R6B — Category-level bounded dilution envelope / 희석 category 범위

## Purpose / 목적

M30-R6B is a noncanonical analytical-range layer that complements, but does not replace, the existing M30-R6 disclosure-limited diluted-share ASSUMPTION path.

The two paths answer different questions:

- disclosure-limited R6: can a separately typed point ASSUMPTION be selected under a conservative aggregate envelope?
- R6B: what lower/upper dilution interval is supported for each M22 category, and how much denominator uncertainty does that create?

R6B never produces equity.diluted_shares, FACT, or DERIVED_FACT.

## Upstream requirements / 선행조건

R6B requires:

- a fresh reviewed current-common-share base;
- an M30-R4/R4.1 HOLD inventory;
- at least one BLOCKED_DEPENDENCY;
- no UNKNOWN_CONFLICT;
- exactly the six M22 dilution categories.

The exact R4 path always outranks R6B.

## Category states / category 상태

Each category is projected as one of:

- EXACT
- BOUNDED
- UNBOUNDED_DEPENDENCY

R4 PRESENT must become EXACT and reproduce its exact adjustment.

R4 ABSENT_SUPPORTED must become EXACT zero.

R4 BLOCKED_DEPENDENCY may become BOUNDED or remain UNBOUNDED_DEPENDENCY, but may not become EXACT inside R6B. If stronger evidence resolves the category exactly, R4 must be rebuilt instead.

## Bound authority / 범위 권위

Bound kinds are:

- EXACT_REPRODUCED
- EVIDENCE_IMPLIED
- ASSUMPTION_CONDITIONAL
- UNBOUNDED_DISCLOSURE

ASSUMPTION_CONDITIONAL requires explicit assumptions. EVIDENCE_IMPLIED forbids assumptions.

This distinction prevents a research scenario from being mislabeled as a hard evidence-implied bound.

## Envelope projection / 범위 투영

For finite category ranges:

    lower fully diluted shares
      = current common shares
      + sum(category lower shares)

    upper fully diluted shares
      = current common shares
      + sum(category upper shares)

    relative share uncertainty
      = upper / lower - 1

    maximum per-share denominator effect
      = 1 - lower / upper

The last metric is denominator sensitivity only. It does not assume an enterprise value or equity value.

Default materiality threshold is 5%.

- <= 5%: RANGE_READY_FOR_VALUATION_SCENARIOS
- > 5%: HOLD_MATERIAL_DILUTION_UNCERTAINTY
- any unbounded category: HOLD_UNBOUNDED_DILUTION_DEPENDENCY

## Ingredion research-shaped interval / Ingredion 조사형 범위

Current exact R4.1 inputs:

- base common shares: 63,063,979
- employee RSU: EXACT +534,000
- warrants: EXACT 0
- convertibles: EXACT 0

Research-shaped conditional bounds for the three public-disclosure blockers:

### Options

Issuer Q2 reports 1.242 million options outstanding at June 30, 2026, weighted-average strike $105.61 and aggregate intrinsic value $3 million, but not the strike distribution.

Using the June 30 close of $94.71, valuation-date close of $98.63, no post-June-30 option grants, and a conservative $3.5 million upper interpretation of the rounded $3 million intrinsic-value disclosure:

    upper intrinsic value at valuation date
      <= 3.5m + 1.242m * (98.63 - 94.71)

    TSM incremental shares
      <= upper intrinsic value / 98.63
      ~= 84,849

Rounded conditional interval:

    0 .. 84,850 shares

### Performance shares

Proxy target PSU count at December 31, 2025: 151,570.

2026 Q2 reports 116,000 YTD awards and 15,000 forfeitures. Using a 200% maximum payout and intentionally not subtracting the 2023 cohort from the conservative upper:

    (151,570 + 116,000 - 15,000) * 200%
      = 505,140

Conditional interval:

    0 .. 505,140 shares

### Director / deferred equity

The 2026 proxy provides a stronger aggregate anchor than the earlier 35,694 phantom-unit table: as of March 23, 2026, all directors and executive officers as a group had 332,440 shares underlying deferred phantom stock units and deferred RSUs.

The 2026 director-compensation program also establishes a May 20 outside-director RSU grant. A representative Form 4 reports 1,797 RSUs for an outside director.

For research sensitivity only, a conservative conditional scenario uses:

    March 23 aggregate                       332,440
    10 May outside-director grants
      at 1,797 each                           17,970
    one additional May-grant-sized
      placeholder for the new July director   1,797
    additional phantom/deferred buffer
      equal to full 2025 year-end
      stock-settleable phantom balance       35,694
    ------------------------------------------------
    conditional upper                       387,901

The 387,901 figure is not an exact issuer-reported September 14 total and is not an evidence-implied hard cap. It is ASSUMPTION_CONDITIONAL and must retain those assumptions in the artifact.

Conditional interval:

    0 .. 387,901 shares

## Resulting research sensitivity / 조사형 민감도

Using those category ranges:

    lower diluted shares = 63,597,979
    upper diluted shares = 64,575,870
    width                =    977,891

    relative share uncertainty
      ~= 1.538%

    maximum per-share denominator reduction
      ~= 1.514%

This is below the default 5% materiality threshold, so the interval is suitable for valuation-scenario sensitivity analysis.

It is not eligible to direct-bind as equity.diluted_shares.

## Semantic boundary / 의미경계

R6B enforces:

- interval != exact fact
- interval != derived fact
- conditional bound != evidence-implied bound
- current shares != fully diluted shares
- blocked R4 category cannot become exact inside R6B
- UNKNOWN_CONFLICT cannot use bounded fallback
- range-ready != Draft-binding authority
- no Draft, registry, admission, or canonical-case mutation
