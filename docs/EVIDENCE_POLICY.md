# Evidence & Provenance Policy / 근거·출처 정책

## Purpose / 목적

Valuation-Intelligence-Hub treats evidence quality as a first-class valuation input. A valuation result is not analysis-grade merely because its arithmetic is correct; material facts must be traceable, time-bounded, classified, and reproducible.

Valuation-Intelligence-Hub는 근거 품질을 가치평가의 1급 입력으로 취급한다. 계산이 맞다는 이유만으로 분석급 결과가 되는 것은 아니다. 중요 사실은 추적 가능하고, 기준시점이 명확하며, 분류되고, 재현 가능해야 한다.

## Canonical claim classes / 표준 주장 분류

Every material claim MUST be classified as one of:

모든 중요 주장은 다음 중 하나로 분류해야 한다.

- `FACT` — directly observed from an admissible source / 허용 가능한 출처에서 직접 관측된 사실
- `NORMALIZED_FACT` — a documented transformation of one or more facts / 하나 이상의 사실을 문서화된 규칙으로 변환한 정규화 사실
- `ASSUMPTION` — explicit forward-looking or simplifying input / 명시적 미래전망 또는 단순화 가정
- `DERIVED` — deterministic calculation from admissible inputs / 허용 입력으로부터 결정론적으로 계산한 파생값
- `INTERPRETATION` — analytical judgement that is not itself a fact / 사실 자체가 아닌 분석적 판단
- `UNKNOWN` — unresolved, missing, conflicting, or insufficiently supported / 미해결·누락·충돌·근거 부족

An AI system MUST NOT silently promote `ASSUMPTION`, `INTERPRETATION`, or `UNKNOWN` into `FACT`.

AI 시스템은 `ASSUMPTION`, `INTERPRETATION`, `UNKNOWN`을 암묵적으로 `FACT`로 승격해서는 안 된다.

## Source-quality ladder / 출처 품질 등급

### Tier A — Primary authoritative / 1차 권위자료

Examples: audited filings, statutory filings, exchange filings, company IR releases, official government datasets, bond prospectuses, signed contracts when lawfully available.

예: 감사 재무제표, 법정 공시, 거래소 공시, 회사 IR, 정부 공식 데이터, 채권 설명서, 합법적으로 이용 가능한 체결 계약.

### Tier B — High-quality secondary / 고품질 2차자료

Examples: established market-data vendors, major financial databases, recognized credit-rating reports, reputable industry datasets.

예: 주요 시장데이터 공급자, 금융 데이터베이스, 공인 신용평가 보고서, 신뢰 가능한 산업 데이터.

### Tier C — Secondary explanatory / 설명형 2차자료

Examples: reputable press, analyst commentary, industry commentary. Useful for context, normally insufficient alone for canonical financial facts when Tier A/B evidence is available.

예: 신뢰 가능한 언론, 애널리스트·산업 코멘터리. 맥락에는 유용하지만 A/B 자료가 가능한 재무 사실을 단독 확정하는 근거로는 원칙적으로 부족하다.

### Tier D — Exploratory / 탐색자료

Examples: forums, social posts, unsourced summaries, AI-generated text. These MAY guide research but MUST NOT independently support a canonical material fact.

예: 포럼, 소셜 게시물, 무출처 요약, AI 생성 텍스트. 탐색 방향에는 사용할 수 있으나 중요 사실의 정식 근거가 될 수 없다.

## Required provenance fields / 필수 출처 필드

A material `FACT` MUST carry, at minimum:

중요 `FACT`는 최소 다음 필드를 가져야 한다.

- metric / 지표명
- value / 값
- unit / 단위
- currency where applicable / 해당 시 통화
- period or point-in-time date / 기간 또는 시점
- as-of date / 기준일
- source publisher / 출처 발행기관
- source type / 출처 유형
- source locator / URL, filing identifier, document path, or equivalent
- source tier / 출처 등급
- extraction note when interpretation is required / 해석이 필요한 경우 추출 메모

## Authority and precedence / 권위와 우선순위

