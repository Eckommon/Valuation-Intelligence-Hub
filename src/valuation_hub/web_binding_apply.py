"""Read-only/in-memory M17 human-approved Draft binding application Web Lab."""
from __future__ import annotations
import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from valuation_hub import web as legacy_web
from valuation_hub.binding_apply import build_binding_approval, validate_binding_approval, apply_binding_approval, validate_bound_draft_result
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.web_binding import make_handler as make_binding_handler, _dashboard_with_binding_link
from valuation_hub.web_product import product_layout

MAX_APPLY_REQUEST_BYTES = 32 * 1024 * 1024


def render_binding_apply_lab() -> str:
    body = """
<div class="breadcrumbs"><a href="/">Dashboard</a><span>›</span><strong>Human-approved Draft Binding / 인간승인 Draft 바인딩</strong></div>
<div class="section-head"><div><h2>Human-approved Binding Apply / 인간승인 바인딩 적용</h2><p class="muted">Create a SHA-locked approval, then apply only approved DIRECT_BIND fields in memory to a noncanonical Draft. / SHA 잠금 승인을 만든 뒤 승인된 DIRECT_BIND만 비정식 Draft에 메모리상 적용합니다.</p></div><span class="state-preview">IN-MEMORY ONLY · NO FILE OVERWRITE</span></div>
<div class="card"><p class="warn"><strong>No approval, no apply / 승인 없이는 적용 불가</strong></p><p>The approval locks proposal SHA, Draft-before SHA, target entity/scope, reviewer, timestamp, and approved fields. Output remains a Draft and <code>canonical=false</code>. / 승인 객체가 모든 적용 범위를 잠그며 결과는 여전히 비정식 Draft입니다.</p></div>
<label>M16 Binding Proposal JSON<textarea id="a-proposal" spellcheck="false" style="width:100%;min-height:280px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<label>Target Draft JSON<textarea id="a-draft" spellcheck="false" style="width:100%;min-height:320px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<div class="grid compact"><label>Reviewer<input id="a-reviewer"></label><label>Entity ID<input id="a-entity"></label><label>Financial scope<input id="a-scope" value="CFS"></label><label>Approved fields<input id="a-fields" placeholder="equity.cash"></label><label>Approved at<input id="a-time" placeholder="2026-09-11T17:50:00+09:00"></label></div>
<p><button class="primary" onclick="buildApproval()">Build approval / 승인 생성</button></p>
<label>Approval JSON<textarea id="a-approval" spellcheck="false" style="width:100%;min-height:280px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><button class="primary" onclick="validateApproval()">Validate approval / 승인 검증</button> <button class="primary" onclick="applyBinding()">Apply in memory / 메모리 적용</button></p>
<label>Bound Draft Result JSON<textarea id="a-result" spellcheck="false" style="width:100%;min-height:360px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><button class="primary" onclick="validateResult()">Validate result / 결과 검증</button></p>
<div id="a-summary" class="preview-summary"><div class="muted">No filesystem or canonical write is available. / 파일시스템·정식 기록 기능은 없습니다.</div></div><pre id="a-output">—</pre>
<script>
const p=document.getElementById('a-proposal'),d=document.getElementById('a-draft'),a=document.getElementById('a-approval'),r=document.getElementById('a-result'),s=document.getElementById('a-summary'),o=document.getElementById('a-output');
function obj(x,l){try{return JSON.parse(x.value)}catch(e){throw new Error(l+' JSON error: '+e.message)}} async function post(path,payload){const q=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const j=await q.json();o.textContent=JSON.stringify(j,null,2);if(!q.ok)throw new Error(j.error||('HTTP '+q.status));return j} function fields(){return document.getElementById('a-fields').value.split(',').map(x=>x.trim()).filter(Boolean)}
async function buildApproval(){try{const j=await post('/api/binding-apply/approval-build',{proposal:obj(p,'Proposal'),draft:obj(d,'Draft'),reviewer:document.getElementById('a-reviewer').value,target_entity_id:document.getElementById('a-entity').value,target_financial_scope:document.getElementById('a-scope').value,approved_fields:fields(),approved_at:document.getElementById('a-time').value});a.value=JSON.stringify(j,null,2);s.innerHTML='<div class="warn"><strong>'+j.status+'</strong><br><code>'+j.approval_sha256+'</code><br><span class="muted">NO APPLY YET · CANONICAL=false</span></div>'}catch(e){s.innerHTML='<div class="bad">'+String(e)+'</div>'}}
async function validateApproval(){try{const j=await post('/api/binding-apply/approval-validate',{proposal:obj(p,'Proposal'),draft:obj(d,'Draft'),approval:obj(a,'Approval')});s.innerHTML='<div class="good"><strong>'+j.status+'</strong><br>Approved fields: '+j.approved_field_count+'</div>'}catch(e){s.innerHTML='<div class="bad">'+String(e)+'</div>'}}
async function applyBinding(){try{const j=await post('/api/binding-apply/apply',{proposal:obj(p,'Proposal'),draft:obj(d,'Draft'),approval:obj(a,'Approval')});r.value=JSON.stringify(j,null,2);s.innerHTML='<div class="warn"><strong>'+j.status+'</strong><br>Diffs: '+j.applied_diffs.length+'<br><code>'+j.result_sha256+'</code><br><span class="muted">IN-MEMORY RESULT · CANONICAL=false</span></div>'}catch(e){s.innerHTML='<div class="bad">'+String(e)+'</div>'}}
async function validateResult(){try{const j=await post('/api/binding-apply/result-validate',{result:obj(r,'Result')});s.innerHTML='<div class="good"><strong>'+j.status+'</strong><br>Applied: '+j.applied_field_count+' · Unresolved: '+j.unresolved_count+'</div>'}catch(e){s.innerHTML='<div class="bad">'+String(e)+'</div>'}}
</script>
"""
    return product_layout("Human-approved Draft Binding — Valuation Intelligence Hub", body)


