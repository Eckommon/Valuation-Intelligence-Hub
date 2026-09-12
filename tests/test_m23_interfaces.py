"""M23 CLI/Web share-aware binding interface contracts."""
from __future__ import annotations

from pathlib import Path

from valuation_hub import cli_entry
from valuation_hub.web_share_binding import render_share_binding_lab


def test_cli_dispatch_exposes_m23_share_aware_binding_command()->None:
    assert cli_entry._command(["binding-build-with-diluted-shares"]) == "binding-build-with-diluted-shares"
    assert cli_entry._command(["binding-validate"]) == "binding-validate"


def test_binding_parser_accepts_base_proposal_and_share_bridge_paths()->None:
    args=cli_entry._binding_parser().parse_args([
        "binding-build-with-diluted-shares",
        "base.json",
        "bridge.json",
    ])
    assert args.command=="binding-build-with-diluted-shares"
    assert args.base_proposal==Path("base.json")
    assert args.share_bridge==Path("bridge.json")


def test_web_share_binding_lab_is_proposal_only_and_no_write()->None:
    page=render_share_binding_lab()
    assert "COMPLETE REVIEWED BRIDGE ONLY · PROPOSAL ONLY · NO WRITE" in page
    assert "M23 may replace only" in page
    assert "equity.diluted_shares" in page
    assert "/api/share-binding/build" in page
    assert "/api/share-binding/validate" in page
    assert "/api/share-binding/apply" not in page
    assert "/api/share-binding/file-write" not in page
    assert "/api/share-binding/canonical" not in page
    assert "NO DRAFT APPLY · NO FILE WRITE · NO CANONICAL WRITE" in page
