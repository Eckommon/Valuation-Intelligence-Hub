"""Promotion Package Web Lab / 승격 패키지 Web Lab.

The browser can build and validate deterministic in-memory staging packages from
already approved M9 candidates. Server-side package materialization is excluded;
explicit local filesystem writes remain a CLI-only operation.

브라우저는 M9 승인 Candidate에서 결정론적 메모리 스테이징 패키지를 생성·검증한다.
서버측 파일 materialization은 제외하고 명시적 로컬 파일 기록은 CLI에서만 수행한다.
"""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from valuation_hub import web as legacy_web
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.promotion_package import build_promotion_package, validate_promotion_package
from valuation_hub.web_promotion import (
    _dashboard_with_promotion_link,
    make_handler as make_promotion_handler,
)
from valuation_hub.web_product import product_layout

MAX_PACKAGE_REQUEST_BYTES = 2 * 1024 * 1024


def render_package_lab() -> str:
    body = """
<div class="breadcrumbs"><a href="/">Dashboard</a><span>›</span><strong>Promotion Package / 승격 패키지</strong></div>
<div class="section-head"><div><h2>Promotion Package Lab / 승격 패키지 랩</h2><p class="muted">Approved Candidate → deterministic tamper-evident staging package / 승인 Candidate → 결정론적 변조탐지 스테이징 패키지</p></div><span class="state-preview">STAGED · NOT CANONICAL</span></div>
<div class="card"><p class="warn"><strong>Not registry-executable yet / 아직 정식 레지스트리 실행 불가</strong></p><p>M8 Draft economics are preserved losslessly. The package explicitly declares the canonical adapter still required; this Web Lab never writes repository files. / M8 Draft 경제값을 손실 없이 보존하고 필요한 canonical adapter를 명시합니다. 이 Web Lab은 저장소 파일을 기록하지 않습니다.</p></div>
<div class="grid compact">
<label>Case ID / 사례 ID<input id="pkg-case-id" value="KR_NEW_REVIEWED_CASE"></label>
<label>Name EN<input id="pkg-name-en" value="New Reviewed Case"></label>
<label>Name KO<input id="pkg-name-ko" value="신규 검토 사례"></label>
<label>Asset class / 자산분류<input id="pkg-asset-class" value="public_equity"></label>
</div>
<label style="margin-top:14px">Approved Candidate JSON / 승인 Candidate JSON<textarea id="pkg-candidate" spellcheck="false" style="width:100%;min-height:420px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><button class="primary" onclick="buildPackage()">Build staged package / 스테이징 패키지 생성</button> <button class="primary" onclick="validatePackage()">Validate package / 패키지 검증</button></p>
<label>Promotion Package JSON / 승격 패키지 JSON<textarea id="pkg-json" spellcheck="false" style="width:100%;min-height:520px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<div id="pkg-summary" class="preview-summary"><div class="muted">Paste an already human-approved M9 Candidate. / 이미 인간 승인된 M9 Candidate를 붙여넣으세요.</div></div>
<details><summary>Diagnostics JSON / 진단 JSON</summary><pre id="pkg-output">—</pre></details>
<script>
const pc=document.getElementById('pkg-candidate'),pp=document.getElementById('pkg-json'),ps=document.getElementById('pkg-summary'),po=document.getElementById('pkg-output');
function parseArea(area,label){try{return JSON.parse(area.value)}catch(e){throw new Error(label+' JSON error / JSON 오류: '+e.message)}}
async function post(path,payload){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const j=await r.json();po.textContent=JSON.stringify(j,null,2);if(!r.ok)throw new Error(j.error||('HTTP '+r.status));return j;}
async function buildPackage(){try{const payload={candidate:parseArea(pc,'Candidate'),case_id:document.getElementById('pkg-case-id').value,display_name_en:document.getElementById('pkg-name-en').value,display_name_ko:document.getElementById('pkg-name-ko').value,asset_class:document.getElementById('pkg-asset-class').value};const j=await post('/api/package/build',payload);pp.value=JSON.stringify(j,null,2);ps.innerHTML='<div class="warn"><strong>'+j.status+'</strong><br>Package SHA-256: <code>'+j.package_sha256+'</code><br>'+j.adapter_requirement.compatibility_status+'<br><span class="muted">CANONICAL = false</span></div>'; }catch(e){ps.innerHTML='<div class="bad">'+String(e)+'</div>';}}
async function validatePackage(){try{const j=await post('/api/package/validate',parseArea(pp,'Package'));ps.innerHTML='<div class="good"><strong>PASS PACKAGE / 패키지 검증 통과</strong><br>'+j.package_sha256+'<br>'+j.next_action_ko+'<br><span class="muted">CANONICAL = false</span></div>'; }catch(e){ps.innerHTML='<div class="bad">'+String(e)+'</div>';}}
</script>
"""
    return product_layout("Promotion Package — Valuation Intelligence Hub", body)


