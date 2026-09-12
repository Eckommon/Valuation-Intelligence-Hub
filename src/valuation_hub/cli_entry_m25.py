"""M25 additive CLI wrapper / M25 추가형 CLI wrapper.

Only M25 commands and v0.5-aware binding validation are intercepted. All older
commands delegate unchanged to the M24 dispatcher.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from valuation_hub import cli_entry_m24 as prior_cli
from valuation_hub.case_service import CaseServiceError
from valuation_hub.terminal_growth_assumption import (
    REQUIRED_ANCHORS,
    SOURCE_CLAIM_CLASSES,
    SOURCE_TIERS,
    build_terminal_growth_anchor_input,
    build_terminal_growth_candidate,
    build_terminal_growth_review_assertion,
    finalize_reviewed_terminal_growth,
    validate_reviewed_terminal_growth,
    validate_terminal_growth_anchor_input,
    validate_terminal_growth_candidate,
    validate_terminal_growth_review_assertion,
)
from valuation_hub.terminal_growth_draft_binding import (
    build_binding_proposal_with_terminal_growth,
    validate_binding_proposal_any,
)
from valuation_hub.web_terminal_growth import serve as serve_web

TERMINAL_GROWTH_COMMANDS = {
    "terminal-growth-anchor-build",
    "terminal-growth-anchor-validate",
    "terminal-growth-candidate-build",
    "terminal-growth-candidate-validate",
    "terminal-growth-review-build",
    "terminal-growth-review-validate",
    "terminal-growth-finalize",
    "terminal-growth-validate",
    "binding-build-with-terminal-growth",
}
INTERCEPT = TERMINAL_GROWTH_COMMANDS | {"binding-validate", "web"}


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

    command = sub.add_parser("terminal-growth-anchor-build")
    command.add_argument("--metric", required=True, choices=REQUIRED_ANCHORS)
    command.add_argument("--value", required=True, type=float)
    command.add_argument("--observed-on", required=True)
    command.add_argument("--claim-class", required=True, choices=SOURCE_CLAIM_CLASSES)
    command.add_argument("--source-publisher", required=True)
    command.add_argument("--source-type", required=True)
    command.add_argument("--source-tier", required=True, choices=SOURCE_TIERS)
    command.add_argument("--source-locator", required=True)
    command.add_argument("--source-sha256", required=True)
    sub.add_parser("terminal-growth-anchor-validate").add_argument("file", type=Path)

    command = sub.add_parser("terminal-growth-candidate-build")
    command.add_argument("anchors", type=Path)
    command.add_argument("wacc_package", type=Path)
    command.add_argument("scenario_assumptions", type=Path)
    sub.add_parser("terminal-growth-candidate-validate").add_argument("file", type=Path)

    command = sub.add_parser("terminal-growth-review-build")
    command.add_argument("candidate", type=Path)
    command.add_argument("--reviewer", required=True)
    command.add_argument("--approved-at", required=True)
    command.add_argument("--review-basis", required=True)
    command = sub.add_parser("terminal-growth-review-validate")
    command.add_argument("assertion", type=Path)
    command.add_argument("candidate", type=Path)
    command = sub.add_parser("terminal-growth-finalize")
    command.add_argument("candidate", type=Path)
    command.add_argument("assertion", type=Path)
    sub.add_parser("terminal-growth-validate").add_argument("file", type=Path)

    command = sub.add_parser("binding-build-with-terminal-growth")
    command.add_argument("base_proposal", type=Path)
    command.add_argument("terminal_growth_package", type=Path)
    sub.add_parser("binding-validate").add_argument("file", type=Path)

    command = sub.add_parser("web")
    command.add_argument("--host", default="127.0.0.1")
    command.add_argument("--port", type=int, default=8765)
    return parser


def _run(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "terminal-growth-anchor-build":
            _dump(build_terminal_growth_anchor_input(
                metric=args.metric,
                value=args.value,
                observed_on=args.observed_on,
                claim_class=args.claim_class,
                source_publisher=args.source_publisher,
                source_type=args.source_type,
                source_tier=args.source_tier,
                source_locator=args.source_locator,
                source_sha256=args.source_sha256,
            ))
            return 0
        if args.command == "terminal-growth-anchor-validate":
            _dump(validate_terminal_growth_anchor_input(_obj(args.file, "terminal-growth anchor input")))
            return 0
        if args.command == "terminal-growth-candidate-build":
            _dump(build_terminal_growth_candidate(
                _arr(args.anchors, "terminal-growth anchors"),
                _obj(args.wacc_package, "reviewed WACC package"),
                scenario_assumptions=_arr(args.scenario_assumptions, "terminal-growth scenario assumptions"),
            ))
            return 0
        if args.command == "terminal-growth-candidate-validate":
            _dump(validate_terminal_growth_candidate(_obj(args.file, "terminal-growth candidate")))
            return 0
        if args.command == "terminal-growth-review-build":
            _dump(build_terminal_growth_review_assertion(
                _obj(args.candidate, "terminal-growth candidate"),
                reviewer=args.reviewer,
                approved_at=args.approved_at,
                review_basis=args.review_basis,
            ))
            return 0
        if args.command == "terminal-growth-review-validate":
            _dump(validate_terminal_growth_review_assertion(
                _obj(args.assertion, "terminal-growth review assertion"),
                _obj(args.candidate, "terminal-growth candidate"),
            ))
            return 0
        if args.command == "terminal-growth-finalize":
            _dump(finalize_reviewed_terminal_growth(
                _obj(args.candidate, "terminal-growth candidate"),
                _obj(args.assertion, "terminal-growth review assertion"),
            ))
            return 0
        if args.command == "terminal-growth-validate":
            _dump(validate_reviewed_terminal_growth(_obj(args.file, "reviewed terminal-growth package")))
            return 0
        if args.command == "binding-build-with-terminal-growth":
            _dump(build_binding_proposal_with_terminal_growth(
                _obj(args.base_proposal, "v0.4 base binding proposal"),
                _obj(args.terminal_growth_package, "reviewed terminal-growth package"),
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
        raise CaseServiceError("unsupported M25 command / 미지원 M25 명령")
    except (CaseServiceError, ValueError, OSError) as exc:
        return _error(args, exc)


def main(argv: list[str] | None = None) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    if _command(values) is not None:
        return _run(values)
    return prior_cli.main(values)


if __name__ == "__main__":
    raise SystemExit(main())
