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
| M23 Complete reviewed share bridge → `equity.diluted_shares` | `58d963238992f562c89c8325b42046ae35ac71bf` | #50 |
| M24 Governed WACC assumption → `scenario.wacc` | `ca85f04c1bd84c5189f78c81e2653cc4f65bccca` | #52 |

M24 final PR CI `34693544084` and post-merge `main` CI `34693990230` both passed Python 3.11/3.12. Issue #52 is completed.

Earlier milestones remain completed and regression-locked in repository history.

## Authority model / 권위모델

```text
SOURCE
  ↓
IMMUTABLE / SOURCE-LOCKED INPUT / NOT CANONICAL
  ↓
FACT / NORMALIZED FACT / ASSUMPTION_CANDIDATE
  ↓
GOVERNED CONTEXT or HUMAN-REVIEWED ASSUMPTION / NOT CANONICAL
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

Calculation never silently upgrades `ASSUMPTION_CANDIDATE` to `ASSUMPTION`, nor `ASSUMPTION` to `FACT`.

## Active mission / 활성 미션

- Issue: `#54 [M25] Governed terminal-growth assumption + scenario.terminal_growth binding`
- PR: `#55 M25 Governed terminal growth + scenario.terminal_growth binding`
- Branch: `mission/m25-terminal-growth-binding-v01`
- Base main: `ca85f04c1bd84c5189f78c81e2653cc4f65bccca`
- Status: `ACTIVE_FINALIZATION`

## M25 CI history / M25 CI 이력

- Core head: `9e1c6d34c8d8d1189ae6703d6cce2b0608585d6f`
  - CI `34694364761`: Python 3.11/3.12 `success`
- Hardened core head: `fb9b54dab458582e569ff7ced994f10cefb82c42`
  - CI `34694428378`: Python 3.11/3.12 `success`
- Interface/schema head: `cb0a83d32c9492d18a8168cfc233ead9c90d837a`
  - CI `34694626345`: Python 3.11/3.12 `success`

A fresh final-head CI is required after M25 docs/README/PROJECT_STATE changes. Only that exact tested head may authorize merge.

## M25 authority boundary / M25 권위경계

```text
macro forecast / anchor != terminal-growth fact
selected g              != reviewed terminal-growth assumption
ASSUMPTION_CANDIDATE     != ASSUMPTION
reviewed ASSUMPTION      != canonical state
```

M25 never auto-generates terminal growth from a macro forecast. Macro evidence constrains a scenario assumption; human review creates assumption authority.

M25는 거시 전망에서 영구성장률을 자동 생성하지 않는다. 거시 근거는 시나리오 가정의 경계를 제공하며 인간 검토가 가정 권위를 만든다.

## Required dependency / 필수 의존성

M25 requires a valid M24:

```text
reviewed-wacc-assumption-v0.1
```

The full WACC package is embedded in the M25 candidate and independently revalidated. The WACC package SHA used by M25 must exactly equal the WACC package SHA embedded in the v0.4 base proposal.

M25 candidate에 전체 WACC 패키지를 내장하고 독립 재검증한다. M25가 사용한 WACC package SHA는 v0.4 base proposal에 내장된 WACC package SHA와 정확히 같아야 한다.

## Macro anchor / 거시 Anchor

Required source-backed inputs:

```text
long_run_inflation
long_run_real_growth
```

Each carries value, observed date, claim class, source publisher/type/tier/locator, source SHA, and input SHA.

Both anchors use a v0.1 freshness maximum of 365 days. Future-dated anchors fail closed. Tier D cannot become human-review eligible.

The nominal ceiling is independently reconstructed:

```text
nominal_growth_anchor
  = (1 + long_run_inflation)
  × (1 + long_run_real_growth)
  - 1
```

This ceiling is not itself terminal growth.

이 상한은 영구성장률 그 자체가 아니다.

## Scenario terminal growth / 시나리오 영구성장률

Every target scenario must include exactly one:

```text
scenario_name
terminal_growth
rationale
```

The candidate validator enforces:

```text
g > -1
g < reviewed WACC
g <= nominal_growth_anchor
```

Negative terminal growth is supported when explicitly selected and reviewed.

명시적으로 선택·검토된 음의 영구성장률은 허용한다.

## Human review / 인간검토

`terminal-growth-review-assertion-v0.1` locks:

- exact candidate SHA
- exact source WACC package SHA
- methodology version
- valuation `as_of`
- exact scenario set
- exact scenario growth values and rationales
- reviewer
- timezone-aware `approved_at`
- review basis
- assertion SHA

Approval cannot predate valuation `as_of`.

Finalization yields:

```text
reviewed-terminal-growth-assumption-v0.1
class = ASSUMPTION
binding_eligibility = REVIEWED_TERMINAL_GROWTH_ASSUMPTION
```

## v0.5 binding / v0.5 바인딩

```text
validated draft-binding-proposal-v0.4
        +
reviewed terminal-growth ASSUMPTION
        ↓
draft-binding-proposal-v0.5
```

