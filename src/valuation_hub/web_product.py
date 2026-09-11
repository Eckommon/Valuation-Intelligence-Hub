"""Product-oriented Web adapter / 제품 지향 Web 어댑터.

M7 layers decision-oriented visualization on the stable M6 Web/API contract.
All valuation/evidence computation stays in existing services and kernels.

M7은 안정된 M6 Web/API 계약 위에 의사결정 중심 시각화를 추가한다.
가치평가·근거 계산은 기존 서비스·커널에 그대로 둔다.
"""

from __future__ import annotations

import html
import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from valuation_hub import web as legacy_web
from valuation_hub.case_service import CaseServiceError, find_repo_root
from valuation_hub.interactive import evidence_view
from valuation_hub.visualization import (
    equity_market_scenario_chart,
    evidence_classification_summary,
    fcff_trend_chart,
    venture_outcome_chart,
)


def _preview_panel(view: dict[str, Any]) -> str:
    case_id = html.escape(view["case_id"])
    if view["model"] == "equity_fcff":
        controls = """
<label>Scenario / 시나리오<select id="scenario"><option>BASE</option><option>BEAR</option><option>BULL</option></select></label>
<label>Revenue scale / 매출 배율<input id="revenue_scale" type="number" value="1" min="0.1" max="5" step="0.05"></label>
<label>EBIT margin Δ<input id="ebit_margin_delta" type="number" value="0" min="-0.10" max="0.10" step="0.005"></label>
<label>WACC<input id="wacc" type="number" placeholder="canonical" min="0.001" max="0.99" step="0.001"></label>
<label>Terminal growth / 영구성장률<input id="terminal_growth" type="number" placeholder="canonical" step="0.001"></label>
"""
        payload_js = """const p={scenario:v('scenario'),revenue_scale:n('revenue_scale'),ebit_margin_delta:n('ebit_margin_delta')};const w=n('wacc',true),g=n('terminal_growth',true);if(w!==null)p.wacc=w;if(g!==null)p.terminal_growth=g;"""
        value_js = "const value=j.preview?.value_per_share;"
    else:
        controls = """
<label>Failure / 실패<input id="FAILURE" type="number" value="0.60" min="0" max="1" step="0.01"></label>
<label>Survival / 생존<input id="SURVIVAL" type="number" value="0.30" min="0" max="1" step="0.01"></label>
<label>Breakout / 대성공<input id="BREAKOUT" type="number" value="0.10" min="0" max="1" step="0.01"></label>
<label>Revenue scale / 매출 배율<input id="revenue_scale" type="number" value="1" min="0.1" max="5" step="0.05"></label>
<label>Multiple scale / 배수 배율<input id="multiple_scale" type="number" value="1" min="0.1" max="3" step="0.05"></label>
<label>Dilution scale / 희석 배율<input id="dilution_scale" type="number" value="1" min="0.25" max="4" step="0.05"></label>
"""
        payload_js = """const p={probabilities:{FAILURE:n('FAILURE'),SURVIVAL:n('SURVIVAL'),BREAKOUT:n('BREAKOUT')},revenue_scale:n('revenue_scale'),multiple_scale:n('multiple_scale'),dilution_scale:n('dilution_scale')};"""
        value_js = "const value=j.preview?.expected_present_value_per_share;"
    return f"""
<section class="preview-shell">
<div class="section-head"><div><h2>Scenario Lab / 시나리오 랩</h2><p class="muted">Experiment without changing canonical data / 정식 데이터를 변경하지 않는 실험</p></div><span class="state-preview">PREVIEW · NOT CANONICAL</span></div>
<div class="card"><div class="grid compact">{controls}</div><p><button class="primary" onclick="runPreview()">Run preview / 미리보기 실행</button></p>
<div id="preview-summary" class="preview-summary"><div class="muted">Change assumptions and run a preview. / 가정을 변경해 미리보기를 실행하세요.</div></div>
<details><summary>Diagnostics JSON / 진단 JSON</summary><pre id="preview-output">—</pre></details></div></section>
<script>
function v(id){{return document.getElementById(id).value}}function n(id,nullable=false){{const x=v(id);if(nullable&&x==='')return null;return Number(x)}}
function fmt(x){{if(x===undefined||x===null)return '—';return new Intl.NumberFormat(undefined,{{maximumFractionDigits:2}}).format(x)}}
async function runPreview(){{{payload_js}const out=document.getElementById('preview-output'),sum=document.getElementById('preview-summary');sum.innerHTML='<div class="muted">Running / 계산 중...</div>';try{{const r=await fetch('/api/cases/{case_id}/preview',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(p)}});const j=await r.json();out.textContent=JSON.stringify(j,null,2);if(!r.ok){{sum.innerHTML='<div class="bad">'+j.error+'</div>';return;}}{value_js}const market=j.market_price;const gap=(value-market)/market;sum.innerHTML='<div class="grid compact"><div class="mini-kpi"><span>Preview value / 미리보기 가치</span><strong>'+fmt(value)+'</strong></div><div class="mini-kpi"><span>Market / 시장</span><strong>'+fmt(market)+'</strong></div><div class="mini-kpi"><span>Gap / 괴리</span><strong class="'+(gap>=0?'good':'bad')+'">'+(gap*100).toFixed(1)+'%</strong></div></div>';}}catch(e){{sum.innerHTML='<div class="bad">'+String(e)+'</div>';}}}}
</script>"""


