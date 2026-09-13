# Complete Governed Equity Handoff / 완전 거버넌스 Equity 인계

## Purpose / 목적

M29 connects a **complete, human-approved M28 v0.8 bound equity-FCFF Draft** to the existing promotion, admission, and guarded repository-change pipeline without rebuilding governance for the 13 material fields.

M29는 **완전한 인간승인 M28 v0.8 equity-FCFF bound Draft**를 13개 중요필드의 거버넌스를 다시 만들지 않고 기존 승격·수용·guarded 저장소 변경 흐름으로 연결한다.

```text
complete M28 bound Draft result
        ↓
promotion-candidate-v0.2
        ↓
M10 promotion package
        ↓
M29 admission dispatcher → M11 canonical admission contract
        ↓
M29 repository-plan dispatcher → M12 guarded change-plan contract
        ↓
separate admission/* PR + CI + human review + merge
        ↓
CANONICAL
```

M29 does **not** make a bound Draft canonical and does not bypass the historical M9–M12 controls.

M29는 bound Draft를 자동으로 정식화하지 않으며 기존 M9–M12 통제를 우회하지 않는다.

## Complete-result gate / 완전 결과 게이트

The source must independently validate as an M28 `bound-draft-result-v0.1` whose embedded proposal is exactly `draft-binding-proposal-v0.8`. M29 accepts it only when all of the following are true:

M29는 원천 결과가 M28 `bound-draft-result-v0.1`로 독립 검증되고 내부 proposal이 정확히 `draft-binding-proposal-v0.8`인 경우에만 진행한다. 다음 조건을 모두 만족해야 한다.

- all 13 material fields are `DIRECT_BIND` / 13개 중요필드 모두 `DIRECT_BIND`
- human approval covers exactly all 13 fields / 인간승인이 정확히 13개 필드를 포함
- `applied_diffs` contains every field exactly once / 모든 필드의 applied diff가 정확히 1회 존재
- `unresolved_binding_matrix == []`
- `draft_after` is a valid `equity_fcff` Draft
- proposal, approval, before/after, applied-diff, and result SHA lineage revalidates

Partial approval, duplicate or missing diff entries, stale or tampered lineage, an older proposal version, or an unresolved material field fails closed.

부분승인·중복/누락 diff·오염된 lineage·구버전 proposal·미해결 중요필드는 fail-closed 처리한다.

## Authority inheritance / 권위 상속

M29 inherits authority from the completed M20–M28 binding chain. It must not relabel governed derived values as observed facts.

M29는 M20–M28에서 완성된 바인딩 체인의 권위를 상속한다. 거버넌스된 파생값을 관측 FACT로 재분류해서는 안 된다.

| Material input / 중요입력 | M29 class / 권위 class |
|---|---|
| `market_price` | `FACT` |
| `equity.cash` | `NORMALIZED_FACT` |
| `equity.minority_interest` | `NORMALIZED_FACT` |
| `equity.debt` | `DERIVED` |
| `equity.diluted_shares` | `DERIVED` |
| WACC paths | `ASSUMPTION` |
| terminal-growth paths | `ASSUMPTION` |
| six forecast-input paths | `ASSUMPTION` |

In particular, `equity.debt` and `equity.diluted_shares` must never be silently upgraded to `FACT` or `NORMALIZED_FACT`.

특히 `equity.debt`와 `equity.diluted_shares`는 `FACT` 또는 `NORMALIZED_FACT`로 조용히 승격될 수 없다.

## Observed evidence catalog / 관측근거 catalog

The complete M28 result already preserves binding authority and SHA lineage, but some early binding contexts do not retain every descriptive field required by the historical M9 evidence interface. M29 therefore accepts a small explicit catalog for **exactly five observed material fields**.

완전 M28 결과는 바인딩 권위와 SHA lineage를 보존하지만 일부 초기 바인딩 context는 역사적 M9 근거 인터페이스가 요구하는 모든 설명 메타데이터를 보존하지 않는다. 따라서 M29는 **정확히 5개 관측 중요필드**에 한해 명시적 catalog를 받는다.

Each catalog claim must contain an M9-compatible claim ID, metric, value, status, publisher, locator, source tier, and exact binding lineage. The catalog can supplement descriptive provenance only; it cannot alter the bound numeric value, authority class, valuation `as_of`, proposal decision, applied diff, or SHA lineage.

각 claim은 M9 호환 claim ID·metric·값·상태·publisher·locator·source tier·정확한 binding lineage를 포함해야 한다. Catalog는 설명적 provenance만 보완할 수 있으며 bound 숫자값·권위 class·가치평가일·proposal decision·applied diff·SHA lineage를 변경할 수 없다.

Tier D is forbidden for all five observed fields, including `DERIVED` debt and diluted shares. Only source tiers A/B/C may pass the M29 observed-evidence gate.

Tier D는 `DERIVED` debt와 diluted shares를 포함한 5개 관측필드 모두에서 금지된다. M29 관측근거 게이트는 A/B/C source tier만 허용한다.

