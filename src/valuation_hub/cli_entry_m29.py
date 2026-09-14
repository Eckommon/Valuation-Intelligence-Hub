"""M29 additive CLI wrapper / M29 추가형 CLI wrapper."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from valuation_hub import cli_entry_m28 as prior_cli
from valuation_hub.admission_apply_m29 import build_repository_change_plan, validate_repository_change_plan
from valuation_hub.admission_m29 import build_admission_bundle, validate_admission_bundle
from valuation_hub.case_service import CaseServiceError
from valuation_hub.promotion_m29 import (
    assess_candidate,
    build_complete_equity_candidate,
    build_evidence_catalog_claim,
    promotion_check,
    validate_candidate,
)
from valuation_hub.web_complete_equity_handoff import serve as serve_web

INTERCEPT = {
    "complete-handoff-catalog-claim",
    "complete-handoff-build",
    "complete-handoff-assess",
    "candidate-validate",
    "promotion-check",
    "admission-build",
    "admission-validate",
    "admission-plan",
    "admission-plan-validate",
    "web",
}


def _dump(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _load(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CaseServiceError(f"{label} file not found / {label} 파일 없음: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise CaseServiceError(f"{label} read failed / {label} 읽기 실패: {path}") from exc


def _obj(path: Path, label: str) -> dict[str, Any]:
    value = _load(path, label)
    if not isinstance(value, dict):
        raise CaseServiceError(f"{label} JSON object required / {label} JSON 객체 필요")
    return value


def _array(path: Path, label: str) -> list[dict[str, Any]]:
    value = _load(path, label)
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise CaseServiceError(f"{label} JSON object array required / {label} JSON 객체 배열 필요")
    return value


def _command(argv: list[str]) -> str | None:
    return next((item for item in argv if item in INTERCEPT), None)


def _error(args: Any, exc: Exception) -> int:
    if getattr(args, "as_json", False):
        _dump({"ok": False, "error": str(exc)})
    else:
        print(f"ERROR / 오류: {exc}", file=sys.stderr)
    return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vih")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--json", action="store_true", dest="as_json")
    sub = parser.add_subparsers(dest="command", required=True)

    command = sub.add_parser("complete-handoff-catalog-claim")
    command.add_argument("bound_result", type=Path)
    command.add_argument("--field", required=True)
    command.add_argument("--claim-id", required=True)
    command.add_argument("--metric", required=True)
    command.add_argument("--publisher", required=True)
    command.add_argument("--locator", required=True)
    command.add_argument("--tier", required=True, choices=("A", "B", "C"))
    command.add_argument("--source-type", default=None)
    command.add_argument("--source-date", default=None)

    command = sub.add_parser("complete-handoff-build")
    command.add_argument("bound_result", type=Path)
    command.add_argument("catalog", type=Path)
    sub.add_parser("complete-handoff-assess").add_argument("file", type=Path)
    sub.add_parser("candidate-validate").add_argument("file", type=Path)
    sub.add_parser("promotion-check").add_argument("file", type=Path)
    sub.add_parser("admission-build").add_argument("file", type=Path)
    sub.add_parser("admission-validate").add_argument("file", type=Path)

    command = sub.add_parser("admission-plan")
    command.add_argument("admission", type=Path)
    command.add_argument("--target-repo", type=Path, required=True)
    command = sub.add_parser("admission-plan-validate")
    command.add_argument("plan", type=Path)
    command.add_argument("admission", type=Path)
    command.add_argument("--target-repo", type=Path, required=True)

    command = sub.add_parser("web")
    command.add_argument("--host", default="127.0.0.1")
    command.add_argument("--port", type=int, default=8765)
    return parser


def _run(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "complete-handoff-catalog-claim":
            _dump(build_evidence_catalog_claim(
                _obj(args.bound_result, "M28 bound result"),
                field=args.field,
                claim_id=args.claim_id,
                metric=args.metric,
                publisher=args.publisher,
                locator=args.locator,
                tier=args.tier,
                source_type=args.source_type,
                source_date=args.source_date,
            )); return 0
        if args.command == "complete-handoff-build":
            _dump(build_complete_equity_candidate(
                _obj(args.bound_result, "M28 bound result"),
                _array(args.catalog, "M29 evidence catalog"),
            )); return 0
        if args.command == "complete-handoff-assess":
            _dump(assess_candidate(_obj(args.file, "promotion candidate"))); return 0
        if args.command == "candidate-validate":
            _dump(validate_candidate(_obj(args.file, "promotion candidate"))); return 0
        if args.command == "promotion-check":
            _dump(promotion_check(_obj(args.file, "promotion candidate"))); return 0
        if args.command == "admission-build":
            _dump(build_admission_bundle(_obj(args.file, "promotion package"), args.root)); return 0
        if args.command == "admission-validate":
            _dump(validate_admission_bundle(_obj(args.file, "admission bundle"), args.root)); return 0
        if args.command == "admission-plan":
            _dump(build_repository_change_plan(_obj(args.admission, "admission bundle"), args.target_repo)); return 0
        if args.command == "admission-plan-validate":
            _dump(validate_repository_change_plan(
                _obj(args.plan, "repository change plan"),
                _obj(args.admission, "admission bundle"),
                args.target_repo,
            )); return 0
        if args.command == "web":
            if args.as_json:
                raise CaseServiceError("--json is not valid with web / web 명령은 --json을 지원하지 않습니다")
            serve_web(host=args.host, port=args.port, root=args.root); return 0
        raise CaseServiceError("unsupported M29 command / 미지원 M29 명령")
    except (CaseServiceError, ValueError, OSError, KeyError, TypeError) as exc:
        return _error(args, exc)


def main(argv: list[str] | None = None) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    if _command(values) is not None:
        return _run(values)
    return prior_cli.main(values)


if __name__ == "__main__":
    raise SystemExit(main())
