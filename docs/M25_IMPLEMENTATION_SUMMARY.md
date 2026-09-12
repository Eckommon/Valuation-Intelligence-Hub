# M25 Implementation Summary / M25 구현요약

## Delivered / 구현완료

M25 adds governed terminal-growth assumptions on top of M24 reviewed WACC governance.

M25는 M24 reviewed WACC 거버넌스 위에 영구성장률 가정 거버넌스를 추가한다.

### Core / 코어

- `src/valuation_hub/terminal_growth_assumption.py`
  - source-backed long-run inflation / real-growth anchors
  - independent nominal-growth ceiling calculation
  - scenario-specific explicit terminal-growth assumptions
  - WACC and macro-ceiling constraints
  - candidate/reviewed authority separation
  - SHA-locked human review
- `src/valuation_hub/terminal_growth_draft_binding.py`
  - `draft-binding-proposal-v0.5`
  - accepts only validated M24 v0.4 base
  - exact WACC package lineage dependency
  - only `scenario.terminal_growth` replacement
- `src/valuation_hub/binding_apply.py`
  - M25 scenario-specific apply support
  - exact target-set checks
  - WACC dependency enforcement at approval/apply time
  - scenario-by-scenario diff lineage

### Interfaces / 인터페이스

- `src/valuation_hub/cli_entry_m25.py`
  - additive wrapper above M24
  - pre-M25 commands delegate unchanged
- `src/valuation_hub/web_terminal_growth.py`
  - `/terminal-growth`
  - `/api/terminal-growth/*`
  - calculate/validate only
- `pyproject.toml`
  - `vih = valuation_hub.cli_entry_m25:main`

### Schemas / 스키마

- `schemas/terminal_growth_anchor_input.schema.json`
- `schemas/terminal_growth_assumption_candidate.schema.json`
- `schemas/terminal_growth_review_assertion.schema.json`
- `schemas/reviewed_terminal_growth_assumption.schema.json`
- `schemas/draft_binding_proposal_v05.schema.json`

### Tests / 테스트

- `tests/test_m25_terminal_growth_binding.py`
  - macro anchor arithmetic
  - stale/Tier-D blocking
  - macro ceiling
  - negative-growth support
  - reviewed authority
  - v0.4-only dependency
  - WACC lineage equality
  - exact scenario targets
  - combined WACC + terminal-growth apply
  - terminal-growth-only WACC precondition
  - Draft immutability
- `tests/test_m25_hardening.py`
  - valid low-WACC `g >= WACC` rejection
  - calculation re-signing bypass rejection
  - v0.5 policy weakening rejection
  - baseline projection tamper rejection
- `tests/test_m25_interfaces.py`
  - additive CLI interception/delegation boundary
  - explicit candidate artifact inputs
  - Web assumption/no-write contract

## CI checkpoints / CI 체크포인트

- Core head `9e1c6d34c8d8d1189ae6703d6cce2b0608585d6f`
  - CI `34694364761`
  - Python 3.11/3.12 `success`
- Hardened core head `fb9b54dab458582e569ff7ced994f10cefb82c42`
  - CI `34694428378`
  - Python 3.11/3.12 `success`
- Interface/schema head `cb0a83d32c9492d18a8168cfc233ead9c90d837a`
  - CI `34694626345`
  - Python 3.11/3.12 `success`

## Remaining closeout / 남은 종결절차

1. refresh README + `PROJECT_STATE.md`
2. run fresh full Python 3.11/3.12 CI on exact final PR head
3. update PR #55 with final tested SHA/run
4. merge with `expected_head_sha`
5. confirm Issue #54 `completed`
6. verify post-merge `main` Python 3.11/3.12 CI

Only after these steps may M25 be declared canonical.

위 절차 완료 후에만 M25를 canonical 완료로 선언한다.
