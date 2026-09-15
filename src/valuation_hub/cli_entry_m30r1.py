"""M30-R1 additive CLI wrapper for governed real SEC aggregate-debt review.

This wrapper exposes the already-canonical M30-P1 runtime lifecycle without changing
its semantics. Human semantic review inputs remain explicit runtime arguments; no
reviewer identity, timestamp, basis, locator, or semantic decision is inferred.
All commands outside this additive surface delegate unchanged to M30.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from valuation_hub import cli_entry_m30 as prior_cli
from valuation_hub.case_service import CaseServiceError
from valuation_hub.debt_draft_binding_m30 import (
    build_binding_proposal_with_sec_aggregate_debt,
    validate_binding_proposal_sec_aggregate,
)
from valuation_hub.sec_aggregate_debt import (
    build_sec_aggregate_debt_binding_context,
    build_sec_aggregate_debt_review_assertion,
    extract_sec_aggregate_debt_candidate,
    finalize_reviewed_sec_aggregate_debt,
    normalize_sec_aggregate_debt_candidate,
    validate_reviewed_sec_aggregate_debt,
    validate_sec_aggregate_debt_binding_context,
    validate_sec_aggregate_debt_candidate,
    validate_sec_aggregate_debt_observation,
    validate_sec_aggregate_debt_review_assertion,
)

INTERCEPT = {
    "sec-aggregate-debt-extract",
    "sec-aggregate-debt-candidate-validate",
    "sec-aggregate-debt-normalize",
    "sec-aggregate-debt-observation-validate",
    "sec-aggregate-debt-review-build",
    "sec-aggregate-debt-review-validate",
    "sec-aggregate-debt-finalize",
    "sec-aggregate-debt-profile-validate",
    "sec-aggregate-debt-context-build",
    "sec-aggregate-debt-context-validate",
    "binding-sec-aggregate-debt-build",
    "binding-sec-aggregate-debt-validate",
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

    command = sub.add_parser("sec-aggregate-debt-extract")
    command.add_argument("snapshot", type=Path)
    command.add_argument("--form", default=None)
    command.add_argument("--period-end", default=None)

    sub.add_parser("sec-aggregate-debt-candidate-validate").add_argument("candidate", type=Path)

    sub.add_parser("sec-aggregate-debt-normalize").add_argument("candidate", type=Path)

    sub.add_parser("sec-aggregate-debt-observation-validate").add_argument("observation", type=Path)

    command = sub.add_parser("sec-aggregate-debt-review-build")
    command.add_argument("observation", type=Path)
    command.add_argument("--reviewer", required=True)
    command.add_argument("--reviewed-at", required=True)
    command.add_argument("--review-basis", required=True)
    command.add_argument("--source-basis-locator", required=True)
    command.add_argument("--semantic-scope-decision", required=True)

    command = sub.add_parser("sec-aggregate-debt-review-validate")
    command.add_argument("assertion", type=Path)
    command.add_argument("observation", type=Path)

    command = sub.add_parser("sec-aggregate-debt-finalize")
    command.add_argument("observation", type=Path)
    command.add_argument("assertion", type=Path)

    sub.add_parser("sec-aggregate-debt-profile-validate").add_argument("profile", type=Path)

    command = sub.add_parser("sec-aggregate-debt-context-build")
    command.add_argument("profile", type=Path)
    command.add_argument("--as-of", required=True)
    command.add_argument("--max-age-days", type=int, default=550)

    sub.add_parser("sec-aggregate-debt-context-validate").add_argument("context", type=Path)

    command = sub.add_parser("binding-sec-aggregate-debt-build")
    command.add_argument("observations", type=Path)
    command.add_argument("debt_context", type=Path)
    command.add_argument("--as-of", required=True)
    command.add_argument("--max-age-days", type=int, default=550)

    sub.add_parser("binding-sec-aggregate-debt-validate").add_argument("proposal", type=Path)
    return parser


def _run(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "sec-aggregate-debt-extract":
            _dump(extract_sec_aggregate_debt_candidate(
                _obj(args.snapshot, "SEC snapshot"),
                form=args.form,
                period_end=args.period_end,
            ))
            return 0
        if args.command == "sec-aggregate-debt-candidate-validate":
            _dump(validate_sec_aggregate_debt_candidate(_obj(args.candidate, "SEC aggregate-debt candidate")))
            return 0
        if args.command == "sec-aggregate-debt-normalize":
            _dump(normalize_sec_aggregate_debt_candidate(_obj(args.candidate, "SEC aggregate-debt candidate")))
            return 0
        if args.command == "sec-aggregate-debt-observation-validate":
            _dump(validate_sec_aggregate_debt_observation(_obj(args.observation, "SEC aggregate-debt observation")))
            return 0
        if args.command == "sec-aggregate-debt-review-build":
            _dump(build_sec_aggregate_debt_review_assertion(
                _obj(args.observation, "SEC aggregate-debt observation"),
                reviewer=args.reviewer,
                reviewed_at=args.reviewed_at,
                review_basis=args.review_basis,
                source_basis_locator=args.source_basis_locator,
                semantic_scope_decision=args.semantic_scope_decision,
            ))
            return 0
        if args.command == "sec-aggregate-debt-review-validate":
            _dump(validate_sec_aggregate_debt_review_assertion(
                _obj(args.assertion, "SEC aggregate-debt review assertion"),
                _obj(args.observation, "SEC aggregate-debt observation"),
            ))
            return 0
        if args.command == "sec-aggregate-debt-finalize":
            _dump(finalize_reviewed_sec_aggregate_debt(
                _obj(args.observation, "SEC aggregate-debt observation"),
                _obj(args.assertion, "SEC aggregate-debt review assertion"),
            ))
            return 0
        if args.command == "sec-aggregate-debt-profile-validate":
            _dump(validate_reviewed_sec_aggregate_debt(_obj(args.profile, "reviewed SEC aggregate-debt profile")))
            return 0
        if args.command == "sec-aggregate-debt-context-build":
            _dump(build_sec_aggregate_debt_binding_context(
                _obj(args.profile, "reviewed SEC aggregate-debt profile"),
                as_of=args.as_of,
                max_age_days=args.max_age_days,
            ))
            return 0
        if args.command == "sec-aggregate-debt-context-validate":
            _dump(validate_sec_aggregate_debt_binding_context(_obj(args.context, "SEC aggregate-debt binding context")))
            return 0
        if args.command == "binding-sec-aggregate-debt-build":
            _dump(build_binding_proposal_with_sec_aggregate_debt(
                _arr(args.observations, "financial observations"),
                _obj(args.debt_context, "SEC aggregate-debt binding context"),
                as_of=args.as_of,
                max_age_days=args.max_age_days,
            ))
            return 0
        if args.command == "binding-sec-aggregate-debt-validate":
            _dump(validate_binding_proposal_sec_aggregate(_obj(args.proposal, "SEC aggregate-debt binding proposal")))
            return 0
        raise CaseServiceError("unsupported M30-R1 command / 미지원 M30-R1 명령")
    except (CaseServiceError, ValueError, OSError, KeyError, TypeError) as exc:
        return _error(args, exc)


def main(argv: list[str] | None = None) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    if _command(values) is not None:
        return _run(values)
    return prior_cli.main(values)


if __name__ == "__main__":
    raise SystemExit(main())
