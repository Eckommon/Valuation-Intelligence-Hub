# Project State / 프로젝트 상태

> Canonical human-and-AI handoff. Repository-grounded state outranks chat or AI recollection.  
> 인간·AI 공통 정식 인계 문서. 저장소 근거 상태는 채팅·AI 기억보다 우선한다.

## Repository / 저장소

- `Eckommon/Valuation-Intelligence-Hub`
- Purpose: cross-asset, evidence-grounded valuation intelligence / 범자산 근거 기반 가치분석 인텔리전스

## Completed canonical baseline / 완료 기준선

| Milestone | Main commit | Issue |
|---|---|---:|
| M12 Guarded admission apply | `a40e92c196c39b40172711f38f7231f5e8812d52` | #26 |
| M13 Immutable SEC live evidence | `372b8b0b26307730c3e91afea97c979b59906042` | #28 |
| M14 Immutable OpenDART financial evidence | `1fff272cc583ec294226f5f530ebe483c2957fb5` | #30 |
| M15 Financial normalization + TTM | `a99a6f24fa6736b01b270a2eeeb4592e8b673563` | #32 |
| M16 Governed evidence → Draft binding proposal | `fbaf90bab04a877ba6afaaa035a4e99e9ef085a0` | #34 |
| M17 Human-approved noncanonical Draft binding apply | `ef68c2549bef842ef417d401140b49c88af209b5` | #38 |
| M18 Governed derived financial evidence + historical margins | `fb33cfbf401ab9c2e36ccd831bd059c8951214ba` | #40 |
| M19 Governed interest-bearing debt components + aggregation | `5b2ab53b0c83632abae187f12e1a682ecc254b77` | #42 |
| M20 Reviewed debt → `equity.debt` binding | `236547512919b5d68e283b3431183f56f5fc845c` | #44 |
| M21 Governed historical dilution reference | `03af933835b8fbcf9ef4e6b3fd1b3db7603782fc` | #46 |
| M22 Valuation-date common-share base + diluted-share bridge | `0a476cc9927b2d63164143447428f3e69b06051b` | #48 |

M21 final PR CI `34690797078` and post-merge main CI `34690857449` passed on Python 3.11/3.12.

M22 final PR CI `34691494304` and post-merge main CI `34691545005` passed on Python 3.11/3.12. Issue #48 is completed.

Earlier M1–M11 milestones remain completed and regression-locked in repository history.

## Authority model / 권위모델

```text
SOURCE
  ↓
IMMUTABLE SNAPSHOT / NOT CANONICAL
  ↓
EVIDENCE CANDIDATE / NOT CANONICAL
  ↓
NORMALIZED / DERIVED EVIDENCE / NOT CANONICAL
  ↓
GOVERNED CONTEXT / NOT CANONICAL
  ↓
BINDING PROPOSAL / NOT CANONICAL
  ↓
HUMAN APPROVAL LOCK / NOT CANONICAL
  ↓
BOUND DRAFT RESULT / NOT CANONICAL
  ↓
DRAFT GOVERNANCE → PROMOTION → ADMISSION → guarded apply → PR/CI merge
  ↓
CANONICAL
```

Source acquisition, normalization, derivation, coverage assertion, binding preparation, and Draft application never upgrade evidence authority by themselves.

## Active mission / 활성 미션

- Issue: `#50 [M23] Complete reviewed share bridge → equity.diluted_shares binding`
- PR: `#51 M23 Complete reviewed share bridge → equity.diluted_shares binding`
- Branch: `mission/m23-diluted-shares-binding-v01`
- Base main: `0a476cc9927b2d63164143447428f3e69b06051b`
- Status: `ACTIVE_FINALIZATION`

## M23 CI history / M23 CI 이력

- Core tested head: `1dc2fee8cb400ef642f7dd64460bb60956a88a29`
- Core CI `34692432321`: Python 3.11/3.12 `success`
- Interface/schema tested head: `005a1dd58dae6a2a3162c6a2b06629860540fffd`
- Interface/schema CI `34692614288`: Python 3.11/3.12 `success`

A fresh final-head CI is required after M23 docs/README/PROJECT_STATE changes. Only the exact current PR head after this handoff commit may authorize merge.

## M23 architecture / M23 구조

```text
validated M16 v0.1 proposal
or validated M20 v0.2 proposal
        +
complete reviewed fresh M22 diluted-share bridge
        ↓
draft-binding-proposal-v0.3
        ↓
M17 binding-approval-v0.1
        ↓
noncanonical bound Draft result
```