## Deterministic governance projection / 결정론적 거버넌스 투영

`promotion-candidate-v0.2` stores the **exact M28 `draft_after`** as its `draft`. Material numeric paths are enumerated through the historical M9 material-path logic, so M29 does not invent a second path taxonomy.

`promotion-candidate-v0.2`의 `draft`는 **정확한 M28 `draft_after`**이다. 중요 숫자 path는 역사적 M9 material-path 로직으로 열거하므로 M29가 별도 path 분류체계를 만들지 않는다.

Every material numeric path is projected exactly once:

- five observed fields receive their inherited class and one catalog claim link;
- WACC, terminal growth, and forecast numeric paths remain `ASSUMPTION` with the governed decision rationale;
- structural forecast `year` values are not material numeric inputs;
- no material numeric path may remain `UNKNOWN`.

모든 중요 숫자 path는 정확히 한 번 투영되며 `UNKNOWN`이 남을 수 없다.

## Independent revalidation and review lock / 독립 재검증 및 검토 잠금

A v0.2 candidate embeds the full source bound result and its SHA. Validation reconstructs the complete-result gate, observed catalog, material-path projection, and lineage rather than trusting outer fields.

v0.2 candidate는 전체 source bound result와 SHA를 내장한다. 검증기는 외부 필드를 신뢰하지 않고 완전결과 게이트·관측 catalog·material-path 투영·lineage를 재구축한다.

Human promotion review remains explicit. `APPROVE`, reviewer identity, rationale, timezone-aware review time, and the exact `review_scope_sha256` are required. The scope hash covers the Draft, input governance, evidence catalog, embedded source result, and source-result SHA. Re-signing an outer object cannot legitimize nested tampering.

인간 승격 검토는 계속 명시적이다. `APPROVE`·reviewer·rationale·시간대가 포함된 검토시각·정확한 `review_scope_sha256`이 필요하며, outer object 재서명으로 nested tampering을 정당화할 수 없다.

## M10–M12 compatibility / M10–M12 호환

Historical `promotion-candidate-v0.1` behavior is delegated unchanged. M10 promotion-package semantics remain `promotion-package-v0.1`; its promotion check now dispatches to v0.1 or v0.2 candidate validation as appropriate.

역사적 `promotion-candidate-v0.1` 동작은 그대로 위임된다. M10 promotion package 자체의 의미는 `promotion-package-v0.1`로 유지되고 promotion check만 candidate 버전에 따라 v0.1/v0.2 검증기로 분기한다.

For v0.2 admission, two views are deliberately separated:

```text
SOURCE_PACKAGE.json
  = exact reviewed M29 package
  = exact raw M28 draft_after preserved
  = complete governance and lineage preserved

case_inputs.json
  = deterministic normalized view of the same Draft
  = canonical adapter compatibility only
```

The historical canonical equity adapter requires the `BEAR / BASE / BULL` profile. M29 does not weaken that contract and does not mutate the source candidate to satisfy it; it uses the existing deterministic reviewed-Draft normalization for canonical artifacts.

역사적 canonical equity adapter의 `BEAR / BASE / BULL` 요구조건을 낮추지 않는다. 이를 위해 source candidate를 변조하지 않고 동일 Draft의 기존 결정론적 reviewed-Draft 정규화를 canonical 산출물에만 사용한다.

The M29 repository-plan dispatcher reuses M12 branch, registry-baseline, collision, artifact-hash, and deterministic-plan controls. Actual file application remains a separate governed `admission/*` operation.

M29 repository-plan dispatcher는 M12의 branch·registry baseline·충돌·artifact hash·결정론적 plan 통제를 그대로 재사용하며, 실제 파일 적용은 별도 거버넌스 `admission/*` 작업으로 남는다.

## Interfaces / 인터페이스

CLI entrypoint: `valuation_hub.cli_entry_m29:main`.

M29 adds complete-handoff build/assess/validation commands and v0.2-aware admission-plan dispatch while delegating all predecessor commands through M28 and earlier wrappers.

Web Lab:

```text
/equity-handoff
/api/equity-handoff/catalog-claim
/api/equity-handoff/build
/api/equity-handoff/assess
/api/equity-handoff/validate
/api/equity-handoff/check
```

The Web surface is preparation and validation only:

```text
NO AUTO APPROVAL
NO FILE WRITE
NO ADMISSION APPLY
NO CANONICAL WRITE
```

## Security and governance invariants / 보안·거버넌스 불변조건

M29 must fail closed on authority relabeling, Tier-D observed evidence, partial approval, missing or duplicate material-field diffs, path-coverage drift, nested source-result tampering, review-scope drift, canonical-adapter incompatibility, registry-baseline drift, target collision, or attempt to bypass the separate repository-governed admission flow.

M29는 권위 재라벨링·Tier-D 관측근거·부분승인·중요필드 diff 누락/중복·path coverage drift·nested source-result 변조·review-scope drift·canonical adapter 불일치·registry baseline drift·대상 충돌·별도 repository-governed admission 우회에 대해 fail-closed 해야 한다.
