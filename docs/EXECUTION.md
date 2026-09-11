# Executable Interface / 실행형 인터페이스

## Purpose / 목적

M4 introduces the first user-executable layer of Valuation-Intelligence-Hub. The CLI is intentionally thin: it loads versioned cases, validates evidence gates, routes each case to the correct existing valuation kernel, recomputes the result, and verifies that runtime output still matches the repository's canonical stored result.

M4는 Valuation-Intelligence-Hub의 첫 사용자 실행 계층을 도입한다. CLI는 의도적으로 얇게 유지한다. 버전 관리 사례를 로드하고 근거 게이트를 검증하며, 각 사례를 올바른 기존 가치평가 커널로 라우팅하고, 결과를 재계산한 뒤 런타임 결과가 저장소의 정식 저장 결과와 여전히 일치하는지 확인한다.

```text
User / 사용자
   ↓
CLI (`vih`)  ─────────────── future Web UI / 향후 Web UI
   ↓                          ↓
        Shared Case Service / 공통 사례 서비스
                    ↓
             Case Registry / 사례 레지스트리
                    ↓
          Validate Evidence Gate / 근거 게이트 검증
                    ↓
             Model Router / 모델 라우터
              ↙                  ↘
      FCFF Scenario Kernel     Venture Probability Kernel
      FCFF 시나리오 커널       벤처 확률가중 커널
              ↘                  ↙
        Runtime ↔ Canonical Result Check
        실행값 ↔ 정식 저장값 검증
```

The CLI and future Web UI must never implement separate valuation formulas.

CLI와 향후 Web UI는 별도의 가치평가 공식을 구현해서는 안 된다.

## Install for local development / 로컬 개발 설치

From the repository root / 저장소 루트에서:

```bash
python -m pip install -e ".[dev]"
```

This registers the `vih` command.

위 명령은 `vih` 실행 명령을 등록한다.

The module form uses the same entry point logic:

모듈 방식도 동일한 실행 로직을 사용한다.

```bash
python -m valuation_hub.cli --help
```

## Commands / 명령어

### List registered cases / 등록 사례 목록

```bash
vih list
```

Machine-readable output / 기계 판독 출력:

```bash
vih --json list
```

### Validate a case / 사례 검증

```bash
vih validate KR_010120_LS_ELECTRIC
vih validate KR_229640_LS_ECO_ENERGY
vih validate US_JTAI_JET_AI
```

Validation fails closed when required files are missing, the evidence promotion gate is not PASS, the case ID is inconsistent, or the model version does not match the registered model route.

필수 파일 누락, 근거 승격 게이트 미통과, 사례 ID 불일치, 모델 버전과 등록 모델 라우트 불일치 시 검증은 fail-closed한다.

### Run a valuation case / 가치평가 사례 실행

```bash
vih run KR_010120_LS_ELECTRIC
```

The runner does **not** read the stored valuation result and print it as if it had calculated the value. It rebuilds the valuation from `case_inputs.json` through the shared kernel, then compares the recomputed value against `valuation_result.json`.

실행기는 저장된 가치평가 결과를 읽어 계산한 것처럼 출력하지 않는다. `case_inputs.json`을 공통 커널로 다시 계산한 다음 재계산값을 `valuation_result.json`과 비교한다.

Default runtime-drift tolerances / 기본 실행값 drift 허용오차:

- `equity_fcff`: **1.0 currency unit/share** / 주당 통화단위 1.0
- `venture_probability`: **1e-6 currency unit/share** / 주당 통화단위 1e-6

A value outside the defined tolerance is an error, not an automatic canonical update.

허용오차를 벗어난 값은 오류이며 정식 결과를 자동으로 갱신하지 않는다.

JSON mode / JSON 모드:

```bash
vih --json run KR_229640_LS_ECO_ENERGY
```

### Print canonical bilingual report / 정식 영한문 보고서 출력

```bash
vih report US_JTAI_JET_AI
```

JSON wrapper / JSON 래퍼:

```bash
vih --json report US_JTAI_JET_AI
```

## Current registry / 현재 레지스트리

| Case ID | Asset / 자산 | Model route / 모델 라우트 |
|---|---|---|
| `KR_010120_LS_ELECTRIC` | LS ELECTRIC | `equity_fcff` |
| `KR_229640_LS_ECO_ENERGY` | LS Eco Energy / LS에코에너지 | `equity_fcff` |
| `US_JTAI_JET_AI` | Jet.AI | `venture_probability` |

The registry is versioned in `registry/cases.json`.

레지스트리는 `registry/cases.json`에서 버전 관리한다.

## Fail-closed guarantees / Fail-closed 보장

The executable layer must refuse to produce a grounded result when:

다음 조건에서는 실행 계층이 근거화된 결과 생성을 거부해야 한다.

- the case is not registered / 사례가 등록되지 않음
- required case/evidence/result files are missing / 필수 사례·근거·결과 파일 누락
- the evidence promotion gate is not PASS / 근거 승격 게이트 미통과
- the registry model and case model version disagree / 레지스트리 모델과 사례 모델 버전 불일치
- the registered case path escapes the repository root / 등록 경로가 저장소 루트를 벗어남
- runtime valuation drifts from the canonical result beyond tolerance / 런타임 가치가 정식 결과와 허용오차 이상 불일치
- a model route is unsupported / 모델 라우트 미지원

No missing material value is silently invented to keep execution going.

실행을 지속하기 위해 누락된 중요 값을 암묵적으로 만들어내지 않는다.

## Current limitation / 현재 제한

M4 executes **versioned repository cases**. It does not yet fetch live market data, create a new valuation case from a ticker, or provide an interactive Web UI.

M4는 **버전 관리된 저장소 사례**를 실행한다. 아직 실시간 시장데이터를 자동 수집하거나 종목코드만으로 새 가치평가 사례를 생성하거나 대화형 Web UI를 제공하지 않는다.

These limitations are deliberate. The execution contract must be stable and reproducible before the Web layer is added.

이는 의도된 제한이다. Web 계층을 추가하기 전에 실행 계약이 안정적이고 재현 가능해야 한다.

## Next product layer / 다음 제품 계층

After M4 is accepted, the next product mission should expose this same service contract through a read-oriented Web application MVP. The Web UI should make evidence, assumptions, scenario values, and blocked states visible by default rather than hiding them behind a single target-price number.

M4 승인 후 다음 제품 미션은 동일 서비스 계약을 읽기 중심 Web Application MVP로 노출해야 한다. Web UI는 단일 목표주가 뒤에 내용을 숨기지 않고 근거, 가정, 시나리오 가치, 차단 상태를 기본적으로 보여줘야 한다.
