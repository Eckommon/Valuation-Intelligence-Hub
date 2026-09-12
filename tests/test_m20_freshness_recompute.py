"""M20 debt-context freshness must be semantically recomputable, not hash-only."""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub.debt_binding import build_debt_binding_context, validate_debt_binding_context
from valuation_hub.debt_components import CORE_COMPONENTS, aggregate_interest_bearing_debt


def _hash(value:dict,field:str)->str:
    x=copy.deepcopy(value);x.pop(field,None)
    return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def _obs(metric:str,value:int)->dict:
    x={"schema_version":"debt-component-observation-v0.1","status":"DEBT_COMPONENT_NORMALIZED","canonical":False,"class":"NORMALIZED_FACT","metric":metric,"value":value,"unit":"KRW","entity":{"id":"DART_CORP:00126380","source_system":"TEST","financial_scope":"CFS"},"period":{"kind":"INSTANT","start":None,"end":"2026-06-30","duration_days":None,"fiscal_year":2026,"fiscal_period":"H1","fiscal_quarter":2,"report_stage":"H1","date_precision":"EXACT"},"lineage":{"normalization_rule":"TEST","source_candidate_sha256":"a"*64,"source_class":"FACT","source_snapshot_sha256":"b"*64,"source_body_sha256":"c"*64,"filing_identity":{"id":"test"},"source_detail":{"account_id":metric}},"observation_sha256":""}
    x['observation_sha256']=_hash(x,'observation_sha256');return x


def test_standalone_validator_recomputes_freshness_even_if_hash_is_resealed()->None:
    debt=aggregate_interest_bearing_debt([_obs(m,(i+1)*100) for i,m in enumerate(CORE_COMPONENTS)])
    context=build_debt_binding_context(debt,as_of='2026-09-12',max_age_days=550)
    tampered=copy.deepcopy(context)
    tampered['freshness']['age_days']=1
    tampered['context_sha256']=_hash(tampered,'context_sha256')
    with pytest.raises(CaseServiceError,match='recomputation'):
        validate_debt_binding_context(tampered)


def test_proposal_policy_cannot_reuse_context_built_for_different_as_of()->None:
    debt=aggregate_interest_bearing_debt([_obs(m,(i+1)*100) for i,m in enumerate(CORE_COMPONENTS)])
    context=build_debt_binding_context(debt,as_of='2026-09-11',max_age_days=550)
    assert context['policy']=={'version':'DEBT_BINDING_CONTEXT_V01','as_of':'2026-09-11','max_age_days':550}
