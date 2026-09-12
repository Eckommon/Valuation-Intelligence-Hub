"""M21 governed historical share-dilution evidence / 역사적 희석주식 참조근거.

SEC weighted-average basic/diluted EPS denominators are duration evidence. They are
useful historical dilution context but are never valuation-date fully diluted shares.
M21 uses an isolated source registry and does not mutate M13 SEC metric contracts.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import date
from math import isfinite
from typing import Any
from urllib.parse import urlparse

from valuation_hub.case_service import CaseServiceError
from valuation_hub.financial_normalization import DURATION_ANNUAL, DURATION_QUARTER, DURATION_YTD
from valuation_hub.sec_live import ACCESSION_RE, validate_source_snapshot

CANDIDATE_SCHEMA = "share-dilution-candidate-v0.1"
CANDIDATE_STATUS = "SHARE_DILUTION_CANDIDATE_UNREVIEWED"
OBSERVATION_SCHEMA = "share-dilution-observation-v0.1"
OBSERVATION_STATUS = "SHARE_DILUTION_OBSERVATION_NORMALIZED"
DERIVED_SCHEMA = "historical-dilution-evidence-v0.1"
DERIVED_STATUS = "HISTORICAL_DILUTION_EVIDENCE"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
CIK_PATH_RE = re.compile(r"/CIK([0-9]{10})\.json$")
ALLOWED_FORMS = frozenset({"10-Q", "10-Q/A", "10-K", "10-K/A"})
METRICS = {
    "weighted_average_basic_shares": "WeightedAverageNumberOfSharesOutstandingBasic",
    "weighted_average_diluted_shares": "WeightedAverageNumberOfDilutedSharesOutstanding",
}


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    out=copy.deepcopy(value);out.pop(key,None);return out


def _iso(value: Any, field: str) -> str:
    if not isinstance(value,str): raise CaseServiceError(f"{field} date required / {field} 날짜 필요")
    try: parsed=date.fromisoformat(value)
    except ValueError as exc: raise CaseServiceError(f"{field} invalid / {field} 오류") from exc
    if parsed.isoformat()!=value: raise CaseServiceError(f"{field} canonical YYYY-MM-DD required / {field} 정규날짜 필요")
    return value


def _num(value: Any, field: str) -> int|float:
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not isfinite(float(value)):
        raise CaseServiceError(f"{field} finite numeric required / {field} 유한 숫자 필요")
    return value


def _source_class(value: Any) -> str:
    if value=="FACT": return "NORMALIZED_FACT"
    if value=="FACT_CANDIDATE": return "NORMALIZED_FACT_CANDIDATE"
    raise CaseServiceError("dilution source class must be FACT or FACT_CANDIDATE / 희석주식 source class 오류")


def extract_sec_dilution_candidate(snapshot:dict[str,Any],metric:str,*,period_start:str,period_end:str,form:str|None=None)->dict[str,Any]:
    validation=validate_source_snapshot(snapshot)
    concept=METRICS.get(metric)
    if concept is None: raise CaseServiceError(f"unsupported dilution metric / 미지원 희석주식 지표: {metric}")
    start,end=_iso(period_start,"period_start"),_iso(period_end,"period_end")
    if date.fromisoformat(start)>date.fromisoformat(end): raise CaseServiceError("period_start after period_end / 기간 시작일이 종료일 이후")
    requested_form=form.upper() if form else None
    if requested_form is not None and requested_form not in ALLOWED_FORMS: raise CaseServiceError("unsupported SEC form for dilution metric / 희석주식 SEC form 오류")
    payload=json.loads(snapshot["raw_text"])
    facts=payload.get("facts",{});usgaap=facts.get("us-gaap",{}) if isinstance(facts,dict) else {}
    obj=usgaap.get(concept) if isinstance(usgaap,dict) else None;units=obj.get("units") if isinstance(obj,dict) else None
    series=units.get("shares") if isinstance(units,dict) else None
    if not isinstance(series,list): raise CaseServiceError("SEC dilution concept/shares unit unavailable / SEC 희석주식 concept·shares unit 없음")
    candidates=[]
    for raw in series:
        if not isinstance(raw,dict) or raw.get("start")!=start or raw.get("end")!=end: continue
        raw_form=raw.get("form")
        if raw_form not in ALLOWED_FORMS or (requested_form and raw_form!=requested_form): continue
        filed=raw.get("filed");accn=raw.get("accn")
        if not isinstance(filed,str): continue
        _iso(filed,"filed")
        if not isinstance(accn,str) or not ACCESSION_RE.fullmatch(accn): raise CaseServiceError("SEC dilution accession invalid / SEC 희석주식 accession 오류")
        if "val" not in raw: continue
        candidates.append(copy.deepcopy(raw))
    if not candidates: raise CaseServiceError("no exact SEC dilution fact for requested period / 요청기간과 정확히 일치하는 SEC 희석주식 fact 없음")
    latest=max(item["filed"] for item in candidates);top=[x for x in candidates if x["filed"]==latest]
    distinct={json.dumps(x.get("val"),sort_keys=True,allow_nan=False) for x in top}
    if len(distinct)!=1: raise CaseServiceError("conflicting SEC dilution facts at equal precedence / 동일 우선순위 SEC 희석주식 fact 충돌")
    chosen=sorted(top,key=lambda x:(str(x.get("accn","")),str(x.get("form","")),str(x.get("frame",""))),reverse=True)[0]
    candidate={
        "schema_version":CANDIDATE_SCHEMA,"status":CANDIDATE_STATUS,"canonical":False,"class":"FACT_CANDIDATE",
        "metric":metric,"value":chosen["val"],"unit":"shares",
        "entity":{"id":f"SEC_CIK:{validation['cik']}","source_system":"SEC","financial_scope":"AS_REPORTED"},
        "period":{"start":start,"end":end,"fy":chosen.get("fy"),"fp":chosen.get("fp"),"frame":chosen.get("frame")},
        "filing":{"accession":chosen["accn"],"form":chosen["form"],"filed":chosen["filed"]},
        "taxonomy":"us-gaap","concept":concept,
        "source":{"publisher":"U.S. Securities and Exchange Commission","source_type":"official_edgar_companyfacts_api","tier_proposal":"A","locator":snapshot["source"]["final_locator"],"snapshot_sha256":snapshot["snapshot_sha256"],"body_sha256":snapshot["response"]["body_sha256"]},
        "selection":{"rule":"EXACT_START_END_THEN_LATEST_FILED","requested_start":start,"requested_end":end,"requested_form":requested_form,"equal_precedence_count":len(top)},
        "warning_en":"Historical weighted-average EPS denominator evidence only; not valuation-date fully diluted shares.",
        "warning_ko":"역사적 기간평균 EPS denominator 근거일 뿐 valuation-date 완전희석주식수가 아닙니다.",
        "candidate_sha256":"",
    }
    candidate["candidate_sha256"]=_sha(_without(candidate,"candidate_sha256"));validate_share_dilution_candidate(candidate);return candidate


def validate_share_dilution_candidate(candidate:dict[str,Any])->dict[str,Any]:
    if not isinstance(candidate,dict) or candidate.get("schema_version")!=CANDIDATE_SCHEMA or candidate.get("status")!=CANDIDATE_STATUS or candidate.get("canonical") is not False:
        raise CaseServiceError("share dilution candidate schema/status invalid / 희석주식 candidate 스키마·상태 오류")
    metric=candidate.get("metric");concept=METRICS.get(metric)
    if concept is None or candidate.get("taxonomy")!="us-gaap" or candidate.get("concept")!=concept or candidate.get("unit")!="shares":
        raise CaseServiceError("share dilution candidate semantic mapping invalid / 희석주식 candidate 의미매핑 오류")
    _source_class(candidate.get("class"));_num(candidate.get("value"),"dilution candidate value")
    entity,period,filing,source,selection=candidate.get("entity"),candidate.get("period"),candidate.get("filing"),candidate.get("source"),candidate.get("selection")
    if not all(isinstance(x,dict) for x in (entity,period,filing,source,selection)): raise CaseServiceError("share dilution candidate provenance incomplete / 희석주식 candidate 출처정보 불완전")
    if not isinstance(entity.get("id"),str) or not entity["id"].startswith("SEC_CIK:") or entity.get("financial_scope")!="AS_REPORTED": raise CaseServiceError("share dilution entity invalid / 희석주식 entity 오류")
    start,end=_iso(period.get("start"),"period.start"),_iso(period.get("end"),"period.end")
    if selection.get("requested_start")!=start or selection.get("requested_end")!=end or selection.get("rule")!="EXACT_START_END_THEN_LATEST_FILED": raise CaseServiceError("share dilution selection/period mismatch / 희석주식 selection·기간 불일치")
    if filing.get("form") not in ALLOWED_FORMS or not isinstance(filing.get("accession"),str) or not ACCESSION_RE.fullmatch(filing["accession"]): raise CaseServiceError("share dilution filing invalid / 희석주식 filing 오류")
    _iso(filing.get("filed"),"filing.filed")
    for key in ("snapshot_sha256","body_sha256"):
        if not isinstance(source.get(key),str) or not SHA256_RE.fullmatch(source[key]): raise CaseServiceError("share dilution source SHA invalid / 희석주식 source SHA 오류")
    expected=_sha(_without(candidate,"candidate_sha256"))
    if candidate.get("candidate_sha256")!=expected: raise CaseServiceError("share dilution candidate SHA-256 mismatch / 희석주식 candidate SHA-256 불일치")
    return {"status":"PASS_SHARE_DILUTION_CANDIDATE_VALIDATION","canonical":False,"candidate_sha256":expected}


def _period_kind(candidate:dict[str,Any])->tuple[str,int|None,int]:
    start=date.fromisoformat(candidate["period"]["start"]);end=date.fromisoformat(candidate["period"]["end"]);days=(end-start).days+1
    form=candidate["filing"]["form"];fp=str(candidate["period"].get("fp"))
    fq={"Q1":1,"Q2":2,"Q3":3,"FY":4}.get(fp)
    if form in {"10-K","10-K/A"}:
        if not 330<=days<=400: raise CaseServiceError("SEC dilution 10-K duration invalid / SEC 희석주식 10-K 기간 오류")
        return DURATION_ANNUAL,4,days
    if form in {"10-Q","10-Q/A"}:
        if fq not in {1,2,3}: raise CaseServiceError("SEC dilution 10-Q fp invalid / SEC 희석주식 10-Q fp 오류")
        if 60<=days<=120: return DURATION_QUARTER,fq,days
        if fq==2 and 140<=days<=220: return DURATION_YTD,fq,days
        if fq==3 and 230<=days<=320: return DURATION_YTD,fq,days
        raise CaseServiceError("SEC dilution 10-Q duration cannot be safely classified / SEC 희석주식 10-Q 기간 분류불가")
    raise CaseServiceError("unsupported dilution filing form / 미지원 희석주식 filing form")


def normalize_share_dilution_candidate(candidate:dict[str,Any])->dict[str,Any]:
    validate_share_dilution_candidate(candidate);kind,fq,days=_period_kind(candidate)
    result={
        "schema_version":OBSERVATION_SCHEMA,"status":OBSERVATION_STATUS,"canonical":False,"class":_source_class(candidate["class"]),
        "metric":candidate["metric"],"value":_num(candidate["value"],"dilution value"),"unit":"shares","entity":copy.deepcopy(candidate["entity"]),
        "period":{"kind":kind,"start":candidate["period"]["start"],"end":candidate["period"]["end"],"duration_days":days,"fiscal_year":candidate["period"].get("fy"),"fiscal_period":candidate["period"].get("fp"),"fiscal_quarter":fq,"report_stage":candidate["period"].get("fp"),"date_precision":"EXACT"},
        "lineage":{"normalization_rule":"SEC_WEIGHTED_AVERAGE_SHARE_DURATION_V01","source_candidate_sha256":candidate["candidate_sha256"],"source_class":candidate["class"],"source_snapshot_sha256":candidate["source"]["snapshot_sha256"],"source_body_sha256":candidate["source"]["body_sha256"],"filing_identity":copy.deepcopy(candidate["filing"]),"source_detail":{"taxonomy":"us-gaap","concept":candidate["concept"],"frame":candidate["period"].get("frame")}},
        "observation_sha256":"",
    }
    result["observation_sha256"]=_sha(_without(result,"observation_sha256"));validate_share_dilution_observation(result);return result


def validate_share_dilution_observation(obs:dict[str,Any])->dict[str,Any]:
    if not isinstance(obs,dict) or obs.get("schema_version")!=OBSERVATION_SCHEMA or obs.get("status")!=OBSERVATION_STATUS or obs.get("canonical") is not False:
        raise CaseServiceError("share dilution observation schema/status invalid / 희석주식 observation 스키마·상태 오류")
    if obs.get("metric") not in METRICS or obs.get("unit")!="shares" or obs.get("class") not in {"NORMALIZED_FACT","NORMALIZED_FACT_CANDIDATE"}: raise CaseServiceError("share dilution observation semantics invalid / 희석주식 observation 의미 오류")
    _num(obs.get("value"),"dilution observation value")
    period=obs.get("period");entity=obs.get("entity");lineage=obs.get("lineage")
    if not all(isinstance(x,dict) for x in (period,entity,lineage)): raise CaseServiceError("share dilution observation structure invalid / 희석주식 observation 구조 오류")
    if period.get("kind") not in {DURATION_QUARTER,DURATION_YTD,DURATION_ANNUAL} or period.get("date_precision")!="EXACT": raise CaseServiceError("share dilution observation duration semantics invalid / 희석주식 observation 기간 의미 오류")
    start,end=_iso(period.get("start"),"period.start"),_iso(period.get("end"),"period.end")
    if period.get("duration_days")!=(date.fromisoformat(end)-date.fromisoformat(start)).days+1: raise CaseServiceError("share dilution duration_days mismatch / 희석주식 duration_days 불일치")
    if lineage.get("normalization_rule")!="SEC_WEIGHTED_AVERAGE_SHARE_DURATION_V01": raise CaseServiceError("share dilution normalization rule invalid / 희석주식 정규화 규칙 오류")
    for key in ("source_candidate_sha256","source_snapshot_sha256","source_body_sha256"):
        if not isinstance(lineage.get(key),str) or not SHA256_RE.fullmatch(lineage[key]): raise CaseServiceError("share dilution lineage SHA invalid / 희석주식 lineage SHA 오류")
    expected=_sha(_without(obs,"observation_sha256"))
    if obs.get("observation_sha256")!=expected: raise CaseServiceError("share dilution observation SHA-256 mismatch / 희석주식 observation SHA-256 불일치")
    return {"status":"PASS_SHARE_DILUTION_OBSERVATION_VALIDATION","canonical":False,"observation_sha256":expected}


def derive_historical_dilution(basic:dict[str,Any],diluted:dict[str,Any])->dict[str,Any]:
    validate_share_dilution_observation(basic);validate_share_dilution_observation(diluted)
    if basic.get("metric")!="weighted_average_basic_shares" or diluted.get("metric")!="weighted_average_diluted_shares": raise CaseServiceError("basic/diluted metric pair required / basic·diluted 지표쌍 필요")
    if basic.get("entity")!=diluted.get("entity") or basic.get("unit")!=diluted.get("unit") or basic.get("period")!=diluted.get("period"): raise CaseServiceError("dilution observations entity/unit/period mismatch / 희석주식 observation entity·unit·period 불일치")
    b=_num(basic["value"],"basic shares");d=_num(diluted["value"],"diluted shares")
    if b<=0: raise CaseServiceError("basic shares must be > 0 / basic shares는 0보다 커야 함")
    if d<b: raise CaseServiceError("diluted shares cannot be below basic shares / diluted shares가 basic shares보다 작을 수 없음")
    klass="DERIVED_FACT" if basic["class"]==diluted["class"]=="NORMALIZED_FACT" else "DERIVED_FACT_CANDIDATE"
    result={
        "schema_version":DERIVED_SCHEMA,"status":DERIVED_STATUS,"canonical":False,"class":klass,
        "entity":copy.deepcopy(basic["entity"]),"period":copy.deepcopy(basic["period"]),
        "historical_dilution_factor":d/b,"historical_incremental_diluted_shares":d-b,"unit":"ratio+shares",
        "sources":[{"metric":basic["metric"],"value":b,"class":basic["class"],"observation_sha256":basic["observation_sha256"]},{"metric":diluted["metric"],"value":d,"class":diluted["class"],"observation_sha256":diluted["observation_sha256"]}],
        "semantic_boundary":{"historical_only":True,"valuation_date_direct_bind":False,"forecast_direct_bind":False,"shares_outstanding_substitution":False,"warning_en":"Weighted-average diluted EPS shares are historical duration evidence, not valuation-date fully diluted shares.","warning_ko":"기간평균 diluted EPS 주식수는 역사적 기간근거이며 valuation-date 완전희석주식수가 아닙니다."},
        "derived_sha256":"",
    }
    result["derived_sha256"]=_sha(_without(result,"derived_sha256"));validate_historical_dilution(result);return result


def validate_historical_dilution(value:dict[str,Any])->dict[str,Any]:
    if not isinstance(value,dict) or value.get("schema_version")!=DERIVED_SCHEMA or value.get("status")!=DERIVED_STATUS or value.get("canonical") is not False or value.get("class") not in {"DERIVED_FACT","DERIVED_FACT_CANDIDATE"}: raise CaseServiceError("historical dilution schema/status/authority invalid / 역사적 희석도 스키마·상태·권위 오류")
    sources=value.get("sources");boundary=value.get("semantic_boundary")
    if not isinstance(sources,list) or len(sources)!=2 or not isinstance(boundary,dict): raise CaseServiceError("historical dilution structure invalid / 역사적 희석도 구조 오류")
    by={x.get("metric"):x for x in sources if isinstance(x,dict)}
    if set(by)!=set(METRICS): raise CaseServiceError("historical dilution source metrics invalid / 역사적 희석도 source metric 오류")
    for item in sources:
        if item.get("class") not in {"NORMALIZED_FACT","NORMALIZED_FACT_CANDIDATE"} or not isinstance(item.get("observation_sha256"),str) or not SHA256_RE.fullmatch(item["observation_sha256"]): raise CaseServiceError("historical dilution source lineage invalid / 역사적 희석도 source lineage 오류")
    b=_num(by["weighted_average_basic_shares"]["value"],"basic shares");d=_num(by["weighted_average_diluted_shares"]["value"],"diluted shares")
    if b<=0 or d<b: raise CaseServiceError("historical dilution source arithmetic invalid / 역사적 희석도 source 산술 오류")
    expected_class="DERIVED_FACT" if all(x["class"]=="NORMALIZED_FACT" for x in sources) else "DERIVED_FACT_CANDIDATE"
    if value.get("class")!=expected_class: raise CaseServiceError("historical dilution authority propagation mismatch / 역사적 희석도 권위전파 불일치")
    if abs(_num(value.get("historical_dilution_factor"),"dilution factor")-(d/b))>1e-12 or _num(value.get("historical_incremental_diluted_shares"),"incremental shares")!=(d-b): raise CaseServiceError("historical dilution arithmetic mismatch / 역사적 희석도 산술 불일치")
    expected_boundary={"historical_only":True,"valuation_date_direct_bind":False,"forecast_direct_bind":False,"shares_outstanding_substitution":False,"warning_en":"Weighted-average diluted EPS shares are historical duration evidence, not valuation-date fully diluted shares.","warning_ko":"기간평균 diluted EPS 주식수는 역사적 기간근거이며 valuation-date 완전희석주식수가 아닙니다."}
    if boundary!=expected_boundary: raise CaseServiceError("historical dilution semantic boundary mismatch / 역사적 희석도 의미경계 불일치")
    expected=_sha(_without(value,"derived_sha256"))
    if value.get("derived_sha256")!=expected: raise CaseServiceError("historical dilution SHA-256 mismatch / 역사적 희석도 SHA-256 불일치")
    return {"status":"PASS_HISTORICAL_DILUTION_VALIDATION","canonical":False,"derived_sha256":expected,"class":expected_class}