For canonical project state, repository records outrank model recollection. When facts conflict, use this precedence unless a documented exception applies:

정식 프로젝트 상태에서는 저장소 기록이 모델 기억보다 우선한다. 사실이 충돌하면 문서화된 예외가 없는 한 다음 우선순위를 따른다.

1. Later valid restatement or statutory correction / 후속 유효 재작성·법정 정정
2. Tier A primary source / Tier A 1차자료
3. Tier B high-quality secondary source / Tier B 고품질 2차자료
4. Explicit normalized fact with reproducible transform / 재현 가능한 변환을 가진 명시적 정규화 사실
5. Tier C contextual source / Tier C 맥락자료
6. Current chat / 현재 대화
7. AI memory or recollection / AI 기억

## Freshness / 최신성

Time-sensitive inputs MUST include an as-of date. Market price, shares outstanding, debt, cash, risk-free rate, ERP, beta, and other time-varying inputs MUST NOT be reused indefinitely without freshness checks.

시점 민감 입력은 반드시 기준일을 포함한다. 시장가격, 주식수, 부채, 현금, 무위험금리, ERP, 베타 등 변동 입력은 최신성 점검 없이 무기한 재사용해서는 안 된다.

A case MAY define stricter freshness thresholds by metric. If an input breaches its threshold, it becomes `STALE` and canonical output promotion MUST fail closed until the input is refreshed or an explicit waiver is recorded.

사례별로 지표별 더 엄격한 최신성 기준을 둘 수 있다. 기준을 초과하면 `STALE`로 분류하며, 재수집 또는 명시적 예외기록 전에는 정식 산출물 승격을 fail-closed한다.

## Normalization / 정규화

Normalization MUST be explicit and reproducible. Typical adjustments include:

정규화는 명시적이고 재현 가능해야 한다. 대표 조정은 다음과 같다.

- stock splits and reverse splits / 액면분할·병합
- discontinued operations / 중단사업
- acquisitions and disposals / 인수·매각
- one-off gains and losses / 일회성 손익
- lease treatment / 리스 처리
- pro-forma business perimeter / 프로포마 사업범위
- currency conversion / 환산
- period alignment / 기간 정렬
- diluted-share reconstruction / 희석주식수 재구성

Every normalized fact MUST reference its source facts and transformation rule.

모든 정규화 사실은 원천 사실과 변환 규칙을 참조해야 한다.

## Contradictions / 충돌

When two material sources disagree and precedence does not resolve the conflict, the value becomes `UNKNOWN_CONFLICT` rather than being silently selected.

두 중요 출처가 충돌하고 우선순위로 해결되지 않으면 임의 선택하지 않고 `UNKNOWN_CONFLICT`로 둔다.

## Promotion gate / 정식 승격 게이트

A valuation result MAY be promoted to canonical status only if:

가치평가 결과는 다음을 충족할 때만 정식 상태로 승격할 수 있다.

1. all material factual inputs have compliant provenance / 모든 중요 사실 입력이 출처 규약 충족
2. normalization transforms are reproducible / 정규화 변환 재현 가능
3. assumptions are explicitly separated from facts / 가정과 사실 명시 분리
4. stale or conflicting material inputs are resolved or explicitly waived / 노후·충돌 중요 입력 해결 또는 명시 예외
5. the exact model version and scenario inputs are recorded / 정확한 모델 버전·시나리오 입력 기록
6. the result can be reproduced from repository state / 저장소 상태만으로 결과 재현 가능

## AI grounding contract / AI 근거화 계약

Before answering a project-state or valuation-state question, GPT/Codex/Astra SHOULD ground itself in the canonical repository files relevant to that question. If repository evidence is unavailable or contradictory, the model MUST state the limitation and use `UNKNOWN`/`HOLD` rather than inventing continuity.

프로젝트 상태나 가치평가 상태 질문에 답하기 전 GPT/Codex/Astra는 관련 정식 저장소 파일을 우선 확인해야 한다. 저장소 근거가 없거나 충돌하면 한계를 명시하고 연속성을 만들어내지 말고 `UNKNOWN`/`HOLD`를 사용해야 한다.
