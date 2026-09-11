# Project State / 프로젝트 상태

> Canonical human-and-AI handoff. Repository-grounded state outranks chat or AI recollection.  
> 인간·AI 공통 정식 인계 문서. 저장소 근거 상태는 채팅·AI 기억보다 우선한다.

## Repository identity / 저장소 식별

- Repository: `Eckommon/Valuation-Intelligence-Hub`
- Purpose: cross-asset, evidence-grounded valuation intelligence system / 범자산 근거 기반 가치분석 인텔리전스 시스템
- Product strategy: Web-first hybrid, one shared valuation/evidence kernel / 웹 우선 하이브리드, 단일 공통 가치·근거 커널
- Documentation: English + Korean bilingual / 영한문 병기

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
- M11 Reviewed-Draft canonical adapter + admission: `243f941b2f323ac5fdca31b86e13966950156114` — #24 `COMPLETED`
- M12 Guarded admission applicator + PR-ready plan: `a40e92c196c39b40172711f38f7231f5e8812d52` — #26 `COMPLETED`

M12 post-merge `main` CI run `34568371340` completed `success` on Python 3.11/3.12.

M12 병합 후 `main` CI run `34568371340`은 Python 3.11/3.12에서 `success` 완료했다.

## Canonical product capability / 정식 제품 기능

The merged M1–M12 product provides:

- three regression-locked reference cases / 3개 회귀 잠금 기준 사례
- shared FCFF + venture-probability kernels / 공통 FCFF + 벤처 확률가중 커널
- versioned registry, CLI, local Web UI, evidence browser, scenario preview / 버전 레지스트리·CLI·Web·근거탐색·preview
- user Draft → governed Candidate → human review → deterministic package / Draft→Candidate→인간검토→패키지
- versioned reviewed-Draft canonical admission / 버전 검토 Draft 정식 수용
- deterministic repository change planning / 결정론적 저장소 변경계획
- guarded `admission/*` branch/worktree apply with baseline locking, exact bytes, post-apply validation and rollback / 안전 브랜치 적용

The canonical authority boundary remains repository PR + CI + reviewed merge.

정식 권위의 최종 경계는 저장소 PR + CI + 검토 병합이다.

## Active mission / 활성 미션

- Issue: `#28 [M13] Immutable live evidence acquisition + SEC CompanyFacts adapter / 불변 live 근거수집 + SEC CompanyFacts adapter`
- Branch: `mission/m13-sec-live-evidence-v01`
- Status: `ACTIVE_IMPLEMENTATION`

## M13 objective / M13 목표

Introduce the first production live-source acquisition layer while preserving the M9–M12 rule that source acquisition, evidence review, and canonical authority are different states.

첫 production live-source 수집계층을 도입하되 source 수집·근거 검토·정식 권위가 서로 다른 상태라는 M9–M12 원칙을 유지한다.

```text
LIVE OFFICIAL SOURCE
        ↓
SOURCE_SNAPSHOT_CAPTURED / NOT_CANONICAL
        ↓
EVIDENCE_CANDIDATE_UNREVIEWED / NOT_CANONICAL
        ↓ explicit governance/review
existing M9–M12 promotion/admission path
        ↓
CANONICAL only after reviewed repository merge
```

## First production source / 첫 production 소스

Adapter:

```text
sec-companyfacts-v0.1
```

Official endpoint pattern:

```text
https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json
```

The adapter constructs the endpoint from a normalized ten-digit CIK. Arbitrary user-supplied live URLs are not accepted.

Adapter가 정규화 10자리 CIK에서 endpoint를 직접 구성하며 임의 사용자 live URL은 받지 않는다.

## Transport controls / 전송 통제

`src/valuation_hub/sec_live.py` enforces:

- HTTPS only / HTTPS 전용
- initial host fixed to `data.sec.gov`
- redirects restricted to approved SEC hosts / redirect host 제한
- identifying User-Agent containing contact email / 연락 이메일 포함 User-Agent
- process-local conservative rate limiter (`>=0.1s` request interval) / 보수적 rate limiter
- timeout and maximum response bytes / timeout·응답크기 제한
- HTTP/content-type/UTF-8/JSON failures fail closed / 응답 오류 차단
- injectable transport for deterministic offline tests / CI용 transport 주입

The User-Agent string is not persisted into source snapshots.

User-Agent 문자열은 source snapshot에 저장하지 않는다.

## Immutable source snapshot / 불변 source snapshot

Schema:

- `schemas/source_snapshot.schema.json`
- version `source-snapshot-v0.1`
- state `SOURCE_SNAPSHOT_CAPTURED`
- `canonical=false`

Snapshot content includes:

- publisher, source type, source tier
- requested/final locator
- requested normalized CIK
- fetched timestamp
- response content type, ETag, Last-Modified when present
- exact raw UTF-8 response text
- raw body byte count + SHA-256
- full snapshot SHA-256

`validate_source_snapshot()` reparses raw JSON, checks payload CIK identity, rechecks body size/hash, and reconstructs the full snapshot digest. Any metadata/raw-body tamper fails closed.

