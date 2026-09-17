"""M30-R2 additive CLI wrapper for evidence-first AI debt adjudication."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from valuation_hub import cli_entry_m30r1 as prior_cli
from valuation_hub.ai_debt_adjudication import (
    build_ai_sec_aggregate_debt_adjudication,
    build_ai_sec_aggregate_debt_evidence,
    build_legacy_compatible_ai_review_assertion,
    validate_ai_sec_aggregate_debt_adjudication,
    validate_ai_sec_aggregate_debt_evidence,
)
from valuation_hub.case_service import CaseServiceError
from valuation_hub.sec_aggregate_debt_authority import (
    build_sec_aggregate_debt_binding_context,
    finalize_reviewed_sec_aggregate_debt,
    validate_reviewed_sec_aggregate_debt,
    validate_sec_aggregate_debt_binding_context,
)

INTERCEPT = {
    "sec-aggregate-debt-ai-evidence-build",
    "sec-aggregate-debt-ai-evidence-validate",
    "sec-aggregate-debt-ai-adjudicate",
    "sec-aggregate-debt-ai-adjudication-validate",
    "sec-aggregate-debt-ai-review-build",
    "sec-aggregate-debt-finalize",
    "sec-aggregate-debt-profile-validate",
    "sec-aggregate-debt-context-build",
    "sec-aggregate-debt-context-validate",
}


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

    c = sub.add_parser("sec-aggregate-debt-ai-evidence-build")
    c.add_argument("observation", type=Path)
    c.add_argument("--primary-filing-locator", required=True)
    c.add_argument("--supporting-filing-locator", action="append", default=[])
    c.add_argument("--evidence-basis", required=True)
    c.add_argument("--contradiction-search-summary", required=True)
    c.add_argument("--material-contradiction", action="append", default=[])
    c.add_argument("--q1-financing-components-are-interest-bearing", action="store_true")
    c.add_argument("--q2-issuer-total-debt-reconciles-to-observation", action="store_true")
    c.add_argument("--q3-operating-lease-liabilities-separately-classified", action="store_true")
    c.add_argument("--q4-lease-exclusion-supported", action="store_true")

    c = sub.add_parser("sec-aggregate-debt-ai-evidence-validate")
    c.add_argument("evidence", type=Path)
    c.add_argument("observation", type=Path)

    c = sub.add_parser("sec-aggregate-debt-ai-adjudicate")
    c.add_argument("observation", type=Path)
    c.add_argument("evidence", type=Path)
    c.add_argument("--adjudicated-at", required=True)

    c = sub.add_parser("sec-aggregate-debt-ai-adjudication-validate")
    c.add_argument("adjudication", type=Path)
    c.add_argument("observation", type=Path)
    c.add_argument("evidence", type=Path)

    c = sub.add_parser("sec-aggregate-debt-ai-review-build")
    c.add_argument("observation", type=Path)
    c.add_argument("adjudication", type=Path)
    c.add_argument("evidence", type=Path)

    c = sub.add_parser("sec-aggregate-debt-finalize")
    c.add_argument("observation", type=Path)
    c.add_argument("assertion", type=Path)

    sub.add_parser("sec-aggregate-debt-profile-validate").add_argument("profile", type=Path)

    c = sub.add_parser("sec-aggregate-debt-context-build")
    c.add_argument("profile", type=Path)
    c.add_argument("--as-of", required=True)
    c.add_argument("--max-age-days", type=int, default=550)

    sub.add_parser("sec-aggregate-debt-context-validate").add_argument("context", type=Path)
    return parser


def _run(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "sec-aggregate-debt-ai-evidence-build":
            _dump(build_ai_sec_aggregate_debt_evidence(
                _obj(args.observation, "observation"),
                primary_filing_locator=args.primary_filing_locator,
                supporting_filing_locators=list(args.supporting_filing_locator),
                evidence_basis=args.evidence_basis,
                contradiction_search_summary=args.contradiction_search_summary,
                material_contradictions=list(args.material_contradiction),
                criteria={
                    "q1_financing_components_are_interest_bearing": args.q1_financing_components_are_interest_bearing,
                    "q2_issuer_total_debt_reconciles_to_observation": args.q2_issuer_total_debt_reconciles_to_observation,
                    "q3_operating_lease_liabilities_separately_classified": args.q3_operating_lease_liabilities_separately_classified,
                    "q4_lease_exclusion_supported": args.q4_lease_exclusion_supported,
                },
            ))
            return 0
        if args.command == "sec-aggregate-debt-ai-evidence-validate":
            _dump(validate_ai_sec_aggregate_debt_evidence(_obj(args.evidence, "AI evidence"), _obj(args.observation, "observation")))
            return 0
        if args.command == "sec-aggregate-debt-ai-adjudicate":
            _dump(build_ai_sec_aggregate_debt_adjudication(
                _obj(args.observation, "observation"),
                _obj(args.evidence, "AI evidence"),
                adjudicated_at=args.adjudicated_at,
            ))
            return 0
        if args.command == "sec-aggregate-debt-ai-adjudication-validate":
            _dump(validate_ai_sec_aggregate_debt_adjudication(
                _obj(args.adjudication, "AI adjudication"),
                _obj(args.observation, "observation"),
                _obj(args.evidence, "AI evidence"),
            ))
            return 0
        if args.command == "sec-aggregate-debt-ai-review-build":
            _dump(build_legacy_compatible_ai_review_assertion(
                _obj(args.observation, "observation"),
                _obj(args.adjudication, "AI adjudication"),
                _obj(args.evidence, "AI evidence"),
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
        raise CaseServiceError("unsupported M30-R2 command / 미지원 M30-R2 명령")
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
