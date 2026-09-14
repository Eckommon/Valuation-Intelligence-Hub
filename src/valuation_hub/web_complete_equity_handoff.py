"""Read-only M29 complete governed equity handoff Web Lab."""
from __future__ import annotations

import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from valuation_hub import web as legacy_web
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.promotion_m29 import (
    assess_candidate,
    build_complete_equity_candidate,
    build_evidence_catalog_claim,
    promotion_check,
    validate_candidate,
)
from valuation_hub.web_minority_interest import _dashboard as _prior_dashboard, make_handler as make_prior_handler
from valuation_hub.web_product import product_layout

MAX_REQUEST_BYTES = 32 * 1024 * 1024


def render_complete_handoff_lab() -> str:
    body = """
<div class="breadcrumbs"><a href="/">Dashboard</a><span>›</span><strong>Complete Equity Handoff / 완전 Equity 인계</strong></div>
<div class="section-head"><div><h2>Complete Governed Equity Handoff / 완전 거버넌스 Equity 인계</h2><p class="muted">Project a complete human-approved M28 v0.8 bound result into promotion-candidate-v0.2 without reclassifying the 13 governed material inputs.</p></div><span class="state-preview">13/13 DIRECT_BIND · NO UNKNOWN · PREPARATION ONLY</span></div>
<div class="card"><p class="warn"><strong>Authority is inherited, not reinvented.</strong></p><p>Observed fields preserve FACT / NORMALIZED_FACT / DERIVED. WACC, terminal growth and forecast paths remain ASSUMPTION. Tier-D evidence, partial approvals, nested tampering and lineage drift fail closed.</p></div>
<label>Request JSON<textarea id="req" spellcheck="false" style="width:100%;min-height:420px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><select id="action"><option value="catalog-claim">Build observed evidence claim</option><option value="build">Build promotion candidate v0.2</option><option value="assess">Assess candidate</option><option value="validate">Validate candidate</option><option value="check">Promotion check</option></select> <button class="primary" onclick="run()">Run / 실행</button></p>
<div class="preview-summary"><div class="muted">NO AUTO APPROVAL · NO FILE WRITE · NO ADMISSION APPLY · NO CANONICAL WRITE</div></div><pre id="out">—</pre>
<script>
const q=document.getElementById('req'),a=document.getElementById('action'),o=document.getElementById('out');
async function run(){try{const body=JSON.parse(q.value);const r=await fetch('/api/equity-handoff/'+a.value,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});o.textContent=JSON.stringify(await r.json(),null,2)}catch(e){o.textContent=String(e)}}
</script>
"""
    return product_layout("Complete Equity Handoff — Valuation Intelligence Hub", body)


def _dashboard(repo: Path) -> str:
    page = _prior_dashboard(repo)
    marker = '<h2>Canonical cases / 정식 사례</h2>'
    banner = '<div class="card" style="margin-bottom:18px;border-color:#22c55e"><div><strong>M29 Complete Equity Handoff / M29 완전 Equity 인계</strong></div><p>Complete M28 13/13 governed bound result → promotion-candidate-v0.2 with inherited authority and lineage.</p><a href="/equity-handoff">Open Complete Handoff Lab / 완전 인계 랩 열기 →</a></div>'
    return page.replace(marker, banner + marker, 1)


def make_handler(root: Path | None = None):
    repo = root.resolve() if root else find_repo_root()
    Base = make_prior_handler(repo)

    class CompleteHandoffHandler(Base):
        def _payload(self) -> dict:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise CaseServiceError("invalid Content-Length / Content-Length 오류") from exc
            if length <= 0 or length > MAX_REQUEST_BYTES:
                raise CaseServiceError("equity-handoff request size invalid / Equity 인계 요청크기 오류")
            try:
                value = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise CaseServiceError("invalid equity-handoff JSON / Equity 인계 JSON 오류") from exc
            if not isinstance(value, dict):
                raise CaseServiceError("equity-handoff payload object required / Equity 인계 payload 객체 필요")
            if any(key in value for key in ("api_key", "crtfc_key", "user_agent")):
                raise CaseServiceError("credentials forbidden / 인증정보 금지")
            return value

        def do_GET(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            try:
                if path == "/":
                    self._send(HTTPStatus.OK, _dashboard(repo).encode("utf-8"), "text/html; charset=utf-8"); return
                if path == "/equity-handoff":
                    self._send(HTTPStatus.OK, render_complete_handoff_lab().encode("utf-8"), "text/html; charset=utf-8"); return
                super().do_GET()
            except CaseServiceError as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

        def do_POST(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            prefix = "/api/equity-handoff/"
            if not path.startswith(prefix):
                super().do_POST(); return
            try:
                q = self._payload(); action = path[len(prefix):]
                if action == "catalog-claim":
                    result = q.get("bound_result")
                    if not isinstance(result, dict):
                        raise CaseServiceError("bound_result object required / bound_result 객체 필요")
                    output = build_evidence_catalog_claim(
                        result,
                        field=q.get("field"),
                        claim_id=q.get("claim_id"),
                        metric=q.get("metric"),
                        publisher=q.get("publisher"),
                        locator=q.get("locator"),
                        tier=q.get("tier"),
                        source_type=q.get("source_type"),
                        source_date=q.get("source_date"),
                    )
                elif action == "build":
                    result, catalog = q.get("bound_result"), q.get("evidence_catalog")
                    if not isinstance(result, dict) or not isinstance(catalog, list) or not all(isinstance(x, dict) for x in catalog):
                        raise CaseServiceError("bound_result and evidence_catalog required / bound_result·evidence_catalog 필요")
                    output = build_complete_equity_candidate(result, catalog)
                elif action in {"assess", "validate", "check"}:
                    candidate = q.get("candidate")
                    if not isinstance(candidate, dict):
                        raise CaseServiceError("candidate object required / candidate 객체 필요")
                    output = assess_candidate(candidate) if action == "assess" else validate_candidate(candidate) if action == "validate" else promotion_check(candidate)
                else:
                    raise CaseServiceError("unsupported equity-handoff action / 미지원 Equity 인계 action")
                self._send(HTTPStatus.OK, legacy_web._json_bytes(output), "application/json; charset=utf-8")
            except (CaseServiceError, ValueError, TypeError, KeyError) as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

    return CompleteHandoffHandler


def serve(*, host: str = "127.0.0.1", port: int = 8765, root: Path | None = None) -> None:
    if not 0 < port < 65536:
        raise ValueError("port must be in 1..65535 / 포트 범위 오류")
    server = ThreadingHTTPServer((host, port), make_handler(root))
    print(f"Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}")
    print("Complete Equity Handoff / 완전 Equity 인계: /equity-handoff")
    print("Press Ctrl+C to stop / 종료하려면 Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
