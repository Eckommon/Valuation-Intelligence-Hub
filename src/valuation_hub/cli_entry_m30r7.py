"""M30-R7 additive CLI wrapper for M21 historical-dilution AI authority."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from valuation_hub import cli_entry_m30r6 as prior_cli
from valuation_hub.ai_historical_dilution_authority import (
    REQUIRED_CRITERIA,
    build_ai_historical_dilution_adjudication,
    build_ai_historical_dilution_evidence,
    build_ai_reviewed_historical_dilution_package,
    validate_ai_historical_dilution_adjudication,
    validate_ai_historical_dilution_evidence,
    validate_ai_reviewed_historical_dilution_package,
)
from valuation_hub.case_service import CaseServiceError, find_repo_root

INTERCEPT = {
    "historical-dilution-ai-evidence-build",
    "historical-dilution-ai-evidence-validate",
    "historical-dilution-ai-adjudicate",
    "historical-dilution-ai-adjudication-validate",
    "historical-dilution-ai-finalize",
    "historical-dilution-ai-package-validate",
}


def _dump(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _command(argv: list[str]) -> str | None:
    return next((item for item in argv if item in INTERCEPT), None)


def _root(value: Path | None) -> Path:
    return value.resolve() if value else find_repo_root()


def _obj(value: Path, root: Path, label: str) -> dict[str, Any]:
    path = value.resolve() if value.is_absolute() else (root / value).resolve()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CaseServiceError(f"{label} read failed / {label} 읽기 실패") from exc
    if not isinstance(payload, dict):
        raise CaseServiceError(f"{label} object required / {label} 객체 필요")
    return payload


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="vih")
    p.add_argument("--root", type=Path, default=None)
    p.add_argument("--json", action="store_true", dest="as_json")
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("historical-dilution-ai-evidence-build")
    c.add_argument("basic_candidate", type=Path)
    c.add_argument("basic_observation", type=Path)
    c.add_argument("diluted_candidate", type=Path)
    c.add_argument("diluted_observation", type=Path)
    c.add_argument("--primary-filing-locator", required=True)
    c.add_argument("--evidence-basis", required=True)
    c.add_argument("--contradiction-search-summary", required=True)
    c.add_argument("--material-contradiction", action="append", default=[])
    c.add_argument("--criterion", action="append", choices=REQUIRED_CRITERIA, default=[])

    c = sub.add_parser("historical-dilution-ai-evidence-validate")
    c.add_argument("evidence", type=Path)
    _add_source_pair(c)

    c = sub.add_parser("historical-dilution-ai-adjudicate")
    c.add_argument("evidence", type=Path)
    _add_source_pair(c)
    c.add_argument("--adjudicated-at", required=True)

    c = sub.add_parser("historical-dilution-ai-adjudication-validate")
    c.add_argument("adjudication", type=Path)
    c.add_argument("evidence", type=Path)
    _add_source_pair(c)

    c = sub.add_parser("historical-dilution-ai-finalize")
    _add_source_pair(c)
    c.add_argument("evidence", type=Path)
    c.add_argument("adjudication", type=Path)

    c = sub.add_parser("historical-dilution-ai-package-validate")
    c.add_argument("package", type=Path)
    return p


def _add_source_pair(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("basic_candidate", type=Path)
    parser.add_argument("basic_observation", type=Path)
    parser.add_argument("diluted_candidate", type=Path)
    parser.add_argument("diluted_observation", type=Path)


def _pair(args: Any, root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    return (
        _obj(args.basic_candidate, root, "basic_candidate"),
        _obj(args.basic_observation, root, "basic_observation"),
        _obj(args.diluted_candidate, root, "diluted_candidate"),
        _obj(args.diluted_observation, root, "diluted_observation"),
    )


def _run(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    root = _root(args.root)
    try:
        if args.command == "historical-dilution-ai-evidence-build":
            pair = _pair(args, root)
            selected = set(args.criterion)
            _dump(
                build_ai_historical_dilution_evidence(
                    *pair,
                    primary_filing_locator=args.primary_filing_locator,
                    evidence_basis=args.evidence_basis,
                    contradiction_search_summary=args.contradiction_search_summary,
                    material_contradictions=list(args.material_contradiction),
                    criteria={key: key in selected for key in REQUIRED_CRITERIA},
                )
            )
            return 0

        if args.command == "historical-dilution-ai-evidence-validate":
            _dump(
                validate_ai_historical_dilution_evidence(
                    _obj(args.evidence, root, "evidence"), *_pair(args, root)
                )
            )
            return 0

        if args.command == "historical-dilution-ai-adjudicate":
            _dump(
                build_ai_historical_dilution_adjudication(
                    _obj(args.evidence, root, "evidence"),
                    *_pair(args, root),
                    adjudicated_at=args.adjudicated_at,
                )
            )
            return 0

        if args.command == "historical-dilution-ai-adjudication-validate":
            _dump(
                validate_ai_historical_dilution_adjudication(
                    _obj(args.adjudication, root, "adjudication"),
                    _obj(args.evidence, root, "evidence"),
                    *_pair(args, root),
                )
            )
            return 0

        if args.command == "historical-dilution-ai-finalize":
            pair = _pair(args, root)
            _dump(
                build_ai_reviewed_historical_dilution_package(
                    *pair,
                    _obj(args.evidence, root, "evidence"),
                    _obj(args.adjudication, root, "adjudication"),
                )
            )
            return 0

        if args.command == "historical-dilution-ai-package-validate":
            _dump(
                validate_ai_reviewed_historical_dilution_package(
                    _obj(args.package, root, "package")
                )
            )
            return 0

        raise CaseServiceError("unsupported M30-R7 command / 미지원 M30-R7 명령")
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
