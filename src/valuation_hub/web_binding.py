"""Read-only M16 Draft binding proposal Web Lab / 읽기전용 M16 Draft 바인딩 제안 Web Lab."""
from __future__ import annotations

import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from valuation_hub import web as legacy_web
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.draft_binding import build_binding_proposal, validate_binding_proposal
from valuation_hub.web_normalization import make_handler as make_normalization_handler, _dashboard_with_normalization_link
from valuation_hub.web_product import product_layout

MAX_BINDING_REQUEST_BYTES = 24 * 1024 * 1024


def render_binding_lab() -> str:
    body = """
<div class="breadcrumbs"><a href="/">Dashboard</a><span>›</span><strong>Draft Binding Proposal / Draft 바인딩 제안</strong></div>
<div class="section-head"><div><h2>Evidence → Draft Binding Proposal / 근거 → Draft 바인딩 제안</h2><p class="muted">Classify normalized evidence against equity-FCFF Draft inputs without mutating a Draft. / 정규화 근거를 equity-FCFF Draft 입력과 비교하되 Draft를 변경하지 않습니다.</p></div><span class="state-preview">PROPOSAL ONLY · NO DRAFT MUTATION</span></div>
<div class="card"><p class="warn"><strong>Semantic equivalence is required for DIRECT_BIND / 의미 동일성이 DIRECT_BIND의 필수조건</strong></p><p><code>liabilities ≠ debt</code>, <code>shares_outstanding ≠ diluted_shares</code>, and historical/TTM revenue is not forecast revenue. Candidate evidence can provide context but cannot directly bind. / 의미가 다른 값을 자동대입하지 않습니다.</p></div>
<div class="grid compact"><label>As of / 기준일<input id="bind-asof" placeholder="YYYY-MM-DD"></label><label>Max age days / 최대 경과일<input id="bind-age" type="number" min="0" max="3650" value="550"></label></div>
<label>Normalized observations JSON array<textarea id="bind-observations" spellcheck="false" style="width:100%;min-height:420px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><button class="primary" onclick="buildBinding()">Build proposal / 제안 생성</button></p>
<label>Binding proposal JSON<textarea id="bind-proposal" spellcheck="false" style="width:100%;min-height:420px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><button class="primary" onclick="validateBinding()">Validate proposal / 제안 검증</button></p>
<div id="bind-summary" class="preview-summary"><div class="muted">Proposal-only. No Draft or repository mutation. / 제안 전용이며 Draft·저장소를 변경하지 않습니다.</div></div>
<pre id="bind-output">—</pre>
<script>
const bo=document.getElementById('bind-observations'),bp=document.getElementById('bind-proposal'),bs=document.getElementById('bind-summary'),bout=document.getElementById('bind-output');
function parse(area,label){try{return JSON.parse(area.value)}catch(e){throw new Error(label+' JSON error / JSON 오류: '+e.message)}}
async function post(path,payload){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const j=await r.json();bout.textContent=JSON.stringify(j,null,2);if(!r.ok)throw new Error(j.error||('HTTP '+r.status));return j;}
async function buildBinding(){try{const obs=parse(bo,'Observations');const age=Number(document.getElementById('bind-age').value);const j=await post('/api/binding/build',{observations:obs,as_of:document.getElementById('bind-asof').value,max_age_days:age});bp.value=JSON.stringify(j,null,2);bs.innerHTML='<div class="warn"><strong>'+j.status+'</strong><br>Direct bind: '+j.completeness.direct_bind_count+' · Unresolved: '+j.completeness.unresolved_count+'<br><code>'+j.proposal_sha256+'</code><br><span class="muted">CANONICAL=false · NO APPLY</span></div>';}catch(e){bs.innerHTML='<div class="bad">'+String(e)+'</div>';}}
async function validateBinding(){try{const j=await post('/api/binding/validate',{proposal:parse(bp,'Proposal')});bs.innerHTML='<div class="good"><strong>'+j.status+'</strong><br>Direct bind: '+j.direct_bind_count+' · Unresolved: '+j.unresolved_count+'<br><span class="muted">CANONICAL=false</span></div>';}catch(e){bs.innerHTML='<div class="bad">'+String(e)+'</div>';}}
</script>
"""
    return product_layout("Draft Binding Proposal — Valuation Intelligence Hub", body)


