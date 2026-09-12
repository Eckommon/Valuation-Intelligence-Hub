"""Read-only M21 historical dilution Web Lab / 읽기전용 역사적 희석도 Web Lab."""
from __future__ import annotations

import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from valuation_hub import web as legacy_web
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.share_dilution import (
    derive_historical_dilution,
    extract_sec_dilution_candidate,
    normalize_share_dilution_candidate,
    validate_historical_dilution,
    validate_share_dilution_observation,
)
from valuation_hub.web_debt import make_handler as make_debt_handler, _dashboard_with_debt_link
from valuation_hub.web_product import product_layout

MAX_REQUEST_BYTES=16*1024*1024


def render_dilution_lab()->str:
    body="""
<div class="breadcrumbs"><a href="/">Dashboard</a><span>›</span><strong>Historical Dilution / 역사적 희석도</strong></div>
<div class="section-head"><div><h2>Governed Dilution Reference / 거버넌스 희석주식 참조근거</h2><p class="muted">Compare exact same-period weighted-average basic and diluted EPS denominators without converting them into valuation-date shares.</p></div><span class="state-preview">HISTORICAL ONLY · NOT VALUATION-DATE SHARES · CALCULATE ONLY</span></div>
<div class="card"><p class="warn"><strong>weighted-average diluted shares ≠ valuation-date fully diluted shares</strong></p><p>M21 is historical reference only. It cannot write <code>equity.diluted_shares</code>, mutate a Draft, or create canonical state.</p></div>
<label>Basic observation JSON<textarea id="basic" spellcheck="false" style="width:100%;min-height:220px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<label>Diluted observation JSON<textarea id="diluted" spellcheck="false" style="width:100%;min-height:220px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><button class="primary" onclick="derive()">Derive historical dilution / 역사적 희석도 계산</button></p>
<pre id="out">—</pre>
<script>
const b=document.getElementById('basic'),d=document.getElementById('diluted'),o=document.getElementById('out');
function p(x,l){try{return JSON.parse(x.value)}catch(e){throw new Error(l+' JSON error: '+e.message)}}
async function derive(){try{const r=await fetch('/api/dilution/derive',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({basic:p(b,'Basic'),diluted:p(d,'Diluted')})});const j=await r.json();o.textContent=JSON.stringify(j,null,2)}catch(e){o.textContent=String(e)}}
</script>
"""
    return product_layout("Historical Dilution — Valuation Intelligence Hub",body)


def _dashboard(repo:Path)->str:
    page=_dashboard_with_debt_link(repo);marker='<h2>Canonical cases / 정식 사례</h2>'
    banner=('<div class="card" style="margin-bottom:18px;border-color:#a78bfa"><div><strong>Historical Dilution Reference / 역사적 희석도 참조</strong></div><p>SEC weighted-average EPS denominator evidence, explicitly separated from valuation-date fully diluted shares.</p><a href="/dilution">Open Dilution Lab / 희석도 랩 열기 →</a></div>')
    return page.replace(marker,banner+marker,1)


def make_handler(root:Path|None=None):
    repo=root.resolve() if root else find_repo_root();Base=make_debt_handler(repo)
    class DilutionHandler(Base):
        def _payload(self)->dict:
            try:length=int(self.headers.get('Content-Length','0'))
            except ValueError as exc:raise CaseServiceError('invalid Content-Length / Content-Length 오류') from exc
            if length<=0 or length>MAX_REQUEST_BYTES:raise CaseServiceError('dilution request size invalid / 희석도 요청크기 오류')
            try:value=json.loads(self.rfile.read(length).decode('utf-8'))
            except (UnicodeDecodeError,json.JSONDecodeError) as exc:raise CaseServiceError('invalid dilution JSON / 희석도 JSON 오류') from exc
            if not isinstance(value,dict):raise CaseServiceError('dilution payload object required / 희석도 payload 객체 필요')
            if any(k in value for k in ('api_key','crtfc_key','user_agent')):raise CaseServiceError('credentials forbidden / 인증정보 금지')
            return value
        def do_GET(self)->None:  # noqa:N802
            path=unquote(urlparse(self.path).path)
            try:
                if path=='/':self._send(HTTPStatus.OK,_dashboard(repo).encode(),'text/html; charset=utf-8');return
                if path=='/dilution':self._send(HTTPStatus.OK,render_dilution_lab().encode(),'text/html; charset=utf-8');return
                super().do_GET()
            except CaseServiceError as exc:self._error(path,exc,HTTPStatus.BAD_REQUEST)
        def do_POST(self)->None:  # noqa:N802
            path=unquote(urlparse(self.path).path)
            routes={'/api/dilution/sec-extract','/api/dilution/normalize','/api/dilution/observation-validate','/api/dilution/derive','/api/dilution/validate'}
            if path not in routes:super().do_POST();return
            try:
                q=self._payload()
                if path=='/api/dilution/sec-extract':
                    snapshot=q.get('snapshot');
                    if not isinstance(snapshot,dict):raise CaseServiceError('SEC snapshot required / SEC snapshot 필요')
                    result=extract_sec_dilution_candidate(snapshot,q.get('metric'),period_start=q.get('period_start'),period_end=q.get('period_end'),form=q.get('form'))
                elif path=='/api/dilution/normalize':
                    c=q.get('candidate');
                    if not isinstance(c,dict):raise CaseServiceError('dilution candidate required / 희석주식 candidate 필요')
                    result=normalize_share_dilution_candidate(c)
                elif path=='/api/dilution/observation-validate':
                    x=q.get('observation');
                    if not isinstance(x,dict):raise CaseServiceError('dilution observation required / 희석주식 observation 필요')
                    result=validate_share_dilution_observation(x)
                elif path=='/api/dilution/derive':
                    b,d=q.get('basic'),q.get('diluted')
                    if not isinstance(b,dict) or not isinstance(d,dict):raise CaseServiceError('basic and diluted observations required / basic·diluted observation 필요')
                    result=derive_historical_dilution(b,d)
                else:
                    x=q.get('derived');
                    if not isinstance(x,dict):raise CaseServiceError('historical dilution evidence required / 역사적 희석도 근거 필요')
                    result=validate_historical_dilution(x)
                self._send(HTTPStatus.OK,legacy_web._json_bytes(result),'application/json; charset=utf-8')
            except (CaseServiceError,ValueError,TypeError) as exc:self._error(path,exc,HTTPStatus.BAD_REQUEST)
    return DilutionHandler


def serve(*,host:str='127.0.0.1',port:int=8765,root:Path|None=None)->None:
    if not 0<port<65536:raise ValueError('port must be in 1..65535 / 포트 범위 오류')
    server=ThreadingHTTPServer((host,port),make_handler(root));print(f'Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}');print('Historical Dilution / 역사적 희석도: /dilution');print('Press Ctrl+C to stop / 종료하려면 Ctrl+C')
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
