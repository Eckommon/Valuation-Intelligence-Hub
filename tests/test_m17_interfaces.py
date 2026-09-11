"""M17 CLI/Web contracts for human-approved noncanonical binding apply."""
from __future__ import annotations
import copy, hashlib, json, threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from valuation_hub import cli_entry
from valuation_hub.draft_binding import build_binding_proposal
from valuation_hub.web_binding_apply import make_handler, render_binding_apply_lab

ROOT=Path(__file__).resolve().parents[1]; TEMPLATE=ROOT/'templates'/'draft_equity_fcff.json'

def _hash(v:dict,f:str)->str:
    x=copy.deepcopy(v);x.pop(f,None);return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def _cash()->dict:
    x={"schema_version":"financial-observation-v0.1","status":"FINANCIAL_OBSERVATION_NORMALIZED","canonical":False,"class":"NORMALIZED_FACT","metric":"cash","value":777,"unit":"KRW","entity":{"id":"DART_CORP:00126380","source_system":"TEST","financial_scope":"CFS"},"period":{"kind":"INSTANT","start":None,"end":"2026-06-30","duration_days":None,"fiscal_year":2026,"fiscal_period":"H1","fiscal_quarter":2,"report_stage":"H1","date_precision":"EXACT"},"lineage":{"normalization_rule":"TEST","source_candidate_sha256":"a"*64},"observation_sha256":""};x['observation_sha256']=_hash(x,'observation_sha256');return x

def _proposal()->dict:return build_binding_proposal([_cash()],as_of='2026-09-11')
def _draft()->dict:
    d=json.loads(TEMPLATE.read_text(encoding='utf-8'));d['currency']='KRW';d['name']='M17 Interface Test';return d

def _post(base:str,path:str,payload:dict)->tuple[int,dict]:
    q=Request(base+path,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urlopen(q,timeout=4) as r:return r.status,json.loads(r.read().decode())

def test_cli_dispatch_exposes_m17_commands()->None:
    for c in ('binding-approval-build','binding-approval-validate','binding-apply','bound-draft-validate'):assert cli_entry._command([c])==c

def test_cli_approval_apply_validate_round_trip(tmp_path:Path,capsys)->None:
    p,d=_proposal(),_draft(); pp=tmp_path/'p.json';dp=tmp_path/'d.json';pp.write_text(json.dumps(p));dp.write_text(json.dumps(d))
    args=['binding-approval-build',str(pp),str(dp),'--reviewer','human','--target-entity-id','DART_CORP:00126380','--target-financial-scope','CFS','--approved-field','equity.cash','--approved-at','2026-09-11T17:50:00+09:00']
    assert cli_entry.main(args)==0; approval=json.loads(capsys.readouterr().out); ap=tmp_path/'a.json';ap.write_text(json.dumps(approval))
    assert cli_entry.main(['binding-apply',str(pp),str(dp),str(ap)])==0; result=json.loads(capsys.readouterr().out); assert result['draft_after']['equity']['cash']==777; rp=tmp_path/'r.json';rp.write_text(json.dumps(result))
    assert cli_entry.main(['bound-draft-validate',str(rp)])==0; checked=json.loads(capsys.readouterr().out);assert checked['status']=='PASS_BOUND_DRAFT_RESULT_VALIDATION'

def test_web_lab_requires_approval_and_has_no_file_write()->None:
    page=render_binding_apply_lab();assert 'No approval, no apply' in page;assert 'IN-MEMORY ONLY · NO FILE OVERWRITE' in page;assert '/api/binding-apply/apply' in page;assert '/api/binding-apply/file-write' not in page

def test_web_approval_apply_round_trip()->None:
    server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(ROOT));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        base=f'http://127.0.0.1:{server.server_port}';p,d=_proposal(),_draft()
        _,a=_post(base,'/api/binding-apply/approval-build',{'proposal':p,'draft':d,'reviewer':'human','target_entity_id':'DART_CORP:00126380','target_financial_scope':'CFS','approved_fields':['equity.cash'],'approved_at':'2026-09-11T17:50:00+09:00'})
        _,r=_post(base,'/api/binding-apply/apply',{'proposal':p,'draft':d,'approval':a});assert r['draft_after']['equity']['cash']==777;assert r['canonical'] is False
        _,v=_post(base,'/api/binding-apply/result-validate',{'result':r});assert v['status']=='PASS_BOUND_DRAFT_RESULT_VALIDATION'
    finally:server.shutdown();server.server_close();thread.join(timeout=4)

def test_web_apply_without_valid_approval_fails()->None:
    server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(ROOT));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        base=f'http://127.0.0.1:{server.server_port}';req=Request(base+'/api/binding-apply/apply',data=json.dumps({'proposal':_proposal(),'draft':_draft(),'approval':{}}).encode(),headers={'Content-Type':'application/json'},method='POST')
        try:urlopen(req,timeout=4);raise AssertionError('apply accepted without valid approval')
        except HTTPError as exc:assert exc.code==400
    finally:server.shutdown();server.server_close();thread.join(timeout=4)
