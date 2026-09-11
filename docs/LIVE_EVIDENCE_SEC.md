# Immutable SEC Live Evidence / 불변 SEC Live 근거

## Purpose / 목적

M13 introduces the first production live-evidence acquisition adapter without changing the authority model established by M9–M12.

M13은 M9–M12에서 확립한 권위모델을 변경하지 않고 첫 production live-evidence 수집 adapter를 도입한다.

Official SEC data is **source material**, not automatic canonical truth. Every live response first becomes a hash-locked noncanonical snapshot, and every extracted fact remains an unreviewed evidence candidate until it passes the existing governance/review pipeline.

SEC 공식 데이터도 자동으로 정식 사실이 되지 않는다. 모든 live 응답은 먼저 해시 잠금된 비정식 snapshot이 되며, 추출 fact는 기존 거버넌스·검토 파이프라인을 통과하기 전까지 미검토 근거후보로 유지된다.

```text
LIVE SEC COMPANYFACTS
        ↓
SOURCE_SNAPSHOT_CAPTURED / NOT_CANONICAL
        ↓ exact raw UTF-8 body + SHA-256
EVIDENCE_CANDIDATE_UNREVIEWED / NOT_CANONICAL
        ↓ existing M9–M12 review/promotion pipeline
CANONICAL only after governed review + repository admission
```

## Source adapter / 소스 adapter

Adapter: `sec-companyfacts-v0.1`

Endpoint pattern:

```text
https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json
```

The adapter constructs this locator from a normalized ten-digit CIK. Arbitrary user-supplied network URLs are not accepted by the live fetch path.

Adapter가 10자리 정규화 CIK에서 locator를 직접 구성한다. live fetch 경로는 임의 사용자 URL을 받지 않는다.

## Transport boundary / 전송 경계

The default transport enforces:

- HTTPS only / HTTPS 전용
- initial host `data.sec.gov` / 최초 host 고정
- redirects only to approved SEC hosts / redirect SEC host 제한
- identifying User-Agent with contact email / 연락 이메일 포함 식별 User-Agent
- conservative process-local rate limiter of at least 0.1 seconds between requests / 프로세스 로컬 보수적 rate 제한
- bounded timeout / timeout 제한
- bounded response bytes / 응답크기 제한
- JSON content type / JSON content-type
- strict UTF-8 decode / 엄격 UTF-8
- HTTP/network failures fail closed / HTTP·네트워크 오류 fail-closed

The User-Agent itself is never persisted into the snapshot. The snapshot records only `user_agent_provided=true`.

User-Agent 문자열은 snapshot에 저장하지 않고 `user_agent_provided=true`만 기록한다.

## Snapshot contract / Snapshot 계약

Schema: `schemas/source_snapshot.schema.json`

Required properties include:

- `schema_version=source-snapshot-v0.1`
- `status=SOURCE_SNAPSHOT_CAPTURED`
- `canonical=false`
- `adapter=sec-companyfacts-v0.1`
- publisher/source type/tier
- requested and final locator
- normalized CIK
- fetched timestamp
- content type, ETag, Last-Modified where supplied
- exact raw UTF-8 text
- raw-body byte length + SHA-256
- full snapshot SHA-256

Validation reparses the raw JSON, reconciles requested CIK with payload CIK, rechecks body bytes/hash, and reconstructs the full snapshot digest. Metadata or raw-body mutation invalidates the snapshot.

검증 시 raw JSON을 다시 파싱하고 요청 CIK와 payload CIK를 대조하며 body bytes/hash와 전체 snapshot digest를 재구성한다. 메타데이터나 원문 변경은 snapshot을 무효화한다.

## Evidence extraction / 근거 추출

Initial metric registry:

- `revenue`
- `operating_income`
- `net_income`
- `assets`
- `cash`
- `shares_outstanding`

Each metric has an explicit ordered taxonomy/concept fallback list, accepted units, and accepted filing forms. Fallback is visible through `concept_fallback_index` and `concept_fallback_used`.

각 metric은 명시적인 taxonomy/concept 우선순위, 허용 unit, 허용 filing form을 가진다. fallback 사용 여부는 결과에 그대로 노출된다.

Selection rule v0.1:

```text
FIRST_AVAILABLE_CONCEPT
→ LATEST_FILED
→ LATEST_PERIOD_END
```

Optional `form` and `period_end` filters may narrow the selection. If equal-precedence facts have conflicting values, extraction fails closed rather than choosing arbitrarily. Equal-precedence duplicate representations with the same value are allowed and resolved deterministically.

동일 우선순위 fact 값이 충돌하면 임의 선택하지 않고 fail-closed한다. 동일 값의 중복 표현은 결정론적으로 정리할 수 있다.

M13 intentionally does **not** synthesize TTM, normalize discontinued operations, combine quarters, or map extracted values directly into a Draft/Candidate.

M13은 TTM 합성, 중단사업 정규화, 분기 결합, Draft/Candidate 자동 연결을 수행하지 않는다.

## CLI / CLI

Live fetch is explicit local CLI work:

```bash
vih sec-fetch 0000320193 \
  --user-agent "Valuation-Intelligence-Hub contact@example.com" \
  --output workspace/source_snapshots/AAPL-companyfacts.json
```

Validate an existing snapshot:

```bash
vih sec-snapshot-validate workspace/source_snapshots/AAPL-companyfacts.json
```

Extract one unreviewed candidate:

```bash
vih sec-extract workspace/source_snapshots/AAPL-companyfacts.json revenue
vih sec-extract workspace/source_snapshots/AAPL-companyfacts.json revenue --form 10-Q --period-end 2026-06-27
```

Snapshot materialization is restricted to `workspace/source_snapshots/` and refuses overwrite.

snapshot materialization은 `workspace/source_snapshots/` 아래로 제한하며 기존 파일 overwrite를 거부한다.

## Web / Web

The Web product exposes `/source` only as a **snapshot inspector**:

- validate a pasted snapshot
- extract an unreviewed evidence candidate

There is no browser-origin live-fetch endpoint and no canonical-write endpoint in M13.

Web은 snapshot 검증·근거후보 추출만 제공한다. 브라우저 live fetch 및 정식 write endpoint는 없다.

## Testing / 테스트

CI is network-free. Tests inject fixture transport responses and verify:

- deterministic CIK/locator construction
- User-Agent non-persistence
- rate limiting
- host/content-type/identity failures
- raw-body and snapshot tamper detection
- exact filing provenance
- visible concept fallback
- equal-precedence conflict failure
- workspace-only no-overwrite materialization
- CLI and Web read-only interfaces
- absence of browser live-fetch routes
- all M1–M12 regressions

## Next boundary / 다음 경계

The next source adapter should reuse the same source-snapshot and candidate authority model rather than creating a separate evidence truth path. For Korean public-company data, the natural next adapter is DART/OpenDART with its own authentication, filing identity, taxonomy/account mapping, and rate-limit contract.

다음 소스 adapter도 별도 진실경로를 만들지 않고 동일 source-snapshot·candidate 권위모델을 재사용해야 한다. 한국 상장사 데이터의 자연스러운 다음 adapter는 인증·공시식별·계정매핑·rate-limit 계약을 가진 DART/OpenDART이다.
