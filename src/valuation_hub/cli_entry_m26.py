"""M26 additive CLI wrapper / M26 추가형 CLI wrapper.

Only integrated-forecast commands and v0.6-aware binding validation are
intercepted. All older commands delegate unchanged to the M25 dispatcher.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from valuation_hub import cli_entry_m25 as prior_cli
from valuation_hub.case_service import CaseServiceError
from valuation_hub.forecast_assumption import (
    build_forecast_candidate,
    build_forecast_review_assertion,
    finalize_reviewed_forecast,
    validate_forecast_candidate,
    validate_forecast_review_assertion,
    validate_reviewed_forecast,
)
from valuation_hub.forecast_draft_binding import (
    build_binding_proposal_with_forecast,
    validate_binding_proposal_any,
)
from valuation_hub.web_forecast import serve as serve_web

FORECAST_COMMANDS = {
    "forecast-candidate-build",
    "forecast-candidate-validate",
    "forecast-review-build",
    "forecast-review-validate",
    "forecast-finalize",
    "forecast-validate",
    "binding-build-with-forecast",
}
INTERCEPT = FORECAST_COMMANDS | {"binding-validate", "web"}


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


def _arr(path: Path, label: str) -> list[dict[str, Any]]:
    value = _load(path, label)
    if not isinstance(value, list) or not value or not all(isinstance(item, dict) for item in value):
        raise CaseServiceError(f"{label} non-empty object array required / {label} 비어있지 않은 객체배열 필요")
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

    command = sub.add_parser("forecast-candidate-build")
    command.add_argument("scenarios", type=Path)
    command.add_argument("--entity-id", required=True)
    command.add_argument("--financial-scope", required=True)
    command.add_argument("--capital-currency", required=True)
    command.add_argument("--as-of", required=True)
    sub.add_parser("forecast-candidate-validate").add_argument("file", type=Path)

    command = sub.add_parser("forecast-review-build")
    command.add_argument("candidate", type=Path)
    command.add_argument("--reviewer", required=True)
    command.add_argument("--approved-at", required=True)
    command.add_argument("--review-basis", required=True)
    command = sub.add_parser("forecast-review-validate")
    command.add_argument("assertion", type=Path)
    command.add_argument("candidate", type=Path)
    command = sub.add_parser("forecast-finalize")
    command.add_argument("candidate", type=Path)
    command.add_argument("assertion", type=Path)
    sub.add_parser("forecast-validate").add_argument("file", type=Path)

    command = sub.add_parser("binding-build-with-forecast")
    command.add_argument("base_proposal", type=Path)
    command.add_argument("forecast_package", type=Path)
    sub.add_parser("binding-validate").add_argument("file", type=Path)

    command = sub.add_parser("web")
    command.add_argument("--host", default="127.0.0.1")
    command.add_argument("--port", type=int, default=8765)
    return parser


def _run(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "forecast-candidate-build":
            _dump(build_forecast_candidate(
                _arr(args.scenarios, "forecast scenarios"),
                entity_id=args.entity_id,
                financial_scope=args.financial_scope,
                capital_currency=args.capital_currency,
                as_of=args.as_of,
            ))
            return 0
        if args.command == "forecast-candidate-validate":
            _dump(validate_forecast_candidate(_obj(args.file, "forecast candidate")))
            return 0
        if args.command == "forecast-review-build":
            _dump(build_forecast_review_assertion(
                _obj(args.candidate, "forecast candidate"),
                reviewer=args.reviewer,
                approved_at=args.approved_at,
                review_basis=args.review_basis,
            ))
            return 0
        if args.command == "forecast-review-validate":
            _dump(validate_forecast_review_assertion(
                _obj(args.assertion, "forecast review assertion"),
                _obj(args.candidate, "forecast candidate"),
            ))
            return 0
        if args.command == "forecast-finalize":
            _dump(finalize_reviewed_forecast(
                _obj(args.candidate, "forecast candidate"),
                _obj(args.assertion, "forecast review assertion"),
            ))
            return 0
        if args.command == "forecast-validate":
            _dump(validate_reviewed_forecast(_obj(args.file, "reviewed forecast package")))
            return 0
        if args.command == "binding-build-with-forecast":
            _dump(build_binding_proposal_with_forecast(
                _obj(args.base_proposal, "v0.5 base binding proposal"),
                _obj(args.forecast_package, "reviewed forecast package"),
            ))
            return 0
        if args.command == "binding-validate":
            _dump(validate_binding_proposal_any(_obj(args.file, "binding proposal")))
            return 0
        if args.command == "web":
            if args.as_json:
                raise CaseServiceError("--json is not valid with web / web 명령은 --json을 지원하지 않습니다")
            serve_web(host=args.host, port=args.port, root=args.root)
            return 0
        raise CaseServiceError("unsupported M26 command / 미지원 M26 명령")
    except (CaseServiceError, ValueError, OSError, KeyError, TypeError) as exc:
        return _error(args, exc)


def main(argv: list[str] | None = None) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    if _command(values) is not None:
        return _run(values)
    return prior_cli.main(values)


if __name__ == "__main__":
    raise SystemExit(main())
