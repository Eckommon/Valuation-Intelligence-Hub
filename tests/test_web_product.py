"""M7 product Web UX integration tests / M7 제품 Web UX 통합테스트."""

from __future__ import annotations

import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

from valuation_hub.web_product import make_handler, render_product_case, render_product_evidence

ROOT = Path(__file__).resolve().parents[1]


def test_equity_product_page_has_canonical_visuals_and_preview_separation() -> None:
    page = render_product_case("KR_010120_LS_ELECTRIC", ROOT)
    assert "Canonical valuation / 정식 가치평가" in page
    assert "Market vs intrinsic value / 시장 vs 내재가치" in page
    assert "FCFF trend / FCFF 추세" in page
    assert "PREVIEW · NOT CANONICAL" in page
    assert "Evidence & decision / 근거와 판단" in page


def test_venture_product_page_has_probability_visualization() -> None:
    page = render_product_case("US_JTAI_JET_AI", ROOT)
    assert "Probability-weighted outcomes / 확률가중 결과" in page
    assert "Failure (60%)" in page
    assert "Breakout (10%)" in page


def test_product_evidence_page_has_filters() -> None:
    page = render_product_evidence("KR_229640_LS_ECO_ENERGY", ROOT)
    assert "Evidence browser / 근거 탐색" in page
    assert "filter-card" in page
    assert "data-class=\"FACT\"" in page
    assert "data-class=\"ALL\"" in page


def test_product_handler_serves_enhanced_case_page() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/case/KR_010120_LS_ELECTRIC", timeout=3) as response:
            page = response.read().decode("utf-8")
            assert response.status == 200
            assert "Market vs intrinsic value / 시장 vs 내재가치" in page
        with urlopen(f"http://127.0.0.1:{server.server_port}/api/cases", timeout=3) as response:
            assert response.status == 200  # inherited M6 API remains available
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=3)
