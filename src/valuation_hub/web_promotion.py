"""Promotion Review Web Lab / 승격 검토 Web Lab.

This adapter exposes M9 candidate-building, assessment, and hash-locked review
checks. It inherits all M8 Draft and earlier product routes. It never writes
canonical repository files or fabricates reviewer approval.

본 어댑터는 M9 candidate 생성·평가·해시 잠금 검토 확인을 제공하고 M8 Draft 및
기존 제품 경로를 상속한다. 정식 저장소 파일을 기록하거나 검토자 승인을 생성하지 않는다.
"""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from valuation_hub import web as legacy_web
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.promotion import assess_candidate, build_candidate, promotion_check
from valuation_hub.web_draft import _dashboard_with_draft_link, make_handler as make_draft_handler
from valuation_hub.web_product import product_layout

MAX_PROMOTION_REQUEST_BYTES = 1024 * 1024


def render_promotion_lab() -> str:
    body = """
<div class="breadcrumbs"><a href="/">Dashboard</a><span>›</span><strong>Promotion Review / 승격 검토</strong></div>
<div class="section-head"><div><h2>Promotion Review Lab / 승격 검토 랩</h2><p class="muted">Draft → Candidate → human review → reviewed PR readiness / Draft → Candidate → 인간 검토 → 검토 PR 준비</p></div><span class="state-preview">NOT CANONICAL</span></div>
<div class="card"><p class="warn"><strong>No automatic canonicalization / 자동 정식화 없음</strong></p><p>This lab can only declare <code>REVIEW_APPROVED_READY_FOR_PR</code>. Canonical status still requires a separately reviewed repository PR, CI, and merge. / 이 랩은 PR 준비 상태까지만 선언합니다. 정식 상태는 별도 인간 검토 PR·CI·병합이 필요합니다.</p></div>
<h3>1. Build candidate from Draft / Draft에서 Candidate 생성</h3>
<p><button class="primary" onclick="loadDraftTemplate()">Load equity Draft template / Equity Draft 템플릿</button> <button class="primary" onclick="buildCandidate()">Build candidate / Candidate 생성</button></p>
<label>Draft JSON<textarea id="promotion-draft" spellcheck="false" style="width:100%;min-height:260px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<h3>2. Classify inputs, attach evidence, and review / 입력 분류·근거 연결·검토</h3>
<p class="muted">Every numeric model input must be classified. Observed market/share/balance-sheet bridge values cannot be downgraded to assumptions. FACT/NORMALIZED_FACT must link evidence whose numeric value matches the model input. / 모든 숫자 입력을 분류해야 하며 관측값을 가정으로 우회할 수 없습니다.</p>
<label>Candidate JSON<textarea id="promotion-candidate" spellcheck="false" style="width:100%;min-height:520px;background:#0b1220;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:14px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace"></textarea></label>
<p><button class="primary" onclick="assessCandidate()">Assess candidate / Candidate 평가</button> <button class="primary" onclick="checkPromotion()">Check reviewed PR readiness / 검토 PR 준비 확인</button></p>
<div id="promotion-summary" class="preview-summary"><div class="muted">Build a candidate, complete governance/evidence, then assess. / Candidate를 생성하고 거버넌스·근거를 완성한 뒤 평가하세요.</div></div>
<details><summary>Diagnostics JSON / 진단 JSON</summary><pre id="promotion-output">—</pre></details>
<script>
const d=document.getElementById('promotion-draft'),c=document.getElementById('promotion-candidate'),s=document.getElementById('promotion-summary'),o=document.getElementById('promotion-output');
async function loadDraftTemplate(){const r=await fetch('/api/drafts/templates/equity_fcff');const j=await r.json();d.value=JSON.stringify(j,null,2);}
function parseArea(area,label){try{return JSON.parse(area.value)}catch(e){throw new Error(label+' JSON error / JSON 오류: '+e.message)}}
async function post(path,payload){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const j=await r.json();o.textContent=JSON.stringify(j,null,2);if(!r.ok)throw new Error(j.error||('HTTP '+r.status));return j;}
async function buildCandidate(){try{const j=await post('/api/promotion/build',parseArea(d,'Draft'));c.value=JSON.stringify(j,null,2);s.innerHTML='<div class="warn"><strong>CANDIDATE_REVIEW</strong><br>All material inputs are enumerated as UNKNOWN. Classify each before review. / 모든 중요 입력이 UNKNOWN으로 열거되었습니다. 검토 전 분류하세요.</div>';}catch(e){s.innerHTML='<div class="bad">'+String(e)+'</div>';}}
async function assessCandidate(){try{const j=await post('/api/promotion/assess',parseArea(c,'Candidate'));const cls=j.ready_for_review?'good':'warn';s.innerHTML='<div class="'+cls+'"><strong>Ready for review / 검토 준비: '+j.ready_for_review+'</strong><br>Scope SHA-256: <code>'+String(j.review_scope_sha256)+'</code><br>Blockers / 차단요인: '+j.blockers.length+'</div>'; }catch(e){s.innerHTML='<div class="bad">'+String(e)+'</div>';}}
async function checkPromotion(){try{const j=await post('/api/promotion/check',parseArea(c,'Candidate'));s.innerHTML='<div class="good"><strong>'+j.status+'</strong><br>'+j.next_action_ko+'<br><span class="muted">CANONICAL = false</span></div>';}catch(e){s.innerHTML='<div class="bad">'+String(e)+'</div>';}}
loadDraftTemplate();
</script>
"""
    return product_layout("Promotion Review — Valuation Intelligence Hub", body)


