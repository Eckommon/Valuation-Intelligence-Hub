# Project State / 프로젝트 상태

> This file is the canonical human-and-AI session handoff for the active repository state. It must describe only repository-grounded state and must not depend on chat memory.
>
> 본 파일은 활성 저장소 상태에 대한 인간·AI 공통 정식 인계 문서이다. 저장소 근거만 기술하며 채팅 기억에 의존해서는 안 된다.

## Repository identity / 저장소 식별

- Repository / 저장소: `Eckommon/Valuation-Intelligence-Hub`
- Purpose / 목적: Cross-asset, evidence-grounded valuation intelligence system / 범자산 근거 기반 가치분석 인텔리전스 시스템
- Documentation rule / 문서 원칙: English + Korean bilingual canonical documentation / 정식 문서 영한문 병기

## Canonical baseline / 정식 기준선

### Bootstrap v0.1 / Bootstrap v0.1

Merged to `main` via:

`1d9881bcffb2499fdb72204070d058ef86676841`

### M1 Evidence grounding + public-equity normalization / M1 근거화 + 상장기업 정규화

Merged to `main` via:

`e3a11259c0e248f055ee16466e08ccfef2a4d13e`

M1 established the evidence/provenance policy, machine-readable evidence schema, fail-closed evidence-promotion gate, public-equity normalization primitives, GitHub Actions CI, and executable-product end-state.

M1은 근거·출처 정책, 기계 판독 근거 스키마, fail-closed 근거 승격 게이트, 상장기업 정규화 원시함수, GitHub Actions CI, 사용자 실행형 제품 최종 목표를 확립했다.

Issue `#1` is `COMPLETED`.

### M2 Scenario + reverse valuation engines / M2 시나리오 + 역산 가치평가 엔진

Merged to `main` via:

`2b6d7522e7d847673a7310b9e7f4346cd26cb59e`

M2 established the explicit FCFF scenario runner, WACC × terminal-growth sensitivity grid, deterministic bisection solver, terminal-growth reverse valuation, revenue-scale reverse valuation, regression tests, and bilingual scenario/reverse policy.

M2는 명시기간 FCFF 시나리오 실행기, WACC × 영구성장률 민감도, 결정론적 이분법 솔버, 영구성장률 역산, 매출스케일 역산, 회귀테스트, 영한문 시나리오·역산 정책을 확립했다.

Issue `#2` is `COMPLETED`.

## Active mission / 활성 미션

- Issue: `#3 [M3] Re-source 3 equity reference cases / 3개 상장기업 기준 사례 재수집`
- Branch: `mission/m3-reference-cases-evidence-rebuild-v01`
- Status: `ACTIVE`
- Required order / 필수 순서:
  1. LS ELECTRIC
  2. LS Eco Energy / LS에코에너지
  3. Jet.AI

## Current M3 progress / 현재 M3 진행상태

### LS ELECTRIC

Status: `EVIDENCE_REBUILD_ACTIVE`

Created:

- `analyses/equities/KR_010120_LS_ELECTRIC/evidence_manifest.json`

Primary Tier-A evidence already recorded includes:

정식 Tier-A 1차근거로 기록 완료된 항목:

- FY2025 consolidated revenue / 2025 연결 매출
- FY2025 consolidated operating income / 2025 연결 영업이익
- FY2025 consolidated net income / 2025 연결 순이익
- 2026 Q2 revenue / 2026 2분기 매출
- 2026 Q2 operating income / 2026 2분기 영업이익
- 2026 Q2 order backlog / 2026 2분기 수주잔고
- 2026 5-for-1 stock split / 2026년 5:1 주식분할
- post-split issued common shares = 150,000,000 / 분할 후 발행 보통주 150,000,000주

Promotion gate remains:

`HOLD_MATERIAL_INPUTS_INCOMPLETE`

The valuation MUST NOT be canonicalized until current market price, current diluted-share reconciliation, 2026 H1 debt/cash, working capital, D&A, CAPEX, tax normalization, and cost-of-capital inputs are sourced and reconciled.

현재 시장가격, 현 희석주식수 조정, 2026 H1 부채·현금, 운전자본, D&A, CAPEX, 세율 정규화, 자본비용 입력을 출처화·조정하기 전 가치평가 결과를 정식 승격해서는 안 된다.

### LS Eco Energy / LS에코에너지

Status: `NOT_STARTED_M3`

### Jet.AI

Status: `NOT_STARTED_M3`

## Grounding authority / 근거화 권위

For project-state recovery, use this order:

프로젝트 상태 복구 시 다음 순서를 사용한다.

1. `main` canonical files and merged decisions / `main` 정식 파일·병합 결정
2. This `PROJECT_STATE.md` and active mission records / 본 상태파일·활성 미션 기록
3. Active Issue/PR/branch contents / 활성 Issue·PR·브랜치 내용
4. Primary evidence manifests for target cases / 대상 사례 1차 근거 매니페스트
5. Current chat / 현재 대화
6. AI memory / AI 기억

If repository state and AI recollection disagree, repository state wins unless a newer primary source requires explicit reconciliation.

저장소 상태와 AI 기억이 다르면 더 최신의 1차자료에 의한 명시적 조정이 필요한 경우를 제외하고 저장소 상태가 우선한다.

## Product end-state / 제품 최종 목표

The project must eventually deliver a user-executable valuation tool, not only documentation or libraries. The intended path is shared kernel → stable case format → CLI → user-friendly Web UI → optional API/automation, all using the same valuation kernel.

프로젝트는 최종적으로 문서나 라이브러리뿐 아니라 사용자가 직접 실행할 수 있는 가치분석 도구를 제공해야 한다. 동일 가치평가 커널을 공유하며 커널 → 안정적 사례 포맷 → CLI → 사용자 친화 Web UI → 선택적 API·자동화 순으로 발전한다.

## Exact resume point / 정확한 재개점

Continue LS ELECTRIC evidence reconstruction. Source and reconcile the remaining material inputs listed in `evidence_manifest.json`, then produce normalized historicals and only after the promotion gate passes run the five valuation lenses, Bear/Base/Bull FCFF DCF, sensitivity, reverse valuation, and expected IRR. Do not begin LS Eco Energy until the LS ELECTRIC reference case is reproducible or explicitly terminal-HOLD.

LS ELECTRIC 근거 재구축을 계속한다. `evidence_manifest.json`의 잔여 중요 입력을 출처화·조정하고 정규화 과거치를 생성한 뒤 승격 게이트 통과 후에만 5대 가치평가 렌즈, Bear/Base/Bull FCFF DCF, 민감도, 역산 가치평가, 기대 IRR을 실행한다. LS ELECTRIC 사례가 재현 가능 상태 또는 명시적 terminal-HOLD가 되기 전 LS에코에너지로 넘어가지 않는다.
