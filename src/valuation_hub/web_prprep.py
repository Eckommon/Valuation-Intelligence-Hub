"""Read-only PR Preparation Web Lab / 읽기 전용 PR 준비 Web Lab.

M12 Web can build and validate repository change plans against the configured
repository baseline. It intentionally exposes no apply endpoint; guarded file
application is a local CLI/service operation on an explicit `admission/*` target.
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
from valuation_hub.web_admission import (
    _dashboard_with_admission_link,
    make_handler as make_admission_handler,
)
from valuation_hub.web_product import product_layout

MAX_PR_PREP_REQUEST_BYTES = 8 * 1024 * 1024


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


def _dashboard_with_pr_prep_link(repo: Path) -> str:
    page = _dashboard_with_admission_link(repo)
    marker = '<h2>Canonical cases / 정식 사례</h2>'
    banner = (
        '<div class="card" style="margin-bottom:18px;border-color:#38bdf8">'
        '<div><strong>PR Preparation / PR 준비</strong></div>'
        '<p>Build and inspect a deterministic repository change plan. Browser apply is disabled. / '
        '결정론적 저장소 변경계획을 생성·검토합니다. 브라우저 apply는 비활성화되어 있습니다.</p>'
        '<a href="/pr-prep">Open PR Preparation Lab / PR 준비 랩 열기 →</a></div>'
    )
    return page.replace(marker, banner + marker, 1)


def make_handler(root: Path | None = None):
    repo = root.resolve() if root else find_repo_root()
    Base = make_admission_handler(repo)

    class PRPrepHandler(Base):
        def _prep_payload(self) -> dict:
            raw = self.headers.get("Content-Length", "0")
            try:
                length = int(raw)
            except ValueError as exc:
                raise CaseServiceError("invalid Content-Length / Content-Length 오류") from exc
            if length <= 0 or length > MAX_PR_PREP_REQUEST_BYTES:
                raise CaseServiceError("PR-prep request size invalid / PR 준비 요청 크기 오류")
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise CaseServiceError("invalid PR-prep JSON / PR 준비 JSON 오류") from exc
            if not isinstance(payload, dict):
                raise CaseServiceError("PR-prep payload must be an object / PR 준비 payload는 객체여야 합니다")
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
                super().do_GET()
            except CaseServiceError as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

        def do_POST(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            if path not in {"/api/pr-prep/plan", "/api/pr-prep/validate"}:
                # No /apply route exists. Unknown routes inherit earlier read/preview labs.
                super().do_POST()
                return
            try:
                payload = self._prep_payload()
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
    print("Press Ctrl+C to stop / 종료하려면 Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