def render_product_case(case_id: str, root: Path | None = None) -> str:
    view = legacy_web.case_view(case_id, root)
    runtime, currency = view["runtime"], view["currency"]
    classification = view.get("classification", {})
    tags = "".join(f'<span class="tag">{html.escape(str(v))}</span>' for v in (view["model"], view["model_version"], view["valuation_as_of"]))
    if view["model"] == "equity_fcff":
        chart = equity_market_scenario_chart(runtime, view["market_price"], currency)
        trend = fcff_trend_chart(runtime, currency=currency)
        rows = "".join(f'<tr><td>{name}</td><td>{legacy_web._fmt_number(runtime[name]["value_per_share"], currency)}</td><td>{legacy_web._fmt_number(runtime[name]["enterprise_value"], currency)}</td></tr>' for name in ("BEAR","BASE","BULL"))
        detail = f'<div class="chart-card"><h3>Market vs intrinsic value / 시장 vs 내재가치</h3>{chart}</div><div class="chart-card"><h3>FCFF trend / FCFF 추세</h3>{trend}</div><table><thead><tr><th>Scenario</th><th>Value / share</th><th>Enterprise value</th></tr></thead><tbody>{rows}</tbody></table>'
    else:
        chart = venture_outcome_chart(runtime, view["market_price"], currency)
        rows = "".join(f'<tr><td>{html.escape(name)}</td><td>{item["probability"]:.1%}</td><td>{legacy_web._fmt_number(item["present_value_per_share"],currency)}</td></tr>' for name,item in runtime["scenarios"].items())
        detail = f'<div class="chart-card"><h3>Probability-weighted outcomes / 확률가중 결과</h3>{chart}</div><table><thead><tr><th>Outcome</th><th>Probability</th><th>PV / share</th></tr></thead><tbody>{rows}</tbody></table>'
    decision = classification.get("decision_note_ko") or classification.get("decision_note_en") or classification.get("valuation_state") or "—"
    body = f"""
<div class="breadcrumbs"><a href="/">Dashboard</a><span>›</span><strong>{html.escape(view['display_name_en'])}</strong></div>
<div class="hero"><div><h2>{html.escape(view['display_name_en'])} <span class="muted">/ {html.escape(view['display_name_ko'])}</span></h2>{tags}</div><div class="hero-price"><span>Market / 시장가격</span><strong>{legacy_web._fmt_number(view['market_price'],currency)}</strong></div></div>
<div class="grid status-grid"><div class="card"><span class="eyebrow">Evidence / 근거</span><strong class="good">PASS</strong><small>{html.escape(view['promotion_gate'])}</small></div><div class="card"><span class="eyebrow">Grounded / 근거화</span><strong class="good">YES</strong><small>{html.escape(str(view['evidence_status']))}</small></div><div class="card"><span class="eyebrow">Model / 모델</span><strong>{html.escape(view['model'])}</strong><small>{html.escape(view['model_version'])}</small></div></div>
<div class="section-head"><div><h2>Canonical valuation / 정식 가치평가</h2><p class="muted">Evidence-gated · versioned · regression-locked / 근거게이트 · 버전 · 회귀잠금</p></div><span class="state-canonical">CANONICAL / 정식</span></div>
{detail}
{_preview_panel(view)}
<div class="section-head"><div><h2>Evidence & decision / 근거와 판단</h2></div><a class="button-link" href="/case/{html.escape(case_id)}/evidence">Browse evidence / 근거 탐색 →</a></div>
<div class="card"><p>{html.escape(str(decision))}</p></div>
"""
    return product_layout(f"{view['display_name_en']} — Valuation Intelligence Hub", body)


