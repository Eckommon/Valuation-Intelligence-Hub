"""M30 additive CLI wrapper / M30 추가형 CLI wrapper.

The identifying SEC User-Agent is accepted only through the SEC_USER_AGENT runtime
environment variable. M30-E additionally provides local immutable intake for already-
acquired non-SEC UTF-8 sources; it performs no generic network fetch.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from valuation_hub import cli_entry_m29 as prior_cli
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.external_source import (
    SOURCE_TIERS as EXTERNAL_SOURCE_TIERS,
    build_external_source_snapshot,
    build_market_price_candidate_from_snapshot,
    build_terminal_growth_anchor_from_snapshot,
    build_wacc_source_input_from_snapshot,
    load_external_source_snapshot,
    materialize_external_source_snapshot,
    validate_external_source_snapshot,
)
from valuation_hub.market_price import QUOTE_TYPES
from valuation_hub.real_case_preflight_m30b import build_real_equity_source_preflight_v2
from valuation_hub.real_case_readiness import (
    build_real_equity_readiness_manifest,
    validate_real_equity_readiness_manifest,
)
from valuation_hub.sec_live import (
    capture_companyfacts_snapshot,
    load_source_snapshot,
    materialize_source_snapshot,
    validate_source_snapshot,
)
from valuation_hub.terminal_growth_assumption import (
    REQUIRED_ANCHORS,
    SOURCE_CLAIM_CLASSES as TERMINAL_CLAIM_CLASSES,
)
from valuation_hub.wacc_assumption import (
    REQUIRED_METRICS,
    SOURCE_CLAIM_CLASSES as WACC_CLAIM_CLASSES,
)

SEC_USER_AGENT_ENV = "SEC_USER_AGENT"
INTERCEPT = {
    "sec-companyfacts-fetch",
    "sec-source-snapshot-validate",
    "real-equity-preflight-v2",
    "real-equity-readiness-build",
    "real-equity-readiness-validate",
    "external-source-snapshot-build",
    "external-source-snapshot-validate",
    "market-price-candidate-build-from-snapshot",
    "wacc-source-build-from-snapshot",
    "terminal-growth-anchor-build-from-snapshot",
}


def _dump(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _command(argv: list[str]) -> str | None:
    return next((item for item in argv if item in INTERCEPT), None)


def _error(args: Any, exc: Exception) -> int:
    if getattr(args, "as_json", False):
        _dump({"ok": False, "error": str(exc)})
    else:
        print(f"ERROR / 오류: {exc}", file=sys.stderr)
    return 2


def _runtime_sec_user_agent() -> str:
    value = os.environ.get(SEC_USER_AGENT_ENV, "").strip()
    if not value:
        raise CaseServiceError(
            "SEC_USER_AGENT environment variable required; do not commit or pass the identifying value as a CLI argument / "
            "SEC_USER_AGENT 환경변수가 필요합니다. 식별값을 저장소에 커밋하거나 CLI 인자로 전달하지 마십시오"
        )
    if "@" not in value or len(value) < 8:
        raise CaseServiceError(
            "SEC_USER_AGENT must be an identifying SEC User-Agent containing a contact email / "
            "SEC_USER_AGENT에는 연락 이메일이 포함된 식별 User-Agent가 필요합니다"
        )
    return value


def _repo_root(root: Path | None) -> Path:
    return root.resolve() if root is not None else find_repo_root()


def _snapshot_output(output: Path, root: Path | None, *, label: str = "source snapshot") -> tuple[Path, Path]:
    repo = _repo_root(root)
    target = output if output.is_absolute() else repo / output
    resolved = target.resolve()
    allowed = (repo / "workspace" / "source_snapshots").resolve()
    try:
        resolved.relative_to(allowed)
    except ValueError as exc:
        raise CaseServiceError(
            f"{label} output must be under workspace/source_snapshots / {label} 출력은 workspace/source_snapshots 아래여야 합니다"
        ) from exc
    return repo, resolved


def _snapshot_input(path: Path, root: Path | None) -> Path:
    repo = _repo_root(root)
    return path.resolve() if path.is_absolute() else (repo / path).resolve()


def _json_input(path: Path, root: Path | None) -> dict[str, Any]:
    resolved = _snapshot_input(path, root)
    try:
        value = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CaseServiceError(f"JSON input unreadable: {resolved} / JSON 입력 읽기 실패") from exc
    if not isinstance(value, dict):
        raise CaseServiceError("JSON input must be object / JSON 입력은 객체여야 함")
    return value


def _utf8_input(path: Path, root: Path | None) -> str:
    resolved = _snapshot_input(path, root)
    try:
        return resolved.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeError) as exc:
        raise CaseServiceError(f"UTF-8 source input unreadable: {resolved} / UTF-8 원문 입력 읽기 실패") from exc


def _external_snapshot(path: Path, root: Path | None) -> dict[str, Any]:
    resolved = _snapshot_input(path, root)
    snapshot = load_external_source_snapshot(resolved)
    validate_external_source_snapshot(snapshot)
    return snapshot


def _add_target_arguments(command: argparse.ArgumentParser) -> None:
    command.add_argument("--case-id", required=True)
    command.add_argument("--legal-name", required=True)
    command.add_argument("--ticker", required=True)
    command.add_argument("--exchange", required=True)
    command.add_argument("--cik", required=True)
    command.add_argument("--financial-period-end", required=True)
    command.add_argument("--valuation-as-of", required=True)
    command.add_argument("--form", default="10-Q")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vih")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--json", action="store_true", dest="as_json")
    sub = parser.add_subparsers(dest="command", required=True)

    command = sub.add_parser("sec-companyfacts-fetch")
    command.add_argument("cik")
    command.add_argument("--output", type=Path, required=True)
    sub.add_parser("sec-source-snapshot-validate").add_argument("snapshot", type=Path)

    command = sub.add_parser("real-equity-preflight-v2")
    command.add_argument("snapshot", type=Path)
    _add_target_arguments(command)
    command.add_argument("--shares-period-end", default=None)

    command = sub.add_parser("real-equity-readiness-build")
    _add_target_arguments(command)
    command.add_argument("--preflight", type=Path, default=None)
    sub.add_parser("real-equity-readiness-validate").add_argument("manifest", type=Path)

    command = sub.add_parser("external-source-snapshot-build")
    command.add_argument("input", type=Path)
    command.add_argument("--publisher", required=True)
    command.add_argument("--source-type", required=True)
    command.add_argument("--source-tier", required=True, choices=EXTERNAL_SOURCE_TIERS)
    command.add_argument("--source-locator", required=True)
    command.add_argument("--captured-at", required=True)
    command.add_argument("--output", type=Path, required=True)
    sub.add_parser("external-source-snapshot-validate").add_argument("snapshot", type=Path)

    command = sub.add_parser("market-price-candidate-build-from-snapshot")
    command.add_argument("snapshot", type=Path)
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
    command.add_argument("--max-age-days", type=int, default=7)

    command = sub.add_parser("wacc-source-build-from-snapshot")
    command.add_argument("snapshot", type=Path)
    command.add_argument("--metric", required=True, choices=REQUIRED_METRICS)
    command.add_argument("--value", required=True, type=float)
    command.add_argument("--unit", required=True)
    command.add_argument("--observed-on", required=True)
    command.add_argument("--claim-class", required=True, choices=WACC_CLAIM_CLASSES)

    command = sub.add_parser("terminal-growth-anchor-build-from-snapshot")
    command.add_argument("snapshot", type=Path)
    command.add_argument("--metric", required=True, choices=REQUIRED_ANCHORS)
    command.add_argument("--value", required=True, type=float)
    command.add_argument("--observed-on", required=True)
    command.add_argument("--claim-class", required=True, choices=TERMINAL_CLAIM_CLASSES)
    return parser


def _run(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "sec-companyfacts-fetch":
            repo, output = _snapshot_output(args.output, args.root, label="SEC snapshot")
            user_agent = _runtime_sec_user_agent()
            snapshot = capture_companyfacts_snapshot(args.cik, user_agent=user_agent)
            result = materialize_source_snapshot(snapshot, output, repo)
            _dump({
                **result,
                "cik": snapshot["request"]["cik"],
                "body_sha256": snapshot["response"]["body_sha256"],
                "fetched_at": snapshot["response"]["fetched_at"],
                "user_agent_persisted": False,
                "next_action": "RUN_SEC_SOURCE_SNAPSHOT_VALIDATE_THEN_REAL_EQUITY_PREFLIGHT_V2",
            })
            return 0

        if args.command == "sec-source-snapshot-validate":
            path = _snapshot_input(args.snapshot, args.root)
            snapshot = load_source_snapshot(path)
            checked = validate_source_snapshot(snapshot)
            if SEC_USER_AGENT_ENV in json.dumps(snapshot, ensure_ascii=False):
                raise CaseServiceError("snapshot unexpectedly contains environment-variable identifier / snapshot에 환경변수 식별자가 포함됨")
            _dump({**checked, "path": str(path), "user_agent_persisted": False})
            return 0

        if args.command == "real-equity-preflight-v2":
            repo = _repo_root(args.root)
            path = _snapshot_input(args.snapshot, repo)
            snapshot = load_source_snapshot(path)
            _dump(build_real_equity_source_preflight_v2(
                case_id=args.case_id,
                legal_name=args.legal_name,
                ticker=args.ticker,
                exchange=args.exchange,
                cik=args.cik,
                financial_period_end=args.financial_period_end,
                valuation_as_of=args.valuation_as_of,
                sec_snapshot=snapshot,
                root=repo,
                form=args.form,
                shares_period_end=args.shares_period_end,
            ))
            return 0

        if args.command == "real-equity-readiness-build":
            preflight = _json_input(args.preflight, args.root) if args.preflight is not None else None
            _dump(build_real_equity_readiness_manifest(
                case_id=args.case_id,
                legal_name=args.legal_name,
                ticker=args.ticker,
                exchange=args.exchange,
                cik=args.cik,
                financial_period_end=args.financial_period_end,
                valuation_as_of=args.valuation_as_of,
                form=args.form,
                preflight=preflight,
            ))
            return 0

        if args.command == "real-equity-readiness-validate":
            _dump(validate_real_equity_readiness_manifest(_json_input(args.manifest, args.root)))
            return 0

        if args.command == "external-source-snapshot-build":
            repo, output = _snapshot_output(args.output, args.root, label="external source snapshot")
            snapshot = build_external_source_snapshot(
                _utf8_input(args.input, repo),
                source_publisher=args.publisher,
                source_type=args.source_type,
                source_tier=args.source_tier,
                source_locator=args.source_locator,
                captured_at=args.captured_at,
            )
            _dump(materialize_external_source_snapshot(snapshot, output, repo))
            return 0

        if args.command == "external-source-snapshot-validate":
            snapshot = _external_snapshot(args.snapshot, args.root)
            _dump(validate_external_source_snapshot(snapshot))
            return 0

        if args.command == "market-price-candidate-build-from-snapshot":
            _dump(build_market_price_candidate_from_snapshot(
                _external_snapshot(args.snapshot, args.root),
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
                max_age_days=args.max_age_days,
            ))
            return 0

        if args.command == "wacc-source-build-from-snapshot":
            _dump(build_wacc_source_input_from_snapshot(
                _external_snapshot(args.snapshot, args.root),
                metric=args.metric,
                value=args.value,
                unit=args.unit,
                observed_on=args.observed_on,
                claim_class=args.claim_class,
            ))
            return 0

        if args.command == "terminal-growth-anchor-build-from-snapshot":
            _dump(build_terminal_growth_anchor_from_snapshot(
                _external_snapshot(args.snapshot, args.root),
                metric=args.metric,
                value=args.value,
                observed_on=args.observed_on,
                claim_class=args.claim_class,
            ))
            return 0

        raise CaseServiceError("unsupported M30 command / 미지원 M30 명령")
    except (CaseServiceError, ValueError, OSError, KeyError, TypeError) as exc:
        return _error(args, exc)


def main(argv: list[str] | None = None) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    if _command(values) is not None:
        return _run(values)
    return prior_cli.main(values)


if __name__ == "__main__":
    raise SystemExit(main())
