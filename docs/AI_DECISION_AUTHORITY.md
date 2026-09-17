# AI Decision Authority / AI 판단 권한

## Principle / 원칙

Valuation-Intelligence-Hub uses **evidence-first AI autonomy with human-on-exception governance**.

신빙성 있는 근거를 수집하고, 출처·기간·대상·의미를 검증하며, 반대증거를 탐색하고, 정책 기준을 만족한 내부 분석 판단은 AI가 자율적으로 내린다. 인간은 비용·자금·계약·법적/규제적 제출·계정/권한 변경 등 외부 구속효과가 있는 승인에 집중한다.

## AI-authorized scope / AI 자율 판단 범위

When evidence gates pass, AI may autonomously:

- interpret accounting and financial disclosures;
- classify facts, normalized facts, derived facts, and assumptions;
- resolve semantic compatibility between external data and internal valuation definitions;
- choose valuation assumptions and analytical methods with explicit evidence/rationale;
- perform contradiction search and select among supported alternatives;
- create/update repository analytical artifacts, issues, branches, PRs, CI fixes, and canonical analytical state;
- admit analytical cases when all repository policy gates pass and the admission has no external binding side effect.

The AI must never invent evidence, reviewer identities, approvals, timestamps, source locators, or external consent.

## Human-required boundary / 인간 필수 승인 경계

Human approval remains mandatory before an action that creates a material external commitment or side effect, including:

1. spending money, subscribing to paid services, or committing budget;
2. executing trades, payments, transfers, purchases, or other asset movements;
3. signing or accepting contracts, legal attestations, warranties, or binding terms;
4. regulatory, tax, legal, or other external submissions made on the user's behalf;
5. creating/changing credentials, account permissions, privileged access, or disclosing secrets;
6. irreversible external actions not already explicitly delegated by the user.

## Evidence-first gate / 증거우선 판단 게이트

AI approval is permitted only when all applicable conditions are satisfied:

1. **Source authority** — use the strongest practical source; official issuer/regulator sources are preferred for factual claims.
2. **Identity match** — entity, period, metric, filing, and scope are matched explicitly.
3. **Provenance** — immutable snapshot/hash lineage is preserved where the repository contract requires it.
4. **Semantic fit** — the external concept is shown to match the project's internal definition rather than merely sharing a similar label.
5. **Cross-check** — material conclusions are checked against supporting evidence where reasonably available.
6. **Contradiction search** — plausible conflicting evidence is actively sought.
7. **No material unresolved contradiction** — any material contradiction, ambiguity, or insufficient evidence results in HOLD/escalation, not forced approval.
8. **No prohibited external side effect** — if the next action crosses the human-required boundary, execution stops for human approval.

## Decision states / 판단 상태

- `APPROVE`: evidence gates pass; AI may continue autonomously.
- `HOLD`: evidence is incomplete, stale, ambiguous, or conflicting; gather more evidence or escalate.
- `REJECT`: evidence establishes that the proposed interpretation/action is invalid.
- `HUMAN_APPROVAL_REQUIRED`: analytical conclusion may be complete, but the next action crosses an external binding boundary.

## SEC aggregate-debt policy / SEC 총부채 정책

`AUTO_APPROVE_SEC_AGGREGATE_DEBT_V01` may approve the exact SEC concept `us-gaap:DebtLongtermAndShorttermCombinedAmount` for the project's `interest_bearing_debt` boundary only when:

- financing components are interest-bearing debt instruments;
- issuer disclosure reconciles reported total debt to the selected observation;
- operating lease liabilities are separately classified or otherwise demonstrably outside the selected financing-debt total;
- lease-liability exclusion is positively supported by issuer filing evidence;
- contradiction search finds no material contrary evidence;
- SEC observation provenance is Tier A and hash-linked.

The semantic decision remains:

`EXPLICIT_FILING_RECONCILIATION_EXCLUDES_LEASE_LIABILITIES`

If any criterion is not affirmatively supported, autonomous approval fails closed.

## Compatibility / 호환성

Historical explicit-human review artifacts remain valid. New AI adjudication artifacts are explicitly typed as AI and may generate a legacy-compatible downstream assertion only to reuse already-canonical validators and binding machinery. Such compatibility output must identify `AI_EVIDENCE_ADJUDICATOR_V01`; it must not impersonate a human reviewer.

## Migration rule / 전환 규칙

Older analytical gates that require human approval solely for internal interpretation are governance debt. They should be migrated incrementally to the evidence-first AI authority model, preserving provenance, validation, fail-closed behavior, and backward compatibility.
