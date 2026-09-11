# Valuation-Intelligence-Hub / 가치분석 인텔리전스 허브

> **Separate price from economic value, make assumptions explicit, and make valuation reproducible.**  
> **가격과 경제적 가치를 분리하고, 가정을 명시하며, 가치평가를 재현 가능하게 만든다.**

Valuation-Intelligence-Hub is a reproducible, evidence-grounded **cross-asset valuation intelligence system**. It connects official/user evidence, explicit assumptions, valuation kernels, review governance, and repository-controlled canonicalization.

Valuation-Intelligence-Hub는 공식·사용자 근거, 명시적 가정, 가치평가 커널, 검토 거버넌스, 저장소 기반 정식화를 연결하는 재현 가능한 **범자산 가치분석 인텔리전스 시스템**입니다.

## Principles / 원칙

- **Facts ≠ assumptions / 사실 ≠ 가정**
- **Official source ≠ automatic canonical fact / 공식 출처 ≠ 자동 정식 사실**
- **Every material fact needs provenance / 모든 중요 사실은 출처 필요**
- **Repository canonical state > AI recollection / 저장소 정식 상태 > AI 기억**
- **Growth must reconcile with reinvestment / 성장은 재투자와 일치**
- **Choose the model for the asset / 자산에 맞는 모델 선택**
- **Same versioned inputs + model ⇒ reproducible output / 동일 버전 입력·모델 ⇒ 재현 결과**
- **One kernel, multiple interfaces / 하나의 커널, 여러 인터페이스**

## Valuation methods / 가치평가 방법

Operating-company FCFF:

\[
FCFF = EBIT(1-T) + D\&A - CAPEX - \Delta NWC
\]

The Hub also supports reverse valuation and a probability-weighted venture model for option-like/financing-dependent assets.

Hub는 역산 가치평가와 옵션형·자금조달 의존 자산을 위한 확률가중 벤처 모델도 지원합니다.

## Reference cases / 기준 사례

| Case | Model | Reference classification |
|---|---|---|
| [`LS ELECTRIC`](analyses/equities/KR_010120_LS_ELECTRIC/) | FCFF Bear/Base/Bull | `MARKET_PRICE_ABOVE_MODELED_BULL` |
| [`LS Eco Energy`](analyses/equities/KR_229640_LS_ECO_ENERGY/) | FCFF Bear/Base/Bull | `MARKET_PRICE_BETWEEN_MODELED_BASE_AND_BULL` |
| [`Jet.AI`](analyses/equities/US_JTAI_JET_AI/) | Probability-weighted venture | option-like / very high model risk |

These are versioned methodology references, **not live investment recommendations or target prices**.

위 결과는 버전 관리된 방법론 기준이며 **실시간 투자권고·목표주가가 아닙니다**.

## Install / 설치

```bash
python -m pip install -e ".[dev]"
```

## Canonical execution / 정식 사례 실행

```bash
vih list
vih validate KR_010120_LS_ELECTRIC
vih run KR_229640_LS_ECO_ENERGY
vih report US_JTAI_JET_AI
```

## Governed authority flow / 정식 권위 흐름

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

A mathematically valid value, an official API response, and a canonical repository fact are deliberately different states.

수학적으로 유효한 값, 공식 API 응답, 저장소 정식 사실은 의도적으로 서로 다른 상태입니다.

## User Draft → Canonical / 사용자 Draft → 정식

### M8 — Draft

```bash
vih draft-template equity_fcff > workspace/user_cases/my_company.json
vih draft-validate workspace/user_cases/my_company.json
vih draft-run workspace/user_cases/my_company.json
```

### M9 — Evidence-governed Candidate

```bash
vih candidate-build workspace/user_cases/my_company.json > workspace/user_cases/candidate.json
vih candidate-validate workspace/user_cases/candidate.json
vih promotion-check workspace/user_cases/candidate.json
```

Human review is scope-hash locked; post-review mutation invalidates approval.

### M10 — Deterministic promotion package

```bash
vih package-build workspace/user_cases/candidate.json \
  --case-id KR_EXAMPLE_COMPANY \
  --name-en "Example Company" \
  --name-ko "예시회사" \
  --asset-class public_equity > workspace/user_cases/package.json
```

### M11 — Canonical admission proposal

```bash
vih admission-build workspace/user_cases/package.json > workspace/user_cases/admission.json
vih admission-validate workspace/user_cases/admission.json
```

### M12 — Guarded repository apply

```bash
git switch -c admission/KR_EXAMPLE_COMPANY
vih admission-plan workspace/user_cases/admission.json --target-repo . > workspace/user_cases/change-plan.json
vih admission-plan-validate workspace/user_cases/change-plan.json workspace/user_cases/admission.json --target-repo .
vih admission-apply workspace/user_cases/change-plan.json workspace/user_cases/admission.json --target-repo .
```

Filesystem apply is restricted to `admission/*` branches/worktrees; `main`, `master`, detached HEAD, collisions, symlink escapes, and registry baseline drift fail closed.

## Live evidence / 실시간 근거

### M13 — SEC EDGAR CompanyFacts

