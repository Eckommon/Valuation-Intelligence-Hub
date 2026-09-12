"""M20 debt-aware M16/M17 integration tests."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from valuation_hub.binding_apply import build_binding_approval, apply_binding_approval, validate_bound_draft_result
from valuation_hub.case_service import CaseServiceError
from valuation_hub.debt_binding import build_debt_binding_context, build_debt_date_assertion
from valuation_hub.debt_components import CORE_COMPONENTS, aggregate_interest_bearing_debt
from valuation_hub.debt_draft_binding import build_binding_proposal_with_debt, validate_binding_proposal_v2
from valuation_hub.draft_binding import build_binding_proposal

ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=ROOT/'templates'/'draft_equity_fcff.json'


def _hash(v:dict,f:str)->str:
    x=copy.deepcopy(v);x.pop(f,None)
    return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def _cash()->dict:
    x={"schema_version":"financial-observation-v0.1","status":"FINANCIAL_OBSERVATION_NORMALIZED","canonical":False,"class":"NORMALIZED_FACT","metric":"cash","value":777,"unit":"KRW","entity":{"id":"DART_CORP:00126380","source_system":"TEST","financial_scope":"CFS"},"period":{"kind":"INSTANT","start":None,"end":"2026-06-30","duration_days":None,"fiscal_year":2026,"fiscal_period":"H1","fiscal_quarter":2,"report_stage":"H1","date_precision":"EXACT"},"lineage":{"normalization_rule":"TEST","source_candidate_sha256":"a"*64},"observation_sha256":""}
    x['observation_sha256']=_hash(x,'observation_sha256');return x


def _debt_obs(metric:str,value:int,*,precision:str='REPORT_STAGE_ONLY',end:str|None=None,entity:str='DART_CORP:00126380',scope:str='CFS',unit:str='KRW')->dict:
    x={"schema_version":"debt-component-observation-v0.1","status":"DEBT_COMPONENT_NORMALIZED","canonical":False,"class":"NORMALIZED_FACT","metric":metric,"value":value,"unit":unit,"entity":{"id":entity,"source_system":"TEST","financial_scope":scope},"period":{"kind":"INSTANT","start":None,"end":end,"duration_days":None,"fiscal_year":2026,"fiscal_period":"H1","fiscal_quarter":2,"report_stage":"H1","date_precision":precision},"lineage":{"normalization_rule":"TEST","source_candidate_sha256":"a"*64,"source_class":"FACT","source_snapshot_sha256":"b"*64,"source_body_sha256":"c"*64,"filing_identity":{"id":"test"},"source_detail":{"account_id":metric}},"observation_sha256":""}
    x['observation_sha256']=_hash(x,'observation_sha256');return x


def _debt(*,precision:str='REPORT_STAGE_ONLY',end:str|None=None,entity:str='DART_CORP:00126380',scope:str='CFS',unit:str='KRW')->dict:
    return aggregate_interest_bearing_debt([_debt_obs(m,(i+1)*100,precision=precision,end=end,entity=entity,scope=scope,unit=unit) for i,m in enumerate(CORE_COMPONENTS)])


def _context(*,stale:bool=False)->tuple[dict,dict|None]:
    if stale:
        debt=_debt(precision='EXACT',end='2024-01-01')
        return build_debt_binding_context(debt,as_of='2026-09-12',max_age_days=550),None
    debt=_debt()
    assertion=build_debt_date_assertion(debt,reviewer='human',approved_at='2026-09-12T19:30:00+09:00',asserted_period_end='2026-06-30',review_basis='Official filing statement date reviewed.')
    return build_debt_binding_context(debt,as_of='2026-09-12',date_assertion=assertion),assertion


def _draft()->dict:
    d=json.loads(TEMPLATE.read_text(encoding='utf-8'));d['currency']='KRW';d['name']='M20 debt integration';return d


def test_original_v01_builder_remains_cash_only_semantics()->None:
    proposal=build_binding_proposal([_cash()],as_of='2026-09-12')
    assert proposal['schema_version']=='draft-binding-proposal-v0.1'
    by={x['field']:x for x in proposal['draft_input_matrix']}
    assert by['equity.cash']['state']=='DIRECT_BIND'
    assert by['equity.debt']['state']=='MISSING_REQUIRED'


def test_debt_aware_v02_direct_binds_fresh_complete_reviewed_debt()->None:
    context,assertion=_context()
    proposal=build_binding_proposal_with_debt([_cash()],context,as_of='2026-09-12')
    checked=validate_binding_proposal_v2(proposal)
    assert proposal['schema_version']=='draft-binding-proposal-v0.2'
    by={x['field']:x for x in proposal['draft_input_matrix']}
    assert by['equity.debt']['state']=='DIRECT_BIND'
    assert by['equity.cash']['state']=='DIRECT_BIND'
    assert proposal['debt_binding_context']==context
    assert by['equity.debt']['date_assertion_sha256']==assertion['assertion_sha256']
    assert checked['direct_bind_count']==2


def test_m17_approval_can_apply_debt_with_full_lineage_and_no_input_mutation()->None:
    context,assertion=_context();proposal=build_binding_proposal_with_debt([_cash()],context,as_of='2026-09-12');draft=_draft();before=copy.deepcopy(draft)
    approval=build_binding_approval(proposal,draft,reviewer='human',target_entity_id='DART_CORP:00126380',target_financial_scope='CFS',approved_fields=['equity.debt'],approved_at='2026-09-12T19:35:00+09:00')
    result=apply_binding_approval(proposal,draft,approval)
    assert draft==before
    assert result['draft_after']['equity']['debt']==1500
    assert result['draft_after']['equity']['cash']==before['equity']['cash']
    diff=result['applied_diffs'][0]
    assert diff['field']=='equity.debt'
    assert diff['source_context_sha256']==context['context_sha256']
    assert diff['source_debt_sha256']==context['source_debt_sha256']
    assert diff['date_assertion_sha256']==assertion['assertion_sha256']
    assert validate_bound_draft_result(result)['applied_field_count']==1


def test_stale_debt_cannot_be_approved()->None:
    context,_=_context(stale=True);proposal=build_binding_proposal_with_debt([_cash()],context,as_of='2026-09-12')
    by={x['field']:x for x in proposal['draft_input_matrix']};assert by['equity.debt']['state']=='STALE_BLOCKED'
    with pytest.raises(CaseServiceError,match='DIRECT_BIND'):
        build_binding_approval(proposal,_draft(),reviewer='human',target_entity_id='DART_CORP:00126380',target_financial_scope='CFS',approved_fields=['equity.debt'],approved_at='2026-09-12T19:35:00+09:00')


def test_debt_context_identity_or_unit_mismatch_fails_closed()->None:
    other=_debt(entity='DART_CORP:99999999');assertion=build_debt_date_assertion(other,reviewer='human',approved_at='2026-09-12T19:30:00+09:00',asserted_period_end='2026-06-30',review_basis='review');context=build_debt_binding_context(other,as_of='2026-09-12',date_assertion=assertion)
    with pytest.raises(CaseServiceError,match='entity/scope'):
        build_binding_proposal_with_debt([_cash()],context,as_of='2026-09-12')
    usd=_debt(unit='USD');assertion2=build_debt_date_assertion(usd,reviewer='human',approved_at='2026-09-12T19:30:00+09:00',asserted_period_end='2026-06-30',review_basis='review');context2=build_debt_binding_context(usd,as_of='2026-09-12',date_assertion=assertion2)
    with pytest.raises(CaseServiceError,match='unit mismatch'):
        build_binding_proposal_with_debt([_cash()],context2,as_of='2026-09-12')


def test_v02_tamper_is_detected()->None:
    context,_=_context();proposal=build_binding_proposal_with_debt([_cash()],context,as_of='2026-09-12')
    tampered=copy.deepcopy(proposal);tampered['debt_binding_context']['value']+=1
    with pytest.raises(CaseServiceError):
        validate_binding_proposal_v2(tampered)
