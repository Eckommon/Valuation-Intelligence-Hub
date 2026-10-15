"""M30-R8M24-RD.1: SEC fixed-rate note inventory; never forward YTM."""
from __future__ import annotations

import copy
from datetime import datetime
import hashlib
from pathlib import Path

import pytest

from valuation_hub import ingr_wacc_debt_bond_terms as debt
from valuation_hub.case_service import CaseServiceError
from valuation_hub.external_source import build_external_source_snapshot


RAW="""<!doctype html><html><body>
<h1>Ingredion Incorporated</h1>
For the quarterly period ended June 30, 2026
Notes to the Condensed Consolidated Financial Statements (dollars in millions, except per share data)
<h2>6. Financing Arrangements</h2>
<p>Debt carrying amounts, net of related discounts, premiums and debt issuance costs, were as follows:</p>
<table><tr><td>As of June 30, 2026</td><td>As of December 31, 2025</td></tr>
<tr><td>2.900% senior notes due June 1, 2030</td><td>597</td><td>597</td></tr>
<tr><td>3.200% senior notes due October 1, 2026 (i)</td><td>500</td><td>499</td></tr>
<tr><td>3.900% senior notes due June 1, 2050</td><td>392</td><td>392</td></tr>
<tr><td>6.625% senior notes due April 15, 2037</td><td>253</td><td>253</td></tr>
<tr><td>Revolving credit agreement</td><td>—</td><td>—</td></tr>
<tr><td>Other long-term borrowings</td><td>—</td><td>1</td></tr>
<tr><td>Total long-term debt</td><td>1,742</td><td>1,742</td></tr>
<tr><td>Other short-term borrowings</td><td>41</td><td>48</td></tr>
<tr><td>Delayed draw term loan facility</td><td>—</td><td>—</td></tr>
<tr><td>Bridge facility</td><td>—</td><td>—</td></tr>
<tr><td>Total short-term borrowings</td><td>41</td><td>48</td></tr>
<tr><td>Total debt</td><td>$</td><td>1,783</td><td>$</td><td>1,790</td></tr></table>
<p>_________________ (i)The senior notes due October 1, 2026 are classified as long-term debt
as we have the intent and ability to refinance them on a long-term basis.</p>
<p>No amounts were outstanding under the Bridge Facility as of June 30, 2026.</p>
<p>No amounts were outstanding under the DDTL Facility as of June 30, 2026.</p>
<h2>7. Pension and Other Postretirement Benefits</h2>
</body></html>"""


def test_exact_bonds_and_accounting_classification_but_no_forward_interest_yield():
    x=debt.extract_sec_debt_inventory(RAW)
    assert x["fixed_note_carrying_total_usd_millions"] == 1742
    assert x["total_reported_debt_carrying_usd_millions"] == 1783
    assert x["short_term_carrying_usd_millions"] == 41
    assert [v["coupon_percent"] for v in x["tranches"]] == [2.9,3.2,3.9,6.625]
    assert [v["maturity"] for v in x["tranches"]] == [
        "2030-06-01","2026-10-01","2050-06-01","2037-04-15"
    ]
    assert [v["carrying_june2026_usd_millions"] for v in x["tranches"]] == [597,500,392,253]
    assert x["pending_acquisition_bridge_and_ddtl_undrawn_at_period_end"] is True
    assert x["face_values_verified"] is False
    assert x["company_specific_bond_ytm_observed"] is False
    assert x["pretax_debt_rate_selected"] is None
    assert x["wacc_debt_input_created"] is False


def _original_fixture(monkeypatch:pytest.MonkeyPatch):
    snap=build_external_source_snapshot(
        RAW,source_publisher="US SEC / Ingredion Incorporated",
        source_type="2026q2_form10q_fair_value_financing",source_tier="A",
        source_locator=debt.URL,captured_at="2026-10-16T00:00:00+00:00"
    )
    # Only tests can replace known synthetic fixture SHA. Production keeps
    # the immutable original-user-capture SHA frozen as a source invariant.
    monkeypatch.setattr(debt,"REQUIRED_ORIGINAL_SHA256",snap["body"]["sha256"])
    return snap


def test_strict_original_snapshot_source_proof_and_no_wacc_promotion(monkeypatch):
    snap=_original_fixture(monkeypatch)
    proof=debt._projection(snap)
    result=debt.validate_sec_debt_inventory_proof(proof,snap)
    assert result["status"] == "PASS_BOND_INVENTORY_SOURCE_RECORDED_FORWARD_COST_HOLD"
    assert result["bond_count"] == 4
    assert result["human_review_completed"] is False
    assert proof["wacc_debt_input_created"] is False
    swapped=copy.deepcopy(proof)
    swapped["method"]["pretax_debt_rate_selected"] = 0.05
    with pytest.raises(CaseServiceError):
        debt.validate_sec_debt_inventory_proof(swapped,snap)
    bad=copy.deepcopy(snap)
    bad["source"]["locator"]="https://wrong-source.example/data"
    with pytest.raises(CaseServiceError):
        debt._projection(bad)


