"""Stable CLI entry dispatcher / 안정적 CLI 진입 dispatcher.

M14 keeps the mature M1-M13 parser untouched. New OpenDART commands and the
extended Web server are intercepted here; every existing command delegates to
`valuation_hub.cli.main` unchanged.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from valuation_hub import cli as legacy_cli
from valuation_hub.case_service import CaseServiceError
from valuation_hub.dart_live import (
    DART_METRIC_SPECS,
    capture_dart_snapshot,
    extract_dart_evidence_candidate,
    load_dart_snapshot,
    materialize_dart_snapshot,
    validate_dart_snapshot,
)
from valuation_hub.web_sources import serve as serve_web

DART_COMMANDS = {"dart-fetch", "dart-snapshot-validate", "dart-extract"}


def _dump(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _command(argv: list[str]) -> str | None:
    known = DART_COMMANDS | {"web"}
    for token in argv:
        if token in known:
            return token
    return None


def _dart_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vih")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--json", action="store_true", dest="as_json")
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("dart-fetch", help="Fetch OpenDART financial statements into immutable noncanonical snapshot")
    fetch.add_argument("corp_code")
    fetch.add_argument("--bsns-year", required=True)
    fetch.add_argument("--reprt-code", required=True, choices=("11013", "11012", "11014", "11011"))
    fetch.add_argument("--fs-div", required=True, choices=("CFS", "OFS"))
    fetch.add_argument("--api-key", required=True)
    fetch.add_argument("--output", type=Path, required=True)

    validate = sub.add_parser("dart-snapshot-validate", help="Validate immutable OpenDART snapshot")
    validate.add_argument("file", type=Path)

    extract = sub.add_parser("dart-extract", help="Extract unreviewed evidence candidate from OpenDART snapshot")
    extract.add_argument("file", type=Path)
    extract.add_argument("metric", choices=tuple(DART_METRIC_SPECS))
    extract.add_argument("--statement-section", default=None, choices=("BS", "IS", "CIS", "CF", "SCE"))
    return parser


def _web_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vih")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--json", action="store_true", dest="as_json")
    sub = parser.add_subparsers(dest="command", required=True)
    web = sub.add_parser("web")
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--port", type=int, default=8765)
    return parser


def _run_dart(argv: list[str]) -> int:
    args = _dart_parser().parse_args(argv)
    try:
        if args.command == "dart-fetch":
            snapshot = capture_dart_snapshot(
                args.corp_code,
                args.bsns_year,
                args.reprt_code,
                args.fs_div,
                api_key=args.api_key,
            )
            result = materialize_dart_snapshot(snapshot, args.output, args.root)
            _dump(result)
            return 0
        if args.command == "dart-snapshot-validate":
            result = validate_dart_snapshot(load_dart_snapshot(args.file))
            _dump(result)
            return 0
        if args.command == "dart-extract":
            result = extract_dart_evidence_candidate(
                load_dart_snapshot(args.file),
                args.metric,
                statement_section=args.statement_section,
            )
            _dump(result)
            return 0
        raise CaseServiceError(f"unsupported OpenDART command / 미지원 OpenDART 명령: {args.command}")
    except (CaseServiceError, ValueError, OSError) as exc:
        if args.as_json:
            _dump({"ok": False, "error": str(exc)})
        else:
            print(f"ERROR / 오류: {exc}", file=sys.stderr)
        return 2


def _run_web(argv: list[str]) -> int:
    args = _web_parser().parse_args(argv)
    try:
        if args.as_json:
            raise CaseServiceError("--json is not valid with web / web 명령은 --json을 지원하지 않습니다")
        serve_web(host=args.host, port=args.port, root=args.root)
        return 0
    except (CaseServiceError, ValueError, OSError) as exc:
        print(f"ERROR / 오류: {exc}", file=sys.stderr)
        return 2


def main(argv: list[str] | None = None) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    command = _command(values)
    if command in DART_COMMANDS:
        return _run_dart(values)
    if command == "web":
        return _run_web(values)
    return legacy_cli.main(values)


if __name__ == "__main__":
    raise SystemExit(main())
