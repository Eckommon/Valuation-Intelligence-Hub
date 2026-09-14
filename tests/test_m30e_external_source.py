from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from valuation_hub.case_service import CaseServiceError
from valuation_hub.external_source import (
    build_external_source_snapshot,
    build_market_price_candidate_from_snapshot,
    build_terminal_growth_anchor_from_snapshot,
    build_wacc_source_input_from_snapshot,
    materialize_external_source_snapshot,
    validate_external_source_snapshot,
    validate_market_price_candidate_against_snapshot,
    validate_terminal_growth_anchor_against_snapshot,
    validate_wacc_source_input_against_snapshot,
)
from valuation_hub.market_price import validate_market_price_candidate
from valuation_hub.terminal_growth_assumption import validate_terminal_growth_anchor_input
from valuation_hub.wacc_assumption import validate_wacc_source_input


def _snapshot(*, tier: str = "A", locator: str = "https://example.org/source/quote") -> dict:
    return build_external_source_snapshot(
        "official source text\nINGR quote 132.50\n",
        source_publisher="Example Official Publisher",
        source_type="official_market_or_macro_release",
        source_tier=tier,
        source_locator=locator,
        captured_at="2026-09-14T10:00:00+09:00",
    )


def _reseal(value: dict, field: str) -> None:
    unsigned = copy.deepcopy(value)
    unsigned.pop(field, None)
    value[field] = hashlib.sha256(
        json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def test_snapshot_preserves_exact_utf8_and_hashes() -> None:
    snapshot = _snapshot()
    checked = validate_external_source_snapshot(snapshot)
    raw = snapshot["raw_text"].encode("utf-8")
    assert snapshot["body"]["bytes"] == len(raw)
    assert snapshot["body"]["sha256"] == hashlib.sha256(raw).hexdigest()
    assert checked["snapshot_sha256"] == snapshot["snapshot_sha256"]
    assert snapshot["capture"] == {
        "method": "LOCAL_UTF8_INTAKE",
        "captured_at": "2026-09-14T10:00:00+09:00",
        "network_fetch_performed": False,
        "credentials_persisted": False,
    }
    assert "headers" not in snapshot and "cookies" not in snapshot and "authorization" not in snapshot


def test_https_locator_and_no_embedded_credentials_required() -> None:
    with pytest.raises(CaseServiceError, match="HTTPS"):
        _snapshot(locator="http://example.org/source")
    with pytest.raises(CaseServiceError, match="authority"):
        _snapshot(locator="https://user:secret@example.org/source")
    with pytest.raises(CaseServiceError, match="port"):
        _snapshot(locator="https://example.org:notaport/source")


def test_body_tamper_fails_even_after_outer_reseal() -> None:
    snapshot = _snapshot()
    tampered = copy.deepcopy(snapshot)
    tampered["raw_text"] += "tampered"
    _reseal(tampered, "snapshot_sha256")
    with pytest.raises(CaseServiceError, match="body hash|해시"):
        validate_external_source_snapshot(tampered)


def test_provenance_tamper_fails_without_reseal() -> None:
    snapshot = _snapshot()
    tampered = copy.deepcopy(snapshot)
    tampered["source"]["publisher"] = "Other Publisher"
    with pytest.raises(CaseServiceError, match="SHA-256"):
        validate_external_source_snapshot(tampered)


def test_materialization_is_confined_and_no_overwrite(tmp_path: Path) -> None:
    (tmp_path / "workspace" / "source_snapshots").mkdir(parents=True)
    snapshot = _snapshot()
    target = tmp_path / "workspace" / "source_snapshots" / "market.json"
    result = materialize_external_source_snapshot(snapshot, target, tmp_path)
    assert result["snapshot_sha256"] == snapshot["snapshot_sha256"]
    assert json.loads(target.read_text(encoding="utf-8"))["raw_text"] == snapshot["raw_text"]
    with pytest.raises(CaseServiceError, match="already exists|이미 존재"):
        materialize_external_source_snapshot(snapshot, target, tmp_path)
    with pytest.raises(CaseServiceError, match="workspace/source_snapshots"):
        materialize_external_source_snapshot(snapshot, tmp_path / "outside.json", tmp_path)


def _market(snapshot: dict) -> dict:
    return build_market_price_candidate_from_snapshot(
        snapshot,
        price=132.50,
        currency="USD",
        entity_id="SEC_CIK:0001046257",
        financial_scope="CFS",
        instrument_id="NYSE:INGR",
        symbol="INGR",
        venue="NYSE",
        quote_type="OFFICIAL_CLOSE",
        trading_date="2026-09-14",
        observed_at="2026-09-14T16:00:00-04:00",
        as_of="2026-09-14",
        max_age_days=7,
    )


def test_market_price_builder_binds_snapshot_provenance() -> None:
    snapshot = _snapshot(tier="A")
    candidate = _market(snapshot)
    validate_market_price_candidate(candidate)
    validate_market_price_candidate_against_snapshot(candidate, snapshot)
    assert candidate["source"] == {
        "publisher": snapshot["source"]["publisher"],
        "source_type": snapshot["source"]["source_type"],
        "tier": snapshot["source"]["tier"],
        "locator": snapshot["source"]["locator"],
        "snapshot_sha256": snapshot["snapshot_sha256"],
    }


def test_wacc_and_terminal_growth_builders_bind_snapshot_sha() -> None:
    snapshot = _snapshot(tier="B")
    wacc = build_wacc_source_input_from_snapshot(
        snapshot,
        metric="risk_free_rate",
        value=0.041,
        unit="decimal",
        observed_on="2026-09-14",
        claim_class="FACT",
    )
    anchor = build_terminal_growth_anchor_from_snapshot(
        snapshot,
        metric="long_run_inflation",
        value=0.02,
        observed_on="2026-09-14",
        claim_class="ASSUMPTION",
    )
    validate_wacc_source_input(wacc)
    validate_terminal_growth_anchor_input(anchor)
    validate_wacc_source_input_against_snapshot(wacc, snapshot)
    validate_terminal_growth_anchor_against_snapshot(anchor, snapshot)
    for value in (wacc, anchor):
        assert value["source"]["publisher"] == snapshot["source"]["publisher"]
        assert value["source"]["locator"] == snapshot["source"]["locator"]
        assert value["source"]["source_sha256"] == snapshot["snapshot_sha256"]


def test_source_provenance_override_is_forbidden() -> None:
    snapshot = _snapshot()
    with pytest.raises(CaseServiceError, match="only from snapshot|snapshot에서만"):
        build_wacc_source_input_from_snapshot(
            snapshot,
            metric="risk_free_rate",
            value=0.04,
            unit="decimal",
            observed_on="2026-09-14",
            claim_class="FACT",
            source_sha256="0" * 64,
        )


def test_resealed_downstream_provenance_divergence_is_rejected() -> None:
    snapshot = _snapshot(tier="A")
    market = _market(snapshot)
    tampered_market = copy.deepcopy(market)
    tampered_market["source"]["publisher"] = "Different Publisher"
    _reseal(tampered_market, "candidate_sha256")
    validate_market_price_candidate(tampered_market)
    with pytest.raises(CaseServiceError, match="provenance mismatch|provenance 불일치"):
        validate_market_price_candidate_against_snapshot(tampered_market, snapshot)

    wacc = build_wacc_source_input_from_snapshot(
        snapshot,
        metric="risk_free_rate",
        value=0.041,
        unit="decimal",
        observed_on="2026-09-14",
        claim_class="FACT",
    )
    tampered_wacc = copy.deepcopy(wacc)
    tampered_wacc["source"]["locator"] = "https://example.org/other"
    _reseal(tampered_wacc, "input_sha256")
    validate_wacc_source_input(tampered_wacc)
    with pytest.raises(CaseServiceError, match="provenance mismatch|provenance 불일치"):
        validate_wacc_source_input_against_snapshot(tampered_wacc, snapshot)


def test_downstream_tier_policy_remains_authoritative() -> None:
    snapshot = _snapshot(tier="D")
    candidate = _market(snapshot)
    checked = validate_market_price_candidate(candidate)
    assert checked["eligible_for_human_review"] is False
