# Project State / 프로젝트 상태

> This file is the canonical human-and-AI session handoff for the active repository state. It must describe only repository-grounded state and must not depend on chat memory.
>
> 본 파일은 활성 저장소 상태에 대한 인간·AI 공통 정식 인계 문서이다. 저장소 근거만 기술하며 채팅 기억에 의존해서는 안 된다.

## Repository identity / 저장소 식별

- Repository / 저장소: `Eckommon/Valuation-Intelligence-Hub`
- Purpose / 목적: Cross-asset, evidence-grounded valuation intelligence system / 범자산 근거 기반 가치분석 인텔리전스 시스템
- Documentation rule / 문서 원칙: English + Korean bilingual canonical documentation / 정식 문서 영한문 병기
- Product strategy / 제품 전략: **Web-first hybrid** — Web UI primary, CLI/local secondary, one shared kernel / **웹 우선 하이브리드** — Web UI 주 인터페이스, CLI·로컬 보조, 단일 공통 커널

## Canonical baseline / 정식 기준선

### Bootstrap v0.1
`1d9881bcffb2499fdb72204070d058ef86676841`

### M1 Evidence grounding + public-equity normalization / M1 근거화 + 상장기업 정규화
`e3a11259c0e248f055ee16466e08ccfef2a4d13e`
Issue `#1`: `COMPLETED`

### M2 Scenario + reverse valuation engines / M2 시나리오 + 역산 가치평가 엔진
`2b6d7522e7d847673a7310b9e7f4346cd26cb59e`
Issue `#2`: `COMPLETED`

## Active mission / 활성 미션

- Issue: `#3 [M3] Re-source 3 equity reference cases / 3개 상장기업 기준 사례 재수집`
- Branch: `mission/m3-reference-cases-evidence-rebuild-v01`
- Status: `ACTIVE`
- Required order / 필수 순서:
  1. LS ELECTRIC
  2. LS Eco Energy / LS에코에너지
  3. Jet.AI

## Current M3 progress / 현재 M3 진행상태

### Case 1 — LS ELECTRIC

Status: `REFERENCE_RESULT_READY_ON_BRANCH`

Evidence/model/result files / 근거·모델·결과 파일:

- `analyses/equities/KR_010120_LS_ELECTRIC/evidence_manifest.json`
- `evidence_market.json`
- `evidence_financials.json`
- `evidence_cost_of_capital.json`
- `case_inputs.json`
- `valuation_result.json`
- `REPORT.md`
- `tests/test_reference_ls_electric.py`

Evidence gate / 근거 게이트: `PASS_MATERIAL_INPUTS_RECONCILED`

Reference model / 기준 모델: `reference-equity-fcff-v0.1`

Reference-case outputs / 기준사례 산출:

- Bear intrinsic value/share / Bear 현재 내재가치: ~KRW 13,705
- Base intrinsic value/share / Base 현재 내재가치: ~KRW 41,475
- Bull intrinsic value/share / Bull 현재 내재가치: ~KRW 88,458
- Market price in snapshot / 스냅샷 시장가격: KRW 206,000
- Classification / 분류: `MARKET_PRICE_ABOVE_MODELED_BULL`
- Base reverse stress diagnostic / Base 역산 스트레스 진단: ~4.62x proportional revenue/cash-economics scale required under fixed Base margins/WACC/g.

These outputs are versioned model results, not forecasts or recommendations. The regression test locks stored values against the shared scenario engine.

위 산출물은 버전 관리된 모델 결과이며 전망 또는 투자권고가 아니다. 회귀테스트는 저장 결과가 공통 시나리오 엔진과 일치하도록 고정한다.

### Case 2 — LS Eco Energy / LS에코에너지

Status: `NEXT`

Rebuild evidence bundles and case inputs under the same M1/M2 contracts. Do not copy prior-chat exploratory values into canonical files.

동일한 M1/M2 계약 아래 근거 묶음과 사례 입력을 재구축한다. 이전 채팅의 탐색 수치를 정식 파일로 복사하지 않는다.

### Case 3 — Jet.AI

Status: `QUEUED`

Use dilution-aware probability/venture logic where conventional FCFF DCF is economically inappropriate.

전통적 FCFF DCF가 경제적으로 부적합한 구간에서는 희석·확률을 반영한 벤처/옵션형 논리를 사용한다.

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

The project must deliver a **web-first hybrid valuation product**. Non-developers use a human-friendly Web UI; advanced/private/batch workflows use CLI/local execution. Web, CLI, API and any future desktop shell must use the same kernel, schemas, evidence gates and model registry.

프로젝트는 **웹 우선 하이브리드 가치분석 제품**을 제공해야 한다. 비개발자는 사용자 친화 Web UI를 사용하고 고급·비공개·대량 작업은 CLI·로컬 실행을 사용한다. Web, CLI, API, 향후 데스크톱 셸은 동일 커널·스키마·근거게이트·모델 레지스트리를 사용해야 한다.

## Exact resume point / 정확한 재개점

Rebuild **LS Eco Energy / LS에코에너지** as M3 Case 2: source primary/authoritative financial, market, capital-structure and cost-of-capital evidence; reconcile material inputs; construct versioned Bear/Base/Bull inputs; run FCFF/sensitivity/reverse valuation; store regression-locked outputs and bilingual report. Then proceed to Jet.AI. Do not close Issue #3 or merge M3 until all three cases pass CI and acceptance criteria.

M3 Case 2인 **LS에코에너지**를 재구축한다. 1차·권위 재무, 시장, 자본구조, 자본비용 근거를 수집하고 중요 입력을 조정한 뒤 버전 관리 Bear/Base/Bull 입력을 구성하고 FCFF·민감도·역산 가치평가를 실행하며 회귀 고정 결과와 영한문 보고서를 저장한다. 이후 Jet.AI로 진행한다. 세 사례가 모두 CI와 완료조건을 통과하기 전에는 Issue #3을 종료하거나 M3를 병합하지 않는다.
