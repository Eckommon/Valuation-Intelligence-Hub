"""M30 additive CLI wrapper / M30 추가형 CLI wrapper.

The identifying SEC User-Agent is accepted only through the SEC_USER_AGENT runtime
environment variable. It is never accepted as a CLI argument and the M13 snapshot
stores only `user_agent_provided=true`, not the identifying string.
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
from valuation_hub.real_case_preflight_m30b import build_real_equity_source_preflight_v2
from valuation_hub.sec_live import (
    capture_companyfacts_snapshot,
    load_source_snapshot,
    materialize_source_snapshot,
    validate_source_snapshot,
)

SEC_USER_AGENT_ENV = "SEC_USER_AGENT"
INTERCEPT = {
    "sec-companyfacts-fetch",
    "sec-source-snapshot-validate",
    "real-equity-preflight-v2",
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


def _snapshot_output(output: Path, root: Path | None) -> tuple[Path, Path]:
    repo = _repo_root(root)
    target = output if output.is_absolute() else repo / output
    resolved = target.resolve()
    allowed = (repo / "workspace" / "source_snapshots").resolve()
    try:
        resolved.relative_to(allowed)
    except ValueError as exc:
        raise CaseServiceError(
            "SEC snapshot output must be under workspace/source_snapshots / "
            "SEC snapshot 출력은 workspace/source_snapshots 아래여야 합니다"
        ) from exc
    return repo, resolved


def _snapshot_input(path: Path, root: Path | None) -> Path:
    repo = _repo_root(root)
    return path.resolve() if path.is_absolute() else (repo / path).resolve()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vih")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--json", action="store_true", dest="as_json")
    sub = parser.add_subparsers(dest="command", required=True)

    command = sub.add_parser("sec-companyfacts-fetch")
    command.add_argument("cik")
    command.add_argument("--output", type=Path, required=True)

    command = sub.add_parser("sec-source-snapshot-validate")
    command.add_argument("snapshot", type=Path)

    command = sub.add_parser("real-equity-preflight-v2")
    command.add_argument("snapshot", type=Path)
    command.add_argument("--case-id", required=True)
    command.add_argument("--legal-name", required=True)
    command.add_argument("--ticker", required=True)
    command.add_argument("--exchange", required=True)
    command.add_argument("--cik", required=True)
    command.add_argument("--financial-period-end", required=True)
    command.add_argument("--valuation-as-of", required=True)
    command.add_argument("--form", default="10-Q")
    command.add_argument("--shares-period-end", default=None)
    return parser


def _run(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "sec-companyfacts-fetch":
            # Resolve and reject unsafe output before reading credentials or network I/O.
            repo, output = _snapshot_output(args.output, args.root)
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
