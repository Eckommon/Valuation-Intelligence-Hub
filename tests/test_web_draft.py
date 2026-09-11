"""Web Draft Lab integration tests / Web Draft Lab 통합테스트."""

from __future__ import annotations

import hashlib
import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from valuation_hub.web_draft import make_handler, render_draft_lab

ROOT = Path(__file__).resolve().parents[1]


def _post(url: str, payload: dict):
    request = Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    return urlopen(request, timeout=3)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_draft_lab_page_labels_noncanonical_state() -> None:
    page = render_draft_lab()
    assert "User Draft Lab / 사용자 Draft 랩" in page
    assert "DRAFT · NOT CANONICAL" in page
    assert "USER_SUPPLIED_UNVERIFIED" in page


def test_dashboard_surfaces_draft_lab_and_http_flow_is_nonpersistent() -> None:
    protected = [
        ROOT / "registry" / "cases.json",
        ROOT / "analyses" / "equities" / "KR_229640_LS_ECO_ENERGY" / "valuation_result.json",
    ]
    before = {path: _digest(path) for path in protected}
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        with urlopen(base + "/", timeout=3) as response:
            page = response.read().decode("utf-8")
            assert "Open Draft Lab / Draft 랩 열기" in page

        with urlopen(base + "/api/drafts/templates/equity_fcff", timeout=3) as response:
            draft = json.loads(response.read())
            assert draft["status"] == "DRAFT_USER_SUPPLIED"

        with _post(base + "/api/drafts/validate", draft) as response:
            normalized = json.loads(response.read())
            assert normalized["canonical"] is False

        with _post(base + "/api/drafts/run", draft) as response:
            result = json.loads(response.read())
            assert result["canonical"] is False
            assert result["runtime"]["scenarios"]["BASE"]["value_per_share"] > 0
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=3)
    after = {path: _digest(path) for path in protected}
    assert before == after


def test_web_draft_invalid_probability_fails_closed() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        with urlopen(base + "/api/drafts/templates/venture_probability", timeout=3) as response:
            draft = json.loads(response.read())
        draft["venture"]["scenarios"][0]["probability"] = 0.95
        try:
            _post(base + "/api/drafts/run", draft)
            raise AssertionError("expected HTTPError")
        except HTTPError as exc:
            assert exc.code == 400
            payload = json.loads(exc.read())
            assert "probabilities must sum" in payload["error"]
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=3)
