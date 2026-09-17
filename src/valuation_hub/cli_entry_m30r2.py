"""M30-R2 additive CLI wrapper for evidence-first AI debt adjudication."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from valuation_hub import cli_entry_m30r1 as prior_cli
from valuation_hub.ai_debt_adjudication import (
    build_ai_sec_aggregate_debt_adjudication,
    build_legacy_compatible_ai_review_assertion,
    validate_ai_sec_aggregate_debt_adjudication,
    validate_ai_sec_aggregate_debt_evidence,
)
from valuation_hub.case_service import CaseServiceError

INTERCEPT = {
    "sec-aggregate-debt-ai-evidence-validate",
    "sec-aggregate-debt-ai-adjudicate",
    "sec-aggregate-debt-ai-adjudication-validate",
    "sec-aggregate-debt-ai-review-build",
}


def _dump(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _obj(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        raise CaseServiceError(f"{label} read failed / {label} 읽기 실패: {path}") from exc
    if not isinstance(value, dict):
        raise CaseServiceError(f"{label} JSON object required / {label} JSON 객체 필요")
    return value


def _command(argv: list[str]) -> str | None:
    return next((item for item in argv if item in INTERCEPT), None)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vih")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--json", action="store_true", dest="as_json")
    sub = parser.add_subparsers(dest="command", required=True)

    c = sub.add_parser("sec-aggregate-debt-ai-evidence-validate")
    c.add_argument("evidence", type=Path)
    c.add_argument("observation", type=Path)

    c = sub.add_parser("sec-aggregate-debt-ai-adjudicate")
    c.add_argument("observation", type=Path)
    c.add_argument("evidence", type=Path)
    c.add_argument("--adjudicated-at", required=True)

    c = sub.add_parser("sec-aggregate-debt-ai-adjudication-validate")
    c.add_argument("adjudication", type=Path)
    c.add_argument("observation", type=Path)
    c.add_argument("evidence", type=Path)

    c = sub.add_parser("sec-aggregate-debt-ai-review-build")
    c.add_argument("observation", type=Path)
    c.add_argument("adjudication", type=Path)
    c.add_argument("evidence", type=Path)
    return parser


def _run(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "sec-aggregate-debt-ai-evidence-validate":
            _dump(validate_ai_sec_aggregate_debt_evidence(_obj(args.evidence, "AI evidence"), _obj(args.observation, "observation")))
            return 0
        if args.command == "sec-aggregate-debt-ai-adjudicate":
            _dump(build_ai_sec_aggregate_debt_adjudication(
                _obj(args.observation, "observation"),
                _obj(args.evidence, "AI evidence"),
                adjudicated_at=args.adjudicated_at,
            ))
            return 0
        if args.command == "sec-aggregate-debt-ai-adjudication-validate":
            _dump(validate_ai_sec_aggregate_debt_adjudication(
                _obj(args.adjudication, "AI adjudication"),
                _obj(args.observation, "observation"),
                _obj(args.evidence, "AI evidence"),
            ))
            return 0
        if args.command == "sec-aggregate-debt-ai-review-build":
            _dump(build_legacy_compatible_ai_review_assertion(
                _obj(args.observation, "observation"),
                _obj(args.adjudication, "AI adjudication"),
                _obj(args.evidence, "AI evidence"),
            ))
            return 0
        raise CaseServiceError("unsupported M30-R2 command / 미지원 M30-R2 명령")
    except (CaseServiceError, ValueError, OSError, KeyError, TypeError) as exc:
        if getattr(args, "as_json", False):
            _dump({"ok": False, "error": str(exc)})
        else:
            print(f"ERROR / 오류: {exc}", file=sys.stderr)
        return 2


def main(argv: list[str] | None = None) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    if _command(values) is not None:
        return _run(values)
    return prior_cli.main(values)


if __name__ == "__main__":
    raise SystemExit(main())
