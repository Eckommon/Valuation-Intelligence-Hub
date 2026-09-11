# Promotion Protocol v0.1 / 승격 프로토콜 v0.1

## Purpose / 목적

M9 defines the controlled path from user-supplied valuation work to a repository-reviewable candidate. It does **not** make a candidate canonical by itself.

M9은 사용자 제공 가치평가를 저장소 검토 가능한 Candidate로 전환하는 통제 경로를 정의합니다. Candidate를 자체적으로 정식 상태로 만들지는 않습니다.

```text
DRAFT_USER_SUPPLIED
        │
        ▼
CANDIDATE_REVIEW
        │  evidence + input governance complete
        ▼
HUMAN REVIEW + SHA-256 SCOPE LOCK
        │
        ▼
REVIEW_APPROVED_READY_FOR_PR
        │  separate repository PR + CI + review + merge
        ▼
CANONICAL
```

`CANONICAL` is outside the M9 service boundary. / `CANONICAL`은 M9 서비스 경계 밖의 상태입니다.

## Why this exists / 필요한 이유

A valuation can calculate correctly while its inputs are unsupported, stale, misclassified, or silently assumed. M9 therefore separates mathematical executability from evidence admissibility and from human approval.

가치평가 계산이 수학적으로 정상이어도 입력이 무근거·노후·오분류·암묵 가정일 수 있습니다. M9은 계산 가능성, 근거 적격성, 인간 승인을 서로 분리합니다.

## Candidate contract / Candidate 계약

Schema / 스키마:

- `schemas/promotion_candidate.schema.json`
- `schema_version = promotion-candidate-v0.1`
- `status = CANDIDATE_REVIEW`
- `canonical = false`

A candidate contains four controlled areas:

Candidate는 네 개의 통제 영역으로 구성됩니다.

1. `draft` — validated M8 Draft / 검증된 M8 Draft
2. `input_governance` — classification of every material numeric model input / 모든 중요 숫자 모델입력 분류
3. `evidence` — provenance records linked to factual inputs / 사실 입력에 연결된 출처 레코드
4. `review` — explicit human decision and review-scope hash / 명시적 인간 검토 결정·범위 해시

## Material-input enumeration / 중요입력 전수열거

`candidate-build` validates and normalizes a Draft, then deterministically enumerates every material numeric model input. Forecast `year` labels are structural and excluded; economic values are included.

`candidate-build`는 Draft를 검증·정규화한 뒤 모든 중요 숫자 모델입력을 결정론적으로 전수열거합니다. 전망 `year` 표시는 구조값이므로 제외하고 경제적 값은 포함합니다.

Every generated binding begins as:

모든 생성 binding의 최초 상태:

```json
{"path":"...","class":"UNKNOWN","claim_ids":[],"rationale":""}
```

`UNKNOWN` can never pass the review gate. / `UNKNOWN`은 검토게이트를 통과할 수 없습니다.

## Input classes / 입력 분류

Promotion candidates permit only:

승격 Candidate의 모델입력 분류는 다음만 허용합니다.

- `FACT`
- `NORMALIZED_FACT`
- `ASSUMPTION`

`FACT` and `NORMALIZED_FACT` require linked evidence. The linked evidence class must match the binding class, and its numeric `value` must reconcile with the model input.

`FACT`와 `NORMALIZED_FACT`는 연결 근거가 필수입니다. 연결 근거의 class는 binding class와 일치해야 하고 숫자 `value`도 모델입력과 조정되어야 합니다.

`ASSUMPTION` requires a non-empty rationale. / `ASSUMPTION`은 비어 있지 않은 rationale이 필요합니다.

## Mandatory observed facts / 필수 관측 사실

Some inputs cannot be downgraded to assumptions simply to avoid evidence requirements.

일부 입력은 근거 요구를 회피하기 위해 가정으로 낮출 수 없습니다.

For `equity_fcff` / `equity_fcff`:

- `market_price`
- `equity.diluted_shares`
- `equity.debt`
- `equity.cash`
- `equity.minority_interest`

For `venture_probability` / `venture_probability`:

- `market_price`

