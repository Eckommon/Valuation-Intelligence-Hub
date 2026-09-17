"""M30-R3 additive CLI wrapper for evidence-first SEC observed-field AI authority."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from valuation_hub import cli_entry_m30r2 as prior_cli
from valuation_hub.ai_sec_observed_authority import (
    FIELDS,
    REQUIRED_CRITERIA,
    build_ai_reviewed_cash_observation,
    build_ai_reviewed_current_share_observation,
    build_ai_reviewed_minority_interest_package,
    build_ai_sec_observed_adjudication,
    build_ai_sec_observed_evidence,
    validate_ai_reviewed_cash_observation,
    validate_ai_reviewed_current_share_observation,
    validate_ai_reviewed_minority_interest_package,
    validate_ai_sec_observed_adjudication,
    validate_ai_sec_observed_evidence,
)
from valuation_hub.case_service import CaseServiceError

INTERCEPT = {
    "sec-observed-ai-evidence-build",
    "sec-observed-ai-evidence-validate",
    "sec-observed-ai-adjudicate",
    "sec-observed-ai-adjudication-validate",
    "cash-ai-finalize",
    "cash-ai-validate",
    "share-ai-finalize",
    "share-ai-validate",
    "minority-ai-finalize",
    "minority-ai-validate",
}
ALL_CRITERIA = tuple(sorted({item for values in REQUIRED_CRITERIA.values() for item in values}))


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

    c = sub.add_parser("sec-observed-ai-evidence-build")
    c.add_argument("field", choices=FIELDS)
    c.add_argument("candidate", type=Path)
    c.add_argument("observation", type=Path)
    c.add_argument("--primary-filing-locator", required=True)
    c.add_argument("--evidence-basis", required=True)
    c.add_argument("--contradiction-search-summary", required=True)
    c.add_argument("--material-contradiction", action="append", default=[])
    c.add_argument("--criterion", action="append", choices=ALL_CRITERIA, default=[])

    c = sub.add_parser("sec-observed-ai-evidence-validate")
    c.add_argument("evidence", type=Path)
    c.add_argument("candidate", type=Path)
    c.add_argument("observation", type=Path)

    c = sub.add_parser("sec-observed-ai-adjudicate")
    c.add_argument("candidate", type=Path)
    c.add_argument("observation", type=Path)
    c.add_argument("evidence", type=Path)
    c.add_argument("--adjudicated-at", required=True)

    c = sub.add_parser("sec-observed-ai-adjudication-validate")
    c.add_argument("adjudication", type=Path)
    c.add_argument("candidate", type=Path)
    c.add_argument("observation", type=Path)
    c.add_argument("evidence", type=Path)

    for name in ("cash-ai-finalize", "share-ai-finalize"):
        c = sub.add_parser(name)
        c.add_argument("candidate", type=Path)
        c.add_argument("observation", type=Path)
        c.add_argument("adjudication", type=Path)
        c.add_argument("evidence", type=Path)

    for name in ("cash-ai-validate", "share-ai-validate"):
        c = sub.add_parser(name)
        c.add_argument("reviewed", type=Path)
        c.add_argument("candidate", type=Path)
        c.add_argument("observation", type=Path)
        c.add_argument("adjudication", type=Path)
        c.add_argument("evidence", type=Path)

    c = sub.add_parser("minority-ai-finalize")
    c.add_argument("candidate", type=Path)
    c.add_argument("observation", type=Path)
    c.add_argument("adjudication", type=Path)
    c.add_argument("evidence", type=Path)
    c.add_argument("--as-of", required=True)
    c.add_argument("--max-age-days", type=int, default=550)

    c = sub.add_parser("minority-ai-validate")
    c.add_argument("package", type=Path)
    c.add_argument("candidate", type=Path)
    c.add_argument("observation", type=Path)
    c.add_argument("adjudication", type=Path)
    c.add_argument("evidence", type=Path)
    return parser


def _common(args: Any) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    return (
        _obj(args.candidate, "candidate"),
        _obj(args.observation, "observation"),
        _obj(args.adjudication, "AI adjudication"),
        _obj(args.evidence, "AI evidence"),
    )


def _run(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "sec-observed-ai-evidence-build":
            selected = set(args.criterion)
            required = REQUIRED_CRITERIA[args.field]
            _dump(build_ai_sec_observed_evidence(
                args.field,
                _obj(args.candidate, "candidate"),
                _obj(args.observation, "observation"),
                primary_filing_locator=args.primary_filing_locator,
                evidence_basis=args.evidence_basis,
                contradiction_search_summary=args.contradiction_search_summary,
                material_contradictions=list(args.material_contradiction),
                criteria={key: key in selected for key in required},
            ))
            return 0
        if args.command == "sec-observed-ai-evidence-validate":
            _dump(validate_ai_sec_observed_evidence(
                _obj(args.evidence, "AI evidence"),
                _obj(args.candidate, "candidate"),
                _obj(args.observation, "observation"),
            ))
            return 0
        if args.command == "sec-observed-ai-adjudicate":
            _dump(build_ai_sec_observed_adjudication(
                _obj(args.candidate, "candidate"),
                _obj(args.observation, "observation"),
                _obj(args.evidence, "AI evidence"),
                adjudicated_at=args.adjudicated_at,
            ))
            return 0
        if args.command == "sec-observed-ai-adjudication-validate":
            _dump(validate_ai_sec_observed_adjudication(
                _obj(args.adjudication, "AI adjudication"),
                _obj(args.candidate, "candidate"),
                _obj(args.observation, "observation"),
                _obj(args.evidence, "AI evidence"),
            ))
            return 0
        if args.command == "cash-ai-finalize":
            _dump(build_ai_reviewed_cash_observation(*_common(args)))
            return 0
        if args.command == "cash-ai-validate":
            candidate, observation, adjudication, evidence = _common(args)
            _dump(validate_ai_reviewed_cash_observation(_obj(args.reviewed, "AI-reviewed cash"), candidate, observation, adjudication, evidence))
            return 0
        if args.command == "share-ai-finalize":
            _dump(build_ai_reviewed_current_share_observation(*_common(args)))
            return 0
        if args.command == "share-ai-validate":
            candidate, observation, adjudication, evidence = _common(args)
            _dump(validate_ai_reviewed_current_share_observation(_obj(args.reviewed, "AI-reviewed shares"), candidate, observation, adjudication, evidence))
            return 0
        if args.command == "minority-ai-finalize":
            candidate, observation, adjudication, evidence = _common(args)
            _dump(build_ai_reviewed_minority_interest_package(
                candidate, observation, adjudication, evidence,
                as_of=args.as_of, max_age_days=args.max_age_days,
            ))
            return 0
        if args.command == "minority-ai-validate":
            candidate, observation, adjudication, evidence = _common(args)
            _dump(validate_ai_reviewed_minority_interest_package(
                _obj(args.package, "AI-reviewed minority-interest package"), candidate, observation, adjudication, evidence
            ))
            return 0
        raise CaseServiceError("unsupported M30-R3 command / 미지원 M30-R3 명령")
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
