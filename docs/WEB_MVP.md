# Web Application MVP / Web 애플리케이션 MVP

## Purpose / 목적

The M5 Web application is the first non-developer-facing interface of Valuation-Intelligence-Hub. It is a **read-oriented, local-first Web adapter** over the M4 `case_service` contract.

M5 Web 애플리케이션은 Valuation-Intelligence-Hub의 첫 비개발자 중심 인터페이스다. M4 `case_service` 계약 위에 구축하는 **읽기 중심·로컬 우선 Web 어댑터**다.

The Web layer does not own valuation formulas. / Web 계층은 가치평가 공식을 소유하지 않는다.

```text
Browser / 브라우저
       ↓
Web adapter / Web 어댑터
       ↓
case_service
       ↓
registry + evidence gates
       ↓
shared FCFF / venture kernels
```

## Run locally / 로컬 실행

```bash
python -m pip install -e ".[dev]"
vih web
```

Default URL / 기본 주소:

```text
http://127.0.0.1:8765
```

Custom bind / 사용자 지정:

```bash
vih web --host 127.0.0.1 --port 9000
```

The default bind is loopback-only for local/private usage. / 기본 바인드는 로컬·비공개 사용을 위해 loopback 전용이다.

## User-visible capabilities / 사용자 기능

- Dashboard of canonical registered cases / 정식 등록 사례 대시보드
- Case detail page / 사례 상세 화면
- Market snapshot / 시장가격 스냅샷
- Evidence promotion gate / 근거 승격 게이트
- Model and model version / 모델·모델버전
- Valuation date and currency / 가치평가 기준일·통화
- FCFF Bear/Base/Bull runtime values / FCFF Bear·Base·Bull 런타임 가치
- Venture probability-weighted runtime value / 벤처 확률가중 런타임 가치
- Decision/risk classification from canonical result metadata / 정식 결과 메타데이터의 판단·위험 분류
- Grounding status / 저장소 근거화 상태

## HTTP endpoints / HTTP 엔드포인트

```text
GET /                         HTML dashboard / HTML 대시보드
GET /case/<case_id>           HTML case detail / HTML 사례 상세
GET /healthz                  JSON health check / JSON 상태 확인
GET /api/cases                JSON registry list / JSON 사례 목록
GET /api/cases/<case_id>      JSON grounded case view / JSON 근거화 사례 보기
```

Unknown or invalid case IDs fail closed. / 미등록·비정상 case ID는 fail-closed한다.

## Security and scope / 보안·범위

M5 is intentionally local-first and read-only. It does not implement authentication, case editing, cloud deployment, or live market-data ingestion.

M5는 의도적으로 로컬 우선·읽기 전용이다. 인증, 사례 편집, 클라우드 배포, 실시간 시장데이터 수집은 구현하지 않는다.

Do not bind the MVP to a public network interface without a later security mission. / 후속 보안 미션 전에는 MVP를 공개 네트워크 인터페이스에 바인드하지 않는다.

## Product trajectory / 제품 진행방향

M5 proves that a human-friendly browser interface can reuse the same grounded execution path as the CLI. Later missions may add hosted deployment, interactive assumptions, scenario controls, evidence browsing, user-created cases, and cross-asset adapters while preserving the service boundary.

M5는 사용자 친화 브라우저 인터페이스가 CLI와 동일한 근거화 실행 경로를 재사용할 수 있음을 검증한다. 후속 미션에서는 서비스 경계를 유지하면서 호스팅 배포, 가정 편집, 시나리오 조작, 근거 탐색, 사용자 사례 생성, 범자산 어댑터를 추가할 수 있다.
