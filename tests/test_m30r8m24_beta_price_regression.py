"""M30-R8M24-BETA: isolated synthetic data regression for real original-source contract."""
from __future__ import annotations

import copy
from datetime import date,timedelta
import math
from pathlib import Path

import pytest

from valuation_hub import ingr_wacc_levered_beta as beta
from valuation_hub import ingr_r8_m24_readiness as readiness
from valuation_hub.case_service import CaseServiceError


def _csvs() -> tuple[str,str]:
    lines1 = ["Date,Open,High,Low,Close,Volume"]
    lines2 = ["Date,Open,High,Low,Close,Volume"]
    d = date(2023,9,14)
    issuer,market = 102.0,4200.0
    i = 0
    while d <= date(2026,9,14):
        if d.weekday() < 5:
            # Invented deterministic source fixture, NEVER user-real prices:
            mr = 0.0002 + math.sin(i*0.37)*0.004 + math.cos(i*0.19)*0.002
            ir = 0.00025 + .8*mr + math.sin(i*0.17)*.001
            market *= 1+mr
            issuer *= 1+ir
            for col,value,output in (("x",issuer,lines1),("y",market,lines2)):
                output.append(f"{d.isoformat()},{value:.8f},{value:.8f},{value:.8f},{value:.8f},100000")
            i += 1
        d += timedelta(days=1)
    return "\n".join(lines1)+"\n","\n".join(lines2)+"\n"


ISSUER,MARKET = _csvs()


def test_weekly_price_regression_is_deterministic_and_explicitly_unapproved():
    result = beta.calculate_beta(ISSUER,MARKET)
    assert 0.6 < result["regression_beta"] < 1.05
    assert result["weekly_returns"] >= 125
    assert result["aligned_daily_days"] >= 500
    assert result["weekly_last_return"] == "2026-09-14"
    assert result["return_basis"] == "PRICE_ONLY_CLOSE_TO_CLOSE_NOT_TOTAL_RETURN"
    assert result["historical_source_availability_asof_proven"] is False
    assert result["industry_comparator_not_company_beta"] is True
    assert 0.0 < result["regression_r_squared"] <= 1.0


def test_source_locked_two_original_csv_pair_proof_and_readiness():
    result=beta.build_beta_source(ISSUER,MARKET,captured_at="2026-10-16T00:00:00+00:00")
    issuer,market,inp,proof = [result[k] for k in (
        "issuer_snapshot","market_snapshot","wacc_input","proof"
    )]
    assert inp["claim_class"] == "ASSUMPTION"
    assert inp["metric"] == "levered_beta"
    assert inp["observed_on"] == "2026-09-14"
    assert proof["status"] == "UNREVIEWED_TWO_SOURCE_PRICE_ONLY_INGR_BETA"
    check=beta.validate_beta_method_proof(proof,inp,issuer,market)
    assert check["status"] == "PASS_TWO_SOURCE_INGR_BETA_PRICE_ONLY_CANDIDATE"
    rows=readiness._rows([inp],[issuer,market],[],[],[],[proof])
    assert rows[2]["status"] == "FRESH_SOURCE_INPUT_CANDIDATE"
    assert rows[2]["provenance"]["beta_method"]["status"] == "BETA_PRICE_ONLY_TWO_SOURCE_PROOF_VERIFIED_REVIEW_PENDING"
    assert rows[2]["provenance"]["beta_method"]["historical_availability_asof_proven"] is False
    assert readiness._rows([inp],[issuer,market])[2]["status"] == "BETA_TWO_SOURCE_PRICE_REGRESSION_PROOF_MISSING"
    assert readiness._rows([inp],[issuer],[],[],[],[proof])[2]["status"] == "BETA_ORIGINAL_ISSUER_OR_MARKET_SNAPSHOT_MISSING"
    mutated=copy.deepcopy(proof)
    mutated["human_review_completed"]=True
    with pytest.raises(CaseServiceError):
        beta.validate_beta_method_proof(mutated,inp,issuer,market)
    mutated=copy.deepcopy(proof)
    mutated["method"]["regression_beta"]+=0.01
    with pytest.raises(CaseServiceError):
        beta.validate_beta_method_proof(mutated,inp,issuer,market)


@pytest.mark.parametrize("kind",[
    "future","duplicate","missing","zero","gap","header","non_csv","insufficient","misalignment"
])
def test_bad_csv_data_fails_closed(kind):
    original,market=ISSUER,MARKET
    if kind=="future":
        original+="2026-09-15,100,100,100,100,1000\n"
    elif kind=="duplicate":
        original+=original.splitlines()[-1]+"\n"
    elif kind=="missing":
        original=original.replace("2026-09-14,", "2026-09-16,")
    elif kind=="zero":
        original=original.replace("2026-09-14,", "2026-09-14,0,",1)
    elif kind=="gap":
        original="\n".join(x for x in original.splitlines()
              if not ("2025-06-" in x or "2025-07-" in x))+"\n"
    elif kind=="header":
        original=original.replace("Close,Volume", "Adj Close,Volume",1)
    elif kind=="non_csv":
        original="<html>access denied</html>"
    elif kind=="insufficient":
        original="\n".join(original.splitlines()[-70:])+"\n"
    elif kind=="misalignment":
        market=market.replace("2026-09-14,", "2026-09-12,")
    with pytest.raises(CaseServiceError):
        beta.calculate_beta(original,market)


def test_two_original_sha_pair_replay_is_immutable_and_not_canonical(tmp_path:Path):
    root=tmp_path/"workspace"/"source_snapshots"
    root.mkdir(parents=True)
    a=root/"INGR_US_source.csv"
    b=root/"SPX_source.csv"
    a.write_text(ISSUER,encoding="utf-8")
    b.write_text(MARKET,encoding="utf-8")
    out=beta.materialize_beta_source(tmp_path,a,b)
    assert out["status"] == "REAL_INGR_PRICE_ONLY_BETA_SOURCE_CANDIDATE_READY_FOR_REVIEW"
    assert out["human_review_completed"] is False
    assert out["price_only_not_total_return"] is True
    assert all(Path(out[k]).exists() for k in (
        "issuer_snapshot_path","market_snapshot_path","wacc_input_path","method_proof_path"
    ))
    with pytest.raises(CaseServiceError,match="already captured"):
        beta.materialize_beta_source(tmp_path,a,b)
    outside=tmp_path/"not_workspace.csv"
    outside.write_text(ISSUER,encoding="utf-8")
    with pytest.raises(CaseServiceError):
        beta.materialize_beta_source(tmp_path,outside,b)
