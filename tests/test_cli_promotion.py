"""Promotion CLI workflow tests / 승격 CLI 흐름 테스트."""

from __future__ import annotations

import json
from pathlib import Path

from valuation_hub import cli
from valuation_hub.draft_service import template
from valuation_hub.promotion import validate_candidate

ROOT = Path(__file__).resolve().parents[1]


def _complete(candidate: dict) -> dict:
    draft = candidate["draft"]
    observed = {
        "market_price": draft["market_price"],
        "equity.diluted_shares": draft["equity"]["diluted_shares"],
        "equity.debt": draft["equity"]["debt"],
        "equity.cash": draft["equity"]["cash"],
        "equity.minority_interest": draft["equity"]["minority_interest"],
    }
    evidence = []
    for binding in candidate["input_governance"]:
        path = binding["path"]
        if path in observed:
            claim_id = "cli_" + path.replace(".", "_")
            binding.update({"class": "FACT", "claim_ids": [claim_id], "rationale": "Observed value."})
            evidence.append(
                {
                    "claim_id": claim_id,
                    "class": "FACT",
                    "metric": path,
                    "value": observed[path],
                    "unit": draft["currency"],
                    "as_of": "2026-09-11",
                    "status": "CURRENT",
                    "waiver": None,
                    "source": {"publisher": "CLI test evidence", "locator": "https://example.invalid/cli", "tier": "B"},
                }
            )
        else:
            binding.update({"class": "ASSUMPTION", "claim_ids": [], "rationale": "Reviewed forward assumption."})
    candidate["evidence"] = evidence
    return candidate


def test_cli_candidate_build_validate_and_promotion_check(tmp_path: Path, capsys) -> None:
    draft_path = tmp_path / "draft.json"
    draft_path.write_text(json.dumps(template("equity_fcff", ROOT)), encoding="utf-8")

    rc = cli.main(["--root", str(ROOT), "candidate-build", str(draft_path)])
    assert rc == 0
    candidate = json.loads(capsys.readouterr().out)
    assert candidate["status"] == "CANDIDATE_REVIEW"
    assert candidate["canonical"] is False

    candidate = _complete(candidate)
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    rc = cli.main(["--root", str(ROOT), "candidate-validate", str(candidate_path)])
    assert rc == 0
    output = capsys.readouterr().out
    assert "PASS CANDIDATE" in output
    assessment = validate_candidate(candidate)

    candidate["review"] = {
        "decision": "APPROVE",
        "reviewer": "cli-human-reviewer",
        "reviewed_at": "2026-09-11T14:30:00+09:00",
        "rationale": "Reviewed candidate for PR readiness.",
        "scope_sha256": assessment["review_scope_sha256"],
    }
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    rc = cli.main(["--root", str(ROOT), "--json", "promotion-check", str(candidate_path)])
    assert rc == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "REVIEW_APPROVED_READY_FOR_PR"
    assert result["canonical"] is False


def test_cli_candidate_validate_fails_closed_on_unclassified_skeleton(tmp_path: Path, capsys) -> None:
    draft_path = tmp_path / "draft.json"
    draft_path.write_text(json.dumps(template("equity_fcff", ROOT)), encoding="utf-8")
    rc = cli.main(["candidate-build", str(draft_path)])
    assert rc == 0
    candidate = json.loads(capsys.readouterr().out)
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    rc = cli.main(["candidate-validate", str(candidate_path)])
    assert rc == 2
    assert "Candidate" in capsys.readouterr().err
