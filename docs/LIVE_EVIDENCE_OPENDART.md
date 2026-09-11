# OpenDART Immutable Financial Evidence / OpenDART 불변 재무 근거

## Purpose / 목적

M14 adds Korea FSS OpenDART as the second production live-evidence source while preserving the authority model established by M13.

M14는 한국 금융감독원 OpenDART를 두 번째 production live-evidence source로 추가하면서 M13의 권위모델을 그대로 유지한다.

```text
LIVE OPENDART
      ↓
SOURCE_SNAPSHOT_CAPTURED / NOT_CANONICAL
      ↓ exact raw response + hash lock
DART_EVIDENCE_CANDIDATE_UNREVIEWED / NOT_CANONICAL
      ↓ existing evidence governance + human review
M9–M12 promotion/admission
      ↓ reviewed repository merge
CANONICAL
```

Official origin does not itself grant canonical authority.

공식 출처라는 이유만으로 정식 권위를 부여하지 않는다.

## Adapter / Adapter

`opendart-fnltt-singl-acnt-all-v0.1`

Endpoint:

```text
GET https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json
```

Request identity:

- `corp_code` — 8-digit DART corporation code
- `bsns_year` — 4-digit fiscal year
- `reprt_code` — `11013` 1Q, `11012` half-year, `11014` 3Q, `11011` annual
- `fs_div` — `CFS` or `OFS`
- `crtfc_key` — authentication credential used only inside transport

## Secret boundary / 비밀정보 경계

The API key is never part of the persistent source identity.

API key는 영속 source identity의 일부가 아니다.

The live transport receives the key only to construct the actual request. Everything leaving the transport uses a sanitized locator containing only `corp_code`, `bsns_year`, `reprt_code`, and `fs_div`.

실제 HTTP 요청 생성 시에만 key를 사용하며 transport 밖으로 나오는 locator에는 `corp_code`, `bsns_year`, `reprt_code`, `fs_div`만 남긴다.

The adapter fails closed if key material is detected in the snapshot. Web surfaces do not accept API keys at all.

snapshot에 key material이 감지되면 fail-closed하며 Web은 API key 자체를 입력받지 않는다.

## Snapshot contract / Snapshot 계약

Schema: `schemas/dart_source_snapshot.schema.json`

State:

```text
dart-source-snapshot-v0.1
SOURCE_SNAPSHOT_CAPTURED
canonical=false
```

Snapshot records:

- adapter/source/publisher/Tier A proposal
- sanitized requested + final locator
- request identity fields
- fetched timestamp
- content type, ETag, Last-Modified when present
- exact raw UTF-8 JSON body
- raw-body byte size + SHA-256
- full snapshot SHA-256

Validation reparses the raw payload, requires OpenDART API `status=000`, verifies request identity on every row where the fields are present, and reconstructs all hashes.

검증 시 raw payload를 다시 파싱하고 OpenDART API `status=000`을 요구하며 각 row의 요청식별 필드를 대조하고 모든 해시를 재계산한다.

HTTP 200 alone is not success: OpenDART API-level error statuses fail closed.

HTTP 200만으로 성공으로 간주하지 않으며 OpenDART API status 오류는 차단한다.

## Metric extraction / 지표 추출

Initial metrics:

- `revenue`
- `operating_income`
- `net_income`
- `assets`
- `cash`
- `equity`
- `liabilities`

Each metric declares:

- allowed ordered statement sections
- ordered exact `account_id` matches
- ordered exact `account_nm` fallbacks

There is no fuzzy account-name matching.

계정명 fuzzy matching은 사용하지 않는다.

Selection is deterministic:

```text
STATEMENT SECTION ORDER
→ EXACT ACCOUNT_ID ORDER
→ EXACT ACCOUNT_NM FALLBACK ORDER
→ equal-precedence value reconciliation
```

The output exposes whether account-name fallback was used and which fallback index won.

결과에는 account-name fallback 사용 여부와 index를 명시한다.

### Statement isolation / 재무제표 구분 격리

- balance-sheet metrics are selected from `BS`
- income metrics use explicit `IS`/`CIS` ordering
- a cash-flow (`CF`) row cannot silently satisfy an income-statement metric
- `CFS` and `OFS` are isolated by snapshot request identity

### Amount parsing / 금액 파싱

`thstrm_amount` is parsed deterministically from formatted integer text such as `1,234` or `(1,234)`.

- raw text remains preserved in row provenance
- parsed integer becomes candidate `value`
- blank or `-` remains unknown, not zero
- non-integer malformed text fails closed

M14 does **not** reinterpret `thstrm_add_amount` as TTM, quarter-only, or YTD. It is preserved as provenance only.

M14는 `thstrm_add_amount`를 TTM·분기단독·누계로 자동 재해석하지 않고 출처정보로만 보존한다.

## Candidate provenance / 후보 출처정보

Where available, the candidate preserves:

- `rcept_no`
- `reprt_code`
- `bsns_year`
- `corp_code`, `stock_code`
- `fs_div`, `fs_nm`
- `sj_div`, `sj_nm`
- `account_id`, `account_nm`, `account_detail`
- current/prior-period names and amounts
- `ord`
- `currency`
- snapshot SHA-256 + body SHA-256

Output remains:

```text
DART_EVIDENCE_CANDIDATE_UNREVIEWED
FACT_CANDIDATE
canonical=false
```

## CLI / CLI

```bash
vih dart-fetch 00126380 \
  --bsns-year 2026 \
  --reprt-code 11012 \
  --fs-div CFS \
  --api-key <LOCAL_SECRET> \
  --output workspace/source_snapshots/dart-00126380-2026-h1.json

vih dart-snapshot-validate workspace/source_snapshots/dart-00126380-2026-h1.json
vih dart-extract workspace/source_snapshots/dart-00126380-2026-h1.json revenue --statement-section IS
```

Snapshot materialization is restricted to `workspace/source_snapshots/` and refuses overwrite.

## Web / Web

```text
/dart-source
POST /api/dart-source/validate
POST /api/dart-source/extract
```

There is no Web API-key field and no browser-origin OpenDART live-fetch endpoint.

Web에는 API key 입력필드와 browser-origin OpenDART live fetch endpoint가 없다.

## M14 non-goals / M14 비목표

- corpCode ZIP/XML acquisition
- stock-code → corp-code discovery
- TTM synthesis
- quarter/YTD normalization
- automatic Draft/Candidate binding
- canonical evidence write

These require separate governed missions.

위 기능은 별도 거버넌스 미션으로 분리한다.
