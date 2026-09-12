"""Stable CLI entry dispatcher / 안정적 CLI 진입 dispatcher."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from valuation_hub import cli as legacy_cli
from valuation_hub.binding_apply import build_binding_approval, validate_binding_approval, apply_binding_approval, validate_bound_draft_result
from valuation_hub.case_service import CaseServiceError
from valuation_hub.dart_live import DART_METRIC_SPECS, capture_dart_snapshot, extract_dart_evidence_candidate, load_dart_snapshot, materialize_dart_snapshot, validate_dart_snapshot
from valuation_hub.debt_binding import build_debt_binding_context, build_debt_date_assertion, validate_debt_binding_context, validate_debt_date_assertion
from valuation_hub.debt_components import (
    CORE_COMPONENTS,
    SEC_COMPONENT_SUPPORT,
    aggregate_interest_bearing_debt,
    extract_dart_debt_component_candidate,
    extract_sec_debt_component_candidate,
    normalize_debt_component_candidate,
    validate_debt_component_observation,
    validate_interest_bearing_debt_evidence,
)
from valuation_hub.debt_draft_binding import build_binding_proposal_with_debt, validate_binding_proposal_any
from valuation_hub.derived_financial import derive_historical_net_income_margin, derive_historical_operating_margin, validate_derived_financial_evidence
from valuation_hub.draft_binding import build_binding_proposal
from valuation_hub.financial_normalization import DURATION_ANNUAL, DURATION_QUARTER, DURATION_YTD, normalize_dart_candidate, normalize_sec_candidate, reconcile_same_period, ttm_annual_bridge, ttm_four_quarters, validate_financial_observation, validate_ttm_result
from valuation_hub.web_debt import serve as serve_web

DART_COMMANDS = {"dart-fetch", "dart-snapshot-validate", "dart-extract"}
NORMALIZATION_COMMANDS = {"normalize-sec", "normalize-dart", "normalize-validate", "ttm-four-quarters", "ttm-annual-bridge", "ttm-validate", "normalize-reconcile"}
BINDING_COMMANDS = {"binding-build", "binding-build-with-debt", "binding-validate"}
BINDING_APPLY_COMMANDS = {"binding-approval-build", "binding-approval-validate", "binding-apply", "bound-draft-validate"}
DERIVED_COMMANDS = {"derive-operating-margin", "derive-net-margin", "derived-validate"}
DEBT_COMMANDS = {
    "debt-sec-extract", "debt-dart-extract", "debt-normalize", "debt-component-validate", "debt-aggregate", "debt-validate",
    "debt-date-assertion-build", "debt-date-assertion-validate", "debt-binding-context-build", "debt-binding-context-validate",
}


def _dump(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _load_json(path: Path, label: str) -> Any:
    try: return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc: raise CaseServiceError(f"{label} file not found / {label} 파일 없음: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc: raise CaseServiceError(f"{label} read failed / {label} 읽기 실패: {path}") from exc


def _load_object(path: Path, label: str) -> dict[str, Any]:
    payload = _load_json(path, label)
    if not isinstance(payload, dict): raise CaseServiceError(f"{label} must be a JSON object / {label} JSON 객체 필요")
    return payload


def _load_object_list(path: Path, label: str) -> list[dict[str, Any]]:
    payload = _load_json(path, label)
    if not isinstance(payload, list) or not payload or not all(isinstance(x, dict) for x in payload): raise CaseServiceError(f"{label} must be a non-empty JSON object array / {label} 비어있지 않은 JSON 객체 배열 필요")
    return payload


def _command(argv: list[str]) -> str | None:
    known = DART_COMMANDS | NORMALIZATION_COMMANDS | BINDING_COMMANDS | BINDING_APPLY_COMMANDS | DERIVED_COMMANDS | DEBT_COMMANDS | {"web"}
    return next((token for token in argv if token in known), None)


def _dart_parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(prog="vih"); p.add_argument("--root",type=Path,default=None); p.add_argument("--json",action="store_true",dest="as_json"); s=p.add_subparsers(dest="command",required=True)
    f=s.add_parser("dart-fetch"); f.add_argument("corp_code"); f.add_argument("--bsns-year",required=True); f.add_argument("--reprt-code",required=True,choices=("11013","11012","11014","11011")); f.add_argument("--fs-div",required=True,choices=("CFS","OFS")); f.add_argument("--api-key",required=True); f.add_argument("--output",type=Path,required=True)
    s.add_parser("dart-snapshot-validate").add_argument("file",type=Path); e=s.add_parser("dart-extract"); e.add_argument("file",type=Path); e.add_argument("metric",choices=tuple(DART_METRIC_SPECS)); e.add_argument("--statement-section",default=None,choices=("BS","IS","CIS","CF","SCE")); return p


def _normalization_parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(prog="vih"); p.add_argument("--root",type=Path,default=None); p.add_argument("--json",action="store_true",dest="as_json"); s=p.add_subparsers(dest="command",required=True)
    x=s.add_parser("normalize-sec"); x.add_argument("file",type=Path); x.add_argument("--period-kind",choices=(DURATION_QUARTER,DURATION_YTD,DURATION_ANNUAL),default=None)
    x=s.add_parser("normalize-dart"); x.add_argument("file",type=Path); x.add_argument("--amount-basis",choices=("CURRENT","CUMULATIVE"),default="CURRENT")
    s.add_parser("normalize-validate").add_argument("file",type=Path); s.add_parser("ttm-four-quarters").add_argument("files",nargs=4,type=Path)
    x=s.add_parser("ttm-annual-bridge"); x.add_argument("prior_annual",type=Path); x.add_argument("current_ytd",type=Path); x.add_argument("prior_ytd",type=Path)
    s.add_parser("ttm-validate").add_argument("file",type=Path); s.add_parser("normalize-reconcile").add_argument("files",nargs="+",type=Path); return p


def _binding_parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(prog="vih"); p.add_argument("--root",type=Path,default=None); p.add_argument("--json",action="store_true",dest="as_json"); s=p.add_subparsers(dest="command",required=True)
    b=s.add_parser("binding-build"); b.add_argument("observations",type=Path); b.add_argument("--as-of",required=True); b.add_argument("--max-age-days",type=int,default=550)
    b=s.add_parser("binding-build-with-debt"); b.add_argument("observations",type=Path); b.add_argument("debt_context",type=Path); b.add_argument("--as-of",required=True); b.add_argument("--max-age-days",type=int,default=550)
    s.add_parser("binding-validate").add_argument("file",type=Path); return p


def _binding_apply_parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(prog="vih"); p.add_argument("--root",type=Path,default=None); p.add_argument("--json",action="store_true",dest="as_json"); s=p.add_subparsers(dest="command",required=True)
    a=s.add_parser("binding-approval-build"); a.add_argument("proposal",type=Path); a.add_argument("draft",type=Path); a.add_argument("--reviewer",required=True); a.add_argument("--target-entity-id",required=True); a.add_argument("--target-financial-scope",required=True); a.add_argument("--approved-field",action="append",default=[]); a.add_argument("--approved-at",required=True)
    a=s.add_parser("binding-approval-validate"); a.add_argument("approval",type=Path); a.add_argument("proposal",type=Path); a.add_argument("draft",type=Path)
    a=s.add_parser("binding-apply"); a.add_argument("proposal",type=Path); a.add_argument("draft",type=Path); a.add_argument("approval",type=Path)
    s.add_parser("bound-draft-validate").add_argument("result",type=Path); return p


def _derived_parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(prog="vih"); p.add_argument("--root",type=Path,default=None); p.add_argument("--json",action="store_true",dest="as_json"); s=p.add_subparsers(dest="command",required=True)
    d=s.add_parser("derive-operating-margin",help="Derive historical operating margin / 역사적 영업마진 파생"); d.add_argument("operating_income",type=Path); d.add_argument("revenue",type=Path)
    d=s.add_parser("derive-net-margin",help="Derive historical net-income margin / 역사적 순이익률 파생"); d.add_argument("net_income",type=Path); d.add_argument("revenue",type=Path)
    s.add_parser("derived-validate",help="Validate derived financial evidence / 파생재무근거 검증").add_argument("file",type=Path); return p


def _debt_parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(prog="vih"); p.add_argument("--root",type=Path,default=None); p.add_argument("--json",action="store_true",dest="as_json"); s=p.add_subparsers(dest="command",required=True)
    x=s.add_parser("debt-sec-extract",help="Extract exact SEC debt component / SEC debt 구성요소 추출"); x.add_argument("snapshot",type=Path); x.add_argument("metric",choices=tuple(sorted(SEC_COMPONENT_SUPPORT))); x.add_argument("--form",default=None); x.add_argument("--period-end",default=None)
    x=s.add_parser("debt-dart-extract",help="Extract exact OpenDART debt component / OpenDART debt 구성요소 추출"); x.add_argument("snapshot",type=Path); x.add_argument("metric",choices=CORE_COMPONENTS)
    s.add_parser("debt-normalize",help="Normalize debt component candidate / debt 구성요소 정규화").add_argument("candidate",type=Path)
    s.add_parser("debt-component-validate",help="Validate normalized debt component / 정규화 debt 구성요소 검증").add_argument("file",type=Path)
    s.add_parser("debt-aggregate",help="Aggregate explicit debt components / 명시적 이자부채 구성요소 집계").add_argument("observations",type=Path)
    s.add_parser("debt-validate",help="Validate interest-bearing debt evidence / 이자부채 근거 검증").add_argument("file",type=Path)
    x=s.add_parser("debt-date-assertion-build",help="Human-assert exact period end for REPORT_STAGE_ONLY debt / debt 기간말 인간승인"); x.add_argument("debt",type=Path); x.add_argument("--reviewer",required=True); x.add_argument("--approved-at",required=True); x.add_argument("--asserted-period-end",required=True); x.add_argument("--review-basis",required=True)
    x=s.add_parser("debt-date-assertion-validate"); x.add_argument("assertion",type=Path); x.add_argument("debt",type=Path)
    x=s.add_parser("debt-binding-context-build"); x.add_argument("debt",type=Path); x.add_argument("--as-of",required=True); x.add_argument("--max-age-days",type=int,default=550); x.add_argument("--date-assertion",type=Path,default=None)
    s.add_parser("debt-binding-context-validate").add_argument("file",type=Path)
    return p


def _web_parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(prog="vih"); p.add_argument("--root",type=Path,default=None); p.add_argument("--json",action="store_true",dest="as_json"); s=p.add_subparsers(dest="command",required=True); w=s.add_parser("web"); w.add_argument("--host",default="127.0.0.1"); w.add_argument("--port",type=int,default=8765); return p


def _error(args: Any, exc: Exception) -> int:
    _dump({"ok":False,"error":str(exc)}) if getattr(args,"as_json",False) else print(f"ERROR / 오류: {exc}",file=sys.stderr); return 2


def _run_dart(argv:list[str])->int:
    a=_dart_parser().parse_args(argv)
    try:
        if a.command=="dart-fetch": _dump(materialize_dart_snapshot(capture_dart_snapshot(a.corp_code,a.bsns_year,a.reprt_code,a.fs_div,api_key=a.api_key),a.output,a.root)); return 0
        if a.command=="dart-snapshot-validate": _dump(validate_dart_snapshot(load_dart_snapshot(a.file))); return 0
        if a.command=="dart-extract": _dump(extract_dart_evidence_candidate(load_dart_snapshot(a.file),a.metric,statement_section=a.statement_section)); return 0
        raise CaseServiceError("unsupported OpenDART command / 미지원 OpenDART 명령")
    except (CaseServiceError,ValueError,OSError) as exc: return _error(a,exc)


def _run_normalization(argv:list[str])->int:
    a=_normalization_parser().parse_args(argv)
    try:
        if a.command=="normalize-sec": _dump(normalize_sec_candidate(_load_object(a.file,"SEC evidence candidate"),declared_period_kind=a.period_kind)); return 0
        if a.command=="normalize-dart": _dump(normalize_dart_candidate(_load_object(a.file,"OpenDART evidence candidate"),amount_basis=a.amount_basis)); return 0
        if a.command=="normalize-validate": _dump(validate_financial_observation(_load_object(a.file,"financial observation"))); return 0
        if a.command=="ttm-four-quarters": _dump(ttm_four_quarters([_load_object(x,"financial observation") for x in a.files])); return 0
        if a.command=="ttm-annual-bridge": _dump(ttm_annual_bridge(_load_object(a.prior_annual,"prior annual observation"),_load_object(a.current_ytd,"current YTD observation"),_load_object(a.prior_ytd,"prior YTD observation"))); return 0
        if a.command=="ttm-validate": _dump(validate_ttm_result(_load_object(a.file,"TTM result"))); return 0
        if a.command=="normalize-reconcile": _dump(reconcile_same_period([_load_object(x,"financial observation") for x in a.files])); return 0
        raise CaseServiceError("unsupported normalization command / 미지원 정규화 명령")
    except (CaseServiceError,ValueError,OSError) as exc: return _error(a,exc)


def _run_binding(argv:list[str])->int:
    a=_binding_parser().parse_args(argv)
    try:
        if a.command=="binding-build": _dump(build_binding_proposal(_load_object_list(a.observations,"normalized observations"),as_of=a.as_of,max_age_days=a.max_age_days)); return 0
        if a.command=="binding-build-with-debt": _dump(build_binding_proposal_with_debt(_load_object_list(a.observations,"normalized observations"),_load_object(a.debt_context,"debt binding context"),as_of=a.as_of,max_age_days=a.max_age_days)); return 0
        if a.command=="binding-validate": _dump(validate_binding_proposal_any(_load_object(a.file,"binding proposal"))); return 0
        raise CaseServiceError("unsupported binding command / 미지원 바인딩 명령")
    except (CaseServiceError,ValueError,OSError) as exc: return _error(a,exc)


def _run_binding_apply(argv:list[str])->int:
    a=_binding_apply_parser().parse_args(argv)
    try:
        if a.command=="binding-approval-build": _dump(build_binding_approval(_load_object(a.proposal,"binding proposal"),_load_object(a.draft,"Draft"),reviewer=a.reviewer,target_entity_id=a.target_entity_id,target_financial_scope=a.target_financial_scope,approved_fields=a.approved_field,approved_at=a.approved_at)); return 0
        if a.command=="binding-approval-validate": _dump(validate_binding_approval(_load_object(a.approval,"binding approval"),_load_object(a.proposal,"binding proposal"),_load_object(a.draft,"Draft"))); return 0
        if a.command=="binding-apply": _dump(apply_binding_approval(_load_object(a.proposal,"binding proposal"),_load_object(a.draft,"Draft"),_load_object(a.approval,"binding approval"))); return 0
        if a.command=="bound-draft-validate": _dump(validate_bound_draft_result(_load_object(a.result,"bound Draft result"))); return 0
        raise CaseServiceError("unsupported binding apply command / 미지원 바인딩 적용 명령")
    except (CaseServiceError,ValueError,OSError) as exc: return _error(a,exc)


def _run_derived(argv:list[str])->int:
    a=_derived_parser().parse_args(argv)
    try:
        if a.command=="derive-operating-margin": _dump(derive_historical_operating_margin(_load_object(a.operating_income,"operating income observation"),_load_object(a.revenue,"revenue observation"))); return 0
        if a.command=="derive-net-margin": _dump(derive_historical_net_income_margin(_load_object(a.net_income,"net income observation"),_load_object(a.revenue,"revenue observation"))); return 0
        if a.command=="derived-validate": _dump(validate_derived_financial_evidence(_load_object(a.file,"derived financial evidence"))); return 0
        raise CaseServiceError("unsupported derived command / 미지원 파생근거 명령")
    except (CaseServiceError,ValueError,OSError) as exc: return _error(a,exc)


def _run_debt(argv:list[str])->int:
    a=_debt_parser().parse_args(argv)
    try:
        if a.command=="debt-sec-extract": _dump(extract_sec_debt_component_candidate(_load_object(a.snapshot,"SEC source snapshot"),a.metric,form=a.form,period_end=a.period_end)); return 0
        if a.command=="debt-dart-extract": _dump(extract_dart_debt_component_candidate(_load_object(a.snapshot,"OpenDART source snapshot"),a.metric)); return 0
        if a.command=="debt-normalize": _dump(normalize_debt_component_candidate(_load_object(a.candidate,"debt component candidate"))); return 0
        if a.command=="debt-component-validate": _dump(validate_debt_component_observation(_load_object(a.file,"debt component observation"))); return 0
        if a.command=="debt-aggregate": _dump(aggregate_interest_bearing_debt(_load_object_list(a.observations,"debt component observations"))); return 0
        if a.command=="debt-validate": _dump(validate_interest_bearing_debt_evidence(_load_object(a.file,"interest-bearing debt evidence"))); return 0
        if a.command=="debt-date-assertion-build": _dump(build_debt_date_assertion(_load_object(a.debt,"interest-bearing debt evidence"),reviewer=a.reviewer,approved_at=a.approved_at,asserted_period_end=a.asserted_period_end,review_basis=a.review_basis)); return 0
        if a.command=="debt-date-assertion-validate": _dump(validate_debt_date_assertion(_load_object(a.assertion,"debt date assertion"),_load_object(a.debt,"interest-bearing debt evidence"))); return 0
        if a.command=="debt-binding-context-build":
            assertion=_load_object(a.date_assertion,"debt date assertion") if a.date_assertion else None
            _dump(build_debt_binding_context(_load_object(a.debt,"interest-bearing debt evidence"),as_of=a.as_of,max_age_days=a.max_age_days,date_assertion=assertion)); return 0
        if a.command=="debt-binding-context-validate": _dump(validate_debt_binding_context(_load_object(a.file,"debt binding context"))); return 0
        raise CaseServiceError("unsupported debt command / 미지원 이자부채 명령")
    except (CaseServiceError,ValueError,OSError) as exc: return _error(a,exc)


def _run_web(argv:list[str])->int:
    a=_web_parser().parse_args(argv)
    try:
        if a.as_json: raise CaseServiceError("--json is not valid with web / web 명령은 --json을 지원하지 않습니다")
        serve_web(host=a.host,port=a.port,root=a.root); return 0
    except (CaseServiceError,ValueError,OSError) as exc: return _error(a,exc)


def main(argv:list[str]|None=None)->int:
    values=list(sys.argv[1:] if argv is None else argv); command=_command(values)
    if command in DART_COMMANDS: return _run_dart(values)
    if command in NORMALIZATION_COMMANDS: return _run_normalization(values)
    if command in BINDING_COMMANDS: return _run_binding(values)
    if command in BINDING_APPLY_COMMANDS: return _run_binding_apply(values)
    if command in DERIVED_COMMANDS: return _run_derived(values)
    if command in DEBT_COMMANDS: return _run_debt(values)
    if command=="web": return _run_web(values)
    return legacy_cli.main(values)

if __name__=="__main__": raise SystemExit(main())