def render_product_evidence(case_id: str, root: Path | None = None) -> str:
    data = evidence_view(case_id, root)
    summary = evidence_classification_summary(data["classification_counts"])
    rows: list[str] = []
    for c in data["claims"]:
        cls = str(c.get("class","UNKNOWN")); source=c.get("source") or {}; locator=str(source.get("locator") or "")
        source_text=html.escape(str(source.get("publisher") or "—"))
        if locator.startswith(("http://","https://")):
            source_text=f'<a href="{html.escape(locator,quote=True)}" target="_blank" rel="noreferrer">{source_text}</a>'
        rows.append(f'<tr data-claim-class="{html.escape(cls)}"><td><span class="tag">{html.escape(cls)}</span></td><td>{html.escape(str(c.get("metric","—")))}</td><td>{html.escape(str(c.get("value")))}</td><td>{html.escape(str(c.get("period") or c.get("as_of") or "—"))}</td><td>{source_text}<br><small class="muted">Tier {html.escape(str(source.get("tier") or "—"))}</small></td></tr>')
    body=f"""<div class="breadcrumbs"><a href="/case/{html.escape(case_id)}">Case / 사례</a><span>›</span><strong>Evidence / 근거</strong></div>
<div class="section-head"><div><h2>Evidence browser / 근거 탐색</h2><p class="muted">Read-only canonical provenance / 읽기 전용 정식 출처</p></div><span class="state-canonical">READ ONLY</span></div>
{summary}<table id="evidence-table"><thead><tr><th>Class</th><th>Metric</th><th>Value</th><th>Period / As-of</th><th>Source</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<script>document.querySelectorAll('.filter-card').forEach(b=>b.addEventListener('click',()=>{{const cls=b.dataset.class;document.querySelectorAll('#evidence-table tbody tr').forEach(r=>r.style.display=(cls==='ALL'||r.dataset.claimClass===cls)?'':'none');document.querySelectorAll('.filter-card').forEach(x=>x.classList.remove('active'));b.classList.add('active');}}));</script>"""
    return product_layout("Evidence — Valuation Intelligence Hub",body)


