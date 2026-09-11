# Project State / 프로젝트 상태

> Canonical human-and-AI handoff. Repository-grounded state outranks chat or AI recollection.  
> 인간·AI 공통 정식 인계 문서. 저장소 근거 상태는 채팅·AI 기억보다 우선한다.

## Repository / 저장소

- `Eckommon/Valuation-Intelligence-Hub`
- Purpose: cross-asset, evidence-grounded valuation intelligence / 범자산 근거 기반 가치분석 인텔리전스
- Documentation: English + Korean bilingual / 영한문 병기

## Completed canonical baseline / 완료 기준선

| Milestone | Main commit | Issue |
|---|---|---:|
| M1 Evidence grounding + normalization | `e3a11259c0e248f055ee16466e08ccfef2a4d13e` | #1 |
| M2 Scenario + reverse valuation | `2b6d7522e7d847673a7310b9e7f4346cd26cb59e` | #2 |
| M3 Reference cases | `5c39c6a1857a5b4aeffa9782399e24bcbd77c0ae` | #3 |
| M4 Registry + CLI | `db14a21bb706f4f3cd74f5a33d88ca5937249aa5` | #8 |
| M5 Web MVP | `5867363d26d4efa57e5fb92d4861de9bfbf00d7f` | #12 |
| M6 Interactive preview + evidence | `caf7576c1a2c13916449d445f5badc3a29712d36` | #14 |
| M7 Product UX | `243cea0233031088fac8edb0362971326840b858` | #16 |
| M8 User Draft | `899271709ef3c49d431e0fce716eff48d0b22370` | #18 |
| M9 Reviewed promotion | `3e2d0a58b13c6e90ae6e665db72dc2683d5fad3f` | #20 |
| M10 Promotion package | `951e6be93a2d98db3e71c7e9f77bc06b90516dd2` | #22 |
| M11 Reviewed-Draft canonical admission | `243f941b2f323ac5fdca31b86e13966950156114` | #24 |
| M12 Guarded admission apply | `a40e92c196c39b40172711f38f7231f5e8812d52` | #26 |
| M13 Immutable SEC live evidence | `372b8b0b26307730c3e91afea97c979b59906042` | #28 |

M13 post-merge `main` CI run `34574729338` completed `success` on Python 3.11/3.12.

## Canonical authority model / 정식 권위모델

```text
OFFICIAL / USER SOURCE
        ↓
IMMUTABLE SOURCE SNAPSHOT / NOT CANONICAL
        ↓
UNREVIEWED EVIDENCE CANDIDATE / NOT CANONICAL
        ↓
DRAFT + EVIDENCE GOVERNANCE
        ↓
HUMAN SHA-256 REVIEW LOCK
        ↓
DETERMINISTIC PROMOTION PACKAGE
        ↓
CANONICAL ADMISSION PROPOSAL
        ↓
BASELINE-BOUND REPOSITORY CHANGE PLAN
        ↓
GUARDED admission/* BRANCH APPLY
        ↓
PR + FULL CI + REVIEWED MERGE
        ↓
CANONICAL
```

Official-source provenance does not skip evidence review or repository admission.

공식출처라는 이유로 근거검토 또는 저장소 수용을 건너뛰지 않는다.

## Active mission / 활성 미션

- Issue: `#30 [M14] OpenDART immutable financial-statement source adapter`
- PR: `#31 M14 OpenDART immutable financial evidence`
- Branch: `mission/m14-opendart-live-evidence-v01`
- Status: `ACTIVE_FINALIZATION`
- Core CI run `34575135025`: Python 3.11/3.12 `success`
- Interface CI run `34575324786`: Python 3.11/3.12 `success`

## M14 scope / M14 범위

Adapter:

```text
opendart-fnltt-singl-acnt-all-v0.1
```

Endpoint identity:

```text
https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json
corp_code + bsns_year + reprt_code + fs_div
```

Authentication key `crtfc_key` is a transport-only secret. It must not appear in durable snapshots, sanitized locators, Web payloads, normal output, or evidence candidates.

`crtfc_key`는 transport 전용 secret이며 durable snapshot·sanitized locator·Web payload·일반 출력·근거후보에 남길 수 없다.

## M14 source snapshot / M14 source snapshot

