# M30-R8 — truthful R6 diluted-share ASSUMPTION handoff

## Activation evidence

Real user-local Ingredion R7→R7X→R6 run on canonical
`80298f47dd9a62fecfb5362e670a70be412be40b` reported:

- R6 package SHA `ae1e6612b67a56e568b9a9bcd6588c8765240a196ab395aa2dc86887b027e3af`;
- `APPROVE_DISCLOSURE_LIMITED_DILUTION_ASSUMPTION`;
- 63,900,000 selected shares;
- 3.2542% upper-envelope spread versus a 5% threshold.

The real R6 bytes remain **user-local under gitignored workspace**. They are
not synthesized from the reported hashes and are not included in this PR.

## Authority routes

```text
LEGACY EXACT
M22 reviewed complete share bridge → M23 v0.3 DERIVED_FACT
→ M24..M28 v0.8 → M29 promotion-candidate-v0.2 DERIVED

DISCLOSURE-LIMITED
R7 historical-only + R4 HOLD + R7X Tier-A source-bound manifest + R6 PASS
→ R8 source-embedded proof
→ M23 v0.3 route R6_DISCLOSURE_LIMITED_ASSUMPTION
→ existing M24..M28 v0.8 validators
→ R8 v0.9 bound proposal + explicit human approval + noncanonical apply
→ M29 promotion-candidate-v0.2 ASSUMPTION
```

M23's R6 route **requires a fully revalidated source-bound R6 proof**, so
a legacy M22 DERIVED share bridge cannot be silently overwritten at M28.
The complete proposal chain validates through embedded provenance to R6.

R8 modifies only dilution-share authority. It does not recalculate R6,
relax materiality, alter WACC, terminal growth, or forecast assumptions,
or automatically promote/admit the case.

## Commands

Installed CLI: `vih`, through `valuation_hub.cli_entry_m30r8:main`.
All historical CLI commands delegate unchanged to M30-R7 and predecessors.

```powershell
# 1. Revalidate source bytes and produce an embedded R6 proof
vih r8-proof-build package.json base_context.json inventory.json historical.json r7x_manifest.json > proof.json
vih r8-proof-validate proof.json

# 2. M23 R6 route from validated v0.2 debt proposal
vih r8-m23-build debt_v02.json proof.json > r6_v03.json
vih r8-m23-validate r6_v03.json

# 3. Use existing governed M24-M28 construction on r6_v03.json.
#    The resulting v0.8 proposal must preserve the SAME R6 proof.
vih r8-proposal-build complete_v08.json proof.json > r8_v09.json
vih r8-proposal-validate r8_v09.json

# 4. Explicit reviewer approval is still necessary
#    (repeat --field for each approved material field).
vih r8-approval-build r8_v09.json draft.json --reviewer "Reviewer" --entity-id ENTITY --financial-scope CFS --field equity.diluted_shares --approved-at 2026-10-14T10:00:00+09:00 > approval.json
vih r8-approval-validate approval.json r8_v09.json draft.json
vih r8-apply r8_v09.json draft.json approval.json > bound_result.json
vih r8-bound-validate bound_result.json
```

The example partial approval **does not meet** M29's 13-field complete
handoff gate. Full promotion requires all 13 separately eligible fields,
a separate explicit reviewer, source-grounded evidence catalog,
promotion review, and guarded admission.

For R8, M29 evidence catalog contains **four observed inputs**, excluding
the share assumption; the share path has class `ASSUMPTION` and zero
observed claim links. Exact M22 remains five observed inputs and
`DERIVED` for the share path.

## Fail-closed boundaries

- package and embedded R6 evidence/adjudication revalidate against R4,
  base shares, R7 historical anchor and source-bound R7X raw snapshots;
- R4 UNKNOWN_CONFLICT, materiality HOLD, stale entity/period or mismatched
  SHA blocks the proof;
- exact M22 route always outranks fallback;
- no conversion of an R6B analytical range or M21/R7 historical duration
  reference into valuation-date point FACT;
- no tampered nested proposal, approval, diff, catalog claim or review
  scope can pass independent reconstruction;
- `ASSUMPTION` never becomes `DERIVED` or `FACT` for compatibility;
- R8 apply returns only `canonical: false`; no registry or case write.

## Verification and release

- exact-head Python 3.11/3.12 CI;
- synthetic PASS path through R6→M23→M28→M29 and exact-M22 regression;
- materiality, authority, lineage, and result-tampering negatives;
- expected-head merge only after both jobs pass.
