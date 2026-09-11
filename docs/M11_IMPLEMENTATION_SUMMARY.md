# M11 Implementation Summary / M11 구현 요약

M11 introduces a versioned canonical admission path for reviewed M10 packages while preserving legacy reference routes.

- adapters: `reviewed-draft-equity-fcff-v0.1`, `reviewed-draft-venture-probability-v0.1`
- admission service: deterministic proposed canonical artifacts, no repository mutation
- case service: adapter-aware validation, package/review/evidence/runtime provenance chain
- interactive service: reviewed-Draft preview using absolute economics
- CLI: `admission-build`, `admission-validate`
- Web: `/admission`, `/api/admission/build`, `/api/admission/validate`
- tests: deterministic admission, profile gate, market-date gate, temporary-repository E2E, tamper detection, legacy regression, CLI/Web integration, canonical-byte immutability

M11 does not auto-admit any user case. Future case admission remains a separate reviewed repository PR.

M11은 사용자의 어떤 사례도 자동 정식화하지 않는다. 향후 사례 수용은 각각 별도 인간 검토 저장소 PR을 요구한다.
