"""M24 re-signing and nested validation hardening tests."""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_binding import build_binding_proposal
from valuation_hub.wacc_assumption import (
    DEBT_MARKET_VALUE,EQUITY_MARKET_VALUE,EQUITY_RISK_PREMIUM,LEVERED_BETA,PRE_TAX_COST_OF_DEBT,RISK_FREE_RATE,TAX_RATE,
    build_wacc_candidate,build_wacc_review_assertion,build_wacc_source_input,finalize_reviewed_wacc,validate_wacc_candidate,
)
from valuation_hub.wacc_draft_binding import build_binding_proposal_with_wacc,validate_binding_proposal_v4


def _resign(obj:dict,field:str)->dict:
    x=copy.deepcopy(obj);x.pop(field,None)
    obj[field]=hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest();return obj


def _src(metric:str,value:float,unit:str,date:str)->dict:
    return build_wacc_source_input(metric=metric,value=value,unit=unit,observed_on=date,claim_class='ASSUMPTION' if metric in {EQUITY_RISK_PREMIUM,LEVERED_BETA,PRE_TAX_COST_OF_DEBT,TAX_RATE} else 'FACT',source_publisher='test',source_type='TEST',source_tier='B',source_locator=f'test://{metric}',source_sha256=hashlib.sha256(metric.encode()).hexdigest())


def _candidate()->dict:
    inputs=[_src(RISK_FREE_RATE,.04,'decimal','2026-09-01'),_src(EQUITY_RISK_PREMIUM,.05,'decimal','2026-09-01'),_src(LEVERED_BETA,1.1,'ratio','2026-08-01'),_src(PRE_TAX_COST_OF_DEBT,.05,'decimal','2026-08-01'),_src(EQUITY_MARKET_VALUE,1000,'KRW','2026-09-01'),_src(DEBT_MARKET_VALUE,200,'KRW','2026-06-30'),_src(TAX_RATE,.25,'decimal','2026-06-30')]
    return build_wacc_candidate(inputs,entity_id='DART_CORP:00126380',financial_scope='CFS',capital_currency='KRW',as_of='2026-09-12',scenario_names=['BASE'])


def _package()->dict:
    c=_candidate();a=build_wacc_review_assertion(c,reviewer='human',approved_at='2026-09-12T21:00:00+09:00',review_basis='reviewed');return finalize_reviewed_wacc(c,a)


def _cash()->dict:
    x={"schema_version":"financial-observation-v0.1","status":"FINANCIAL_OBSERVATION_NORMALIZED","canonical":False,"class":"NORMALIZED_FACT","metric":"cash","value":100.0,"unit":"KRW","entity":{"id":"DART_CORP:00126380","source_system":"TEST","financial_scope":"CFS"},"period":{"kind":"INSTANT","start":None,"end":"2026-06-30","duration_days":None,"fiscal_year":2026,"fiscal_period":"H1","fiscal_quarter":2,"report_stage":"H1","date_precision":"EXACT"},"lineage":{"normalization_rule":"TEST","source_candidate_sha256":"a"*64},"observation_sha256":""};return _resign(x,'observation_sha256')


def test_candidate_missing_calculation_field_fails_even_after_outer_resign()->None:
    c=_candidate();c['calculation'].pop('weight_debt');_resign(c,'candidate_sha256')
    with pytest.raises(CaseServiceError,match='calculation|계산'):
        validate_wacc_candidate(c)


def test_candidate_nonfinite_calculation_fails_closed()->None:
    c=_candidate();c['calculation']['wacc']=float('nan')
    with pytest.raises(CaseServiceError):validate_wacc_candidate(c)


def test_v04_policy_tamper_fails_even_after_outer_resign()->None:
    base=build_binding_proposal([_cash()],as_of='2026-09-12');p=build_binding_proposal_with_wacc(base,_package())
    p['policy']['direct_bind_requires']=['REVIEWED_ASSUMPTION'];_resign(p,'proposal_sha256')
    with pytest.raises(CaseServiceError,match='policy|정책'):
        validate_binding_proposal_v4(p)
