"""Synthetic Fitch-like excerpt: tests only, never proprietary agency research."""
from __future__ import annotations

import copy
from pathlib import Path
import pytest

from valuation_hub import ingr_wacc_fitch_rating as fit
from valuation_hub.case_service import CaseServiceError


RAW="""<!doctype html><html><body>
<h1>Fitch Affirms Ingredion Incorporated's IDR at 'BBB'; Outlook Stable</h1>
<p>Mon 08 Jun, 2026</p>
<div>Fitch Ratings - Toronto - 08 Jun 2026: Fitch Ratings has affirmed
Ingredion Incorporated's Long-Term Issuer Default Rating (IDR) at 'BBB'
and Short-Term IDR at 'F2' and assigned 'BBB' ratings to proposed
three- and five-year delayed draw term loans. The Rating Outlook is Stable.</div>
<p>The transaction is expected to close in the second half of 2027.</p>
<p>Tate &amp; Lyle future deal is expected to involve around $4.4 billion of incremental debt.</p>
<table><tr><td>Entity / Debt</td><td>Rating Type</td><td>Rating</td><td>Rating Action</td></tr>
<tr><td>Ingredion Incorporated</td><td>LT IDR</td><td>BBB</td><td>Affirmed</td></tr>
<tr><td>senior unsecured</td><td>LT</td><td>BBB</td><td>Affirmed</td></tr>
</table>
</body></html>"""


def test_exact_asof_issuer_credit_rating_without_wacc_yield():
    x=fit.extract_fitch_ingr_rating(RAW)
    assert x["rating_action_date"]=="2026-06-08"
    assert x["issuer_long_term_idr"]=="BBB"
    assert x["senior_unsecured_long_term"]=="BBB"
    assert x["outlook"]=="Stable"
    assert x["credit_grade_bbb_asof_dated_rating_action_observed"] is True
    assert x["planned_incremental_debt_usd_billions_from_agency_case"]==4.4
    assert x["planned_2027_tate_lyle_financing_is_future"] is True
    assert x["wacc_debt_source_input_created"] is False
    assert x["issued_refinancing_20260914_market_yield_observed"] is False


def test_fitch_exact_original_snapshot_and_method_proof():
    source=fit.build_external_source_snapshot(
        RAW,source_publisher="Fitch Ratings",source_type="2026_06_08_rating",
        source_tier="A",source_locator=fit.URL,captured_at="2026-10-18T00:00:00+00:00")
    proof=fit._projection(source)
    assert fit.validate_fitch_rating(proof,source)["status"]=="PASS_REAL_FITCH_BBB_2026_RATING_INGR_RD_ASSUMPTION_HOLD"
    bad=copy.deepcopy(proof)
    bad["method"]["wacc_debt_source_input_created"]=True
    with pytest.raises(CaseServiceError):
        fit.validate_fitch_rating(bad,source)
    wrong=copy.deepcopy(source)
    wrong["source"]["locator"]="https://wrong.example/ratings"
    with pytest.raises(CaseServiceError):
        fit._projection(wrong)


@pytest.mark.parametrize("old,new",[
    ("Mon 08 Jun, 2026","Mon 08 Jun, 2027"),
    ("Ingredion Incorporated's IDR at 'BBB'","Other Incorporated's IDR at 'BBB'"),
    ("Issuer Default Rating (IDR) at 'BBB'","Issuer Default Rating (IDR) at 'BB'"),
    ("senior unsecured</td><td>LT</td><td>BBB","senior unsecured</td><td>LT</td><td>BB"),
    ("The Rating Outlook is Stable","The Rating Outlook is Negative"),
    ("the second half of 2027","the second half of 2026"),
    ("around $4.4 billion of incremental debt","around $8.4 billion of incremental debt"),
    ("Fitch Ratings - Toronto - 08 Jun 2026","Fitch Ratings - Toronto - 08 Jun 2027"),
])
def test_wrong_issuer_or_agency_credit_grade_and_date_fail_closed(old,new):
    raw=RAW.replace(old,new)
    assert raw!=RAW
    with pytest.raises(CaseServiceError):
        fit.extract_fitch_ingr_rating(raw)


def test_identical_source_replay_rejected_and_off_workspace_prohibited(tmp_path:Path):
    base=tmp_path/"workspace"/"source_snapshots"
    base.mkdir(parents=True)
    p=base/"Fitch_20260608_original.html"
    p.write_text(RAW,encoding="utf-8")
    result=fit.materialize_fitch_rating(tmp_path,p)
    assert result["status"]=="REAL_FITCH_INGR_BBB_ISSUER_SENIOR_UNSECURED_RATING_CAPTURED_RD_HOLD"
    assert result["wacc_debt_source_input_created"] is False
    assert result["human_review_completed"] is False
    assert Path(result["snapshot_path"]).exists()
    assert Path(result["proof_path"]).exists()
    with pytest.raises(CaseServiceError,match="already captured"):
        fit.materialize_fitch_rating(tmp_path,p)
    other=tmp_path/"outside.html"
    other.write_text(RAW,encoding="utf-8")
    with pytest.raises(CaseServiceError):
        fit.materialize_fitch_rating(tmp_path,other)
