"""M30-R8M24-BETA.Y independent Yahoo v8 original JSON proof regression."""
from __future__ import annotations

import copy
import json
import math
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import pytest

from valuation_hub import ingr_wacc_yahoo_chart_beta as beta
from valuation_hub import ingr_r8_m24_readiness as readiness
from valuation_hub.case_service import CaseServiceError


def _make_json(symbol:str, is_index:bool=False)->str:
    dates=[]
    closes=[]
    d=date.fromisoformat("2023-09-14")
    price=4100.0 if is_index else 105.0
    index=0
    while d<=date.fromisoformat("2026-09-14"):
        if d.weekday()<5:
            delta=0.0002+0.0035*math.sin(index*.19)+0.0015*math.cos(index*.38)
            delta = delta if is_index else .8*delta+0.001*math.sin(index*.11)
            price*=1+delta
            dates.append(int(datetime(d.year,d.month,d.day,16,tzinfo=timezone.utc).timestamp()))
            closes.append(round(price,8))
            index+=1
        d+=timedelta(days=1)
    return json.dumps({"chart":{"result":[{
        "meta":{"symbol":symbol,"currency":"USD","instrumentType":
                "INDEX" if is_index else "EQUITY"},
        "timestamp":dates,
        "indicators":{"quote":[{"close":closes}],"adjclose":[{"adjclose":closes}]},
        "events":{},
    }],"error":None}},separators=(",",":"))


ISSUER=_make_json("INGR")
MARKET=_make_json("^GSPC",True)


def test_yahoo_original_json_price_only_model_and_no_authority():
    val=beta.calculate_yahoo_beta(ISSUER,MARKET)
    assert val["weekly_returns"]>=125
    assert val["last_return"]=="2026-09-14"
    assert 0.65<val["regression_beta"]<0.95
    assert val["dividends_included"] is False
    assert val["historical_source_availability_asof_proven"] is False
    assert val["vendor_api_official_or_supported"] is False
    assert val["claim_class"]=="ASSUMPTION"


def test_proof_tied_to_two_original_json_and_wacc_readiness():
    val=beta.build_yahoo_beta_source(ISSUER,MARKET,captured_at="2026-10-16T00:00:00+00:00")
    i,m,w,p=[val[x] for x in ("issuer_snapshot","market_snapshot","wacc_input","proof")]
    assert w["metric"]=="levered_beta" and w["unit"]=="ratio"
    assert w["claim_class"]=="ASSUMPTION"
    assert p["status"]=="UNREVIEWED_ORIGINAL_YAHOO_PRICE_ONLY_INGR_BETA"
    checked=beta.validate_yahoo_beta_proof(p,w,i,m)
    assert checked["status"]=="PASS_YAHOO_ORIGINAL_TWO_SOURCE_PRICE_ONLY_BETA"
    rows=readiness._rows([w],[i,m],[],[],[],[],[p])
    assert rows[2]["status"]=="FRESH_SOURCE_INPUT_CANDIDATE"
    assert rows[2]["provenance"]["beta_method"]["provider"]=="Yahoo v8 chart original JSON"
    assert rows[2]["provenance"]["beta_method"]["historical_availability_asof_proven"] is False
    assert rows[2]["provenance"]["beta_method"]["regression_quality"]["threshold_semantics"] == "INTERNAL_NON_BLOCKING_REVIEW_TRIAGE_NOT_STATISTICAL_SIGNIFICANCE"
    assert rows[2]["provenance"]["beta_method"]["regression_quality"]["beta_source_candidate_not_reviewed_wacc"] is True
    assert readiness._rows([w],[i,m])[2]["status"]=="BETA_TWO_SOURCE_PRICE_REGRESSION_PROOF_MISSING"
    assert readiness._rows([w],[i],[],[],[],[],[p])[2]["status"]=="BETA_ORIGINAL_ISSUER_OR_MARKET_SNAPSHOT_MISSING"
    tampered=copy.deepcopy(p)
    tampered["method"]["regression_beta"]+=.05
    with pytest.raises(CaseServiceError):
        beta.validate_yahoo_beta_proof(tampered,w,i,m)
    spoofed=copy.deepcopy(m)
    spoofed["source"]["locator"]="https://another.example/yahoo"
    with pytest.raises(CaseServiceError):
        beta.validate_yahoo_beta_proof(p,w,i,spoofed)


