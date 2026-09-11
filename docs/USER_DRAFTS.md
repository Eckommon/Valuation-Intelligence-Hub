# User Draft Cases / 사용자 Draft 사례

## Purpose / 목적

User Drafts let a user run the shared valuation kernels with their own inputs without editing source code or changing canonical repository facts.

사용자 Draft는 소스코드를 수정하거나 정식 저장소 사실을 변경하지 않고 사용자가 자신의 입력값으로 공통 가치평가 커널을 실행하게 한다.

Every Draft is explicitly:

모든 Draft의 명시적 상태:

```text
DRAFT_USER_SUPPLIED
NOT_CANONICAL
USER_SUPPLIED_UNVERIFIED
```

A successful valuation calculation does **not** mean the inputs have passed evidence review.

가치평가 계산에 성공했다고 입력값이 근거 검토를 통과한 것은 아니다.

## CLI workflow / CLI 흐름

### Equity FCFF / 상장기업 FCFF

```bash
mkdir -p workspace/user_cases
vih draft-template equity_fcff > workspace/user_cases/my_company.json
# edit the JSON / JSON 수정
vih draft-validate workspace/user_cases/my_company.json
vih draft-run workspace/user_cases/my_company.json
```

### Venture / 벤처

```bash
vih draft-template venture_probability > workspace/user_cases/my_venture.json
vih draft-validate workspace/user_cases/my_venture.json
vih draft-run workspace/user_cases/my_venture.json
```

Add global `--json` before the command for machine-readable validation/run output.

기계 판독 출력은 명령 앞에 전역 `--json`을 추가한다.

## Web Draft Lab / Web Draft 랩

Run:

실행:

```bash
vih web
```

Then open / 이후 접속:

```text
http://127.0.0.1:8765/draft
```

The Draft Lab can load either model template, validate pasted JSON, and execute it in memory. The server does not save the Draft payload.

Draft Lab은 두 모델 템플릿을 불러오고 붙여넣은 JSON을 검증·실행한다. 서버는 Draft payload를 저장하지 않는다.

## Draft models / Draft 모델

### `equity_fcff`

The Draft provides explicit forecast-year economics:

Draft는 연도별 경제성을 명시적으로 입력한다.

- revenue / 매출
- EBIT margin / EBIT 마진
- tax rate / 세율
- D&A / 감가상각·상각
- CAPEX / 자본적지출
- ΔNWC / 운전자본 변화
- WACC
- terminal growth / 영구성장률
- diluted shares and EV-to-equity bridge inputs / 희석주식수·EV→Equity 입력

The shared `run_fcff_scenario` kernel performs valuation.

가치평가는 공통 `run_fcff_scenario` 커널이 수행한다.

### `venture_probability`

The Draft provides scenario probabilities and conditional terminal economics:

Draft는 시나리오 확률과 조건부 종착 경제성을 입력한다.

- probability / 확률
- terminal revenue / 종착 매출
- EV/Sales multiple / EV/Sales 배수
- terminal net debt / 종착 순부채
- future diluted shares / 미래 희석주식수
- discount rate / 할인율
- recovery value where applicable / 필요 시 회수가치

The shared venture kernel performs probability-weighted valuation.

공통 Venture 커널이 확률가중 가치평가를 수행한다.

## Fail-closed validation / Fail-closed 검증

Draft execution rejects conditions including:

Draft 실행은 다음 조건 등을 차단한다.

- non-finite numbers / NaN·무한대 등 비유한 숫자
- terminal growth >= WACC / 영구성장률 ≥ WACC
- invalid or duplicate forecast years / 비정상·중복 전망연도
- negative CAPEX / 음수 CAPEX
- zero/negative diluted shares / 0·음수 희석주식수
- venture probabilities not summing to 1.0 / 벤처 확률합 ≠ 1.0
- unsupported schema or model / 미지원 스키마·모델

## Local workspace / 로컬 작업공간

`workspace/user_cases/` is Git-ignored by default so personal Drafts are not accidentally committed.

`workspace/user_cases/`는 기본 Git 제외 경로이므로 개인 Draft가 실수로 커밋되지 않는다.

This is convenience, not a security boundary. Users must still protect confidential input files appropriately.

이는 편의장치이지 보안 경계가 아니다. 기밀 입력파일은 사용자가 별도로 적절히 보호해야 한다.

## Canonical promotion boundary / 정식 승격 경계

M8 deliberately provides **no automatic Draft → canonical path**.

M8은 의도적으로 **Draft → 정식 자동 경로를 제공하지 않는다.**

A later promotion workflow must attach provenance, classify claims, reconcile conflicts, pass evidence gates, generate canonical results, pass regression tests, and enter the repository through reviewed version control.

향후 승격 절차는 출처 연결, 주장분류, 충돌조정, 근거게이트, 정식 결과 생성, 회귀테스트, 검토된 버전관리 절차를 모두 거쳐야 한다.
