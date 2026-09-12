"""Read-only M19/M20 debt Web Lab / 읽기전용 이자부채·바인딩 준비 Web Lab."""
from __future__ import annotations

import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from valuation_hub import web as legacy_web
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.debt_binding import build_debt_binding_context, build_debt_date_assertion, validate_debt_binding_context, validate_debt_date_assertion
from valuation_hub.debt_components import aggregate_interest_bearing_debt, validate_interest_bearing_debt_evidence
from valuation_hub.debt_draft_binding import build_binding_proposal_with_debt, validate_binding_proposal_any
from valuation_hub.web_derived import make_handler as make_derived_handler, _dashboard_with_derived_link
from valuation_hub.web_product import product_layout

MAX_DEBT_REQUEST_BYTES = 16 * 1024 * 1024


def render_debt_lab() -> str:
    body = """
<div class="breadcrumbs"><a href="/">Dashboard</a><span>›</span><strong>Interest-Bearing Debt / 이자부채</strong></div>
<div class="section-head"><div><h2>Governed Debt Components + Binding Prep / 이자부채 구성요소 + 바인딩 준비</h2><p class="muted">Aggregate explicit debt, resolve report-stage dates only by human assertion, and prepare noncanonical debt-aware binding context. / 명시적 debt를 집계하고 report-stage 날짜는 인간승인으로만 해소하며 비정식 바인딩 context를 준비합니다.</p></div><span class="state-preview">LIABILITIES ≠ DEBT · HUMAN DATE LOCK · NO WRITE</span></div>
<div class="card"><p class="warn"><strong>Missing ≠ zero / 누락 ≠ 0</strong></p><p>Partial/conflict/candidate debt never binds. <code>REPORT_STAGE_ONLY</code> debt requires a SHA-locked human date assertion. No endpoint writes a Draft or canonical state.</p></div>
<label>Normalized debt-component observations JSON array<textarea id="debt-input" spellcheck="false" style="width:100%;min-height:240px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><button class="primary" onclick="aggregateDebt()">Aggregate / 집계</button></p>
<label>Debt evidence JSON<textarea id="debt-result" spellcheck="false" style="width:100%;min-height:300px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<div class="card"><h3>M20 Human Date Assertion / 인간 날짜승인</h3><p><input id="reviewer" placeholder="reviewer" style="width:24%"> <input id="approved-at" placeholder="2026-09-12T19:30:00+09:00" style="width:34%"> <input id="period-end" placeholder="YYYY-MM-DD" style="width:20%"></p><p><input id="review-basis" placeholder="review basis / 검토근거" style="width:90%"></p><button class="primary" onclick="buildAssertion()">Build Date Assertion</button></div>
<label>Date assertion JSON<textarea id="assertion" spellcheck="false" style="width:100%;min-height:220px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<div class="card"><h3>Binding Context / 바인딩 Context</h3><p><input id="as-of" placeholder="as_of YYYY-MM-DD" style="width:28%"> <input id="max-age" value="550" style="width:12%"></p><button class="primary" onclick="buildContext()">Build Binding Context</button></div>
<label>Debt binding context JSON<textarea id="context" spellcheck="false" style="width:100%;min-height:260px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<div id="debt-summary" class="preview-summary"><div class="muted">CALCULATE/VALIDATE ONLY · NO DRAFT FILE WRITE · NO CANONICAL WRITE</div></div><pre id="debt-output">—</pre>
<script>
const di=document.getElementById('debt-input'),dr=document.getElementById('debt-result'),da=document.getElementById('assertion'),dc=document.getElementById('context'),ds=document.getElementById('debt-summary'),doo=document.getElementById('debt-output');
function parsed(x,l){try{return JSON.parse(x.value)}catch(e){throw new Error(l+' JSON error: '+e.message)}}
async function post(path,payload){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const j=await r.json();doo.textContent=JSON.stringify(j,null,2);if(!r.ok)throw new Error(j.error||('HTTP '+r.status));return j}
async function aggregateDebt(){try{const obs=parsed(di,'Observations');if(!Array.isArray(obs))throw new Error('Observations must be an array');const j=await post('/api/debt/aggregate',{observations:obs});dr.value=JSON.stringify(j,null,2);ds.innerHTML='<div class="warn"><strong>'+j.coverage.status+'</strong><br>Debt value: '+j.interest_bearing_debt_value+' · '+j.class+'</div>'}catch(e){ds.innerHTML='<div class="bad">'+String(e)+'</div>'}}
async function buildAssertion(){try{const j=await post('/api/debt/date-assertion-build',{debt:parsed(dr,'Debt'),reviewer:document.getElementById('reviewer').value,approved_at:document.getElementById('approved-at').value,asserted_period_end:document.getElementById('period-end').value,review_basis:document.getElementById('review-basis').value});da.value=JSON.stringify(j,null,2);ds.innerHTML='<div class="good">Date assertion SHA locked</div>'}catch(e){ds.innerHTML='<div class="bad">'+String(e)+'</div>'}}
async function buildContext(){try{let a=null;if(da.value.trim())a=parsed(da,'Assertion');const j=await post('/api/debt/binding-context-build',{debt:parsed(dr,'Debt'),date_assertion:a,as_of:document.getElementById('as-of').value,max_age_days:Number(document.getElementById('max-age').value)});dc.value=JSON.stringify(j,null,2);ds.innerHTML='<div class="good"><strong>'+j.freshness.status+'</strong> · eligible='+j.binding_eligibility.eligible+'</div>'}catch(e){ds.innerHTML='<div class="bad">'+String(e)+'</div>'}}
</script>
"""
    return product_layout("Interest-Bearing Debt — Valuation Intelligence Hub", body)


