"""Promotion-package Web integration tests / 승격 패키지 Web 통합테스트."""

from __future__ import annotations

import hashlib
import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from valuation_hub.draft_service import template
from valuation_hub.promotion import build_candidate, validate_candidate
from valuation_hub.web_package import make_handler, render_package_lab

ROOT = Path(__file__).resolve().parents[1]


def _post(url: str, payload: dict):
    request = Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    return urlopen(request, timeout=3)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _approved_candidate() -> dict:
    candidate = build_candidate(template("equity_fcff", ROOT))
    draft = candidate["draft"]
    observed = {
        "market_price": draft["market_price"],
        "equity.diluted_shares": draft["equity"]["diluted_shares"],
        "equity.debt": draft["equity"]["debt"],
        "equity.cash": draft["equity"]["cash"],
        "equity.minority_interest": draft["equity"]["minority_interest"],
    }
    evidence = []
    for binding in candidate["input_governance"]:
        path = binding["path"]
        if path in observed:
            claim_id = "web_pkg_" + path.replace(".", "_")
            binding.update({"class": "FACT", "claim_ids": [claim_id], "rationale": "Observed."})
            evidence.append({
                "claim_id": claim_id, "class": "FACT", "metric": path, "value": observed[path],
                "unit": draft["currency"], "as_of": "2026-09-11", "status": "CURRENT", "waiver": None,
                "source": {"publisher": "Web package test", "locator": "https://example.invalid/web-package", "tier": "B"},
            })
        else:
            binding.update({"class": "ASSUMPTION", "claim_ids": [], "rationale": "Reviewed assumption."})
    candidate["evidence"] = evidence
    assessment = validate_candidate(candidate)
    candidate["review"] = {
        "decision": "APPROVE", "reviewer": "web-package-reviewer",
        "reviewed_at": "2026-09-11T15:05:00+09:00", "rationale": "Reviewed for package staging.",
        "scope_sha256": assessment["review_scope_sha256"],
    }
    return candidate


def test_package_lab_labels_staged_noncanonical_boundary() -> None:
    page = render_package_lab()
    assert "Promotion Package Lab / 승격 패키지 랩" in page
    assert "STAGED · NOT CANONICAL" in page
    assert "Not registry-executable yet" in page


def test_http_package_build_validate_is_memory_only_and_preserves_canonical_state() -> None:
    protected = [
        ROOT / "registry" / "cases.json",
        ROOT / "analyses" / "equities" / "KR_229640_LS_ECO_ENERGY" / "valuation_result.json",
    ]
    before = {path: _digest(path) for path in protected}
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        with urlopen(base + "/", timeout=3) as response:
            page = response.read().decode("utf-8")
            assert "Open Promotion Package Lab" in page

        build_payload = {
            "candidate": _approved_candidate(),
            "case_id": "KR_WEB_PACKAGE_TEST",
            "display_name_en": "Web Package Test",
            "display_name_ko": "Web 패키지 테스트",
            "asset_class": "public_equity",
        }
        with _post(base + "/api/package/build", build_payload) as response:
            package = json.loads(response.read())
            assert package["status"] == "PROMOTION_PACKAGE_STAGED"
            assert package["canonical"] is False

        with _post(base + "/api/package/validate", package) as response:
            result = json.loads(response.read())
            assert result["valid"] is True
            assert result["compatibility_status"] == "NOT_EXECUTABLE_UNTIL_CANONICAL_ADAPTER"
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=3)
    after = {path: _digest(path) for path in protected}
    assert before == after


def test_http_package_build_rejects_existing_canonical_id() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        payload = {
            "candidate": _approved_candidate(),
            "case_id": "KR_010120_LS_ELECTRIC",
            "display_name_en": "Collision",
            "display_name_ko": "충돌",
            "asset_class": "public_equity",
        }
        try:
            _post(base + "/api/package/build", payload)
            raise AssertionError("expected HTTPError")
        except HTTPError as exc:
            assert exc.code == 400
            error = json.loads(exc.read())
            assert "충돌" in error["error"]
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=3)


def test_http_package_validate_detects_tamper() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        payload = {
            "candidate": _approved_candidate(), "case_id": "KR_WEB_PACKAGE_TAMPER",
            "display_name_en": "Tamper", "display_name_ko": "변조", "asset_class": "public_equity",
        }
        with _post(base + "/api/package/build", payload) as response:
            package = json.loads(response.read())
        package["artifacts"]["REGISTRY_PROPOSAL.json"]["registration_blocked"] = False
        try:
            _post(base + "/api/package/validate", package)
            raise AssertionError("expected HTTPError")
        except HTTPError as exc:
            assert exc.code == 400
            error = json.loads(exc.read())
            assert "artifact hash mismatch" in error["error"]
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=3)
