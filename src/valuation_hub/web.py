"""Read-oriented local Web application / 읽기 중심 로컬 Web 애플리케이션.

The Web layer is intentionally thin. It calls the canonical case-service layer
and never reimplements valuation formulas.

Web 계층은 의도적으로 얇게 유지하며 정식 case-service 계층을 호출하고
가치평가 공식을 재구현하지 않는다.
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
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root{{--bg:#0f172a;--panel:#111827;--card:#182235;--text:#e5e7eb;--muted:#94a3b8;--line:#334155;--accent:#60a5fa;--good:#34d399;--warn:#fbbf24}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
a{{color:var(--accent);text-decoration:none}}a:hover{{text-decoration:underline}}.wrap{{max-width:1180px;margin:auto;padding:28px 20px 64px}}
header{{display:flex;justify-content:space-between;gap:20px;align-items:center;margin-bottom:28px}}h1{{font-size:28px;margin:0}}h2{{font-size:20px;margin:28px 0 12px}}.muted{{color:var(--muted)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}}.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px}}
.kpi{{font-size:25px;font-weight:750;margin-top:7px}}.tag{{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:4px 9px;font-size:12px;color:var(--muted);margin:2px 4px 2px 0}}
table{{width:100%;border-collapse:collapse;background:var(--card);border-radius:12px;overflow:hidden}}th,td{{padding:11px 12px;text-align:left;border-bottom:1px solid var(--line)}}th{{color:var(--muted);font-size:12px;text-transform:uppercase}}.good{{color:var(--good)}}.warn{{color:var(--warn)}}code{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}}.error{{border-color:#ef4444}}
</style>
</head><body><div class="wrap"><header><div><h1>Valuation Intelligence Hub</h1><div class="muted">Evidence-grounded valuation / 근거 기반 가치분석</div></div><a href="/">Dashboard / 대시보드</a></header>{body}</div></body></html>"""


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


def render_case(case_id: str, root: Path | None = None) -> str:
    view = case_view(case_id, root)
    currency = view["currency"]
    classification = view.get("classification", {})
    tags = "".join(
        f'<span class="tag">{html.escape(str(value))}</span>'
        for value in (view["model"], view["model_version"], view["promotion_gate"], view["valuation_as_of"])
    )
    runtime = view["runtime"]
    if view["model"] == "equity_fcff":
        rows = "".join(
            f'<tr><td>{name}</td><td>{_fmt_number(runtime[name]["value_per_share"], currency)}</td><td>{_fmt_number(runtime[name]["enterprise_value"], currency)}</td></tr>'
            for name in ("BEAR", "BASE", "BULL")
        )
        model_section = f'<h2>Scenario valuation / 시나리오 가치평가</h2><table><thead><tr><th>Scenario</th><th>Value / Share</th><th>Enterprise Value</th></tr></thead><tbody>{rows}</tbody></table>'
    else:
        rows = "".join(
            f'<tr><td>{html.escape(name)}</td><td>{item["probability"]:.1%}</td><td>{_fmt_number(item["present_value_per_share"], currency)}</td></tr>'
            for name, item in runtime["scenarios"].items()
        )
        expected = _fmt_number(runtime["expected_present_value_per_share"], currency)
        model_section = f'<h2>Probability-weighted valuation / 확률가중 가치평가</h2><div class="card"><div class="muted">Expected present value/share / 기대 현재 주당가치</div><div class="kpi">{expected}</div></div><table><thead><tr><th>Scenario</th><th>Probability</th><th>PV / Share</th></tr></thead><tbody>{rows}</tbody></table>'
    decision = classification.get("decision_note_ko") or classification.get("decision_note_en") or classification.get("valuation_state") or "—"
    body = (
        f'<a href="/">← Back / 돌아가기</a><h2>{html.escape(view["display_name_en"])} / {html.escape(view["display_name_ko"])}</h2>{tags}'
        f'<div class="grid"><div class="card"><div class="muted">Market price / 시장가격</div><div class="kpi">{_fmt_number(view["market_price"], currency)}</div></div>'
        f'<div class="card"><div class="muted">Evidence gate / 근거 게이트</div><div class="kpi good">PASS</div><div>{html.escape(view["promotion_gate"])}</div></div>'
        f'<div class="card"><div class="muted">Grounding / 근거화</div><div class="kpi good">{html.escape(str(view["grounded"]))}</div><div>{html.escape(str(view["evidence_status"]))}</div></div></div>'
        + model_section
        + f'<h2>Decision context / 판단 맥락</h2><div class="card"><p>{html.escape(str(decision))}</p></div>'
        + f'<p class="muted">API: <a href="/api/cases/{html.escape(case_id)}">/api/cases/{html.escape(case_id)}</a></p>'
    )
    return _layout(f'{view["display_name_en"]} — Valuation Intelligence Hub', body)


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")


def make_handler(root: Path | None = None) -> type[BaseHTTPRequestHandler]:
    repo = root.resolve() if root else find_repo_root()

    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
            path = unquote(urlparse(self.path).path)
            try:
                if path == "/healthz":
                    self._send(HTTPStatus.OK, _json_bytes({"ok": True}), "application/json; charset=utf-8")
                    return
                if path == "/api/cases":
                    self._send(HTTPStatus.OK, _json_bytes(list_cases(repo)), "application/json; charset=utf-8")
                    return
                if path.startswith("/api/cases/"):
                    case_id = path.removeprefix("/api/cases/")
                    self._send(HTTPStatus.OK, _json_bytes(case_view(case_id, repo)), "application/json; charset=utf-8")
                    return
                if path == "/":
                    body = render_dashboard(repo).encode("utf-8")
                    self._send(HTTPStatus.OK, body, "text/html; charset=utf-8")
                    return
                if path.startswith("/case/"):
                    case_id = path.removeprefix("/case/")
                    body = render_case(case_id, repo).encode("utf-8")
                    self._send(HTTPStatus.OK, body, "text/html; charset=utf-8")
                    return
                self._send(HTTPStatus.NOT_FOUND, b"Not Found", "text/plain; charset=utf-8")
            except CaseServiceError as exc:
                payload = {"ok": False, "error": str(exc)}
                if path.startswith("/api/"):
                    self._send(HTTPStatus.NOT_FOUND, _json_bytes(payload), "application/json; charset=utf-8")
                else:
                    body = _layout("Blocked / 차단", f'<div class="card error"><h2>BLOCKED / 차단</h2><p>{html.escape(str(exc))}</p></div>').encode("utf-8")
                    self._send(HTTPStatus.NOT_FOUND, body, "text/html; charset=utf-8")

        def log_message(self, format: str, *args: object) -> None:
            return

    return Handler


def serve(*, host: str = "127.0.0.1", port: int = 8765, root: Path | None = None) -> None:
    """Run local read-only Web MVP / 로컬 읽기 전용 Web MVP 실행."""
    if not 0 < port < 65536:
        raise ValueError("port must be in 1..65535 / 포트 범위 오류")
    server = ThreadingHTTPServer((host, port), make_handler(root))
    print(f"Valuation Intelligence Hub Web / Web 앱: http://{host}:{port}")
    print("Press Ctrl+C to stop / 종료하려면 Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
