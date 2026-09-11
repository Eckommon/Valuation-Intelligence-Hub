"""Valuation Intelligence Hub CLI / 가치분석 Hub CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from valuation_hub.admission import build_admission_bundle, validate_admission_bundle
from valuation_hub.case_service import (
    CaseServiceError,
    list_cases,
    read_report,
    run_case,
    validate_case,
)
from valuation_hub.draft_service import load_draft_file, run_draft, template, validate_draft
from valuation_hub.promotion import (
    build_candidate,
    load_candidate_file,
    promotion_check,
    validate_candidate,
)
from valuation_hub.promotion_package import (
    build_promotion_package,
    load_package_file,
    materialize_promotion_package,
    validate_materialized_package,
    validate_promotion_package,
)
from valuation_hub.web_admission import serve as serve_web


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vih",
        description="Valuation Intelligence Hub / 가치분석 인텔리전스 Hub",
    )
    parser.add_argument("--root", type=Path, default=None, help="Repository root / 저장소 루트")
    parser.add_argument("--json", action="store_true", dest="as_json", help="JSON output / JSON 출력")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List registered cases / 등록 사례 목록")
    for command, help_text in (
        ("validate", "Validate a canonical case / 정식 사례 검증"),
        ("run", "Run a canonical case / 정식 사례 실행"),
        ("report", "Print canonical report / 정식 보고서 출력"),
    ):
        p = sub.add_parser(command, help=help_text)
        p.add_argument("case_id")

    draft_template = sub.add_parser("draft-template", help="Print a user Draft template / 사용자 Draft 템플릿 출력")
    draft_template.add_argument("model", choices=("equity_fcff", "venture_probability"))
    draft_validate = sub.add_parser("draft-validate", help="Validate a user Draft JSON file / 사용자 Draft JSON 검증")
    draft_validate.add_argument("file", type=Path)
    draft_run = sub.add_parser("draft-run", help="Run a user Draft JSON file / 사용자 Draft JSON 실행")
    draft_run.add_argument("file", type=Path)

    candidate_build = sub.add_parser("candidate-build", help="Build a review candidate from Draft JSON / Draft에서 검토 Candidate 생성")
    candidate_build.add_argument("file", type=Path)
    candidate_validate = sub.add_parser("candidate-validate", help="Validate evidence-governed candidate / 근거 거버넌스 Candidate 검증")
    candidate_validate.add_argument("file", type=Path)
    promotion = sub.add_parser("promotion-check", help="Verify reviewed PR readiness / 인간검토 PR 준비 확인")
    promotion.add_argument("file", type=Path)

    package_build = sub.add_parser("package-build", help="Build deterministic reviewed promotion package / 검토 완료 승격 패키지 생성")
    package_build.add_argument("file", type=Path, help="Approved candidate JSON / 승인 Candidate JSON")
    package_build.add_argument("--case-id", required=True)
    package_build.add_argument("--name-en", required=True)
    package_build.add_argument("--name-ko", required=True)
    package_build.add_argument("--asset-class", required=True)
    package_build.add_argument("--output-dir", type=Path, default=None, help="Optional explicit materialization directory / 선택적 명시 출력 디렉터리")
    package_validate = sub.add_parser("package-validate", help="Validate package JSON or materialized directory / 패키지 JSON·materialized 디렉터리 검증")
    package_validate.add_argument("path", type=Path)

    admission_build = sub.add_parser("admission-build", help="Build proposed canonical admission bundle from M10 package / M10 패키지에서 정식 수용 bundle 생성")
    admission_build.add_argument("file", type=Path, help="M10 package JSON / M10 패키지 JSON")
    admission_validate = sub.add_parser("admission-validate", help="Validate proposed canonical admission bundle / 정식 수용 제안 bundle 검증")
    admission_validate.add_argument("file", type=Path)

    web = sub.add_parser("web", help="Run local Web application / 로컬 Web 앱 실행")
    web.add_argument("--host", default="127.0.0.1", help="Bind host / 바인드 호스트")
    web.add_argument("--port", type=int, default=8765, help="Bind port / 바인드 포트")
    return parser


def _dump(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CaseServiceError(f"{label} file not found / {label} 파일 없음: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CaseServiceError(f"invalid {label} JSON / {label} JSON 오류: {exc}") from exc
    if not isinstance(payload, dict):
        raise CaseServiceError(f"{label} must be a JSON object / {label}는 JSON 객체여야 합니다")
    return payload


def _human_list(cases: list[dict[str, Any]]) -> None:
    print("Registered valuation cases / 등록 가치평가 사례")
    for item in cases:
        adapter = item.get("adapter")
        suffix = f" | {adapter}" if adapter else ""
        print(
            f"- {item['case_id']} | {item['display_name_en']} / {item['display_name_ko']} "
            f"| {item['model']}{suffix}"
        )


def _human_validate(result: dict[str, Any]) -> None:
    print(f"PASS / 통과: {result['case_id']}")
    print(f"Model / 모델: {result['model']} ({result['model_version']})")
    if result.get("adapter"):
        print(f"Adapter / 어댑터: {result['adapter']}")
    print(f"Evidence gate / 근거 게이트: {result['promotion_gate']}")


def _human_run(result: dict[str, Any]) -> None:
    print(f"Case / 사례: {result['case_id']}")
    print(f"As of / 기준일: {result['valuation_as_of']}")
    print(f"Market price / 시장가격: {result['market_price']}")
    print(f"Grounded / 저장소 근거화: {result['grounded']}")
    runtime = result["runtime"]
    if result["model"] == "equity_fcff":
        for name in ("BEAR", "BASE", "BULL"):
            print(f"{name}: value/share = {runtime[name]['value_per_share']:.2f}")
    else:
        print(
            "Probability-weighted present value/share / 확률가중 현재 주당가치: "
            f"{runtime['expected_present_value_per_share']:.4f}"
        )
        for name, item in runtime["scenarios"].items():
            print(
                f"{name}: p={item['probability']:.2%}, "
                f"PV/share={item['present_value_per_share']:.4f}"
            )


def _human_draft_validate(result: dict[str, Any]) -> None:
    print("PASS DRAFT / Draft 검증 통과")
    print(f"Name / 이름: {result['name']}")
    print(f"Model / 모델: {result['model']}")
    print("Status / 상태: DRAFT_USER_SUPPLIED / NOT_CANONICAL")
    print("Evidence / 근거: USER_SUPPLIED_UNVERIFIED / 사용자 제공·미검증")


def _human_draft_run(result: dict[str, Any]) -> None:
    print("DRAFT RESULT / Draft 결과 — NOT CANONICAL / 정식 아님")
    print(f"Name / 이름: {result['name']}")
    print(f"Model / 모델: {result['model']}")
    print(f"Market price / 시장가격: {result['market_price']}")
    print(result["warning_ko"])
    runtime = result["runtime"]
    if result["model"] == "equity_fcff":
        for name, item in runtime["scenarios"].items():
            print(f"{name}: value/share = {item['value_per_share']:.4f}")
    else:
        print(f"Expected PV/share / 기대 현재 주당가치: {runtime['expected_present_value_per_share']:.4f}")
        for name, item in runtime["scenarios"].items():
            print(f"{name}: p={item['probability']:.2%}, PV/share={item['present_value_per_share']:.4f}")


def _human_candidate_validate(result: dict[str, Any]) -> None:
    print("PASS CANDIDATE / Candidate 검토게이트 통과")
    print(f"Material inputs / 중요 입력: {result['material_input_count']}")
    print(f"Evidence records / 근거 레코드: {result['evidence_count']}")
    print(f"Review scope SHA-256 / 검토범위 해시: {result['review_scope_sha256']}")
    print("Next / 다음: perform explicit human review and copy this exact hash into review.scope_sha256.")


def _human_promotion(result: dict[str, Any]) -> None:
    print(result["status"])
    print("CANONICAL / 정식: FALSE")
    print(f"Reviewer / 검토자: {result['reviewer']}")
    print(f"Review scope SHA-256 / 검토범위 해시: {result['review_scope_sha256']}")
    print(result["next_action_ko"])


def _human_package(result: dict[str, Any]) -> None:
    print(result["status"])
    print("CANONICAL / 정식: FALSE")
    print(f"Case ID / 사례 ID: {result['case_id']}")
    print(f"Package SHA-256 / 패키지 SHA-256: {result['package_sha256']}")
    print(f"Canonical adapter / 정식 adapter: {result['required_canonical_adapter']}")
    if result.get("materialized"):
        print(f"Output / 출력: {result['output_dir']}")
    print(result["next_action_ko"])


def _human_admission(result: dict[str, Any]) -> None:
    print(result["status"])
    print("BUNDLE CANONICAL / bundle 정식: FALSE")
    print(f"Case ID / 사례 ID: {result['case_id']}")
    print(f"Adapter / 어댑터: {result['adapter']}")
    print(f"Valuation as of / 기준일: {result['valuation_as_of']}")
    print(f"Admission bundle SHA-256 / 수용 bundle SHA-256: {result['bundle_sha256']}")
    print(result["next_action_ko"])


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "list":
            result = list_cases(args.root)
            _dump(result) if args.as_json else _human_list(result)
            return 0
        if args.command == "validate":
            result = validate_case(args.case_id, args.root)
            _dump(result) if args.as_json else _human_validate(result)
            return 0
        if args.command == "run":
            result = run_case(args.case_id, args.root)
            _dump(result) if args.as_json else _human_run(result)
            return 0
        if args.command == "report":
            report = read_report(args.case_id, args.root)
            _dump({"case_id": args.case_id, "report": report}) if args.as_json else print(report)
            return 0
        if args.command == "draft-template":
            _dump(template(args.model, args.root))
            return 0
        if args.command == "draft-validate":
            result = validate_draft(load_draft_file(args.file))
            _dump(result) if args.as_json else _human_draft_validate(result)
            return 0
        if args.command == "draft-run":
            result = run_draft(load_draft_file(args.file))
            _dump(result) if args.as_json else _human_draft_run(result)
            return 0
        if args.command == "candidate-build":
            result = build_candidate(load_draft_file(args.file))
            _dump(result)
            return 0
        if args.command == "candidate-validate":
            result = validate_candidate(load_candidate_file(args.file))
            _dump(result) if args.as_json else _human_candidate_validate(result)
            return 0
        if args.command == "promotion-check":
            result = promotion_check(load_candidate_file(args.file))
            _dump(result) if args.as_json else _human_promotion(result)
            return 0
        if args.command == "package-build":
            package = build_promotion_package(
                load_candidate_file(args.file),
                case_id=args.case_id,
                display_name_en=args.name_en,
                display_name_ko=args.name_ko,
                asset_class=args.asset_class,
                root=args.root,
            )
            if args.output_dir is None:
                _dump(package)
            else:
                result = materialize_promotion_package(package, args.output_dir, args.root)
                _dump(result) if args.as_json else _human_package(result)
            return 0
        if args.command == "package-validate":
            if args.path.is_dir():
                result = validate_materialized_package(args.path, args.root)
            else:
                result = validate_promotion_package(load_package_file(args.path), args.root)
            _dump(result) if args.as_json else _human_package(result)
            return 0
        if args.command == "admission-build":
            package = _load_json_object(args.file, "promotion package")
            _dump(build_admission_bundle(package, args.root))
            return 0
        if args.command == "admission-validate":
            bundle = _load_json_object(args.file, "admission bundle")
            result = validate_admission_bundle(bundle, args.root)
            _dump(result) if args.as_json else _human_admission(result)
            return 0
        if args.command == "web":
            if args.as_json:
                raise CaseServiceError("--json is not valid with web / web 명령은 --json을 지원하지 않습니다")
            serve_web(host=args.host, port=args.port, root=args.root)
            return 0
        raise CaseServiceError(f"unsupported command / 미지원 명령: {args.command}")
    except (CaseServiceError, ValueError, OSError) as exc:
        if args.as_json:
            _dump({"ok": False, "error": str(exc)})
        else:
            print(f"ERROR / 오류: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
