# Reviewed-Draft Canonical Admission / 검토 Draft 정식 수용

## Purpose / 목적

M11 closes the gap between a human-reviewed M10 promotion package and an executable canonical case **without coercing reviewed economics into the legacy reference-case shape**.

M11은 인간 검토된 M10 승격 패키지와 실행 가능한 정식 사례 사이의 간극을 연결하되, **검토된 경제값을 기존 reference-case 구조로 억지 변환하지 않습니다.**

## State machine / 상태기계

```text
DRAFT_USER_SUPPLIED
        ↓ M9 evidence governance + human SHA-256 review
REVIEW_APPROVED_READY_FOR_PR
        ↓ M10 deterministic staging
PROMOTION_PACKAGE_STAGED / NOT_CANONICAL
        ↓ M11 deterministic admission planning
CANONICAL_ADMISSION_PROPOSED / BUNDLE canonical=false
        ↓ exact repository PR + full CI + human review + merge
CANONICAL
```

The admission bundle itself is always `canonical=false`. Its proposed files contain `canonical=true` because they are the exact bytes intended for a canonical PR; that flag has no repository authority until the exact artifacts are merged.

수용 bundle 자체는 항상 `canonical=false`입니다. 내부 제안 파일은 정식 PR에 들어갈 정확한 산출물이므로 `canonical=true`를 포함하지만, 해당 산출물이 정확히 병합되기 전에는 저장소 정식 권위를 갖지 않습니다.

## Versioned adapters / 버전 Adapter

M11 introduces two explicit adapters:

- `reviewed-draft-equity-fcff-v0.1`
- `reviewed-draft-venture-probability-v0.1`

Registry entries without `adapter` continue to use the legacy M3 reference-case route. Existing LS ELECTRIC, LS Eco Energy, and Jet.AI cases are therefore unchanged.

`adapter`가 없는 registry 항목은 기존 M3 reference-case 경로를 계속 사용합니다. 따라서 기존 LS ELECTRIC, LS에코에너지, Jet.AI 사례는 변경되지 않습니다.

## Lossless economics / 경제값 무손실 원칙

Reviewed equity Drafts retain absolute forecast fields:

- revenue / 매출
- EBIT margin / EBIT 마진
- tax rate / 세율
- depreciation & amortization / 감가상각
- CAPEX / 자본적지출
- ΔNWC / 운전자본 증감

The canonical adapter does **not** reverse-engineer these values into the legacy opening-NWC and revenue-ratio representation. It routes the exact reviewed Draft through the shared FCFF kernel and only normalizes the external service runtime shape.

정식 adapter는 이 값을 기존 opening-NWC 및 매출비율 표현으로 역산하지 않습니다. 정확한 검토 Draft를 공통 FCFF 커널로 전달하고 외부 서비스 runtime 형태만 정규화합니다.

## Canonical compatibility profile v0.1 / 정식 호환 프로파일 v0.1

Generic Drafts may use arbitrary valid scenario names. M11 admission v0.1 is intentionally narrower because existing product UI contracts require stable scenario names.

일반 Draft는 유효한 임의 시나리오 이름을 사용할 수 있습니다. 다만 기존 제품 UI 계약을 유지하기 위해 M11 정식 수용 v0.1은 더 엄격합니다.

- equity: exactly `BEAR`, `BASE`, `BULL`
- venture: exactly `FAILURE`, `SURVIVAL`, `BREAKOUT`

A Draft can therefore be valid in M8 and stage successfully in M10 while still failing M11 canonical admission. This is intentional fail-closed behavior, not data loss.

따라서 M8에서 유효하고 M10 스테이징까지 성공한 Draft가 M11 정식 수용에서 차단될 수 있습니다. 이는 데이터 손실이 아니라 의도된 fail-closed 동작입니다.

## Admission artifacts / 수용 산출물

A deterministic M11 bundle proposes:

1. `SOURCE_PACKAGE.json` — exact M10 package / 정확한 M10 패키지
2. `case_inputs.json` — exact embedded reviewed Draft + provenance / 검토 Draft 원문 + 출처
3. `evidence_manifest.json` — admission gate + source hashes / 수용 게이트 + 원천 해시
4. `evidence_reviewed.json` — exact approved evidence and input governance / 승인 근거·입력거버넌스 원문
5. `valuation_result.json` — shared-kernel runtime / 공통커널 runtime
6. `REPORT.md` — bilingual admission report / 영한문 수용 보고서
7. proposed registry entry with explicit `adapter` / 명시적 adapter registry 제안

The bundle and every embedded artifact are SHA-256 locked.

bundle과 모든 내장 산출물은 SHA-256으로 잠깁니다.

## Valuation date / 가치평가 기준일

`valuation_as_of` is not user-entered during M11. It is derived from the governed `market_price` evidence `as_of` date. Missing, malformed, or conflicting dates fail closed.

`valuation_as_of`는 M11에서 임의 입력하지 않습니다. 거버넌스된 `market_price` 근거의 `as_of` 날짜에서 도출하며 누락·형식오류·충돌은 차단합니다.

## Runtime provenance validation / Runtime 출처 검증

An admitted reviewed case must prove the following chain on every canonical validation:

```text
SOURCE_PACKAGE.json
  → approved Candidate SHA-256
  → human review-scope SHA-256
  → exact reviewed_draft
  → exact evidence + input_governance
  → versioned adapter/model match
  → shared kernel recomputation
  → stored canonical runtime match
```

Any break in this chain blocks `validate_case()` and therefore blocks the Web/API/CLI read path.

이 체인 중 하나라도 불일치하면 `validate_case()`가 차단되고 결과적으로 Web/API/CLI 읽기 경로도 차단됩니다.

## Preview behavior / Preview 동작

Preview remains `PREVIEW_NOT_CANONICAL` for both legacy and reviewed cases.

For reviewed equity cases, revenue scaling preserves the reviewed D&A/CAPEX/ΔNWC economics proportionally rather than converting them into legacy case inputs. Margin/WACC/terminal-growth overrides are applied only in memory.

검토 equity 사례의 preview는 D&A/CAPEX/ΔNWC를 기존 입력포맷으로 변환하지 않고 검토된 경제관계를 비례 유지합니다. 마진·WACC·영구성장률 변경 역시 메모리에서만 수행됩니다.

## CLI / CLI

```bash
vih admission-build workspace/user_cases/package.json > workspace/user_cases/admission.json
vih admission-validate workspace/user_cases/admission.json
```

These commands do not mutate `registry/cases.json` or `analyses/`.

이 명령은 `registry/cases.json` 또는 `analyses/`를 변경하지 않습니다.

## Web / Web

```text
/admission
POST /api/admission/build
POST /api/admission/validate
```

The Web admission path is memory-only. There is no endpoint that writes canonical files or merges a PR.

Web 정식 수용 경로는 메모리 전용이며 정식 파일을 기록하거나 PR을 병합하는 endpoint는 존재하지 않습니다.

## Canonicalization rule / 정식화 규칙

M11 prepares and validates canonical admission material; it does not grant repository authority. The only canonicalizing event remains a separately reviewed repository merge whose exact files pass the full test matrix.

M11은 정식 수용 자료를 생성·검증할 뿐 저장소 권위를 부여하지 않습니다. 전체 테스트를 통과한 정확한 파일이 별도 인간 검토 PR을 통해 병합되는 사건만이 정식화 이벤트입니다.