def _dashboard_with_package_link(repo: Path) -> str:
    page = _dashboard_with_promotion_link(repo)
    marker = '<h2>Canonical cases / 정식 사례</h2>'
    banner = (
        '<div class="card" style="margin-bottom:18px;border-color:#a78bfa">'
        '<div><strong>Promotion Package / 승격 패키지</strong></div>'
        '<p>Stage an approved Candidate as deterministic tamper-evident review material without writing canonical state. / '
        '승인 Candidate를 정식 상태 기록 없이 결정론적·변조탐지형 검토 패키지로 스테이징합니다.</p>'
        '<a href="/package">Open Promotion Package Lab / 승격 패키지 랩 열기 →</a></div>'
    )
    return page.replace(marker, banner + marker, 1)


def make_handler(root: Path | None = None):
    repo = root.resolve() if root else find_repo_root()
    Base = make_promotion_handler(repo)

    class PackageHandler(Base):
        def _package_payload(self) -> dict:
            raw = self.headers.get("Content-Length", "0")
            try:
                length = int(raw)
            except ValueError as exc:
                raise CaseServiceError("invalid Content-Length / Content-Length 오류") from exc
            if length <= 0 or length > MAX_PACKAGE_REQUEST_BYTES:
                raise CaseServiceError("package request size invalid / 패키지 요청 크기 오류")
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise CaseServiceError("invalid package JSON / 패키지 JSON 오류") from exc
            if not isinstance(payload, dict):
                raise CaseServiceError("package payload must be a JSON object / 패키지 payload는 JSON 객체여야 합니다")
            return payload

        def do_GET(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            try:
                if path == "/":
                    self._send(HTTPStatus.OK, _dashboard_with_package_link(repo).encode("utf-8"), "text/html; charset=utf-8")
                    return
                if path == "/package":
                    self._send(HTTPStatus.OK, render_package_lab().encode("utf-8"), "text/html; charset=utf-8")
                    return
                super().do_GET()
            except CaseServiceError as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

        def do_POST(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            if path not in {"/api/package/build", "/api/package/validate"}:
                super().do_POST()
                return
            try:
                payload = self._package_payload()
                if path.endswith("/build"):
                    candidate = payload.get("candidate")
                    if not isinstance(candidate, dict):
                        raise CaseServiceError("candidate object required / Candidate 객체 필요")
                    result = build_promotion_package(
                        candidate,
                        case_id=payload.get("case_id"),
                        display_name_en=payload.get("display_name_en"),
                        display_name_ko=payload.get("display_name_ko"),
                        asset_class=payload.get("asset_class"),
                        root=repo,
                    )
                else:
                    result = validate_promotion_package(payload, repo)
                self._send(HTTPStatus.OK, legacy_web._json_bytes(result), "application/json; charset=utf-8")
            except CaseServiceError as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

    return PackageHandler


def serve(*, host: str = "127.0.0.1", port: int = 8765, root: Path | None = None) -> None:
    if not 0 < port < 65536:
        raise ValueError("port must be in 1..65535 / 포트 범위 오류")
    server = ThreadingHTTPServer((host, port), make_handler(root))
    print(f"Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}")
    print("Draft Lab / Draft 랩: /draft")
    print("Promotion Review / 승격 검토: /promotion")
    print("Promotion Package / 승격 패키지: /package")
    print("Press Ctrl+C to stop / 종료하려면 Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
