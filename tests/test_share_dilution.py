"""M21 governed historical share-dilution tests."""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub.sec_live import METRIC_SPECS, TransportResponse, capture_companyfacts_snapshot
from valuation_hub.share_dilution import (
    derive_historical_dilution,
    extract_sec_dilution_candidate,
    normalize_share_dilution_candidate,
    validate_historical_dilution,
    validate_share_dilution_candidate,
    validate_share_dilution_observation,
)

FETCHED_AT="2026-09-12T10:40:00+00:00"


def _payload()->dict:
    return {
        "cik":1234567,"entityName":"Dilution Fixture Inc.",
        "facts":{"us-gaap":{
            "WeightedAverageNumberOfSharesOutstandingBasic":{"units":{"shares":[
                {"start":"2026-04-01","end":"2026-06-30","val":100,"accn":"0001234567-26-000030","fy":2026,"fp":"Q2","form":"10-Q","filed":"2026-08-05","frame":"CY2026Q2"},
                {"start":"2026-01-01","end":"2026-06-30","val":98,"accn":"0001234567-26-000030","fy":2026,"fp":"Q2","form":"10-Q","filed":"2026-08-05"}
            ]}},
            "WeightedAverageNumberOfDilutedSharesOutstanding":{"units":{"shares":[
                {"start":"2026-04-01","end":"2026-06-30","val":110,"accn":"0001234567-26-000030","fy":2026,"fp":"Q2","form":"10-Q","filed":"2026-08-05","frame":"CY2026Q2"},
                {"start":"2026-01-01","end":"2026-06-30","val":108,"accn":"0001234567-26-000030","fy":2026,"fp":"Q2","form":"10-Q","filed":"2026-08-05"}
            ]}}
        }}
    }


def _snapshot()->dict:
    body=json.dumps(_payload(),separators=(',',':')).encode()
    def transport(locator:str,*,user_agent:str)->TransportResponse:
        return TransportResponse(status=200,content_type='application/json',body=body,final_locator=locator)
    return capture_companyfacts_snapshot('1234567',user_agent='Valuation-Intelligence-Hub test@example.com',transport=transport,fetched_at=FETCHED_AT)


def _reviewed(candidate:dict)->dict:
    c=copy.deepcopy(candidate);c['class']='FACT'
    x=copy.deepcopy(c);x.pop('candidate_sha256',None)
    c['candidate_sha256']=hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    validate_share_dilution_candidate(c);return c


def test_m21_does_not_mutate_m13_sec_registry()->None:
    assert set(METRIC_SPECS)=={'revenue','operating_income','net_income','assets','cash','shares_outstanding'}


def test_exact_start_end_prevents_quarter_ytd_conflation()->None:
    snap=_snapshot()
    q=extract_sec_dilution_candidate(snap,'weighted_average_basic_shares',period_start='2026-04-01',period_end='2026-06-30',form='10-Q')
    y=extract_sec_dilution_candidate(snap,'weighted_average_basic_shares',period_start='2026-01-01',period_end='2026-06-30',form='10-Q')
    assert q['value']==100 and y['value']==98
    qobs=normalize_share_dilution_candidate(q);yobs=normalize_share_dilution_candidate(y)
    assert qobs['period']['kind']=='DURATION_QUARTER'
    assert yobs['period']['kind']=='DURATION_YTD'
    assert validate_share_dilution_observation(qobs)['canonical'] is False


def test_reviewed_same_period_derives_historical_dilution_only()->None:
    snap=_snapshot()
    basic=normalize_share_dilution_candidate(_reviewed(extract_sec_dilution_candidate(snap,'weighted_average_basic_shares',period_start='2026-04-01',period_end='2026-06-30',form='10-Q')))
    diluted=normalize_share_dilution_candidate(_reviewed(extract_sec_dilution_candidate(snap,'weighted_average_diluted_shares',period_start='2026-04-01',period_end='2026-06-30',form='10-Q')))
    result=derive_historical_dilution(basic,diluted)
    assert result['class']=='DERIVED_FACT'
    assert result['historical_dilution_factor']==pytest.approx(1.1)
    assert result['historical_incremental_diluted_shares']==10
    assert result['semantic_boundary']['valuation_date_direct_bind'] is False
    assert result['semantic_boundary']['forecast_direct_bind'] is False
    assert result['semantic_boundary']['shares_outstanding_substitution'] is False
    assert validate_historical_dilution(result)['status']=='PASS_HISTORICAL_DILUTION_VALIDATION'


def test_candidate_authority_propagates_without_upgrade()->None:
    snap=_snapshot()
    basic=normalize_share_dilution_candidate(extract_sec_dilution_candidate(snap,'weighted_average_basic_shares',period_start='2026-04-01',period_end='2026-06-30'))
    diluted=normalize_share_dilution_candidate(extract_sec_dilution_candidate(snap,'weighted_average_diluted_shares',period_start='2026-04-01',period_end='2026-06-30'))
    assert derive_historical_dilution(basic,diluted)['class']=='DERIVED_FACT_CANDIDATE'


def test_period_mismatch_and_negative_dilution_fail_closed()->None:
    snap=_snapshot()
    b=normalize_share_dilution_candidate(_reviewed(extract_sec_dilution_candidate(snap,'weighted_average_basic_shares',period_start='2026-04-01',period_end='2026-06-30')))
    dytd=normalize_share_dilution_candidate(_reviewed(extract_sec_dilution_candidate(snap,'weighted_average_diluted_shares',period_start='2026-01-01',period_end='2026-06-30')))
    with pytest.raises(CaseServiceError,match='period mismatch'):
        derive_historical_dilution(b,dytd)
    d=normalize_share_dilution_candidate(_reviewed(extract_sec_dilution_candidate(snap,'weighted_average_diluted_shares',period_start='2026-04-01',period_end='2026-06-30')))
    d=copy.deepcopy(d);d['value']=90
    x=copy.deepcopy(d);x.pop('observation_sha256',None)
    d['observation_sha256']=hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    with pytest.raises(CaseServiceError,match='below basic'):
        derive_historical_dilution(b,d)


def test_derived_arithmetic_and_boundary_are_recomputed_not_hash_only()->None:
    snap=_snapshot();b=normalize_share_dilution_candidate(_reviewed(extract_sec_dilution_candidate(snap,'weighted_average_basic_shares',period_start='2026-04-01',period_end='2026-06-30')));d=normalize_share_dilution_candidate(_reviewed(extract_sec_dilution_candidate(snap,'weighted_average_diluted_shares',period_start='2026-04-01',period_end='2026-06-30')))
    result=derive_historical_dilution(b,d)
    tampered=copy.deepcopy(result);tampered['historical_dilution_factor']=9.9
    x=copy.deepcopy(tampered);x.pop('derived_sha256',None)
    tampered['derived_sha256']=hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    with pytest.raises(CaseServiceError,match='arithmetic'):
        validate_historical_dilution(tampered)
