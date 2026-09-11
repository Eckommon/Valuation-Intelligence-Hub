"""M15 CLI/Web interface contracts / M15 CLI·Web 인터페이스 계약."""

from __future__ import annotations

import copy
import hashlib
import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from valuation_hub import cli_entry
from valuation_hub.financial_normalization import DURATION_QUARTER
from valuation_hub.web_normalization import make_handler, render_normalization_lab

ROOT = Path(__file__).resolve().parents[1]


def _hash_payload(value: dict, field: str) -> str:
    payload = copy.deepcopy(value)
    payload.pop(field, None)
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _quarter(value: int, fy: int, fq: int) -> dict:
    obs = {
        "schema_version": "financial-observation-v0.1",
        "status": "FINANCIAL_OBSERVATION_NORMALIZED",
        "canonical": False,
        "class": "NORMALIZED_FACT_CANDIDATE",
        "metric": "revenue",
        "value": value,
        "unit": "KRW",
        "entity": {"id": "DART_CORP:00126380", "source_system": "TEST", "financial_scope": "CFS"},
        "period": {"kind": DURATION_QUARTER, "start": None, "end": None, "duration_days": None, "fiscal_year": fy, "fiscal_period": f"Q{fq}", "fiscal_quarter": fq, "report_stage": f"Q{fq}", "date_precision": "TEST"},
        "lineage": {"normalization_rule": "TEST_FIXTURE", "source_candidate_sha256": "a" * 64},
        "observation_sha256": "",
    }
    obs["observation_sha256"] = _hash_payload(obs, "observation_sha256")
    return obs


def _post(base: str, path: str, payload: dict) -> tuple[int, dict]:
    req = Request(base + path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=4) as response:
        return response.status, json.loads(response.read().decode())


def test_cli_dispatch_recognizes_m15_commands() -> None:
    for command in (
        "normalize-sec", "normalize-dart", "normalize-validate", "ttm-four-quarters",
        "ttm-annual-bridge", "ttm-validate", "normalize-reconcile",
    ):
        assert cli_entry._command([command]) == command


def test_cli_four_quarter_ttm_json_output(tmp_path: Path, capsys) -> None:
    files = []
    for index, (fy, fq, value) in enumerate(((2025, 3, 10), (2025, 4, 20), (2026, 1, 30), (2026, 2, 40))):
        path = tmp_path / f"q{index}.json"
        path.write_text(json.dumps(_quarter(value, fy, fq)), encoding="utf-8")
        files.append(str(path))
    code = cli_entry.main(["ttm-four-quarters", *files])
    assert code == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "FINANCIAL_TTM_NORMALIZED"
    assert result["value"] == 100
    assert result["canonical"] is False
    assert result["class"] == "NORMALIZED_FACT_CANDIDATE"


def test_normalization_lab_is_calculate_only() -> None:
    page = render_normalization_lab()
    assert "Financial Normalization + TTM Lab" in page
    assert "CALCULATE ONLY · NO WRITE" in page
    assert "/api/normalize/one" in page
    assert "/api/normalize/ttm-four" in page
    assert "/api/normalize/write" not in page
    assert "api_key" not in page
    assert "crtfc_key" not in page


def test_web_four_quarter_ttm_and_validation_are_read_only() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        observations = [_quarter(10, 2025, 3), _quarter(20, 2025, 4), _quarter(30, 2026, 1), _quarter(40, 2026, 2)]
        status, ttm = _post(base, "/api/normalize/ttm-four", {"observations": observations})
        assert status == 200
        assert ttm["value"] == 100
        assert ttm["canonical"] is False
        status, validation = _post(base, "/api/normalize/ttm-validate", {"ttm": ttm})
        assert status == 200
        assert validation["status"] == "PASS_TTM_VALIDATION"

        request = Request(base + "/api/normalize/write", data=b"{}", headers={"Content-Type": "application/json"}, method="POST")
        try:
            urlopen(request, timeout=4)
            raise AssertionError("unexpected normalization write endpoint")
        except HTTPError as exc:
            assert exc.code in {400, 404, 405}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=4)


def test_web_rejects_credentials_in_normalization_payload() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        req = Request(
            base + "/api/normalize/ttm-four",
            data=json.dumps({"observations": [], "api_key": "secret"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urlopen(req, timeout=4)
            raise AssertionError("credential-bearing payload accepted")
        except HTTPError as exc:
            assert exc.code == 400
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=4)
