"""Read-only M23 complete share-bridge → Draft-binding proposal Web Lab."""
from __future__ import annotations

import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from valuation_hub import web as legacy_web
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.share_draft_binding import (
    build_binding_proposal_with_diluted_shares,
    validate_binding_proposal_v3,
)
from valuation_hub.web_product import product_layout
from valuation_hub.web_valuation_shares import (
    _dashboard as _dashboard_with_shares_link,
    make_handler as make_share_handler,
)

MAX_REQUEST_BYTES = 16 * 1024 * 1024


def render_share_binding_lab() -> str:
    body = """
<div class="breadcrumbs"><a href="/">Dashboard</a><span>›</span><strong>Share Binding / 희석주식 바인딩</strong></div>
<div class="section-head"><div><h2>M23 Share-Aware Draft Binding / M23 희석주식 Draft 바인딩</h2><p class="muted">Enrich an already validated M16 v0.1 or M20 v0.2 proposal with one complete, reviewed, fresh M22 diluted-share bridge.</p></div><span class="state-preview">COMPLETE REVIEWED BRIDGE ONLY · PROPOSAL ONLY · NO WRITE</span></div>
<div class="card"><p class="warn"><strong>M23 may replace only <code>equity.diluted_shares</code>.</strong></p><p>Cash/debt and every other base decision remain unchanged. This surface creates or validates a noncanonical proposal only; it does not approve, apply, mutate a Draft file, promote, admit, or write canonical state.</p></div>
<label>Validated base proposal JSON (v0.1 or v0.2)<textarea id="proposal" spellcheck="false" style="width:100%;min-height:300px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<label>Complete reviewed M22 diluted-share bridge JSON<textarea id="bridge" spellcheck="false" style="width:100%;min-height:300px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><button class="primary" onclick="buildProposal()">Build v0.3 proposal / v0.3 제안 생성</button></p>
<label>v0.3 proposal JSON to validate<textarea id="validation" spellcheck="false" style="width:100%;min-height:260px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><button onclick="validateProposal()">Validate v0.3 / v0.3 검증</button></p>
<div class="preview-summary"><div class="muted">CALCULATE/VALIDATE ONLY · NO DRAFT APPLY · NO FILE WRITE · NO CANONICAL WRITE</div></div><pre id="out">—</pre>
<script>
const proposal=document.getElementById('proposal'),bridge=document.getElementById('bridge'),validation=document.getElementById('validation'),out=document.getElementById('out');
function p(x,l){try{return JSON.parse(x.value)}catch(e){throw new Error(l+' JSON error: '+e.message)}}
async function buildProposal(){try{const r=await fetch('/api/share-binding/build',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({base_proposal:p(proposal,'Base proposal'),share_bridge:p(bridge,'Share bridge')})});const j=await r.json();validation.value=JSON.stringify(j,null,2);out.textContent=JSON.stringify(j,null,2)}catch(e){out.textContent=String(e)}}
async function validateProposal(){try{const r=await fetch('/api/share-binding/validate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proposal:p(validation,'v0.3 proposal')})});const j=await r.json();out.textContent=JSON.stringify(j,null,2)}catch(e){out.textContent=String(e)}}
</script>
"""
    return product_layout("Share Binding — Valuation Intelligence Hub", body)


def _dashboard(repo: Path) -> str:
    page = _dashboard_with_shares_link(repo)
    marker = '<h2>Canonical cases / 정식 사례</h2>'
    banner = ('<div class="card" style="margin-bottom:18px;border-color:#f59e0b"><div><strong>M23 Share-Aware Binding / M23 희석주식 바인딩</strong></div><p>Complete reviewed fresh M22 bridge → noncanonical v0.3 proposal. Only equity.diluted_shares may change.</p><a href="/share-binding">Open Share Binding Lab / 희석주식 바인딩 랩 열기 →</a></div>')
    return page.replace(marker, banner + marker, 1)


def make_handler(root: Path | None = None):
    repo = root.resolve() if root else find_repo_root()
    Base = make_share_handler(repo)

    class ShareBindingHandler(Base):
        def _m23_payload(self) -> dict:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise CaseServiceError("invalid Content-Length / Content-Length 오류") from exc
            if length <= 0 or length > MAX_REQUEST_BYTES:
                raise CaseServiceError("share-binding request size invalid / 희석주식 바인딩 요청크기 오류")
            try:
                value = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise CaseServiceError("invalid share-binding JSON / 희석주식 바인딩 JSON 오류") from exc
            if not isinstance(value, dict):
                raise CaseServiceError("share-binding payload object required / 희석주식 바인딩 payload 객체 필요")
            if any(key in value for key in ("api_key", "crtfc_key", "user_agent")):
                raise CaseServiceError("credentials forbidden / 인증정보 금지")
            return value

        def do_GET(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            try:
                if path == "/":
                    self._send(HTTPStatus.OK, _dashboard(repo).encode("utf-8"), "text/html; charset=utf-8")
                    return
                if path == "/share-binding":
                    self._send(HTTPStatus.OK, render_share_binding_lab().encode("utf-8"), "text/html; charset=utf-8")
                    return
                super().do_GET()
            except CaseServiceError as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

        def do_POST(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            if path not in {"/api/share-binding/build", "/api/share-binding/validate"}:
                super().do_POST()
                return
            try:
                q = self._m23_payload()
                if path == "/api/share-binding/build":
                    base, bridge = q.get("base_proposal"), q.get("share_bridge")
                    if not isinstance(base, dict) or not isinstance(bridge, dict):
                        raise CaseServiceError("base_proposal and share_bridge required / base_proposal·share_bridge 필요")
                    result = build_binding_proposal_with_diluted_shares(base, bridge)
                else:
                    proposal = q.get("proposal")
                    if not isinstance(proposal, dict):
                        raise CaseServiceError("v0.3 proposal required / v0.3 proposal 필요")
                    result = validate_binding_proposal_v3(proposal)
                self._send(HTTPStatus.OK, legacy_web._json_bytes(result), "application/json; charset=utf-8")
            except (CaseServiceError, ValueError, TypeError) as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

    return ShareBindingHandler


def serve(*, host: str = "127.0.0.1", port: int = 8765, root: Path | None = None) -> None:
    if not 0 < port < 65536:
        raise ValueError("port must be in 1..65535 / 포트 범위 오류")
    server = ThreadingHTTPServer((host, port), make_handler(root))
    print(f"Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}")
    print("M23 Share Binding / M23 희석주식 바인딩: /share-binding")
    print("Press Ctrl+C to stop / 종료하려면 Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
