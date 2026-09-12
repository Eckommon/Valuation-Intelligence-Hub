"""M24 governed WACC assumption package.

WACC is a valuation assumption, not a historical fact. Sourced inputs,
deterministic arithmetic, and human review remain separate authority states.
"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import date, datetime
from math import isfinite
from typing import Any

from valuation_hub.case_service import CaseServiceError

SOURCE_SCHEMA="wacc-source-input-v0.1";SOURCE_STATUS="WACC_SOURCE_INPUT"
CANDIDATE_SCHEMA="wacc-assumption-candidate-v0.1";CANDIDATE_STATUS="WACC_ASSUMPTION_CANDIDATE"
REVIEW_SCHEMA="wacc-review-assertion-v0.1";REVIEW_STATUS="WACC_REVIEW_APPROVED"
PACKAGE_SCHEMA="reviewed-wacc-assumption-v0.1";PACKAGE_STATUS="WACC_ASSUMPTION_REVIEWED"
METHODOLOGY_VERSION="wacc-capm-market-weights-v0.1"
SOURCE_CLAIM_CLASSES=("FACT","NORMALIZED_FACT","ASSUMPTION");SOURCE_TIERS=("A","B","C","D");REVIEWABLE_TIERS={"A","B","C"}
RISK_FREE_RATE="risk_free_rate";EQUITY_RISK_PREMIUM="equity_risk_premium";LEVERED_BETA="levered_beta"
PRE_TAX_COST_OF_DEBT="pre_tax_cost_of_debt";EQUITY_MARKET_VALUE="equity_market_value";DEBT_MARKET_VALUE="debt_market_value";TAX_RATE="tax_rate"
REQUIRED_METRICS=(RISK_FREE_RATE,EQUITY_RISK_PREMIUM,LEVERED_BETA,PRE_TAX_COST_OF_DEBT,EQUITY_MARKET_VALUE,DEBT_MARKET_VALUE,TAX_RATE)
RATE_METRICS={RISK_FREE_RATE,EQUITY_RISK_PREMIUM,PRE_TAX_COST_OF_DEBT,TAX_RATE}
FRESHNESS_MAX_AGE_DAYS={RISK_FREE_RATE:30,EQUITY_RISK_PREMIUM:90,LEVERED_BETA:180,PRE_TAX_COST_OF_DEBT:180,EQUITY_MARKET_VALUE:30,DEBT_MARKET_VALUE:550,TAX_RATE:550}
CALC_KEYS=("cost_of_equity","after_tax_cost_of_debt","weight_equity","weight_debt","wacc")


def _bytes(v:Any)->bytes:return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def _sha(v:Any)->str:return hashlib.sha256(_bytes(v)).hexdigest()
def _without(v:dict[str,Any],k:str)->dict[str,Any]:x=copy.deepcopy(v);x.pop(k,None);return x

def _finite(v:Any,label:str)->float:
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(float(v)):raise CaseServiceError(f"{label} must be finite number / {label} 유한 숫자 필요")
    return float(v)

def _canonical_date(v:Any,label:str)->date:
    if not isinstance(v,str):raise CaseServiceError(f"{label} date required / {label} 날짜 필요")
    try:p=date.fromisoformat(v)
    except ValueError as exc:raise CaseServiceError(f"{label} must be YYYY-MM-DD / {label} 날짜 형식 오류") from exc
    if p.isoformat()!=v:raise CaseServiceError(f"{label} must be canonical YYYY-MM-DD / {label} 정규 날짜 필요")
    return p

def _timestamp(v:Any,label:str)->str:
    if not isinstance(v,str):raise CaseServiceError(f"{label} timestamp required / {label} 시각 필요")
    try:p=datetime.fromisoformat(v)
    except ValueError as exc:raise CaseServiceError(f"{label} ISO timestamp invalid / {label} ISO 시각 오류") from exc
    if p.tzinfo is None:raise CaseServiceError(f"{label} timezone required / {label} 시간대 필요")
    return p.isoformat()

def _metric_unit(metric:str,currency:str)->str:
    if metric in RATE_METRICS:return "decimal"
    if metric==LEVERED_BETA:return "ratio"
    if metric in {EQUITY_MARKET_VALUE,DEBT_MARKET_VALUE}:return currency
    raise CaseServiceError(f"unsupported WACC metric / 미지원 WACC 지표: {metric}")
def _range(metric:str,v:float)->None:
    checks={RISK_FREE_RATE:(-0.10,0.50),EQUITY_RISK_PREMIUM:(0,0.50),LEVERED_BETA:(-5,10),PRE_TAX_COST_OF_DEBT:(0,0.99),TAX_RATE:(0,0.99)}
    if metric in checks:
        lo,hi=checks[metric]
        if not lo<=v<=hi:raise CaseServiceError(f"{metric} outside v0.1 range / {metric} 범위 오류")
    elif metric==EQUITY_MARKET_VALUE and v<=0:raise CaseServiceError("equity_market_value must be positive / 자기자본 시장가치 양수 필요")
    elif metric==DEBT_MARKET_VALUE and v<0:raise CaseServiceError("debt_market_value must be nonnegative / 부채 시장가치 음수 불가")

def _scenario_names(v:Any)->list[str]:
    if not isinstance(v,list) or not v:raise CaseServiceError("scenario_names non-empty list required / scenario_names 필요")
    names=[str(x).strip().upper() for x in v]
    if any(not x or len(x)>80 for x in names) or len(set(names))!=len(names):raise CaseServiceError("scenario_names must be unique non-empty names / scenario_names 고유 이름 필요")
    return sorted(names)


def build_wacc_source_input(*,metric:str,value:float,unit:str,observed_on:str,claim_class:str,source_publisher:str,source_type:str,source_tier:str,source_locator:str,source_sha256:str)->dict[str,Any]:
    if metric not in REQUIRED_METRICS:raise CaseServiceError("unsupported WACC source metric / 미지원 WACC 원천지표")
    number=_finite(value,metric);_range(metric,number);_canonical_date(observed_on,"observed_on")
    if claim_class not in SOURCE_CLAIM_CLASSES:raise CaseServiceError("WACC source claim_class invalid / WACC 원천 claim_class 오류")
    if source_tier not in SOURCE_TIERS:raise CaseServiceError("WACC source tier invalid / WACC 원천 tier 오류")
    for label,text in (("unit",unit),("source_publisher",source_publisher),("source_type",source_type),("source_locator",source_locator)):
        if not isinstance(text,str) or not text.strip():raise CaseServiceError(f"{label} required / {label} 필요")
    if not isinstance(source_sha256,str) or len(source_sha256)!=64 or any(ch not in '0123456789abcdef' for ch in source_sha256):raise CaseServiceError("source_sha256 invalid / source_sha256 오류")
    out={"schema_version":SOURCE_SCHEMA,"status":SOURCE_STATUS,"canonical":False,"claim_class":claim_class,"metric":metric,"value":number,"unit":unit.strip(),"observed_on":observed_on,"source":{"publisher":source_publisher.strip(),"type":source_type.strip(),"tier":source_tier,"locator":source_locator.strip(),"source_sha256":source_sha256},"input_sha256":""}
    out["input_sha256"]=_sha(_without(out,"input_sha256"));validate_wacc_source_input(out);return out


def validate_wacc_source_input(v:dict[str,Any])->dict[str,Any]:
    if not isinstance(v,dict) or v.get("schema_version")!=SOURCE_SCHEMA or v.get("status")!=SOURCE_STATUS or v.get("canonical") is not False:raise CaseServiceError("WACC source input schema/status invalid / WACC 원천입력 스키마·상태 오류")
    metric=v.get("metric")
    if metric not in REQUIRED_METRICS:raise CaseServiceError("WACC source metric invalid / WACC 원천지표 오류")
    number=_finite(v.get("value"),str(metric));_range(str(metric),number);_canonical_date(v.get("observed_on"),"observed_on")
    if v.get("claim_class") not in SOURCE_CLAIM_CLASSES or not isinstance(v.get("unit"),str) or not v["unit"].strip():raise CaseServiceError("WACC source claim/unit invalid / WACC 원천 claim·unit 오류")
    source=v.get("source")
    if not isinstance(source,dict) or source.get("tier") not in SOURCE_TIERS:raise CaseServiceError("WACC source provenance invalid / WACC 원천 provenance 오류")
    for f in ("publisher","type","locator"):
        if not isinstance(source.get(f),str) or not source[f].strip():raise CaseServiceError("WACC source provenance incomplete / WACC 원천 provenance 불완전")
    s=source.get("source_sha256")
    if not isinstance(s,str) or len(s)!=64 or any(ch not in '0123456789abcdef' for ch in s):raise CaseServiceError("WACC source SHA invalid / WACC 원천 SHA 오류")
    expected=_sha(_without(v,"input_sha256"))
    if v.get("input_sha256")!=expected:raise CaseServiceError("WACC source input SHA-256 mismatch / WACC 원천입력 SHA 불일치")
    return {"status":"PASS_WACC_SOURCE_INPUT_VALIDATION","input_sha256":expected,"metric":metric}


def _freshness(item:dict[str,Any],as_of:date)->dict[str,Any]:
    observed=_canonical_date(item["observed_on"],"observed_on");age=(as_of-observed).days
    if age<0:raise CaseServiceError("WACC source observed_on after as_of / WACC 원천일자가 as_of 이후")
    maximum=FRESHNESS_MAX_AGE_DAYS[item["metric"]]
    return {"status":"FRESH" if age<=maximum else "STALE_BLOCKED","age_days":age,"max_age_days":maximum}

def _arithmetic(by:dict[str,dict[str,Any]])->dict[str,float]:
    rf=by[RISK_FREE_RATE]["value"];erp=by[EQUITY_RISK_PREMIUM]["value"];beta=by[LEVERED_BETA]["value"];rd=by[PRE_TAX_COST_OF_DEBT]["value"];e=by[EQUITY_MARKET_VALUE]["value"];d=by[DEBT_MARKET_VALUE]["value"];tax=by[TAX_RATE]["value"]
    total=e+d
    if total<=0:raise CaseServiceError("WACC capital total must be positive / WACC 총자본 양수 필요")
    ce=rf+beta*erp;we=e/total;wd=d/total;atd=rd*(1-tax);wacc=we*ce+wd*atd
    if not isfinite(wacc) or not 0<wacc<=0.99:raise CaseServiceError("calculated WACC outside Draft-valid range / 계산 WACC가 Draft 허용범위 밖")
    return {"cost_of_equity":ce,"after_tax_cost_of_debt":atd,"weight_equity":we,"weight_debt":wd,"wacc":wacc}


def build_wacc_candidate(inputs:list[dict[str,Any]],*,entity_id:str,financial_scope:str,capital_currency:str,as_of:str,scenario_names:list[str])->dict[str,Any]:
    if not isinstance(inputs,list) or len(inputs)!=len(REQUIRED_METRICS):raise CaseServiceError("exact seven WACC source inputs required / WACC 원천입력 정확히 7개 필요")
    if not isinstance(entity_id,str) or not entity_id.strip() or not isinstance(financial_scope,str) or not financial_scope.strip():raise CaseServiceError("WACC entity/scope required / WACC entity·scope 필요")
    if not isinstance(capital_currency,str) or not 3<=len(capital_currency.strip())<=8:raise CaseServiceError("capital_currency invalid / 자본 통화 오류")
    currency=capital_currency.strip().upper();as_date=_canonical_date(as_of,"as_of");names=_scenario_names(scenario_names);by:dict[str,dict[str,Any]]={}
    for item in inputs:
        validate_wacc_source_input(item);metric=item["metric"]
        if metric in by:raise CaseServiceError("duplicate WACC source metric / WACC 원천지표 중복")
        if item["unit"]!=_metric_unit(metric,currency):raise CaseServiceError(f"WACC source unit mismatch for {metric} / WACC 원천단위 불일치")
        by[metric]=copy.deepcopy(item)
    if list(by)!=list(REQUIRED_METRICS):raise CaseServiceError("WACC required metric order/coverage invalid / WACC 필수지표 순서·coverage 오류")
    calc=_arithmetic(by);fresh={m:_freshness(x,as_date) for m,x in by.items()};all_fresh=all(x["status"]=="FRESH" for x in fresh.values());all_tiers=all(x["source"]["tier"] in REVIEWABLE_TIERS for x in by.values())
    out={"schema_version":CANDIDATE_SCHEMA,"status":CANDIDATE_STATUS,"canonical":False,"class":"ASSUMPTION_CANDIDATE","methodology_version":METHODOLOGY_VERSION,"entity":{"id":entity_id.strip(),"financial_scope":financial_scope.strip()},"capital_currency":currency,"as_of":as_of,"scenario_names":names,"inputs":[by[m] for m in REQUIRED_METRICS],"freshness":fresh,"calculation":calc,"review_readiness":{"all_required_inputs_present":True,"all_inputs_fresh":all_fresh,"all_source_tiers_reviewable":all_tiers,"eligible_for_human_review":all_fresh and all_tiers},"candidate_sha256":""}
    out["candidate_sha256"]=_sha(_without(out,"candidate_sha256"));validate_wacc_candidate(out);return out


def validate_wacc_candidate(c:dict[str,Any])->dict[str,Any]:
    if not isinstance(c,dict) or c.get("schema_version")!=CANDIDATE_SCHEMA or c.get("status")!=CANDIDATE_STATUS or c.get("canonical") is not False or c.get("class")!="ASSUMPTION_CANDIDATE":raise CaseServiceError("WACC candidate schema/status/authority invalid / WACC candidate 스키마·상태·권위 오류")
    if c.get("methodology_version")!=METHODOLOGY_VERSION:raise CaseServiceError("WACC methodology version invalid / WACC 방법론 버전 오류")
    entity=c.get("entity")
    if not isinstance(entity,dict) or not isinstance(entity.get("id"),str) or not entity["id"] or not isinstance(entity.get("financial_scope"),str) or not entity["financial_scope"]:raise CaseServiceError("WACC candidate entity invalid / WACC candidate entity 오류")
    currency=c.get("capital_currency")
    if not isinstance(currency,str) or not 3<=len(currency)<=8:raise CaseServiceError("WACC candidate currency invalid / WACC candidate 통화 오류")
    as_date=_canonical_date(c.get("as_of"),"as_of");names=_scenario_names(c.get("scenario_names"))
    if c.get("scenario_names")!=names:raise CaseServiceError("WACC scenario_names must be sorted canonical names / WACC scenario_names 정규화 오류")
    inputs=c.get("inputs")
    if not isinstance(inputs,list) or len(inputs)!=len(REQUIRED_METRICS):raise CaseServiceError("WACC candidate inputs invalid / WACC candidate 입력 오류")
    by:dict[str,dict[str,Any]]={}
    for item in inputs:
        validate_wacc_source_input(item);metric=item["metric"]
        if metric in by or item["unit"]!=_metric_unit(metric,currency):raise CaseServiceError("WACC candidate metric/unit conflict / WACC candidate 지표·단위 충돌")
        by[metric]=item
    if list(by)!=list(REQUIRED_METRICS):raise CaseServiceError("WACC candidate input order/coverage invalid / WACC candidate 입력순서·coverage 오류")
    expected_calc=_arithmetic(by);calc=c.get("calculation")
    if not isinstance(calc,dict) or set(calc)!=set(CALC_KEYS):raise CaseServiceError("WACC candidate calculation shape invalid / WACC candidate 계산구조 오류")
    for k,v in expected_calc.items():
        actual=_finite(calc.get(k),f"calculation.{k}")
        if abs(actual-v)>1e-12:raise CaseServiceError("WACC candidate arithmetic mismatch / WACC candidate 계산 불일치")
    if abs((expected_calc["weight_equity"]+expected_calc["weight_debt"])-1.0)>1e-12:raise CaseServiceError("WACC weights do not sum to one / WACC 가중치 합 오류")
    fresh={m:_freshness(x,as_date) for m,x in by.items()}
    if c.get("freshness")!=fresh:raise CaseServiceError("WACC candidate freshness mismatch / WACC candidate 최신성 불일치")
    all_fresh=all(x["status"]=="FRESH" for x in fresh.values());all_tiers=all(x["source"]["tier"] in REVIEWABLE_TIERS for x in by.values());ready={"all_required_inputs_present":True,"all_inputs_fresh":all_fresh,"all_source_tiers_reviewable":all_tiers,"eligible_for_human_review":all_fresh and all_tiers}
    if c.get("review_readiness")!=ready:raise CaseServiceError("WACC candidate review readiness mismatch / WACC candidate 검토준비도 불일치")
    expected=_sha(_without(c,"candidate_sha256"))
    if c.get("candidate_sha256")!=expected:raise CaseServiceError("WACC candidate SHA-256 mismatch / WACC candidate SHA 불일치")
    return {"status":"PASS_WACC_CANDIDATE_VALIDATION","candidate_sha256":expected,"wacc":expected_calc["wacc"],"eligible_for_human_review":ready["eligible_for_human_review"]}


def build_wacc_review_assertion(candidate:dict[str,Any],*,reviewer:str,approved_at:str,review_basis:str)->dict[str,Any]:
    checked=validate_wacc_candidate(candidate)
    if checked["eligible_for_human_review"] is not True:raise CaseServiceError("WACC candidate not eligible for human review / WACC candidate 인간검토 부적격")
    if not isinstance(reviewer,str) or not reviewer.strip() or len(reviewer)>160:raise CaseServiceError("WACC reviewer required / WACC reviewer 필요")
    ts=_timestamp(approved_at,"approved_at")
    if datetime.fromisoformat(ts).date()<_canonical_date(candidate["as_of"],"as_of"):raise CaseServiceError("WACC approval cannot predate valuation as_of / WACC 승인이 가치평가 as_of보다 앞설 수 없음")
    if not isinstance(review_basis,str) or not review_basis.strip() or len(review_basis)>4000:raise CaseServiceError("WACC review_basis required / WACC review_basis 필요")
    out={"schema_version":REVIEW_SCHEMA,"status":REVIEW_STATUS,"canonical":False,"decision":"APPROVE_WACC_ASSUMPTION","candidate_sha256":candidate["candidate_sha256"],"methodology_version":candidate["methodology_version"],"as_of":candidate["as_of"],"scenario_names":copy.deepcopy(candidate["scenario_names"]),"reviewer":reviewer.strip(),"approved_at":ts,"review_basis":review_basis.strip(),"assertion_sha256":""}
    out["assertion_sha256"]=_sha(_without(out,"assertion_sha256"));validate_wacc_review_assertion(out,candidate);return out


def validate_wacc_review_assertion(a:dict[str,Any],c:dict[str,Any])->dict[str,Any]:
    checked=validate_wacc_candidate(c)
    if checked["eligible_for_human_review"] is not True:raise CaseServiceError("review assertion cannot approve ineligible WACC candidate / 부적격 WACC candidate 승인 불가")
    if not isinstance(a,dict) or a.get("schema_version")!=REVIEW_SCHEMA or a.get("status")!=REVIEW_STATUS or a.get("canonical") is not False or a.get("decision")!="APPROVE_WACC_ASSUMPTION":raise CaseServiceError("WACC review assertion schema/status invalid / WACC 검토승인 스키마·상태 오류")
    if a.get("candidate_sha256")!=c.get("candidate_sha256") or a.get("methodology_version")!=c.get("methodology_version") or a.get("as_of")!=c.get("as_of") or a.get("scenario_names")!=c.get("scenario_names"):raise CaseServiceError("WACC review assertion candidate lineage mismatch / WACC 검토승인 candidate lineage 불일치")
    if not isinstance(a.get("reviewer"),str) or not a["reviewer"].strip() or not isinstance(a.get("review_basis"),str) or not a["review_basis"].strip():raise CaseServiceError("WACC review assertion reviewer/basis invalid / WACC 검토승인 reviewer·basis 오류")
    ts=_timestamp(a.get("approved_at"),"approved_at")
    if datetime.fromisoformat(ts).date()<_canonical_date(c["as_of"],"as_of"):raise CaseServiceError("WACC approval predates valuation as_of / WACC 승인이 가치평가 as_of보다 앞섬")
    expected=_sha(_without(a,"assertion_sha256"))
    if a.get("assertion_sha256")!=expected:raise CaseServiceError("WACC review assertion SHA-256 mismatch / WACC 검토승인 SHA 불일치")
    return {"status":"PASS_WACC_REVIEW_ASSERTION_VALIDATION","assertion_sha256":expected}


def finalize_reviewed_wacc(c:dict[str,Any],a:dict[str,Any])->dict[str,Any]:
    validate_wacc_candidate(c);validate_wacc_review_assertion(a,c)
    out={"schema_version":PACKAGE_SCHEMA,"status":PACKAGE_STATUS,"canonical":False,"class":"ASSUMPTION","methodology_version":c["methodology_version"],"entity":copy.deepcopy(c["entity"]),"capital_currency":c["capital_currency"],"as_of":c["as_of"],"scenario_names":copy.deepcopy(c["scenario_names"]),"wacc":c["calculation"]["wacc"],"candidate":copy.deepcopy(c),"review_assertion":copy.deepcopy(a),"binding_eligibility":{"eligible":True,"reason":"REVIEWED_WACC_ASSUMPTION"},"package_sha256":""}
    out["package_sha256"]=_sha(_without(out,"package_sha256"));validate_reviewed_wacc(out);return out


def validate_reviewed_wacc(p:dict[str,Any])->dict[str,Any]:
    if not isinstance(p,dict) or p.get("schema_version")!=PACKAGE_SCHEMA or p.get("status")!=PACKAGE_STATUS or p.get("canonical") is not False or p.get("class")!="ASSUMPTION":raise CaseServiceError("reviewed WACC package schema/status/authority invalid / 검토완료 WACC 패키지 스키마·상태·권위 오류")
    c=p.get("candidate");a=p.get("review_assertion")
    if not isinstance(c,dict) or not isinstance(a,dict):raise CaseServiceError("reviewed WACC nested candidate/assertion missing / 검토완료 WACC 중첩객체 누락")
    checked=validate_wacc_candidate(c);validate_wacc_review_assertion(a,c)
    if checked["eligible_for_human_review"] is not True:raise CaseServiceError("reviewed WACC candidate no longer eligible / 검토완료 WACC candidate 부적격")
    expected_fields={"methodology_version":c["methodology_version"],"entity":c["entity"],"capital_currency":c["capital_currency"],"as_of":c["as_of"],"scenario_names":c["scenario_names"],"wacc":c["calculation"]["wacc"]}
    for k,v in expected_fields.items():
        if p.get(k)!=v:raise CaseServiceError("reviewed WACC projection mismatch / 검토완료 WACC 투영 불일치")
    if p.get("binding_eligibility")!={"eligible":True,"reason":"REVIEWED_WACC_ASSUMPTION"}:raise CaseServiceError("reviewed WACC binding eligibility invalid / 검토완료 WACC 바인딩 적격성 오류")
    expected=_sha(_without(p,"package_sha256"))
    if p.get("package_sha256")!=expected:raise CaseServiceError("reviewed WACC package SHA-256 mismatch / 검토완료 WACC 패키지 SHA 불일치")
    return {"status":"PASS_REVIEWED_WACC_VALIDATION","package_sha256":expected,"wacc":p["wacc"],"scenario_names":copy.deepcopy(p["scenario_names"]),"eligible":True}
