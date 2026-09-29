from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from valuation_hub import cli_entry_m30r6
from valuation_hub.case_service import CaseServiceError
from valuation_hub.dilution_envelope_source import (
    build_source_bound_dilution_envelope_manifest,
    validate_source_bound_dilution_envelope_manifest,
)
from valuation_hub.disclosure_limited_dilution import (
    ROLE_ANCHOR,
    ROLE_BUFFER,
    ROLE_PERFORMANCE_UPLIFT,
    ROLE_SUBSEQUENT,
)
from valuation_hub.external_source import build_external_source_snapshot


PROXY_LOCATOR = "https://www.sec.gov/Archives/edgar/data/1046257/000104625726000151/ingr-20260402.htm"
Q2_LOCATOR = "https://www.sec.gov/Archives/edgar/data/1046257/000162828026054722/ingr-20260630.htm"

PROXY_TEXT = """
<html><body>
<p>Equity Compensation Plan Information as of December 31, 2025.</p>
<p>Total 2,177,904 securities under equity compensation plans.</p>
<p>151,570 PSUs at 100% vesting assumption.</p>
<p>510,000 RSUs outstanding as of December 31, 2025.</p>
<p>35,694 phantom stock units under non-stockholder-approved plans.</p>
</body></html>
"""

Q2_TEXT = """
<html><body>
<p>Granted 215 thousand employee RSUs through June 30, 2026.</p>
<p>For year-to-date 2026, we awarded 116 thousand performance shares.</p>
<p>For the 2026 performance shares, vesting can range from zero to 200 percent.</p>
</body></html>
"""


def _snapshot(raw_text: str, locator: str, *, tier: str = "A") -> dict:
    return build_external_source_snapshot(
        raw_text,
        source_publisher="U.S. Securities and Exchange Commission",
        source_type="issuer_filing_snapshot",
        source_tier=tier,
        source_locator=locator,
        captured_at="2026-09-30T06:00:00+09:00",
    )


def _snapshots() -> tuple[dict, dict]:
    return _snapshot(PROXY_TEXT, PROXY_LOCATOR), _snapshot(Q2_TEXT, Q2_LOCATOR)


def _binding(snapshot: dict, excerpt: str, observed_quantity: int, unit_multiplier: int = 1) -> dict:
    return {
        "snapshot_sha256": snapshot["snapshot_sha256"],
        "evidence_excerpt": excerpt,
        "observed_quantity": observed_quantity,
        "unit_multiplier": unit_multiplier,
    }


def _specs(proxy: dict, q2: dict) -> list[dict]:
    q2_psu_excerpt = "For year-to-date 2026, we awarded 116 thousand performance shares."
    q2_rsu_excerpt = "Granted 215 thousand employee RSUs through June 30, 2026."
    return [
        {
            "component_id": "2025YE_EQUITY_PLAN_SECURITIES",
            "role": ROLE_ANCHOR,
            "shares": 2_177_904,
            "as_of": "2025-12-31",
            "evidence_basis": "Issuer proxy total securities reflected in the equity compensation plan table.",
            "source_bindings": [
                _binding(proxy, "Total 2,177,904 securities under equity compensation plans.", 2_177_904),
            ],
            "calculation": None,
        },
        {
            "component_id": "2026_YTD_RSU_GRANTS",
            "role": ROLE_SUBSEQUENT,
            "shares": 215_000,
            "as_of": "2026-06-30",
            "evidence_basis": "Issuer Q2 YTD employee RSU grants.",
            "source_bindings": [
                _binding(q2, q2_rsu_excerpt, 215, 1000),
            ],
            "calculation": None,
        },
        {
            "component_id": "2026_YTD_PSU_GRANTS",
            "role": ROLE_SUBSEQUENT,
            "shares": 116_000,
            "as_of": "2026-06-30",
            "evidence_basis": "Issuer Q2 YTD performance-share grants.",
            "source_bindings": [
                _binding(q2, q2_psu_excerpt, 116, 1000),
            ],
            "calculation": None,
        },
        {
            "component_id": "PSU_200_PERCENT_MAX_UPLIFT",
            "role": ROLE_PERFORMANCE_UPLIFT,
            "shares": 267_570,
            "as_of": "2026-06-30",
            "evidence_basis": "Extra 100% uplift above proxy target PSUs plus 2026 YTD PSU grants.",
            "source_bindings": [
                _binding(proxy, "151,570 PSUs at 100% vesting assumption.", 151_570),
                _binding(q2, q2_psu_excerpt, 116, 1000),
            ],
            "calculation": None,
        },
        {
            "component_id": "DISCLOSURE_LAG_BUFFER",
            "role": ROLE_BUFFER,
            "shares": 331_000 * 76 / 181,
            "as_of": "2026-09-14",
            "evidence_basis": "Observed H1 gross RSU+PSU grant run-rate pro-rated over the disclosure lag.",
            "source_bindings": [
                _binding(q2, q2_rsu_excerpt, 215, 1000),
                _binding(q2, q2_psu_excerpt, 116, 1000),
            ],
            "calculation": {
                "method": "PRO_RATA_GROSS_GRANT_RUN_RATE_V01",
                "observed_gross_grants": 331_000,
                "observed_days": 181,
                "lag_days": 76,
            },
        },
    ]


