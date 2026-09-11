# Project State / 프로젝트 상태

> Canonical human-and-AI handoff. Repository-grounded state outranks chat or AI recollection.  
> 인간·AI 공통 정식 인계 문서. 저장소 근거 상태는 채팅·AI 기억보다 우선한다.

## Repository identity / 저장소 식별

- Repository / 저장소: `Eckommon/Valuation-Intelligence-Hub`
- Purpose / 목적: Cross-asset, evidence-grounded valuation intelligence system / 범자산 근거 기반 가치분석 인텔리전스 시스템
- Product strategy / 제품 전략: Web-first hybrid; one shared valuation/evidence kernel / 웹 우선 하이브리드; 단일 공통 가치·근거 커널
- Documentation / 문서: English + Korean bilingual / 영한문 병기

## Canonical baseline / 정식 기준선

- Bootstrap: `1d9881bcffb2499fdb72204070d058ef86676841`
- M1 Evidence grounding + normalization: `e3a11259c0e248f055ee16466e08ccfef2a4d13e` — #1 `COMPLETED`
- M2 Scenario + reverse valuation: `2b6d7522e7d847673a7310b9e7f4346cd26cb59e` — #2 `COMPLETED`
- M3 Evidence-grounded reference cases: `5c39c6a1857a5b4aeffa9782399e24bcbd77c0ae` — #3 `COMPLETED`
- M4 Executable registry + CLI: `db14a21bb706f4f3cd74f5a33d88ca5937249aa5` — #8 `COMPLETED`
- M5 Web MVP: `5867363d26d4efa57e5fb92d4861de9bfbf00d7f` — #12 `COMPLETED`
- M6 Interactive preview + evidence browser: `caf7576c1a2c13916449d445f5badc3a29712d36` — #14 `COMPLETED`
- M7 Product UX + visualization: `243cea0233031088fac8edb0362971326840b858` — #16 `COMPLETED`
- M8 User Draft workflow: `899271709ef3c49d431e0fce716eff48d0b22370` — #18 `COMPLETED`
- M9 Reviewed promotion protocol: `3e2d0a58b13c6e90ae6e665db72dc2683d5fad3f` — #20 `COMPLETED`
- M10 Deterministic promotion package staging: `951e6be93a2d98db3e71c7e9f77bc06b90516dd2` — #22 `COMPLETED`

M10 post-merge `main` CI run `34566368596` completed `success` on Python 3.11/3.12.

M10 병합 후 `main` CI run `34566368596`은 Python 3.11/3.12에서 `success` 완료했다.

## Canonical product capability / 정식 제품 기능

- Three regression-locked reference cases / 3개 회귀 잠금 기준 사례
- Shared FCFF and venture-probability kernels / 공통 FCFF·벤처 확률가중 커널
- Versioned registry + runtime/canonical drift validation / 버전 레지스트리 + runtime drift 검증
- CLI + local Web product / CLI + 로컬 Web 제품
- Evidence browser + scenario preview / 근거 탐색 + 시나리오 preview
- User Draft Lab / 사용자 Draft 랩
- M9 evidence-governed Candidate + human SHA-256 review lock / M9 근거 거버넌스 Candidate + 인간검토 해시 잠금
- M10 deterministic tamper-evident promotion package / M10 결정론적 변조탐지 승격 패키지

## Active mission / 활성 미션

- Issue: `#24 [M11] Versioned reviewed-Draft canonical adapter + admission contract / 검토 Draft 정식 adapter + 수용 계약`
- Branch: `mission/m11-reviewed-draft-canonical-adapter-v01`
- Status: `ACTIVE_IMPLEMENTATION`

## M11 objective / M11 목표

M11 provides a lossless bridge from an M10 reviewed package to proposed canonical repository artifacts while keeping actual canonical authority behind a separate reviewed PR + CI + merge.

M11은 M10 검토 패키지에서 정식 저장소 제안 산출물까지 무손실 연결하되 실제 정식 권위는 별도 인간 검토 PR + CI + 병합 뒤에 유지한다.

```text
DRAFT_USER_SUPPLIED
  ↓ M9 evidence governance + human review lock
REVIEW_APPROVED_READY_FOR_PR
  ↓ M10 deterministic staging
PROMOTION_PACKAGE_STAGED / NOT_CANONICAL
  ↓ M11 deterministic admission planning
CANONICAL_ADMISSION_PROPOSED / BUNDLE canonical=false
  ↓ exact repository PR + full CI + human review + merge
CANONICAL
```

## M11 adapters / M11 Adapter

- `reviewed-draft-equity-fcff-v0.1`
- `reviewed-draft-venture-probability-v0.1`

Registry entries without `adapter` continue using the legacy M3 reference route. Existing LS ELECTRIC, LS Eco Energy, and Jet.AI execution remains unchanged.

`adapter`가 없는 registry 항목은 기존 M3 reference 경로를 그대로 사용한다. 기존 LS ELECTRIC, LS에코에너지, Jet.AI 실행은 변경되지 않는다.

## Lossless admission rule / 무손실 수용 규칙

M8 equity Draft stores absolute forecast D&A/CAPEX/ΔNWC while legacy reference cases reconstruct economics from opening NWC and revenue-linked ratios. M11 therefore embeds the exact reviewed Draft and never reconstructs it into the legacy representation.

M8 equity Draft는 D&A/CAPEX/ΔNWC 전망 절대값을 저장하지만 기존 reference 사례는 opening NWC와 매출연동 비율에서 경제값을 재구축한다. M11은 검토 Draft 원문을 그대로 내장하며 legacy 표현으로 재구축하지 않는다.

