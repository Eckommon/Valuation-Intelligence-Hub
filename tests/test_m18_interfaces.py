"""M18 CLI/Web contracts for governed derived financial evidence."""
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
from valuation_hub.web_derived import make_handler, render_derived_lab

ROOT = Path(__file__).resolve().parents[1]


def _hash(value: dict, field: str) -> str:
    payload = copy.deepcopy(value)
    payload.pop(field, None)
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _obs(metric: str, value: int | float, *, klass: str = "NORMALIZED_FACT") -> dict:
    item = {
        "schema_version": "financial-observation-v0.1",
        "status": "FINANCIAL_OBSERVATION_NORMALIZED",
        "canonical": False,
        "class": klass,
        "metric": metric,
        "value": value,
        "unit": "KRW",
        "entity": {"id": "DART_CORP:00126380", "source_system": "TEST", "financial_scope": "CFS"},
        "period": {"kind": "DURATION_ANNUAL", "start": "2025-01-01", "end": "2025-12-31", "duration_days": 365, "fiscal_year": 2025, "fiscal_period": "FY", "fiscal_quarter": 4, "report_stage": "FY", "date_precision": "EXACT"},
        "lineage": {"normalization_rule": "TEST"},
        "observation_sha256": "",
    }
    item["observation_sha256"] = _hash(item, "observation_sha256")
    return item


def _post(base: str, path: str, payload: dict) -> tuple[int, dict]:
    req = Request(base + path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=4) as response:
        return response.status, json.loads(response.read().decode())


def test_cli_dispatch_exposes_m18_commands() -> None:
    for command in ("derive-operating-margin", "derive-net-margin", "derived-validate"):
        assert cli_entry._command([command]) == command


def test_cli_derive_and_validate_round_trip(tmp_path: Path, capsys) -> None:
    operating = tmp_path / "op.json"
    revenue = tmp_path / "rev.json"
    operating.write_text(json.dumps(_obs("operating_income", 120)), encoding="utf-8")
    revenue.write_text(json.dumps(_obs("revenue", 1000)), encoding="utf-8")
    assert cli_entry.main(["derive-operating-margin", str(operating), str(revenue)]) == 0
    derived = json.loads(capsys.readouterr().out)
    assert derived["value"] == 0.12
    assert derived["semantic_boundary"]["forecast_direct_bind"] is False
    output = tmp_path / "derived.json"
    output.write_text(json.dumps(derived), encoding="utf-8")
    assert cli_entry.main(["derived-validate", str(output)]) == 0
    checked = json.loads(capsys.readouterr().out)
    assert checked["status"] == "PASS_DERIVED_FINANCIAL_EVIDENCE_VALIDATION"


def test_web_lab_is_calculate_only_and_not_forecast() -> None:
    page = render_derived_lab()
    assert "CALCULATE ONLY · NOT FORECAST" in page
    assert "Historical fact ≠ forecast assumption" in page
    assert "/api/derived/calculate" in page
    assert "/api/derived/write" not in page
    assert "/api/derived/apply" not in page


def test_web_derived_round_trip() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        _, derived = _post(base, "/api/derived/calculate", {"kind": "net", "numerator": _obs("net_income", 70), "revenue": _obs("revenue", 1000)})
        assert derived["value"] == 0.07
        assert derived["canonical"] is False
        assert derived["semantic_boundary"]["historical_only"] is True
        _, checked = _post(base, "/api/derived/validate", {"derived": derived})
        assert checked["status"] == "PASS_DERIVED_FINANCIAL_EVIDENCE_VALIDATION"
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=4)


def test_web_rejects_credentials_and_wrong_semantics() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        for payload in (
            {"kind": "operating", "numerator": _obs("operating_income", 10), "revenue": _obs("revenue", 100), "api_key": "secret"},
            {"kind": "operating", "numerator": _obs("net_income", 10), "revenue": _obs("revenue", 100)},
        ):
            req = Request(base + "/api/derived/calculate", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
            try:
                urlopen(req, timeout=4)
                raise AssertionError("invalid derived request accepted")
            except HTTPError as exc:
                assert exc.code == 400
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=4)