@pytest.mark.parametrize("bad",[
    RAW.replace("597</td><td>597", "598</td><td>597"),
    RAW.replace("3.200% senior notes", "3.300% senior notes"),
    RAW.replace("6.625% senior notes due April 15, 2037", "6.625% senior notes due April 15, 2038"),
    RAW.replace("Total long-term debt</td><td>1,742", "Total long-term debt</td><td>1,741"),
    RAW.replace("Other short-term borrowings</td><td>41", "Other short-term borrowings</td><td>42"),
    RAW.replace("As of June 30, 2026", "As of June 30, 2025"),
    RAW.replace("No amounts were outstanding under the Bridge Facility", "Some amounts were outstanding under the Bridge Facility"),
    RAW.replace("No amounts were outstanding under the DDTL Facility", "Some amounts were outstanding under the DDTL Facility"),
    RAW.replace("intent and ability to refinance", "unable to refinance"),
    RAW.replace("</body>", "<p>2.900% senior notes due June 1, 2030</p></body>"),
])
def test_malformed_debt_tranches_and_undrawn_funding_fail_closed(bad):
    if bad==RAW:
        pytest.fail("test fixture did not actually mutate original")
    # Duplicates in OTHER notes after Note 7 do not affect the bounded
    # Note-6 table, so only within-note duplicate tests belong here.
    if "2.900% senior notes due June 1, 2030</p>" in bad:
        bad=RAW.replace("Total long-term debt</td>", "2.900% senior notes due June 1, 2030 Total long-term debt</td>")
    with pytest.raises(CaseServiceError):
        debt.extract_sec_debt_inventory(bad)


def test_local_proof_reuses_original_snapshot_without_new_download(tmp_path:Path,monkeypatch):
    snap=_original_fixture(monkeypatch)
    root=tmp_path/"workspace"/"source_snapshots"
    root.mkdir(parents=True)
    original=root/"INGR_Q2_debt_market_value_original_snapshot.json"
    original.write_text(__import__("json").dumps(snap),encoding="utf-8")
    result=debt.materialize_sec_debt_inventory(tmp_path,original)
    assert result["status"] == "REAL_INGR_SEC_BOND_TERMS_CAPTURED_FORWARD_YIELD_HOLD"
    assert result["pretax_debt_rate_selected"] is None
    assert result["wacc_debt_input_created"] is False
    with pytest.raises(CaseServiceError,match="already exists"):
        debt.materialize_sec_debt_inventory(tmp_path,original)
    outside=tmp_path/"other.json"
    outside.write_text(original.read_text(),encoding="utf-8")
    with pytest.raises(CaseServiceError):
        debt.materialize_sec_debt_inventory(tmp_path,outside)


def test_inline_xbrl_coupon_and_date_node_splits_keep_exact_numbers():
    changed = (RAW
        .replace("2.900% senior notes due June 1, 2030",
                 "2.<strong>900</strong> % senior notes due June 1 <span>,</span> 2030")
        .replace("3.200% senior notes due October 1, 2026",
                 "3 . <b>200</b> % senior notes due October <i>1</i> , 2026")
        .replace("3.900% senior notes due June 1, 2050",
                 "3. <i>900</i> % senior notes due June 1, 2050")
        .replace("6.625% senior notes due April 15, 2037",
                 "6.<strong>625</strong> % senior notes due April 15 , 2037")
    )
    data = debt.extract_sec_debt_inventory(changed)
    assert [v["coupon_percent"] for v in data["tranches"]] == [2.9,3.2,3.9,6.625]
    info = debt.inspect_sec_bond_html(changed)
    assert info["status"] == "SEC_NOTE6_ORIGINAL_VISIBLE_DIAGNOSTIC_ONLY"
    assert len(info["senior_note_label_excerpts"]) == 4
    assert info["pretax_debt_rate_selected"] is None


@pytest.mark.parametrize("before,after", [
    ("2.900%", "2.901%"),
    ("3.200%", "3.201%"),
    ("6.625%", "6.626%"),
    ("June 1, 2030", "June 2, 2030"),
])
def test_inline_xbrl_whitespace_tolerance_does_not_tolerate_value_or_maturity_change(before,after):
    with pytest.raises(CaseServiceError):
        debt.extract_sec_debt_inventory(RAW.replace(before,after))
