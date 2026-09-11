"""Canonical Admission Web Lab / 정식 수용 Web Lab.

The browser can build and validate deterministic M11 admission bundles from
already validated M10 promotion packages. This adapter never writes registry or
analysis files; actual canonicalization remains a separately reviewed PR action.
"""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from valuation_hub import web as legacy_web
from valuation_hub.admission import build_admission_bundle, validate_admission_bundle
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.web_package import (
    _dashboard_with_package_link,
    make_handler as make_package_handler,
)
from valuation_hub.web_product import product_layout

MAX_ADMISSION_REQUEST_BYTES = 4 * 1024 * 1024


def render_admission_lab() -> str:
    body = """
<div class="breadcrumbs"><a href="/">Dashboard</a><span>›</span><strong>Canonical Admission / 정식 수용</strong></div>
<div class="section-head"><div><h2>Canonical Admission Lab / 정식 수용 랩</h2><p class="muted">M10 staged package → deterministic proposed canonical artifacts / M10 스테이징 패키지 → 결정론적 정식 제안 산출물</p></div><span class="state-preview">PROPOSED · NOT MERGED</span></div>
<div class="card"><p class="warn"><strong>Review-only boundary / 검토 전용 경계</strong></p><p>This Web Lab does not modify <code>registry/cases.json</code> or <code>analyses/</code>. A bundle becomes canonical only after the exact proposed artifacts are reviewed, committed, pass CI, and are merged. / 이 Web Lab은 정식 레지스트리나 분석경로를 변경하지 않습니다. 정확한 제안 산출물이 별도 PR에서 검토·CI·병합된 이후에만 정식이 됩니다.</p></div>
<label>M10 Promotion Package JSON / M10 승격 패키지 JSON<textarea id="adm-package" spellcheck="false" style="width:100%;min-height:440px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><button class="primary" onclick="buildAdmission()">Build admission bundle / 정식 수용 bundle 생성</button> <button class="primary" onclick="validateAdmission()">Validate admission bundle / 수용 bundle 검증</button></p>
<label>Admission Bundle JSON / 정식 수용 Bundle JSON<textarea id="adm-json" spellcheck="false" style="width:100%;min-height:560px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<div id="adm-summary" class="preview-summary"><div class="muted">Paste a valid M10 package. / 유효한 M10 패키지를 붙여넣으세요.</div></div>
<details><summary>Diagnostics JSON / 진단 JSON</summary><pre id="adm-output">—</pre></details>
<script>
const ap=document.getElementById('adm-package'),ab=document.getElementById('adm-json'),as=document.getElementById('adm-summary'),ao=document.getElementById('adm-output');
function parseArea(area,label){try{return JSON.parse(area.value)}catch(e){throw new Error(label+' JSON error / JSON 오류: '+e.message)}}
async function post(path,payload){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const j=await r.json();ao.textContent=JSON.stringify(j,null,2);if(!r.ok)throw new Error(j.error||('HTTP '+r.status));return j;}
async function buildAdmission(){try{const j=await post('/api/admission/build',parseArea(ap,'Package'));ab.value=JSON.stringify(j,null,2);as.innerHTML='<div class="warn"><strong>'+j.status+'</strong><br>Bundle SHA-256: <code>'+j.bundle_sha256+'</code><br>Adapter: <code>'+j.registry_entry.adapter+'</code><br><span class="muted">Bundle canonical = false · proposed files declare canonical=true only after exact PR merge.</span></div>'; }catch(e){as.innerHTML='<div class="bad">'+String(e)+'</div>';}}
async function validateAdmission(){try{const j=await post('/api/admission/validate',parseArea(ab,'Admission bundle'));as.innerHTML='<div class="good"><strong>PASS ADMISSION / 수용 bundle 검증 통과</strong><br>'+j.case_id+' · '+j.adapter+'<br>'+j.next_action_ko+'<br><span class="muted">Bundle canonical = false</span></div>'; }catch(e){as.innerHTML='<div class="bad">'+String(e)+'</div>';}}
</script>
"""
    return product_layout("Canonical Admission — Valuation Intelligence Hub", body)


def _dashboard_with_admission_link(repo: Path) -> str:
    page = _dashboard_with_package_link(repo)
    marker = '<h2>Canonical cases / 정식 사례</h2>'
    banner = (
        '<div class="card" style="margin-bottom:18px;border-color:#22c55e">'
        '<div><strong>Canonical Admission / 정식 수용</strong></div>'
        '<p>Convert a validated M10 package into deterministic proposed canonical artifacts without writing repository state. / '
        '검증된 M10 패키지를 저장소 변경 없이 결정론적 정식 제안 산출물로 변환합니다.</p>'
        '<a href="/admission">Open Canonical Admission Lab / 정식 수용 랩 열기 →</a></div>'
    )
    return page.replace(marker, banner + marker, 1)


def make_handler(root: Path | None = None):
    repo = root.resolve() if root else find_repo_root()
    Base = make_package_handler(repo)

    class AdmissionHandler(Base):
        def _admission_payload(self) -> dict:
            raw = self.headers.get("Content-Length", "0")
            try:
                length = int(raw)
            except ValueError as exc:
                raise CaseServiceError("invalid Content-Length / Content-Length 오류") from exc
            if length <= 0 or length > MAX_ADMISSION_REQUEST_BYTES:
                raise CaseServiceError("admission request size invalid / 정식 수용 요청 크기 오류")
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise CaseServiceError("invalid admission JSON / 정식 수용 JSON 오류") from exc
            if not isinstance(payload, dict):
                raise CaseServiceError("admission payload must be a JSON object / 정식 수용 payload는 JSON 객체여야 합니다")
            return payload

        def do_GET(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            try:
                if path == "/":
                    self._send(
                        HTTPStatus.OK,
                        _dashboard_with_admission_link(repo).encode("utf-8"),
                        "text/html; charset=utf-8",
                    )
                    return
                if path == "/admission":
                    self._send(
                        HTTPStatus.OK,
                        render_admission_lab().encode("utf-8"),
                        "text/html; charset=utf-8",
                    )
                    return
                super().do_GET()
            except CaseServiceError as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

        def do_POST(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            if path not in {"/api/admission/build", "/api/admission/validate"}:
                super().do_POST()
                return
            try:
                payload = self._admission_payload()
                result = (
                    build_admission_bundle(payload, repo)
                    if path.endswith("/build")
                    else validate_admission_bundle(payload, repo)
                )
                self._send(
                    HTTPStatus.OK,
                    legacy_web._json_bytes(result),
                    "application/json; charset=utf-8",
                )
            except (CaseServiceError, ValueError) as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

    return AdmissionHandler


def serve(*, host: str = "127.0.0.1", port: int = 8765, root: Path | None = None) -> None:
    if not 0 < port < 65536:
        raise ValueError("port must be in 1..65535 / 포트 범위 오류")
    server = ThreadingHTTPServer((host, port), make_handler(root))
    print(f"Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}")
    print("Draft Lab / Draft 랩: /draft")
    print("Promotion Review / 승격 검토: /promotion")
    print("Promotion Package / 승격 패키지: /package")
    print("Canonical Admission / 정식 수용: /admission")
    print("Press Ctrl+C to stop / 종료하려면 Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