def _dashboard_with_binding_link(repo: Path) -> str:
    page = _dashboard_with_normalization_link(repo)
    marker = '<h2>Canonical cases / 정식 사례</h2>'
    banner = (
        '<div class="card" style="margin-bottom:18px;border-color:#fb7185">'
        '<div><strong>Evidence → Draft Binding Proposal / 근거→Draft 바인딩 제안</strong></div>'
        '<p>Classify safe direct bindings, references, derivations, assumptions, missing inputs, conflicts, and staleness. Proposal only; no Draft mutation. / '
        '안전한 직접바인딩·참고·파생·가정·누락·충돌·최신성을 분류합니다. 제안 전용이며 Draft를 변경하지 않습니다.</p>'
        '<a href="/binding">Open Binding Proposal Lab / 바인딩 제안 랩 열기 →</a></div>'
    )
    return page.replace(marker, banner + marker, 1)


def make_handler(root: Path | None = None):
    repo = root.resolve() if root else find_repo_root()
    Base = make_normalization_handler(repo)

    class BindingHandler(Base):
        def _binding_payload(self) -> dict:
            raw = self.headers.get("Content-Length", "0")
            try:
                length = int(raw)
            except ValueError as exc:
                raise CaseServiceError("invalid Content-Length / Content-Length 오류") from exc
            if length <= 0 or length > MAX_BINDING_REQUEST_BYTES:
                raise CaseServiceError("binding request size invalid / 바인딩 요청크기 오류")
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise CaseServiceError("invalid binding JSON / 바인딩 JSON 오류") from exc
            if not isinstance(payload, dict):
                raise CaseServiceError("binding payload must be object / 바인딩 payload는 객체여야 합니다")
            if any(key in payload for key in ("api_key", "crtfc_key", "user_agent")):
                raise CaseServiceError("credentials are forbidden in binding payloads / 바인딩 payload에 인증정보를 넣을 수 없습니다")
            return payload

        def do_GET(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            try:
                if path == "/":
                    self._send(HTTPStatus.OK, _dashboard_with_binding_link(repo).encode("utf-8"), "text/html; charset=utf-8")
                    return
                if path == "/binding":
                    self._send(HTTPStatus.OK, render_binding_lab().encode("utf-8"), "text/html; charset=utf-8")
                    return
                super().do_GET()
            except CaseServiceError as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

        def do_POST(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            if path not in {"/api/binding/build", "/api/binding/validate"}:
                super().do_POST()
                return
            try:
                payload = self._binding_payload()
                if path.endswith("/build"):
                    observations = payload.get("observations")
                    as_of = payload.get("as_of")
                    max_age = payload.get("max_age_days", 550)
                    if not isinstance(observations, list) or not observations or not all(isinstance(x, dict) for x in observations):
                        raise CaseServiceError("non-empty observations object array required / 비어있지 않은 observation 객체 배열 필요")
                    if not isinstance(as_of, str):
                        raise CaseServiceError("as_of string required / as_of 문자열 필요")
                    result = build_binding_proposal(observations, as_of=as_of, max_age_days=max_age)
                else:
                    proposal = payload.get("proposal")
                    if not isinstance(proposal, dict):
                        raise CaseServiceError("proposal object required / proposal 객체 필요")
                    result = validate_binding_proposal(proposal)
                self._send(HTTPStatus.OK, legacy_web._json_bytes(result), "application/json; charset=utf-8")
            except (CaseServiceError, ValueError) as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

    return BindingHandler


def serve(*, host: str = "127.0.0.1", port: int = 8765, root: Path | None = None) -> None:
    if not 0 < port < 65536:
        raise ValueError("port must be in 1..65535 / 포트 범위 오류")
    server = ThreadingHTTPServer((host, port), make_handler(root))
    print(f"Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}")
    print("Financial Normalization + TTM / 재무근거 정규화 + TTM: /normalize")
    print("Evidence → Draft Binding Proposal / 근거→Draft 바인딩 제안: /binding")
    print("Press Ctrl+C to stop / 종료하려면 Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
