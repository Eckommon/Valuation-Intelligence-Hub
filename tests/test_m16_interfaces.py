"""M16 binding proposal CLI/Web interface contracts / M16 바인딩 제안 인터페이스 계약."""
from __future__ import annotations

import copy
import hashlib
import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from valuation_hub import cli_entry
from valuation_hub.web_binding import make_handler, render_binding_lab

ROOT = Path(__file__).resolve().parents[1]


def _hash(value: dict, field: str) -> str:
    payload = copy.deepcopy(value); payload.pop(field, None)
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _cash(*, klass: str = "NORMALIZED_FACT", value: int = 100) -> dict:
    result = {
        "schema_version": "financial-observation-v0.1", "status": "FINANCIAL_OBSERVATION_NORMALIZED", "canonical": False,
        "class": klass, "metric": "cash", "value": value, "unit": "KRW",
        "entity": {"id": "DART_CORP:00126380", "source_system": "TEST", "financial_scope": "CFS"},
        "period": {"kind": "INSTANT", "start": None, "end": "2026-06-30", "duration_days": None, "fiscal_year": 2026, "fiscal_period": "H1", "fiscal_quarter": 2, "report_stage": "H1", "date_precision": "EXACT"},
        "lineage": {"normalization_rule": "TEST", "source_candidate_sha256": "a" * 64}, "observation_sha256": "",
    }
    result["observation_sha256"] = _hash(result, "observation_sha256")
    return result


def _post(base: str, path: str, payload: dict) -> tuple[int, dict]:
    request = Request(base + path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=4) as response:
        return response.status, json.loads(response.read().decode())


def test_cli_dispatch_exposes_binding_commands() -> None:
    assert cli_entry._command(["binding-build"]) == "binding-build"
    assert cli_entry._command(["binding-validate"]) == "binding-validate"


def test_cli_binding_build_and_validate_are_proposal_only(tmp_path: Path, capsys) -> None:
    observations = tmp_path / "observations.json"
    observations.write_text(json.dumps([_cash()]), encoding="utf-8")
    assert cli_entry.main(["binding-build", str(observations), "--as-of", "2026-09-11"]) == 0
    proposal = json.loads(capsys.readouterr().out)
    assert proposal["canonical"] is False
    assert proposal["completeness"]["direct_bind_count"] == 1
    proposal_file = tmp_path / "proposal.json"
    proposal_file.write_text(json.dumps(proposal), encoding="utf-8")
    assert cli_entry.main(["binding-validate", str(proposal_file)]) == 0
    validation = json.loads(capsys.readouterr().out)
    assert validation["status"] == "PASS_DRAFT_BINDING_PROPOSAL_VALIDATION"


def test_candidate_cash_via_cli_has_zero_direct_bind(tmp_path: Path, capsys) -> None:
    observations = tmp_path / "candidate.json"
    observations.write_text(json.dumps([_cash(klass="NORMALIZED_FACT_CANDIDATE")]), encoding="utf-8")
    assert cli_entry.main(["binding-build", str(observations), "--as-of", "2026-09-11"]) == 0
    proposal = json.loads(capsys.readouterr().out)
    assert proposal["completeness"]["direct_bind_count"] == 0


def test_binding_lab_is_proposal_only_no_apply() -> None:
    page = render_binding_lab()
    assert "PROPOSAL ONLY · NO DRAFT MUTATION" in page
    assert "/api/binding/build" in page
    assert "/api/binding/validate" in page
    assert "/api/binding/apply" not in page
    assert "liabilities ≠ debt" in page
    assert "shares_outstanding ≠ diluted_shares" in page


def test_web_build_validate_and_no_apply_endpoint() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        status, proposal = _post(base, "/api/binding/build", {"observations": [_cash()], "as_of": "2026-09-11", "max_age_days": 550})
        assert status == 200
        assert proposal["completeness"]["direct_bind_count"] == 1
        status, validation = _post(base, "/api/binding/validate", {"proposal": proposal})
        assert status == 200
        assert validation["status"] == "PASS_DRAFT_BINDING_PROPOSAL_VALIDATION"
        req = Request(base + "/api/binding/apply", data=b"{}", headers={"Content-Type": "application/json"}, method="POST")
        try:
            urlopen(req, timeout=4)
            raise AssertionError("unexpected Draft binding apply endpoint")
        except HTTPError as exc:
            assert exc.code in {400, 404, 405}
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=4)


def test_web_rejects_credentials() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        req = Request(base + "/api/binding/build", data=json.dumps({"observations": [_cash()], "as_of": "2026-09-11", "api_key": "secret"}).encode(), headers={"Content-Type": "application/json"}, method="POST")
        try:
            urlopen(req, timeout=4)
            raise AssertionError("credential-bearing binding payload accepted")
        except HTTPError as exc:
            assert exc.code == 400
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=4)
