"""M28 additive CLI wrapper / M28 추가형 CLI wrapper."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from valuation_hub import cli_entry_m27 as prior_cli
from valuation_hub.binding_apply_m28 import apply_binding_approval, build_binding_approval, validate_binding_approval, validate_bound_draft_result
from valuation_hub.case_service import CaseServiceError
from valuation_hub.minority_interest import (
    build_minority_interest_review_assertion,
    extract_dart_minority_interest_candidate,
    extract_sec_minority_interest_candidate,
    finalize_reviewed_minority_interest,
    normalize_minority_interest_candidate,
    validate_minority_interest_candidate,
    validate_minority_interest_observation,
    validate_minority_interest_review_assertion,
    validate_reviewed_minority_interest,
)
from valuation_hub.minority_interest_draft_binding import build_binding_proposal_with_minority_interest, validate_binding_proposal_any
from valuation_hub.web_minority_interest import serve as serve_web

MINORITY_COMMANDS = {
    "minority-sec-extract", "minority-dart-extract", "minority-candidate-validate",
    "minority-normalize", "minority-observation-validate", "minority-review-build",
    "minority-review-validate", "minority-finalize", "minority-validate",
    "binding-build-with-minority-interest",
}
APPLY_COMMANDS = {"binding-approval-build", "binding-approval-validate", "binding-apply", "bound-draft-validate"}
INTERCEPT = MINORITY_COMMANDS | APPLY_COMMANDS | {"binding-validate", "web"}


def _dump(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _load(path: Path, label: str) -> Any:
    try: return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc: raise CaseServiceError(f"{label} file not found / {label} 파일 없음: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc: raise CaseServiceError(f"{label} read failed / {label} 읽기 실패: {path}") from exc


def _obj(path: Path, label: str) -> dict[str, Any]:
    value = _load(path, label)
    if not isinstance(value, dict): raise CaseServiceError(f"{label} JSON object required / {label} JSON 객체 필요")
    return value


def _command(argv: list[str]) -> str | None:
    return next((item for item in argv if item in INTERCEPT), None)


def _error(args: Any, exc: Exception) -> int:
    if getattr(args, "as_json", False): _dump({"ok": False, "error": str(exc)})
    else: print(f"ERROR / 오류: {exc}", file=sys.stderr)
    return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vih")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--json", action="store_true", dest="as_json")
    sub = parser.add_subparsers(dest="command", required=True)

    command = sub.add_parser("minority-sec-extract")
    command.add_argument("snapshot", type=Path); command.add_argument("--form", default=None); command.add_argument("--period-end", default=None)
    sub.add_parser("minority-dart-extract").add_argument("snapshot", type=Path)
    sub.add_parser("minority-candidate-validate").add_argument("file", type=Path)
    sub.add_parser("minority-normalize").add_argument("candidate", type=Path)
    sub.add_parser("minority-observation-validate").add_argument("file", type=Path)

    command = sub.add_parser("minority-review-build")
    command.add_argument("observation", type=Path); command.add_argument("--as-of", required=True); command.add_argument("--reviewer", required=True)
    command.add_argument("--approved-at", required=True); command.add_argument("--review-basis", required=True); command.add_argument("--asserted-period-end", default=None)
    command.add_argument("--max-age-days", type=int, default=550)
    command = sub.add_parser("minority-review-validate")
    command.add_argument("assertion", type=Path); command.add_argument("observation", type=Path)
    command = sub.add_parser("minority-finalize")
    command.add_argument("observation", type=Path); command.add_argument("assertion", type=Path)
    sub.add_parser("minority-validate").add_argument("file", type=Path)

    command = sub.add_parser("binding-build-with-minority-interest")
    command.add_argument("base_proposal", type=Path); command.add_argument("minority_interest_package", type=Path)
    sub.add_parser("binding-validate").add_argument("file", type=Path)

    command = sub.add_parser("binding-approval-build")
    command.add_argument("proposal", type=Path); command.add_argument("draft", type=Path); command.add_argument("--reviewer", required=True)
    command.add_argument("--target-entity-id", required=True); command.add_argument("--target-financial-scope", required=True)
    command.add_argument("--approved-field", action="append", default=[]); command.add_argument("--approved-at", required=True)
    command = sub.add_parser("binding-approval-validate")
    command.add_argument("approval", type=Path); command.add_argument("proposal", type=Path); command.add_argument("draft", type=Path)
    command = sub.add_parser("binding-apply")
    command.add_argument("proposal", type=Path); command.add_argument("draft", type=Path); command.add_argument("approval", type=Path)
    sub.add_parser("bound-draft-validate").add_argument("result", type=Path)

    command = sub.add_parser("web"); command.add_argument("--host", default="127.0.0.1"); command.add_argument("--port", type=int, default=8765)
    return parser


def _run(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "minority-sec-extract":
            _dump(extract_sec_minority_interest_candidate(_obj(args.snapshot, "SEC snapshot"), form=args.form, period_end=args.period_end)); return 0
        if args.command == "minority-dart-extract":
            _dump(extract_dart_minority_interest_candidate(_obj(args.snapshot, "OpenDART snapshot"))); return 0
        if args.command == "minority-candidate-validate":
            _dump(validate_minority_interest_candidate(_obj(args.file, "minority-interest candidate"))); return 0
        if args.command == "minority-normalize":
            _dump(normalize_minority_interest_candidate(_obj(args.candidate, "minority-interest candidate"))); return 0
        if args.command == "minority-observation-validate":
            _dump(validate_minority_interest_observation(_obj(args.file, "minority-interest observation"))); return 0
        if args.command == "minority-review-build":
            _dump(build_minority_interest_review_assertion(
                _obj(args.observation, "minority-interest observation"), as_of=args.as_of, reviewer=args.reviewer,
                approved_at=args.approved_at, review_basis=args.review_basis, asserted_period_end=args.asserted_period_end,
                max_age_days=args.max_age_days,
            )); return 0
        if args.command == "minority-review-validate":
            _dump(validate_minority_interest_review_assertion(_obj(args.assertion, "minority-interest review"), _obj(args.observation, "minority-interest observation"))); return 0
        if args.command == "minority-finalize":
            _dump(finalize_reviewed_minority_interest(_obj(args.observation, "minority-interest observation"), _obj(args.assertion, "minority-interest review"))); return 0
        if args.command == "minority-validate":
            _dump(validate_reviewed_minority_interest(_obj(args.file, "reviewed minority-interest package"))); return 0
        if args.command == "binding-build-with-minority-interest":
            _dump(build_binding_proposal_with_minority_interest(_obj(args.base_proposal, "v0.7 base proposal"), _obj(args.minority_interest_package, "reviewed minority-interest package"))); return 0
        if args.command == "binding-validate":
            _dump(validate_binding_proposal_any(_obj(args.file, "binding proposal"))); return 0
        if args.command == "binding-approval-build":
            _dump(build_binding_approval(_obj(args.proposal, "binding proposal"), _obj(args.draft, "Draft"), reviewer=args.reviewer, target_entity_id=args.target_entity_id, target_financial_scope=args.target_financial_scope, approved_fields=args.approved_field, approved_at=args.approved_at)); return 0
        if args.command == "binding-approval-validate":
            _dump(validate_binding_approval(_obj(args.approval, "binding approval"), _obj(args.proposal, "binding proposal"), _obj(args.draft, "Draft"))); return 0
        if args.command == "binding-apply":
            _dump(apply_binding_approval(_obj(args.proposal, "binding proposal"), _obj(args.draft, "Draft"), _obj(args.approval, "binding approval"))); return 0
        if args.command == "bound-draft-validate":
            _dump(validate_bound_draft_result(_obj(args.result, "bound Draft result"))); return 0
        if args.command == "web":
            if args.as_json: raise CaseServiceError("--json is not valid with web / web 명령은 --json을 지원하지 않습니다")
            serve_web(host=args.host, port=args.port, root=args.root); return 0
        raise CaseServiceError("unsupported M28 command / 미지원 M28 명령")
    except (CaseServiceError, ValueError, OSError, KeyError, TypeError) as exc:
        return _error(args, exc)


def main(argv: list[str] | None = None) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    if _command(values) is not None: return _run(values)
    return prior_cli.main(values)


if __name__ == "__main__": raise SystemExit(main())
