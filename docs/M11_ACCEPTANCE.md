# M11 Acceptance Contract / M11 완료조건

M11 may merge only if all of the following pass in the full Python 3.11/3.12 matrix:

M11은 다음 조건이 Python 3.11/3.12 전체 매트릭스에서 모두 통과할 때만 병합한다.

1. Both reviewed-Draft adapters preserve reviewed economics through the shared kernels. / 두 reviewed-Draft adapter가 검토 경제값을 공통커널에서 그대로 보존한다.
2. M11 admission is deterministic for identical M10 packages. / 동일 M10 package의 M11 수용 bundle이 결정론적이다.
3. `valuation_as_of` comes from governed market-price evidence and malformed/conflicting dates fail closed. / 기준일은 시장가격 근거에서 도출되며 오류·충돌 날짜는 차단한다.
4. v0.1 canonical scenario profiles are enforced only at admission, not at generic Draft/M10 staging. / v0.1 정식 시나리오 프로파일은 수용 단계에서만 강제한다.
5. A temporary admitted repository passes `validate_case → run_case → evidence_view → preview_case → Web render`. / 임시 정식 저장소가 전체 read/preview/Web 경로를 통과한다.
6. `SOURCE_PACKAGE`, candidate/review hashes, reviewed Draft, evidence/governance, adapter/model, and stored runtime form one validated provenance chain. / 원천 package부터 stored runtime까지 하나의 검증 출처 체인을 구성한다.
7. Any canonical evidence or reviewed-economics drift fails closed. / 정식 근거·검토 경제값 drift는 fail-closed한다.
8. Existing LS ELECTRIC, LS Eco Energy, and Jet.AI reference routes remain executable without adapters. / 기존 3개 reference 사례는 adapter 없이 기존 경로를 유지한다.
9. CLI and Web admission interfaces reuse `admission.py` and do not write canonical repository state. / CLI·Web은 공통 admission 서비스를 사용하고 정식 저장소를 기록하지 않는다.
10. Current canonical registry/evidence/results remain byte-identical throughout M11 builder tests. / M11 builder 테스트 동안 현재 정식 bytes가 불변이다.

A successful M11 merge enables reviewed-Draft canonical execution capability, but it does not automatically admit any user case. Each future case still requires its own reviewed package, admission artifacts, PR, CI, human review, and merge.

M11 병합은 검토 Draft를 정식 실행할 수 있는 capability를 추가할 뿐 사용자 사례를 자동 수용하지 않는다. 향후 각 사례는 개별 검토 package, admission 산출물, PR, CI, 인간 검토, 병합을 거쳐야 한다.
