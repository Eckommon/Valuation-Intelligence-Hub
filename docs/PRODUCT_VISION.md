# Product Vision / 제품 비전

## End-state / 최종 상태

Valuation-Intelligence-Hub must mature beyond a methodology and code repository into a user-executable valuation product. The user should be able to provide an asset or company, review sourced facts and assumptions, run valuation models, compare scenarios, inspect market-implied expectations, and export a reproducible report without editing source code.

Valuation-Intelligence-Hub는 방법론·코드 저장소를 넘어 사용자가 직접 실행할 수 있는 가치분석 제품으로 발전해야 한다. 사용자는 소스코드를 수정하지 않고도 자산·기업을 입력하고, 출처가 있는 사실과 가정을 검토하며, 가치평가 모델을 실행하고, 시나리오를 비교하고, 시장 내재 기대를 확인하며, 재현 가능한 보고서를 출력할 수 있어야 한다.

## Product decision / 제품 결정

The preferred end-state is **web-first hybrid**, not web-only and not desktop-only.

권장 최종 형태는 **웹 우선 하이브리드(web-first hybrid)**이며, 웹 전용도 데스크톱 전용도 아니다.

### Primary interface: Web application / 주 인터페이스: 웹 애플리케이션

The Web UI is the default interface for most users because it minimizes installation friction and is best suited to evidence inspection, interactive tables, scenario comparison, sensitivity surfaces, charts, audit trails, bilingual reporting, and collaboration.

웹 UI는 설치 장벽이 가장 낮고 근거 검토, 대화형 표, 시나리오 비교, 민감도 분석, 차트, 감사추적, 영한문 보고서, 협업에 가장 적합하므로 대부분 사용자의 기본 인터페이스로 사용한다.

### Secondary interface: CLI / local executable / 보조 인터페이스: CLI·로컬 실행형

A CLI/local execution path remains a first-class interface for deterministic batch analysis, automation, offline/private cases, CI/CD, reproducibility, advanced users, and future desktop packaging.

CLI·로컬 실행 경로는 대량 결정론적 분석, 자동화, 오프라인·민감 사례, CI/CD, 재현성, 고급 사용자, 향후 데스크톱 패키징을 위한 1급 인터페이스로 유지한다.

### Shared backend / 공통 백엔드

Web, CLI, API, and any future desktop shell MUST call the same tested valuation kernel, schemas, evidence gates, and model registry. User interfaces may not reimplement valuation logic independently.

웹, CLI, API, 향후 데스크톱 셸은 반드시 동일한 검증 가치평가 커널, 스키마, 근거 게이트, 모델 레지스트리를 호출해야 한다. 사용자 인터페이스가 가치평가 로직을 별도로 재구현해서는 안 된다.

## Why both / 둘 다 필요한 이유

| Need / 필요 | Web | CLI / Local |
|---|---|---|
| Zero/low installation / 설치 편의 | Best / 최상 | Lower / 낮음 |
| Non-developer usability / 비개발자 사용성 | Best / 최상 | Low / 낮음 |
| Interactive evidence review / 대화형 근거 검토 | Best / 최상 | Limited / 제한적 |
| Scenario and sensitivity visualization / 시나리오·민감도 시각화 | Best / 최상 | Limited / 제한적 |
| Batch automation / 대량 자동화 | Possible / 가능 | Best / 최상 |
| Offline/private analysis / 오프라인·민감 분석 | Limited by deployment / 배포방식 의존 | Best / 최상 |
| Reproducible CI execution / 재현 CI 실행 | Backend dependent / 백엔드 의존 | Best / 최상 |
| Public sharing/collaboration / 공개 공유·협업 | Best / 최상 | Low / 낮음 |

The Web UI is therefore the user experience center, while CLI/local execution is the reproducibility and power-user center.

따라서 웹 UI는 사용자 경험의 중심이고, CLI·로컬 실행은 재현성과 고급 사용자의 중심이다.

## Product principles / 제품 원칙

