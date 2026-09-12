# M25 Acceptance / M25 완료계약

## Mission / 미션

Govern terminal-growth assumptions on top of the exact reviewed M24 WACC lineage and integrate only reviewed scenario-specific values into `scenario.terminal_growth` without weakening prior cash/debt/share/WACC governance.

정확한 M24 reviewed WACC lineage 위에서 영구성장률 가정을 거버넌스하고, 검토완료된 시나리오별 값만 `scenario.terminal_growth`에 연결하며 기존 cash/debt/share/WACC 거버넌스를 약화하지 않는다.

## Acceptance checklist / 완료 체크리스트

- [x] Terminal growth remains `ASSUMPTION`, never FACT/NORMALIZED_FACT.
- [x] A valid M24 reviewed WACC package is required and independently revalidated.
- [x] Long-run inflation and real-growth anchors are explicit and provenance-locked.
- [x] Missing anchor inputs are never zero-imputed.
- [x] Nominal macro growth ceiling is independently recomputed.
- [x] Stale or Tier-D required anchors cannot reach human review.
- [x] Every scenario has exactly one explicit terminal-growth value and rationale.
- [x] `g > -1` is required.
- [x] `g < reviewed WACC` is required.
- [x] `g <= nominal_growth_anchor` is required.
- [x] Negative reviewed terminal growth is supported.
- [x] Candidate and reviewed assumption authority states are distinct.
- [x] Human review locks candidate/WACC/methodology/as-of/scenario lineage.
- [x] Reviewed package embeds and revalidates candidate + review assertion.
- [x] `draft-binding-proposal-v0.5` accepts only validated v0.4 base proposals.
- [x] M25 requires the exact same WACC package lineage as the v0.4 base.
- [x] v0.5 may replace only `scenario.terminal_growth`.
- [x] `scenario.wacc` and all pre-M25 decisions remain unchanged in v0.5.
- [x] Scenario target set must equal the complete Draft scenario set.
- [x] Terminal-growth-only approval requires reviewed WACC already present in Draft.
- [x] Otherwise WACC must be approved in the same binding approval.
- [x] Applied terminal-growth diff is scenario-by-scenario and lineage-preserving.
- [x] Input Draft remains unchanged; output remains noncanonical.
- [x] Outer SHA re-signing cannot bypass calculation, policy, or projection validation.
- [x] CLI wrapper delegates all pre-M25 commands unchanged.
- [x] Web M25 surfaces are calculate/validate only; no Draft/canonical write path.
- [x] M1-M24 regressions remain required.
- [ ] Final-head Python 3.11 CI success recorded.
- [ ] Final-head Python 3.12 CI success recorded.
- [ ] PR merged from exact tested head SHA.
- [ ] Issue #54 closed as completed.
- [ ] Post-merge `main` Python 3.11/3.12 CI success recorded.

## Merge gate / 병합 게이트

Do not merge if any path can bind terminal growth from a different WACC lineage, apply terminal growth against a Draft carrying another WACC, exceed the reviewed WACC or macro ceiling, silently omit an anchor/scenario, upgrade authority by arithmetic, or bypass nested validation by recomputing only an outer SHA.

다른 WACC lineage의 영구성장률을 바인딩하거나, 다른 WACC가 있는 Draft에 영구성장률을 적용하거나, reviewed WACC/거시 상한을 초과하거나, anchor/시나리오를 암묵적으로 누락하거나, 계산만으로 권위를 승격하거나, outer SHA만 재계산해 중첩검증을 우회할 수 있으면 병합하지 않는다.
