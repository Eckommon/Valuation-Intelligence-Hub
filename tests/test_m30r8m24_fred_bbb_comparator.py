"""Synthetic original-like FRED markup; no copyrighted ICE data included."""
from __future__ import annotations

import copy
from datetime import date,timedelta
from pathlib import Path
import pytest

from valuation_hub import ingr_wacc_fred_bbb_comparator as mod
from valuation_hub.case_service import CaseServiceError


def _fake() -> str:
    d=date.fromisoformat("2025-01-01")
    rows=[]
    while d<=date.fromisoformat("2026-10-16"):
        y=5.40
        if d==date.fromisoformat("2026-09-11"): y=5.89
        if d==date.fromisoformat("2026-09-14"): y=5.90
        rows.append(f"<tr><td>{d.isoformat()}</td><td>{y:.2f}</td></tr>")
        d+=timedelta(days=1)
    return ("""<!DOCTYPE html><html><head><title>Table Data - ICE BofA BBB US Corporate Index Effective Yield</title></head><body>
<h1>Table Data - ICE BofA BBB US Corporate Index Effective Yield</h1>
Series ID BAMLC0A4CBBBEY<br>Source Ice Data Indices, LLC<br>
Units Percent<br>Frequency Daily, Close<br>
ICE DATA Top Level Data provided for your internal use only.
<table><tr><th>DATE</th><th>VALUE</th></tr>
"""+"".join(rows)+"</table></body></html>")


RAW=_fake()


def test_index_dated_rate_is_context_only_and_no_issuer_observation():
    value=mod.extract_fred_bbb_comparator(RAW)
    assert value["index_effective_yield_percent"]==5.90
    assert value["previous_trading_day_yield_percent"]==5.89
    assert value["company_issuer_specific_bond_market_yield_observed"] is False
    assert value["ingr_credit_rating_asof_proven"] is False
    assert value["issuer_bond_tenor_and_duration_matched"] is False
    assert value["pre_tax_cost_of_debt_wacc_input_created"] is False
    assert value["source_is_licensed_ice_internal_use_only"] is True
    assert value["status"].startswith("HOLD_")


def test_original_source_sha_proof_no_wacc_and_tamper():
    source=mod.build_external_source_snapshot(
        RAW,source_publisher="FRED / ICE Data Indices LLC",
        source_type="licensed_bbb_market_comparator",source_tier="B",
        source_locator=mod.URL,captured_at="2026-10-18T01:00:00+00:00")
    proof=mod._projection(source)
    assert mod.validate_bbb_comparator(proof,source)["status"]=="PASS_FRED_BBB_MARKET_INDEX_CONTEXT_INGR_DEBT_YIELD_HOLD"
    bad=copy.deepcopy(proof)
    bad["method"]["pre_tax_cost_of_debt_wacc_input_created"]=True
    with pytest.raises(CaseServiceError):
        mod.validate_bbb_comparator(bad,source)
    wrong=copy.deepcopy(source)
    wrong["source"]["locator"]="https://fake.example"
    with pytest.raises(CaseServiceError):
        mod._projection(wrong)


@pytest.mark.parametrize("original,modified",[
    ("2026-09-14</td><td>5.90","2026-09-14</td><td>5.91"),
    ("2026-09-11</td><td>5.89","2026-09-11</td><td>5.90"),
    ("BAMLC0A4CBBBEY","BAMLC0A4CBBAEY"),
    ("ICE BofA BBB US Corporate Index","ICE BofA AAA US Corporate Index"),
    ("internal use only","unrestricted public data"),
    ("Daily, Close","Monthly"),
    ("ICE Data Indices, LLC","Another Data Provider"),
])
def test_bad_original_identity_or_dated_value_fails_closed(original,modified):
    bad=RAW.replace(original,modified)
    assert bad!=RAW
    with pytest.raises(CaseServiceError):
        mod.extract_fred_bbb_comparator(bad)


def test_repeated_observation_fails_closed():
    added=RAW.replace("</table>","<tr><td>2026-09-14</td><td>5.90</td></tr></table>")
    with pytest.raises(CaseServiceError):
        mod.extract_fred_bbb_comparator(added)


def test_locked_local_comparator_capture_duplicate_and_outside(tmp_path:Path):
    base=tmp_path/"workspace"/"source_snapshots"
    base.mkdir(parents=True)
    original=base/"FRED_BBB_original.html"
    original.write_text(RAW,encoding="utf-8")
    result=mod.materialize_bbb_comparator(tmp_path,original)
    assert result["status"]=="REAL_20260914_BBB_INDEX_MARKET_COMPARATOR_CAPTURED_INGR_RD_HOLD"
    assert result["company_rating_and_duration_match_proven"] is False
    assert result["pre_tax_cost_of_debt_wacc_input_created"] is False
    assert result["human_review_completed"] is False
    assert Path(result["snapshot_path"]).is_file()
    assert Path(result["proof_path"]).is_file()
    with pytest.raises(CaseServiceError,match="already captured"):
        mod.materialize_bbb_comparator(tmp_path,original)
    outside=tmp_path/"not_in_workspace.html"
    outside.write_text(RAW,encoding="utf-8")
    with pytest.raises(CaseServiceError):
        mod.materialize_bbb_comparator(tmp_path,outside)
