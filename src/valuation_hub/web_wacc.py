"""Read-only M24 governed WACC Web Lab / 읽기전용 M24 WACC Web Lab."""
from __future__ import annotations

import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote,urlparse

from valuation_hub import web as legacy_web
from valuation_hub.case_service import CaseServiceError,find_repo_root
from valuation_hub.wacc_assumption import build_wacc_candidate,build_wacc_review_assertion,finalize_reviewed_wacc,validate_reviewed_wacc,validate_wacc_candidate,validate_wacc_review_assertion
from valuation_hub.wacc_draft_binding import build_binding_proposal_with_wacc,validate_binding_proposal_v4
from valuation_hub.web_product import product_layout
from valuation_hub.web_share_binding import make_handler as make_prior_handler,_dashboard as _prior_dashboard

MAX_REQUEST_BYTES=16*1024*1024


def render_wacc_lab()->str:
    body="""
<div class="breadcrumbs"><a href="/">Dashboard</a><span>›</span><strong>WACC / 할인율</strong></div>
<div class="section-head"><div><h2>Governed WACC Assumption / 거버넌스 WACC 가정</h2><p class="muted">Build from explicit sourced inputs, review separately, then enrich an existing binding proposal. WACC remains an ASSUMPTION.</p></div><span class="state-preview">ASSUMPTION · HUMAN REVIEW · CALCULATE/VALIDATE ONLY</span></div>
<div class="card"><p class="warn"><strong>Calculated WACC ≠ reviewed assumption ≠ historical fact.</strong></p><p>Required components: risk-free rate, ERP, levered beta, pre-tax debt cost, equity/debt market values, tax rate. Stale or Tier-D required inputs cannot be reviewed.</p></div>
<label>Request JSON<textarea id="req" spellcheck="false" style="width:100%;min-height:360px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p>
<select id="action"><option value="candidate-build">Build candidate</option><option value="candidate-validate">Validate candidate</option><option value="review-build">Build review assertion</option><option value="review-validate">Validate review assertion</option><option value="finalize">Finalize reviewed package</option><option value="validate">Validate reviewed package</option><option value="binding-build">Build v0.4 proposal</option><option value="binding-validate">Validate v0.4 proposal</option></select>
<button class="primary" onclick="run()">Run / 실행</button></p>
<div class="preview-summary"><div class="muted">NO DRAFT APPLY · NO FILE WRITE · NO PROMOTION · NO CANONICAL WRITE</div></div><pre id="out">—</pre>
<script>
const q=document.getElementById('req'),a=document.getElementById('action'),o=document.getElementById('out');
async function run(){try{const body=JSON.parse(q.value);const r=await fetch('/api/wacc/'+a.value,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});o.textContent=JSON.stringify(await r.json(),null,2)}catch(e){o.textContent=String(e)}}
</script>
"""
    return product_layout("Governed WACC — Valuation Intelligence Hub",body)


def _dashboard(repo:Path)->str:
    page=_prior_dashboard(repo);marker='<h2>Canonical cases / 정식 사례</h2>'
    banner='<div class="card" style="margin-bottom:18px;border-color:#22c55e"><div><strong>M24 Governed WACC / M24 거버넌스 WACC</strong></div><p>Sourced components → assumption candidate → human review → reviewed WACC → v0.4 scenario.wacc proposal.</p><a href="/wacc">Open WACC Lab / WACC 랩 열기 →</a></div>'
    return page.replace(marker,banner+marker,1)


def make_handler(root:Path|None=None):
    repo=root.resolve() if root else find_repo_root();Base=make_prior_handler(repo)
    class WaccHandler(Base):
        def _m24_payload(self)->dict:
            try:length=int(self.headers.get('Content-Length','0'))
            except ValueError as exc:raise CaseServiceError('invalid Content-Length / Content-Length 오류') from exc
            if length<=0 or length>MAX_REQUEST_BYTES:raise CaseServiceError('WACC request size invalid / WACC 요청크기 오류')
            try:v=json.loads(self.rfile.read(length).decode('utf-8'))
            except (UnicodeDecodeError,json.JSONDecodeError) as exc:raise CaseServiceError('invalid WACC JSON / WACC JSON 오류') from exc
            if not isinstance(v,dict):raise CaseServiceError('WACC payload object required / WACC payload 객체 필요')
            if any(k in v for k in ('api_key','crtfc_key','user_agent')):raise CaseServiceError('credentials forbidden / 인증정보 금지')
            return v
        def do_GET(self)->None:  # noqa:N802
            path=unquote(urlparse(self.path).path)
            try:
                if path=='/':self._send(HTTPStatus.OK,_dashboard(repo).encode(),'text/html; charset=utf-8');return
                if path=='/wacc':self._send(HTTPStatus.OK,render_wacc_lab().encode(),'text/html; charset=utf-8');return
                super().do_GET()
            except CaseServiceError as exc:self._error(path,exc,HTTPStatus.BAD_REQUEST)
        def do_POST(self)->None:  # noqa:N802
            path=unquote(urlparse(self.path).path);prefix='/api/wacc/'
            if not path.startswith(prefix):super().do_POST();return
            try:
                q=self._m24_payload();action=path[len(prefix):]
                if action=='candidate-build':
                    inputs=q.get('inputs');scenarios=q.get('scenario_names')
                    if not isinstance(inputs,list) or not all(isinstance(x,dict) for x in inputs):raise CaseServiceError('WACC inputs array required / WACC inputs 배열 필요')
                    result=build_wacc_candidate(inputs,entity_id=q.get('entity_id'),financial_scope=q.get('financial_scope'),capital_currency=q.get('capital_currency'),as_of=q.get('as_of'),scenario_names=scenarios)
                elif action=='candidate-validate':result=validate_wacc_candidate(q.get('candidate'))
                elif action=='review-build':result=build_wacc_review_assertion(q.get('candidate'),reviewer=q.get('reviewer'),approved_at=q.get('approved_at'),review_basis=q.get('review_basis'))
                elif action=='review-validate':result=validate_wacc_review_assertion(q.get('assertion'),q.get('candidate'))
                elif action=='finalize':result=finalize_reviewed_wacc(q.get('candidate'),q.get('assertion'))
                elif action=='validate':result=validate_reviewed_wacc(q.get('package'))
                elif action=='binding-build':result=build_binding_proposal_with_wacc(q.get('base_proposal'),q.get('wacc_package'))
                elif action=='binding-validate':result=validate_binding_proposal_v4(q.get('proposal'))
                else:raise CaseServiceError('unsupported WACC Web action / 미지원 WACC Web 동작')
                self._send(HTTPStatus.OK,legacy_web._json_bytes(result),'application/json; charset=utf-8')
            except (CaseServiceError,ValueError,TypeError,KeyError) as exc:self._error(path,exc,HTTPStatus.BAD_REQUEST)
    return WaccHandler


def serve(*,host:str='127.0.0.1',port:int=8765,root:Path|None=None)->None:
    if not 0<port<65536:raise ValueError('port must be in 1..65535 / 포트 범위 오류')
    server=ThreadingHTTPServer((host,port),make_handler(root));print(f'Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}');print('M24 WACC Lab / M24 WACC 랩: /wacc');print('Press Ctrl+C to stop / 종료하려면 Ctrl+C')
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
