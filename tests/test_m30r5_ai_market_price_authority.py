from __future__ import annotations

import json
from pathlib import Path

import pytest

from valuation_hub import cli_entry_m30r5
from valuation_hub.ai_market_price_authority import (
    ADJUDICATOR_ID,
    build_ai_market_price_adjudication,
    build_ai_market_price_evidence,
    build_ai_reviewed_market_price,
    validate_ai_market_price_adjudication,
    validate_ai_market_price_evidence,
    validate_ai_reviewed_market_price,
)
from valuation_hub.case_service import CaseServiceError
from valuation_hub.external_source import build_external_source_snapshot, build_market_price_candidate_from_snapshot
from valuation_hub.market_price import validate_reviewed_market_price

PRIMARY_TEXT = """Ingredion Incorporated (INGR)\nNYSE\nCurrency in USD\nDate | Price | Open | High | Low | Volume\nSep 14, 2026 | 98.63 | 101.73 | 102.24 | 98.43 | 704.76K\nSep 15, 2026 | 99.07 | 98.01 | 99.23 | 97.55 | 613.00K\n"""
PRIMARY_EXCERPT = "Sep 14, 2026 | 98.63 | 101.73 | 102.24 | 98.43 | 704.76K"
CORR_TEXT = """INGR Ingredion Incorporated NYSE\nDate (EDT) | Open | High | Low | Close | Volume\n2026-09-14 | 101.7300 | 102.2350 | 98.4350 | 98.6300 | 704,761\n"""
CORR_EXCERPT = "2026-09-14 | 101.7300 | 102.2350 | 98.4350 | 98.6300 | 704,761"


def _snap(text: str, publisher: str, locator: str, tier: str = "B") -> dict:
    return build_external_source_snapshot(
        text,
        source_publisher=publisher,
        source_type="historical_market_data",
        source_tier=tier,
        source_locator=locator,
        captured_at="2026-09-18T03:10:00+09:00",
    )


def _primary(tier: str = "B") -> dict:
    return _snap(PRIMARY_TEXT, "Investing.com", "https://www.investing.com/equities/ingredion-inc-historical-data", tier)


def _corr() -> dict:
    return _snap(CORR_TEXT, "ChartExchange", "https://chartexchange.com/symbol/nyse-ingr/historical/", "B")


def _candidate(primary: dict | None = None) -> dict:
    primary = primary or _primary()
    return build_market_price_candidate_from_snapshot(
        primary,
        price=98.63,
        currency="USD",
        entity_id="SEC_CIK:0001046257",
        financial_scope="AS_REPORTED",
        instrument_id="US4571871023",
        symbol="INGR",
        venue="NYSE",
        quote_type="OFFICIAL_CLOSE",
        trading_date="2026-09-14",
        observed_at="2026-09-14T16:00:00-04:00",
        as_of="2026-09-14",
        max_age_days=0,
    )


def _corrs() -> list[dict]:
    return [{"snapshot": _corr(), "excerpt": CORR_EXCERPT}]


def _evidence(candidate: dict | None = None, primary: dict | None = None, corrs: list[dict] | None = None) -> tuple[dict, dict, dict, list[dict]]:
    primary = primary or _primary(); candidate = candidate or _candidate(primary); corrs = _corrs() if corrs is None else corrs
    evidence = build_ai_market_price_evidence(
        candidate,
        primary,
        primary_excerpt=PRIMARY_EXCERPT,
        corroborations=corrs,
        contradiction_search_summary="Independent source snapshots agree on INGR 2026-09-14 official close of USD 98.63; no material contrary close identified.",
        material_contradictions=[],
    )
    return evidence, candidate, primary, corrs


def test_tier_b_dual_snapshot_ai_authority_reuses_m27_package() -> None:
    evidence, candidate, primary, corrs = _evidence()
    assert validate_ai_market_price_evidence(evidence, candidate, primary, corrs)["price"] == 98.63
    adjudication = build_ai_market_price_adjudication(candidate, evidence, primary, corrs, adjudicated_at="2026-09-18T03:15:00+09:00")
    assert adjudication["adjudicator"] == {"type": "AI", "id": ADJUDICATOR_ID}
    assert validate_ai_market_price_adjudication(adjudication, candidate, evidence, primary, corrs)["decision"] == "APPROVE"
    package = build_ai_reviewed_market_price(candidate, evidence, adjudication, primary, corrs)
    checked = validate_ai_reviewed_market_price(package, candidate, evidence, adjudication, primary, corrs)
    assert checked["eligible"] is True
    assert checked["price"] == 98.63
    assert checked["review_authority"] == "AI"
    assert validate_reviewed_market_price(package)["eligible"] is True
    assert package["class"] == "FACT"
    assert package["review_assertion"]["reviewer"] == ADJUDICATOR_ID


