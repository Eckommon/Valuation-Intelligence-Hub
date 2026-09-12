"""Read-only M26 integrated forecast Web Lab / 읽기전용 M26 통합 Forecast Web Lab."""
from __future__ import annotations

import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from valuation_hub import web as legacy_web
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.forecast_assumption import (
    build_forecast_candidate,
    build_forecast_review_assertion,
    finalize_reviewed_forecast,
    validate_forecast_candidate,
    validate_forecast_review_assertion,
    validate_reviewed_forecast,
)
from valuation_hub.forecast_draft_binding import (
    build_binding_proposal_with_forecast,
    validate_binding_proposal_v6,
)
from valuation_hub.web_product import product_layout
from valuation_hub.web_terminal_growth import _dashboard as _prior_dashboard, make_handler as make_prior_handler

MAX_REQUEST_BYTES = 16 * 1024 * 1024


def render_forecast_lab() -> str:
    body = """
<div class="breadcrumbs"><a href="/">Dashboard</a><span>›</span><strong>Integrated Forecast / 통합 Forecast</strong></div>
<div class="section-head"><div><h2>Governed Integrated FCFF Forecast / 거버넌스 통합 FCFF Forecast</h2><p class="muted">Review revenue, EBIT margin, tax, D&amp;A, CAPEX and ΔNWC as one coherent scenario block before atomic Draft binding.</p></div><span class="state-preview">ASSUMPTION · SIX-FIELD ATOMIC · HUMAN REVIEW</span></div>
<div class="card"><p class="warn"><strong>Historical fact ≠ forecast authority.</strong></p><p>Every scenario must use the same explicit future-year set. EBIT, NOPAT and FCFF are diagnostics only and never upgrade forecast authority.</p></div>
<label>Request JSON<textarea id="req" spellcheck="false" style="width:100%;min-height:360px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><select id="action"><option value="candidate-build">Build candidate</option><option value="candidate-validate">Validate candidate</option><option value="review-build">Build review assertion</option><option value="review-validate">Validate review assertion</option><option value="finalize">Finalize reviewed package</option><option value="validate">Validate reviewed package</option><option value="binding-build">Build v0.6 proposal</option><option value="binding-validate">Validate v0.6 proposal</option></select> <button class="primary" onclick="run()">Run / 실행</button></p>
<div class="preview-summary"><div class="muted">NO DRAFT APPLY · NO FILE WRITE · NO PROMOTION · NO CANONICAL WRITE</div></div><pre id="out">—</pre>
<script>
const q=document.getElementById('req'),a=document.getElementById('action'),o=document.getElementById('out');
async function run(){try{const body=JSON.parse(q.value);const r=await fetch('/api/forecast/'+a.value,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});o.textContent=JSON.stringify(await r.json(),null,2)}catch(e){o.textContent=String(e)}}
</script>
"""
    return product_layout("Integrated Forecast — Valuation Intelligence Hub", body)


def _dashboard(repo: Path) -> str:
    page = _prior_dashboard(repo)
    marker = '<h2>Canonical cases / 정식 사례</h2>'
    banner = '<div class="card" style="margin-bottom:18px;border-color:#f59e0b"><div><strong>M26 Integrated Forecast / M26 통합 Forecast</strong></div><p>Six FCFF forecast inputs → one reviewed scenario package → atomic v0.6 Draft-binding proposal.</p><a href="/forecast">Open Forecast Lab / Forecast 랩 열기 →</a></div>'
    return page.replace(marker, banner + marker, 1)


def make_handler(root: Path | None = None):
    repo = root.resolve() if root else find_repo_root()
    Base = make_prior_handler(repo)

    class ForecastHandler(Base):
        def _m26_payload(self) -> dict:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise CaseServiceError("invalid Content-Length / Content-Length 오류") from exc
            if length <= 0 or length > MAX_REQUEST_BYTES:
                raise CaseServiceError("forecast request size invalid / Forecast 요청크기 오류")
            try:
                value = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise CaseServiceError("invalid forecast JSON / Forecast JSON 오류") from exc
            if not isinstance(value, dict):
                raise CaseServiceError("forecast payload object required / Forecast payload 객체 필요")
            if any(key in value for key in ("api_key", "crtfc_key", "user_agent")):
                raise CaseServiceError("credentials forbidden / 인증정보 금지")
            return value

        def do_GET(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            try:
                if path == "/":
                    self._send(HTTPStatus.OK, _dashboard(repo).encode("utf-8"), "text/html; charset=utf-8")
                    return
                if path == "/forecast":
                    self._send(HTTPStatus.OK, render_forecast_lab().encode("utf-8"), "text/html; charset=utf-8")
                    return
                super().do_GET()
            except CaseServiceError as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

        def do_POST(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            prefix = "/api/forecast/"
            if not path.startswith(prefix):
                super().do_POST()
                return
            try:
                query = self._m26_payload()
                action = path[len(prefix):]
                if action == "candidate-build":
                    scenarios = query.get("scenarios")
                    if not isinstance(scenarios, list) or not scenarios or not all(isinstance(item, dict) for item in scenarios):
                        raise CaseServiceError("forecast scenarios array required / Forecast 시나리오 배열 필요")
                    result = build_forecast_candidate(
                        scenarios,
                        entity_id=query.get("entity_id"),
                        financial_scope=query.get("financial_scope"),
                        capital_currency=query.get("capital_currency"),
                        as_of=query.get("as_of"),
                    )
                elif action == "candidate-validate":
                    result = validate_forecast_candidate(query.get("candidate"))
                elif action == "review-build":
                    result = build_forecast_review_assertion(query.get("candidate"), reviewer=query.get("reviewer"), approved_at=query.get("approved_at"), review_basis=query.get("review_basis"))
                elif action == "review-validate":
                    result = validate_forecast_review_assertion(query.get("assertion"), query.get("candidate"))
                elif action == "finalize":
                    result = finalize_reviewed_forecast(query.get("candidate"), query.get("assertion"))
                elif action == "validate":
                    result = validate_reviewed_forecast(query.get("package"))
                elif action == "binding-build":
                    result = build_binding_proposal_with_forecast(query.get("base_proposal"), query.get("forecast_package"))
                elif action == "binding-validate":
                    result = validate_binding_proposal_v6(query.get("proposal"))
                else:
                    raise CaseServiceError("unsupported forecast Web action / 미지원 Forecast Web 동작")
                self._send(HTTPStatus.OK, legacy_web._json_bytes(result), "application/json; charset=utf-8")
            except (CaseServiceError, ValueError, TypeError, KeyError) as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

    return ForecastHandler


def serve(*, host: str = "127.0.0.1", port: int = 8765, root: Path | None = None) -> None:
    if not 0 < port < 65536:
        raise ValueError("port must be in 1..65535 / 포트 범위 오류")
    server = ThreadingHTTPServer((host, port), make_handler(root))
    print(f"Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}")
    print("M26 Integrated Forecast Lab / M26 통합 Forecast 랩: /forecast")
    print("Press Ctrl+C to stop / 종료하려면 Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