def _rehash(value: dict) -> dict:
    copied = copy.deepcopy(value)
    copied.pop("manifest_sha256", None)
    value["manifest_sha256"] = hashlib.sha256(
        json.dumps(copied, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    return value


def test_source_bound_manifest_reproduces_real_shaped_r6_components() -> None:
    proxy, q2 = _snapshots()
    manifest = build_source_bound_dilution_envelope_manifest(_specs(proxy, q2), [proxy, q2])
    checked = validate_source_bound_dilution_envelope_manifest(manifest)

    assert checked["status"] == "PASS_SOURCE_BOUND_DILUTION_ENVELOPE_VALIDATION"
    assert checked["component_count"] == 5
    assert checked["source_snapshot_count"] == 2
    assert [row["role"] for row in checked["components"]] == [
        ROLE_ANCHOR,
        ROLE_SUBSEQUENT,
        ROLE_SUBSEQUENT,
        ROLE_PERFORMANCE_UPLIFT,
        ROLE_BUFFER,
    ]
    assert checked["components"][0]["shares"] == 2_177_904
    assert checked["components"][3]["shares"] == 267_570
    assert checked["components"][4]["calculation"]["observed_gross_grants"] == 331_000


def test_manifest_accepts_visible_excerpt_from_html_source() -> None:
    proxy, q2 = _snapshots()
    manifest = build_source_bound_dilution_envelope_manifest(_specs(proxy, q2), [proxy, q2])
    assert manifest["source_policy"]["required_tier"] == "A"


def test_excerpt_mismatch_fails_closed() -> None:
    proxy, q2 = _snapshots()
    specs = _specs(proxy, q2)
    specs[0]["source_bindings"][0]["evidence_excerpt"] = "Total 9,999,999 securities under equity compensation plans."
    specs[0]["source_bindings"][0]["observed_quantity"] = 9_999_999
    specs[0]["shares"] = 9_999_999
    with pytest.raises(CaseServiceError, match="excerpt"):
        build_source_bound_dilution_envelope_manifest(specs, [proxy, q2])


def test_direct_claim_must_equal_bound_quantity() -> None:
    proxy, q2 = _snapshots()
    specs = _specs(proxy, q2)
    specs[1]["shares"] = 216_000
    with pytest.raises(CaseServiceError, match="direct envelope claim"):
        build_source_bound_dilution_envelope_manifest(specs, [proxy, q2])


def test_performance_uplift_must_equal_bound_claim_sum() -> None:
    proxy, q2 = _snapshots()
    specs = _specs(proxy, q2)
    specs[3]["shares"] = 267_571
    with pytest.raises(CaseServiceError, match="performance uplift"):
        build_source_bound_dilution_envelope_manifest(specs, [proxy, q2])


def test_buffer_gross_grants_must_reconcile_to_bound_claims() -> None:
    proxy, q2 = _snapshots()
    specs = _specs(proxy, q2)
    specs[4]["calculation"]["observed_gross_grants"] = 330_000
    with pytest.raises(CaseServiceError, match="observed gross grants"):
        build_source_bound_dilution_envelope_manifest(specs, [proxy, q2])


def test_tier_b_source_is_rejected_for_real_r7x_envelope() -> None:
    proxy = _snapshot(PROXY_TEXT, PROXY_LOCATOR, tier="B")
    q2 = _snapshot(Q2_TEXT, Q2_LOCATOR)
    with pytest.raises(CaseServiceError, match="Tier-A"):
        build_source_bound_dilution_envelope_manifest(_specs(proxy, q2), [proxy, q2])


def test_embedded_snapshot_tamper_is_revalidated_not_hash_only() -> None:
    proxy, q2 = _snapshots()
    manifest = build_source_bound_dilution_envelope_manifest(_specs(proxy, q2), [proxy, q2])
    tampered = copy.deepcopy(manifest)
    tampered["source_snapshots"][0]["raw_text"] += "tampered"
    _rehash(tampered)
    with pytest.raises(CaseServiceError, match="hash|SHA"):
        validate_source_bound_dilution_envelope_manifest(tampered)


def test_spec_tamper_cannot_be_rehashed_into_valid_manifest() -> None:
    proxy, q2 = _snapshots()
    manifest = build_source_bound_dilution_envelope_manifest(_specs(proxy, q2), [proxy, q2])
    tampered = copy.deepcopy(manifest)
    tampered["component_specs"][0]["shares"] = 2_177_905
    tampered["components"][0]["shares"] = 2_177_905
    _rehash(tampered)
    with pytest.raises(CaseServiceError, match="direct envelope claim"):
        validate_source_bound_dilution_envelope_manifest(tampered)


def test_cli_build_validate_and_r6_projection(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    proxy, q2 = _snapshots()
    specs = _specs(proxy, q2)

    spec_path = tmp_path / "specs.json"
    proxy_path = tmp_path / "proxy.json"
    q2_path = tmp_path / "q2.json"
    manifest_path = tmp_path / "manifest.json"
    for path, payload in (
        (spec_path, specs),
        (proxy_path, proxy),
        (q2_path, q2),
    ):
        path.write_text(json.dumps(payload), encoding="utf-8")

    rc = cli_entry_m30r6.main([
        "--root",
        str(tmp_path),
        "--json",
        "dilution-envelope-source-build",
        str(spec_path),
        str(proxy_path),
        str(q2_path),
    ])
    assert rc == 0
    manifest = json.loads(capsys.readouterr().out)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    rc = cli_entry_m30r6.main([
        "--root",
        str(tmp_path),
        "--json",
        "dilution-envelope-source-validate",
        str(manifest_path),
    ])
    assert rc == 0
    validated = json.loads(capsys.readouterr().out)
    assert validated["component_count"] == 5

    for name in ("base", "inventory", "historical"):
        (tmp_path / f"{name}.json").write_text("{}", encoding="utf-8")

    seen: dict = {}

    def fake_build(base, inventory, historical, upper, **kwargs):
        seen["upper"] = upper
        seen["kwargs"] = kwargs
        return {"status": "TEST", "component_count": len(upper)}

    monkeypatch.setattr(cli_entry_m30r6, "build_disclosure_limited_dilution_evidence", fake_build)
    rc = cli_entry_m30r6.main([
        "--root",
        str(tmp_path),
        "--json",
        "dilution-assumption-evidence-build",
        str(tmp_path / "base.json"),
        str(tmp_path / "inventory.json"),
        str(tmp_path / "historical.json"),
        str(manifest_path),
        "--as-of",
        "2026-09-14",
    ])
    assert rc == 0
    projected = json.loads(capsys.readouterr().out)
    assert projected["component_count"] == 5
    assert seen["upper"] == manifest["components"]
    assert seen["kwargs"]["materiality_threshold"] == 0.05
