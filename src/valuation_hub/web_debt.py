"""Read-only M19 interest-bearing debt Web Lab / 읽기전용 이자부채 Web Lab."""
from __future__ import annotations

import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from valuation_hub import web as legacy_web
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.debt_components import aggregate_interest_bearing_debt, validate_interest_bearing_debt_evidence
from valuation_hub.web_derived import make_handler as make_derived_handler, _dashboard_with_derived_link
from valuation_hub.web_product import product_layout

MAX_DEBT_REQUEST_BYTES = 16 * 1024 * 1024


def render_debt_lab() -> str:
    body = """
<div class="breadcrumbs"><a href="/">Dashboard</a><span>›</span><strong>Interest-Bearing Debt / 이자부채</strong></div>
<div class="section-head"><div><h2>Governed Debt Components / 이자부채 구성요소</h2><p class="muted">Aggregate only explicit compatible debt-component observations. / 명시적이며 호환되는 debt 구성요소 observation만 집계합니다.</p></div><span class="state-preview">LIABILITIES ≠ DEBT · CALCULATE ONLY</span></div>
<div class="card"><p class="warn"><strong>Missing ≠ zero / 누락 ≠ 0</strong></p><p>Partial coverage exposes only <code>known_component_sum</code>. A final debt value exists only when all five core components are explicitly evidenced with no conflict. Lease liabilities are excluded pending an explicit policy.</p></div>
<label>Normalized debt-component observations JSON array<textarea id="debt-input" spellcheck="false" style="width:100%;min-height:380px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><button class="primary" onclick="aggregateDebt()">Aggregate / 집계</button></p>
<label>Debt evidence JSON<textarea id="debt-result" spellcheck="false" style="width:100%;min-height:420px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><button class="primary" onclick="validateDebt()">Validate / 검증</button></p>
<div id="debt-summary" class="preview-summary"><div class="muted">No Draft mutation or canonical write is available. / Draft 변경·정식 기록 기능은 없습니다.</div></div><pre id="debt-output">—</pre>
<script>
const di=document.getElementById('debt-input'),dr=document.getElementById('debt-result'),ds=document.getElementById('debt-summary'),doo=document.getElementById('debt-output');
function parsed(x,l){try{return JSON.parse(x.value)}catch(e){throw new Error(l+' JSON error: '+e.message)}}
async function post(path,payload){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const j=await r.json();doo.textContent=JSON.stringify(j,null,2);if(!r.ok)throw new Error(j.error||('HTTP '+r.status));return j}
async function aggregateDebt(){try{const obs=parsed(di,'Observations');if(!Array.isArray(obs))throw new Error('Observations must be an array');const j=await post('/api/debt/aggregate',{observations:obs});dr.value=JSON.stringify(j,null,2);ds.innerHTML='<div class="warn"><strong>'+j.coverage.status+'</strong><br>Known sum: '+j.known_component_sum+'<br>Debt value: '+j.interest_bearing_debt_value+'<br>'+j.class+' · eligible='+j.semantic_boundary.eligible_for_draft_direct_bind+'</div>'}catch(e){ds.innerHTML='<div class="bad">'+String(e)+'</div>'}}
async function validateDebt(){try{const j=await post('/api/debt/validate',{debt:parsed(dr,'Debt evidence')});ds.innerHTML='<div class="good"><strong>'+j.status+'</strong><br>'+j.coverage_status+' · '+j.class+' · eligible='+j.eligible_for_draft_direct_bind+'</div>'}catch(e){ds.innerHTML='<div class="bad">'+String(e)+'</div>'}}
</script>
"""
    return product_layout("Interest-Bearing Debt — Valuation Intelligence Hub", body)


def _dashboard_with_debt_link(repo: Path) -> str:
    page = _dashboard_with_derived_link(repo)
    marker = '<h2>Canonical cases / 정식 사례</h2>'
    banner = ('<div class="card" style="margin-bottom:18px;border-color:#f59e0b"><div><strong>Interest-Bearing Debt / 이자부채</strong></div><p>Aggregate explicit borrowing/bond components with visible completeness. Total liabilities and missing values are never substituted. / 명시적 차입금·사채 구성요소만 집계하며 총부채·누락값을 대체하지 않습니다.</p><a href="/debt">Open Debt Lab / 이자부채 랩 열기 →</a></div>')
    return page.replace(marker, banner + marker, 1)


def make_handler(root: Path | None = None):
    repo = root.resolve() if root else find_repo_root()
    Base = make_derived_handler(repo)

    class DebtHandler(Base):
        def _debt_payload(self) -> dict:
            raw = self.headers.get("Content-Length", "0")
            try: length = int(raw)
            except ValueError as exc: raise CaseServiceError("invalid Content-Length / Content-Length 오류") from exc
            if length <= 0 or length > MAX_DEBT_REQUEST_BYTES:
                raise CaseServiceError("debt request size invalid / 이자부채 요청크기 오류")
            try: payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc: raise CaseServiceError("invalid debt JSON / 이자부채 JSON 오류") from exc
            if not isinstance(payload, dict): raise CaseServiceError("debt payload must be object / 이자부채 payload 객체 필요")
            if any(key in payload for key in ("api_key", "crtfc_key", "user_agent")):
                raise CaseServiceError("credentials forbidden / 인증정보 금지")
            return payload

        def do_GET(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            try:
                if path == "/": self._send(HTTPStatus.OK, _dashboard_with_debt_link(repo).encode("utf-8"), "text/html; charset=utf-8"); return
                if path == "/debt": self._send(HTTPStatus.OK, render_debt_lab().encode("utf-8"), "text/html; charset=utf-8"); return
                super().do_GET()
            except CaseServiceError as exc: self._error(path, exc, HTTPStatus.BAD_REQUEST)

        def do_POST(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            if path not in {"/api/debt/aggregate", "/api/debt/validate"}:
                super().do_POST(); return
            try:
                payload = self._debt_payload()
                if path.endswith("/aggregate"):
                    observations = payload.get("observations")
                    if not isinstance(observations, list) or not observations or not all(isinstance(item, dict) for item in observations):
                        raise CaseServiceError("non-empty observations array required / 비어있지 않은 observation 배열 필요")
                    result = aggregate_interest_bearing_debt(observations)
                else:
                    debt = payload.get("debt")
                    if not isinstance(debt, dict): raise CaseServiceError("debt evidence required / 이자부채 근거 필요")
                    result = validate_interest_bearing_debt_evidence(debt)
                self._send(HTTPStatus.OK, legacy_web._json_bytes(result), "application/json; charset=utf-8")
            except (CaseServiceError, ValueError, TypeError) as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

    return DebtHandler


def serve(*, host: str = "127.0.0.1", port: int = 8765, root: Path | None = None) -> None:
    if not 0 < port < 65536: raise ValueError("port must be in 1..65535 / 포트 범위 오류")
    server = ThreadingHTTPServer((host, port), make_handler(root))
    print(f"Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}")
    print("Interest-Bearing Debt / 이자부채: /debt")
    print("Press Ctrl+C to stop / 종료하려면 Ctrl+C")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
