"""M30-R8M24-TAX.2: SEC 2025 10-K contextual bridge, NOT WACC marginal tax."""
from __future__ import annotations

import copy
from pathlib import Path
import pytest

from valuation_hub import ingr_wacc_tax_bridge_10k as tax
from valuation_hub.case_service import CaseServiceError


RAW = """<!doctype html><html><body>
<h1>INGREDION INCORPORATED</h1>
FORM 10-K For the fiscal year ended December 31, 2025
<p>The following table reconciles the U.S. federal statutory income tax rate
to the Company’s effective tax rate for 2025.</p>
<table>
<tr><td>2025</td></tr><tr><td>Amount</td><td>Percent</td></tr>
<tr><td>Federal statutory tax rate</td><td>$</td><td>204</td><td>21.0</td><td>%</td></tr>
<tr><td>U.S. tax effects:</td></tr>
<tr><td>State and local income taxes, net of federal benefit (i)</td><td>7</td><td>0.7</td></tr>
<tr><td>Effect of cross-border tax laws:</td></tr>
<tr><td>Foreign-derived intangible income</td><td>(17)</td><td>(1.7)</td></tr>
<tr><td>Other</td><td>2</td><td>0.2</td></tr>
<tr><td>Tax credits:</td></tr>
<tr><td>Foreign tax credit</td><td>(26)</td><td>(2.7)</td></tr>
<tr><td>Other credits</td><td>(3)</td><td>(0.3)</td></tr>
<tr><td>Nontaxable or nondeductible items</td><td>6</td><td>0.6</td></tr>
<tr><td>Other</td><td>9</td><td>0.9</td></tr>
<tr><td>Foreign tax effects:</td></tr>
<tr><td>Mexico:</td></tr>
<tr><td>Statutory tax rate difference</td><td>25</td><td>2.6</td></tr>
<tr><td>Other</td><td>9</td><td>0.9</td></tr>
<tr><td>Foreign currency foreign exchange</td><td>(14)</td><td>(1.5)</td></tr>
<tr><td>Germany:</td></tr>
<tr><td>Provincial tax</td><td>13</td><td>1.3</td></tr>
<tr><td>Other</td><td>(4)</td><td>(0.4)</td></tr>
<tr><td>Colombia</td><td>11</td><td>1.1</td></tr>
<tr><td>Other foreign jurisdictions</td><td>19</td><td>2.0</td></tr>
<tr><td>Changes in unrecognized tax benefits</td><td>(3)</td><td>(0.3)</td></tr>
<tr><td>Effective income tax rate</td><td>$</td><td>238</td><td>24.4</td><td>%</td></tr></table>
<p>(i) Illinois and New York make up the majority of state and local income taxes, net of federal benefit.</p>
</body></html>"""


def test_2025_statutory_vs_etr_tax_bridge_no_wacc_input():
    result=tax.extract_2025_tax_bridge(RAW)
    assert result["historical_us_federal_statutory_percent"]==21.0
    assert result["historical_consolidated_effective_percent"]==24.4
    assert result["historical_etr_minus_us_base_percentage_points"]==3.4
    assert result["historical_state_and_local_effect_percentage_points"]==0.7
    assert result["foreign_country_effects_present"] == ["Mexico","Germany","Colombia","other"]
    assert result["foreign_tax_credit_effect_present"] is True
    assert result["selected_2026_wacc_marginal_cash_tax_rate"] is None
    assert result["incremental_cash_tax_shield_verified"] is False
    assert result["wacc_tax_source_input_created"] is False
    assert result["status"].startswith("HOLD_")


def test_2025_original_bytes_tax_context_proof_noncanonical():
    value=tax.build_2025_tax_bridge(RAW,captured_at="2026-10-17T00:00:00+00:00")
    assert value["snapshot"]["source"]["locator"]==tax.URL
    assert value["snapshot"]["source"]["tier"]=="A"
    assert value["snapshot"]["raw_text"]==RAW
    assert tax.validate_2025_tax_bridge(value["proof"],value["snapshot"])["status"]=="PASS_FY2025_TAX_CONTEXT_MARGINAL_INTEREST_SHIELD_HOLD"
    altered=copy.deepcopy(value["proof"])
    altered["method"]["selected_2026_wacc_marginal_cash_tax_rate"]=.21
    with pytest.raises(CaseServiceError):
        tax.validate_2025_tax_bridge(altered,value["snapshot"])
    altered=copy.deepcopy(value["snapshot"])
    altered["source"]["locator"]="https://fake.example/10k"
    with pytest.raises(CaseServiceError):
        tax._projection(altered)


@pytest.mark.parametrize("bad",[
    RAW.replace("21.0</td>","21.5</td>"),
    RAW.replace("204</td>","205</td>"),
    RAW.replace("24.4</td>","24.5</td>"),
    RAW.replace("238</td>","239</td>"),
    RAW.replace("0.7</td>","0.8</td>"),
    RAW.replace("Federal statutory tax rate","Different base rate"),
    RAW.replace("Mexico:","Other country:"),
    RAW.replace("Colombia","Canada"),
    RAW.replace("Other foreign jurisdictions","Other geographic effects"),
    RAW.replace("Foreign tax credit","Tax credit"),
    RAW.replace("For the fiscal year ended December 31, 2025",
                "For the fiscal year ended December 31, 2024"),
    RAW.replace("</table>","<tr><td>Federal statutory tax rate $ 204 21.0%</td></tr></table>"),
])
def test_tamper_2025_source_values_or_tax_scope_fail_closed(bad):
    with pytest.raises(CaseServiceError):
        tax.extract_2025_tax_bridge(bad)


def test_10k_exact_body_hash_replay_immutable(tmp_path: Path):
    root=tmp_path/"workspace"/"source_snapshots"
    root.mkdir(parents=True)
    p=root/"INGR_2025_10K_original.html"
    p.write_text(RAW,encoding="utf-8")
    out=tax.materialize_2025_tax_bridge(tmp_path,p)
    assert out["status"] == "REAL_INGR_2025_TAX_STATUTORY_EFFECTIVE_BRIDGE_CAPTURED_METHOD_HOLD"
    assert out["2026_wacc_marginal_rate_selected"] is None
    assert out["wacc_tax_source_input_created"] is False
    assert out["human_review_completed"] is False
    assert Path(out["snapshot_path"]).exists()
    assert Path(out["proof_path"]).exists()
    with pytest.raises(CaseServiceError,match="already captured"):
        tax.materialize_2025_tax_bridge(tmp_path,p)
    outside=tmp_path/"outside.html"
    outside.write_text(RAW,encoding="utf-8")
    with pytest.raises(CaseServiceError):
        tax.materialize_2025_tax_bridge(tmp_path,outside)
