"""M6 Web interactive integration tests / M6 Web 인터랙티브 통합테스트."""

from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from valuation_hub.web import make_handler, render_evidence

ROOT = Path(__file__).resolve().parents[1]


def _post_json(url: str, payload: dict):
    request = Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    return urlopen(request, timeout=3)


def test_evidence_html_exposes_fact_and_source() -> None:
    page = render_evidence("KR_010120_LS_ELECTRIC", ROOT)
    assert "Evidence browser / 근거 탐색" in page
    assert "FACT" in page
    assert "S&P Global" in page or "LS ELECTRIC" in page


def test_preview_http_is_noncanonical_and_invalid_state_fails_closed() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        with urlopen(base + "/api/cases/KR_010120_LS_ELECTRIC/evidence", timeout=3) as response:
            evidence = json.loads(response.read())
            assert evidence["read_only"] is True
            assert evidence["claims"]

        with _post_json(base + "/api/cases/KR_229640_LS_ECO_ENERGY/preview", {"scenario": "BASE", "revenue_scale": 1.1}) as response:
            preview = json.loads(response.read())
            assert preview["canonical"] is False
            assert preview["status"] == "PREVIEW_NOT_CANONICAL"
            assert preview["preview"]["value_per_share"] > 0

        with pytest.raises(HTTPError) as exc_info:
            _post_json(base + "/api/cases/KR_010120_LS_ELECTRIC/preview", {"wacc": 0.03, "terminal_growth": 0.04})
        assert exc_info.value.code == 400
        payload = json.loads(exc_info.value.read())
        assert "terminal growth" in payload["error"]
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=3)


def test_venture_preview_http_probability_validation() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        with _post_json(base + "/api/cases/US_JTAI_JET_AI/preview", {"probabilities": {"FAILURE": 0.55, "SURVIVAL": 0.30, "BREAKOUT": 0.15}}) as response:
            payload = json.loads(response.read())
            assert payload["canonical"] is False
            assert payload["preview"]["expected_present_value_per_share"] > 0
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=3)
