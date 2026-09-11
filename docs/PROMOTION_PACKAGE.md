# Promotion Package v0.1 / 승격 패키지 v0.1

## Purpose / 목적

M10 materializes a human-approved M9 candidate into deterministic review material without altering canonical repository state.

M10은 인간 승인된 M9 Candidate를 정식 저장소 상태 변경 없이 결정론적 검토 자료로 materialize합니다.

```text
REVIEW_APPROVED_READY_FOR_PR
        ↓
PROMOTION_PACKAGE_STAGED / NOT_CANONICAL
        ↓ package review + canonical-adapter implementation
SEPARATE GOVERNED PR
        ↓ full CI + human review + merge
CANONICAL
```

A staged package is **not** a canonical case. / 스테이징 패키지는 **정식 사례가 아닙니다**.

## Why M10 does not generate legacy `case_inputs.json` / 기존 정식 입력파일을 만들지 않는 이유

The M8 generic equity Draft contract stores forecast D&A, CAPEX, and ΔNWC as absolute values. The current M3 reference-equity contract instead reconstructs D&A/CAPEX from revenue ratios and ΔNWC from opening core NWC plus NWC-to-sales ratios.

M8 일반 equity Draft 계약은 전망 D&A·CAPEX·ΔNWC를 절대값으로 저장합니다. 반면 현재 M3 reference-equity 계약은 D&A·CAPEX를 매출비율에서, ΔNWC를 opening core NWC와 NWC-to-sales 비율에서 재구축합니다.

These representations are not losslessly interchangeable. M10 therefore preserves the reviewed Draft exactly and declares a required versioned canonical adapter rather than inventing missing economic structure.

두 표현은 손실 없이 상호변환되지 않습니다. 따라서 M10은 누락된 경제구조를 발명하지 않고 검토 Draft를 그대로 보존하며 필요한 버전 canonical adapter를 명시합니다.

## Package contents / 패키지 구성

A `promotion-package-v0.1` contains six deterministic artifacts:

1. `reviewed_candidate.json` — exact M9 approved candidate / M9 승인 Candidate 원문
2. `reviewed_case_payload.json` — identity + reviewed Draft + adapter requirement / 식별·검토 Draft·adapter 요구
3. `evidence_bundle.json` — input governance + evidence / 입력 거버넌스·근거
4. `staged_valuation_result.json` — valuation recomputed through shared Draft kernel / 공통 Draft 커널 재계산 결과
5. `REGISTRY_PROPOSAL.json` — blocked proposal metadata, **not** a registry entry / 차단된 제안 메타데이터
6. `REPORT.md` — deterministic bilingual review summary / 결정론적 영한문 검토 요약

Every artifact receives SHA-256, and the whole package has its own SHA-256.

모든 산출물에 SHA-256을 부여하고 전체 패키지에도 별도 SHA-256을 부여합니다.

## Compatibility state / 호환상태

Every M10 package declares:

```text
NOT_EXECUTABLE_UNTIL_CANONICAL_ADAPTER
```

Current adapter requirements:

- `equity_fcff` → `reviewed-draft-equity-fcff-v0.1`
- `venture_probability` → `reviewed-draft-venture-probability-v0.1`

`REGISTRY_PROPOSAL.json` always contains `registration_blocked = true`.

`REGISTRY_PROPOSAL.json`은 항상 `registration_blocked = true`를 유지합니다.

## Determinism / 결정론

Given the same:

- approved Candidate bytes/semantics / 승인 Candidate
- case ID / 사례 ID
- English/Korean names / 영문·국문 이름
- asset class / 자산분류

M10 produces the same artifact contents, artifact hashes, and package hash. No current timestamp or random identifier is inserted by the builder.

동일 입력에는 동일 산출물·산출물 해시·패키지 해시가 생성됩니다. Builder는 현재시각이나 임의 ID를 삽입하지 않습니다.

## Collision and path safety / 충돌·경로 안전

Case IDs must match:

```text
^[A-Z0-9][A-Z0-9_]{2,79}$
```

An ID already present in the canonical registry is rejected. M10 is intentionally a **new-case staging flow**; canonical updates require a separate governed design.

정식 레지스트리에 이미 존재하는 ID는 거부합니다. M10은 의도적으로 **신규 사례 스테이징 흐름**이며 기존 정식 사례 업데이트는 별도 거버넌스 설계가 필요합니다.

When materializing inside the repository, output is permitted only below:

저장소 내부 materialization 허용 위치:

```text
workspace/promotion_packages/
```

This directory is Git-ignored except for `.gitkeep`. External explicit output directories are also allowed. Canonical `analyses/` and `registry/` paths cannot be used as M10 output targets.

해당 디렉터리는 `.gitkeep`을 제외하고 Git에서 제외됩니다. 명시적인 저장소 외부 출력 디렉터리도 허용하지만, 정식 `analyses/`·`registry/` 경로는 M10 출력 대상으로 사용할 수 없습니다.

## CLI / CLI

Build package JSON without writing files:

파일 기록 없이 package JSON 생성:

```bash
vih package-build workspace/user_cases/my_candidate.json \
  --case-id KR_EXAMPLE_COMPANY \
  --name-en "Example Company" \
  --name-ko "예시회사" \
  --asset-class public_equity > workspace/user_cases/package.json
```

Materialize explicitly:

명시적 materialization:

```bash
vih package-build workspace/user_cases/my_candidate.json \
  --case-id KR_EXAMPLE_COMPANY \
  --name-en "Example Company" \
  --name-ko "예시회사" \
  --asset-class public_equity \
  --output-dir workspace/promotion_packages/KR_EXAMPLE_COMPANY
```

Validate embedded package JSON or a materialized directory:

```bash
vih package-validate workspace/user_cases/package.json
vih package-validate workspace/promotion_packages/KR_EXAMPLE_COMPANY
```

## Web / Web

`vih web` exposes `/package` and:

- `POST /api/package/build`
- `POST /api/package/validate`

The browser path is intentionally memory-only. It does not write server files.

브라우저 경로는 의도적으로 메모리 전용이며 서버 파일을 기록하지 않습니다.

## Integrity model / 무결성 모델

Validation checks:

- M9 human approval remains valid / M9 인간 승인 유효성
- review-scope hash still matches / 검토범위 해시 일치
- approved Candidate SHA-256 / 승인 Candidate SHA-256
- every artifact SHA-256 / 모든 산출물 SHA-256
- package SHA-256 / 전체 패키지 SHA-256
- reviewed Draft preservation / 검토 Draft 보존
- evidence/governance preservation / 근거·거버넌스 보존
- shared-kernel valuation reproduction / 공통커널 가치 재현
- blocked registry proposal / 레지스트리 제안 차단상태
- canonical ID collision / 정식 ID 충돌

The SHA-256 manifest is an integrity/determinism mechanism, not a digital signature. Trust still depends on retaining or reviewing the expected package hash through the governed PR process.

SHA-256 manifest는 무결성·결정론 장치이지 전자서명이 아닙니다. 신뢰는 거버넌스 PR 과정에서 기대 package hash를 보존·검토하는 절차에도 의존합니다.

## Next gate / 다음 게이트

M10 deliberately stops before canonical execution. The next mission should implement the versioned `reviewed-draft-*` canonical adapter and prove that a staged package can be admitted through a separate PR without changing its reviewed economics.

M10은 정식 실행 전에 의도적으로 멈춥니다. 다음 미션에서는 버전 `reviewed-draft-*` canonical adapter를 구현하고, 검토된 경제값을 변경하지 않은 채 별도 PR을 통해 staged package를 수용할 수 있음을 증명해야 합니다.
