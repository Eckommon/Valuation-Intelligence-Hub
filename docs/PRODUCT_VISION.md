# Product Vision / 제품 비전

## End-state / 최종 상태

Valuation-Intelligence-Hub must mature beyond a methodology and code repository into a user-executable valuation tool. The user should be able to provide an asset or company, review sourced facts and assumptions, run valuation models, compare scenarios, inspect market-implied expectations, and export a reproducible report without editing source code.

Valuation-Intelligence-Hub는 방법론·코드 저장소를 넘어 사용자가 직접 실행할 수 있는 가치분석 도구로 발전해야 한다. 사용자는 소스코드를 수정하지 않고도 자산·기업을 입력하고, 출처가 있는 사실과 가정을 검토하며, 가치평가 모델을 실행하고, 시나리오를 비교하고, 시장 내재 기대를 확인하며, 재현 가능한 보고서를 출력할 수 있어야 한다.

## Product principles / 제품 원칙

1. **One kernel, multiple interfaces / 하나의 커널, 여러 인터페이스** — CLI, Web UI, and future API MUST call the same tested valuation kernel rather than reimplementing calculations.
2. **Evidence visible by default / 근거 기본 노출** — Material outputs should expose the underlying facts, assumptions, dates, and sources.
3. **Fail closed / 실패 시 차단** — Missing, stale, or conflicting material inputs should visibly block canonical valuation rather than be silently filled.
4. **Progressive usability / 단계적 사용성** — Advanced controls may exist, but a non-developer should be able to run a standard valuation workflow.
5. **Cross-asset extensibility / 범자산 확장성** — User experience should select the appropriate adapter/model for public equity, private company, startup, real estate, infrastructure, project finance, IP, and future asset classes.
6. **Reproducible export / 재현 가능한 출력** — Every final report should identify model version, evidence snapshot, assumptions, scenario set, and calculation result.

## Planned interface path / 예정 인터페이스 경로

The precise UI technology is intentionally not fixed during M1. The intended progression is:

M1 단계에서는 UI 기술을 성급히 고정하지 않는다. 목표 진행 순서는 다음과 같다.

1. Tested Python kernel / 검증 Python 커널
2. Stable machine-readable case format / 안정적 기계 판독 사례 포맷
3. CLI for deterministic execution / 결정론적 실행 CLI
4. Human-friendly Web UI using the same kernel / 동일 커널 기반 사용자 친화 Web UI
5. Optional API or automation interface / 선택적 API·자동화 인터페이스

## User-level definition of done / 사용자 관점 완료 정의

The project is not considered product-complete until a user can:

다음이 가능하기 전까지 프로젝트를 제품 완성으로 보지 않는다.

- create or open a valuation case / 가치평가 사례 생성·열기
- import or enter evidence-backed data / 근거 기반 데이터 불러오기·입력
- distinguish facts from assumptions / 사실과 가정 구분
- run an appropriate valuation model / 적합 가치평가 모델 실행
- compare Bear/Base/Bull and sensitivity / Bear/Base/Bull 및 민감도 비교
- run reverse valuation / 역산 가치평가 실행
- inspect expected return and key risks / 기대수익률·핵심위험 확인
- see blocked/unknown inputs explicitly / 차단·미확정 입력 명시 확인
- export a bilingual, reproducible valuation report / 영한문 재현 가능 가치평가 보고서 출력
