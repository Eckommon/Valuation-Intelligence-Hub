"""Read-only M18 derived financial evidence Web Lab / 읽기전용 파생재무근거 Web Lab."""
from __future__ import annotations

import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from valuation_hub import web as legacy_web
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.derived_financial import derive_historical_net_income_margin, derive_historical_operating_margin, validate_derived_financial_evidence
from valuation_hub.web_binding_apply import make_handler as make_apply_handler, _dashboard_with_apply_link
from valuation_hub.web_product import product_layout

MAX_DERIVED_REQUEST_BYTES = 16 * 1024 * 1024


def render_derived_lab() -> str:
    body = """
<div class="breadcrumbs"><a href="/">Dashboard</a><span>›</span><strong>Derived Financial Evidence / 파생재무근거</strong></div>
<div class="section-head"><div><h2>Historical Derived Evidence / 역사적 파생근거</h2><p class="muted">Calculate only semantically exact historical ratios from compatible normalized observations. / 호환되는 정규화 observation에서 의미가 정확한 역사적 ratio만 계산합니다.</p></div><span class="state-preview">CALCULATE ONLY · NOT FORECAST</span></div>
<div class="card"><p class="warn"><strong>Historical fact ≠ forecast assumption / 역사적 사실 ≠ 미래 가정</strong></p><p>Outputs remain <code>canonical=false</code> and explicitly carry <code>forecast_direct_bind=false</code>. / 결과는 비정식이며 forecast 직접바인딩이 금지됩니다.</p></div>
<label>Derivation<select id="d-kind"><option value="operating">Historical operating margin / 역사적 영업마진</option><option value="net">Historical net-income margin / 역사적 순이익률</option></select></label>
<label>Numerator normalized observation JSON<textarea id="d-num" spellcheck="false" style="width:100%;min-height:300px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<label>Revenue normalized observation JSON<textarea id="d-rev" spellcheck="false" style="width:100%;min-height:300px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><button class="primary" onclick="deriveEvidence()">Derive / 파생</button></p>
<label>Derived evidence JSON<textarea id="d-result" spellcheck="false" style="width:100%;min-height:360px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><button class="primary" onclick="validateDerived()">Validate / 검증</button></p>
<div id="d-summary" class="preview-summary"><div class="muted">No Draft mutation or canonical write is available. / Draft 변경·정식 기록 기능은 없습니다.</div></div><pre id="d-output">—</pre>
<script>
const dn=document.getElementById('d-num'),dr=document.getElementById('d-rev'),rr=document.getElementById('d-result'),ds=document.getElementById('d-summary'),doo=document.getElementById('d-output');
function obj(x,l){try{return JSON.parse(x.value)}catch(e){throw new Error(l+' JSON error: '+e.message)}}
async function post(path,payload){const q=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const j=await q.json();doo.textContent=JSON.stringify(j,null,2);if(!q.ok)throw new Error(j.error||('HTTP '+q.status));return j}
async function deriveEvidence(){try{const j=await post('/api/derived/calculate',{kind:document.getElementById('d-kind').value,numerator:obj(dn,'Numerator'),revenue:obj(dr,'Revenue')});rr.value=JSON.stringify(j,null,2);ds.innerHTML='<div class="warn"><strong>'+j.metric+'</strong><br>Value: '+j.value+'<br>'+j.class+' · CANONICAL=false · FORECAST DIRECT BIND=false</div>'}catch(e){ds.innerHTML='<div class="bad">'+String(e)+'</div>'}}
async function validateDerived(){try{const j=await post('/api/derived/validate',{derived:obj(rr,'Derived evidence')});ds.innerHTML='<div class="good"><strong>'+j.status+'</strong><br>'+j.metric+' · '+j.class+' · historical_only='+j.historical_only+'</div>'}catch(e){ds.innerHTML='<div class="bad">'+String(e)+'</div>'}}
</script>
"""
    return product_layout("Derived Financial Evidence — Valuation Intelligence Hub", body)


def _dashboard_with_derived_link(repo: Path) -> str:
    page = _dashboard_with_apply_link(repo)
    marker = '<h2>Canonical cases / 정식 사례</h2>'
    banner = ('<div class="card" style="margin-bottom:18px;border-color:#22c55e"><div><strong>Derived Financial Evidence / 파생재무근거</strong></div><p>Calculate historical operating/net margin only from compatible normalized facts. Historical ratios never become forecast assumptions automatically. / 호환되는 정규화 근거로 역사적 마진만 계산하며 미래 가정으로 자동 승격하지 않습니다.</p><a href="/derived">Open Derived Evidence Lab / 파생근거 랩 열기 →</a></div>')
    return page.replace(marker, banner + marker, 1)


def make_handler(root: Path | None = None):
    repo = root.resolve() if root else find_repo_root()
    Base = make_apply_handler(repo)

    class DerivedHandler(Base):
        def _derived_payload(self) -> dict:
            raw = self.headers.get("Content-Length", "0")
            try: length = int(raw)
            except ValueError as exc: raise CaseServiceError("invalid Content-Length / Content-Length 오류") from exc
            if length <= 0 or length > MAX_DERIVED_REQUEST_BYTES:
                raise CaseServiceError("derived request size invalid / 파생근거 요청크기 오류")
            try: payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc: raise CaseServiceError("invalid derived JSON / 파생근거 JSON 오류") from exc
            if not isinstance(payload, dict):
                raise CaseServiceError("derived payload must be object / 파생근거 payload 객체 필요")
            if any(key in payload for key in ("api_key", "crtfc_key", "user_agent")):
                raise CaseServiceError("credentials forbidden / 인증정보 금지")
            return payload

        def do_GET(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            try:
                if path == "/":
                    self._send(HTTPStatus.OK, _dashboard_with_derived_link(repo).encode("utf-8"), "text/html; charset=utf-8"); return
                if path == "/derived":
                    self._send(HTTPStatus.OK, render_derived_lab().encode("utf-8"), "text/html; charset=utf-8"); return
                super().do_GET()
            except CaseServiceError as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

        def do_POST(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            if path not in {"/api/derived/calculate", "/api/derived/validate"}:
                super().do_POST(); return
            try:
                payload = self._derived_payload()
                if path.endswith("/calculate"):
                    numerator, revenue, kind = payload.get("numerator"), payload.get("revenue"), payload.get("kind")
                    if not isinstance(numerator, dict) or not isinstance(revenue, dict):
                        raise CaseServiceError("numerator/revenue observations required / 분자·revenue observation 필요")
                    if kind == "operating": result = derive_historical_operating_margin(numerator, revenue)
                    elif kind == "net": result = derive_historical_net_income_margin(numerator, revenue)
                    else: raise CaseServiceError("derived kind must be operating or net / 파생종류 오류")
                else:
                    derived = payload.get("derived")
                    if not isinstance(derived, dict): raise CaseServiceError("derived evidence required / 파생근거 필요")
                    result = validate_derived_financial_evidence(derived)
                self._send(HTTPStatus.OK, legacy_web._json_bytes(result), "application/json; charset=utf-8")
            except (CaseServiceError, ValueError, TypeError) as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

    return DerivedHandler


def serve(*, host: str = "127.0.0.1", port: int = 8765, root: Path | None = None) -> None:
    if not 0 < port < 65536: raise ValueError("port must be in 1..65535 / 포트 범위 오류")
    server = ThreadingHTTPServer((host, port), make_handler(root))
    print(f"Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}")
    print("Derived Financial Evidence / 파생재무근거: /derived")
    print("Press Ctrl+C to stop / 종료하려면 Ctrl+C")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