def _dashboard_with_apply_link(repo: Path) -> str:
    page=_dashboard_with_binding_link(repo); marker='<h2>Canonical cases / 정식 사례</h2>'
    banner=('<div class="card" style="margin-bottom:18px;border-color:#f59e0b"><div><strong>Human-approved Draft Binding / 인간승인 Draft 바인딩</strong></div><p>SHA-lock approval and apply only approved DIRECT_BIND fields in memory. No file overwrite or canonical write. / 승인 잠금 후 DIRECT_BIND만 메모리 적용합니다. 파일 덮어쓰기·정식 기록 없음.</p><a href="/binding-apply">Open Human-approved Binding Lab / 인간승인 바인딩 랩 열기 →</a></div>')
    return page.replace(marker,banner+marker,1)


def make_handler(root: Path|None=None):
    repo=root.resolve() if root else find_repo_root(); Base=make_binding_handler(repo)
    class ApplyHandler(Base):
        def _payload(self)->dict:
            raw=self.headers.get('Content-Length','0')
            try:length=int(raw)
            except ValueError as exc: raise CaseServiceError('invalid Content-Length / Content-Length 오류') from exc
            if length<=0 or length>MAX_APPLY_REQUEST_BYTES: raise CaseServiceError('binding apply request size invalid / 바인딩 적용 요청크기 오류')
            try: payload=json.loads(self.rfile.read(length).decode('utf-8'))
            except (UnicodeDecodeError,json.JSONDecodeError) as exc: raise CaseServiceError('invalid binding apply JSON / 바인딩 적용 JSON 오류') from exc
            if not isinstance(payload,dict): raise CaseServiceError('binding apply payload must be object / 바인딩 적용 payload 객체 필요')
            if any(k in payload for k in ('api_key','crtfc_key','user_agent')): raise CaseServiceError('credentials forbidden / 인증정보 금지')
            return payload
        def do_GET(self)->None:  # noqa: N802
            path=unquote(urlparse(self.path).path)
            try:
                if path=='/': self._send(HTTPStatus.OK,_dashboard_with_apply_link(repo).encode('utf-8'),'text/html; charset=utf-8'); return
                if path=='/binding-apply': self._send(HTTPStatus.OK,render_binding_apply_lab().encode('utf-8'),'text/html; charset=utf-8'); return
                super().do_GET()
            except CaseServiceError as exc:self._error(path,exc,HTTPStatus.BAD_REQUEST)
        def do_POST(self)->None:  # noqa: N802
            path=unquote(urlparse(self.path).path); routes={'/api/binding-apply/approval-build','/api/binding-apply/approval-validate','/api/binding-apply/apply','/api/binding-apply/result-validate'}
            if path not in routes: super().do_POST(); return
            try:
                x=self._payload()
                if path.endswith('/approval-build'):
                    proposal=x.get('proposal'); draft=x.get('draft'); fields=x.get('approved_fields')
                    if not isinstance(proposal,dict) or not isinstance(draft,dict) or not isinstance(fields,list): raise CaseServiceError('proposal/draft/approved_fields required / 필수 객체 누락')
                    result=build_binding_approval(proposal,draft,reviewer=x.get('reviewer'),target_entity_id=x.get('target_entity_id'),target_financial_scope=x.get('target_financial_scope'),approved_fields=fields,approved_at=x.get('approved_at'))
                elif path.endswith('/approval-validate'):
                    result=validate_binding_approval(x.get('approval'),x.get('proposal'),x.get('draft'))
                elif path.endswith('/apply'):
                    result=apply_binding_approval(x.get('proposal'),x.get('draft'),x.get('approval'))
                else: result=validate_bound_draft_result(x.get('result'))
                self._send(HTTPStatus.OK,legacy_web._json_bytes(result),'application/json; charset=utf-8')
            except (CaseServiceError,ValueError,TypeError) as exc:self._error(path,exc,HTTPStatus.BAD_REQUEST)
    return ApplyHandler


def serve(*,host:str='127.0.0.1',port:int=8765,root:Path|None=None)->None:
    if not 0<port<65536: raise ValueError('port must be in 1..65535 / 포트 범위 오류')
    server=ThreadingHTTPServer((host,port),make_handler(root)); print(f'Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}'); print('Human-approved Draft Binding / 인간승인 Draft 바인딩: /binding-apply'); print('Press Ctrl+C to stop / 종료하려면 Ctrl+C')
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
