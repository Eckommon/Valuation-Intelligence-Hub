"""Read-only multi-source evidence inspection Web layer / 읽기전용 다중소스 근거검사 Web 계층.

M14 extends the M13 Web server with OpenDART snapshot validation/extraction only.
There is deliberately no browser live-fetch route and no API-key input surface.
"""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from valuation_hub import web as legacy_web
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.dart_live import DART_METRIC_SPECS, extract_dart_evidence_candidate, validate_dart_snapshot
from valuation_hub.web_prprep import make_handler as make_prprep_handler, _dashboard_with_pr_prep_link
from valuation_hub.web_product import product_layout

MAX_DART_INSPECT_REQUEST_BYTES = 24 * 1024 * 1024


def render_dart_source_lab() -> str:
    options = "".join(f'<option value="{name}">{name}</option>' for name in DART_METRIC_SPECS)
    body = f"""
<div class="breadcrumbs"><a href="/">Dashboard</a><span>›</span><strong>OpenDART Source Inspector / OpenDART 출처 검사</strong></div>
<div class="section-head"><div><h2>OpenDART Source Snapshot Inspector / OpenDART Source Snapshot 검사기</h2><p class="muted">Validate immutable snapshots and extract unreviewed row-grounded candidates. / 불변 snapshot 검증 및 미검토 row 기반 근거후보 추출</p></div><span class="state-preview">INSPECT ONLY · NO LIVE FETCH</span></div>
<div class="card"><p class="warn"><strong>No API-key field, browser live fetch, or canonical write / API key 입력·브라우저 live fetch·정식 기록 없음</strong></p><p>Paste a snapshot previously captured by the local CLI. OpenDART origin does not grant canonical authority. / 로컬 CLI로 수집한 snapshot을 붙여넣습니다. OpenDART 공식 출처도 자동으로 정식 권위를 부여하지 않습니다.</p></div>
<label>OpenDART Snapshot JSON<textarea id="dart-snapshot" spellcheck="false" style="width:100%;min-height:460px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<div class="grid compact" style="margin-top:14px"><label>Metric / 지표<select id="dart-metric">{options}</select></label><label>Statement section / 재무제표 구분<select id="dart-section"><option value="">automatic</option><option>BS</option><option>IS</option><option>CIS</option><option>CF</option><option>SCE</option></select></label></div>
<p><button class="primary" onclick="validateDart()">Validate snapshot / snapshot 검증</button> <button class="primary" onclick="extractDart()">Extract candidate / 후보 추출</button></p>
<div id="dart-summary" class="preview-summary"><div class="muted">Read-only inspection. API credentials are never accepted here. / 읽기 전용 검사이며 API 인증정보를 받지 않습니다.</div></div>
<pre id="dart-output">—</pre>
<script>
const ds=document.getElementById('dart-snapshot'),do_=document.getElementById('dart-output'),dm=document.getElementById('dart-summary');
function dartObj(){{try{{return JSON.parse(ds.value)}}catch(e){{throw new Error('Snapshot JSON error / JSON 오류: '+e.message)}}}}
async function dartPost(path,payload){{const r=await fetch(path,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(payload)}});const j=await r.json();do_.textContent=JSON.stringify(j,null,2);if(!r.ok)throw new Error(j.error||('HTTP '+r.status));return j;}}
async function validateDart(){{try{{const j=await dartPost('/api/dart-source/validate',{{snapshot:dartObj()}});dm.innerHTML='<div class="good"><strong>'+j.status+'</strong><br>'+j.corp_code+' · '+j.bsns_year+' · '+j.reprt_code+' · '+j.fs_div+'<br><code>'+j.snapshot_sha256+'</code><br><span class="muted">CANONICAL=false</span></div>';}}catch(e){{dm.innerHTML='<div class="bad">'+String(e)+'</div>';}}}}
async function extractDart(){{try{{const section=document.getElementById('dart-section').value;const payload={{snapshot:dartObj(),metric:document.getElementById('dart-metric').value}};if(section)payload.statement_section=section;const j=await dartPost('/api/dart-source/extract',payload);dm.innerHTML='<div class="warn"><strong>'+j.status+'</strong><br>'+j.metric+' = '+j.value+' '+j.unit+'<br>'+j.statement_section+' · '+(j.row.account_nm||j.row.account_id)+'<br><span class="muted">UNREVIEWED · CANONICAL=false</span></div>';}}catch(e){{dm.innerHTML='<div class="bad">'+String(e)+'</div>';}}}}
</script>
"""
    return product_layout("OpenDART Source Inspector — Valuation Intelligence Hub", body)


