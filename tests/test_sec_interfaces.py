"""M13 SEC CLI/Web interface tests / SEC CLI·Web 인터페이스 테스트."""

from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from valuation_hub import cli
from valuation_hub.sec_live import TransportResponse, capture_companyfacts_snapshot
from valuation_hub.web_prprep import make_handler, render_source_lab

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "sec_companyfacts_sample.json"
AGENT = "Valuation-Intelligence-Hub test@example.com"


def _snapshot() -> dict:
    body = FIXTURE.read_bytes()

    def transport(locator: str, *, user_agent: str) -> TransportResponse:
        assert user_agent == AGENT
        return TransportResponse(200, "application/json", body, locator)

    return capture_companyfacts_snapshot(
        1234567,
        user_agent=AGENT,
        transport=transport,
        fetched_at="2026-09-11T06:30:00+00:00",
    )


def _post(base: str, path: str, payload: dict) -> tuple[int, dict]:
    request = Request(
        base + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=4) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def test_cli_parser_exposes_sec_commands() -> None:
    parser = cli._parser()
    fetched = parser.parse_args([
        "sec-fetch", "1234567", "--user-agent", AGENT,
        "--output", "workspace/source_snapshots/x.json",
    ])
    assert fetched.command == "sec-fetch"
    assert fetched.cik == "1234567"
    validated = parser.parse_args(["sec-snapshot-validate", "snapshot.json"])
    assert validated.command == "sec-snapshot-validate"
    extracted = parser.parse_args([
        "sec-extract", "snapshot.json", "revenue", "--form", "10-Q", "--period-end", "2026-03-31",
    ])
    assert extracted.command == "sec-extract"
    assert extracted.metric == "revenue"


def test_cli_fetch_materializes_only_explicit_workspace_output(monkeypatch, tmp_path: Path, capsys) -> None:
    repo = tmp_path / "repo"
    (repo / "workspace" / "source_snapshots").mkdir(parents=True)
    snapshot = _snapshot()
    monkeypatch.setattr(cli, "capture_companyfacts_snapshot", lambda cik, *, user_agent: snapshot)
    output = repo / "workspace" / "source_snapshots" / "fixture.json"
    code = cli.main([
        "--root", str(repo), "--json", "sec-fetch", "1234567",
        "--user-agent", AGENT, "--output", str(output),
    ])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "SOURCE_SNAPSHOT_MATERIALIZED"
    assert payload["canonical"] is False
    assert output.is_file()


def test_cli_validate_and_extract_from_existing_snapshot(tmp_path: Path, capsys) -> None:
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(_snapshot()), encoding="utf-8")
    assert cli.main(["--json", "sec-snapshot-validate", str(path)]) == 0
    validation = json.loads(capsys.readouterr().out)
    assert validation["status"] == "PASS_SOURCE_SNAPSHOT_VALIDATION"
    assert cli.main(["sec-extract", str(path), "revenue", "--form", "10-Q"]) == 0
    candidate = json.loads(capsys.readouterr().out)
    assert candidate["status"] == "EVIDENCE_CANDIDATE_UNREVIEWED"
    assert candidate["value"] == 280000000


def test_source_web_page_is_inspect_only() -> None:
    page = render_source_lab()
    assert "SEC Source Snapshot Inspector" in page
    assert "INSPECT ONLY · NO LIVE FETCH" in page
    assert "/api/source/validate" in page
    assert "/api/source/extract" in page
    assert "/api/source/fetch" not in page


def test_web_validates_and_extracts_snapshot_without_live_fetch_endpoint() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        status, validation = _post(base, "/api/source/validate", {"snapshot": _snapshot()})
        assert status == 200
        assert validation["status"] == "PASS_SOURCE_SNAPSHOT_VALIDATION"
        status, candidate = _post(
            base,
            "/api/source/extract",
            {"snapshot": _snapshot(), "metric": "revenue", "form": "10-Q"},
        )
        assert status == 200
        assert candidate["status"] == "EVIDENCE_CANDIDATE_UNREVIEWED"
        assert candidate["filing"]["accession"] == "0001234567-26-000020"

        request = Request(
            base + "/api/source/fetch",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urlopen(request, timeout=4)
            raise AssertionError("unexpected browser live-fetch endpoint")
        except HTTPError as exc:
            assert exc.code in {400, 404, 405}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=4)
