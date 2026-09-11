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
- Status: `READY_FOR_PR_CI_VALIDATION`

## Current M3 progress / 현재 M3 진행상태

### Case 1 — LS ELECTRIC

Status: `REFERENCE_RESULT_READY_ON_BRANCH`

- Model / 모델: `reference-equity-fcff-v0.1`
- Evidence gate / 근거 게이트: `PASS_MATERIAL_INPUTS_RECONCILED`
- Snapshot price / 스냅샷 가격: KRW 206,000
- Bear / Base / Bull intrinsic value/share: ~KRW 13,705 / 41,475 / 88,458
- Classification / 분류: `MARKET_PRICE_ABOVE_MODELED_BULL`
- Reverse Base stress / Base 역산 스트레스: ~4.62x proportional revenue/cash-economics scale
- Regression lock / 회귀 잠금: `tests/test_reference_ls_electric.py`

### Case 2 — LS Eco Energy / LS에코에너지

Status: `REFERENCE_RESULT_READY_ON_BRANCH`

- Model / 모델: `reference-equity-fcff-v0.1`
- Evidence gate / 근거 게이트: `PASS_MATERIAL_INPUTS_RECONCILED`
- Snapshot price / 스냅샷 가격: KRW 47,900
- Bear / Base / Bull intrinsic value/share: ~KRW 4,445 / 27,326 / 57,748
- Classification / 분류: `MARKET_PRICE_BETWEEN_MODELED_BASE_AND_BULL`
- Reverse Base stress / Base 역산 스트레스: ~1.67x proportional revenue/cash-economics scale
- Regression lock / 회귀 잠금: `tests/test_reference_ls_eco_energy.py`

### Case 3 — Jet.AI

Status: `REFERENCE_RESULT_READY_ON_BRANCH`

- Model / 모델: `reference-venture-probability-v0.1`
- Evidence gate / 근거 게이트: `PASS_VENTURE_MODEL_INPUTS_RECONCILED`
- Model selection / 모델선택: `PROBABILITY_WEIGHTED_VENTURE_OPTION_MODEL`
- Snapshot price / 스냅샷 가격: USD 1.28
- Failure / Survival / Breakout probabilities: 60% / 30% / 10%
- Probability-weighted present value/share / 확률가중 현재 주당가치: ~USD 3.247
- Reverse diagnostic / 역산 진단: Survival 30% 고정 시 시장가격에 필요한 Breakout 확률 ~2.20%
- Classification / 분류: `OPTION_LIKE_EXPECTED_VALUE_ABOVE_MARKET_WITH_EXTREME_MODEL_RISK`
- Standard historical P/E/FCFF extrapolation / 역사적 PER·FCFF 단순연장: `REJECTED`
- Regression lock / 회귀 잠금: `tests/test_reference_jet_ai.py`

The three cases intentionally represent three different valuation regimes: market-implied Hyper-Bull pressure, Base-versus-Bull growth economics, and dilution-aware venture optionality.

세 사례는 의도적으로 서로 다른 가치평가 체계를 대표한다: 시장 내재 Hyper-Bull 압력, Base 대 Bull 성장경제성, 희석을 반영한 벤처 옵션가치.

## New reusable kernel added in M3 / M3 신규 공통 커널

- `src/valuation_hub/venture.py` — probability-weighted venture/option valuation with explicit dilution / 명시적 희석을 포함한 확률가중 벤처·옵션 가치평가
- `tests/test_venture.py` — probability, dilution and reverse-probability invariants / 확률·희석·역산확률 불변조건

## Grounding authority / 근거화 권위

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

Open the M3 pull request, run the full Python 3.11/3.12 CI suite, inspect failures if any, and merge only if all three reference cases and the shared venture engine pass. After merge, close Issue #3 and define the next productization mission: a stable case registry plus executable CLI foundation that uses the same kernels without duplicating valuation logic.

M3 PR을 개설하고 Python 3.11/3.12 전체 CI를 실행하며 실패가 있으면 원인을 조정한다. 세 기준 사례와 공통 Venture Engine이 모두 통과할 때만 병합한다. 병합 후 Issue #3을 종료하고 다음 제품화 미션인 안정적 사례 레지스트리 + 실행형 CLI 기반을 정의한다. CLI는 기존 가치평가 로직을 복제하지 않고 동일 커널을 사용해야 한다.
