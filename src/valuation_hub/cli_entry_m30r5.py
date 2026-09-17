"""M30-R5 additive CLI wrapper for AI market-price authority."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from valuation_hub import cli_entry_m30r4 as prior_cli
from valuation_hub.ai_market_price_authority import (
    build_ai_market_price_adjudication,
    build_ai_market_price_evidence,
    build_ai_reviewed_market_price,
    validate_ai_market_price_adjudication,
    validate_ai_market_price_evidence,
    validate_ai_reviewed_market_price,
)
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.external_source import load_external_source_snapshot, validate_external_source_snapshot

INTERCEPT = {
    "market-price-ai-evidence-build",
    "market-price-ai-evidence-validate",
    "market-price-ai-adjudicate",
    "market-price-ai-adjudication-validate",
    "market-price-ai-finalize",
    "market-price-ai-package-validate",
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


def _snapshot(value: Path, root: Path) -> dict[str, Any]:
    snap = load_external_source_snapshot(_path(value, root)); validate_external_source_snapshot(snap); return snap


def _excerpt(value: Path, root: Path, label: str) -> str:
    try:
        text = _path(value, root).read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeError) as exc:
        raise CaseServiceError(f"{label} read failed / {label} 읽기 실패") from exc
    if not text:
        raise CaseServiceError(f"{label} empty / {label} 비어 있음")
    return text.rstrip("\r\n")


def _corroborations(value: Path, root: Path) -> list[dict[str, Any]]:
    try:
        rows = json.loads(_path(value, root).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CaseServiceError("corroborations manifest read failed / corroborations manifest 읽기 실패") from exc
    if not isinstance(rows, list):
        raise CaseServiceError("corroborations manifest array required / corroborations manifest 배열 필요")
    result = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("snapshot"), str) or not isinstance(row.get("excerpt"), str):
            raise CaseServiceError("corroboration row requires snapshot/excerpt paths / corroboration row snapshot/excerpt 경로 필요")
        result.append({"snapshot": _snapshot(Path(row["snapshot"]), root), "excerpt": _excerpt(Path(row["excerpt"]), root, "corroboration excerpt")})
    return result


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="vih")
    p.add_argument("--root", type=Path, default=None)
    p.add_argument("--json", action="store_true", dest="as_json")
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("market-price-ai-evidence-build")
    c.add_argument("candidate", type=Path); c.add_argument("primary_snapshot", type=Path)
    c.add_argument("--primary-excerpt", type=Path, required=True); c.add_argument("--corroborations", type=Path, required=True)
    c.add_argument("--contradiction-search-summary", required=True); c.add_argument("--material-contradiction", action="append", default=[])

    for name in ("market-price-ai-evidence-validate", "market-price-ai-adjudicate", "market-price-ai-adjudication-validate", "market-price-ai-finalize", "market-price-ai-package-validate"):
        c = sub.add_parser(name)
        if name == "market-price-ai-package-validate": c.add_argument("package", type=Path)
        if name in {"market-price-ai-adjudication-validate", "market-price-ai-finalize", "market-price-ai-package-validate"}: c.add_argument("adjudication", type=Path)
        if name in {"market-price-ai-evidence-validate", "market-price-ai-adjudicate", "market-price-ai-adjudication-validate", "market-price-ai-finalize", "market-price-ai-package-validate"}: c.add_argument("evidence", type=Path)
        c.add_argument("candidate", type=Path); c.add_argument("primary_snapshot", type=Path); c.add_argument("--corroborations", type=Path, required=True)
        if name == "market-price-ai-adjudicate": c.add_argument("--adjudicated-at", required=True)
    return p


def _run(argv: list[str]) -> int:
    args = _parser().parse_args(argv); root = _root(args.root)
    try:
        candidate = _obj(args.candidate, root, "candidate")
        primary = _snapshot(args.primary_snapshot, root)
        corrs = _corroborations(args.corroborations, root)
        if args.command == "market-price-ai-evidence-build":
            _dump(build_ai_market_price_evidence(candidate, primary, primary_excerpt=_excerpt(args.primary_excerpt, root, "primary excerpt"), corroborations=corrs, contradiction_search_summary=args.contradiction_search_summary, material_contradictions=args.material_contradiction)); return 0
        evidence = _obj(args.evidence, root, "evidence")
        if args.command == "market-price-ai-evidence-validate":
            _dump(validate_ai_market_price_evidence(evidence, candidate, primary, corrs)); return 0
        if args.command == "market-price-ai-adjudicate":
            _dump(build_ai_market_price_adjudication(candidate, evidence, primary, corrs, adjudicated_at=args.adjudicated_at)); return 0
        adjudication = _obj(args.adjudication, root, "adjudication")
        if args.command == "market-price-ai-adjudication-validate":
            _dump(validate_ai_market_price_adjudication(adjudication, candidate, evidence, primary, corrs)); return 0
        if args.command == "market-price-ai-finalize":
            _dump(build_ai_reviewed_market_price(candidate, evidence, adjudication, primary, corrs)); return 0
        if args.command == "market-price-ai-package-validate":
            _dump(validate_ai_reviewed_market_price(_obj(args.package, root, "package"), candidate, evidence, adjudication, primary, corrs)); return 0
        raise CaseServiceError("unsupported M30-R5 command / 미지원 M30-R5 명령")
    except (CaseServiceError, ValueError, OSError, KeyError, TypeError) as exc:
        if getattr(args, "as_json", False): _dump({"ok": False, "error": str(exc)})
        else: print(f"ERROR / 오류: {exc}", file=sys.stderr)
        return 2


def main(argv: list[str] | None = None) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    if _command(values) is not None: return _run(values)
    return prior_cli.main(values)


if __name__ == "__main__":
    raise SystemExit(main())
