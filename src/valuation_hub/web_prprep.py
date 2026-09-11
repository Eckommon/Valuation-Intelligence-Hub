"""Read-only PR Preparation + source-inspection Web Labs / 읽기 전용 Web Labs.

M12 builds/validates repository change plans but exposes no apply endpoint. M13 adds
SEC source-snapshot validation and evidence-candidate extraction, also without any
browser-origin live fetch or canonical write endpoint.
"""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from valuation_hub import web as legacy_web
from valuation_hub.admission_apply import (
    build_repository_change_plan,
    validate_repository_change_plan,
)
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.sec_live import METRIC_SPECS, extract_sec_evidence_candidate, validate_source_snapshot
from valuation_hub.web_admission import (
    _dashboard_with_admission_link,
    make_handler as make_admission_handler,
)
from valuation_hub.web_product import product_layout

MAX_PR_PREP_REQUEST_BYTES = 8 * 1024 * 1024
MAX_SOURCE_INSPECT_REQUEST_BYTES = 40 * 1024 * 1024


def render_pr_prep_lab() -> str:
    body = """
<div class="breadcrumbs"><a href="/">Dashboard</a><span>›</span><strong>PR Preparation / PR 준비</strong></div>
<div class="section-head"><div><h2>PR Preparation Lab / PR 준비 랩</h2><p class="muted">M11 admission bundle → deterministic repository change plan / M11 수용 bundle → 결정론적 저장소 변경계획</p></div><span class="state-preview">PLAN ONLY · NO APPLY</span></div>
<div class="card"><p class="warn"><strong>Browser write is intentionally unavailable / 브라우저 저장소 적용은 의도적으로 제공하지 않음</strong></p><p>This page can calculate and validate the exact registry/artifact change plan against the configured repository baseline. It has no apply endpoint. Actual filesystem application requires the CLI on an explicit <code>admission/*</code> checkout/worktree. / 이 페이지는 현재 저장소 기준선에 대한 정확한 registry·산출물 변경계획만 계산·검증합니다. apply endpoint는 없으며 실제 파일 적용은 명시적 <code>admission/*</code> checkout/worktree에서 CLI로만 수행합니다.</p></div>
<label>M11 Admission Bundle JSON / M11 정식 수용 Bundle JSON<textarea id="prep-admission" spellcheck="false" style="width:100%;min-height:400px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><button class="primary" onclick="buildPlan()">Build change plan / 변경계획 생성</button> <button class="primary" onclick="validatePlan()">Validate plan / 계획 검증</button></p>
<label>Repository Change Plan JSON / 저장소 변경계획 JSON<textarea id="prep-plan" spellcheck="false" style="width:100%;min-height:480px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<div id="prep-summary" class="preview-summary"><div class="muted">Paste a valid M11 admission bundle. / 유효한 M11 정식 수용 bundle을 붙여넣으세요.</div></div>
<details><summary>Diagnostics JSON / 진단 JSON</summary><pre id="prep-output">—</pre></details>
<script>
const pa=document.getElementById('prep-admission'),pp=document.getElementById('prep-plan'),ps=document.getElementById('prep-summary'),po=document.getElementById('prep-output');
function parseArea(area,label){try{return JSON.parse(area.value)}catch(e){throw new Error(label+' JSON error / JSON 오류: '+e.message)}}
async function post(path,payload){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const j=await r.json();po.textContent=JSON.stringify(j,null,2);if(!r.ok)throw new Error(j.error||('HTTP '+r.status));return j;}
async function buildPlan(){try{const admission=parseArea(pa,'Admission');const j=await post('/api/pr-prep/plan',{admission});pp.value=JSON.stringify(j,null,2);ps.innerHTML='<div class="warn"><strong>'+j.status+'</strong><br>Plan SHA-256: <code>'+j.plan_sha256+'</code><br>Registry: <code>'+j.expected_registry_sha256+'</code> → <code>'+j.planned_registry_sha256+'</code><br><span class="muted">PLAN ONLY · CANONICAL=false</span></div>'; }catch(e){ps.innerHTML='<div class="bad">'+String(e)+'</div>';}}
async function validatePlan(){try{const j=await post('/api/pr-prep/validate',{admission:parseArea(pa,'Admission'),plan:parseArea(pp,'Plan')});ps.innerHTML='<div class="good"><strong>PASS PLAN / 변경계획 검증 통과</strong><br>'+j.case_id+' · '+j.plan_sha256+'<br>Required branch: '+j.branch_required+'<br><span class="muted">Use local CLI admission-apply on an explicit target checkout.</span></div>'; }catch(e){ps.innerHTML='<div class="bad">'+String(e)+'</div>';}}
</script>
"""
    return product_layout("PR Preparation — Valuation Intelligence Hub", body)


