"""Promotion Review Web integration tests / 승격 검토 Web 통합테스트."""

from __future__ import annotations

import hashlib
import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from valuation_hub.draft_service import template
from valuation_hub.promotion import validate_candidate
from valuation_hub.web_promotion import make_handler, render_promotion_lab

ROOT = Path(__file__).resolve().parents[1]


def _post(url: str, payload: dict):
    request = Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    return urlopen(request, timeout=3)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _complete(candidate: dict) -> dict:
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
            claim_id = "web_" + path.replace(".", "_")
            binding.update({"class": "FACT", "claim_ids": [claim_id], "rationale": "Observed value."})
            evidence.append(
                {
                    "claim_id": claim_id,
                    "class": "FACT",
                    "metric": path,
                    "value": observed[path],
                    "unit": draft["currency"],
                    "as_of": "2026-09-11",
                    "status": "CURRENT",
                    "waiver": None,
                    "source": {"publisher": "Web test evidence", "locator": "https://example.invalid/web", "tier": "B"},
                }
            )
        else:
            binding.update({"class": "ASSUMPTION", "claim_ids": [], "rationale": "Reviewed forward assumption."})
    candidate["evidence"] = evidence
    return candidate


def test_promotion_lab_exposes_noncanonical_review_boundary() -> None:
    page = render_promotion_lab()
    assert "Promotion Review Lab / 승격 검토 랩" in page
    assert "No automatic canonicalization" in page
    assert "REVIEW_APPROVED_READY_FOR_PR" in page


def test_http_promotion_build_assess_and_check_preserves_canonical_state() -> None:
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
            assert "Open Promotion Review Lab" in page

        draft = template("equity_fcff", ROOT)
        with _post(base + "/api/promotion/build", draft) as response:
            candidate = json.loads(response.read())
            assert candidate["status"] == "CANDIDATE_REVIEW"
            assert candidate["canonical"] is False

        candidate = _complete(candidate)
        with _post(base + "/api/promotion/assess", candidate) as response:
            assessment = json.loads(response.read())
            assert assessment["ready_for_review"] is True
            scope_hash = assessment["review_scope_sha256"]

        candidate["review"] = {
            "decision": "APPROVE",
            "reviewer": "web-human-reviewer",
            "reviewed_at": "2026-09-11T14:35:00+09:00",
            "rationale": "Human review completed for PR readiness.",
            "scope_sha256": scope_hash,
        }
        with _post(base + "/api/promotion/check", candidate) as response:
            result = json.loads(response.read())
            assert result["status"] == "REVIEW_APPROVED_READY_FOR_PR"
            assert result["canonical"] is False
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=3)
    after = {path: _digest(path) for path in protected}
    assert before == after


def test_http_promotion_check_rejects_mutated_review_scope() -> None:
    candidate = _complete(__import__("valuation_hub.promotion", fromlist=["build_candidate"]).build_candidate(template("equity_fcff", ROOT)))
    assessment = validate_candidate(candidate)
    candidate["review"] = {
        "decision": "APPROVE",
        "reviewer": "web-human-reviewer",
        "reviewed_at": "2026-09-11T14:40:00+09:00",
        "rationale": "Reviewed.",
        "scope_sha256": assessment["review_scope_sha256"],
    }
    next(item for item in candidate["input_governance"] if item["class"] == "ASSUMPTION")["rationale"] += " mutated"

    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            _post(base + "/api/promotion/check", candidate)
            raise AssertionError("expected HTTPError")
        except HTTPError as exc:
            assert exc.code == 400
            payload = json.loads(exc.read())
            assert "hash mismatch" in payload["error"]
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=3)
