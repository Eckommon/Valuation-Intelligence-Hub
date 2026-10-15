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


OCTOBER_AUTHOR_HTML = FAKE_NYU.replace(
    "Implied ERP on September 1, 2026 = 4.14%",
    "Implied ERP on October 1, 2026 = 4.20%",
).replace(
    "Implied ERP in previous month = 4.28% (Trailing 12 month, with adjusted payout).",
    "Implied ERP in previous month = 4.14% (Trailing 12 month, with adjusted payout); "
    "4.09% (Trailing 12 month cash yield); 6.05% (Average CF yield last 10 years); "
    "3.80% (Net cash yield); 3.56% (Normalized Earnings &amp; Payout) "
    "(with the US treasury rate of 4.75% used as the riskfree rate in US dollars).",
)


def test_october_explicit_previous_month_is_valid_sep1_method_only_as_retrospective():
    result = erp.extract_dated_adjusted_erp(OCTOBER_AUTHOR_HTML)
    assert result["erp_decimal"] == 0.0414
    assert result["observed_on"] == "2026-09-01"
    assert result["source_extraction_route"] == "OCT1_CURRENT_EXPLICIT_SEP1_PREVIOUS_MONTH_RECAP"
    assert result["author_page_current_date_header"] == "October 1, 2026"
    assert result["source_is_retrospective_asof"] is True
    assert result["historical_availability_asof_proven"] is False
    artifact = erp.build_erp_source(
        OCTOBER_AUTHOR_HTML, captured_at="2026-10-15T00:00:00+00:00")
    assert artifact["proof"]["method"]["source_is_retrospective_asof"] is True
    assert erp.validate_erp_source_proof(
        artifact["proof"], artifact["wacc_input"], artifact["snapshot"]
    )["status"] == "PASS_SOURCE_BOUND_NYU_IMPLIED_ERP_CANDIDATE"
    rows = readiness._rows(
        [artifact["wacc_input"]], [artifact["snapshot"]], [], [artifact["proof"]])
    assert rows[1]["status"] == "FRESH_SOURCE_INPUT_CANDIDATE"
    assert rows[1]["provenance"]["erp_method"]["source_class"] == "ASSUMPTION"


@pytest.mark.parametrize("bad_html", [
    OCTOBER_AUTHOR_HTML.replace("October 1, 2026", "November 1, 2026"),
    OCTOBER_AUTHOR_HTML.replace("Implied ERP in previous month =", "Unspecified ERP ="),
    OCTOBER_AUTHOR_HTML.replace("Implied ERP in previous month = 4.14%",
                                "Implied ERP in previous month = 4.12%"),
    OCTOBER_AUTHOR_HTML.replace(
        "(with the US treasury rate of 4.75% used as the riskfree rate in US dollars).",
        "(with the US treasury rate of 5.29% used as the riskfree rate in US dollars)."),
    OCTOBER_AUTHOR_HTML.replace(
        "</p><a>",
        "Implied ERP in previous month = 4.14% (Trailing 12 month, with adjusted payout); "
        "4.09% (Trailing 12 month cash yield); 6.05% (Average CF yield last 10 years); "
        "3.80% (Net cash yield); 3.56% (Normalized Earnings &amp; Payout) "
        "(with the US treasury rate of 4.75% used as the riskfree rate in US dollars).</p><a>"),
])
def test_retrospective_date_method_riskfree_and_duplicate_section_fail_closed(bad_html):
    with pytest.raises(CaseServiceError):
        erp.extract_dated_adjusted_erp(bad_html)


def test_original_downloaded_page_diagnostic_never_creates_source():
    diagnostic = erp.inspect_erp_html(OCTOBER_AUTHOR_HTML)
    assert diagnostic["dated_current_headings"] == ["October 1, 2026"]
    assert diagnostic["explicit_previous_month_sections"] == 1
    assert diagnostic["has_exact_oct_1_heading"] is True
    assert diagnostic["has_exact_sep_1_heading"] is False
    assert diagnostic["eligible_erp_source_assumed"] is False
    assert diagnostic["human_review_completed"] is False
    assert len(diagnostic["raw_body_sha256"]) == 64


