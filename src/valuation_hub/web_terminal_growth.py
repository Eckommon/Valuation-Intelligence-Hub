"""Read-only M25 governed terminal-growth Web Lab / 읽기전용 M25 영구성장률 Web Lab."""
from __future__ import annotations

import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from valuation_hub import web as legacy_web
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.terminal_growth_assumption import (
    build_terminal_growth_candidate,
    build_terminal_growth_review_assertion,
    finalize_reviewed_terminal_growth,
    validate_reviewed_terminal_growth,
    validate_terminal_growth_candidate,
    validate_terminal_growth_review_assertion,
)
from valuation_hub.terminal_growth_draft_binding import (
    build_binding_proposal_with_terminal_growth,
    validate_binding_proposal_v5,
)
from valuation_hub.web_product import product_layout
from valuation_hub.web_wacc import _dashboard as _prior_dashboard, make_handler as make_prior_handler

MAX_REQUEST_BYTES = 16 * 1024 * 1024


def render_terminal_growth_lab() -> str:
    body = """
<div class="breadcrumbs"><a href="/">Dashboard</a><span>›</span><strong>Terminal Growth / 영구성장률</strong></div>
<div class="section-head"><div><h2>Governed Terminal-Growth Assumption / 거버넌스 영구성장률 가정</h2><p class="muted">Tie each scenario's perpetual-growth assumption to the exact reviewed WACC package and explicit long-run macro anchors.</p></div><span class="state-preview">ASSUMPTION · WACC-DEPENDENT · HUMAN REVIEW</span></div>
<div class="card"><p class="warn"><strong>Macro anchor ≠ terminal-growth fact.</strong></p><p>Each scenario requires explicit <code>g</code> and rationale. Validation enforces <code>g &lt; reviewed WACC</code>, <code>g ≤ nominal macro anchor</code>, and <code>g &gt; -1</code>.</p></div>
<label>Request JSON<textarea id="req" spellcheck="false" style="width:100%;min-height:360px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><select id="action"><option value="candidate-build">Build candidate</option><option value="candidate-validate">Validate candidate</option><option value="review-build">Build review assertion</option><option value="review-validate">Validate review assertion</option><option value="finalize">Finalize reviewed package</option><option value="validate">Validate reviewed package</option><option value="binding-build">Build v0.5 proposal</option><option value="binding-validate">Validate v0.5 proposal</option></select> <button class="primary" onclick="run()">Run / 실행</button></p>
<div class="preview-summary"><div class="muted">NO DRAFT APPLY · NO FILE WRITE · NO PROMOTION · NO CANONICAL WRITE</div></div><pre id="out">—</pre>
<script>
const q=document.getElementById('req'),a=document.getElementById('action'),o=document.getElementById('out');
async function run(){try{const body=JSON.parse(q.value);const r=await fetch('/api/terminal-growth/'+a.value,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});o.textContent=JSON.stringify(await r.json(),null,2)}catch(e){o.textContent=String(e)}}
</script>
"""
    return product_layout("Governed Terminal Growth — Valuation Intelligence Hub", body)


def _dashboard(repo: Path) -> str:
    page = _prior_dashboard(repo)
    marker = '<h2>Canonical cases / 정식 사례</h2>'
    banner = '<div class="card" style="margin-bottom:18px;border-color:#a78bfa"><div><strong>M25 Terminal Growth / M25 영구성장률</strong></div><p>Reviewed WACC + macro anchors → scenario assumptions → human review → v0.5 scenario.terminal_growth proposal.</p><a href="/terminal-growth">Open Terminal-Growth Lab / 영구성장률 랩 열기 →</a></div>'
    return page.replace(marker, banner + marker, 1)


def make_handler(root: Path | None = None):
    repo = root.resolve() if root else find_repo_root()
    Base = make_prior_handler(repo)

    class TerminalGrowthHandler(Base):
        def _m25_payload(self) -> dict:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise CaseServiceError("invalid Content-Length / Content-Length 오류") from exc
            if length <= 0 or length > MAX_REQUEST_BYTES:
                raise CaseServiceError("terminal-growth request size invalid / 영구성장률 요청크기 오류")
            try:
                value = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise CaseServiceError("invalid terminal-growth JSON / 영구성장률 JSON 오류") from exc
            if not isinstance(value, dict):
                raise CaseServiceError("terminal-growth payload object required / 영구성장률 payload 객체 필요")
            if any(key in value for key in ("api_key", "crtfc_key", "user_agent")):
                raise CaseServiceError("credentials forbidden / 인증정보 금지")
            return value

        def do_GET(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            try:
                if path == "/":
                    self._send(HTTPStatus.OK, _dashboard(repo).encode("utf-8"), "text/html; charset=utf-8")
                    return
                if path == "/terminal-growth":
                    self._send(HTTPStatus.OK, render_terminal_growth_lab().encode("utf-8"), "text/html; charset=utf-8")
                    return
                super().do_GET()
            except CaseServiceError as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

        def do_POST(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            prefix = "/api/terminal-growth/"
            if not path.startswith(prefix):
                super().do_POST()
                return
            try:
                query = self._m25_payload()
                action = path[len(prefix):]
                if action == "candidate-build":
                    anchors = query.get("anchors")
                    assumptions = query.get("scenario_assumptions")
                    wacc_package = query.get("wacc_package")
                    if not isinstance(anchors, list) or not all(isinstance(item, dict) for item in anchors):
                        raise CaseServiceError("terminal-growth anchors array required / 영구성장률 anchor 배열 필요")
                    if not isinstance(assumptions, list) or not all(isinstance(item, dict) for item in assumptions):
                        raise CaseServiceError("scenario assumptions array required / 시나리오 가정 배열 필요")
                    if not isinstance(wacc_package, dict):
                        raise CaseServiceError("reviewed WACC package required / 검토완료 WACC 패키지 필요")
                    result = build_terminal_growth_candidate(anchors, wacc_package, scenario_assumptions=assumptions)
                elif action == "candidate-validate":
                    result = validate_terminal_growth_candidate(query.get("candidate"))
                elif action == "review-build":
                    result = build_terminal_growth_review_assertion(query.get("candidate"), reviewer=query.get("reviewer"), approved_at=query.get("approved_at"), review_basis=query.get("review_basis"))
                elif action == "review-validate":
                    result = validate_terminal_growth_review_assertion(query.get("assertion"), query.get("candidate"))
                elif action == "finalize":
                    result = finalize_reviewed_terminal_growth(query.get("candidate"), query.get("assertion"))
                elif action == "validate":
                    result = validate_reviewed_terminal_growth(query.get("package"))
                elif action == "binding-build":
                    result = build_binding_proposal_with_terminal_growth(query.get("base_proposal"), query.get("terminal_growth_package"))
                elif action == "binding-validate":
                    result = validate_binding_proposal_v5(query.get("proposal"))
                else:
                    raise CaseServiceError("unsupported terminal-growth Web action / 미지원 영구성장률 Web 동작")
                self._send(HTTPStatus.OK, legacy_web._json_bytes(result), "application/json; charset=utf-8")
            except (CaseServiceError, ValueError, TypeError, KeyError) as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

    return TerminalGrowthHandler


def serve(*, host: str = "127.0.0.1", port: int = 8765, root: Path | None = None) -> None:
    if not 0 < port < 65536:
        raise ValueError("port must be in 1..65535 / 포트 범위 오류")
    server = ThreadingHTTPServer((host, port), make_handler(root))
    print(f"Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}")
    print("M25 Terminal-Growth Lab / M25 영구성장률 랩: /terminal-growth")
    print("Press Ctrl+C to stop / 종료하려면 Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
