"""Local Web application / 로컬 Web 애플리케이션.

The Web layer stays thin: grounded reads and non-canonical previews are routed
through shared services/kernels; valuation formulas are never reimplemented here.

Web 계층은 얇게 유지한다. 근거화 조회와 비정식 preview는 공통 서비스·커널로
라우팅하며 가치평가 공식을 본 계층에서 재구현하지 않는다.
"""

from __future__ import annotations

import html
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from valuation_hub.case_service import (
    CaseServiceError,
    find_repo_root,
    list_cases,
    run_case,
    validate_case,
)
from valuation_hub.interactive import evidence_view, preview_case

MAX_REQUEST_BYTES = 64 * 1024


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CaseServiceError(f"web metadata read failed / Web 메타데이터 읽기 실패: {path}") from exc


def _entry(case_id: str, root: Path) -> dict[str, Any]:
    for item in list_cases(root):
        if item["case_id"] == case_id:
            return item
    raise CaseServiceError(f"unknown case / 알 수 없는 사례: {case_id}")


def case_view(case_id: str, root: Path | None = None) -> dict[str, Any]:
    """Return a grounded read model for Web/API consumers / Web/API용 근거화 읽기모델."""
    repo = root.resolve() if root else find_repo_root()
    validation = validate_case(case_id, repo)
    runtime = run_case(case_id, repo)
    entry = _entry(case_id, repo)
    case_dir = (repo / entry["path"]).resolve()
    inputs = _read_json(case_dir / "case_inputs.json")
    stored = _read_json(case_dir / "valuation_result.json")
    manifest = _read_json(case_dir / "evidence_manifest.json")
    return {
        "case_id": case_id,
        "display_name_en": entry["display_name_en"],
        "display_name_ko": entry["display_name_ko"],
        "asset_class": entry["asset_class"],
        "model": runtime["model"],
        "model_version": runtime["model_version"],
        "valuation_as_of": runtime["valuation_as_of"],
        "currency": inputs.get("currency"),
        "market_price": runtime["market_price"],
        "promotion_gate": validation["promotion_gate"],
        "grounded": runtime["grounded"],
        "runtime": runtime["runtime"],
        "classification": stored.get("classification", {}),
        "stored_status": stored.get("status"),
        "evidence_status": manifest.get("status"),
    }


def _fmt_number(value: float | int | None, currency: str | None = None) -> str:
    if value is None:
        return "—"
    if currency == "KRW":
        return f"₩{value:,.0f}"
    if currency == "USD":
        return f"${value:,.4f}" if abs(float(value)) < 100 else f"${value:,.2f}"
    return f"{value:,.4f}" if isinstance(value, float) else f"{value:,}"


