"""M30-R8M24-TAX.1 — no invented WACC marginal cash tax."""
from __future__ import annotations

import copy
from pathlib import Path
import pytest

from valuation_hub import ingr_wacc_tax_evidence as tax
from valuation_hub.case_service import CaseServiceError
from valuation_hub.external_source import validate_external_source_snapshot


RAW = """<!doctype html><html><body>
<h1>INGREDION INCORPORATED REPORTS SECOND QUARTER 2026 RESULTS</h1>
<h2>Other Financial Items</h2>
<p>The reported and adjusted effective tax rates for the second quarter were
<strong>33.7</strong>% and <b>27.2</b>%, compared to 23.6% and 27.2%,
for the year-ago period. The increase in the reported effective tax rate
was primarily attributable to the gain on the sale of a majority stake in
the Pakistan business and the change in value of the Mexican peso relative
to the U.S. dollar. These impacts were partially offset by the utilization
of previously unbenefited capital losses.</p>
<h2>Full-Year 2026 Outlook</h2>
<p>For full-year 2026, the Company expects a reported effective tax rate
of 27.4% to 28.9% and still expects an adjusted effective tax rate
of 26.0% to <b>27.5</b>%.</p>
<p>Cash from operations for the full year 2026 is expected...</p>
<p>This guidance reflects tariff levels in effect as of the end of July 2026.
In addition, this guidance excludes acquisition-related integration and
restructuring costs, as well as any potential impairment costs.</p>
</body></html>"""


def test_observations_preserve_distinct_accounting_rates_and_wacc_hold():
    x = tax.extract_tax_observations(RAW)
    assert x["quarter_2026_effective_rates_percent"] == {
        "gaap": 33.7, "adjusted_non_gaap": 27.2}
    assert x["quarter_2025_comparator_percent"] == {
        "gaap": 23.6, "adjusted_non_gaap": 27.2}
    assert x["full_year_2026_guidance_percent"] == {
        "gaap": [27.4, 28.9], "adjusted_non_gaap": [26.0, 27.5]}
    assert x["status"] == "HOLD_WACC_MARGINAL_TAX_METHODOLOGY_NOT_EVIDENCED"
    assert x["tax_rate_wacc_numeric_selected"] is None
    assert not x["wacc_tax_source_input_created"]


def test_original_evidence_proof_has_no_tax_rate_or_approval():
    x = tax.build_tax_evidence(RAW, captured_at="2026-10-15T00:00:00+00:00")
    snap, proof = x["snapshot"], x["proof"]
    assert validate_external_source_snapshot(snap)["status"] == "PASS_EXTERNAL_SOURCE_SNAPSHOT_VALIDATION"
    assert snap["raw_text"] == RAW
    assert proof["wacc_tax_source_input_created"] is False
    assert proof["human_review_completed"] is False
    assert tax.validate_tax_evidence(proof, snap)["status"] == "PASS_SOURCE_BOUND_TAX_OBSERVATIONS_MARGINAL_METHOD_HOLD"
    altered = copy.deepcopy(proof)
    altered["method"]["tax_rate_wacc_numeric_selected"] = 0.2675
    with pytest.raises(CaseServiceError):
        tax.validate_tax_evidence(altered, snap)
    altered = copy.deepcopy(snap)
    altered["source"]["locator"] = "https://example.com/not-sec"
    with pytest.raises(CaseServiceError):
        tax.validate_tax_evidence(proof, altered)


@pytest.mark.parametrize("bad", [
    RAW.replace("33.7</strong>", "33.8</strong>"),
    RAW.replace("<b>27.2</b>", "<b>27.3</b>"),
    RAW.replace("23.6%", "22.6%"),
    RAW.replace("of 27.4%", "of 27.5%"),
    RAW.replace("to <b>27.5</b>%", "to <b>27.6</b>%"),
    RAW.replace("26.0%", "26.1%"),
    RAW.replace("The reported and adjusted effective tax rates", "The GAAP and adjusted income tax rates"),
    RAW.replace("Full-Year 2026 Outlook", "Full-Year 2025 Outlook"),
    RAW.replace("Pakistan business and the change in value of the Mexican peso", "different issue"),
    RAW.replace("excludes acquisition-related integration and restructuring costs", "includes them"),
    RAW.replace("</body>", "<p>The reported and adjusted effective tax rates for the second quarter were 33.7% and 27.2%, compared to 23.6% and 27.2%</p></body>"),
])
def test_tampered_or_duplicate_tax_claims_fail_closed(bad):
    with pytest.raises(CaseServiceError):
        tax.extract_tax_observations(bad)


def test_user_local_capture_seals_source_no_replays(tmp_path: Path):
    root = tmp_path / "workspace" / "source_snapshots"
    root.mkdir(parents=True)
    raw = root / "ingr_8k_original.html"
    raw.write_text(RAW, encoding="utf-8")
    x = tax.materialize_tax_evidence(tmp_path, raw)
    assert x["status"] == "REAL_INGR_TAX_OBSERVATIONS_CAPTURED_METHOD_HOLD"
    assert not x["wacc_tax_source_input_created"]
    with pytest.raises(CaseServiceError):
        tax.materialize_tax_evidence(tmp_path, raw)
    bad = tmp_path / "outside_original.html"
    bad.write_text(RAW, encoding="utf-8")
    with pytest.raises(CaseServiceError):
        tax.materialize_tax_evidence(tmp_path, bad)
