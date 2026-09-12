"""M24 governed WACC assumption + Draft binding tests."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from valuation_hub.binding_apply import apply_binding_approval, build_binding_approval, validate_bound_draft_result
from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_binding import build_binding_proposal
from valuation_hub.wacc_assumption import (
    DEBT_MARKET_VALUE,
    EQUITY_MARKET_VALUE,
    EQUITY_RISK_PREMIUM,
    LEVERED_BETA,
    PRE_TAX_COST_OF_DEBT,
    RISK_FREE_RATE,
    TAX_RATE,
    build_wacc_candidate,
    build_wacc_review_assertion,
    build_wacc_source_input,
    finalize_reviewed_wacc,
    validate_reviewed_wacc,
    validate_wacc_candidate,
)
from valuation_hub.wacc_draft_binding import build_binding_proposal_with_wacc, validate_binding_proposal_v4

ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=ROOT/'templates'/'draft_equity_fcff.json'


def _hash(v:dict,f:str)->str:
    x=copy.deepcopy(v);x.pop(f,None)
    return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def _cash()->dict:
    x={"schema_version":"financial-observation-v0.1","status":"FINANCIAL_OBSERVATION_NORMALIZED","canonical":False,"class":"NORMALIZED_FACT","metric":"cash","value":777.0,"unit":"KRW","entity":{"id":"DART_CORP:00126380","source_system":"TEST","financial_scope":"CFS"},"period":{"kind":"INSTANT","start":None,"end":"2026-06-30","duration_days":None,"fiscal_year":2026,"fiscal_period":"H1","fiscal_quarter":2,"report_stage":"H1","date_precision":"EXACT"},"lineage":{"normalization_rule":"TEST","source_candidate_sha256":"a"*64},"observation_sha256":""}
    x['observation_sha256']=_hash(x,'observation_sha256');return x


def _src(metric:str,value:float,unit:str,observed_on:str,*,tier:str='B',claim:str='FACT')->dict:
    return build_wacc_source_input(metric=metric,value=value,unit=unit,observed_on=observed_on,claim_class=claim,source_publisher=f'{metric} publisher',source_type='TEST_SOURCE',source_tier=tier,source_locator=f'test://{metric}',source_sha256=hashlib.sha256(metric.encode()).hexdigest())


def _inputs(*,stale_rf:bool=False,tier_d_beta:bool=False)->list[dict]:
    return [
        _src(RISK_FREE_RATE,0.0436,'decimal','2025-01-01' if stale_rf else '2026-09-01',tier='A'),
        _src(EQUITY_RISK_PREMIUM,0.0418,'decimal','2026-09-01',tier='B',claim='ASSUMPTION'),
        _src(LEVERED_BETA,1.2,'ratio','2026-08-01',tier='D' if tier_d_beta else 'B',claim='ASSUMPTION'),
        _src(PRE_TAX_COST_OF_DEBT,0.05,'decimal','2026-08-01',tier='B',claim='ASSUMPTION'),
        _src(EQUITY_MARKET_VALUE,1000.0,'KRW','2026-09-01',tier='B'),
        _src(DEBT_MARKET_VALUE,200.0,'KRW','2026-06-30',tier='A'),
        _src(TAX_RATE,0.25,'decimal','2026-06-30',tier='A',claim='ASSUMPTION'),
    ]


def _candidate(*,stale_rf:bool=False,tier_d_beta:bool=False,scenarios:list[str]|None=None)->dict:
    return build_wacc_candidate(_inputs(stale_rf=stale_rf,tier_d_beta=tier_d_beta),entity_id='DART_CORP:00126380',financial_scope='CFS',capital_currency='KRW',as_of='2026-09-12',scenario_names=scenarios or ['BASE'])


def _package(*,scenarios:list[str]|None=None)->dict:
    candidate=_candidate(scenarios=scenarios)
    assertion=build_wacc_review_assertion(candidate,reviewer='human-reviewer',approved_at='2026-09-12T21:15:00+09:00',review_basis='Reviewed source dates, source tiers, CAPM methodology, capital weights, tax treatment, and scenario targets.')
    return finalize_reviewed_wacc(candidate,assertion)


def _draft()->dict:
    d=json.loads(TEMPLATE.read_text(encoding='utf-8'));d['currency']='KRW';d['name']='M24 WACC integration';return d


def _decision(p:dict,field:str)->dict:
    return next(x for x in p['draft_input_matrix'] if x['field']==field)


def test_wacc_candidate_recomputes_capm_weights_and_wacc()->None:
    candidate=_candidate()
    c=candidate['calculation']
    assert c['cost_of_equity']==pytest.approx(0.0436+1.2*0.0418)
    assert c['after_tax_cost_of_debt']==pytest.approx(0.05*(1-0.25))
    assert c['weight_equity']==pytest.approx(1000/1200)
    assert c['weight_debt']==pytest.approx(200/1200)
    assert c['weight_equity']+c['weight_debt']==pytest.approx(1.0)
    assert c['wacc']==pytest.approx((1000/1200)*(0.0436+1.2*0.0418)+(200/1200)*(0.05*0.75))
    assert candidate['class']=='ASSUMPTION_CANDIDATE'
    assert validate_wacc_candidate(candidate)['eligible_for_human_review'] is True


def test_stale_or_tier_d_input_cannot_be_human_reviewed()->None:
    stale=_candidate(stale_rf=True)
    assert stale['review_readiness']['eligible_for_human_review'] is False
    with pytest.raises(CaseServiceError,match='eligible'):
        build_wacc_review_assertion(stale,reviewer='human',approved_at='2026-09-12T21:15:00+09:00',review_basis='review')
    tier_d=_candidate(tier_d_beta=True)
    assert tier_d['review_readiness']['all_source_tiers_reviewable'] is False
    with pytest.raises(CaseServiceError,match='eligible'):
        build_wacc_review_assertion(tier_d,reviewer='human',approved_at='2026-09-12T21:15:00+09:00',review_basis='review')


def test_reviewed_package_is_assumption_not_fact_and_nested_tamper_fails()->None:
    package=_package()
    checked=validate_reviewed_wacc(package)
    assert package['class']=='ASSUMPTION'
    assert checked['eligible'] is True
    tampered=copy.deepcopy(package)
    tampered['candidate']['calculation']['wacc']+=0.01
    x=copy.deepcopy(tampered);x.pop('package_sha256',None)
    tampered['package_sha256']=hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    with pytest.raises(CaseServiceError):
        validate_reviewed_wacc(tampered)


def test_v04_replaces_only_scenario_wacc_and_preserves_base_decisions()->None:
    base=build_binding_proposal([_cash()],as_of='2026-09-12')
    proposal=build_binding_proposal_with_wacc(base,_package())
    checked=validate_binding_proposal_v4(proposal)
    assert proposal['schema_version']=='draft-binding-proposal-v0.4'
    assert _decision(proposal,'scenario.wacc')['state']=='DIRECT_BIND'
    base_by={x['field']:x for x in base['draft_input_matrix']};by={x['field']:x for x in proposal['draft_input_matrix']}
    for field in base_by:
        if field!='scenario.wacc': assert by[field]==base_by[field]
    assert checked['direct_bind_count']==base['completeness']['direct_bind_count']+1


def test_wacc_approval_apply_updates_all_exact_target_scenarios_and_keeps_input_draft_immutable()->None:
    base=build_binding_proposal([_cash()],as_of='2026-09-12')
    package=_package();proposal=build_binding_proposal_with_wacc(base,package)
    draft=_draft();before=copy.deepcopy(draft)
    approval=build_binding_approval(proposal,draft,reviewer='human-approver',target_entity_id='DART_CORP:00126380',target_financial_scope='CFS',approved_fields=['scenario.wacc'],approved_at='2026-09-12T21:20:00+09:00')
    result=apply_binding_approval(proposal,draft,approval)
    assert draft==before
    assert result['draft_after']['equity']['scenarios']['BASE']['wacc']==pytest.approx(package['wacc'])
    diff=result['applied_diffs'][0]
    assert diff['field']=='scenario.wacc'
    assert diff['before']=={'BASE':0.10}
    assert diff['after']=={'BASE':pytest.approx(package['wacc'])}
    assert diff['source_package_sha256']==package['package_sha256']
    assert diff['review_assertion_sha256']==package['review_assertion']['assertion_sha256']
    assert diff['scenario_names']==['BASE']
    assert validate_bound_draft_result(result)['applied_field_count']==1


def test_wacc_approval_fails_when_package_targets_do_not_equal_draft_scenarios()->None:
    base=build_binding_proposal([_cash()],as_of='2026-09-12')
    proposal=build_binding_proposal_with_wacc(base,_package(scenarios=['BASE']))
    draft=_draft();draft['equity']['scenarios']['BULL']=copy.deepcopy(draft['equity']['scenarios']['BASE'])
    with pytest.raises(CaseServiceError,match='scenario target set|시나리오'):
        build_binding_approval(proposal,draft,reviewer='human',target_entity_id='DART_CORP:00126380',target_financial_scope='CFS',approved_fields=['scenario.wacc'],approved_at='2026-09-12T21:20:00+09:00')


def test_v04_identity_currency_and_asof_mismatch_fail_closed()->None:
    base=build_binding_proposal([_cash()],as_of='2026-09-12')
    p=_package();bad=copy.deepcopy(p);bad['entity']['id']='OTHER'
    x=copy.deepcopy(bad);x.pop('package_sha256',None);bad['package_sha256']=hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    with pytest.raises(CaseServiceError):build_binding_proposal_with_wacc(base,bad)
    candidate=build_wacc_candidate(_inputs(),entity_id='DART_CORP:00126380',financial_scope='CFS',capital_currency='KRW',as_of='2026-09-11',scenario_names=['BASE'])
    assertion=build_wacc_review_assertion(candidate,reviewer='human',approved_at='2026-09-12T21:15:00+09:00',review_basis='review')
    package=finalize_reviewed_wacc(candidate,assertion)
    with pytest.raises(CaseServiceError,match='as_of'):
        build_binding_proposal_with_wacc(base,package)
