"""M30-R8 CLI: fail-closed source-bound R6 to Draft and M29 handoff."""
import argparse
import json
import sys
from pathlib import Path
from valuation_hub import cli_entry_m30r7 as prior
from valuation_hub.case_service import CaseServiceError
from valuation_hub.r8_assumption_proof import build_r6_binding_proof, validate_r6_binding_proof
from valuation_hub.r8_assumption_proposal import (
    build_r6_v3_proposal, build_assumption_proposal,
    validate_assumption_proposal, validate_r6_v3_proposal,
)
from valuation_hub.r8_assumption_approval import build_assumption_approval, validate_assumption_approval
from valuation_hub.r8_draft_kernel import apply_approval, validate_bound_result

COMMANDS = {
    "r8-proof-build", "r8-proof-validate", "r8-m23-build",
    "r8-m23-validate", "r8-proposal-build", "r8-proposal-validate",
    "r8-approval-build", "r8-approval-validate", "r8-apply", "r8-bound-validate",
}

def _load(path, root):
    p = path if path.is_absolute() else root / path
    try:
        result = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CaseServiceError("R8 input file unreadable") from exc
    if not isinstance(result, dict):
        raise CaseServiceError("R8 input must be JSON object")
    return result

def _parser():
    p = argparse.ArgumentParser(prog="vih")
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--json", dest="as_json", action="store_true")
    sub = p.add_subparsers(dest="command", required=True)
    def positional(cmd, *names):
        parser = sub.add_parser(cmd)
        for name in names:
            parser.add_argument(name, type=Path)
        return parser
    positional("r8-proof-build", "package", "base_context", "hold_inventory", "historical_dilution", "envelope")
    positional("r8-proof-validate", "proof")
    positional("r8-m23-build", "base_v02", "proof")
    positional("r8-m23-validate", "proposal")
    positional("r8-proposal-build", "base_v08", "proof")
    positional("r8-proposal-validate", "proposal")
    appr = positional("r8-approval-build", "proposal", "draft")
    appr.add_argument("--reviewer", required=True)
    appr.add_argument("--entity-id", required=True)
    appr.add_argument("--financial-scope", required=True)
    appr.add_argument("--field", action="append", required=True)
    appr.add_argument("--approved-at", required=True)
    positional("r8-approval-validate", "approval", "proposal", "draft")
    positional("r8-apply", "proposal", "draft", "approval")
    positional("r8-bound-validate", "result")
    return p

def _run(argv):
    a = _parser().parse_args(argv)
    root = a.root.resolve()
    def inp(name):
        return _load(getattr(a, name), root)
    try:
        command = a.command
        if command == "r8-proof-build":
            answer = build_r6_binding_proof(inp("package"), inp("base_context"),
                                             inp("hold_inventory"), inp("historical_dilution"), inp("envelope"))
        elif command == "r8-proof-validate":
            answer = validate_r6_binding_proof(inp("proof"))
        elif command == "r8-m23-build":
            answer = build_r6_v3_proposal(inp("base_v02"), inp("proof"))
        elif command == "r8-m23-validate":
            answer = validate_r6_v3_proposal(inp("proposal"))
        elif command == "r8-proposal-build":
            answer = build_assumption_proposal(inp("base_v08"), inp("proof"))
        elif command == "r8-proposal-validate":
            answer = validate_assumption_proposal(inp("proposal"))
        elif command == "r8-approval-build":
            answer = build_assumption_approval(inp("proposal"), inp("draft"),
                      reviewer=a.reviewer, target_entity_id=a.entity_id,
                      target_financial_scope=a.financial_scope,
                      approved_fields=a.field, approved_at=a.approved_at)
        elif command == "r8-approval-validate":
            answer = validate_assumption_approval(inp("approval"), inp("proposal"), inp("draft"))
        elif command == "r8-apply":
            answer = apply_approval(inp("proposal"), inp("draft"), inp("approval"))
        elif command == "r8-bound-validate":
            answer = validate_bound_result(inp("result"))
        else:
            raise CaseServiceError("unsupported R8 operation")
        print(json.dumps(answer, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    except (CaseServiceError, ValueError, TypeError, KeyError, OSError, AttributeError) as exc:
        print(json.dumps({"ok":False, "error":str(exc)}, ensure_ascii=False) if a.as_json else str(exc), file=sys.stderr)
        return 2

def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if any(x in COMMANDS for x in args):
        return _run(args)
    return prior.main(args)

if __name__ == "__main__":
    raise SystemExit(main())
