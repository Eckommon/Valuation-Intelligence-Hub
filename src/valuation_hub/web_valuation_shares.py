"""Read-only M22 valuation-date share-base and diluted-share bridge Web Lab."""
from __future__ import annotations

import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from valuation_hub import web as legacy_web
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.valuation_shares import (
    ADJUSTMENT_CATEGORIES,
    build_diluted_share_bridge,
    build_dilution_adjustment,
    build_dilution_coverage_assertion,
    build_valuation_share_base_context,
    extract_sec_current_common_shares_candidate,
    normalize_current_common_shares_candidate,
    validate_current_common_shares_observation,
    validate_diluted_share_bridge,
    validate_dilution_adjustment,
    validate_dilution_coverage_assertion,
    validate_valuation_share_base_context,
)
from valuation_hub.web_dilution import _dashboard as _dashboard_with_dilution_link, make_handler as make_dilution_handler
from valuation_hub.web_product import product_layout

MAX_REQUEST_BYTES = 16 * 1024 * 1024


def render_share_bridge_lab() -> str:
    body = """
<div class="breadcrumbs"><a href="/">Dashboard</a><span>›</span><strong>Valuation Shares / 가치평가 주식수</strong></div>
<div class="section-head"><div><h2>Valuation-Date Share Base + Dilution Bridge / 가치평가일 주식기준 + 희석 bridge</h2><p class="muted">Build a point-in-time common-share base and explicit dilution bridge without treating current shares or historical EPS denominators as fully diluted shares.</p></div><span class="state-preview">CURRENT SHARES ≠ FULLY DILUTED · NO MISSING-AS-ZERO · CALCULATE ONLY</span></div>
<div class="card"><p class="warn"><strong>Coverage must be explicit / Coverage는 명시적이어야 합니다.</strong></p><p><code>BASE_ONLY</code> and <code>PARTIAL_DILUTION_COVERAGE</code> are never future-direct-bind eligible. Historical M21 dilution is reference-only and cannot create a current adjustment.</p></div>
<label>Valuation share-base context JSON<textarea id="base" spellcheck="false" style="width:100%;min-height:260px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<label>Dilution adjustments JSON array<textarea id="adjustments" spellcheck="false" style="width:100%;min-height:220px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace">[]</textarea></label>
<label>Coverage assertion JSON (optional)<textarea id="coverage" spellcheck="false" style="width:100%;min-height:180px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<label>M21 historical dilution reference JSON (optional)<textarea id="historical" spellcheck="false" style="width:100%;min-height:180px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><button class="primary" onclick="buildBridge()">Build bridge / Bridge 계산</button></p>
<div class="preview-summary"><div class="muted">CALCULATE/VALIDATE ONLY · NO DRAFT WRITE · NO CANONICAL WRITE</div></div><pre id="out">—</pre>
<script>
const base=document.getElementById('base'),adj=document.getElementById('adjustments'),cov=document.getElementById('coverage'),hist=document.getElementById('historical'),out=document.getElementById('out');
function p(x,l){try{return JSON.parse(x.value)}catch(e){throw new Error(l+' JSON error: '+e.message)}}
async function buildBridge(){try{const payload={base_context:p(base,'Base'),adjustments:p(adj,'Adjustments')};if(cov.value.trim())payload.coverage_assertion=p(cov,'Coverage');if(hist.value.trim())payload.historical_reference=p(hist,'Historical');const r=await fetch('/api/shares/bridge-build',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const j=await r.json();out.textContent=JSON.stringify(j,null,2)}catch(e){out.textContent=String(e)}}
</script>
"""
    return product_layout("Valuation Shares — Valuation Intelligence Hub", body)


def _dashboard(repo: Path) -> str:
    page = _dashboard_with_dilution_link(repo)
    marker = '<h2>Canonical cases / 정식 사례</h2>'
    banner = ('<div class="card" style="margin-bottom:18px;border-color:#38bdf8"><div><strong>Valuation-Date Shares / 가치평가일 주식수</strong></div><p>Point-in-time common-share base plus explicit dilution adjustments with visible coverage. Current shares and historical dilution are never silently promoted to fully diluted shares.</p><a href="/shares">Open Share Bridge Lab / 주식수 Bridge 랩 열기 →</a></div>')
    return page.replace(marker, banner + marker, 1)


