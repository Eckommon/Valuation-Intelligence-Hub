"""Web MVP integration tests / Web MVP 통합테스트."""

from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest

from valuation_hub.web import case_view, make_handler, render_case, render_dashboard


ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_renders_all_registered_cases() -> None:
    page = render_dashboard(ROOT)
    assert "LS ELECTRIC" in page
    assert "LS Eco Energy" in page
    assert "Jet.AI" in page
    assert "Evidence-grounded valuation" in page


def test_case_view_uses_grounded_service_output() -> None:
    view = case_view("KR_010120_LS_ELECTRIC", ROOT)
    assert view["grounded"] is True
    assert view["promotion_gate"] == "PASS_MATERIAL_INPUTS_RECONCILED"
    assert view["model"] == "equity_fcff"
    assert view["runtime"]["BASE"]["value_per_share"] == pytest.approx(41475, abs=1.0)


def test_case_page_exposes_required_user_context() -> None:
    page = render_case("US_JTAI_JET_AI", ROOT)
    assert "Jet.AI" in page
    assert "Evidence gate / 근거 게이트" in page
    assert "reference-venture-probability-v0.1" in page
    assert "Probability-weighted valuation / 확률가중 가치평가" in page


def test_http_endpoints_and_fail_closed_unknown_case() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        with urlopen(base + "/healthz", timeout=3) as response:
            assert response.status == 200
            assert json.loads(response.read())["ok"] is True

        with urlopen(base + "/api/cases", timeout=3) as response:
            cases = json.loads(response.read())
            assert len(cases) == 3

        with urlopen(base + "/api/cases/KR_229640_LS_ECO_ENERGY", timeout=3) as response:
            payload = json.loads(response.read())
            assert payload["grounded"] is True
            assert payload["runtime"]["BASE"]["value_per_share"] == pytest.approx(27326, abs=1.0)

        with pytest.raises(HTTPError) as exc_info:
            urlopen(base + "/api/cases/UNKNOWN_CASE", timeout=3)
        assert exc_info.value.code == 404
        body = json.loads(exc_info.value.read())
        assert body["ok"] is False
        assert "unknown case" in body["error"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
