"""M14 OpenDART CLI/Web boundaries / OpenDART CLI·Web 경계 테스트."""

from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from valuation_hub import cli_entry
from valuation_hub.dart_live import DartTransportResponse, capture_dart_snapshot
from valuation_hub.web_sources import make_handler, render_dart_source_lab

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "opendart_financials_sample.json"
KEY = "K" * 40


def _snapshot() -> dict:
    body = FIXTURE.read_bytes()

    def transport(locator: str, *, api_key: str) -> DartTransportResponse:
        assert api_key == KEY
        return DartTransportResponse(200, "application/json", body, locator)

    return capture_dart_snapshot(
        "00126380", 2026, "11012", "CFS",
        api_key=KEY,
        transport=transport,
        fetched_at="2026-09-11T07:40:00+00:00",
    )


def _post(base: str, path: str, payload: dict) -> tuple[int, dict]:
    request = Request(
        base + path,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=4) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def test_cli_dispatcher_exposes_dart_commands_without_changing_legacy_parser() -> None:
    parser = cli_entry._dart_parser()
    fetched = parser.parse_args([
        "dart-fetch", "00126380", "--bsns-year", "2026", "--reprt-code", "11012",
        "--fs-div", "CFS", "--api-key", KEY, "--output", "workspace/source_snapshots/dart.json",
    ])
    assert fetched.command == "dart-fetch"
    assert fetched.corp_code == "00126380"
    extracted = parser.parse_args(["dart-extract", "snapshot.json", "revenue", "--statement-section", "IS"])
    assert extracted.metric == "revenue"
    assert extracted.statement_section == "IS"


def test_cli_dart_fetch_materializes_and_never_prints_api_key(monkeypatch, tmp_path: Path, capsys) -> None:
    repo = tmp_path / "repo"
    (repo / "workspace" / "source_snapshots").mkdir(parents=True)
    snapshot = _snapshot()
    monkeypatch.setattr(cli_entry, "capture_dart_snapshot", lambda *args, **kwargs: snapshot)
    output = repo / "workspace" / "source_snapshots" / "dart.json"
    code = cli_entry.main([
        "--root", str(repo), "--json", "dart-fetch", "00126380",
        "--bsns-year", "2026", "--reprt-code", "11012", "--fs-div", "CFS",
        "--api-key", KEY, "--output", str(output),
    ])
    assert code == 0
    stdout = capsys.readouterr().out
    assert KEY not in stdout
    payload = json.loads(stdout)
    assert payload["status"] == "DART_SOURCE_SNAPSHOT_MATERIALIZED"
    assert output.is_file()


def test_cli_validate_extract_and_legacy_delegate(tmp_path: Path, capsys, monkeypatch) -> None:
    path = tmp_path / "dart.json"
    path.write_text(json.dumps(_snapshot(), ensure_ascii=False), encoding="utf-8")
    assert cli_entry.main(["--json", "dart-snapshot-validate", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "PASS_DART_SOURCE_SNAPSHOT_VALIDATION"
    assert cli_entry.main(["dart-extract", str(path), "revenue", "--statement-section", "IS"]) == 0
    candidate = json.loads(capsys.readouterr().out)
    assert candidate["status"] == "DART_EVIDENCE_CANDIDATE_UNREVIEWED"
    assert candidate["value"] == 165_000_000_000

    seen: list[list[str]] = []
    monkeypatch.setattr(cli_entry.legacy_cli, "main", lambda argv: seen.append(list(argv)) or 17)
    assert cli_entry.main(["list"]) == 17
    assert seen == [["list"]]


def test_dart_web_page_has_no_credentials_or_live_fetch_surface() -> None:
    page = render_dart_source_lab()
    assert "OpenDART Source Snapshot Inspector" in page
    assert "NO LIVE FETCH" in page
    assert "/api/dart-source/validate" in page
    assert "/api/dart-source/extract" in page
    assert "/api/dart-source/fetch" not in page
    assert 'name="api-key"' not in page
    assert 'id="api-key"' not in page


def test_web_validates_extracts_and_rejects_credentials_and_live_fetch() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        status, validation = _post(base, "/api/dart-source/validate", {"snapshot": _snapshot()})
        assert status == 200
        assert validation["status"] == "PASS_DART_SOURCE_SNAPSHOT_VALIDATION"
        status, candidate = _post(base, "/api/dart-source/extract", {"snapshot": _snapshot(), "metric": "cash"})
        assert status == 200
        assert candidate["status"] == "DART_EVIDENCE_CANDIDATE_UNREVIEWED"
        assert candidate["value"] == 52_000_000_000

        for path, payload in (
            ("/api/dart-source/validate", {"snapshot": _snapshot(), "api_key": KEY}),
            ("/api/dart-source/fetch", {}),
        ):
            request = Request(
                base + path,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                urlopen(request, timeout=4)
                raise AssertionError("unexpected unsafe Web endpoint/payload")
            except HTTPError as exc:
                assert exc.code in {400, 404, 405}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=4)