def _layout(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root{{--bg:#0f172a;--card:#182235;--text:#e5e7eb;--muted:#94a3b8;--line:#334155;--accent:#60a5fa;--good:#34d399;--warn:#fbbf24;--bad:#f87171}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}}
a{{color:var(--accent);text-decoration:none}}a:hover{{text-decoration:underline}}.wrap{{max-width:1180px;margin:auto;padding:28px 20px 64px}}
header{{display:flex;justify-content:space-between;gap:20px;align-items:center;margin-bottom:28px}}h1{{font-size:28px;margin:0}}h2{{font-size:20px;margin:28px 0 12px}}h3{{margin:16px 0 8px}}.muted{{color:var(--muted)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}}.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px}}
.kpi{{font-size:25px;font-weight:750;margin-top:7px}}.tag{{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:4px 9px;font-size:12px;color:var(--muted);margin:2px 4px 2px 0}}
table{{width:100%;border-collapse:collapse;background:var(--card);border-radius:12px;overflow:hidden}}th,td{{padding:10px 11px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}}th{{color:var(--muted);font-size:12px;text-transform:uppercase}}.good{{color:var(--good)}}.warn{{color:var(--warn)}}.bad{{color:var(--bad)}}.error{{border-color:#ef4444}}
input,select,button{{background:#0b1220;color:var(--text);border:1px solid var(--line);border-radius:8px;padding:9px}}button{{cursor:pointer;background:#1d4ed8}}label{{display:flex;flex-direction:column;gap:5px;font-size:13px;color:var(--muted)}}pre{{white-space:pre-wrap;word-break:break-word;background:#0b1220;padding:14px;border-radius:10px;overflow:auto}}
</style></head><body><div class="wrap"><header><div><h1>Valuation Intelligence Hub</h1><div class="muted">Evidence-grounded valuation / 근거 기반 가치분석</div></div><a href="/">Dashboard / 대시보드</a></header>{body}</div></body></html>"""


def render_dashboard(root: Path | None = None) -> str:
    repo = root.resolve() if root else find_repo_root()
    cards: list[str] = []
    for entry in list_cases(repo):
        try:
            view = case_view(entry["case_id"], repo)
            cls = view.get("classification", {})
            state = cls.get("valuation_state") or cls.get("decision_note_en") or "grounded"
            cards.append(
                f'<div class="card"><span class="tag">{html.escape(entry["model"])}</span>'
                f'<h2>{html.escape(entry["display_name_en"])} / {html.escape(entry["display_name_ko"])}</h2>'
                f'<div class="muted">{html.escape(str(state))}</div>'
                f'<p><b>Market / 시장가격</b><br><span class="kpi">{_fmt_number(view["market_price"], view["currency"])}</span></p>'
                f'<a href="/case/{html.escape(entry["case_id"])}">Open analysis / 분석 열기 →</a></div>'
            )
        except CaseServiceError as exc:
            cards.append(f'<div class="card error"><h2>{html.escape(entry["case_id"])}</h2><div class="warn">BLOCKED / 차단</div><p>{html.escape(str(exc))}</p></div>')
    return _layout("Valuation Intelligence Hub", '<h2>Canonical cases / 정식 사례</h2><div class="grid">' + "".join(cards) + "</div>")


def _preview_form(view: dict[str, Any]) -> str:
    case_id = html.escape(view["case_id"])
    if view["model"] == "equity_fcff":
        controls = """
<label>Scenario / 시나리오<select id="scenario"><option>BASE</option><option>BEAR</option><option>BULL</option></select></label>
<label>Revenue scale / 매출 배율<input id="revenue_scale" type="number" value="1" min="0.1" max="5" step="0.05"></label>
<label>EBIT margin delta / EBIT 마진 증감<input id="ebit_margin_delta" type="number" value="0" min="-0.10" max="0.10" step="0.005"></label>
<label>WACC override (blank=canonical) / WACC<input id="wacc" type="number" placeholder="canonical" min="0.001" max="0.99" step="0.001"></label>
<label>Terminal growth override / 영구성장률<input id="terminal_growth" type="number" placeholder="canonical" step="0.001"></label>
"""
        js_payload = """const payload={scenario:v('scenario'),revenue_scale:n('revenue_scale'),ebit_margin_delta:n('ebit_margin_delta')}; const w=n('wacc',true),g=n('terminal_growth',true); if(w!==null)payload.wacc=w;if(g!==null)payload.terminal_growth=g;"""
    else:
        controls = """
<label>Failure probability / 실패확률<input id="FAILURE" type="number" value="0.60" min="0" max="1" step="0.01"></label>
<label>Survival probability / 생존확률<input id="SURVIVAL" type="number" value="0.30" min="0" max="1" step="0.01"></label>
<label>Breakout probability / 대성공확률<input id="BREAKOUT" type="number" value="0.10" min="0" max="1" step="0.01"></label>
<label>Revenue scale / 매출 배율<input id="revenue_scale" type="number" value="1" min="0.1" max="5" step="0.05"></label>
<label>Multiple scale / 배수 배율<input id="multiple_scale" type="number" value="1" min="0.1" max="3" step="0.05"></label>
<label>Dilution scale / 희석 배율<input id="dilution_scale" type="number" value="1" min="0.25" max="4" step="0.05"></label>
"""
        js_payload = """const payload={probabilities:{FAILURE:n('FAILURE'),SURVIVAL:n('SURVIVAL'),BREAKOUT:n('BREAKOUT')},revenue_scale:n('revenue_scale'),multiple_scale:n('multiple_scale'),dilution_scale:n('dilution_scale')};"""
    return f"""
<h2>Sandbox preview / 샌드박스 미리보기 <span class="tag warn">PREVIEW · NOT CANONICAL / 비정식</span></h2>
<div class="card"><div class="grid">{controls}</div><p><button onclick="runPreview()">Run preview / 미리보기 실행</button></p><pre id="preview-output">Canonical files are never modified. / 정식 파일은 변경되지 않습니다.</pre></div>
<script>
function v(id){{return document.getElementById(id).value}} function n(id,nullable=false){{const x=v(id);if(nullable&&x==='')return null;return Number(x)}}
async function runPreview(){{{js_payload} const out=document.getElementById('preview-output'); out.textContent='Running / 계산 중...'; try{{const r=await fetch('/api/cases/{case_id}/preview',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(payload)}}); const j=await r.json(); out.textContent=JSON.stringify(j,null,2);}}catch(e){{out.textContent=String(e)}}}}
</script>"""


def render_case(case_id: str, root: Path | None = None) -> str:
    view = case_view(case_id, root)
    currency = view["currency"]
    classification = view.get("classification", {})
    tags = "".join(f'<span class="tag">{html.escape(str(v))}</span>' for v in (view["model"], view["model_version"], view["promotion_gate"], view["valuation_as_of"]))
    runtime = view["runtime"]
    if view["model"] == "equity_fcff":
        rows = "".join(f'<tr><td>{name}</td><td>{_fmt_number(runtime[name]["value_per_share"], currency)}</td><td>{_fmt_number(runtime[name]["enterprise_value"], currency)}</td></tr>' for name in ("BEAR", "BASE", "BULL"))
        model_section = f'<h2>Scenario valuation / 시나리오 가치평가</h2><table><thead><tr><th>Scenario</th><th>Value / Share</th><th>Enterprise Value</th></tr></thead><tbody>{rows}</tbody></table>'
    else:
        rows = "".join(f'<tr><td>{html.escape(name)}</td><td>{item["probability"]:.1%}</td><td>{_fmt_number(item["present_value_per_share"], currency)}</td></tr>' for name, item in runtime["scenarios"].items())
        expected = _fmt_number(runtime["expected_present_value_per_share"], currency)
        model_section = f'<h2>Probability-weighted valuation / 확률가중 가치평가</h2><div class="card"><div class="muted">Expected present value/share / 기대 현재 주당가치</div><div class="kpi">{expected}</div></div><table><thead><tr><th>Scenario</th><th>Probability</th><th>PV / Share</th></tr></thead><tbody>{rows}</tbody></table>'
    decision = classification.get("decision_note_ko") or classification.get("decision_note_en") or classification.get("valuation_state") or "—"
    body = (
        f'<a href="/">← Back / 돌아가기</a><h2>{html.escape(view["display_name_en"])} / {html.escape(view["display_name_ko"])}</h2>{tags}'
        f'<p><a href="/case/{html.escape(case_id)}/evidence">Evidence browser / 근거 탐색 →</a></p>'
        f'<div class="grid"><div class="card"><div class="muted">Market price / 시장가격</div><div class="kpi">{_fmt_number(view["market_price"], currency)}</div></div>'
        f'<div class="card"><div class="muted">Evidence gate / 근거 게이트</div><div class="kpi good">PASS</div><div>{html.escape(view["promotion_gate"])}</div></div>'
        f'<div class="card"><div class="muted">Grounding / 근거화</div><div class="kpi good">{html.escape(str(view["grounded"]))}</div><div>{html.escape(str(view["evidence_status"]))}</div></div></div>'
        + model_section + _preview_form(view)
        + f'<h2>Decision context / 판단 맥락</h2><div class="card"><p>{html.escape(str(decision))}</p></div>'
        + f'<p class="muted">API: <a href="/api/cases/{html.escape(case_id)}">case</a> · <a href="/api/cases/{html.escape(case_id)}/evidence">evidence</a></p>'
    )
    return _layout(f'{view["display_name_en"]} — Valuation Intelligence Hub', body)


def render_evidence(case_id: str, root: Path | None = None) -> str:
    data = evidence_view(case_id, root)
    rows: list[str] = []
    for c in data["claims"]:
        source = c.get("source") or {}
        locator = str(source.get("locator") or "")
        source_text = html.escape(str(source.get("publisher") or "—"))
        if locator.startswith("http://") or locator.startswith("https://"):
            source_text = f'<a href="{html.escape(locator, quote=True)}" target="_blank" rel="noreferrer">{source_text}</a>'
        value = c.get("value")
        rows.append(
            f'<tr><td><span class="tag">{html.escape(str(c.get("class","UNKNOWN")))}</span></td>'
            f'<td>{html.escape(str(c.get("metric","—")))}</td><td>{html.escape(str(value))}</td>'
            f'<td>{html.escape(str(c.get("period") or c.get("as_of") or "—"))}</td>'
            f'<td>{source_text}<br><span class="muted">Tier {html.escape(str(source.get("tier") or "—"))}</span></td></tr>'
        )
    body = (
        f'<a href="/case/{html.escape(case_id)}">← Case / 사례로</a><h2>Evidence browser / 근거 탐색</h2>'
        f'<div class="card"><b>{html.escape(data["display_name_en"])} / {html.escape(data["display_name_ko"])}</b><p class="muted">Read-only / 읽기 전용 · {html.escape(data["promotion_gate"])}</p></div>'
        '<h2>Claims / 주장</h2><table><thead><tr><th>Class</th><th>Metric</th><th>Value</th><th>Period / As-of</th><th>Source</th></tr></thead><tbody>' + "".join(rows) + '</tbody></table>'
    )
    return _layout("Evidence — Valuation Intelligence Hub", body)


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")


def make_handler(root: Path | None = None) -> type[BaseHTTPRequestHandler]:
    repo = root.resolve() if root else find_repo_root()

    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status); self.send_header("Content-Type", content_type); self.send_header("Content-Length", str(len(body))); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(body)

        def _error(self, path: str, exc: Exception, status: int = HTTPStatus.BAD_REQUEST) -> None:
            payload = {"ok": False, "error": str(exc)}
            if path.startswith("/api/"):
                self._send(status, _json_bytes(payload), "application/json; charset=utf-8")
            else:
                body = _layout("Blocked / 차단", f'<div class="card error"><h2>BLOCKED / 차단</h2><p>{html.escape(str(exc))}</p></div>').encode("utf-8")
                self._send(status, body, "text/html; charset=utf-8")

        def do_GET(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            try:
                if path == "/healthz": self._send(HTTPStatus.OK, _json_bytes({"ok": True}), "application/json; charset=utf-8"); return
                if path == "/api/cases": self._send(HTTPStatus.OK, _json_bytes(list_cases(repo)), "application/json; charset=utf-8"); return
                if path.startswith("/api/cases/") and path.endswith("/evidence"):
                    case_id = path.removeprefix("/api/cases/").removesuffix("/evidence"); self._send(HTTPStatus.OK, _json_bytes(evidence_view(case_id, repo)), "application/json; charset=utf-8"); return
                if path.startswith("/api/cases/"):
                    case_id = path.removeprefix("/api/cases/"); self._send(HTTPStatus.OK, _json_bytes(case_view(case_id, repo)), "application/json; charset=utf-8"); return
                if path == "/": self._send(HTTPStatus.OK, render_dashboard(repo).encode("utf-8"), "text/html; charset=utf-8"); return
                if path.startswith("/case/") and path.endswith("/evidence"):
                    case_id = path.removeprefix("/case/").removesuffix("/evidence"); self._send(HTTPStatus.OK, render_evidence(case_id, repo).encode("utf-8"), "text/html; charset=utf-8"); return
                if path.startswith("/case/"):
                    case_id = path.removeprefix("/case/"); self._send(HTTPStatus.OK, render_case(case_id, repo).encode("utf-8"), "text/html; charset=utf-8"); return
                self._send(HTTPStatus.NOT_FOUND, b"Not Found", "text/plain; charset=utf-8")
            except CaseServiceError as exc:
                self._error(path, exc, HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            try:
                if not (path.startswith("/api/cases/") and path.endswith("/preview")):
                    self._send(HTTPStatus.NOT_FOUND, b"Not Found", "text/plain; charset=utf-8"); return
                length_raw = self.headers.get("Content-Length", "0")
                try: length = int(length_raw)
                except ValueError as exc: raise CaseServiceError("invalid Content-Length / Content-Length 오류") from exc
                if length <= 0 or length > MAX_REQUEST_BYTES: raise CaseServiceError("preview request size invalid / preview 요청 크기 오류")
                try: payload = json.loads(self.rfile.read(length).decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc: raise CaseServiceError("invalid JSON preview payload / preview JSON 오류") from exc
                case_id = path.removeprefix("/api/cases/").removesuffix("/preview")
                self._send(HTTPStatus.OK, _json_bytes(preview_case(case_id, payload, repo)), "application/json; charset=utf-8")
            except CaseServiceError as exc:
                self._error(path, exc, HTTPStatus.BAD_REQUEST)

        def log_message(self, format: str, *args: object) -> None: return

    return Handler


def serve(*, host: str = "127.0.0.1", port: int = 8765, root: Path | None = None) -> None:
    """Run local Web application / 로컬 Web 애플리케이션 실행."""
    if not 0 < port < 65536: raise ValueError("port must be in 1..65535 / 포트 범위 오류")
    server = ThreadingHTTPServer((host, port), make_handler(root))
    print(f"Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}"); print("Press Ctrl+C to stop / 종료하려면 Ctrl+C")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
