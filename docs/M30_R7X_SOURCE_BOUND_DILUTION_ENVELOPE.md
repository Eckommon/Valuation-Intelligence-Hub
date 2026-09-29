# M30-R7X — Source-bound R6 Upper-Envelope Ingress / R6 상단 Envelope 출처결합 실행계층

## Purpose / 목적

M30-R6 deliberately accepts a conservative upper-envelope as an analytical input, but its original CLI accepted that envelope as a raw JSON array. That is sufficient for deterministic tests but leaves the real M30 execution exposed to hand-authored provenance.

M30-R7X adds a thin ingress layer:

```text
validated Tier-A external-source snapshots
        ↓
explicit component claim specs
        ↓
excerpt + observed-quantity binding
        ↓
source-bound-dilution-envelope-manifest-v0.1
        ↓
existing M30-R6 component projection
        ↓
existing R6 materiality / adjudication / ASSUMPTION
```

R7X does **not** change the R6 diluted-share selection rule, envelope arithmetic, 5% materiality threshold, adjudicator, output class, Draft boundary, or R8 activation condition.

## Source contract / 출처 계약

Every source snapshot must independently pass the existing `external-source-snapshot-v0.1` validator and must be Tier A for the real M30 path.

Each component spec binds:

- `component_id`;
- existing R6 `role`;
- claimed `shares`;
- `as_of`;
- analytical `evidence_basis`;
- one or more `source_bindings`;
- buffer calculation inputs only when role = `DISCLOSURE_LAG_BUFFER`.

Each `source_binding` records:

- exact source snapshot SHA;
- exact evidence excerpt supplied by the caller;
- observed quantity as printed in that excerpt;
- unit multiplier used to convert the disclosed unit into shares.

The builder independently checks:

1. the selected snapshot itself validates;
2. source tier = A;
3. the evidence excerpt occurs in the selected source bytes after deterministic whitespace/visible-text normalization;
4. the observed quantity occurs as a bounded numeric token inside the excerpt;
5. direct anchor/subsequent claims equal their one source-bound quantity;
6. performance-max uplift equals the sum of its source-bound quantities;
7. disclosure-lag observed gross grants equal the sum of the bound gross-grant quantities;
8. disclosure-lag shares reproduce the existing R6 pro-rata formula;
9. projected R6 components satisfy the existing R6 component normalizer.

The manifest embeds the referenced immutable snapshots so later R6 commands can revalidate source bytes and excerpt lineage without guessing external paths.

## Real Ingredion evidence / 실기업 근거

The primary 2026 proxy source is the SEC DEF 14A filed April 8, 2026:

```text
https://www.sec.gov/Archives/edgar/data/1046257/000104625726000151/ingr-20260402.htm
```

The proxy equity-compensation table reports at 2025-12-31:

- total securities: 2,177,904;
- PSUs at 100% vesting assumption: 151,570;
- RSUs: 510,000;
- non-approved-plan phantom units: 35,694.

The 2026 Q2 10-Q source is:

```text
https://www.sec.gov/Archives/edgar/data/1046257/000162828026054722/ingr-20260630.htm
```

The already validated local Q2 snapshot SHA is:

```text
f61f33b0e27403ab56882d8cc1daa3a66571e9452fc5d8012268f39ab098b0f9
```

The Q2 filing reports:

- 215 thousand YTD employee RSU grants;
- 116 thousand YTD performance-share grants;
- 0–200% vesting range for the 2026 TSR-linked performance shares.

R7X does not infer those claims automatically. The user-local component-spec file must state the claim and copy the exact supporting excerpt from the selected snapshot.

## Component-spec example / 구성 spec 예시

The real execution should build a JSON array shaped like:

```json
[
  {
    "component_id": "2025YE_EQUITY_PLAN_SECURITIES",
    "role": "ANCHOR_OUTSTANDING_AWARDS",
    "shares": 2177904,
    "as_of": "2025-12-31",
    "evidence_basis": "Issuer proxy total equity-compensation-plan securities; conservative no-netting anchor.",
    "source_bindings": [
      {
        "snapshot_sha256": "<PROXY_SNAPSHOT_SHA>",
        "evidence_excerpt": "<EXACT EXCERPT CONTAINING 2,177,904>",
        "observed_quantity": 2177904,
        "unit_multiplier": 1
      }
    ],
    "calculation": null
  },
  {
    "component_id": "2026_YTD_RSU_GRANTS",
    "role": "SUBSEQUENT_GROSS_GRANT",
    "shares": 215000,
    "as_of": "2026-06-30",
    "evidence_basis": "Issuer Q2 YTD employee RSU grants.",
    "source_bindings": [
      {
        "snapshot_sha256": "f61f33b0e27403ab56882d8cc1daa3a66571e9452fc5d8012268f39ab098b0f9",
        "evidence_excerpt": "<EXACT EXCERPT CONTAINING 215 THOUSAND>",
        "observed_quantity": 215,
        "unit_multiplier": 1000
      }
    ],
    "calculation": null
  }
]
```

The full real manifest also includes:

- 116,000 YTD PSU grants;
- 267,570 performance-max uplift = 151,570 proxy target PSUs + 116,000 YTD PSU grants;
- disclosure-lag buffer whose `observed_gross_grants=331000` must reconcile to 215,000 + 116,000 and whose shares must reproduce `331000 × 76 / 181`.

## CLI / CLI

After the proxy bytes have been sealed through the existing external-source snapshot intake:

```powershell
$manifest = & vih --root . --json dilution-envelope-source-build `
  workspace/source_snapshots/INGR_r6_envelope_specs_20260914.json `
  workspace/source_snapshots/INGR_2026_proxy_snapshot.json `
  workspace/source_snapshots/INGR_2026Q2_10Q_snapshot.json

[IO.File]::WriteAllText(
  (Join-Path (Get-Location) "workspace/source_snapshots/INGR_r6_source_bound_envelope_20260914.json"),
  (($manifest -join "`n") + "`n"),
  [Text.UTF8Encoding]::new($false)
)

vih --root . --json dilution-envelope-source-validate `
  workspace/source_snapshots/INGR_r6_source_bound_envelope_20260914.json
```

The resulting manifest can be passed in the existing R6 `upper_envelope` positional argument:

```powershell
vih --root . --json dilution-assumption-evidence-build `
  <BASE_CONTEXT.json> `
  <R4_1_HOLD_INVENTORY.json> `
  <R7_PACKAGE.json> `
  workspace/source_snapshots/INGR_r6_source_bound_envelope_20260914.json `
  --as-of 2026-09-14 `
  --materiality-threshold 0.05 `
  --max-historical-age-days 180
```

Historical raw component arrays remain accepted for backward compatibility.

## Authority boundary / 권위 경계

R7X proves that:

> the component claim, disclosed quantity, exact cited excerpt, and immutable source bytes were bound together and deterministically projected into the R6 component shape.

It does **not** make the claim a FACT, does not make the upper envelope exact, and does not change R6's final `ASSUMPTION` class.

No Draft, registry, admission, or canonical case is mutated.
