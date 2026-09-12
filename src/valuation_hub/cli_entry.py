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
from valuation_hub.derived_financial import derive_historical_net_income_margin, derive_historical_operating_margin, validate_derived_financial_evidence
from valuation_hub.draft_binding import build_binding_proposal, validate_binding_proposal
from valuation_hub.financial_normalization import DURATION_ANNUAL, DURATION_QUARTER, DURATION_YTD, normalize_dart_candidate, normalize_sec_candidate, reconcile_same_period, ttm_annual_bridge, ttm_four_quarters, validate_financial_observation, validate_ttm_result
from valuation_hub.web_derived import serve as serve_web

DART_COMMANDS = {"dart-fetch", "dart-snapshot-validate", "dart-extract"}
NORMALIZATION_COMMANDS = {"normalize-sec", "normalize-dart", "normalize-validate", "ttm-four-quarters", "ttm-annual-bridge", "ttm-validate", "normalize-reconcile"}
BINDING_COMMANDS = {"binding-build", "binding-validate"}
BINDING_APPLY_COMMANDS = {"binding-approval-build", "binding-approval-validate", "binding-apply", "bound-draft-validate"}
DERIVED_COMMANDS = {"derive-operating-margin", "derive-net-margin", "derived-validate"}


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
    known = DART_COMMANDS | NORMALIZATION_COMMANDS | BINDING_COMMANDS | BINDING_APPLY_COMMANDS | DERIVED_COMMANDS | {"web"}
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
    s.add_parser("derived-validate",help="Validate derived financial evidence / 파생재무근거 검증").add_argument("file",type=Path)
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
        if a.command=="binding-validate": _dump(validate_binding_proposal(_load_object(a.file,"binding proposal"))); return 0
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
    if command=="web": return _run_web(values)
    return legacy_cli.main(values)

if __name__=="__main__": raise SystemExit(main())