Adapter: `sec-companyfacts-v0.1`

```bash
vih sec-fetch 0000320193 \
  --user-agent "Valuation-Intelligence-Hub contact@example.com" \
  --output workspace/source_snapshots/AAPL-companyfacts.json

vih sec-snapshot-validate workspace/source_snapshots/AAPL-companyfacts.json
vih sec-extract workspace/source_snapshots/AAPL-companyfacts.json revenue
```

SEC responses are saved as immutable noncanonical snapshots. Extracted values remain `EVIDENCE_CANDIDATE_UNREVIEWED` until governed review.

SEC 응답은 불변 비정식 snapshot으로 저장되며 추출값은 거버넌스 검토 전까지 미검토 후보입니다.

See [`docs/LIVE_EVIDENCE_SEC.md`](docs/LIVE_EVIDENCE_SEC.md).

### M14 — OpenDART financial statements

Adapter: `opendart-fnltt-singl-acnt-all-v0.1`

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

Security and evidence controls:

- OpenDART API key is transport-only and never persisted.
- Persistent locators omit `crtfc_key`.
- HTTP 200 is insufficient; OpenDART API `status=000` is required.
- raw UTF-8 body + body SHA-256 + snapshot SHA-256 are preserved.
- `CFS`/`OFS` request identity is fixed per snapshot.
- `BS`/`IS`/`CIS`/`CF`/`SCE` boundaries cannot be silently crossed.
- account selection uses explicit exact `account_id` then exact `account_nm` fallback; no fuzzy matching.
- equal-precedence conflicting values fail closed.
- blank amounts remain unknown, not zero.
- `thstrm_add_amount` is preserved but is **not** silently interpreted as TTM/YTD.

OpenDART API key는 transport 내부에서만 사용되고 영속 파일·locator·Web payload·일반 출력에 저장되지 않습니다.

See [`docs/LIVE_EVIDENCE_OPENDART.md`](docs/LIVE_EVIDENCE_OPENDART.md).

## Web product / Web 제품

```bash
vih web
```

Default: `http://127.0.0.1:8765`

Main surfaces include canonical valuation views, evidence browsing, previews, Draft/Promotion/Admission/PR Preparation labs, plus read-only source inspectors:

```text
/source       — SEC snapshot validation + extraction
/dart-source  — OpenDART snapshot validation + extraction
```

There is deliberately no browser-origin SEC/OpenDART live-fetch endpoint and no OpenDART API-key field in Web.

브라우저에서 SEC/OpenDART live fetch를 수행하거나 OpenDART API key를 입력하는 경로는 의도적으로 없습니다.

## Architecture / 아키텍처

```text
Official Sources
      │
Immutable Source Snapshots
      │
Unreviewed Evidence Candidates
      │
Evidence Governance + Human Review
      │
Shared Valuation Kernels
      │
Canonical Admission + Registry
      │
Web · CLI · API
```

## Milestones / 마일스톤

- [x] M1–M3 Evidence, normalization, scenarios, reference cases
- [x] M4–M7 Registry, CLI, Web, interactive product UX
- [x] M8 User Draft workflow
- [x] M9 Reviewed promotion protocol
- [x] M10 Deterministic promotion-package staging
- [x] M11 Versioned reviewed-Draft canonical admission
- [x] M12 Guarded admission applicator + PR-ready plan
- [x] M13 Immutable SEC CompanyFacts acquisition
- [ ] **M14 OpenDART immutable financial-statement adapter — active**
- [ ] Financial evidence normalization + period semantics + TTM transforms
- [ ] First non-equity valuation adapter

## Canonical documentation / 정식 문서

- [`docs/FOUNDATION.md`](docs/FOUNDATION.md)
- [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md)
- [`docs/EVIDENCE_POLICY.md`](docs/EVIDENCE_POLICY.md)
- [`docs/AI_GROUNDING_POLICY.md`](docs/AI_GROUNDING_POLICY.md)
- [`docs/SCENARIO_REVERSE_POLICY.md`](docs/SCENARIO_REVERSE_POLICY.md)
- [`docs/PRODUCT_VISION.md`](docs/PRODUCT_VISION.md)
- [`docs/EXECUTION.md`](docs/EXECUTION.md)
- [`docs/USER_DRAFTS.md`](docs/USER_DRAFTS.md)
- [`docs/PROMOTION_PROTOCOL.md`](docs/PROMOTION_PROTOCOL.md)
- [`docs/PROMOTION_PACKAGE.md`](docs/PROMOTION_PACKAGE.md)
- [`docs/CANONICAL_ADMISSION.md`](docs/CANONICAL_ADMISSION.md)
- [`docs/GUARDED_ADMISSION_APPLY.md`](docs/GUARDED_ADMISSION_APPLY.md)
- [`docs/LIVE_EVIDENCE_SEC.md`](docs/LIVE_EVIDENCE_SEC.md)
- [`docs/LIVE_EVIDENCE_OPENDART.md`](docs/LIVE_EVIDENCE_OPENDART.md)
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — canonical resume point / 정식 재개점
