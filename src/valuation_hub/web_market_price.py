"""Read-only M27 market-price Web Lab / 읽기전용 M27 시장가격 Web Lab."""
from __future__ import annotations

import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from valuation_hub import web as legacy_web
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.market_price import (
    build_market_price_candidate,
    build_market_price_review_assertion,
    finalize_reviewed_market_price,
    validate_market_price_candidate,
    validate_market_price_review_assertion,
    validate_reviewed_market_price,
)
from valuation_hub.market_price_draft_binding import (
    build_binding_proposal_with_market_price,
    validate_binding_proposal_v7,
)
from valuation_hub.web_forecast import _dashboard as _prior_dashboard, make_handler as make_prior_handler
from valuation_hub.web_product import product_layout

MAX_REQUEST_BYTES = 16 * 1024 * 1024


def render_market_price_lab() -> str:
    body = """
<div class="breadcrumbs"><a href="/">Dashboard</a><span>›</span><strong>Market Price / 시장가격</strong></div>
<div class="section-head"><div><h2>Governed Valuation-Date Market Price / 거버넌스 가치평가일 시장가격</h2><p class="muted">Prepare and review an exact as-traded quote as a freshness-controlled market FACT before Draft binding.</p></div><span class="state-preview">FACT · AS-TRADED · FRESHNESS CONTROLLED</span></div>
<div class="card"><p class="warn"><strong>Historical adjusted price ≠ valuation-date market price.</strong></p><p>M27 v0.1 accepts explicit OFFICIAL_CLOSE or LAST_TRADE quotes with source integrity and never silently performs split adjustment or date substitution.</p></div>
<label>Request JSON<textarea id="req" spellcheck="false" style="width:100%;min-height:360px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><select id="action"><option value="candidate-build">Build candidate</option><option value="candidate-validate">Validate candidate</option><option value="review-build">Build review assertion</option><option value="review-validate">Validate review assertion</option><option value="finalize">Finalize reviewed FACT</option><option value="validate">Validate reviewed FACT</option><option value="binding-build">Build v0.7 proposal</option><option value="binding-validate">Validate v0.7 proposal</option></select> <button class="primary" onclick="run()">Run / 실행</button></p>
<div class="preview-summary"><div class="muted">NO DRAFT APPLY · NO FILE WRITE · NO PROMOTION · NO CANONICAL WRITE</div></div><pre id="out">—</pre>
<script>
const q=document.getElementById('req'),a=document.getElementById('action'),o=document.getElementById('out');
async function run(){try{const body=JSON.parse(q.value);const r=await fetch('/api/market-price/'+a.value,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});o.textContent=JSON.stringify(await r.json(),null,2)}catch(e){o.textContent=String(e)}}
</script>
"""
    return product_layout("Market Price — Valuation Intelligence Hub", body)


def _dashboard(repo: Path) -> str:
    page = _prior_dashboard(repo)
    marker = '<h2>Canonical cases / 정식 사례</h2>'
    banner = '<div class="card" style="margin-bottom:18px;border-color:#22c55e"><div><strong>M27 Market Price / M27 시장가격</strong></div><p>Exact as-traded quote → reviewed FACT → v0.7 market-price binding proposal.</p><a href="/market-price">Open Market Price Lab / 시장가격 랩 열기 →</a></div>'
    return page.replace(marker, banner + marker, 1)


def make_handler(root: Path | None = None):
    repo = root.resolve() if root else find_repo_root()
    Base = make_prior_handler(repo)

    class MarketPriceHandler(Base):
        def _m27_payload(self) -> dict:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise CaseServiceError("invalid Content-Length / Content-Length 오류") from exc
            if length <= 0 or length > MAX_REQUEST_BYTES:
                raise CaseServiceError("market-price request size invalid / 시장가격 요청크기 오류")
            try:
                value = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise CaseServiceError("invalid market-price JSON / 시장가격 JSON 오류") from exc
            if not isinstance(value, dict):
                raise CaseServiceError("market-price payload object required / 시장가격 payload 객체 필요")
            if any(key in value for key in ("api_key", "crtfc_key", "user_agent")):
                raise CaseServiceError("credentials forbidden / 인증정보 금지")
            return value

        def do_GET(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            try:
                if path == "/":
                    self._send(HTTPStatus.OK, _dashboard(repo).encode("utf-8"), "text/html; charset=utf-8")
                    return
                if path == "/market-price":
                    self._send(HTTPStatus.OK, render_market_price_lab().encode("utf-8"), "text/html; charset=utf-8")
                    return
                super().do_GET()
            except CaseServiceError as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

        def do_POST(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            prefix = "/api/market-price/"
            if not path.startswith(prefix):
                super().do_POST()
                return
            try:
                query = self._m27_payload()
                action = path[len(prefix):]
                if action == "candidate-build":
                    result = build_market_price_candidate(
                        price=query.get("price"),
                        currency=query.get("currency"),
                        entity_id=query.get("entity_id"),
                        financial_scope=query.get("financial_scope"),
                        instrument_id=query.get("instrument_id"),
                        symbol=query.get("symbol"),
                        venue=query.get("venue"),
                        quote_type=query.get("quote_type"),
                        trading_date=query.get("trading_date"),
                        observed_at=query.get("observed_at"),
                        as_of=query.get("as_of"),
                        source_publisher=query.get("source_publisher"),
                        source_type=query.get("source_type"),
                        source_tier=query.get("source_tier"),
                        source_locator=query.get("source_locator"),
                        source_snapshot_sha256=query.get("source_snapshot_sha256"),
                        max_age_days=query.get("max_age_days", 7),
                    )
                elif action == "candidate-validate":
                    result = validate_market_price_candidate(query.get("candidate"))
                elif action == "review-build":
                    result = build_market_price_review_assertion(query.get("candidate"), reviewer=query.get("reviewer"), approved_at=query.get("approved_at"), review_basis=query.get("review_basis"))
                elif action == "review-validate":
                    result = validate_market_price_review_assertion(query.get("assertion"), query.get("candidate"))
                elif action == "finalize":
                    result = finalize_reviewed_market_price(query.get("candidate"), query.get("assertion"))
                elif action == "validate":
                    result = validate_reviewed_market_price(query.get("package"))
                elif action == "binding-build":
                    result = build_binding_proposal_with_market_price(query.get("base_proposal"), query.get("market_price_package"))
                elif action == "binding-validate":
                    result = validate_binding_proposal_v7(query.get("proposal"))
                else:
                    raise CaseServiceError("unsupported market-price Web action / 미지원 시장가격 Web 동작")
                self._send(HTTPStatus.OK, legacy_web._json_bytes(result), "application/json; charset=utf-8")
            except (CaseServiceError, ValueError, TypeError, KeyError) as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

    return MarketPriceHandler


def serve(*, host: str = "127.0.0.1", port: int = 8765, root: Path | None = None) -> None:
    if not 0 < port < 65536:
        raise ValueError("port must be in 1..65535 / 포트 범위 오류")
    server = ThreadingHTTPServer((host, port), make_handler(root))
    print(f"Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}")
    print("M27 Market Price Lab / M27 시장가격 랩: /market-price")
    print("Press Ctrl+C to stop / 종료하려면 Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
