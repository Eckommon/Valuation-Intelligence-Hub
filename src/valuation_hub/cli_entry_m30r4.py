"""M30-R4 additive CLI wrapper for evidence-first AI dilution coverage."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from valuation_hub import cli_entry_m30r3 as prior_cli
from valuation_hub.ai_dilution_authority import (
    build_ai_dilution_adjudication,
    build_ai_dilution_inventory,
    build_ai_reviewed_dilution_package,
    validate_ai_dilution_adjudication,
    validate_ai_dilution_inventory,
    validate_ai_reviewed_dilution_package,
)
from valuation_hub.case_service import CaseServiceError

INTERCEPT = {
    "dilution-ai-inventory-build",
    "dilution-ai-inventory-validate",
    "dilution-ai-adjudicate",
    "dilution-ai-adjudication-validate",
    "dilution-ai-finalize",
    "dilution-ai-package-validate",
}


def _dump(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        raise CaseServiceError(f"{label} read failed / {label} 읽기 실패: {path}") from exc


def _obj(path: Path, label: str) -> dict[str, Any]:
    value = _json(path, label)
    if not isinstance(value, dict):
        raise CaseServiceError(f"{label} JSON object required / {label} JSON 객체 필요")
    return value


def _list(path: Path, label: str) -> list[dict[str, Any]]:
    value = _json(path, label)
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise CaseServiceError(f"{label} JSON object array required / {label} JSON 객체 배열 필요")
    return value


def _command(argv: list[str]) -> str | None:
    return next((item for item in argv if item in INTERCEPT), None)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vih")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--json", action="store_true", dest="as_json")
    sub = parser.add_subparsers(dest="command", required=True)

    c = sub.add_parser("dilution-ai-inventory-build")
    c.add_argument("base_context", type=Path)
    c.add_argument("categories", type=Path)
    c.add_argument("--market-price-package", type=Path, default=None)

    c = sub.add_parser("dilution-ai-inventory-validate")
    c.add_argument("inventory", type=Path)
    c.add_argument("base_context", type=Path)

    c = sub.add_parser("dilution-ai-adjudicate")
    c.add_argument("inventory", type=Path)
    c.add_argument("base_context", type=Path)
    c.add_argument("--adjudicated-at", required=True)

    c = sub.add_parser("dilution-ai-adjudication-validate")
    c.add_argument("adjudication", type=Path)
    c.add_argument("inventory", type=Path)
    c.add_argument("base_context", type=Path)

    c = sub.add_parser("dilution-ai-finalize")
    c.add_argument("base_context", type=Path)
    c.add_argument("inventory", type=Path)
    c.add_argument("adjudication", type=Path)

    c = sub.add_parser("dilution-ai-package-validate")
    c.add_argument("package", type=Path)
    c.add_argument("base_context", type=Path)
    c.add_argument("inventory", type=Path)
    c.add_argument("adjudication", type=Path)
    return parser


def _run(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "dilution-ai-inventory-build":
            market = _obj(args.market_price_package, "market-price package") if args.market_price_package else None
            _dump(build_ai_dilution_inventory(
                _obj(args.base_context, "share base context"),
                _list(args.categories, "dilution categories"),
                market_price_package=market,
            ))
            return 0
        if args.command == "dilution-ai-inventory-validate":
            _dump(validate_ai_dilution_inventory(
                _obj(args.inventory, "AI dilution inventory"),
                _obj(args.base_context, "share base context"),
            ))
            return 0
        if args.command == "dilution-ai-adjudicate":
            _dump(build_ai_dilution_adjudication(
                _obj(args.inventory, "AI dilution inventory"),
                _obj(args.base_context, "share base context"),
                adjudicated_at=args.adjudicated_at,
            ))
            return 0
        if args.command == "dilution-ai-adjudication-validate":
            _dump(validate_ai_dilution_adjudication(
                _obj(args.adjudication, "AI dilution adjudication"),
                _obj(args.inventory, "AI dilution inventory"),
                _obj(args.base_context, "share base context"),
            ))
            return 0
        if args.command == "dilution-ai-finalize":
            _dump(build_ai_reviewed_dilution_package(
                _obj(args.base_context, "share base context"),
                _obj(args.inventory, "AI dilution inventory"),
                _obj(args.adjudication, "AI dilution adjudication"),
            ))
            return 0
        if args.command == "dilution-ai-package-validate":
            _dump(validate_ai_reviewed_dilution_package(
                _obj(args.package, "AI reviewed dilution package"),
                _obj(args.base_context, "share base context"),
                _obj(args.inventory, "AI dilution inventory"),
                _obj(args.adjudication, "AI dilution adjudication"),
            ))
            return 0
        raise CaseServiceError("unsupported M30-R4 command / 미지원 M30-R4 명령")
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