# Adjacent HTML inline tags produce extra visible-text spaces around %, comma,
# method parentheses and the author Treasury percent. The original source
# snapshot still retains the exact unnormalized HTML bytes and source SHA.
OCTOBER_INLINE_AUTHOR_HTML = (
    OCTOBER_AUTHOR_HTML
    .replace(
        "Implied ERP on October 1, 2026 = 4.20% (Trailing 12 month, with adjusted payout)",
        "Implied ERP on <b>October 1, 2026</b> = "
        "<strong>4.20</strong>% (<i>Trailing 12 month</i>, "
        "<span>with adjusted payout</span>)",
    )
    .replace(
        "Implied ERP in previous month = 4.14% (Trailing 12 month, with adjusted payout)",
        "Implied ERP in previous month = "
        "<strong>4.14</strong>% (<i>Trailing 12 month</i>, "
        "<span>with adjusted payout</span>)",
    )
    .replace(
        "4.09% (Trailing 12 month cash yield)",
        "<strong>4.09</strong>% (<i>Trailing 12 month cash yield</i>)",
    )
    .replace(
        "6.05% (Average CF yield last 10 years)",
        "<strong>6.05</strong>% (Average CF yield last 10 years)",
    )
    .replace(
        "3.80% (Net cash yield)",
        "<strong>3.80</strong>% (Net cash yield)",
    )
    .replace(
        "3.56% (Normalized Earnings &amp; Payout)",
        "<strong>3.56</strong>% (<i>Normalized Earnings</i> &amp; <em>Payout</em>)",
    )
    .replace(
        "4.75% used as the riskfree",
        "<strong>4.75</strong>% used as the riskfree",
    )
)


def test_october_inline_html_markup_is_source_bound_and_unreviewed():
    info = erp.inspect_erp_html(OCTOBER_INLINE_AUTHOR_HTML)
    assert info["dated_current_headings"] == ["October 1, 2026"]
    assert info["explicit_previous_month_sections"] == 1
    assert info["current_adjusted_payout_model_count"] == 1, repr(erp._visible(OCTOBER_INLINE_AUTHOR_HTML)[:550])
    assert info["previous_month_adjusted_payout_model_count"] == 1
    result = erp.extract_dated_adjusted_erp(OCTOBER_INLINE_AUTHOR_HTML)
    assert result["erp_decimal"] == 0.0414
    assert result["source_is_retrospective_asof"] is True
    assert result["historical_availability_asof_proven"] is False
    sealed = erp.build_erp_source(
        OCTOBER_INLINE_AUTHOR_HTML, captured_at="2026-10-15T01:00:00+00:00")
    assert sealed["snapshot"]["raw_text"] == OCTOBER_INLINE_AUTHOR_HTML
    proof = sealed["proof"]
    assert erp.validate_erp_source_proof(
        proof, sealed["wacc_input"], sealed["snapshot"]
    )["status"] == "PASS_SOURCE_BOUND_NYU_IMPLIED_ERP_CANDIDATE"
    assert proof["human_review_completed"] is False
    assert proof["wacc_package_created"] is False


@pytest.mark.parametrize("bad_html", [
    # A second dated heading must fail even if it uses an invalid model.
    OCTOBER_INLINE_AUTHOR_HTML.replace(
        "</body>", "<p>Implied ERP on October 1, 2026 = "
        "7.00% (Trailing 12 month cash yield)</p></body>"
    ),
    # A second prior-month label must fail even if its method is invalid.
    OCTOBER_INLINE_AUTHOR_HTML.replace(
        "</body>", "<p>Implied ERP in previous month = "
        "7.00% (Trailing 12 month cash yield)</p></body>"
    ),
    # Wrong method for the previous-month 4.14% is not adjustable by inference.
    OCTOBER_INLINE_AUTHOR_HTML.replace(
        "<strong>4.14</strong>% (<i>Trailing 12 month</i>, "
        "<span>with adjusted payout</span>)",
        "<strong>4.14</strong>% (Trailing 12 month cash yield)"
    ),
    OCTOBER_INLINE_AUTHOR_HTML.replace(
        "<strong>4.75</strong>% used as the riskfree",
        "<strong>5.29</strong>% used as the riskfree"
    ),
])
def test_october_inline_html_markup_conflicts_fail_closed(bad_html):
    with pytest.raises(CaseServiceError):
        erp.extract_dated_adjusted_erp(bad_html)


# Actual local Oct-2026 raw-page diagnostic at main@041379c:
# one dated current heading + one explicit September previous-month section;
# current adjusted-payout full-label match=0, prior-month match=1.
# This fixture represents HTML-split October current number and a changed
# current-month model label. September method evidence remains completely exact.
OCTOBER_INDEPENDENT_CURRENT_VALUE = OCTOBER_AUTHOR_HTML.replace(
    "Implied ERP on October 1, 2026 = 4.20% (Trailing 12 month, with adjusted payout)",
    "Implied ERP on October 1, 2026 = <b>4</b>.<i>20</i>% "
    "(Trailing 12 month cash yield)",
)


