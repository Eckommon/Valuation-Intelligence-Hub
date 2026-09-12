"""M20 CLI/Web interface contracts."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from valuation_hub import cli_entry
from valuation_hub.debt_binding import build_debt_binding_context, build_debt_date_assertion
from valuation_hub.debt_components import CORE_COMPONENTS, aggregate_interest_bearing_debt
from valuation_hub.web_debt import render_debt_lab


def _hash(v:dict,f:str)->str:
    x=copy.deepcopy(v);x.pop(f,None)
    return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def _cash()->dict:
    x={"schema_version":"financial-observation-v0.1","status":"FINANCIAL_OBSERVATION_NORMALIZED","canonical":False,"class":"NORMALIZED_FACT","metric":"cash","value":777,"unit":"KRW","entity":{"id":"DART_CORP:00126380","source_system":"TEST","financial_scope":"CFS"},"period":{"kind":"INSTANT","start":None,"end":"2026-06-30","duration_days":None,"fiscal_year":2026,"fiscal_period":"H1","fiscal_quarter":2,"report_stage":"H1","date_precision":"EXACT"},"lineage":{"normalization_rule":"TEST","source_candidate_sha256":"a"*64},"observation_sha256":""}
    x['observation_sha256']=_hash(x,'observation_sha256');return x


def _obs(metric:str,value:int)->dict:
    x={"schema_version":"debt-component-observation-v0.1","status":"DEBT_COMPONENT_NORMALIZED","canonical":False,"class":"NORMALIZED_FACT","metric":metric,"value":value,"unit":"KRW","entity":{"id":"DART_CORP:00126380","source_system":"TEST","financial_scope":"CFS"},"period":{"kind":"INSTANT","start":None,"end":None,"duration_days":None,"fiscal_year":2026,"fiscal_period":"H1","fiscal_quarter":2,"report_stage":"H1","date_precision":"REPORT_STAGE_ONLY"},"lineage":{"normalization_rule":"TEST","source_candidate_sha256":"a"*64,"source_class":"FACT","source_snapshot_sha256":"b"*64,"source_body_sha256":"c"*64,"filing_identity":{"id":"test"},"source_detail":{"account_id":metric}},"observation_sha256":""}
    x['observation_sha256']=_hash(x,'observation_sha256');return x


def _debt()->dict:
    return aggregate_interest_bearing_debt([_obs(m,(i+1)*100) for i,m in enumerate(CORE_COMPONENTS)])


def test_cli_dispatch_exposes_m20_commands()->None:
    for command in ('debt-date-assertion-build','debt-date-assertion-validate','debt-binding-context-build','debt-binding-context-validate','binding-build-with-debt'):
        assert cli_entry._command([command])==command


def test_cli_m20_round_trip(tmp_path:Path,capsys)->None:
    debt=_debt(); debt_path=tmp_path/'debt.json';debt_path.write_text(json.dumps(debt))
    assert cli_entry.main(['debt-date-assertion-build',str(debt_path),'--reviewer','human','--approved-at','2026-09-12T19:30:00+09:00','--asserted-period-end','2026-06-30','--review-basis','official filing reviewed'])==0
    assertion=json.loads(capsys.readouterr().out); assertion_path=tmp_path/'assertion.json';assertion_path.write_text(json.dumps(assertion))
    assert cli_entry.main(['debt-binding-context-build',str(debt_path),'--as-of','2026-09-12','--date-assertion',str(assertion_path)])==0
    context=json.loads(capsys.readouterr().out);context_path=tmp_path/'context.json';context_path.write_text(json.dumps(context))
    observations_path=tmp_path/'observations.json';observations_path.write_text(json.dumps([_cash()]))
    assert cli_entry.main(['binding-build-with-debt',str(observations_path),str(context_path),'--as-of','2026-09-12'])==0
    proposal=json.loads(capsys.readouterr().out);proposal_path=tmp_path/'proposal.json';proposal_path.write_text(json.dumps(proposal))
    assert proposal['schema_version']=='draft-binding-proposal-v0.2'
    assert cli_entry.main(['binding-validate',str(proposal_path)])==0
    validated=json.loads(capsys.readouterr().out);assert validated['status']=='PASS_DEBT_AWARE_BINDING_PROPOSAL_VALIDATION'


def test_web_m20_is_calculate_only_and_preserves_m19_contract()->None:
    page=render_debt_lab()
    assert 'LIABILITIES ≠ DEBT · CALCULATE ONLY' in page
    assert '/api/debt/date-assertion-build' in page
    assert '/api/debt/binding-context-build' in page
    assert 'NO DRAFT FILE WRITE' in page
    assert '/api/debt/file-write' not in page
    assert '/api/debt/canonical' not in page