- schema: `schemas/dart_source_snapshot.schema.json`
- version: `dart-source-snapshot-v0.1`
- status: `SOURCE_SNAPSHOT_CAPTURED`
- `canonical=false`
- exact raw UTF-8 OpenDART response
- raw-body size + SHA-256
- full snapshot SHA-256
- request identity reconciliation on every row
- OpenDART API `status=000` required even when HTTP is 200
- sanitized requested/final locator contains no credential

## M14 extraction / M14 추출

Initial metrics:

- revenue
- operating_income
- net_income
- assets
- cash
- equity
- liabilities

Selection uses explicit statement-section ordering and exact account-id/account-name fallback. No fuzzy matching.

```text
STATEMENT SECTION ORDER
→ EXACT ACCOUNT_ID ORDER
→ EXACT ACCOUNT_NM FALLBACK
→ EQUAL-PRECEDENCE VALUE RECONCILIATION
```

Controls:

- CFS/OFS isolated by request identity
- BS/IS/CIS/CF/SCE cannot be silently crossed
- conflicting equal-precedence values fail closed
- blank/`-` current amount stays unknown, never zero
- formatted integer amounts parse deterministically
- raw amount strings remain in row provenance
- `thstrm_add_amount` is preserved but NOT interpreted as TTM/YTD in M14

Output:

```text
DART_EVIDENCE_CANDIDATE_UNREVIEWED
FACT_CANDIDATE
canonical=false
```

## Interfaces / 인터페이스

CLI entry point now uses `valuation_hub.cli_entry:main` as a thin dispatcher. All existing commands delegate unchanged to the mature M1–M13 `valuation_hub.cli.main`; only M14 `dart-*` and extended Web serving are intercepted.

```bash
vih dart-fetch 00126380 --bsns-year 2026 --reprt-code 11012 --fs-div CFS --api-key <LOCAL_SECRET> --output workspace/source_snapshots/dart.json
vih dart-snapshot-validate workspace/source_snapshots/dart.json
vih dart-extract workspace/source_snapshots/dart.json revenue --statement-section IS
```

Web:

```text
/dart-source
POST /api/dart-source/validate
POST /api/dart-source/extract
```

Web has no API-key input and no OpenDART live-fetch endpoint.

## Tests / 테스트

- `tests/test_dart_live.py`
- `tests/test_dart_interfaces.py`
- deterministic fixture: `tests/fixtures/opendart_financials_sample.json`

CI is network-free and uses injected transport.

## Documentation / 문서

- `docs/LIVE_EVIDENCE_SEC.md`
- `docs/LIVE_EVIDENCE_OPENDART.md`
- `docs/M14_ACCEPTANCE.md`
- `docs/M14_IMPLEMENTATION_SUMMARY.md`

## Grounding authority / 근거화 권위

1. merged `main` files and decisions
2. `PROJECT_STATE.md` + active Issue/PR/branch
3. immutable source snapshots + exact extraction provenance
4. current chat
5. AI recollection

New external data must be reconciled through the evidence pipeline before changing canonical state.

새 외부 데이터는 정식상태를 변경하기 전에 근거 파이프라인에서 조정되어야 한다.

## Exact resume point / 정확한 재개점

Finalize PR #31 metadata and README documentation, run a fresh full Python 3.11/3.12 CI on the final PR head, and merge only if API-key non-persistence, OpenDART status handling, snapshot tamper detection, exact account/statement provenance, CLI/Web boundaries, SEC M13 behavior, and all M1–M14 regressions pass. After merge, verify `main` push CI and close #30. The next mission should address **financial evidence normalization**, not add more raw-source breadth: define deterministic period semantics (instant vs duration, quarter-only vs YTD, annual), source-priority reconciliation across SEC/OpenDART, and TTM transforms as `NORMALIZED_FACT`, without silently converting raw evidence into model assumptions.

PR #31 메타데이터와 README를 최종화하고 최종 head에서 Python 3.11/3.12 전체 CI를 실행한다. API key 비보존, OpenDART status 처리, snapshot 변조탐지, 계정·재무제표 provenance, CLI/Web 경계, SEC M13 회귀, 전체 M1–M14가 통과할 때만 병합한다. 병합 후 `main` CI와 #30 종료를 확인한다. 다음 미션은 source 폭을 늘리지 않고 **재무 evidence normalization**으로 이동한다. 즉 instant/duration, 분기단독/YTD/연간 기간 semantics, SEC/OpenDART source-priority reconciliation, TTM 변환을 `NORMALIZED_FACT`로 정의하고 raw evidence를 암묵적 가정으로 바꾸지 않는다.