1. **One kernel, multiple interfaces / 하나의 커널, 여러 인터페이스** — CLI, Web UI, future API and desktop shell MUST call the same tested valuation kernel rather than reimplementing calculations.
2. **Evidence visible by default / 근거 기본 노출** — Material outputs should expose the underlying facts, assumptions, dates, and sources.
3. **Fail closed / 실패 시 차단** — Missing, stale, or conflicting material inputs should visibly block canonical valuation rather than be silently filled.
4. **Progressive usability / 단계적 사용성** — Advanced controls may exist, but a non-developer should be able to run a standard valuation workflow.
5. **Cross-asset extensibility / 범자산 확장성** — User experience should select the appropriate adapter/model for public equity, private company, startup, real estate, infrastructure, project finance, IP, and future asset classes.
6. **Reproducible export / 재현 가능한 출력** — Every final report should identify model version, evidence snapshot, assumptions, scenario set, and calculation result.
7. **Local/privacy escape hatch / 로컬·프라이버시 경로** — Users must have a supported path to run sensitive or proprietary cases without forcing public/cloud persistence.
8. **Interface parity for core results / 핵심결과 인터페이스 일치** — The same case version must produce equivalent core valuation results across Web, CLI and API.

## Planned interface path / 예정 인터페이스 경로

The implementation order prioritizes architectural stability before UI polish:

UI 완성도보다 아키텍처 안정성을 먼저 확보하며 다음 순서로 구현한다.

1. Tested Python kernel / 검증 Python 커널
2. Stable machine-readable case format / 안정적 기계 판독 사례 포맷
3. CLI for deterministic execution and regression / 결정론적 실행·회귀검증 CLI
4. Web backend/service layer over the same kernel / 동일 커널 기반 웹 백엔드·서비스 계층
5. Human-friendly Web UI as the default product surface / 기본 제품화면인 사용자 친화 Web UI
6. Local/private mode and optional desktop packaging / 로컬·비공개 모드와 선택적 데스크톱 패키징
7. Optional public API and scheduled automation / 선택적 공개 API·예약 자동화

The CLI precedes the Web UI technically, but the Web UI is the primary end-user product.

기술 구현 순서상 CLI가 Web UI보다 먼저이지만 최종 일반사용자 제품의 중심은 Web UI이다.

## Target user workflow / 목표 사용자 흐름

```text
Search or create asset / 자산 검색·생성
        ↓
Evidence snapshot / 근거 스냅샷
        ↓
Resolve UNKNOWN/HOLD / UNKNOWN·HOLD 해소
        ↓
Choose/adapt valuation model / 가치평가 모델 선택·적용
        ↓
Review FACT vs ASSUMPTION / 사실·가정 검토
        ↓
Run Base + Bear/Bull / Base + Bear/Bull 실행
        ↓
Sensitivity + Reverse valuation / 민감도 + 역산 가치평가
        ↓
Expected return + risks / 기대수익률 + 위험
        ↓
Bilingual reproducible report / 영한문 재현 보고서
```

## User-level definition of done / 사용자 관점 완료 정의

The project is not considered product-complete until a non-developer can use the Web UI to perform a standard case from start to export, while the same case can also be reproduced via CLI/local execution.

비개발자가 Web UI에서 표준 사례를 생성부터 보고서 출력까지 수행할 수 있고 동일 사례가 CLI·로컬 실행으로도 재현되기 전까지 제품 완성으로 보지 않는다.

The user must be able to:

사용자는 다음을 수행할 수 있어야 한다.

- create or open a valuation case / 가치평가 사례 생성·열기
- search/select an asset where supported / 지원되는 자산 검색·선택
- import or enter evidence-backed data / 근거 기반 데이터 불러오기·입력
- distinguish facts from assumptions / 사실과 가정 구분
- run an appropriate valuation model / 적합 가치평가 모델 실행
- compare Bear/Base/Bull and sensitivity / Bear/Base/Bull 및 민감도 비교
- run reverse valuation / 역산 가치평가 실행
- inspect expected return and key risks / 기대수익률·핵심위험 확인
- see blocked/unknown inputs explicitly / 차단·미확정 입력 명시 확인
- inspect every material source / 모든 중요 출처 확인
- save/version cases / 사례 저장·버전관리
- export a bilingual, reproducible valuation report / 영한문 재현 가능 가치평가 보고서 출력
- reproduce the same result through CLI/local execution / 동일 결과를 CLI·로컬 실행으로 재현