def _dashboard_with_debt_link(repo: Path) -> str:
    page = _dashboard_with_derived_link(repo)
    marker = '<h2>Canonical cases / 정식 사례</h2>'
    banner = ('<div class="card" style="margin-bottom:18px;border-color:#f59e0b"><div><strong>Interest-Bearing Debt + M20 Binding Prep / 이자부채 + 바인딩 준비</strong></div><p>Aggregate explicit borrowing/bond components and resolve REPORT_STAGE_ONLY dates only through a human SHA lock. / 명시적 차입금·사채를 집계하고 REPORT_STAGE_ONLY 날짜는 인간 SHA 승인으로만 해소합니다.</p><a href="/debt">Open Debt Lab / 이자부채 랩 열기 →</a></div>')
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
            routes = {
                "/api/debt/aggregate", "/api/debt/validate",
                "/api/debt/date-assertion-build", "/api/debt/date-assertion-validate",
                "/api/debt/binding-context-build", "/api/debt/binding-context-validate",
                "/api/debt/binding-proposal-build", "/api/debt/binding-proposal-validate",
            }
            if path not in routes:
                super().do_POST(); return
            try:
                payload = self._debt_payload()
                if path == "/api/debt/aggregate":
                    observations = payload.get("observations")
                    if not isinstance(observations, list) or not observations or not all(isinstance(item, dict) for item in observations): raise CaseServiceError("non-empty observations array required / 비어있지 않은 observation 배열 필요")
                    result = aggregate_interest_bearing_debt(observations)
                elif path == "/api/debt/validate":
                    debt=payload.get("debt");
                    if not isinstance(debt,dict): raise CaseServiceError("debt evidence required / 이자부채 근거 필요")
                    result=validate_interest_bearing_debt_evidence(debt)
                elif path == "/api/debt/date-assertion-build":
                    debt=payload.get("debt")
                    if not isinstance(debt,dict): raise CaseServiceError("debt evidence required / 이자부채 근거 필요")
                    result=build_debt_date_assertion(debt,reviewer=payload.get("reviewer"),approved_at=payload.get("approved_at"),asserted_period_end=payload.get("asserted_period_end"),review_basis=payload.get("review_basis"))
                elif path == "/api/debt/date-assertion-validate":
                    assertion,debt=payload.get("assertion"),payload.get("debt")
                    if not isinstance(assertion,dict) or not isinstance(debt,dict): raise CaseServiceError("assertion and debt required / assertion·debt 필요")
                    result=validate_debt_date_assertion(assertion,debt)
                elif path == "/api/debt/binding-context-build":
                    debt,assertion=payload.get("debt"),payload.get("date_assertion")
                    if not isinstance(debt,dict) or (assertion is not None and not isinstance(assertion,dict)): raise CaseServiceError("valid debt/date assertion required / 유효 debt·날짜승인 필요")
                    result=build_debt_binding_context(debt,as_of=payload.get("as_of"),max_age_days=payload.get("max_age_days",550),date_assertion=assertion)
                elif path == "/api/debt/binding-context-validate":
                    context=payload.get("context")
                    if not isinstance(context,dict): raise CaseServiceError("debt binding context required / debt 바인딩 context 필요")
                    result=validate_debt_binding_context(context)
                elif path == "/api/debt/binding-proposal-build":
                    observations,context=payload.get("observations"),payload.get("debt_context")
                    if not isinstance(observations,list) or not observations or not all(isinstance(x,dict) for x in observations) or not isinstance(context,dict): raise CaseServiceError("observations and debt_context required / observations·debt_context 필요")
                    result=build_binding_proposal_with_debt(observations,context,as_of=payload.get("as_of"),max_age_days=payload.get("max_age_days",550))
                else:
                    proposal=payload.get("proposal")
                    if not isinstance(proposal,dict): raise CaseServiceError("binding proposal required / 바인딩 proposal 필요")
                    result=validate_binding_proposal_any(proposal)
                self._send(HTTPStatus.OK, legacy_web._json_bytes(result), "application/json; charset=utf-8")
            except (CaseServiceError, ValueError, TypeError) as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

    return DebtHandler


def serve(*, host: str = "127.0.0.1", port: int = 8765, root: Path | None = None) -> None:
    if not 0 < port < 65536: raise ValueError("port must be in 1..65535 / 포트 범위 오류")
    server = ThreadingHTTPServer((host, port), make_handler(root))
    print(f"Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}")
    print("Interest-Bearing Debt + M20 binding prep / 이자부채 + M20 바인딩 준비: /debt")
    print("Press Ctrl+C to stop / 종료하려면 Ctrl+C")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