def _dashboard_with_promotion_link(repo: Path) -> str:
    page = _dashboard_with_draft_link(repo)
    marker = '<h2>Canonical cases / 정식 사례</h2>'
    banner = (
        '<div class="card" style="margin-bottom:18px;border-color:#60a5fa">'
        '<div><strong>Promotion Review / 승격 검토</strong></div>'
        '<p>Convert a Draft into an evidence-governed candidate and verify human-review hash lock before a repository PR. / '
        'Draft를 근거 거버넌스 Candidate로 전환하고 저장소 PR 전 인간 검토 해시 잠금을 검증합니다.</p>'
        '<a href="/promotion">Open Promotion Review Lab / 승격 검토 랩 열기 →</a></div>'
    )
    return page.replace(marker, banner + marker, 1)


def make_handler(root: Path | None = None):
    repo = root.resolve() if root else find_repo_root()
    Base = make_draft_handler(repo)

    class PromotionHandler(Base):
        def _promotion_payload(self) -> dict:
            raw = self.headers.get("Content-Length", "0")
            try:
                length = int(raw)
            except ValueError as exc:
                raise CaseServiceError("invalid Content-Length / Content-Length 오류") from exc
            if length <= 0 or length > MAX_PROMOTION_REQUEST_BYTES:
                raise CaseServiceError("promotion request size invalid / 승격 요청 크기 오류")
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise CaseServiceError("invalid promotion JSON / 승격 JSON 오류") from exc
            if not isinstance(payload, dict):
                raise CaseServiceError("promotion payload must be a JSON object / 승격 payload는 JSON 객체여야 합니다")
            return payload

        def do_GET(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            try:
                if path == "/":
                    self._send(HTTPStatus.OK, _dashboard_with_promotion_link(repo).encode("utf-8"), "text/html; charset=utf-8")
                    return
                if path == "/promotion":
                    self._send(HTTPStatus.OK, render_promotion_lab().encode("utf-8"), "text/html; charset=utf-8")
                    return
                super().do_GET()
            except CaseServiceError as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

        def do_POST(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            if path not in {"/api/promotion/build", "/api/promotion/assess", "/api/promotion/check"}:
                super().do_POST()
                return
            try:
                payload = self._promotion_payload()
                if path.endswith("/build"):
                    result = build_candidate(payload)
                elif path.endswith("/assess"):
                    result = assess_candidate(payload)
                else:
                    result = promotion_check(payload)
                self._send(HTTPStatus.OK, legacy_web._json_bytes(result), "application/json; charset=utf-8")
            except CaseServiceError as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

    return PromotionHandler


def serve(*, host: str = "127.0.0.1", port: int = 8765, root: Path | None = None) -> None:
    if not 0 < port < 65536:
        raise ValueError("port must be in 1..65535 / 포트 범위 오류")
    server = ThreadingHTTPServer((host, port), make_handler(root))
    print(f"Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}")
    print("Draft Lab / Draft 랩: /draft")
    print("Promotion Review / 승격 검토: /promotion")
    print("Press Ctrl+C to stop / 종료하려면 Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
