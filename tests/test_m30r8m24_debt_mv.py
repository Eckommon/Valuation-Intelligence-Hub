"""M30-R8M24-DMV: exact-source synthetic SEC 10-Q/market-value tests."""
from __future__ import annotations

import copy
from pathlib import Path

import pytest

from valuation_hub import ingr_wacc_debt_market_value as debt
from valuation_hub import ingr_r8_m24_readiness as readiness
from valuation_hub.case_service import CaseServiceError
from valuation_hub.external_source import validate_external_source_snapshot

RAW = """<!doctype html><html><body>
<h1>Ingredion Incorporated</h1><p>For the quarterly period ended June 30, 2026</p>
<p>Notes to the Condensed Consolidated Financial Statements (dollars in millions, except per share data)</p>
<h2>5. Fair Value Measurements</h2>
<p>Assets and liabilities measured at fair value on a recurring basis were as follows:</p>
<table><tr><td>As of June 30, 2026</td><td>As of December 31, 2025</td></tr>
<tr><td>Level 1</td><td>Level 2</td><td>Level 3</td><td>Total</td>
<td>Level 1</td><td>Level 2</td><td>Level 3</td><td>Total</td></tr>
<tr><td>Derivative assets</td><td>5</td><td>101</td><td>—</td><td>106</td><td>22</td><td>2</td><td>—</td><td>24</td></tr>
<tr><td>Long-term debt</td><td>—</td><td><strong>1,640</strong></td><td>—</td><td>1,640</td>
<td>—</td><td>1,649</td><td>—</td><td>1,649</td></tr></table>
<p>The carrying values of cash equivalents, short-term investments, accounts receivable,
short-term borrowings and accounts payable approximate fair values.
The fair value of our long-term debt is estimated based on quotations of major securities dealers.</p>
<h2>6. Financing Arrangements</h2>
<p>Debt carrying amounts, net of related discounts, premiums and debt issuance costs, were as follows:</p>
<table><tr><td>As of June 30, 2026</td><td>As of December 31, 2025</td></tr>
<tr><td>3.200% senior notes</td><td>500</td><td>499</td></tr>
<tr><td>Total long-term debt</td><td>1,742</td><td>1,742</td></tr>
<tr><td>Other short-term borrowings</td><td>41</td><td>48</td></tr>
<tr><td>Bridge facility</td><td>—</td><td>—</td></tr>
<tr><td>Total short-term borrowings</td><td>41</td><td>48</td></tr>
<tr><td>Total debt</td><td>$</td><td>1,783</td><td>$</td><td>1,790</td></tr></table>
<p>_________________ (i)The senior notes due October 1, 2026 are classified as long-term debt.</p>
<p>No amounts were outstanding under the Bridge Facility as of June 30, 2026.</p>
<p>No amounts were outstanding under the DDTL Facility as of June 30, 2026.</p>
<h2>7. Pension and Other Postretirement Benefits</h2>
</body></html>"""


def test_exact_sec_debt_fair_value_level2_and_zero_undrawn_acquisition_debt():
    result = debt.extract_debt_mv(RAW)
    assert result["long_term_level2_fair_value_usd_millions"] == 1640
    assert result["short_term_carrying_as_fair_value_usd_millions"] == 41
    assert result["debt_mv_proxy_usd_millions"] == 1681
    assert result["total_carrying_value_usd_millions"] == 1783
    assert result["book_less_proxy_usd_millions"] == 102
    assert result["debt_market_value_usd"] == 1_681_000_000
    assert result["claim_class"] == "ASSUMPTION"


def test_sec_snapshot_and_independent_wacc_proof_required_for_readiness():
    data = debt.build_debt_mv_source(RAW, captured_at="2026-10-15T00:00:00+00:00")
    snap, item, proof = data["snapshot"], data["wacc_input"], data["proof"]
    assert snap["raw_text"] == RAW
    assert validate_external_source_snapshot(snap)["status"] == "PASS_EXTERNAL_SOURCE_SNAPSHOT_VALIDATION"
    assert item["claim_class"] == "ASSUMPTION"
    assert item["unit"] == "USD"
    assert item["observed_on"] == "2026-06-30"
    assert item["source"]["tier"] == "A"
    assert debt.validate_debt_mv_proof(proof, item, snap)["status"] == "PASS_SOURCE_BOUND_DEBT_MV_PROXY_CANDIDATE"
    assert readiness._rows([item], [snap])[5]["status"] == "DEBT_MV_EXPLICIT_METHOD_PROOF_MISSING"
    rows = readiness._rows([item], [snap], [], [], [proof])
    assert rows[5]["status"] == "FRESH_SOURCE_INPUT_CANDIDATE"
    assert rows[5]["age_days"] == 76
    assert rows[5]["provenance"]["debt_mv_method"]["status"] == "DEBT_MV_SOURCE_MODEL_PROOF_VERIFIED_REVIEW_PENDING"
    bad = copy.deepcopy(proof)
    bad["human_review_completed"] = True
    with pytest.raises(CaseServiceError):
        debt.validate_debt_mv_proof(bad, item, snap)
    altered = copy.deepcopy(item)
    altered["claim_class"] = "FACT"
    with pytest.raises(CaseServiceError):
        debt.validate_debt_mv_proof(proof, altered, snap)


@pytest.mark.parametrize("bad", [
    RAW.replace("1,640</strong>", "1,641</strong>"),
    RAW.replace("<td>1,640</td>", "<td>1,642</td>"),
    RAW.replace("<td>1,649</td>", "<td>1,650</td>"),
    RAW.replace("Level 2", "Level 3"),
    RAW.replace("As of June 30, 2026", "As of June 30, 2025"),
    RAW.replace("Total short-term borrowings</td><td>41", "Total short-term borrowings</td><td>42"),
    RAW.replace("Total debt</td><td>$</td><td>1,783", "Total debt</td><td>$</td><td>1,782"),
    RAW.replace("approximate fair values", "are not near market prices"),
    RAW.replace("No amounts were outstanding under the DDTL Facility as of June 30, 2026.", ""),
    RAW.replace("No amounts were outstanding under the Bridge Facility as of June 30, 2026.", ""),
    RAW.replace("5. Fair Value Measurements", "5. Fair Value Measurements</h2><h2>5. Fair Value Measurements"),
    RAW.replace("dollars in millions", "dollars in thousands"),
])
def test_modified_sec_dated_fair_value_or_undrawn_facility_fails_closed(bad):
    with pytest.raises(CaseServiceError):
        debt.extract_debt_mv(bad)


def test_local_only_nonpromoting_immutable_capture(tmp_path: Path):
    root = tmp_path / "workspace" / "source_snapshots"
    root.mkdir(parents=True)
    raw = root / "ingr_q2_original.html"
    raw.write_text(RAW, encoding="utf-8")
    out = debt.materialize_debt_mv_source(tmp_path, raw)
    assert out["status"] == "REAL_INGR_DEBT_MV_SOURCE_CANDIDATE_READY_FOR_REVIEW"
    assert out["human_review_completed"] is False
    with pytest.raises(CaseServiceError):
        debt.materialize_debt_mv_source(tmp_path, raw)
    outside = tmp_path / "outside.html"
    outside.write_text(RAW, encoding="utf-8")
    with pytest.raises(CaseServiceError):
        debt.materialize_debt_mv_source(tmp_path, outside)
    diagnostic = debt.inspect_debt_mv_html(RAW)
    assert diagnostic["eligible_assumed"] is False
    assert diagnostic["has_note5"] and diagnostic["has_note6"] and diagnostic["has_note7"]
