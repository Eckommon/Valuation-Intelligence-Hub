"""Stable CLI entry dispatcher / 안정적 CLI 진입 dispatcher.

M14 keeps the mature M1-M13 parser untouched. M15 extends the thin dispatcher
with read-only financial normalization and TTM transforms. Existing commands
continue to delegate to `valuation_hub.cli.main` unchanged.
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
from valuation_hub.financial_normalization import (
    DURATION_ANNUAL,
    DURATION_QUARTER,
    DURATION_YTD,
    normalize_dart_candidate,
    normalize_sec_candidate,
    reconcile_same_period,
    ttm_annual_bridge,
    ttm_four_quarters,
    validate_financial_observation,
    validate_ttm_result,
)
from valuation_hub.web_sources import serve as serve_web

DART_COMMANDS = {"dart-fetch", "dart-snapshot-validate", "dart-extract"}
NORMALIZATION_COMMANDS = {
    "normalize-sec",
    "normalize-dart",
    "normalize-validate",
    "ttm-four-quarters",
    "ttm-annual-bridge",
    "ttm-validate",
    "normalize-reconcile",
}


def _dump(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CaseServiceError(f"{label} file not found / {label} 파일 없음: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise CaseServiceError(f"{label} read failed / {label} 읽기 실패: {path}") from exc
    if not isinstance(payload, dict):
        raise CaseServiceError(f"{label} must be a JSON object / {label} JSON 객체 필요")
    return payload


def _command(argv: list[str]) -> str | None:
    known = DART_COMMANDS | NORMALIZATION_COMMANDS | {"web"}
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


def _normalization_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vih")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--json", action="store_true", dest="as_json")
    sub = parser.add_subparsers(dest="command", required=True)

    sec = sub.add_parser("normalize-sec", help="Normalize one SEC evidence candidate / SEC 근거후보 기간 정규화")
    sec.add_argument("file", type=Path)
    sec.add_argument("--period-kind", choices=(DURATION_QUARTER, DURATION_YTD, DURATION_ANNUAL), default=None)

    dart = sub.add_parser("normalize-dart", help="Normalize one OpenDART evidence candidate / OpenDART 근거후보 기간 정규화")
    dart.add_argument("file", type=Path)
    dart.add_argument("--amount-basis", choices=("CURRENT", "CUMULATIVE"), default="CURRENT")

    validate = sub.add_parser("normalize-validate", help="Validate normalized financial observation / 정규화 observation 검증")
    validate.add_argument("file", type=Path)

    four = sub.add_parser("ttm-four-quarters", help="Build TTM from four quarter observations / 4분기 TTM 생성")
    four.add_argument("files", nargs=4, type=Path)

    bridge = sub.add_parser("ttm-annual-bridge", help="Build TTM from prior FY + current YTD - prior comparable YTD")
    bridge.add_argument("prior_annual", type=Path)
    bridge.add_argument("current_ytd", type=Path)
    bridge.add_argument("prior_ytd", type=Path)

    ttm_validate = sub.add_parser("ttm-validate", help="Validate normalized TTM result / TTM 결과 검증")
    ttm_validate.add_argument("file", type=Path)

    reconcile = sub.add_parser("normalize-reconcile", help="Reconcile equal same-period observations / 동일기간 observation 조정")
    reconcile.add_argument("files", nargs="+", type=Path)
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
            _dump(materialize_dart_snapshot(snapshot, args.output, args.root))
            return 0
        if args.command == "dart-snapshot-validate":
            _dump(validate_dart_snapshot(load_dart_snapshot(args.file)))
            return 0
        if args.command == "dart-extract":
            _dump(extract_dart_evidence_candidate(load_dart_snapshot(args.file), args.metric, statement_section=args.statement_section))
            return 0
        raise CaseServiceError(f"unsupported OpenDART command / 미지원 OpenDART 명령: {args.command}")
    except (CaseServiceError, ValueError, OSError) as exc:
        if args.as_json:
            _dump({"ok": False, "error": str(exc)})
        else:
            print(f"ERROR / 오류: {exc}", file=sys.stderr)
        return 2


def _run_normalization(argv: list[str]) -> int:
    args = _normalization_parser().parse_args(argv)
    try:
        if args.command == "normalize-sec":
            _dump(normalize_sec_candidate(_load_object(args.file, "SEC evidence candidate"), declared_period_kind=args.period_kind))
            return 0
        if args.command == "normalize-dart":
            _dump(normalize_dart_candidate(_load_object(args.file, "OpenDART evidence candidate"), amount_basis=args.amount_basis))
            return 0
        if args.command == "normalize-validate":
            _dump(validate_financial_observation(_load_object(args.file, "financial observation")))
            return 0
        if args.command == "ttm-four-quarters":
            _dump(ttm_four_quarters([_load_object(path, "financial observation") for path in args.files]))
            return 0
        if args.command == "ttm-annual-bridge":
            _dump(ttm_annual_bridge(
                _load_object(args.prior_annual, "prior annual observation"),
                _load_object(args.current_ytd, "current YTD observation"),
                _load_object(args.prior_ytd, "prior YTD observation"),
            ))
            return 0
        if args.command == "ttm-validate":
            _dump(validate_ttm_result(_load_object(args.file, "TTM result")))
            return 0
        if args.command == "normalize-reconcile":
            _dump(reconcile_same_period([_load_object(path, "financial observation") for path in args.files]))
            return 0
        raise CaseServiceError(f"unsupported normalization command / 미지원 정규화 명령: {args.command}")
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
    if command in NORMALIZATION_COMMANDS:
        return _run_normalization(values)
    if command == "web":
        return _run_web(values)
    return legacy_cli.main(values)


if __name__ == "__main__":
    raise SystemExit(main())
