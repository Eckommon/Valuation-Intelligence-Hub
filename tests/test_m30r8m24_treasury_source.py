"""Synthetic-only strict M30-R8M24-RF Treasury ten-year dated-cell tests."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub import ingr_wacc_treasury_source as rf
from valuation_hub.ingr_r8_m24_readiness import _rows
from valuation_hub.external_source import (
    validate_external_source_snapshot,
    validate_wacc_source_input_against_snapshot,
)
from valuation_hub.wacc_assumption import REQUIRED_METRICS, validate_wacc_source_input

FAKE_HTML = """<!doctype html><html><body>
<h1>Test-only Treasury 2026 September mock source: NOT REAL MARKET DATA</h1>
<table>
<thead><tr><th>Date</th><th>7 YR</th><th>10 YR</th><th>20 YR</th></tr></thead>
<tbody>
<tr><td>09/11/2026</td><td>4.87</td><td>4.96</td><td>5.38</td></tr>
<tr><td>09/14/2026</td><td>4.88</td><td>4.97</td><td>5.37</td></tr>
<tr><td>09/15/2026</td><td>4.91</td><td>5.00</td><td>5.40</td></tr>
</tbody></table></body></html>"""


def test_strict_dated_ten_year_cell_avoids_seven_year_and_future_rows():
    result = rf.extract_treasury_ten_year(FAKE_HTML)
    assert result["date"] == "2026-09-14"
    assert result["maturity"] == "10 YR"
    assert result["yield_percent"] == pytest.approx(4.97)
    assert result["rate_decimal"] == pytest.approx(.0497)
    assert result["source_table_row"][1] == "4.88"
    assert result["source_table_row"][2] == "4.97"


def test_immutable_snapshot_and_wacc_input_preserve_exact_sha_and_fact_class():
    item = rf.create_treasury_fact_from_raw(FAKE_HTML, captured_at="2026-10-14T12:01:00+00:00")
    snap, wacc, proof = (item["snapshot"], item["wacc_source_input"], item["cell_proof"])
    validate_external_source_snapshot(snap)
    validate_wacc_source_input(wacc)
    validate_wacc_source_input_against_snapshot(wacc, snap)
    assert wacc["metric"] == "risk_free_rate"
    assert wacc["claim_class"] == "FACT"
    assert wacc["unit"] == "decimal"
    assert wacc["value"] == .0497
    assert wacc["observed_on"] == rf.DATE
    assert wacc["source"]["tier"] == "A"
    assert wacc["source"]["source_sha256"] == snap["snapshot_sha256"]
    assert proof["reviewed_wacc"] is False
    assert proof["human_reviewed"] is False
    ready = _rows([wacc], [snap])
    assert ready[0]["status"] == "FRESH_SOURCE_INPUT_CANDIDATE"
    assert sum(row["status"] == "MISSING_SOURCE_INPUT" for row in ready) == 6
    assert [r["metric"] for r in ready] == list(REQUIRED_METRICS)


@pytest.mark.parametrize("bad_html", [
    FAKE_HTML.replace("09/14/2026", "09/13/2026"),
    FAKE_HTML.replace("<th>10 YR</th>", "<th>30 YR</th>"),
    FAKE_HTML.replace("<td>4.97</td>", "<td>4.67</td>"),
    FAKE_HTML.replace("<td>4.97</td>", "<td>N/A</td>"),
    FAKE_HTML.replace("</tbody>", "<tr><td>09/14/2026</td><td>4.88</td><td>4.97</td><td>5.37</td></tr></tbody>"),
])
def test_fail_closed_on_wrong_date_maturity_value_or_duplicates(bad_html):
    with pytest.raises(CaseServiceError):
        rf.create_treasury_fact_from_raw(bad_html, captured_at="2026-10-14T12:01:00+00:00")


def test_csv_supports_exact_column_order_and_ignores_non_ten_year_values():
    csv_text = "Date,7 YR,10 YR,20 YR\n09/11/2026,4.87,4.96,5.38\n09/14/2026,4.88,4.97,5.37\n"
    result = rf.extract_treasury_ten_year(csv_text)
    assert result["rate_decimal"] == .0497


def test_built_proof_rejects_substitution_after_snapshot_sealed():
    item = rf.create_treasury_fact_from_raw(FAKE_HTML, captured_at="2026-10-14T12:01:00+00:00")
    snap = copy.deepcopy(item["snapshot"])
    snap["raw_text"] = snap["raw_text"].replace("09/14/2026", "09/15/2026")
    with pytest.raises(CaseServiceError):
        validate_external_source_snapshot(snap)


def test_offline_materialize_only_gitignored_and_never_overwrites(tmp_path: Path):
    workspace = tmp_path / "workspace" / "source_snapshots"
    workspace.mkdir(parents=True)
    raw_path = workspace / "mock_treasury_202609.html"
    raw_path.write_text(FAKE_HTML, encoding="utf-8")
    result = rf.materialize_treasury_fact(tmp_path, raw_path)
    assert result["status"] == "REAL_INGR_RISK_FREE_RATE_SOURCE_CANDIDATE_READY_FOR_REVIEW"
    assert result["human_review_completed"] is False
    assert result["reviewed_wacc_package"] is None
    assert Path(result["source_snapshot_path"]).exists()
    assert Path(result["wacc_input_path"]).exists()
    assert Path(result["cell_proof_path"]).exists()
    x = json.loads(Path(result["wacc_input_path"]).read_text(encoding="utf-8"))
    y = json.loads(Path(result["source_snapshot_path"]).read_text(encoding="utf-8"))
    assert x["source"]["source_sha256"] == y["snapshot_sha256"]


def test_no_data_if_source_path_is_outside_workspace(tmp_path: Path):
    outside = tmp_path / "treasury.html"
    outside.write_text(FAKE_HTML, encoding="utf-8")
    with pytest.raises(CaseServiceError):
        rf.materialize_treasury_fact(tmp_path, outside)