def test_october_unique_value_anchor_accepts_strict_september_method_without_oct_label():
    info = erp.inspect_erp_html(OCTOBER_INDEPENDENT_CURRENT_VALUE)
    assert info["dated_current_headings"] == ["October 1, 2026"]
    assert info["october_current_4_20_numeric_anchor_count"] == 1
    assert info["current_adjusted_payout_model_count"] == 0
    assert info["previous_month_adjusted_payout_model_count"] == 1
    assert info["eligible_erp_source_assumed"] is False
    assert len(info["current_headline_visible_excerpt"]) <= 220
    source = erp.build_erp_source(
        OCTOBER_INDEPENDENT_CURRENT_VALUE, captured_at="2026-10-15T10:00:00+00:00"
    )
    snapshot, item, proof = source["snapshot"], source["wacc_input"], source["proof"]
    assert snapshot["raw_text"] == OCTOBER_INDEPENDENT_CURRENT_VALUE
    assert proof["source_body_sha256"] == info["raw_body_sha256"]
    assert proof["method"]["source_extraction_route"] == "OCT1_CURRENT_EXPLICIT_SEP1_PREVIOUS_MONTH_RECAP"
    assert proof["method"]["source_is_retrospective_asof"] is True
    assert proof["method"]["historical_availability_asof_proven"] is False
    assert proof["method"]["alternatives_percent"] == {
        "trailing_cash_yield": 4.09, "average_10yr_cash_flow": 6.05,
        "net_cash_yield": 3.8, "normalized_earnings_payout": 3.56,
    }
    assert item["claim_class"] == "ASSUMPTION"
    assert erp.validate_erp_source_proof(proof, item, snapshot)["human_review_completed"] is False
    rows = readiness._rows([item], [snapshot], [], [proof])
    assert rows[1]["status"] == "FRESH_SOURCE_INPUT_CANDIDATE"
    assert rows[1]["provenance"]["erp_method"]["source_is_retrospective_asof"] is True


@pytest.mark.parametrize("bad", [
    OCTOBER_INDEPENDENT_CURRENT_VALUE.replace(
        "October 1, 2026 = <b>4</b>.<i>20</i>%",
        "October 1, 2026 = <b>4</b>.<i>21</i>%",
    ),
    OCTOBER_INDEPENDENT_CURRENT_VALUE.replace(
        "October 1, 2026 = <b>4</b>.<i>20</i>%",
        "October 1, 2026 = unknown",
    ),
    OCTOBER_INDEPENDENT_CURRENT_VALUE.replace(
        "October 1, 2026", "November 1, 2026"
    ),
    OCTOBER_INDEPENDENT_CURRENT_VALUE.replace(
        "Implied ERP in previous month =", "Unspecified previous result ="
    ),
    OCTOBER_INDEPENDENT_CURRENT_VALUE.replace(
        "Implied ERP in previous month = 4.14%", "Implied ERP in previous month = 4.15%"
    ),
    OCTOBER_INDEPENDENT_CURRENT_VALUE.replace(
        "4.75% used as the riskfree", "4.76% used as the riskfree"
    ),
    OCTOBER_INDEPENDENT_CURRENT_VALUE.replace(
        "4.09% (Trailing 12 month cash yield)", "4.10% (Trailing 12 month cash yield)"
    ),
    OCTOBER_INDEPENDENT_CURRENT_VALUE.replace(
        "</body>", "<p>Implied ERP on October 1, 2026 = "
        "4.20% (Trailing 12 month cash yield)</p></body>"
    ),
    OCTOBER_INDEPENDENT_CURRENT_VALUE.replace(
        "</body>", "<p>Implied ERP in previous month = "
        "4.14% (Trailing 12 month, with adjusted payout)</p></body>"
    ),
])
def test_october_value_only_anchor_tampering_fails_closed(bad):
    with pytest.raises(CaseServiceError):
        erp.extract_dated_adjusted_erp(bad)


def test_direct_september_heading_still_requires_exact_adjusted_payout():
    changed = FAKE_NYU.replace(
        "4.14% (Trailing 12 month, with adjusted payout)",
        "4.14% (Trailing 12 month cash yield)",
        1,
    )
    with pytest.raises(CaseServiceError):
        erp.extract_dated_adjusted_erp(changed)
