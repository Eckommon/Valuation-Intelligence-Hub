"""M24 reviewed WACC assumption → Draft binding proposal v0.4.

M24 wraps an already validated v0.1/v0.2/v0.3 proposal and replaces only
`scenario.wacc` with a human-reviewed WACC ASSUMPTION package.
"""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.draft_binding import DIRECT_BIND, MATERIAL_FIELDS, STATUS
from valuation_hub.share_draft_binding import validate_binding_proposal_any as validate_binding_proposal_any_v3
from valuation_hub.wacc_assumption import validate_reviewed_wacc

SCHEMA_VERSION_V4="draft-binding-proposal-v0.4"
POLICY_VERSION_V4="evidence-draft-binding-v0.4-wacc"
DIRECT_REQUIREMENTS=["REVIEWED_ASSUMPTION","FRESH_SOURCE_INPUTS","EXPLICIT_METHOD","HUMAN_REVIEW_ASSERTION","EXACT_SCENARIO_TARGET_SET"]


def _bytes(v:Any)->bytes:return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def _sha(v:Any)->str:return hashlib.sha256(_bytes(v)).hexdigest()
def _without(v:dict[str,Any],k:str)->dict[str,Any]:x=copy.deepcopy(v);x.pop(k,None);return x

def _counts(matrix:list[dict[str,Any]])->dict[str,Any]:
    counts:dict[str,int]={}
    for item in matrix:counts[item["state"]]=counts.get(item["state"],0)+1
    return {"material_field_count":len(MATERIAL_FIELDS),"classified_field_count":len(matrix),"state_counts":counts,"direct_bind_count":counts.get(DIRECT_BIND,0),"unresolved_count":sum(c for s,c in counts.items() if s!=DIRECT_BIND)}

def _eligible_package(package:dict[str,Any])->None:
    checked=validate_reviewed_wacc(package)
    if checked.get("eligible") is not True or package.get("class")!="ASSUMPTION" or package.get("binding_eligibility")!={"eligible":True,"reason":"REVIEWED_WACC_ASSUMPTION"}:raise CaseServiceError("only reviewed eligible WACC assumption can bind / 검토완료 적격 WACC 가정만 바인딩 가능")

def _projection(package:dict[str,Any])->dict[str,Any]:
    return {"metric":"wacc_assumption","value":package["wacc"],"unit":"decimal","class":"ASSUMPTION","entity":copy.deepcopy(package["entity"]),"capital_currency":package["capital_currency"],"as_of":package["as_of"],"scenario_names":copy.deepcopy(package["scenario_names"]),"methodology_version":package["methodology_version"],"context_sha256":package["package_sha256"],"source_package_sha256":package["package_sha256"],"review_assertion_sha256":package["review_assertion"]["assertion_sha256"]}
def _decision(package:dict[str,Any])->dict[str,Any]:
    return {"field":"scenario.wacc","state":DIRECT_BIND,"rationale":"human-reviewed governed WACC assumption / 인간검토완료 거버넌스 WACC 가정","source_metric":"wacc_assumption","source_class":"ASSUMPTION","source_context_sha256":package["package_sha256"],"source_package_sha256":package["package_sha256"],"review_assertion_sha256":package["review_assertion"]["assertion_sha256"],"scenario_names":copy.deepcopy(package["scenario_names"])}
def _policy(base:dict[str,Any])->dict[str,Any]:
    return {"version":POLICY_VERSION_V4,"as_of":base["policy"]["as_of"],"base_policy_version":base["policy"]["version"],"direct_bind_requires":copy.deepcopy(DIRECT_REQUIREMENTS)}


def build_binding_proposal_with_wacc(base_proposal:dict[str,Any],wacc_package:dict[str,Any])->dict[str,Any]:
    validate_binding_proposal_any_v3(base_proposal);_eligible_package(wacc_package)
    identity=base_proposal["identity"];entity=wacc_package["entity"]
    if entity!={"id":identity.get("entity_id"),"financial_scope":identity.get("financial_scope")}:raise CaseServiceError("WACC package entity/scope mismatch with base proposal / WACC 패키지 entity·scope 불일치")
    monetary=identity.get("monetary_unit")
    if monetary is not None and wacc_package.get("capital_currency")!=monetary:raise CaseServiceError("WACC capital currency mismatch with base proposal / WACC 자본통화 불일치")
    base_as_of=base_proposal.get("policy",{}).get("as_of")
    if not isinstance(base_as_of,str) or wacc_package.get("as_of")!=base_as_of:raise CaseServiceError("WACC as_of must equal base proposal as_of / WACC as_of와 base proposal as_of 불일치")
    matrix=[_decision(wacc_package) if item["field"]=="scenario.wacc" else copy.deepcopy(item) for item in base_proposal["draft_input_matrix"]]
    baseline=copy.deepcopy(base_proposal["baseline_context"]);baseline["wacc_assumption"]=_projection(wacc_package)
    out={"schema_version":SCHEMA_VERSION_V4,"status":STATUS,"canonical":False,"target":copy.deepcopy(base_proposal["target"]),"policy":_policy(base_proposal),"identity":copy.deepcopy(identity),"baseline_context":baseline,"conflicts":copy.deepcopy(base_proposal["conflicts"]),"draft_input_matrix":matrix,"completeness":_counts(matrix),"source_observation_sha256":copy.deepcopy(base_proposal["source_observation_sha256"]),"source_wacc_package_sha256":wacc_package["package_sha256"],"wacc_package":copy.deepcopy(wacc_package),"base_proposal":copy.deepcopy(base_proposal),"base_proposal_sha256":base_proposal["proposal_sha256"],"warning_en":"WACC-aware proposal only. WACC remains a reviewed valuation assumption, not a historical fact.","warning_ko":"WACC-aware 제안 전용입니다. WACC는 과거 사실이 아니라 검토완료 가치평가 가정입니다.","proposal_sha256":""}
    out["proposal_sha256"]=_sha(_without(out,"proposal_sha256"));validate_binding_proposal_v4(out);return out


