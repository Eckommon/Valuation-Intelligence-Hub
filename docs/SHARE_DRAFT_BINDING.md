# Share-Aware Draft Binding / 희석주식 Draft 바인딩

## Purpose / 목적

M23 connects only a **complete, reviewed, fresh M22 diluted-share bridge** to the existing equity-FCFF Draft-binding path as `equity.diluted_shares`.

M23 does not recalculate M16 or M20 decisions from scratch. It wraps an already validated proposal and replaces exactly one field classification.

```text
validated M16 v0.1 proposal
or validated M20 v0.2 debt-aware proposal
        +
complete reviewed fresh M22 share bridge
        ↓
draft-binding-proposal-v0.3
```

## Semantic boundary / 의미경계

```text
current_common_shares != fully_diluted_shares
historical_dilution_factor != current dilution adjustment
candidate bridge total != binding authority
complete reviewed fresh bridge + human coverage assertion = binding-eligible evidence
```

M23 itself still creates a **noncanonical proposal**. Draft mutation requires the existing M17 human approval lock.

## v0.3 enrichment rule / v0.3 보강 규칙

M23 may replace only:

```text
equity.diluted_shares
```

All other `draft_input_matrix` entries must remain exactly equivalent to the embedded base proposal. This preserves:

- M16 cash semantics,
- M20 debt semantics,
- base proposal identity,
- conflicts,
- source-observation lineage.

The base proposal may be either:

```text
draft-binding-proposal-v0.1
draft-binding-proposal-v0.2
```

## Direct-bind gate / 직접바인딩 게이트

The supplied M22 bridge must validate as all of the following:

```text
schema = diluted-share-bridge-v0.1
class = DERIVED_FACT
coverage = COMPLETE_REVIEWED_DILUTION_COVERAGE
binding_eligibility.eligible_for_future_direct_bind = true
candidate_fully_diluted_shares > 0
```

In addition:

- bridge entity ID must match the base proposal entity,
- bridge financial scope must match,
- bridge `as_of` must exactly equal proposal `as_of`,
- nested M22 base context, adjustments, coverage assertion, and integrity hashes must remain valid.

BASE_ONLY, PARTIAL, CONFLICT, candidate-authority, stale/ineligible, identity mismatch, scope mismatch, and `as_of` mismatch fail closed before a v0.3 proposal can be created.

## Projected context / 투영 context

An eligible bridge is projected into:

```text
baseline_context.fully_diluted_shares
```

with explicit lineage:

```text
source_bridge_sha256
base_context_sha256
coverage_assertion_sha256
```

The `equity.diluted_shares` DIRECT_BIND decision carries the same lineage.

## Human approval and apply / 인간승인 및 적용

M23 reuses `binding-approval-v0.1`.

A human may approve `equity.diluted_shares` only when the v0.3 proposal marks that field `DIRECT_BIND`. The approval remains locked to:

- proposal SHA,
- Draft-before SHA,
- target entity/scope,
- explicit approved field list,
- reviewer,
- timezone-aware approval timestamp.

The apply stage remains in-memory and noncanonical. It does not overwrite the Draft file.

The resulting diff for `equity.diluted_shares` preserves:

```text
source_bridge_sha256
base_context_sha256
coverage_assertion_sha256
```

Cash and debt diff contracts remain unchanged.

## CLI / CLI

```text
binding-build-with-diluted-shares <base_proposal.json> <share_bridge.json>
binding-validate <proposal.json>
```

`binding-validate` accepts v0.1, v0.2, and v0.3 through the governed proposal validator chain.

Existing M17 approval/apply commands can then operate on a v0.3 proposal.

## Web / Web

```text
/share-binding
/api/share-binding/build
/api/share-binding/validate
```

The Web surface is proposal calculate/validate only. There is deliberately no M23 Web endpoint for Draft apply, file write, promotion, admission, or canonical mutation.

## Authority / 권위

```text
M22 bridge evidence
  ↓
M23 v0.3 proposal / NOT CANONICAL
  ↓
M17 human approval / NOT CANONICAL
  ↓
M17 bound Draft result / NOT CANONICAL
  ↓
existing Draft governance / promotion / admission / guarded apply
  ↓
CANONICAL only after repository governance
```

M23 therefore resolves the governed **binding path** for `equity.diluted_shares` without bypassing the existing authority model.