def test_tier_b_requires_independent_corroborating_snapshot() -> None:
    primary = _primary(); candidate = _candidate(primary)
    with pytest.raises(CaseServiceError, match="corroborating snapshot"):
        build_ai_market_price_evidence(candidate, primary, primary_excerpt=PRIMARY_EXCERPT, corroborations=[], contradiction_search_summary="No contradiction.", material_contradictions=[])


def test_excerpt_must_be_exact_snapshot_substring_and_show_candidate_price() -> None:
    primary = _primary(); candidate = _candidate(primary)
    with pytest.raises(CaseServiceError, match="exact substring"):
        build_ai_market_price_evidence(candidate, primary, primary_excerpt="Sep 14, 2026 | 98.63 | invented", corroborations=_corrs(), contradiction_search_summary="No contradiction.", material_contradictions=[])
    wrong = PRIMARY_TEXT.replace("98.63", "98.64")
    other = _snap(wrong, "Investing.com", "https://www.investing.com/equities/ingredion-inc-historical-data")
    candidate2 = _candidate(other)
    with pytest.raises(CaseServiceError, match="candidate price"):
        build_ai_market_price_evidence(candidate2, other, primary_excerpt=PRIMARY_EXCERPT.replace("98.63", "98.64"), corroborations=_corrs(), contradiction_search_summary="No contradiction.", material_contradictions=[])


def test_material_contradiction_fails_closed() -> None:
    primary = _primary(); candidate = _candidate(primary)
    with pytest.raises(CaseServiceError, match="contradiction"):
        build_ai_market_price_evidence(candidate, primary, primary_excerpt=PRIMARY_EXCERPT, corroborations=_corrs(), contradiction_search_summary="Conflicting close found.", material_contradictions=["Independent official source reports a different close."])


def test_tier_a_can_stand_alone_when_source_claim_is_visible() -> None:
    primary = _primary("A"); candidate = _candidate(primary)
    evidence = build_ai_market_price_evidence(candidate, primary, primary_excerpt=PRIMARY_EXCERPT, corroborations=[], contradiction_search_summary="Tier-A exact close claim checked; no material contradiction identified.", material_contradictions=[])
    assert validate_ai_market_price_evidence(evidence, candidate, primary, [])["price"] == 98.63


def test_cli_surface_delegates_prior_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[list[str]] = []
    monkeypatch.setattr(cli_entry_m30r5.prior_cli, "main", lambda argv: seen.append(list(argv)) or 41)
    argv = ["dilution-ai-inventory-validate", "inventory.json", "base.json"]
    assert cli_entry_m30r5.main(argv) == 41
    assert seen == [argv]


def test_cli_evidence_build_with_snapshot_manifest(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    primary, corr = _primary(), _corr(); candidate = _candidate(primary)
    pp, cp = tmp_path / "primary.json", tmp_path / "corr.json"
    candp, pep, cep, manifest = tmp_path / "candidate.json", tmp_path / "primary.txt", tmp_path / "corr.txt", tmp_path / "manifest.json"
    for path, value in ((pp, primary), (cp, corr), (candp, candidate)):
        path.write_text(json.dumps(value), encoding="utf-8")
    pep.write_text(PRIMARY_EXCERPT, encoding="utf-8"); cep.write_text(CORR_EXCERPT, encoding="utf-8")
    manifest.write_text(json.dumps([{"snapshot": str(cp), "excerpt": str(cep)}]), encoding="utf-8")
    rc = cli_entry_m30r5.main(["--json", "market-price-ai-evidence-build", str(candp), str(pp), "--primary-excerpt", str(pep), "--corroborations", str(manifest), "--contradiction-search-summary", "Independent captured sources agree; no contradiction identified."])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["claim"]["price"] == 98.63
    assert len(out["corroborations"]) == 1