def validate_binding_proposal_v4(p:dict[str,Any])->dict[str,Any]:
    if not isinstance(p,dict) or p.get("schema_version")!=SCHEMA_VERSION_V4 or p.get("status")!=STATUS or p.get("canonical") is not False:raise CaseServiceError("WACC-aware binding proposal schema/status invalid / WACC-aware 바인딩 제안 스키마·상태 오류")
    if p.get("target")!={"draft_schema_version":"draft-case-v0.1","model":"equity_fcff"}:raise CaseServiceError("WACC-aware binding target invalid / WACC-aware 바인딩 대상 오류")
    base=p.get("base_proposal");package=p.get("wacc_package")
    if not isinstance(base,dict) or not isinstance(package,dict):raise CaseServiceError("WACC-aware base proposal/package missing / WACC-aware base proposal·package 누락")
    validate_binding_proposal_any_v3(base);_eligible_package(package)
    if p.get("base_proposal_sha256")!=base.get("proposal_sha256") or p.get("source_wacc_package_sha256")!=package.get("package_sha256"):raise CaseServiceError("WACC-aware source SHA lineage mismatch / WACC-aware source SHA lineage 불일치")
    if p.get("policy")!=_policy(base):raise CaseServiceError("WACC-aware policy/base mismatch / WACC-aware 정책·base 불일치")
    identity=p.get("identity")
    if identity!=base.get("identity") or p.get("conflicts")!=base.get("conflicts") or p.get("source_observation_sha256")!=base.get("source_observation_sha256"):raise CaseServiceError("WACC-aware proposal/base lineage mismatch / WACC-aware proposal·base lineage 불일치")
    if package.get("entity")!={"id":identity.get("entity_id"),"financial_scope":identity.get("financial_scope")} or package.get("as_of")!=p["policy"]["as_of"]:raise CaseServiceError("WACC package identity/as_of mismatch / WACC 패키지 식별·as_of 불일치")
    monetary=identity.get("monetary_unit")
    if monetary is not None and package.get("capital_currency")!=monetary:raise CaseServiceError("WACC package capital currency mismatch / WACC 패키지 자본통화 불일치")
    expected_baseline=copy.deepcopy(base["baseline_context"]);expected_baseline["wacc_assumption"]=_projection(package)
    if p.get("baseline_context")!=expected_baseline:raise CaseServiceError("WACC baseline projection mismatch / WACC baseline 투영 불일치")
    matrix=p.get("draft_input_matrix")
    if not isinstance(matrix,list) or len(matrix)!=len(MATERIAL_FIELDS) or {x.get("field") for x in matrix if isinstance(x,dict)}!=set(MATERIAL_FIELDS):raise CaseServiceError("WACC-aware binding matrix incomplete / WACC-aware 바인딩 matrix 불완전")
    base_by={x["field"]:x for x in base["draft_input_matrix"]};by={x["field"]:x for x in matrix}
    for field in MATERIAL_FIELDS:
        if field!="scenario.wacc" and by[field]!=base_by[field]:raise CaseServiceError("M24 may replace only scenario.wacc classification / M24는 scenario.wacc 판정만 변경 가능")
    if by["scenario.wacc"]!=_decision(package):raise CaseServiceError("WACC DIRECT_BIND lineage/classification mismatch / WACC DIRECT_BIND lineage·판정 불일치")
    if p.get("completeness")!=_counts(matrix):raise CaseServiceError("WACC-aware completeness mismatch / WACC-aware completeness 불일치")
    expected=_sha(_without(p,"proposal_sha256"))
    if p.get("proposal_sha256")!=expected:raise CaseServiceError("WACC-aware binding proposal SHA-256 mismatch / WACC-aware 바인딩 제안 SHA 불일치")
    return {"status":"PASS_WACC_AWARE_BINDING_PROPOSAL_VALIDATION","canonical":False,"proposal_sha256":expected,"direct_bind_count":p["completeness"]["direct_bind_count"],"unresolved_count":p["completeness"]["unresolved_count"]}


def validate_binding_proposal_any(p:dict[str,Any])->dict[str,Any]:
    if isinstance(p,dict) and p.get("schema_version")==SCHEMA_VERSION_V4:return validate_binding_proposal_v4(p)
    return validate_binding_proposal_any_v3(p)
