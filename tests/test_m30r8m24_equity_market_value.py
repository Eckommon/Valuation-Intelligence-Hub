"""M30-R8M24-EQV: synthetic-only two-source market-cap proxy tests."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from valuation_hub import ingr_wacc_equity_market_value as cap
from valuation_hub import ingr_r8_m24_readiness as readiness
from valuation_hub import sec_scope_reconciliation_r8 as scope
from valuation_hub.case_service import CaseServiceError
from valuation_hub.external_source import (
    build_external_source_snapshot, validate_external_source_snapshot,
)

PRICE_HTML = """<html><body><h1>INGR (NYSE) stock history</h1>
<table><thead>
<tr><th>Date</th><th>Open</th><th>High</th><th>Low</th>
<th>Close</th><th>Adj. Close</th><th>Volume</th></tr></thead>
<tbody>
<tr><td>Sep 15, 2026</td><td>98.01</td><td>99.23</td>
<td>97.55</td><td>99.07</td><td>98.21</td><td>612997</td></tr>
<tr><td>Sep 14, 2026</td><td>101.73</td><td>102.24</td>
<td>98.44</td><td>98.63</td><td>97.78</td><td>704761</td></tr>
<tr><td>Sep 11, 2026</td><td>101.46</td><td>101.79</td>
<td>99.82</td><td>100.49</td><td>99.62</td><td>542644</td></tr>
</tbody></table></body></html>"""

COVER = """<section>
<p>Indicate number of shares outstanding as of latest practicable date.</p>
<table><tr><th>Class</th><th>Outstanding as of August 5, 2026</th></tr>
<tr><td>Common Stock, par value $0.01 per share</td>
<td>63,063,979 shares</td></tr></table></section>"""


def _module(name: str):
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location("_eqv_" + name.replace(".py", ""), path)
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    m = _module("test_m30r8scope_reconciliation.py")
    ws, _, _, _, prior = m._context(tmp_path, monkeypatch)
    raw = prior["raw_text"].replace("<h1>Ingredion Incorporated</h1>",
                                     "<h1>Ingredion Incorporated</h1>" + COVER)
    sec = build_external_source_snapshot(
        raw, source_publisher=prior["source"]["publisher"],
        source_type=prior["source"]["source_type"],
        source_tier=prior["source"]["tier"],
        source_locator=prior["source"]["locator"],
        captured_at=prior["capture"]["captured_at"])
    monkeypatch.setattr(cap, "SEC_SHA", sec["snapshot_sha256"])
    monkeypatch.setattr(scope, "SOURCE_SHA", sec["snapshot_sha256"])
    artifact = cap.build_market_cap_proxy(
        PRICE_HTML, sec, captured_at="2026-10-14T15:00:00+00:00")
    return ws, sec, artifact


def _save(p: Path, payload: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, sort_keys=True, ensure_ascii=False), encoding="utf-8")


def test_source_bound_sep14_unadjusted_close_and_aug5_reported_shares(tmp_path, monkeypatch):
    ws, sec, a = _fixture(tmp_path, monkeypatch)
    proof, inp, price = a["proof"], a["wacc_input"], a["price_snapshot"]
    assert cap.extract_unadjusted_close(PRICE_HTML)["price"] == 98.63
    assert proof["reported_common_shares"]["shares"] == 63063979
    assert proof["reported_common_shares"]["observed_on"] == "2026-08-05"
    assert proof["share_lag_days"] == 40
    assert proof["share_count_carryforward"] == "ASSUMPTION_NOT_ASOF_FACT"
    assert inp["value"] == 6220000248.77
    assert inp["metric"] == "equity_market_value"
    assert inp["claim_class"] == "ASSUMPTION"
    assert inp["source"]["source_sha256"] == price["snapshot_sha256"]
    assert cap.validate_market_cap_proxy(proof, inp, price, sec)["human_reviewed"] is False
    assert proof["source_sec_snapshot_sha256"] == sec["snapshot_sha256"]
    assert readiness._rows([inp], [price, sec])[4]["status"] == "EQUITY_MARKET_VALUE_TWO_SOURCE_PROOF_MISSING"
    checked = readiness._rows([inp], [price, sec], [proof])
    assert checked[4]["status"] == "FRESH_SOURCE_INPUT_CANDIDATE"
    assert checked[4]["provenance"]["market_cap_method"]["share_class"] == "ASSUMPTION"


@pytest.mark.parametrize("bad", [
    PRICE_HTML.replace("Sep 14, 2026", "Sep 13, 2026"),
    PRICE_HTML.replace("<th>Close</th>", "<th>Change</th>"),
    PRICE_HTML.replace("<td>98.63</td>", "<td>98.64</td>"),
    PRICE_HTML.replace("</tbody>", "<tr><td>Sep 14, 2026</td><td>101.73</td><td>102.24</td><td>98.44</td><td>98.63</td><td>97.78</td><td>704761</td></tr></tbody>"),
])
def test_price_row_date_close_header_and_duplicates_fail_closed(bad):
    with pytest.raises(CaseServiceError):
        cap.extract_unadjusted_close(bad)


def test_sec_cover_share_count_and_temporal_provenance_tamper_rejected(tmp_path, monkeypatch):
    ws, sec, a = _fixture(tmp_path, monkeypatch)
    tampered = copy.deepcopy(sec)
    tampered["raw_text"] = tampered["raw_text"].replace("63,063,979", "63,900,000")
    with pytest.raises(CaseServiceError):
        cap.validate_market_cap_proxy(a["proof"],a["wacc_input"],a["price_snapshot"],tampered)
    fake = copy.deepcopy(a["proof"])
    fake["reported_common_shares"]["shares"] = 63900000
    with pytest.raises(CaseServiceError):
        cap.validate_market_cap_proxy(fake,a["wacc_input"],a["price_snapshot"],sec)


def test_price_provenance_and_shares_carryforward_are_never_human_review(tmp_path, monkeypatch):
    ws, sec, a = _fixture(tmp_path, monkeypatch)
    bad = copy.deepcopy(a["wacc_input"])
    bad["claim_class"] = "FACT"
    with pytest.raises(CaseServiceError):
        cap.validate_market_cap_proxy(a["proof"],bad,a["price_snapshot"],sec)
    orig = copy.deepcopy(a["price_snapshot"])
    orig["source"]["locator"] = "https://example.com/not-ingr"
    with pytest.raises(CaseServiceError):
        cap.validate_market_cap_proxy(a["proof"],a["wacc_input"],orig,sec)


def test_local_only_storage_and_integrated_readiness_at_most_two_of_seven(tmp_path, monkeypatch):
    ws, sec, a = _fixture(tmp_path, monkeypatch)
    rawpath = ws / "source_snapshots" / "raw_ingr_price.html"
    rawpath.write_text(PRICE_HTML, encoding="utf-8")
    secfile = ws / "source_snapshots" / "INGR_2026Q2_exact_scope_sec.json"
    _save(secfile, sec)
    result = cap.materialize_market_cap_proxy(tmp_path,rawpath,secfile)
    assert result["status"] == "REAL_INGR_EQUITY_MARKET_VALUE_PROXY_READY_FOR_REVIEW"
    inp = json.loads(Path(result["wacc_input_path"]).read_text(encoding="utf-8"))
    proof = json.loads(Path(result["proof_path"]).read_text(encoding="utf-8"))
    price = json.loads(Path(result["price_snapshot_path"]).read_text(encoding="utf-8"))
    assert cap.validate_market_cap_proxy(proof,inp,price,sec)["status"] == "PASS_UNREVIEWED_INGR_EQUITY_MARKET_VALUE_PROXY"
    rows = readiness._rows([inp],[price,sec],[proof])
    assert sum(x["status"] == "FRESH_SOURCE_INPUT_CANDIDATE" for x in rows) == 1
    assert all(row["status"] == "MISSING_SOURCE_INPUT" for row in rows if row["metric"] != "equity_market_value")
    assert result["human_review_completed"] is False