M23 never rebuilds the base proposal. It may replace only:

```text
equity.diluted_shares
```

Every other M16/M20 matrix decision must remain exactly equivalent to the embedded base proposal.

## M23 direct-bind gate / M23 직접바인딩 게이트

The M22 bridge must validate as:

```text
schema = diluted-share-bridge-v0.1
class = DERIVED_FACT
coverage = COMPLETE_REVIEWED_DILUTION_COVERAGE
binding_eligibility.eligible_for_future_direct_bind = true
candidate_fully_diluted_shares > 0
```

Additional exact compatibility requirements:

- entity ID match
- financial-scope match
- bridge `as_of` == base proposal `as_of`
- full nested M22 validation remains valid

The following fail closed before proposal creation:

```text
BASE_ONLY
PARTIAL_DILUTION_COVERAGE
CONFLICT_BLOCKED
candidate authority
stale/ineligible bridge
entity/scope mismatch
as_of mismatch
```

## v0.3 lineage / v0.3 lineage

The full base proposal and full M22 bridge are embedded. The projected `baseline_context.fully_diluted_shares` and the `equity.diluted_shares` DIRECT_BIND decision preserve:

```text
source_bridge_sha256
base_context_sha256
coverage_assertion_sha256
```

The v0.3 validator independently validates the embedded base proposal and M22 bridge, reconstructs the baseline projection and share decision, verifies that all non-share matrix decisions remain unchanged, recomputes completeness, and verifies the final proposal SHA.

## M17 apply extension / M17 적용 확장

`binding-approval-v0.1` remains the approval contract.

M17 can now apply:

```text
equity.cash
equity.debt
equity.diluted_shares
```

only when each approved field is DIRECT_BIND in the supplied proposal.

For `equity.diluted_shares`, the applied diff preserves:

```text
source_bridge_sha256
base_context_sha256
coverage_assertion_sha256
```

The original Draft object remains unchanged. The result remains `canonical=false` and must continue through existing Draft governance before any canonical state can exist.

## Interfaces / 인터페이스

CLI:

```text
binding-build-with-diluted-shares <base_proposal.json> <share_bridge.json>
binding-validate <proposal.json>
```

`binding-validate` now follows the v0.1 → v0.2 → v0.3 governed validator chain.

Web:

```text
/share-binding
/api/share-binding/build
/api/share-binding/validate
```

M23 Web is proposal calculate/validate only. There is no M23 approval/apply, Draft-file write, promotion, admission, or canonical-write route.

## M23 files / M23 파일

- `src/valuation_hub/share_draft_binding.py`
- `src/valuation_hub/binding_apply.py`
- `src/valuation_hub/web_share_binding.py`
- `src/valuation_hub/cli_entry.py`
- `schemas/draft_binding_proposal_v03.schema.json`
- `tests/test_m23_binding.py`
- `tests/test_m23_interfaces.py`
- `docs/SHARE_DRAFT_BINDING.md`
- `docs/M23_ACCEPTANCE.md`
- `docs/M23_IMPLEMENTATION_SUMMARY.md`

## Grounding authority / 근거화 권위

1. merged `main` files and decisions
2. `PROJECT_STATE.md` + active Issue/PR/branch
3. M22 bridge SHA → v0.3 proposal SHA → M17 approval SHA → bound Draft result SHA
4. current chat
5. AI recollection

## Exact resume point / 정확한 재개점

Run a fresh full Python 3.11/3.12 CI on the exact final PR #51 head after this handoff update.

Merge only if all remain green:

- v0.1/v0.2 base proposal validation
- complete reviewed fresh M22 bridge gate
- BASE_ONLY/PARTIAL/CONFLICT/candidate/stale fail-closed behavior
- exact entity/scope/as-of compatibility
- only `equity.diluted_shares` replacement in v0.3
- full nested M22 bridge revalidation
- share bridge/base-context/coverage-assertion lineage preservation
- M17 human approval lock for diluted shares
- original Draft immutability
- existing cash/debt apply regression compatibility
- CLI/Web no-write boundaries
- all M1-M23 regressions

After final-head CI passes, update PR #51 body with exact tested SHA and CI run, merge with `expected_head_sha`, confirm Issue #50 closes as completed, then verify post-merge `main` Python 3.11/3.12 CI before declaring M23 canonical.

If M23 closes cleanly, the next mission should be selected from the remaining valuation-completeness gaps rather than adding another parallel share layer. Reassess the equity-FCFF Draft material-field matrix and choose the highest-value unresolved governed input or the first non-equity valuation adapter.
