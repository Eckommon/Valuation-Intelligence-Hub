"""M30-R6 additive CLI wrapper for disclosure-limited dilution assumption."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from valuation_hub import cli_entry_m30r5 as prior_cli
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.disclosure_limited_dilution import (
    build_disclosure_limited_dilution_adjudication,
    build_disclosure_limited_dilution_evidence,
    finalize_disclosure_limited_dilution_assumption,
    validate_disclosure_limited_dilution_adjudication,
    validate_disclosure_limited_dilution_assumption,
    validate_disclosure_limited_dilution_evidence,
)

INTERCEPT = {
    "dilution-assumption-evidence-build",
    "dilution-assumption-evidence-validate",
    "dilution-assumption-adjudicate",
    "dilution-assumption-adjudication-validate",
    "dilution-assumption-finalize",
    "dilution-assumption-package-validate",
}


def _dump(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _command(argv: list[str]) -> str | None:
    return next((item for item in argv if item in INTERCEPT), None)


def _root(value: Path | None) -> Path:
    return value.resolve() if value else find_repo_root()


def _path(value: Path, root: Path) -> Path:
    return value.resolve() if value.is_absolute() else (root / value).resolve()


def _obj(value: Path, root: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(_path(value, root).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CaseServiceError(f"{label} read failed / {label} 읽기 실패") from exc
    if not isinstance(payload, dict):
        raise CaseServiceError(f"{label} object required / {label} 객체 필요")
    return payload


def _rows(value: Path, root: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(_path(value, root).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CaseServiceError("upper-envelope manifest read failed / upper-envelope manifest 읽기 실패") from exc
    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        raise CaseServiceError("upper-envelope manifest array required / upper-envelope manifest 배열 필요")
    return payload


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="vih")
    p.add_argument("--root", type=Path, default=None)
    p.add_argument("--json", action="store_true", dest="as_json")
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("dilution-assumption-evidence-build")
    c.add_argument("base_context", type=Path)
    c.add_argument("hold_inventory", type=Path)
    c.add_argument("historical_dilution", type=Path)
    c.add_argument("upper_envelope", type=Path)
    c.add_argument("--as-of", required=True)
    c.add_argument("--materiality-threshold", type=float, default=0.05)
    c.add_argument("--max-historical-age-days", type=int, default=180)

    c = sub.add_parser("dilution-assumption-evidence-validate")
    c.add_argument("evidence", type=Path)
    c.add_argument("base_context", type=Path)
    c.add_argument("hold_inventory", type=Path)
    c.add_argument("historical_dilution", type=Path)
    c.add_argument("upper_envelope", type=Path)

    c = sub.add_parser("dilution-assumption-adjudicate")
    c.add_argument("evidence", type=Path)
    c.add_argument("--adjudicated-at", required=True)

    c = sub.add_parser("dilution-assumption-adjudication-validate")
    c.add_argument("adjudication", type=Path)
    c.add_argument("evidence", type=Path)

    c = sub.add_parser("dilution-assumption-finalize")
    c.add_argument("evidence", type=Path)
    c.add_argument("adjudication", type=Path)

    c = sub.add_parser("dilution-assumption-package-validate")
    c.add_argument("package", type=Path)
    c.add_argument("evidence", type=Path)
    c.add_argument("adjudication", type=Path)
    return p


def _run(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    root = _root(args.root)
    try:
        if args.command == "dilution-assumption-evidence-build":
            _dump(build_disclosure_limited_dilution_evidence(
                _obj(args.base_context, root, "base_context"),
                _obj(args.hold_inventory, root, "hold_inventory"),
                _obj(args.historical_dilution, root, "historical_dilution"),
                _rows(args.upper_envelope, root),
                as_of=args.as_of,
                materiality_threshold=args.materiality_threshold,
                max_historical_age_days=args.max_historical_age_days,
            ))
            return 0

        evidence = _obj(args.evidence, root, "evidence")
        if args.command == "dilution-assumption-evidence-validate":
            _dump(validate_disclosure_limited_dilution_evidence(
                evidence,
                _obj(args.base_context, root, "base_context"),
                _obj(args.hold_inventory, root, "hold_inventory"),
                _obj(args.historical_dilution, root, "historical_dilution"),
                _rows(args.upper_envelope, root),
            ))
            return 0

        if args.command == "dilution-assumption-adjudicate":
            _dump(build_disclosure_limited_dilution_adjudication(evidence, adjudicated_at=args.adjudicated_at))
            return 0

        adjudication = _obj(args.adjudication, root, "adjudication")
        if args.command == "dilution-assumption-adjudication-validate":
            _dump(validate_disclosure_limited_dilution_adjudication(adjudication, evidence))
            return 0

        if args.command == "dilution-assumption-finalize":
            _dump(finalize_disclosure_limited_dilution_assumption(evidence, adjudication))
            return 0

        if args.command == "dilution-assumption-package-validate":
            _dump(validate_disclosure_limited_dilution_assumption(
                _obj(args.package, root, "package"), evidence, adjudication
            ))
            return 0

        raise CaseServiceError("unsupported M30-R6 command / 미지원 M30-R6 명령")
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