@pytest.mark.parametrize("invalid",[
    "<!DOCTYPE html><html><script>challenge()</script></html>",
    json.dumps({"chart":{"error":{"code":"Unauthorized"},"result":None}}),
    json.dumps({"error":"429 Too Many Requests"}),
    ISSUER.replace('"symbol":"INGR"','"symbol":"WRONG"'),
    ISSUER.replace('"currency":"USD"','"currency":"EUR"'),
    ISSUER.replace('"close":[','"close":[],"wrong":['),
])
def test_yahoo_challenge_bad_schema_and_wrong_symbol_rejected(invalid):
    with pytest.raises(CaseServiceError):
        beta.calculate_yahoo_beta(invalid,MARKET)


def test_absent_final_date_and_future_date_rejected():
    payload=json.loads(ISSUER)
    r=payload["chart"]["result"][0]
    r["timestamp"].pop()
    r["indicators"]["quote"][0]["close"].pop()
    with pytest.raises(CaseServiceError):
        beta.calculate_yahoo_beta(json.dumps(payload),MARKET)
    payload=json.loads(ISSUER)
    r=payload["chart"]["result"][0]
    r["timestamp"].append(int(datetime(2026,9,15,16,tzinfo=timezone.utc).timestamp()))
    r["indicators"]["quote"][0]["close"].append(100.0)
    with pytest.raises(CaseServiceError):
        beta.calculate_yahoo_beta(json.dumps(payload),MARKET)


def test_replay_is_immutable_and_no_review(tmp_path:Path):
    root=tmp_path/"workspace"/"source_snapshots"
    root.mkdir(parents=True)
    a=root/"INGR_yahoo_original.json"
    b=root/"GSPC_yahoo_original.json"
    a.write_text(ISSUER,encoding="utf-8")
    b.write_text(MARKET,encoding="utf-8")
    out=beta.materialize_yahoo_beta(tmp_path,a,b)
    assert out["status"]=="REAL_INGR_YAHOO_PRICE_ONLY_BETA_CANDIDATE_READY_FOR_REVIEW"
    assert out["human_review_completed"] is False
    assert out["historical_source_availability_asof_proven"] is False
    assert all(Path(out[key]).exists() for key in
        ("issuer_snapshot_path","market_snapshot_path","wacc_input_path","method_proof_path"))
    with pytest.raises(CaseServiceError,match="already materialized"):
        beta.materialize_yahoo_beta(tmp_path,a,b)
    outside=tmp_path/"outside.json"
    outside.write_text(ISSUER,encoding="utf-8")
    with pytest.raises(CaseServiceError):
        beta.materialize_yahoo_beta(tmp_path,outside,b)


def test_beta_r_squared_low_power_is_review_advisory_not_source_rejection():
    from valuation_hub.ingr_r8_m24_readiness import _beta_regression_risk
    low = _beta_regression_risk(0.07067663798658909)
    assert low["status"] == "LOW_EXPLANATORY_POWER_REVIEW_REQUIRED"
    assert low["equity_return_variance_explained"] == 0.07067663798658909
    assert low["beta_source_candidate_not_reviewed_wacc"] is True
    assert _beta_regression_risk(0.2)["status"] == "EXPLANATORY_POWER_REVIEW_PENDING"
    assert _beta_regression_risk(0.1)["status"] == "EXPLANATORY_POWER_REVIEW_PENDING"
    for invalid in (float("nan"), -0.01, 1.1, True):
        with pytest.raises(CaseServiceError):
            _beta_regression_risk(invalid)
