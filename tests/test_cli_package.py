"""Promotion-package CLI tests / 승격 패키지 CLI 테스트."""

from __future__ import annotations

import json
from pathlib import Path

from valuation_hub import cli
from valuation_hub.draft_service import template
from valuation_hub.promotion import build_candidate, validate_candidate

ROOT = Path(__file__).resolve().parents[1]


def _approved_candidate() -> dict:
    candidate = build_candidate(template("equity_fcff", ROOT))
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
            claim_id = "cli_pkg_" + path.replace(".", "_")
            binding.update({"class": "FACT", "claim_ids": [claim_id], "rationale": "Observed."})
            evidence.append({
                "claim_id": claim_id, "class": "FACT", "metric": path, "value": observed[path],
                "unit": draft["currency"], "as_of": "2026-09-11", "status": "CURRENT", "waiver": None,
                "source": {"publisher": "CLI package test", "locator": "https://example.invalid/cli-package", "tier": "B"},
            })
        else:
            binding.update({"class": "ASSUMPTION", "claim_ids": [], "rationale": "Reviewed assumption."})
    candidate["evidence"] = evidence
    assessment = validate_candidate(candidate)
    candidate["review"] = {
        "decision": "APPROVE", "reviewer": "cli-package-reviewer",
        "reviewed_at": "2026-09-11T15:00:00+09:00", "rationale": "Reviewed for package staging.",
        "scope_sha256": assessment["review_scope_sha256"],
    }
    return candidate


def test_cli_package_build_json_and_validate(tmp_path: Path, capsys) -> None:
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text(json.dumps(_approved_candidate()), encoding="utf-8")
    args = [
        "--root", str(ROOT), "package-build", str(candidate_path),
        "--case-id", "KR_CLI_PACKAGE_TEST", "--name-en", "CLI Package Test",
        "--name-ko", "CLI 패키지 테스트", "--asset-class", "public_equity",
    ]
    assert cli.main(args) == 0
    package = json.loads(capsys.readouterr().out)
    assert package["status"] == "PROMOTION_PACKAGE_STAGED"
    assert package["canonical"] is False

    package_path = tmp_path / "package.json"
    package_path.write_text(json.dumps(package), encoding="utf-8")
    assert cli.main(["--root", str(ROOT), "--json", "package-validate", str(package_path)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["valid"] is True
    assert result["case_id"] == "KR_CLI_PACKAGE_TEST"


def test_cli_package_materializes_only_to_explicit_output(tmp_path: Path, capsys) -> None:
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text(json.dumps(_approved_candidate()), encoding="utf-8")
    output = tmp_path / "materialized"
    args = [
        "--root", str(ROOT), "--json", "package-build", str(candidate_path),
        "--case-id", "KR_CLI_PACKAGE_DISK", "--name-en", "CLI Package Disk",
        "--name-ko", "CLI 패키지 디스크", "--asset-class", "public_equity",
        "--output-dir", str(output),
    ]
    assert cli.main(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["materialized"] is True
    assert (output / "PACKAGE.json").is_file()
    assert cli.main(["--root", str(ROOT), "package-validate", str(output)]) == 0
    assert "PROMOTION_PACKAGE_STAGED" in capsys.readouterr().out


def test_cli_package_rejects_canonical_case_collision(tmp_path: Path, capsys) -> None:
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text(json.dumps(_approved_candidate()), encoding="utf-8")
    rc = cli.main([
        "--root", str(ROOT), "package-build", str(candidate_path),
        "--case-id", "KR_010120_LS_ELECTRIC", "--name-en", "Collision",
        "--name-ko", "충돌", "--asset-class", "public_equity",
    ])
    assert rc == 2
    assert "충돌" in capsys.readouterr().err
