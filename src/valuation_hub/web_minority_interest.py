"""Read-only M28 minority-interest Web Lab / 읽기전용 M28 비지배지분 Web Lab."""
from __future__ import annotations

import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from valuation_hub import web as legacy_web
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.minority_interest import (
    build_minority_interest_review_assertion,
    extract_dart_minority_interest_candidate,
    extract_sec_minority_interest_candidate,
    finalize_reviewed_minority_interest,
    normalize_minority_interest_candidate,
    validate_minority_interest_candidate,
    validate_minority_interest_observation,
    validate_minority_interest_review_assertion,
    validate_reviewed_minority_interest,
)
from valuation_hub.minority_interest_draft_binding import build_binding_proposal_with_minority_interest, validate_binding_proposal_v8
from valuation_hub.web_market_price import _dashboard as _prior_dashboard, make_handler as make_prior_handler
from valuation_hub.web_product import product_layout

MAX_REQUEST_BYTES = 16 * 1024 * 1024


def render_minority_interest_lab() -> str:
    body = """
<div class="breadcrumbs"><a href="/">Dashboard</a><span>›</span><strong>Minority Interest / 비지배지분</strong></div>
<div class="section-head"><div><h2>Governed Noncontrolling Interest / 거버넌스 비지배지분</h2><p class="muted">Prepare an exact consolidated balance-sheet noncontrolling-interest fact and review its period/freshness before Draft binding.</p></div><span class="state-preview">FACT · CFS · MISSING ≠ ZERO</span></div>
<div class="card"><p class="warn"><strong>Missing evidence is never zero.</strong></p><p>SEC v0.1 accepts exact nonredeemable NCI only. OpenDART v0.1 accepts exact <code>ifrs-full_NoncontrollingInterests</code> account ID only. Redeemable NCI and equity-difference derivations are outside this field.</p></div>
<label>Request JSON<textarea id="req" spellcheck="false" style="width:100%;min-height:360px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><select id="action"><option value="sec-extract">SEC exact extract</option><option value="dart-extract">OpenDART exact extract</option><option value="candidate-validate">Validate candidate</option><option value="normalize">Normalize</option><option value="observation-validate">Validate observation</option><option value="review-build">Build review/date assertion</option><option value="review-validate">Validate review</option><option value="finalize">Finalize reviewed FACT</option><option value="validate">Validate reviewed FACT</option><option value="binding-build">Build v0.8 proposal</option><option value="binding-validate">Validate v0.8 proposal</option></select> <button class="primary" onclick="run()">Run / 실행</button></p>
<div class="preview-summary"><div class="muted">NO DRAFT APPLY · NO FILE WRITE · NO PROMOTION · NO CANONICAL WRITE</div></div><pre id="out">—</pre>
<script>
const q=document.getElementById('req'),a=document.getElementById('action'),o=document.getElementById('out');
async function run(){try{const body=JSON.parse(q.value);const r=await fetch('/api/minority-interest/'+a.value,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});o.textContent=JSON.stringify(await r.json(),null,2)}catch(e){o.textContent=String(e)}}
</script>
"""
    return product_layout("Minority Interest — Valuation Intelligence Hub", body)


def _dashboard(repo: Path) -> str:
    page = _prior_dashboard(repo)
    marker = '<h2>Canonical cases / 정식 사례</h2>'
    banner = '<div class="card" style="margin-bottom:18px;border-color:#a78bfa"><div><strong>M28 Minority Interest / M28 비지배지분</strong></div><p>Exact CFS NCI → reviewed NORMALIZED_FACT → v0.8 minority-interest binding proposal.</p><a href="/minority-interest">Open Minority Interest Lab / 비지배지분 랩 열기 →</a></div>'
    return page.replace(marker, banner + marker, 1)


def make_handler(root: Path | None = None):
    repo = root.resolve() if root else find_repo_root()
    Base = make_prior_handler(repo)

    class MinorityInterestHandler(Base):
        def _m28_payload(self) -> dict:
            try: length = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc: raise CaseServiceError("invalid Content-Length / Content-Length 오류") from exc
            if length <= 0 or length > MAX_REQUEST_BYTES: raise CaseServiceError("minority-interest request size invalid / 비지배지분 요청크기 오류")
            try: value = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc: raise CaseServiceError("invalid minority-interest JSON / 비지배지분 JSON 오류") from exc
            if not isinstance(value, dict): raise CaseServiceError("minority-interest payload object required / 비지배지분 payload 객체 필요")
            if any(key in value for key in ("api_key", "crtfc_key", "user_agent")): raise CaseServiceError("credentials forbidden / 인증정보 금지")
            return value

        def do_GET(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            try:
                if path == "/": self._send(HTTPStatus.OK, _dashboard(repo).encode("utf-8"), "text/html; charset=utf-8"); return
                if path == "/minority-interest": self._send(HTTPStatus.OK, render_minority_interest_lab().encode("utf-8"), "text/html; charset=utf-8"); return
                super().do_GET()
            except CaseServiceError as exc: self._error(path, exc, HTTPStatus.BAD_REQUEST)

        def do_POST(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path); prefix = "/api/minority-interest/"
            if not path.startswith(prefix): super().do_POST(); return
            try:
                q = self._m28_payload(); action = path[len(prefix):]
                if action == "sec-extract": result = extract_sec_minority_interest_candidate(q.get("snapshot"), form=q.get("form"), period_end=q.get("period_end"))
                elif action == "dart-extract": result = extract_dart_minority_interest_candidate(q.get("snapshot"))
                elif action == "candidate-validate": result = validate_minority_interest_candidate(q.get("candidate"))
                elif action == "normalize": result = normalize_minority_interest_candidate(q.get("candidate"))
                elif action == "observation-validate": result = validate_minority_interest_observation(q.get("observation"))
                elif action == "review-build": result = build_minority_interest_review_assertion(q.get("observation"), as_of=q.get("as_of"), reviewer=q.get("reviewer"), approved_at=q.get("approved_at"), review_basis=q.get("review_basis"), asserted_period_end=q.get("asserted_period_end"), max_age_days=q.get("max_age_days", 550))
                elif action == "review-validate": result = validate_minority_interest_review_assertion(q.get("assertion"), q.get("observation"))
                elif action == "finalize": result = finalize_reviewed_minority_interest(q.get("observation"), q.get("assertion"))
                elif action == "validate": result = validate_reviewed_minority_interest(q.get("package"))
                elif action == "binding-build": result = build_binding_proposal_with_minority_interest(q.get("base_proposal"), q.get("minority_interest_package"))
                elif action == "binding-validate": result = validate_binding_proposal_v8(q.get("proposal"))
                else: raise CaseServiceError("unsupported minority-interest Web action / 미지원 비지배지분 Web 동작")
                self._send(HTTPStatus.OK, legacy_web._json_bytes(result), "application/json; charset=utf-8")
            except (CaseServiceError, ValueError, TypeError, KeyError) as exc: self._error(path, exc, HTTPStatus.BAD_REQUEST)

    return MinorityInterestHandler


def serve(*, host: str = "127.0.0.1", port: int = 8765, root: Path | None = None) -> None:
    if not 0 < port < 65536: raise ValueError("port must be in 1..65535 / 포트 범위 오류")
    server = ThreadingHTTPServer((host, port), make_handler(root))
    print(f"Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}")
    print("M28 Minority Interest Lab / M28 비지배지분 랩: /minority-interest")
    print("Press Ctrl+C to stop / 종료하려면 Ctrl+C")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
