# M30-R3 — SEC observed-field AI authority / SEC 관측필드 AI 권위

## Purpose / 목적

M30-R3 extends the evidence-first, human-on-exception governance proven in M30-R2 from aggregate debt to three remaining SEC-derived observed fields:

- `equity.cash`
- valuation-date `current_common_shares` base
- `equity.minority_interest`

Internal analytical review may be completed by a typed AI adjudicator only when exact source lineage, field-specific semantics, contradiction search, and fail-closed validation all succeed. External-condition approvals remain human-controlled.

## Authority boundary / 권위 경계

```text
Tier-A SEC source
  → FACT_CANDIDATE
  → NORMALIZED_FACT_CANDIDATE
  → structured AI evidence packet
  → contradiction search
  → typed AI adjudication
  → reviewed NORMALIZED_FACT / reviewed NCI package
  → existing downstream binding machinery
```

The AI adjudicator is always identified as:

```text
AI_EVIDENCE_ADJUDICATOR_V01
review_authority = AI
```

No human identity or approval is inferred or fabricated.

## Field-specific invariants / 필드별 불변조건

### Cash

- exact `us-gaap:CashAndCashEquivalentsAtCarryingValue`
- no concept fallback
- unique equal-precedence fact
- Tier-A SEC source
- exact INSTANT USD observation
- candidate → observation must reproduce deterministically

### Current common shares

- exact `dei:EntityCommonStockSharesOutstanding`
- positive exact-INSTANT share count
- unique Tier-A source
- candidate → observation must reproduce deterministically
- immutable semantic boundary:

```text
current_common_shares_only = true
fully_diluted_shares = false
```

AI review makes the observation eligible only as the M22 valuation-date common-share base. It does **not** resolve `equity.diluted_shares`; explicit dilution evidence and complete coverage remain required.

### Minority interest

- exact `us-gaap:NonredeemableNoncontrollingInterest`
- consolidated CFS scope
- exact-INSTANT point-in-time fact
- unique Tier-A source
- candidate → observation must reproduce deterministically
- explicit reported zero is admissible
- missing evidence is never converted to zero
- redeemable NCI is not silently included
- no equity-difference derivation shortcut

## Contradiction rule / 반증 규칙

Every AI evidence packet must record that contradiction search was performed and include a non-empty summary. Any material contradiction causes fail-closed HOLD/escalation; it cannot be overridden by merely setting semantic criteria to true.

## Compatibility / 호환성

M30-R3 is additive:

- historical human-review routes remain available;
- prior CLI commands delegate unchanged through `M30-R3 → M30-R2 → M30-R1 → ...`;
- no Draft file is mutated;
- no registry/canonical case is written;
- reviewed successors remain noncanonical until the existing governed binding/promotion/admission lifecycle is complete.

## Real Ingredion trigger / 실기업 실행 계기

The real execution that triggered M30-R3 established:

- cash: USD `948,000,000`, observation `5603c65cb092f5d2ac49b67cc524da8e0d620561835baf8d4cc93afbf854363b`
- current common shares: `63,063,979`, observation `7c54c10037edce452e4db03991e44440d24cd50e7a37a39e2efc90c9e1bee8f0`
- minority interest: explicit USD `0`, observation `703f9f53859d8cef04fd207b604468735272c49d7955b7047ebe2304694cfa27`

The pre-M30-R3 current-share base build correctly failed because candidate authority had not yet been reviewed; M30-R3 addresses that authority-operability boundary rather than weakening the source or semantic contract.
