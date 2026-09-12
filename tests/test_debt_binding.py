"""M20 debt date assertion and binding-context policy tests."""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub.debt_binding import (
    build_debt_binding_context,
    build_debt_date_assertion,
    validate_debt_binding_context,
    validate_debt_date_assertion,
)
from valuation_hub.debt_components import CORE_COMPONENTS, aggregate_interest_bearing_debt


def _sha(value: dict, field: str) -> str:
    x=copy.deepcopy(value);x.pop(field,None)
    return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def _obs(metric:str,value:int,*,klass:str='NORMALIZED_FACT',precision:str='REPORT_STAGE_ONLY',end:str|None=None,entity:str='DART_CORP:00126380',scope:str='CFS',unit:str='KRW')->dict:
    period={"kind":"INSTANT","start":None,"end":end,"duration_days":None,"fiscal_year":2026,"fiscal_period":"H1","fiscal_quarter":2,"report_stage":"H1","date_precision":precision}
    x={"schema_version":"debt-component-observation-v0.1","status":"DEBT_COMPONENT_NORMALIZED","canonical":False,"class":klass,"metric":metric,"value":value,"unit":unit,"entity":{"id":entity,"source_system":"TEST","financial_scope":scope},"period":period,"lineage":{"normalization_rule":"TEST","source_candidate_sha256":"a"*64,"source_class":"FACT" if klass=='NORMALIZED_FACT' else 'FACT_CANDIDATE',"source_snapshot_sha256":"b"*64,"source_body_sha256":"c"*64,"filing_identity":{"id":"test"},"source_detail":{"account_id":metric}},"observation_sha256":""}
    x['observation_sha256']=_sha(x,'observation_sha256');return x


def _debt(*,precision:str='REPORT_STAGE_ONLY',end:str|None=None,klass:str='NORMALIZED_FACT')->dict:
    return aggregate_interest_bearing_debt([_obs(metric,(i+1)*100,klass=klass,precision=precision,end=end) for i,metric in enumerate(CORE_COMPONENTS)])


def test_report_stage_requires_human_assertion_and_locks_source_debt()->None:
    debt=_debt()
    with pytest.raises(CaseServiceError,match='date assertion'):
        build_debt_binding_context(debt,as_of='2026-09-12')
    assertion=build_debt_date_assertion(debt,reviewer='human-reviewer',approved_at='2026-09-12T19:30:00+09:00',asserted_period_end='2026-06-30',review_basis='Official filing statement period-end reviewed by human.')
    assert validate_debt_date_assertion(assertion,debt)['asserted_period_end']=='2026-06-30'
    context=build_debt_binding_context(debt,as_of='2026-09-12',date_assertion=assertion)
    assert context['date_resolution']['method']=='HUMAN_DATE_ASSERTION'
    assert context['freshness']['status']=='FRESH'
    assert context['binding_eligibility']['eligible'] is True
    assert validate_debt_binding_context(context,debt=debt,date_assertion=assertion)['eligible'] is True
    tampered=copy.deepcopy(assertion);tampered['asserted_period_end']='2026-06-29'
    with pytest.raises(CaseServiceError,match='SHA-256'):
        validate_debt_date_assertion(tampered,debt)
    changed=copy.deepcopy(debt);changed['known_component_sum']+=1
    with pytest.raises(CaseServiceError):
        validate_debt_date_assertion(assertion,changed)


def test_exact_debt_uses_source_date_and_rejects_override()->None:
    debt=_debt(precision='EXACT',end='2026-06-30')
    context=build_debt_binding_context(debt,as_of='2026-09-12')
    assert context['date_resolution']=={'method':'SOURCE_EXACT','date_assertion_sha256':None}
    assert context['resolved_period_end']=='2026-06-30'
    fake={"schema_version":"debt-date-assertion-v0.1"}
    with pytest.raises(CaseServiceError,match='must not be overridden'):
        build_debt_binding_context(debt,as_of='2026-09-12',date_assertion=fake)


def test_stale_complete_debt_is_not_binding_eligible()->None:
    debt=_debt(precision='EXACT',end='2024-01-01')
    context=build_debt_binding_context(debt,as_of='2026-09-12',max_age_days=550)
    assert context['freshness']['status']=='STALE_BLOCKED'
    assert context['binding_eligibility']=={'eligible':False,'reason':'STALE_DEBT'}


def test_candidate_or_partial_debt_cannot_enter_binding_context()->None:
    candidate=_debt(klass='NORMALIZED_FACT_CANDIDATE')
    assertion=build_debt_date_assertion(candidate,reviewer='human',approved_at='2026-09-12T19:30:00+09:00',asserted_period_end='2026-06-30',review_basis='review')
    with pytest.raises(CaseServiceError,match='complete reviewed'):
        build_debt_binding_context(candidate,as_of='2026-09-12',date_assertion=assertion)
    partial=aggregate_interest_bearing_debt([_obs(metric,(i+1)*100) for i,metric in enumerate(CORE_COMPONENTS[:-1])])
    assertion2=build_debt_date_assertion(partial,reviewer='human',approved_at='2026-09-12T19:30:00+09:00',asserted_period_end='2026-06-30',review_basis='review')
    with pytest.raises(CaseServiceError,match='complete reviewed'):
        build_debt_binding_context(partial,as_of='2026-09-12',date_assertion=assertion2)


def test_context_tamper_detected()->None:
    debt=_debt(precision='EXACT',end='2026-06-30')
    context=build_debt_binding_context(debt,as_of='2026-09-12')
    tampered=copy.deepcopy(context);tampered['value']+=1
    with pytest.raises(CaseServiceError,match='SHA-256'):
        validate_debt_binding_context(tampered)