## Canonical compatibility profile v0.1 / 정식 호환 프로파일 v0.1

Generic M8 Drafts remain flexible. M11 canonical admission v0.1 requires the scenario names already expected by the current product runtime contract:

일반 M8 Draft는 유연성을 유지하지만 M11 정식 수용 v0.1은 현재 제품 runtime 계약이 기대하는 시나리오 이름을 요구한다.

- equity: exactly `BEAR / BASE / BULL`
- venture: exactly `FAILURE / SURVIVAL / BREAKOUT`

A valid M8/M10 case may therefore fail M11 admission without losing or rewriting data.

따라서 유효한 M8/M10 사례도 데이터 변경 없이 M11 수용에서 fail-closed될 수 있다.

## Admission bundle / 수용 Bundle

- schema: `schemas/canonical_admission_bundle.schema.json`
- service: `src/valuation_hub/admission.py`
- state: `CANONICAL_ADMISSION_PROPOSED`
- bundle flag: `canonical=false`
- valuation date: derived from governed `market_price` evidence `as_of`
- artifacts:
  1. `SOURCE_PACKAGE.json`
  2. `case_inputs.json`
  3. `evidence_manifest.json`
  4. `evidence_reviewed.json`
  5. `valuation_result.json`
  6. `REPORT.md`
- proposed registry entry contains explicit `adapter`
- every artifact + full bundle SHA-256 locked / 모든 산출물 + 전체 bundle SHA-256 잠금

The proposed files contain `canonical=true` because they are intended canonical bytes, but they have no canonical authority until the exact PR is merged.

제안 파일은 정식 반영 대상 bytes이므로 `canonical=true`를 포함하지만 정확한 PR 병합 전에는 정식 권위를 갖지 않는다.

## Runtime provenance chain / Runtime 출처 체인

Every admitted reviewed case must revalidate:

```text
SOURCE_PACKAGE
→ approved Candidate SHA-256
→ human review-scope SHA-256
→ exact reviewed_draft
→ exact evidence + input_governance
→ adapter/model compatibility
→ shared-kernel recomputation
→ stored canonical runtime
```

A mismatch blocks `validate_case()` and therefore blocks CLI/Web/API consumption.

불일치가 있으면 `validate_case()`와 그 위의 CLI/Web/API 소비경로가 차단된다.

## Interactive compatibility / 인터랙티브 호환

- legacy reference cases keep the existing preview route / 기존 reference 사례 preview 경로 유지
- reviewed equity preview uses absolute Draft economics and proportional D&A/CAPEX/ΔNWC scaling / 검토 equity preview는 절대 Draft 경제값 사용
- reviewed venture preview reuses the same venture kernel / 검토 venture preview는 동일 벤처 커널 재사용
- all previews remain `PREVIEW_NOT_CANONICAL` / 모든 preview는 비정식 유지

## Interfaces / 인터페이스

CLI:

```bash
vih admission-build <m10-package.json> > admission.json
vih admission-validate admission.json
```

Web:

```text
/admission
POST /api/admission/build
POST /api/admission/validate
```

Both are read-only with respect to `registry/` and `analyses/`.

두 경로 모두 `registry/`와 `analyses/`를 자동 변경하지 않는다.

## Tests / 테스트

`tests/test_admission.py` covers:

- deterministic admission bundle / 결정론적 bundle
- equity + venture lossless adapter routing / 두 모델 무손실 adapter 라우팅
- canonical-profile fail-closed behavior / 정식 프로파일 차단
- market evidence date derivation / 시장근거 기준일 도출
- temporary-repository `validate_case → run_case → evidence_view → preview_case → Web` E2E
- canonical evidence tamper detection / 정식 근거 변조 탐지
- legacy reference-case regression / 기존 사례 회귀
- CLI/Web shared admission service / CLI·Web 공통 서비스
- current canonical byte immutability / 현재 정식 bytes 불변

## Documentation / 문서

- `docs/PROMOTION_PROTOCOL.md`
- `docs/PROMOTION_PACKAGE.md`
- `docs/CANONICAL_ADMISSION.md`

## Grounding authority / 근거화 권위

1. merged `main` canonical files and decisions / 병합된 `main` 정식 파일·결정
2. `PROJECT_STATE.md` + active Issue/PR/branch / 상태파일 + 활성 Issue/PR/브랜치
3. evidence manifests and source packages / 근거 매니페스트·원천 패키지
4. current chat / 현재 대화
5. AI recollection / AI 기억

Repository state wins over AI recollection unless newer primary evidence requires explicit reconciliation.

더 최신 1차자료의 명시적 조정이 필요한 경우를 제외하고 저장소 상태가 AI 기억보다 우선한다.

## Exact resume point / 정확한 재개점

Complete M11 documentation, open the M11 PR, and run the full Python 3.11/3.12 CI matrix. Fix any service, adapter, Web, CLI, schema, or E2E regression from preserved diagnostics. Merge only if both reviewed adapters reproduce the exact M10 economics, temporary canonical admission works through the full read/preview/Web path, legacy cases remain unchanged, tampering fails closed, and admission builders never mutate current canonical files.

M11 문서를 완료하고 M11 PR을 개설한 뒤 Python 3.11/3.12 전체 CI를 실행한다. 보존 진단을 근거로 service·adapter·Web·CLI·schema·E2E 실패를 수정한다. 두 reviewed adapter가 M10 경제값을 정확히 재현하고 임시 정식 수용이 전체 read/preview/Web 경로에서 작동하며 기존 사례가 불변이고 변조가 fail-closed되며 admission builder가 현재 정식 파일을 변경하지 않을 때만 병합한다.