def product_layout(title: str, body: str) -> str:
    extra_css="""
<style>
:root{--surface:#182235;--surface2:#0b1220;--border:#334155;--blue:#60a5fa;--green:#34d399;--yellow:#fbbf24;--red:#f87171;--muted2:#94a3b8}
.wrap{max-width:1240px}.breadcrumbs{display:flex;gap:8px;align-items:center;color:var(--muted2);margin-bottom:18px}.hero{display:flex;justify-content:space-between;align-items:flex-end;gap:20px;padding:20px 0}.hero h2{font-size:32px;margin:0 0 8px}.hero-price{text-align:right}.hero-price span,.eyebrow,.mini-kpi span{display:block;color:var(--muted2);font-size:12px}.hero-price strong{font-size:30px}.status-grid .card{display:flex;flex-direction:column;gap:6px}.status-grid strong{font-size:18px}.status-grid small{color:var(--muted2);word-break:break-word}.section-head{display:flex;justify-content:space-between;align-items:center;gap:15px;margin-top:34px}.section-head h2{margin:0}.state-canonical,.state-preview{padding:6px 10px;border-radius:999px;font-size:11px;font-weight:700}.state-canonical{background:#064e3b;color:#a7f3d0}.state-preview{background:#713f12;color:#fde68a}.chart-card{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:16px;margin:14px 0}.viz{width:100%;height:auto;min-height:140px}.svg-label,.svg-value,.svg-axis{fill:#cbd5e1;font:12px system-ui}.svg-value{fill:#f8fafc}.svg-bar{fill:#3b82f6}.svg-grid{stroke:#475569}.legend{display:flex;gap:16px;flex-wrap:wrap}.legend-item{font-size:12px;color:#cbd5e1}.legend-dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:5px}.small{font-size:12px}.compact{grid-template-columns:repeat(auto-fit,minmax(170px,1fr))}.preview-shell{margin-top:34px}.preview-summary{padding:14px;background:var(--surface2);border-radius:10px;margin:12px 0}.mini-kpi{padding:10px;border:1px solid var(--border);border-radius:10px}.mini-kpi strong{font-size:21px;display:block;margin-top:4px}.button-link{border:1px solid var(--border);padding:9px 12px;border-radius:9px}.evidence-summary{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}.filter-card{display:flex;gap:8px;align-items:center;background:var(--surface);border:1px solid var(--border)}.filter-card strong{font-size:18px}.filter-card span{font-size:11px;color:var(--muted2)}.filter-card.active{outline:2px solid var(--blue)}details{margin-top:12px}summary{cursor:pointer;color:var(--muted2)}
@media(max-width:700px){.hero,.section-head{align-items:flex-start;flex-direction:column}.hero-price{text-align:left}.hero h2{font-size:26px}table{font-size:12px}.viz{min-width:580px}.chart-card{overflow-x:auto}}
</style>"""
    base=legacy_web._layout(title,body)
    return base.replace("</head>",extra_css+"</head>")


def make_handler(root: Path | None = None):
    repo=root.resolve() if root else find_repo_root(); Base=legacy_web.make_handler(repo)
    class ProductHandler(Base):
        def do_GET(self) -> None:  # noqa: N802
            path=unquote(urlparse(self.path).path)
            try:
                if path.startswith("/case/") and path.endswith("/evidence"):
                    case_id=path.removeprefix("/case/").removesuffix("/evidence"); self._send(HTTPStatus.OK,render_product_evidence(case_id,repo).encode("utf-8"),"text/html; charset=utf-8"); return
                if path.startswith("/case/") and "/evidence" not in path:
                    case_id=path.removeprefix("/case/"); self._send(HTTPStatus.OK,render_product_case(case_id,repo).encode("utf-8"),"text/html; charset=utf-8"); return
                super().do_GET()
            except CaseServiceError as exc:
                self._error(path,exc,HTTPStatus.NOT_FOUND)
    return ProductHandler


def serve(*, host: str="127.0.0.1", port: int=8765, root: Path | None=None) -> None:
    if not 0 < port < 65536: raise ValueError("port must be in 1..65535 / 포트 범위 오류")
    server=ThreadingHTTPServer((host,port),make_handler(root)); print(f"Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}"); print("Press Ctrl+C to stop / 종료하려면 Ctrl+C")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