M25 accepts **only** v0.4 as its base and may replace only:

```text
scenario.terminal_growth
```

All other matrix entries, including `scenario.wacc`, must remain equivalent to the embedded v0.4 proposal.

The v0.5 validator reconstructs the exact policy, projection, decision, completeness, WACC dependency, and final SHA. Re-signing only the outer object cannot legitimize altered nested state.

## Apply-time WACC dependency / 적용시점 WACC 의존성

A terminal-growth assumption reviewed under one WACC cannot be applied against another Draft WACC.

한 WACC를 기준으로 검토한 영구성장률을 다른 Draft WACC에 적용할 수 없다.

If `scenario.terminal_growth` is approved alone, the Draft must already carry the exact reviewed WACC for every target scenario.

If the Draft does not already carry that WACC, `scenario.wacc` must be approved in the same M17 approval.

Applied terminal-growth diff form:

```text
before = {scenario_name: old_g, ...}
after  = {scenario_name: reviewed_g, ...}
```

and preserves:

```text
source_terminal_growth_package_sha256
source_wacc_package_sha256
review_assertion_sha256
scenario_names
```

The input Draft remains unchanged and the result remains noncanonical.

## Interfaces / 인터페이스

M25 CLI is additive. It intercepts only M25 commands plus v0.5-aware `binding-validate` and `web`; every older M1-M24 command delegates to the M24 dispatcher.

CLI:

```text
terminal-growth-anchor-build
terminal-growth-anchor-validate
terminal-growth-candidate-build
terminal-growth-candidate-validate
terminal-growth-review-build
terminal-growth-review-validate
terminal-growth-finalize
terminal-growth-validate
binding-build-with-terminal-growth
binding-validate
```

Web:

```text
/terminal-growth
/api/terminal-growth/candidate-build
/api/terminal-growth/candidate-validate
/api/terminal-growth/review-build
/api/terminal-growth/review-validate
/api/terminal-growth/finalize
/api/terminal-growth/validate
/api/terminal-growth/binding-build
/api/terminal-growth/binding-validate
```

The M25 Web layer has no Draft-apply, file-write, promotion, admission, or canonical-write endpoint.

## M25 files / M25 파일

- `src/valuation_hub/terminal_growth_assumption.py`
- `src/valuation_hub/terminal_growth_draft_binding.py`
- `src/valuation_hub/binding_apply.py`
- `src/valuation_hub/cli_entry_m25.py`
- `src/valuation_hub/web_terminal_growth.py`
- `schemas/terminal_growth_anchor_input.schema.json`
- `schemas/terminal_growth_assumption_candidate.schema.json`
- `schemas/terminal_growth_review_assertion.schema.json`
- `schemas/reviewed_terminal_growth_assumption.schema.json`
- `schemas/draft_binding_proposal_v05.schema.json`
- `tests/test_m25_terminal_growth_binding.py`
- `tests/test_m25_hardening.py`
- `tests/test_m25_interfaces.py`
- `docs/TERMINAL_GROWTH_ASSUMPTION_BINDING.md`
- `docs/M25_ACCEPTANCE.md`
- `docs/M25_IMPLEMENTATION_SUMMARY.md`

## Grounding authority / 근거화 권위

1. merged `main` files and decisions
2. `PROJECT_STATE.md` + active Issue/PR/branch
3. macro-anchor input SHA → M24 WACC package SHA → M25 candidate SHA → review assertion SHA → reviewed terminal-growth package SHA → v0.5 proposal SHA → M17 approval/result SHA
4. current chat
5. AI recollection

## Exact resume point / 정확한 재개점

Run a fresh full Python 3.11/3.12 CI on the exact current PR #55 head after this handoff update.

Merge only if all remain green:

- anchor provenance/integrity validation
- anchor freshness and Tier-D review blocking
- nominal macro ceiling recomputation
- exact M24 reviewed-WACC dependency
- `g > -1`, `g < WACC`, and `g <= nominal_growth_anchor`
- candidate/reviewed authority separation
- human review lineage lock
- v0.4-only base requirement
- exact WACC package SHA equality
- v0.5 exact policy reconstruction
- only `scenario.terminal_growth` replacement
- exact full-Draft scenario target set
- terminal-growth-only apply requires reviewed WACC already in Draft
- otherwise WACC + terminal growth approved together
- scenario-by-scenario diff reconstruction
- source Draft immutability
- existing M1-M24 regression compatibility
- additive CLI delegation
- Web no-write boundary

After final-head CI passes, update PR #55 with the exact tested SHA/run, merge with `expected_head_sha`, confirm Issue #54 closes as completed, then verify post-merge `main` Python 3.11/3.12 CI before declaring M25 canonical.

If M25 closes cleanly, the next high-value mission should be selected by re-grounding the remaining `MATERIAL_FIELDS`. Current architecture suggests a **single governed forecast-scenario package** covering revenue, EBIT margin, tax, D&A, CAPEX, and ΔNWC together is likely more coherent than six independent one-field missions.