def make_handler(root: Path | None = None):
    repo = root.resolve() if root else find_repo_root()
    Base = make_dilution_handler(repo)

    class ShareBridgeHandler(Base):
        def _share_payload(self) -> dict:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise CaseServiceError("invalid Content-Length / Content-Length 오류") from exc
            if length <= 0 or length > MAX_REQUEST_BYTES:
                raise CaseServiceError("share bridge request size invalid / 주식수 bridge 요청크기 오류")
            try:
                value = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise CaseServiceError("invalid share bridge JSON / 주식수 bridge JSON 오류") from exc
            if not isinstance(value, dict):
                raise CaseServiceError("share bridge payload object required / 주식수 bridge payload 객체 필요")
            if any(key in value for key in ("api_key", "crtfc_key", "user_agent")):
                raise CaseServiceError("credentials forbidden / 인증정보 금지")
            return value

        @staticmethod
        def _adjustments(value: object) -> list[dict]:
            if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
                raise CaseServiceError("adjustments JSON object array required / adjustments JSON 객체 배열 필요")
            return value

        def do_GET(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            try:
                if path == "/":
                    self._send(HTTPStatus.OK, _dashboard(repo).encode("utf-8"), "text/html; charset=utf-8")
                    return
                if path == "/shares":
                    self._send(HTTPStatus.OK, render_share_bridge_lab().encode("utf-8"), "text/html; charset=utf-8")
                    return
                super().do_GET()
            except CaseServiceError as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

        def do_POST(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            routes = {
                "/api/shares/sec-extract",
                "/api/shares/normalize",
                "/api/shares/observation-validate",
                "/api/shares/base-context-build",
                "/api/shares/base-context-validate",
                "/api/shares/adjustment-build",
                "/api/shares/adjustment-validate",
                "/api/shares/coverage-assertion-build",
                "/api/shares/coverage-assertion-validate",
                "/api/shares/bridge-build",
                "/api/shares/bridge-validate",
            }
            if path not in routes:
                super().do_POST()
                return
            try:
                q = self._share_payload()
                if path == "/api/shares/sec-extract":
                    snapshot = q.get("snapshot")
                    if not isinstance(snapshot, dict):
                        raise CaseServiceError("SEC snapshot required / SEC snapshot 필요")
                    result = extract_sec_current_common_shares_candidate(snapshot, period_end=q.get("period_end"), form=q.get("form"))
                elif path == "/api/shares/normalize":
                    candidate = q.get("candidate")
                    if not isinstance(candidate, dict):
                        raise CaseServiceError("current-share candidate required / 현재주식수 candidate 필요")
                    result = normalize_current_common_shares_candidate(candidate)
                elif path == "/api/shares/observation-validate":
                    observation = q.get("observation")
                    if not isinstance(observation, dict):
                        raise CaseServiceError("current-share observation required / 현재주식수 observation 필요")
                    result = validate_current_common_shares_observation(observation)
                elif path == "/api/shares/base-context-build":
                    observation = q.get("observation")
                    if not isinstance(observation, dict):
                        raise CaseServiceError("current-share observation required / 현재주식수 observation 필요")
                    result = build_valuation_share_base_context(observation, as_of=q.get("as_of"), max_age_days=q.get("max_age_days", 180))
                elif path == "/api/shares/base-context-validate":
                    context = q.get("context")
                    if not isinstance(context, dict):
                        raise CaseServiceError("valuation share-base context required / 가치평가 주식기준 context 필요")
                    result = validate_valuation_share_base_context(context)
                elif path == "/api/shares/adjustment-build":
                    result = build_dilution_adjustment(
                        adjustment_id=q.get("adjustment_id"),
                        category=q.get("category"),
                        shares=q.get("shares"),
                        source_sha256=q.get("source_sha256"),
                        source_description=q.get("source_description"),
                    )
                elif path == "/api/shares/adjustment-validate":
                    adjustment = q.get("adjustment")
                    if not isinstance(adjustment, dict):
                        raise CaseServiceError("dilution adjustment required / 희석조정 필요")
                    result = validate_dilution_adjustment(adjustment)
                elif path == "/api/shares/coverage-assertion-build":
                    context = q.get("base_context")
                    if not isinstance(context, dict):
                        raise CaseServiceError("base_context required / base_context 필요")
                    result = build_dilution_coverage_assertion(
                        context,
                        self._adjustments(q.get("adjustments")),
                        reviewer=q.get("reviewer"),
                        approved_at=q.get("approved_at"),
                        coverage_basis=q.get("coverage_basis"),
                        reviewed_categories=q.get("reviewed_categories"),
                    )
                elif path == "/api/shares/coverage-assertion-validate":
                    assertion, context = q.get("assertion"), q.get("base_context")
                    if not isinstance(assertion, dict) or not isinstance(context, dict):
                        raise CaseServiceError("assertion and base_context required / assertion·base_context 필요")
                    result = validate_dilution_coverage_assertion(assertion, context, self._adjustments(q.get("adjustments")))
                elif path == "/api/shares/bridge-build":
                    context = q.get("base_context")
                    if not isinstance(context, dict):
                        raise CaseServiceError("base_context required / base_context 필요")
                    assertion = q.get("coverage_assertion")
                    historical = q.get("historical_reference")
                    if assertion is not None and not isinstance(assertion, dict):
                        raise CaseServiceError("coverage_assertion must be object / coverage_assertion 객체 필요")
                    if historical is not None and not isinstance(historical, dict):
                        raise CaseServiceError("historical_reference must be object / historical_reference 객체 필요")
                    result = build_diluted_share_bridge(
                        context,
                        self._adjustments(q.get("adjustments")),
                        coverage_assertion=assertion,
                        historical_reference=historical,
                    )
                else:
                    bridge = q.get("bridge")
                    if not isinstance(bridge, dict):
                        raise CaseServiceError("diluted-share bridge required / 희석주식 bridge 필요")
                    result = validate_diluted_share_bridge(bridge)
                self._send(HTTPStatus.OK, legacy_web._json_bytes(result), "application/json; charset=utf-8")
            except (CaseServiceError, ValueError, TypeError) as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

    return ShareBridgeHandler


def serve(*, host: str = "127.0.0.1", port: int = 8765, root: Path | None = None) -> None:
    if not 0 < port < 65536:
        raise ValueError("port must be in 1..65535 / 포트 범위 오류")
    server = ThreadingHTTPServer((host, port), make_handler(root))
    print(f"Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}")
    print("Valuation Shares / 가치평가 주식수: /shares")
    print("Press Ctrl+C to stop / 종료하려면 Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
