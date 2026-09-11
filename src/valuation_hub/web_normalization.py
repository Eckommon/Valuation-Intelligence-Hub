"""Read-only M15 financial normalization Web Lab / 읽기전용 M15 재무정규화 Web Lab."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from valuation_hub import web as legacy_web
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.financial_normalization import (
    DURATION_ANNUAL,
    DURATION_QUARTER,
    DURATION_YTD,
    normalize_dart_candidate,
    normalize_sec_candidate,
    reconcile_same_period,
    ttm_annual_bridge,
    ttm_four_quarters,
    validate_financial_observation,
    validate_ttm_result,
)
from valuation_hub.web_product import product_layout
from valuation_hub.web_sources import make_handler as make_source_handler, _dashboard_with_dart_link

MAX_NORMALIZATION_REQUEST_BYTES = 24 * 1024 * 1024


def render_normalization_lab() -> str:
    body = """
<div class="breadcrumbs"><a href="/">Dashboard</a><span>›</span><strong>Financial Normalization / 재무근거 정규화</strong></div>
<div class="section-head"><div><h2>Financial Normalization + TTM Lab / 재무근거 정규화 + TTM 랩</h2><p class="muted">Transform already-captured evidence candidates into period-aware normalized observations and reproducible TTM results. / 이미 수집된 근거후보를 기간 정규화 observation과 재현 가능한 TTM으로 변환합니다.</p></div><span class="state-preview">CALCULATE ONLY · NO WRITE</span></div>
<div class="card"><p class="warn"><strong>Arithmetic never upgrades evidence authority / 산술은 근거 권위를 승격하지 않음</strong></p><p><code>FACT_CANDIDATE → NORMALIZED_FACT_CANDIDATE</code>. This lab accepts JSON only and has no live-fetch, file-write, promotion, admission, or canonical-write endpoint. / JSON 계산만 제공하며 live fetch·파일 기록·승격·수용·정식기록 endpoint가 없습니다.</p></div>
<h3>1. Normalize one evidence candidate / 근거후보 1건 정규화</h3>
<div class="grid compact"><label>Source / 소스<select id="norm-source"><option value="sec">SEC</option><option value="dart">OpenDART</option></select></label><label>SEC period kind<select id="norm-period"><option value="">automatic / required for 10-Q duration</option><option>DURATION_QUARTER</option><option>DURATION_YTD</option><option>DURATION_ANNUAL</option></select></label><label>DART amount basis<select id="norm-basis"><option>CURRENT</option><option>CUMULATIVE</option></select></label></div>
<label>Evidence candidate JSON<textarea id="norm-candidate" spellcheck="false" style="width:100%;min-height:300px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><button class="primary" onclick="normalizeOne()">Normalize / 정규화</button> <button class="primary" onclick="validateObservation()">Validate observation / observation 검증</button></p>
<h3>2. TTM or reconciliation / TTM·조정</h3>
<p class="muted">Paste a JSON array of normalized observations. Four-quarter TTM requires exactly four quarter observations. Reconciliation requires same-period observations. Annual bridge requires exactly [prior annual, current YTD, prior comparable YTD].</p>
<label>Normalized observations JSON array<textarea id="norm-observations" spellcheck="false" style="width:100%;min-height:300px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><button class="primary" onclick="fourQuarter()">4-quarter TTM / 4분기 TTM</button> <button class="primary" onclick="annualBridge()">Annual bridge TTM / 연간 bridge TTM</button> <button class="primary" onclick="reconcile()">Reconcile same period / 동일기간 조정</button> <button class="primary" onclick="validateTtm()">Validate TTM / TTM 검증</button></p>
<div id="norm-summary" class="preview-summary"><div class="muted">Outputs remain noncanonical. / 출력은 비정식 상태를 유지합니다.</div></div>
<pre id="norm-output">—</pre>
<script>
const nc=document.getElementById('norm-candidate'),no=document.getElementById('norm-observations'),nout=document.getElementById('norm-output'),ns=document.getElementById('norm-summary');
function obj(area,label){try{return JSON.parse(area.value)}catch(e){throw new Error(label+' JSON error / JSON 오류: '+e.message)}}
async function postNorm(path,payload){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const j=await r.json();nout.textContent=JSON.stringify(j,null,2);if(!r.ok)throw new Error(j.error||('HTTP '+r.status));return j;}
function show(j){ns.innerHTML='<div class="warn"><strong>'+(j.status||'RESULT')+'</strong><br>'+(j.metric||'')+' '+(j.value??'')+' '+(j.unit||'')+'<br><span class="muted">CANONICAL=false</span></div>';}
async function normalizeOne(){try{const p={source:document.getElementById('norm-source').value,candidate:obj(nc,'Candidate')};const k=document.getElementById('norm-period').value;if(k)p.period_kind=k;p.amount_basis=document.getElementById('norm-basis').value;const j=await postNorm('/api/normalize/one',p);show(j);}catch(e){ns.innerHTML='<div class="bad">'+String(e)+'</div>';}}
async function validateObservation(){try{const j=await postNorm('/api/normalize/validate',{observation:obj(nc,'Observation')});show(j);}catch(e){ns.innerHTML='<div class="bad">'+String(e)+'</div>';}}
async function fourQuarter(){try{const j=await postNorm('/api/normalize/ttm-four',{observations:obj(no,'Observations')});show(j);}catch(e){ns.innerHTML='<div class="bad">'+String(e)+'</div>';}}
async function annualBridge(){try{const j=await postNorm('/api/normalize/ttm-bridge',{observations:obj(no,'Observations')});show(j);}catch(e){ns.innerHTML='<div class="bad">'+String(e)+'</div>';}}
async function reconcile(){try{const j=await postNorm('/api/normalize/reconcile',{observations:obj(no,'Observations')});show(j);}catch(e){ns.innerHTML='<div class="bad">'+String(e)+'</div>';}}
async function validateTtm(){try{const j=await postNorm('/api/normalize/ttm-validate',{ttm:obj(no,'TTM')});show(j);}catch(e){ns.innerHTML='<div class="bad">'+String(e)+'</div>';}}
</script>
"""
    return product_layout("Financial Normalization — Valuation Intelligence Hub", body)


def _dashboard_with_normalization_link(repo: Path) -> str:
    page = _dashboard_with_dart_link(repo)
    marker = '<h2>Canonical cases / 정식 사례</h2>'
    banner = (
        '<div class="card" style="margin-bottom:18px;border-color:#a78bfa">'
        '<div><strong>Financial Normalization + TTM / 재무근거 정규화 + TTM</strong></div>'
        '<p>Period-aware SEC/OpenDART normalization, TTM transforms, and same-period reconciliation. Read-only and noncanonical. / '
        'SEC/OpenDART 기간정규화, TTM 변환, 동일기간 조정을 수행합니다. 읽기전용·비정식입니다.</p>'
        '<a href="/normalize">Open Normalization Lab / 정규화 랩 열기 →</a></div>'
    )
    return page.replace(marker, banner + marker, 1)


def make_handler(root: Path | None = None):
    repo = root.resolve() if root else find_repo_root()
    Base = make_source_handler(repo)

    class NormalizationHandler(Base):
        def _normalization_payload(self) -> dict:
            raw = self.headers.get("Content-Length", "0")
            try:
                length = int(raw)
            except ValueError as exc:
                raise CaseServiceError("invalid Content-Length / Content-Length 오류") from exc
            if length <= 0 or length > MAX_NORMALIZATION_REQUEST_BYTES:
                raise CaseServiceError("normalization request size invalid / 정규화 요청크기 오류")
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise CaseServiceError("invalid normalization JSON / 정규화 JSON 오류") from exc
            if not isinstance(payload, dict):
                raise CaseServiceError("normalization payload must be object / 정규화 payload는 객체여야 합니다")
            if any(key in payload for key in ("api_key", "crtfc_key", "user_agent")):
                raise CaseServiceError("credentials are forbidden in normalization Web payloads / 정규화 Web payload에 인증정보를 넣을 수 없습니다")
            return payload

        def do_GET(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            try:
                if path == "/":
                    self._send(HTTPStatus.OK, _dashboard_with_normalization_link(repo).encode("utf-8"), "text/html; charset=utf-8")
                    return
                if path == "/normalize":
                    self._send(HTTPStatus.OK, render_normalization_lab().encode("utf-8"), "text/html; charset=utf-8")
                    return
                super().do_GET()
            except CaseServiceError as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

        def do_POST(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            routes = {
                "/api/normalize/one", "/api/normalize/validate", "/api/normalize/ttm-four",
                "/api/normalize/ttm-bridge", "/api/normalize/reconcile", "/api/normalize/ttm-validate",
            }
            if path not in routes:
                super().do_POST()
                return
            try:
                payload = self._normalization_payload()
                if path == "/api/normalize/one":
                    candidate = payload.get("candidate")
                    if not isinstance(candidate, dict):
                        raise CaseServiceError("candidate object required / candidate 객체 필요")
                    source = payload.get("source")
                    if source == "sec":
                        result = normalize_sec_candidate(candidate, declared_period_kind=payload.get("period_kind"))
                    elif source == "dart":
                        result = normalize_dart_candidate(candidate, amount_basis=payload.get("amount_basis", "CURRENT"))
                    else:
                        raise CaseServiceError("source must be sec or dart / source는 sec 또는 dart여야 합니다")
                elif path == "/api/normalize/validate":
                    observation = payload.get("observation")
                    if not isinstance(observation, dict):
                        raise CaseServiceError("observation object required / observation 객체 필요")
                    result = validate_financial_observation(observation)
                elif path == "/api/normalize/ttm-validate":
                    ttm = payload.get("ttm")
                    if not isinstance(ttm, dict):
                        raise CaseServiceError("ttm object required / ttm 객체 필요")
                    result = validate_ttm_result(ttm)
                else:
                    observations = payload.get("observations")
                    if not isinstance(observations, list) or not all(isinstance(x, dict) for x in observations):
                        raise CaseServiceError("observations array of objects required / observation 객체 배열 필요")
                    if path == "/api/normalize/ttm-four":
                        result = ttm_four_quarters(observations)
                    elif path == "/api/normalize/ttm-bridge":
                        if len(observations) != 3:
                            raise CaseServiceError("annual bridge requires exactly 3 observations / annual bridge는 observation 3개 필요")
                        result = ttm_annual_bridge(observations[0], observations[1], observations[2])
                    else:
                        result = reconcile_same_period(observations)
                self._send(HTTPStatus.OK, legacy_web._json_bytes(result), "application/json; charset=utf-8")
            except (CaseServiceError, ValueError) as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

    return NormalizationHandler


def serve(*, host: str = "127.0.0.1", port: int = 8765, root: Path | None = None) -> None:
    if not 0 < port < 65536:
        raise ValueError("port must be in 1..65535 / 포트 범위 오류")
    server = ThreadingHTTPServer((host, port), make_handler(root))
    print(f"Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}")
    print("SEC Source Inspector / SEC 출처 검사: /source")
    print("OpenDART Source Inspector / OpenDART 출처 검사: /dart-source")
    print("Financial Normalization + TTM / 재무근거 정규화 + TTM: /normalize")
    print("Press Ctrl+C to stop / 종료하려면 Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
