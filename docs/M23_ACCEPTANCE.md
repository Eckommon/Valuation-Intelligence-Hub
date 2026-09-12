# M23 Acceptance / M23 완료계약

## Mission

Integrate only complete, reviewed, fresh M22 diluted-share bridges into the existing governed equity-FCFF binding path as `equity.diluted_shares`, while preserving M16 cash semantics, M20 debt semantics, M17 human approval, Draft immutability, and repository-controlled canonicalization.

## Acceptance checklist

- [x] `draft-binding-proposal-v0.3` wraps an already validated v0.1 or v0.2 proposal.
- [x] M23 replaces only `equity.diluted_shares`; every other base decision is preserved.
- [x] Only `COMPLETE_REVIEWED_DILUTION_COVERAGE` bridges may enter v0.3.
- [x] Bridge class must be `DERIVED_FACT` and future-direct-bind eligibility must be true.
- [x] Candidate fully diluted shares must be finite and positive.
- [x] Entity, financial scope, and `as_of` must exactly match the base proposal.
- [x] Full M22 bridge is embedded and independently revalidated, including nested coverage lineage.
- [x] BASE_ONLY/PARTIAL/CONFLICT/candidate/stale/ineligible bridges fail closed before proposal creation.
- [x] v0.3 baseline projection preserves bridge SHA, base-context SHA, and coverage-assertion SHA.
- [x] M17 `binding-approval-v0.1` can explicitly approve `equity.diluted_shares` only when DIRECT_BIND.
- [x] M17 apply supports `equity.diluted_shares` without mutating the input Draft.
- [x] Applied share diff preserves bridge/base-context/coverage-assertion lineage.
- [x] Existing cash and debt apply diff contracts remain unchanged.
- [x] One approval can apply eligible cash, debt, and diluted-shares decisions together.
- [x] CLI exposes `binding-build-with-diluted-shares` and v0.1/v0.2/v0.3 `binding-validate`.
- [x] Web `/share-binding` is proposal calculate/validate only.
- [x] No M23 Draft-file write, promotion, admission, or canonical-write route exists.
- [x] v0.3 JSON Schema exists.
- [x] M1-M22 regressions remain required.
- [x] Core checkpoint Python 3.11/3.12 CI success recorded: `34692432321` on `1dc2fee8cb400ef642f7dd64460bb60956a88a29`.
- [x] Interface/schema checkpoint Python 3.11/3.12 CI success recorded: `34692614288` on `005a1dd58dae6a2a3162c6a2b06629860540fffd`.
- [ ] Final-head Python 3.11 CI success recorded.
- [ ] Final-head Python 3.12 CI success recorded.
- [ ] PR merged from exact tested head SHA.
- [ ] Issue #50 closed as completed.
- [ ] Post-merge `main` CI success recorded.

## Merge gate

Do not merge if any path can bind a BASE_ONLY/PARTIAL/CONFLICT/candidate/stale bridge, modify a non-share base decision, accept entity/scope/as-of mismatch, lose nested M22 coverage lineage, allow approval of a non-DIRECT_BIND share field, mutate the input Draft, or expose an M23 direct write/canonicalization route.
