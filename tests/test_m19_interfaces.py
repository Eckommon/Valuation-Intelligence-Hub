"""M19 isolated debt source/normalization/aggregation interface tests."""
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
from valuation_hub.debt_components import CORE_COMPONENTS
from valuation_hub.web_debt import make_handler, render_debt_lab

ROOT = Path(__file__).resolve().parents[1]


def _sha(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _obs(metric: str, value: int, *, klass: str = "NORMALIZED_FACT") -> dict:
    item = {
        "schema_version": "debt-component-observation-v0.1", "status": "DEBT_COMPONENT_NORMALIZED", "canonical": False, "class": klass,
        "metric": metric, "value": value, "unit": "KRW",
        "entity": {"id": "DART_CORP:00126380", "source_system": "TEST", "financial_scope": "CFS"},
        "period": {"kind": "INSTANT", "start": None, "end": None, "duration_days": None, "fiscal_year": 2026, "fiscal_period": "H1", "fiscal_quarter": 2, "report_stage": "H1", "date_precision": "REPORT_STAGE_ONLY"},
        "lineage": {"normalization_rule": "TEST", "source_candidate_sha256": "a" * 64, "source_class": "FACT" if klass == "NORMALIZED_FACT" else "FACT_CANDIDATE", "source_snapshot_sha256": "b" * 64, "source_body_sha256": "c" * 64, "filing_identity": {}, "source_detail": {"account_id": metric}},
        "observation_sha256": "",
    }
    payload = copy.deepcopy(item); payload.pop("observation_sha256")
    item["observation_sha256"] = _sha(payload)
    return item


def _all() -> list[dict]:
    return [_obs(metric, (index + 1) * 100) for index, metric in enumerate(CORE_COMPONENTS)]


def _post(base: str, path: str, payload: dict) -> tuple[int, dict]:
    req = Request(base + path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=4) as response:
        return response.status, json.loads(response.read().decode())


def test_cli_dispatch_exposes_isolated_m19_commands() -> None:
    for command in ("debt-sec-extract", "debt-dart-extract", "debt-normalize", "debt-component-validate", "debt-aggregate", "debt-validate"):
        assert cli_entry._command([command]) == command


def test_cli_debt_aggregate_validate_round_trip(tmp_path: Path, capsys) -> None:
    observations = tmp_path / "debt-components.json"
    observations.write_text(json.dumps(_all()), encoding="utf-8")
    assert cli_entry.main(["debt-aggregate", str(observations)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["coverage"]["status"] == "COMPLETE_CORE_COMPONENTS"
    assert result["interest_bearing_debt_value"] == 1500
    output = tmp_path / "debt.json"
    output.write_text(json.dumps(result), encoding="utf-8")
    assert cli_entry.main(["debt-validate", str(output)]) == 0
    checked = json.loads(capsys.readouterr().out)
    assert checked["status"] == "PASS_INTEREST_BEARING_DEBT_VALIDATION"


def test_cli_debt_normalize_preserves_opendart_account_lineage(tmp_path: Path, capsys) -> None:
    candidate = {
        "schema_version": "dart-debt-component-candidate-v0.1", "status": "DEBT_COMPONENT_EVIDENCE_CANDIDATE_UNREVIEWED", "canonical": False, "class": "FACT_CANDIDATE",
        "metric": "short_term_borrowings", "value": 123, "unit": "KRW",
        "request_identity": {"corp_code": "00126380", "bsns_year": "2026", "reprt_code": "11012", "fs_div": "CFS"}, "statement_section": "BS",
        "account_selection": {"kind": "account_id", "fallback_index": 0, "fallback_used": False, "equal_precedence_count": 1},
        "row": {"rcept_no": "20260814000001", "account_id": "ifrs-full_ShorttermBorrowings", "account_nm": "단기차입금", "thstrm_amount": "123"},
        "source": {"publisher": "FSS", "source_type": "official", "tier_proposal": "A", "locator": "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json?corp_code=00126380&bsns_year=2026&reprt_code=11012&fs_div=CFS", "snapshot_sha256": "b" * 64, "body_sha256": "c" * 64},
    }
    path = tmp_path / "candidate.json"; path.write_text(json.dumps(candidate), encoding="utf-8")
    assert cli_entry.main(["debt-normalize", str(path)]) == 0
    obs = json.loads(capsys.readouterr().out)
    assert obs["class"] == "NORMALIZED_FACT_CANDIDATE"
    assert obs["lineage"]["source_detail"]["account_id"] == "ifrs-full_ShorttermBorrowings"


def test_web_debt_lab_is_calculate_only() -> None:
    page = render_debt_lab()
    assert "LIABILITIES ≠ DEBT · CALCULATE ONLY" in page
    assert "Missing ≠ zero" in page
    assert "/api/debt/aggregate" in page
    assert "/api/debt/write" not in page
    assert "/api/debt/apply" not in page


def test_web_debt_round_trip_and_partial_visibility() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT)); thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        _, partial = _post(base, "/api/debt/aggregate", {"observations": _all()[:-1]})
        assert partial["coverage"]["status"] == "PARTIAL_COMPONENTS"
        assert partial["known_component_sum"] == 1000
        assert partial["interest_bearing_debt_value"] is None
        assert partial["semantic_boundary"]["eligible_for_draft_direct_bind"] is False
        _, checked = _post(base, "/api/debt/validate", {"debt": partial})
        assert checked["status"] == "PASS_INTEREST_BEARING_DEBT_VALIDATION"
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=4)


def test_web_debt_rejects_credentials() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT)); thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        req = Request(base + "/api/debt/aggregate", data=json.dumps({"observations": _all(), "api_key": "secret"}).encode(), headers={"Content-Type": "application/json"}, method="POST")
        try:
            urlopen(req, timeout=4)
            raise AssertionError("credential-bearing debt request accepted")
        except HTTPError as exc:
            assert exc.code == 400
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=4)
