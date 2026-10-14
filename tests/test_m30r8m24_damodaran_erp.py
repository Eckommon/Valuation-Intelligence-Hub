"""M30-R8M24-ERP: synthetic exact-author-model and WACC readiness regressions."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from valuation_hub import ingr_wacc_damodaran_erp as erp
from valuation_hub import ingr_r8_m24_readiness as readiness
from valuation_hub.case_service import CaseServiceError
from valuation_hub.external_source import validate_external_source_snapshot

FAKE_NYU = """<!doctype html><html><body>
<h1>Aswath Damodaran NYU Stern</h1><h2>Equity Risk Premiums (Data, Updates and Papers)</h2>
<p>Implied ERP on September 1, 2026 = 4.14% (Trailing 12 month, with adjusted payout);
4.09% (Trailing 12 month cash yield); 6.05% (Average CF yield last 10 years);
3.80% (Net cash yield); 3.56% (Normalized Earnings &amp; Payout)
(with the US treasury rate of 4.75% used as the riskfree rate in US dollars;
increase each of the premiums by the default spread (0.22%) for the US).
</p><a>Day-to-day ERP in March 2026</a>
<p>Implied ERP in previous month = 4.28% (Trailing 12 month, with adjusted payout).</p>
</body></html>"""


def _payload():
    return erp.build_erp_source(FAKE_NYU, captured_at="2026-10-14T16:00:00+00:00")


def test_exact_sep1_adjusted_erp_with_alternatives_and_treasury_mismatch():
    result = erp.extract_dated_adjusted_erp(FAKE_NYU)
    assert result["erp_decimal"] == 0.0414
    assert result["observed_on"] == "2026-09-01"
    assert result["model"] == "IMPLIED_ERP_US_TTM_ADJUSTED_PAYOUT"
    assert result["author_model_risk_free_decimal"] == 0.0475
    assert result["valuation_asof_risk_free_decimal"] == 0.0497
    assert result["model_rf_valuation_rf_difference_basis_points"] == 22
    assert result["alternatives_percent"] == {
        "trailing_cash_yield": 4.09,
        "average_10yr_cash_flow": 6.05,
        "net_cash_yield": 3.80,
        "normalized_earnings_payout": 3.56,
    }


def test_exact_original_nyu_snapshot_input_and_independent_model_proof():
    x = _payload()
    snap, item, proof = x["snapshot"], x["wacc_input"], x["proof"]
    assert validate_external_source_snapshot(snap)["status"] == "PASS_EXTERNAL_SOURCE_SNAPSHOT_VALIDATION"
    verified = erp.validate_erp_source_proof(proof,item,snap)
    assert verified["status"] == "PASS_SOURCE_BOUND_NYU_IMPLIED_ERP_CANDIDATE"
    assert item["metric"] == "equity_risk_premium"
    assert item["value"] == 0.0414
    assert item["unit"] == "decimal"
    assert item["observed_on"] == "2026-09-01"
    assert item["claim_class"] == "ASSUMPTION"
    assert item["source"]["tier"] == "B"
    assert proof["human_review_completed"] is False
    assert proof["wacc_package_created"] is False
    assert proof["method"]["model_rf_valuation_rf_difference_basis_points"] == 22
    rows = readiness._rows([item],[snap])
    assert rows[1]["status"] == "ERP_EXPLICIT_MODEL_METHOD_PROOF_MISSING"
    rows = readiness._rows([item],[snap],[],[proof])
    assert rows[1]["status"] == "FRESH_SOURCE_INPUT_CANDIDATE"
    assert rows[1]["provenance"]["erp_method"]["status"] == "ERP_SOURCE_MODEL_PROOF_VERIFIED_REVIEW_PENDING"
    assert rows[1]["age_days"] == 13
    assert sum(y["status"] == "MISSING_SOURCE_INPUT" for y in rows) == 6


@pytest.mark.parametrize("bad",[
    FAKE_NYU.replace("September 1, 2026", "October 1, 2026"),
    FAKE_NYU.replace("4.14% (Trailing 12 month, with adjusted payout)",
                     "4.14% (Trailing 12 month cash yield)"),
    FAKE_NYU.replace("4.14% (Trailing 12 month, with adjusted payout)",
                     "4.15% (Trailing 12 month, with adjusted payout)"),
    FAKE_NYU.replace("4.09% (Trailing 12 month cash yield)",
                     "4.14% (Trailing 12 month cash yield)"),
    FAKE_NYU.replace("4.75% used as the riskfree", "4.97% used as the riskfree"),
    FAKE_NYU.replace("</p><a>", "</p><p>Implied ERP on September 1, 2026 = 4.14% (Trailing 12 month, with adjusted payout)</p><a>"),
])
def test_wrong_dated_model_method_other_variant_rf_or_duplicate_fails_closed(bad):
    with pytest.raises(CaseServiceError):
        erp.extract_dated_adjusted_erp(bad)


def test_no_fake_human_review_or_reclass_after_source_sealing():
    x=_payload()
    bad=copy.deepcopy(x["wacc_input"])
    bad["claim_class"]="FACT"
    with pytest.raises(CaseServiceError):
        erp.validate_erp_source_proof(x["proof"],bad,x["snapshot"])
    badp=copy.deepcopy(x["proof"])
    badp["human_review_completed"]=True
    with pytest.raises(CaseServiceError):
        erp.validate_erp_source_proof(badp,x["wacc_input"],x["snapshot"])
    bads=copy.deepcopy(x["snapshot"])
    bads["source"]["locator"]="https://example.com/not-nyu"
    with pytest.raises(CaseServiceError):
        erp.validate_erp_source_proof(x["proof"],x["wacc_input"],bads)


def test_local_only_no_network_and_method_proof_written(tmp_path:Path):
    root=tmp_path/"workspace"/"source_snapshots"
    root.mkdir(parents=True)
    raw=root/"NYU_ERP_source.html"
    raw.write_text(FAKE_NYU,encoding="utf-8")
    out=erp.materialize_erp_source(tmp_path,raw)
    assert out["status"]=="REAL_INGR_ERP_METHOD_SOURCE_CANDIDATE_READY_FOR_REVIEW"
    assert out["human_review_completed"] is False
    assert out["source_tier"]=="B"
    snap=json.loads(Path(out["source_snapshot_path"]).read_text(encoding="utf-8"))
    inp=json.loads(Path(out["erp_input_path"]).read_text(encoding="utf-8"))
    proof=json.loads(Path(out["method_proof_path"]).read_text(encoding="utf-8"))
    assert erp.validate_erp_source_proof(proof,inp,snap)["status"]=="PASS_SOURCE_BOUND_NYU_IMPLIED_ERP_CANDIDATE"
    assert all(Path(out[k]).is_relative_to(root) for k in ("source_snapshot_path","erp_input_path","method_proof_path"))


def test_outside_user_local_workspace_prohibited(tmp_path:Path):
    path=tmp_path/"external.html"
    path.write_text(FAKE_NYU,encoding="utf-8")
    with pytest.raises(CaseServiceError):
        erp.materialize_erp_source(tmp_path,path)