These paths must be `FACT` or `NORMALIZED_FACT`. / 이 경로는 반드시 `FACT` 또는 `NORMALIZED_FACT`여야 합니다.

## Evidence gate reuse / 근거게이트 재사용

M9 reuses `valuation_hub.evidence.evaluate_canonical_promotion`. The candidate therefore fails closed on conditions including:

M9은 기존 `evaluate_canonical_promotion`을 재사용하므로 다음 조건 등을 fail-closed합니다.

- no material evidence / 중요 근거 없음
- `UNKNOWN` claim / UNKNOWN 주장
- `UNKNOWN_CONFLICT` / 미해결 충돌
- `STALE` / 노후 근거
- waiver without rationale / 근거 없는 waiver
- Tier-D source used to canonicalize a FACT/NORMALIZED_FACT / Tier-D 사실 정식화 시도

Candidate evidence additionally requires non-empty source `publisher`, `locator`, and valid source `tier`.

Candidate 근거는 추가로 출처 `publisher`, `locator`, 유효한 `tier`를 요구합니다.

## Human review scope lock / 인간 검토 범위 잠금

The review hash covers:

검토 해시는 다음을 포함합니다.

- candidate schema/status/canonical flag
- normalized Draft
- all input-governance bindings
- all evidence records

It deliberately excludes the `review` object itself. `candidate-validate` returns the computed SHA-256. A human reviewer must review that exact scope and place the hash in `review.scope_sha256` with:

`review` 객체 자체는 해시에서 제외됩니다. `candidate-validate`는 계산된 SHA-256을 반환하며 인간 검토자는 정확히 그 범위를 검토한 뒤 다음과 함께 `review.scope_sha256`에 해시를 기록해야 합니다.

- `decision = APPROVE`
- non-empty `reviewer`
- valid `reviewed_at`
- non-empty `rationale`
- exact matching `scope_sha256`

Any later change to Draft inputs, evidence, or input governance changes the scope hash and invalidates the approval.

이후 Draft 입력·근거·입력거버넌스가 변경되면 검토범위 해시가 바뀌어 승인이 무효화됩니다.

## CLI / CLI

```bash
vih candidate-build workspace/user_cases/my_draft.json > workspace/user_cases/my_candidate.json
vih candidate-validate workspace/user_cases/my_candidate.json
# Human reviews the exact candidate scope and records APPROVE + returned SHA-256.
vih promotion-check workspace/user_cases/my_candidate.json
```

Machine-readable mode / 기계판독 모드:

```bash
vih --json candidate-validate workspace/user_cases/my_candidate.json
vih --json promotion-check workspace/user_cases/my_candidate.json
```

A successful `promotion-check` returns:

성공한 `promotion-check` 상태:

```text
REVIEW_APPROVED_READY_FOR_PR
canonical = false
```

## Web / Web

Run / 실행:

```bash
vih web
```

Then open / 접속:

- `/draft` — user Draft Lab / 사용자 Draft 랩
- `/promotion` — Promotion Review Lab / 승격 검토 랩

Promotion endpoints / 승격 endpoint:

- `POST /api/promotion/build`
- `POST /api/promotion/assess`
- `POST /api/promotion/check`

The Web layer calls the same promotion service as CLI. It does not persist candidate payloads.

Web 계층은 CLI와 동일한 승격 서비스를 호출하며 Candidate payload를 영속화하지 않습니다.

## Canonical boundary / 정식 경계

M9 has no function that inserts into `registry/cases.json`, writes canonical analysis directories, or assigns `CANONICAL` status.

M9에는 `registry/cases.json` 삽입, 정식 분석 디렉터리 기록, `CANONICAL` 상태 부여 기능이 없습니다.

After `REVIEW_APPROVED_READY_FOR_PR`, the required next control is a **separate repository PR with human review, full CI, and merge**. Only that governed repository transition can establish canonical state.

`REVIEW_APPROVED_READY_FOR_PR` 이후에는 **별도 저장소 PR, 인간 검토, 전체 CI, 병합**이 필요합니다. 정식 상태는 이 저장소 거버넌스 전이를 통해서만 확립될 수 있습니다.
