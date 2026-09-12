"""M27 additive CLI wrapper / M27 추가형 CLI wrapper.

M27 market-price preparation, v0.7 validation, and binding-apply commands are
intercepted. Older proposal/apply versions delegate unchanged through the M27
apply adapter to the M26 implementation.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from valuation_hub import cli_entry_m26 as prior_cli
from valuation_hub.binding_apply_m27 import (
    apply_binding_approval,
    build_binding_approval,
    validate_binding_approval,
    validate_bound_draft_result,
)
from valuation_hub.case_service import CaseServiceError
from valuation_hub.market_price import (
    QUOTE_TYPES,
    build_market_price_candidate,
    build_market_price_review_assertion,
    finalize_reviewed_market_price,
    validate_market_price_candidate,
    validate_market_price_review_assertion,
    validate_reviewed_market_price,
)
from valuation_hub.market_price_draft_binding import (
    build_binding_proposal_with_market_price,
    validate_binding_proposal_any,
)
from valuation_hub.web_market_price import serve as serve_web

MARKET_COMMANDS = {
    "market-price-candidate-build",
    "market-price-candidate-validate",
    "market-price-review-build",
    "market-price-review-validate",
    "market-price-finalize",
    "market-price-validate",
    "binding-build-with-market-price",
}
APPLY_COMMANDS = {
    "binding-approval-build",
    "binding-approval-validate",
    "binding-apply",
    "bound-draft-validate",
}
INTERCEPT = MARKET_COMMANDS | APPLY_COMMANDS | {"binding-validate", "web"}


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

    command = sub.add_parser("market-price-candidate-build")
    command.add_argument("--price", required=True, type=float)
    command.add_argument("--currency", required=True)
    command.add_argument("--entity-id", required=True)
    command.add_argument("--financial-scope", required=True)
    command.add_argument("--instrument-id", required=True)
    command.add_argument("--symbol", required=True)
    command.add_argument("--venue", required=True)
    command.add_argument("--quote-type", required=True, choices=QUOTE_TYPES)
    command.add_argument("--trading-date", required=True)
    command.add_argument("--observed-at", required=True)
    command.add_argument("--as-of", required=True)
    command.add_argument("--source-publisher", required=True)
    command.add_argument("--source-type", required=True)
    command.add_argument("--source-tier", required=True, choices=("A", "B", "C", "D"))
    command.add_argument("--source-locator", required=True)
    command.add_argument("--source-snapshot-sha256", required=True)
    command.add_argument("--max-age-days", type=int, default=7)
    sub.add_parser("market-price-candidate-validate").add_argument("file", type=Path)

    command = sub.add_parser("market-price-review-build")
    command.add_argument("candidate", type=Path)
    command.add_argument("--reviewer", required=True)
    command.add_argument("--approved-at", required=True)
    command.add_argument("--review-basis", required=True)
    command = sub.add_parser("market-price-review-validate")
    command.add_argument("assertion", type=Path)
    command.add_argument("candidate", type=Path)
    command = sub.add_parser("market-price-finalize")
    command.add_argument("candidate", type=Path)
    command.add_argument("assertion", type=Path)
    sub.add_parser("market-price-validate").add_argument("file", type=Path)

    command = sub.add_parser("binding-build-with-market-price")
    command.add_argument("base_proposal", type=Path)
    command.add_argument("market_price_package", type=Path)
    sub.add_parser("binding-validate").add_argument("file", type=Path)

    command = sub.add_parser("binding-approval-build")
    command.add_argument("proposal", type=Path)
    command.add_argument("draft", type=Path)
    command.add_argument("--reviewer", required=True)
    command.add_argument("--target-entity-id", required=True)
    command.add_argument("--target-financial-scope", required=True)
    command.add_argument("--approved-field", action="append", default=[])
    command.add_argument("--approved-at", required=True)
    command = sub.add_parser("binding-approval-validate")
    command.add_argument("approval", type=Path)
    command.add_argument("proposal", type=Path)
    command.add_argument("draft", type=Path)
    command = sub.add_parser("binding-apply")
    command.add_argument("proposal", type=Path)
    command.add_argument("draft", type=Path)
    command.add_argument("approval", type=Path)
    sub.add_parser("bound-draft-validate").add_argument("result", type=Path)

    command = sub.add_parser("web")
    command.add_argument("--host", default="127.0.0.1")
    command.add_argument("--port", type=int, default=8765)
    return parser


def _run(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "market-price-candidate-build":
            _dump(build_market_price_candidate(
                price=args.price,
                currency=args.currency,
                entity_id=args.entity_id,
                financial_scope=args.financial_scope,
                instrument_id=args.instrument_id,
                symbol=args.symbol,
                venue=args.venue,
                quote_type=args.quote_type,
                trading_date=args.trading_date,
                observed_at=args.observed_at,
                as_of=args.as_of,
                source_publisher=args.source_publisher,
                source_type=args.source_type,
                source_tier=args.source_tier,
                source_locator=args.source_locator,
                source_snapshot_sha256=args.source_snapshot_sha256,
                max_age_days=args.max_age_days,
            ))
            return 0
        if args.command == "market-price-candidate-validate":
            _dump(validate_market_price_candidate(_obj(args.file, "market-price candidate")))
            return 0
        if args.command == "market-price-review-build":
            _dump(build_market_price_review_assertion(
                _obj(args.candidate, "market-price candidate"),
                reviewer=args.reviewer,
                approved_at=args.approved_at,
                review_basis=args.review_basis,
            ))
            return 0
        if args.command == "market-price-review-validate":
            _dump(validate_market_price_review_assertion(
                _obj(args.assertion, "market-price review assertion"),
                _obj(args.candidate, "market-price candidate"),
            ))
            return 0
        if args.command == "market-price-finalize":
            _dump(finalize_reviewed_market_price(
                _obj(args.candidate, "market-price candidate"),
                _obj(args.assertion, "market-price review assertion"),
            ))
            return 0
        if args.command == "market-price-validate":
            _dump(validate_reviewed_market_price(_obj(args.file, "reviewed market-price package")))
            return 0
        if args.command == "binding-build-with-market-price":
            _dump(build_binding_proposal_with_market_price(
                _obj(args.base_proposal, "v0.6 base binding proposal"),
                _obj(args.market_price_package, "reviewed market-price package"),
            ))
            return 0
        if args.command == "binding-validate":
            _dump(validate_binding_proposal_any(_obj(args.file, "binding proposal")))
            return 0
        if args.command == "binding-approval-build":
            _dump(build_binding_approval(
                _obj(args.proposal, "binding proposal"),
                _obj(args.draft, "Draft"),
                reviewer=args.reviewer,
                target_entity_id=args.target_entity_id,
                target_financial_scope=args.target_financial_scope,
                approved_fields=args.approved_field,
                approved_at=args.approved_at,
            ))
            return 0
        if args.command == "binding-approval-validate":
            _dump(validate_binding_approval(
                _obj(args.approval, "binding approval"),
                _obj(args.proposal, "binding proposal"),
                _obj(args.draft, "Draft"),
            ))
            return 0
        if args.command == "binding-apply":
            _dump(apply_binding_approval(
                _obj(args.proposal, "binding proposal"),
                _obj(args.draft, "Draft"),
                _obj(args.approval, "binding approval"),
            ))
            return 0
        if args.command == "bound-draft-validate":
            _dump(validate_bound_draft_result(_obj(args.result, "bound Draft result")))
            return 0
        if args.command == "web":
            if args.as_json:
                raise CaseServiceError("--json is not valid with web / web 명령은 --json을 지원하지 않습니다")
            serve_web(host=args.host, port=args.port, root=args.root)
            return 0
        raise CaseServiceError("unsupported M27 command / 미지원 M27 명령")
    except (CaseServiceError, ValueError, OSError, KeyError, TypeError) as exc:
        return _error(args, exc)


def main(argv: list[str] | None = None) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    if _command(values) is not None:
        return _run(values)
    return prior_cli.main(values)


if __name__ == "__main__":
    raise SystemExit(main())
