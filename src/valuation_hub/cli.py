"""Valuation Intelligence Hub CLI / 가치분석 Hub CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from valuation_hub.case_service import (
    CaseServiceError,
    list_cases,
    read_report,
    run_case,
    validate_case,
)


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
        ("validate", "Validate a case / 사례 검증"),
        ("run", "Run a case / 사례 실행"),
        ("report", "Print canonical report / 정식 보고서 출력"),
    ):
        p = sub.add_parser(command, help=help_text)
        p.add_argument("case_id")
    return parser


def _dump(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _human_list(cases: list[dict[str, Any]]) -> None:
    print("Registered valuation cases / 등록 가치평가 사례")
    for item in cases:
        print(
            f"- {item['case_id']} | {item['display_name_en']} / {item['display_name_ko']} "
            f"| {item['model']}"
        )


def _human_validate(result: dict[str, Any]) -> None:
    print(f"PASS / 통과: {result['case_id']}")
    print(f"Model / 모델: {result['model']} ({result['model_version']})")
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
        raise CaseServiceError(f"unsupported command / 미지원 명령: {args.command}")
    except CaseServiceError as exc:
        if args.as_json:
            _dump({"ok": False, "error": str(exc)})
        else:
            print(f"ERROR / 오류: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
