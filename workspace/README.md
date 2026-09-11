# Local Draft Workspace / 로컬 Draft 작업공간

`workspace/user_cases/` is reserved for user-authored valuation Drafts that are intentionally **not canonical repository facts**.

`workspace/user_cases/`는 사용자 작성 가치평가 Draft를 위한 공간이며, 이 파일들은 의도적으로 **정식 저장소 사실이 아니다**.

## Rules / 규칙

- Draft status is always `DRAFT_USER_SUPPLIED / NOT_CANONICAL`. / Draft 상태는 항상 `DRAFT_USER_SUPPLIED / NOT_CANONICAL`이다.
- Files under `workspace/user_cases/` are ignored by Git by default. / `workspace/user_cases/` 파일은 기본적으로 Git 추적에서 제외한다.
- Never copy a Draft directly into `analyses/` or `registry/cases.json`. / Draft를 `analyses/`나 `registry/cases.json`에 직접 복사하지 않는다.
- Draft execution uses shared valuation kernels but does **not** imply evidence verification. / Draft 실행은 공통 가치평가 커널을 사용하지만 근거 검증 완료를 의미하지 않는다.
- Any future promotion from Draft to canonical state requires a separate evidence/review workflow. / 향후 Draft→정식 승격은 별도 근거·검토 절차가 필요하다.

## Suggested workflow / 권장 흐름

```bash
mkdir -p workspace/user_cases
vih draft-template equity_fcff > workspace/user_cases/my_company.json
vih draft-validate workspace/user_cases/my_company.json
vih draft-run workspace/user_cases/my_company.json
```

For venture/option-like assets / 벤처·옵션형 자산:

```bash
vih draft-template venture_probability > workspace/user_cases/my_venture.json
vih draft-run workspace/user_cases/my_venture.json
```