def _dashboard_with_dart_link(repo: Path) -> str:
    page = _dashboard_with_pr_prep_link(repo)
    marker = '<h2>Canonical cases / 정식 사례</h2>'
    banner = (
        '<div class="card" style="margin-bottom:18px;border-color:#f59e0b">'
        '<div><strong>OpenDART Source Inspector / OpenDART 출처 검사</strong></div>'
        '<p>Validate CLI-captured immutable OpenDART snapshots and extract unreviewed candidates. No API-key field or browser live fetch. / '
        'CLI로 수집한 불변 OpenDART snapshot을 검증하고 미검토 근거후보를 추출합니다. API key 입력과 브라우저 live fetch는 없습니다.</p>'
        '<a href="/dart-source">Open OpenDART Source Inspector / OpenDART 출처 검사 열기 →</a></div>'
    )
    return page.replace(marker, banner + marker, 1)


def make_handler(root: Path | None = None):
    repo = root.resolve() if root else find_repo_root()
    Base = make_prprep_handler(repo)

    class SourceHandler(Base):
        def _dart_payload(self) -> dict:
            raw = self.headers.get("Content-Length", "0")
            try:
                length = int(raw)
            except ValueError as exc:
                raise CaseServiceError("invalid Content-Length / Content-Length 오류") from exc
            if length <= 0 or length > MAX_DART_INSPECT_REQUEST_BYTES:
                raise CaseServiceError("OpenDART inspect request size invalid / OpenDART 검사 요청크기 오류")
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise CaseServiceError("invalid OpenDART inspect JSON / OpenDART 검사 JSON 오류") from exc
            if not isinstance(payload, dict):
                raise CaseServiceError("OpenDART inspect payload must be object / OpenDART 검사 payload는 객체여야 합니다")
            if "api_key" in payload or "crtfc_key" in payload:
                raise CaseServiceError("OpenDART credentials are forbidden in Web payloads / Web payload에 OpenDART 인증정보를 넣을 수 없습니다")
            return payload

        def do_GET(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            try:
                if path == "/":
                    self._send(HTTPStatus.OK, _dashboard_with_dart_link(repo).encode("utf-8"), "text/html; charset=utf-8")
                    return
                if path == "/dart-source":
                    self._send(HTTPStatus.OK, render_dart_source_lab().encode("utf-8"), "text/html; charset=utf-8")
                    return
                super().do_GET()
            except CaseServiceError as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

        def do_POST(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            if path not in {"/api/dart-source/validate", "/api/dart-source/extract"}:
                # No OpenDART live-fetch or canonical-write route exists here.
                super().do_POST()
                return
            try:
                payload = self._dart_payload()
                snapshot = payload.get("snapshot")
                if not isinstance(snapshot, dict):
                    raise CaseServiceError("snapshot object required / snapshot 객체 필요")
                if path.endswith("/validate"):
                    result = validate_dart_snapshot(snapshot)
                else:
                    metric = payload.get("metric")
                    if not isinstance(metric, str):
                        raise CaseServiceError("metric required / metric 필요")
                    section = payload.get("statement_section")
                    if section is not None and not isinstance(section, str):
                        raise CaseServiceError("statement_section must be string / statement_section 문자열 필요")
                    result = extract_dart_evidence_candidate(snapshot, metric, statement_section=section)
                self._send(HTTPStatus.OK, legacy_web._json_bytes(result), "application/json; charset=utf-8")
            except (CaseServiceError, ValueError) as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

    return SourceHandler


def serve(*, host: str = "127.0.0.1", port: int = 8765, root: Path | None = None) -> None:
    if not 0 < port < 65536:
        raise ValueError("port must be in 1..65535 / 포트 범위 오류")
    server = ThreadingHTTPServer((host, port), make_handler(root))
    print(f"Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}")
    print("SEC Source Inspector / SEC 출처 검사: /source")
    print("OpenDART Source Inspector / OpenDART 출처 검사: /dart-source")
    print("Press Ctrl+C to stop / 종료하려면 Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
