"""User Draft Web Lab / 사용자 Draft Web Lab.

This layer extends the product Web UI with in-memory user Draft validation and
execution. Draft payloads are never persisted or promoted by this adapter.

본 계층은 제품 Web UI에 메모리 기반 사용자 Draft 검증·실행 기능을 추가한다.
Draft payload는 본 어댑터에서 영속화하거나 정식 승격하지 않는다.
"""

from __future__ import annotations

import html
import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from valuation_hub import web as legacy_web
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.draft_service import run_draft, template, validate_draft
from valuation_hub.web_product import make_handler as make_product_handler, product_layout

MAX_DRAFT_REQUEST_BYTES = 512 * 1024


def render_draft_lab() -> str:
    body = """
<div class="breadcrumbs"><a href="/">Dashboard</a><span>›</span><strong>Draft Lab / Draft 랩</strong></div>
<div class="section-head"><div><h2>User Draft Lab / 사용자 Draft 랩</h2><p class="muted">Run your own valuation inputs without modifying canonical repository state. / 정식 저장소 상태를 변경하지 않고 사용자 입력을 실행합니다.</p></div><span class="state-preview">DRAFT · NOT CANONICAL</span></div>
<div class="card"><p class="warn"><strong>USER_SUPPLIED_UNVERIFIED / 사용자 제공·미검증</strong></p><p>Draft values have not passed evidence promotion. They cannot enter the canonical registry automatically. / Draft 값은 근거승격을 통과하지 않았으며 정식 레지스트리에 자동 등록되지 않습니다.</p></div>
<div class="grid compact">
<label>Template / 템플릿<select id="draft-model"><option value="equity_fcff">Equity FCFF / 상장기업 FCFF</option><option value="venture_probability">Venture probability / 벤처 확률</option></select></label>
<div><button class="primary" onclick="loadTemplate()">Load template / 템플릿 불러오기</button></div>
</div>
<label style="margin-top:14px">Draft JSON / Draft JSON<textarea id="draft-json" spellcheck="false" style="width:100%;min-height:440px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><button class="primary" onclick="validateDraft()">Validate / 검증</button> <button class="primary" onclick="runDraft()">Run Draft / Draft 실행</button></p>
<div id="draft-summary" class="preview-summary"><div class="muted">Load a template or paste Draft JSON. / 템플릿을 불러오거나 Draft JSON을 붙여넣으세요.</div></div>
<details><summary>Diagnostics JSON / 진단 JSON</summary><pre id="draft-output">—</pre></details>
<script>
const area=document.getElementById('draft-json'),summary=document.getElementById('draft-summary'),output=document.getElementById('draft-output');
function pretty(x){return new Intl.NumberFormat(undefined,{maximumFractionDigits:4}).format(x)}
async function loadTemplate(){const m=document.getElementById('draft-model').value;const r=await fetch('/api/drafts/templates/'+m);const j=await r.json();area.value=JSON.stringify(j,null,2);summary.innerHTML='<div class="muted">Template loaded. Replace example values before use. / 템플릿을 불러왔습니다. 사용 전 예시값을 교체하세요.</div>';}
function payload(){try{return JSON.parse(area.value)}catch(e){throw new Error('Invalid JSON / JSON 오류: '+e.message)}}
async function callDraft(path){try{const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload())});const j=await r.json();output.textContent=JSON.stringify(j,null,2);if(!r.ok){summary.innerHTML='<div class="bad">'+j.error+'</div>';return null;}return j;}catch(e){summary.innerHTML='<div class="bad">'+String(e)+'</div>';return null;}}
async function validateDraft(){const j=await callDraft('/api/drafts/validate');if(j)summary.innerHTML='<div class="good"><strong>PASS DRAFT / Draft 검증 통과</strong><br>'+j.name+' · '+j.model+'<br><span class="muted">DRAFT_USER_SUPPLIED · NOT_CANONICAL</span></div>';}
async function runDraft(){const j=await callDraft('/api/drafts/run');if(!j)return;let result='';if(j.model==='equity_fcff'){result=Object.entries(j.runtime.scenarios).map(([k,v])=>'<div class="mini-kpi"><span>'+k+'</span><strong>'+pretty(v.value_per_share)+'</strong></div>').join('');}else{result='<div class="mini-kpi"><span>Expected PV/share / 기대 현재 주당가치</span><strong>'+pretty(j.runtime.expected_present_value_per_share)+'</strong></div>';}summary.innerHTML='<div class="warn"><strong>DRAFT RESULT · NOT CANONICAL / Draft 결과 · 정식 아님</strong></div><div class="grid compact" style="margin-top:10px">'+result+'</div><p class="muted">'+j.warning_ko+'</p>';}
loadTemplate();
</script>
"""
    return product_layout("Draft Lab — Valuation Intelligence Hub", body)


def make_handler(root: Path | None = None):
    repo = root.resolve() if root else find_repo_root()
    Base = make_product_handler(repo)

    class DraftHandler(Base):
        def _draft_payload(self) -> dict:
            raw = self.headers.get("Content-Length", "0")
            try:
                length = int(raw)
            except ValueError as exc:
                raise CaseServiceError("invalid Content-Length / Content-Length 오류") from exc
            if length <= 0 or length > MAX_DRAFT_REQUEST_BYTES:
                raise CaseServiceError("Draft request size invalid / Draft 요청 크기 오류")
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise CaseServiceError("invalid Draft JSON / Draft JSON 오류") from exc
            if not isinstance(payload, dict):
                raise CaseServiceError("Draft must be a JSON object / Draft는 JSON 객체여야 합니다")
            return payload

        def do_GET(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            try:
                if path == "/draft":
                    self._send(HTTPStatus.OK, render_draft_lab().encode("utf-8"), "text/html; charset=utf-8")
                    return
                if path.startswith("/api/drafts/templates/"):
                    model = path.removeprefix("/api/drafts/templates/")
                    self._send(HTTPStatus.OK, legacy_web._json_bytes(template(model, repo)), "application/json; charset=utf-8")
                    return
                super().do_GET()
            except CaseServiceError as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

        def do_POST(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            if path not in {"/api/drafts/validate", "/api/drafts/run"}:
                super().do_POST()
                return
            try:
                payload = self._draft_payload()
                result = validate_draft(payload) if path.endswith("/validate") else run_draft(payload)
                self._send(HTTPStatus.OK, legacy_web._json_bytes(result), "application/json; charset=utf-8")
            except CaseServiceError as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

    return DraftHandler


def serve(*, host: str = "127.0.0.1", port: int = 8765, root: Path | None = None) -> None:
    if not 0 < port < 65536:
        raise ValueError("port must be in 1..65535 / 포트 범위 오류")
    server = ThreadingHTTPServer((host, port), make_handler(root))
    print(f"Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}")
    print("Draft Lab / Draft 랩: /draft")
    print("Press Ctrl+C to stop / 종료하려면 Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
