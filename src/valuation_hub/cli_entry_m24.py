"""M24 additive CLI wrapper / M24 추가형 CLI wrapper.

Only M24 commands and v0.4-aware binding validation are intercepted. All older
commands delegate unchanged to the M23 dispatcher.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from valuation_hub import cli_entry as prior_cli
from valuation_hub.case_service import CaseServiceError
from valuation_hub.wacc_assumption import (
    REQUIRED_METRICS,SOURCE_CLAIM_CLASSES,SOURCE_TIERS,
    build_wacc_candidate,build_wacc_review_assertion,build_wacc_source_input,finalize_reviewed_wacc,
    validate_reviewed_wacc,validate_wacc_candidate,validate_wacc_review_assertion,validate_wacc_source_input,
)
from valuation_hub.wacc_draft_binding import build_binding_proposal_with_wacc,validate_binding_proposal_any
from valuation_hub.web_wacc import serve as serve_web

WACC_COMMANDS={"wacc-source-build","wacc-source-validate","wacc-candidate-build","wacc-candidate-validate","wacc-review-build","wacc-review-validate","wacc-finalize","wacc-validate","binding-build-with-wacc"}
INTERCEPT=WACC_COMMANDS|{"binding-validate","web"}


def _dump(v:Any)->None:print(json.dumps(v,ensure_ascii=False,indent=2,sort_keys=True))
def _load(path:Path,label:str)->Any:
    try:return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:raise CaseServiceError(f"{label} file not found / {label} 파일 없음: {path}") from exc
    except (OSError,json.JSONDecodeError) as exc:raise CaseServiceError(f"{label} read failed / {label} 읽기 실패: {path}") from exc
def _obj(path:Path,label:str)->dict[str,Any]:
    v=_load(path,label)
    if not isinstance(v,dict):raise CaseServiceError(f"{label} JSON object required / {label} JSON 객체 필요")
    return v
def _arr(path:Path,label:str)->list[dict[str,Any]]:
    v=_load(path,label)
    if not isinstance(v,list) or not v or not all(isinstance(x,dict) for x in v):raise CaseServiceError(f"{label} non-empty object array required / {label} 비어있지 않은 객체배열 필요")
    return v

def _command(argv:list[str])->str|None:return next((x for x in argv if x in INTERCEPT),None)
def _error(args:Any,exc:Exception)->int:
    _dump({"ok":False,"error":str(exc)}) if getattr(args,"as_json",False) else print(f"ERROR / 오류: {exc}",file=sys.stderr);return 2


def _parser()->argparse.ArgumentParser:
    p=argparse.ArgumentParser(prog='vih');p.add_argument('--root',type=Path,default=None);p.add_argument('--json',action='store_true',dest='as_json');s=p.add_subparsers(dest='command',required=True)
    x=s.add_parser('wacc-source-build');x.add_argument('--metric',required=True,choices=REQUIRED_METRICS);x.add_argument('--value',required=True,type=float);x.add_argument('--unit',required=True);x.add_argument('--observed-on',required=True);x.add_argument('--claim-class',required=True,choices=SOURCE_CLAIM_CLASSES);x.add_argument('--source-publisher',required=True);x.add_argument('--source-type',required=True);x.add_argument('--source-tier',required=True,choices=SOURCE_TIERS);x.add_argument('--source-locator',required=True);x.add_argument('--source-sha256',required=True)
    s.add_parser('wacc-source-validate').add_argument('file',type=Path)
    x=s.add_parser('wacc-candidate-build');x.add_argument('inputs',type=Path);x.add_argument('--entity-id',required=True);x.add_argument('--financial-scope',required=True);x.add_argument('--capital-currency',required=True);x.add_argument('--as-of',required=True);x.add_argument('--scenario-name',action='append',required=True)
    s.add_parser('wacc-candidate-validate').add_argument('file',type=Path)
    x=s.add_parser('wacc-review-build');x.add_argument('candidate',type=Path);x.add_argument('--reviewer',required=True);x.add_argument('--approved-at',required=True);x.add_argument('--review-basis',required=True)
    x=s.add_parser('wacc-review-validate');x.add_argument('assertion',type=Path);x.add_argument('candidate',type=Path)
    x=s.add_parser('wacc-finalize');x.add_argument('candidate',type=Path);x.add_argument('assertion',type=Path)
    s.add_parser('wacc-validate').add_argument('file',type=Path)
    x=s.add_parser('binding-build-with-wacc');x.add_argument('base_proposal',type=Path);x.add_argument('wacc_package',type=Path)
    s.add_parser('binding-validate').add_argument('file',type=Path)
    w=s.add_parser('web');w.add_argument('--host',default='127.0.0.1');w.add_argument('--port',type=int,default=8765)
    return p


def _run(argv:list[str])->int:
    a=_parser().parse_args(argv)
    try:
        if a.command=='wacc-source-build':_dump(build_wacc_source_input(metric=a.metric,value=a.value,unit=a.unit,observed_on=a.observed_on,claim_class=a.claim_class,source_publisher=a.source_publisher,source_type=a.source_type,source_tier=a.source_tier,source_locator=a.source_locator,source_sha256=a.source_sha256));return 0
        if a.command=='wacc-source-validate':_dump(validate_wacc_source_input(_obj(a.file,'WACC source input')));return 0
        if a.command=='wacc-candidate-build':_dump(build_wacc_candidate(_arr(a.inputs,'WACC source inputs'),entity_id=a.entity_id,financial_scope=a.financial_scope,capital_currency=a.capital_currency,as_of=a.as_of,scenario_names=a.scenario_name));return 0
        if a.command=='wacc-candidate-validate':_dump(validate_wacc_candidate(_obj(a.file,'WACC candidate')));return 0
        if a.command=='wacc-review-build':_dump(build_wacc_review_assertion(_obj(a.candidate,'WACC candidate'),reviewer=a.reviewer,approved_at=a.approved_at,review_basis=a.review_basis));return 0
        if a.command=='wacc-review-validate':_dump(validate_wacc_review_assertion(_obj(a.assertion,'WACC review assertion'),_obj(a.candidate,'WACC candidate')));return 0
        if a.command=='wacc-finalize':_dump(finalize_reviewed_wacc(_obj(a.candidate,'WACC candidate'),_obj(a.assertion,'WACC review assertion')));return 0
        if a.command=='wacc-validate':_dump(validate_reviewed_wacc(_obj(a.file,'reviewed WACC package')));return 0
        if a.command=='binding-build-with-wacc':_dump(build_binding_proposal_with_wacc(_obj(a.base_proposal,'base binding proposal'),_obj(a.wacc_package,'reviewed WACC package')));return 0
        if a.command=='binding-validate':_dump(validate_binding_proposal_any(_obj(a.file,'binding proposal')));return 0
        if a.command=='web':
            if a.as_json:raise CaseServiceError('--json is not valid with web / web 명령은 --json을 지원하지 않습니다')
            serve_web(host=a.host,port=a.port,root=a.root);return 0
        raise CaseServiceError('unsupported M24 command / 미지원 M24 명령')
    except (CaseServiceError,ValueError,OSError) as exc:return _error(a,exc)


def main(argv:list[str]|None=None)->int:
    values=list(sys.argv[1:] if argv is None else argv)
    if _command(values) is not None:return _run(values)
    return prior_cli.main(values)

if __name__=='__main__':raise SystemExit(main())