def render_source_lab() -> str:
    options = "".join(f'<option value="{name}">{name}</option>' for name in METRIC_SPECS)
    body = f"""
<div class="breadcrumbs"><a href="/">Dashboard</a><span>›</span><strong>SEC Source Inspector / SEC 출처 검사</strong></div>
<div class="section-head"><div><h2>SEC Source Snapshot Inspector / SEC Source Snapshot 검사기</h2><p class="muted">Validate immutable snapshots and extract unreviewed filing-grounded candidates. / 불변 snapshot 검증 및 미검토 filing 근거후보 추출</p></div><span class="state-preview">INSPECT ONLY · NO LIVE FETCH</span></div>
<div class="card"><p class="warn"><strong>No browser live fetch and no canonical write / 브라우저 live fetch·정식 기록 없음</strong></p><p>Paste a snapshot previously captured by the local CLI. Official SEC origin does not make extracted values canonical; output remains <code>EVIDENCE_CANDIDATE_UNREVIEWED</code>. / 로컬 CLI가 수집한 snapshot을 붙여넣어 검증합니다. SEC 공식 출처라는 이유만으로 정식 FACT가 되지 않으며 추출 결과는 미검토 후보로 남습니다.</p></div>
<label>Source Snapshot JSON / Source Snapshot JSON<textarea id="source-snapshot" spellcheck="false" style="width:100%;min-height:460px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<div class="grid compact" style="margin-top:14px"><label>Metric / 지표<select id="source-metric">{options}</select></label><label>Form filter / Form 필터<input id="source-form" placeholder="10-Q"></label><label>Period end / 기간말<input id="source-period-end" placeholder="YYYY-MM-DD"></label></div>
<p><button class="primary" onclick="validateSnapshot()">Validate snapshot / snapshot 검증</button> <button class="primary" onclick="extractCandidate()">Extract candidate / 후보 추출</button></p>
<div id="source-summary" class="preview-summary"><div class="muted">Snapshot inspection is read-only. / Snapshot 검사는 읽기 전용입니다.</div></div>
<pre id="source-output">—</pre>
<script>
const ss=document.getElementById('source-snapshot'),so=document.getElementById('source-output'),sm=document.getElementById('source-summary');
function snapshotObj(){{try{{return JSON.parse(ss.value)}}catch(e){{throw new Error('Snapshot JSON error / JSON 오류: '+e.message)}}}}
async function sourcePost(path,payload){{const r=await fetch(path,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(payload)}});const j=await r.json();so.textContent=JSON.stringify(j,null,2);if(!r.ok)throw new Error(j.error||('HTTP '+r.status));return j;}}
async function validateSnapshot(){{try{{const j=await sourcePost('/api/source/validate',{{snapshot:snapshotObj()}});sm.innerHTML='<div class="good"><strong>'+j.status+'</strong><br>CIK '+j.cik+'<br><code>'+j.snapshot_sha256+'</code><br><span class="muted">CANONICAL=false</span></div>';}}catch(e){{sm.innerHTML='<div class="bad">'+String(e)+'</div>';}}}}
async function extractCandidate(){{try{{const form=document.getElementById('source-form').value.trim();const period=document.getElementById('source-period-end').value.trim();const payload={{snapshot:snapshotObj(),metric:document.getElementById('source-metric').value}};if(form)payload.form=form;if(period)payload.period_end=period;const j=await sourcePost('/api/source/extract',payload);sm.innerHTML='<div class="warn"><strong>'+j.status+'</strong><br>'+j.metric+' = '+j.value+' '+j.unit+'<br>'+j.filing.form+' · '+j.filing.filed+' · '+j.filing.accession+'<br><span class="muted">UNREVIEWED · CANONICAL=false</span></div>';}}catch(e){{sm.innerHTML='<div class="bad">'+String(e)+'</div>';}}}}
</script>
"""
    return product_layout("SEC Source Inspector — Valuation Intelligence Hub", body)


def _dashboard_with_pr_prep_link(repo: Path) -> str:
    page = _dashboard_with_admission_link(repo)
    marker = '<h2>Canonical cases / 정식 사례</h2>'
    banner = (
        '<div class="card" style="margin-bottom:18px;border-color:#38bdf8">'
        '<div><strong>PR Preparation / PR 준비</strong></div>'
        '<p>Build and inspect a deterministic repository change plan. Browser apply is disabled. / '
        '결정론적 저장소 변경계획을 생성·검토합니다. 브라우저 apply는 비활성화되어 있습니다.</p>'
        '<a href="/pr-prep">Open PR Preparation Lab / PR 준비 랩 열기 →</a></div>'
        '<div class="card" style="margin-bottom:18px;border-color:#22c55e">'
        '<div><strong>SEC Source Inspector / SEC 출처 검사</strong></div>'
        '<p>Validate CLI-captured immutable SEC snapshots and extract unreviewed evidence candidates. No browser live fetch. / '
        'CLI로 수집한 불변 SEC snapshot을 검증하고 미검토 근거후보를 추출합니다. 브라우저 live fetch는 없습니다.</p>'
        '<a href="/source">Open SEC Source Inspector / SEC 출처 검사 열기 →</a></div>'
    )
    return page.replace(marker, banner + marker, 1)