`validate_source_snapshot()`은 raw JSON 재파싱, payload CIK 대조, body size/hash, 전체 snapshot digest를 재검증한다. 메타데이터·원문 변경은 fail-closed한다.

## SEC evidence extraction / SEC 근거추출

Initial metrics:

- `revenue`
- `operating_income`
- `net_income`
- `assets`
- `cash`
- `shares_outstanding`

Each `MetricSpec` explicitly defines ordered taxonomy/concept fallback, accepted units, and filing forms.

Selection rule:

```text
FIRST_AVAILABLE_CONCEPT
→ LATEST_FILED
→ LATEST_PERIOD_END
```

Optional `form` and `period_end` filters are explicit. Equal-precedence facts with conflicting values fail closed. Same-value duplicates are resolved deterministically. Concept fallback is recorded in the output and is never silent.

동일 우선순위 값이 충돌하면 차단하며 동일값 중복은 결정론적으로 처리한다. Concept fallback은 결과에 명시한다.

Each extracted candidate preserves:

- taxonomy + concept + unit
- value
- reporting start/end + FY/FP/frame
- accession + form + filed date
- source snapshot SHA-256 + body SHA-256
- explicit selection rule/filter metadata

Output state:

```text
EVIDENCE_CANDIDATE_UNREVIEWED / canonical=false / FACT_CANDIDATE
```

M13 does not synthesize TTM, normalize financial statements, or automatically bind a candidate into a Draft/Candidate review object.

M13은 TTM 합성, 재무제표 정규화, Draft/Candidate 자동 연결을 수행하지 않는다.

## Interfaces / 인터페이스

CLI:

```bash
vih sec-fetch <CIK> --user-agent "App contact@example.com" --output workspace/source_snapshots/<file>.json
vih sec-snapshot-validate workspace/source_snapshots/<file>.json
vih sec-extract workspace/source_snapshots/<file>.json <metric> [--form ...] [--period-end YYYY-MM-DD]
```

Snapshot materialization is restricted to `workspace/source_snapshots/` and refuses overwrite.

Web:

```text
/source
POST /api/source/validate
POST /api/source/extract
```

There is deliberately no browser-origin live-fetch endpoint and no canonical-write endpoint.

브라우저 live fetch와 정식 write endpoint는 의도적으로 존재하지 않는다.

## Tests / 테스트

M13 currently includes:

- `tests/fixtures/sec_companyfacts_sample.json`
- `tests/test_sec_live.py`
- `tests/test_sec_interfaces.py`

Coverage includes:

- CIK normalization + official locator construction
- immutable hash-locked snapshot capture
- User-Agent non-persistence
- source host/content-type/payload identity failures
- raw-body tamper detection
- explicit metric fallback
- exact filing provenance
- form/period filters
- equal-precedence conflict fail-closed behavior
- deterministic same-value duplicates
- conservative rate limiter
- workspace-only no-overwrite materialization
- CLI commands
- Web source inspection and absence of browser live-fetch route
- M1–M12 regressions through full CI

CI uses injected/fixture responses and does not make external SEC requests.

## Documentation / 문서

- `docs/EVIDENCE_POLICY.md`
- `docs/LIVE_EVIDENCE_SEC.md`
- `schemas/source_snapshot.schema.json`

## Grounding authority / 근거화 권위

1. merged `main` canonical files and decisions / 병합 `main` 정식 파일·결정
2. `PROJECT_STATE.md` + active Issue/PR/branch / 상태파일 + 활성 Issue·PR·브랜치
3. immutable source snapshots + extraction provenance / 불변 source snapshot + 추출출처
4. current chat / 현재 대화
5. AI recollection / AI 기억

Official external data does not outrank the repository merely by being fetched; it must be explicitly reconciled through the evidence pipeline before changing canonical state.

공식 외부 데이터도 단순히 fetch되었다는 이유로 저장소 정식상태를 덮지 않으며 근거 파이프라인에서 명시적으로 조정되어야 한다.

## Exact resume point / 정확한 재개점

Open the M13 PR and run the full Python 3.11/3.12 CI matrix. Fix any snapshot, transport, extraction, CLI, Web, or regression failure using preserved diagnostics. Merge only if source capture remains noncanonical, all snapshot hashes and CIK provenance revalidate, ambiguous facts fail closed, browser live fetch remains absent, and all M1–M13 tests pass. After M13 merge, verify the `main` push CI and close #28. The next mission should add the Korean official-data source using the same authority model: OpenDART adapter + authentication-safe immutable snapshot capture, without yet conflating it with TTM/normalization.

M13 PR을 개설하고 Python 3.11/3.12 전체 CI를 실행한다. snapshot·transport·추출·CLI·Web·회귀 실패를 보존 진단으로 수정한다. 비정식 수집상태, 해시·CIK 출처 재검증, 충돌 fail-closed, browser live fetch 부재, M1–M13 전체 테스트가 통과할 때만 병합한다. 병합 후 `main` push CI와 #28 종료를 확인한다. 다음 미션은 동일 권위모델을 재사용하여 OpenDART adapter와 인증 안전 immutable snapshot 수집을 구현하되 TTM/정규화와는 아직 분리한다.
