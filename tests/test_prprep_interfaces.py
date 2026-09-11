"""M12 interface-boundary tests / M12 인터페이스 경계 테스트."""

from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from valuation_hub import cli
from valuation_hub.admission_apply import current_git_branch
from valuation_hub.web_prprep import make_handler, render_pr_prep_lab

ROOT = Path(__file__).resolve().parents[1]


def test_cli_exposes_plan_validate_and_explicit_target_apply_commands() -> None:
    parser = cli._parser()
    planned = parser.parse_args(["admission-plan", "admission.json", "--target-repo", "target"])
    assert planned.command == "admission-plan"
    assert str(planned.target_repo) == "target"
    validated = parser.parse_args(
        ["admission-plan-validate", "plan.json", "admission.json", "--target-repo", "target"]
    )
    assert validated.command == "admission-plan-validate"
    applied = parser.parse_args(
        ["admission-apply", "plan.json", "admission.json", "--target-repo", "target"]
    )
    assert applied.command == "admission-apply"


def test_pr_prep_page_is_explicitly_plan_only() -> None:
    page = render_pr_prep_lab()
    assert "PR Preparation Lab / PR 준비 랩" in page
    assert "PLAN ONLY · NO APPLY" in page
    assert "Browser write is intentionally unavailable" in page
    assert "/api/pr-prep/plan" in page
    assert "/api/pr-prep/validate" in page
    assert "/api/pr-prep/apply" not in page


def test_web_has_no_pr_prep_apply_endpoint() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        request = Request(
            base + "/api/pr-prep/apply",
            data=json.dumps({}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urlopen(request, timeout=4)
            raise AssertionError("unexpected Web apply endpoint")
        except HTTPError as exc:
            assert exc.code in {400, 404, 405}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=4)


def test_git_worktree_marker_resolves_admission_branch(tmp_path: Path) -> None:
    repo = tmp_path / "worktree"
    (repo / "registry").mkdir(parents=True)
    (repo / "registry" / "cases.json").write_text('{"cases": []}', encoding="utf-8")
    gitdir = tmp_path / "git-common" / "worktrees" / "admission"
    gitdir.mkdir(parents=True)
    (gitdir / "HEAD").write_text("ref: refs/heads/admission/worktree-case\n", encoding="utf-8")
    relative = gitdir.relative_to(repo.parent)
    (repo / ".git").write_text(f"gitdir: ../{relative.as_posix()}\n", encoding="utf-8")
    assert current_git_branch(repo) == "admission/worktree-case"