def make_handler(root: Path | None = None):
    repo = root.resolve() if root else find_repo_root()
    Base = make_admission_handler(repo)

    class PRPrepHandler(Base):
        def _json_payload(self, *, max_bytes: int, label: str) -> dict:
            raw = self.headers.get("Content-Length", "0")
            try:
                length = int(raw)
            except ValueError as exc:
                raise CaseServiceError("invalid Content-Length / Content-Length 오류") from exc
            if length <= 0 or length > max_bytes:
                raise CaseServiceError(f"{label} request size invalid / {label} 요청 크기 오류")
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise CaseServiceError(f"invalid {label} JSON / {label} JSON 오류") from exc
            if not isinstance(payload, dict):
                raise CaseServiceError(f"{label} payload must be an object / {label} payload는 객체여야 합니다")
            return payload

        def do_GET(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            try:
                if path == "/":
                    self._send(HTTPStatus.OK, _dashboard_with_pr_prep_link(repo).encode("utf-8"), "text/html; charset=utf-8")
                    return
                if path == "/pr-prep":
                    self._send(HTTPStatus.OK, render_pr_prep_lab().encode("utf-8"), "text/html; charset=utf-8")
                    return
                if path == "/source":
                    self._send(HTTPStatus.OK, render_source_lab().encode("utf-8"), "text/html; charset=utf-8")
                    return
                super().do_GET()
            except CaseServiceError as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

        def do_POST(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            if path in {"/api/source/validate", "/api/source/extract"}:
                try:
                    payload = self._json_payload(max_bytes=MAX_SOURCE_INSPECT_REQUEST_BYTES, label="source-inspect")
                    snapshot = payload.get("snapshot")
                    if not isinstance(snapshot, dict):
                        raise CaseServiceError("snapshot object required / snapshot 객체 필요")
                    if path.endswith("/validate"):
                        result = validate_source_snapshot(snapshot)
                    else:
                        metric = payload.get("metric")
                        if not isinstance(metric, str):
                            raise CaseServiceError("metric required / metric 필요")
                        result = extract_sec_evidence_candidate(
                            snapshot,
                            metric,
                            form=payload.get("form"),
                            period_end=payload.get("period_end"),
                        )
                    self._send(HTTPStatus.OK, legacy_web._json_bytes(result), "application/json; charset=utf-8")
                except (CaseServiceError, ValueError) as exc:
                    self._error(path, exc, HTTPStatus.BAD_REQUEST)
                return
            if path not in {"/api/pr-prep/plan", "/api/pr-prep/validate"}:
                # No PR apply, source live-fetch, or canonical-write route exists here.
                super().do_POST()
                return
            try:
                payload = self._json_payload(max_bytes=MAX_PR_PREP_REQUEST_BYTES, label="PR-prep")
                admission = payload.get("admission")
                if not isinstance(admission, dict):
                    raise CaseServiceError("admission object required / admission 객체 필요")
                if path.endswith("/plan"):
                    result = build_repository_change_plan(admission, repo)
                else:
                    plan = payload.get("plan")
                    if not isinstance(plan, dict):
                        raise CaseServiceError("plan object required / plan 객체 필요")
                    result = validate_repository_change_plan(plan, admission, repo)
                self._send(HTTPStatus.OK, legacy_web._json_bytes(result), "application/json; charset=utf-8")
            except (CaseServiceError, ValueError) as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

    return PRPrepHandler


def serve(*, host: str = "127.0.0.1", port: int = 8765, root: Path | None = None) -> None:
    if not 0 < port < 65536:
        raise ValueError("port must be in 1..65535 / 포트 범위 오류")
    server = ThreadingHTTPServer((host, port), make_handler(root))
    print(f"Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}")
    print("Draft Lab / Draft 랩: /draft")
    print("Promotion Review / 승격 검토: /promotion")
    print("Promotion Package / 승격 패키지: /package")
    print("Canonical Admission / 정식 수용: /admission")
    print("PR Preparation / PR 준비: /pr-prep (plan only / 계획 전용)")
    print("SEC Source Inspector / SEC 출처 검사: /source (inspect only / 검사 전용)")
    print("Press Ctrl+C to stop / 종료하려면 Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
