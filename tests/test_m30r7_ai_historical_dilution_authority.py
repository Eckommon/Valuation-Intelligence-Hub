from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from valuation_hub import cli_entry_m30r7

from valuation_hub.ai_historical_dilution_authority import (
    ADJUDICATOR_ID,
    REQUIRED_CRITERIA,
    build_ai_historical_dilution_adjudication,
    build_ai_historical_dilution_evidence,
    build_ai_reviewed_historical_dilution_package,
    validate_ai_historical_dilution_adjudication,
    validate_ai_historical_dilution_evidence,
    validate_ai_reviewed_historical_dilution_package,
)
from valuation_hub.case_service import CaseServiceError
from valuation_hub.disclosure_limited_dilution import _historical_diluted_shares
from valuation_hub.sec_live import (
    TransportResponse,
    capture_companyfacts_snapshot,
    companyfacts_locator,
)
from valuation_hub.share_dilution import (
    extract_sec_dilution_candidate,
    normalize_share_dilution_candidate,
    validate_historical_dilution,
)

CIK = "0001046257"
ACCN = "0001628280-26-054722"
PRIMARY = "https://www.sec.gov/Archives/edgar/data/1046257/000162828026054722/ingr-20260630.htm"


def _snapshot() -> dict:
    payload = {
        "cik": 1046257,
        "entityName": "Ingredion Incorporated",
        "facts": {
            "us-gaap": {
                "WeightedAverageNumberOfSharesOutstandingBasic": {
                    "units": {
                        "shares": [
                            {
                                "start": "2026-04-01",
                                "end": "2026-06-30",
                                "val": 63_300_000,
                                "accn": ACCN,
                                "fy": 2026,
                                "fp": "Q2",
                                "form": "10-Q",
                                "filed": "2026-08-07",
                                "frame": "CY2026Q2",
                            }
                        ]
                    }
                },
                "WeightedAverageNumberOfDilutedSharesOutstanding": {
                    "units": {
                        "shares": [
                            {
                                "start": "2026-04-01",
                                "end": "2026-06-30",
                                "val": 63_900_000,
                                "accn": ACCN,
                                "fy": 2026,
                                "fp": "Q2",
                                "form": "10-Q",
                                "filed": "2026-08-07",
                                "frame": "CY2026Q2",
                            }
                        ]
                    }
                },
            }
        },
    }
    body = json.dumps(payload, separators=(",", ":")).encode()

    def transport(locator: str, *, user_agent: str) -> TransportResponse:
        assert locator == companyfacts_locator(CIK)
        return TransportResponse(200, "application/json", body, locator)

    return capture_companyfacts_snapshot(
        CIK,
        user_agent="M30R7 test-contact@example.com",
        transport=transport,
        fetched_at="2026-09-15T17:42:53+00:00",
    )


def _pairs() -> tuple[dict, dict, dict, dict]:
    snapshot = _snapshot()
    basic_candidate = extract_sec_dilution_candidate(
        snapshot,
        "weighted_average_basic_shares",
        period_start="2026-04-01",
        period_end="2026-06-30",
        form="10-Q",
    )
    diluted_candidate = extract_sec_dilution_candidate(
        snapshot,
        "weighted_average_diluted_shares",
        period_start="2026-04-01",
        period_end="2026-06-30",
        form="10-Q",
    )
    return (
        basic_candidate,
        normalize_share_dilution_candidate(basic_candidate),
        diluted_candidate,
        normalize_share_dilution_candidate(diluted_candidate),
    )


def _evidence(
    basic_candidate: dict,
    basic_observation: dict,
    diluted_candidate: dict,
    diluted_observation: dict,
    *,
    contradictions: list[str] | None = None,
) -> dict:
    return build_ai_historical_dilution_evidence(
        basic_candidate,
        basic_observation,
        diluted_candidate,
        diluted_observation,
        primary_filing_locator=PRIMARY,
        evidence_basis=(
            "Exact issuer SEC 2026 Q2 EPS denominator facts reproduce the same "
            "quarter, filing, entity and source lineage."
        ),
        contradiction_search_summary=(
            "Issuer filing and CompanyFacts pair checked for contrary denominator "
            "values at equal precedence; none identified."
        ),
        material_contradictions=[] if contradictions is None else contradictions,
        criteria={key: True for key in REQUIRED_CRITERIA},
    )


def _package() -> dict:
    basic_candidate, basic_observation, diluted_candidate, diluted_observation = _pairs()
    evidence = _evidence(
        basic_candidate,
        basic_observation,
        diluted_candidate,
        diluted_observation,
    )
    adjudication = build_ai_historical_dilution_adjudication(
        evidence,
        basic_candidate,
        basic_observation,
        diluted_candidate,
        diluted_observation,
        adjudicated_at="2026-09-29T18:20:00+09:00",
    )
    return build_ai_reviewed_historical_dilution_package(
        basic_candidate,
        basic_observation,
        diluted_candidate,
        diluted_observation,
        evidence,
        adjudication,
    )


def _rehash(value: dict, field: str) -> dict:
    out = copy.deepcopy(value)
    body = copy.deepcopy(out)
    body.pop(field, None)
    out[field] = hashlib.sha256(
        json.dumps(
            body,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()
    return out


def test_real_shaped_m21_ai_authority_produces_existing_derived_fact_contract() -> None:
    package = _package()
    checked = validate_ai_reviewed_historical_dilution_package(package)

    assert checked["review_authority"] == "AI"
    assert checked["r6_anchor_eligible"] is True
    assert checked["basic_shares"] == 63_300_000
    assert checked["diluted_shares"] == 63_900_000
    assert checked["historical_incremental_diluted_shares"] == 600_000
    assert package["adjudication"]["adjudicator"]["id"] == ADJUDICATOR_ID

    historical = package["historical_dilution"]
    assert historical["class"] == "DERIVED_FACT"
    assert historical["historical_dilution_factor"] == pytest.approx(
        63_900_000 / 63_300_000
    )
    assert historical["semantic_boundary"]["historical_only"] is True
    assert historical["semantic_boundary"]["valuation_date_direct_bind"] is False
    assert validate_historical_dilution(historical)["class"] == "DERIVED_FACT"


def test_r6_accepts_full_r7_authority_package_as_historical_anchor() -> None:
    package = _package()
    diluted, freshness = _historical_diluted_shares(
        package,
        as_of="2026-09-14",
        max_age_days=180,
    )
    assert diluted == 63_900_000
    assert freshness["age_days"] == 76
    assert (
        freshness["authority_status"]
        == "PASS_AI_REVIEWED_HISTORICAL_DILUTION_VALIDATION"
    )


def test_material_contradiction_fails_before_adjudication() -> None:
    pair = _pairs()
    with pytest.raises(CaseServiceError, match="contradiction"):
        _evidence(*pair, contradictions=["Conflicting issuer denominator identified."])


def test_period_or_filing_mismatch_fails_closed() -> None:
    basic_candidate, basic_observation, diluted_candidate, diluted_observation = _pairs()

    bad = copy.deepcopy(diluted_observation)
    bad["period"]["start"] = "2026-01-01"
    bad = _rehash(bad, "observation_sha256")
    with pytest.raises(CaseServiceError):
        _evidence(
            basic_candidate,
            basic_observation,
            diluted_candidate,
            bad,
        )

    bad_candidate = copy.deepcopy(diluted_candidate)
    bad_candidate["filing"]["accession"] = "0001628280-26-054723"
    bad_candidate = _rehash(bad_candidate, "candidate_sha256")
    bad_observation = normalize_share_dilution_candidate(bad_candidate)
    with pytest.raises(CaseServiceError, match="filing mismatch"):
        _evidence(
            basic_candidate,
            basic_observation,
            bad_candidate,
            bad_observation,
        )


def test_false_criterion_and_future_before_filing_adjudication_fail_closed() -> None:
    pair = _pairs()
    criteria = {key: True for key in REQUIRED_CRITERIA}
    criteria[REQUIRED_CRITERIA[3]] = False
    with pytest.raises(CaseServiceError, match="criteria"):
        build_ai_historical_dilution_evidence(
            *pair,
            primary_filing_locator=PRIMARY,
            evidence_basis="Exact source evidence.",
            contradiction_search_summary="No material contradiction.",
            material_contradictions=[],
            criteria=criteria,
        )

    evidence = _evidence(*pair)
    with pytest.raises(CaseServiceError, match="precede filing"):
        build_ai_historical_dilution_adjudication(
            evidence,
            *pair,
            adjudicated_at="2026-08-06T12:00:00+00:00",
        )


def test_package_recomputes_reviewed_observations_not_hash_only() -> None:
    package = _package()
    tampered = copy.deepcopy(package)
    tampered["reviewed_observations"]["diluted"]["value"] = 64_000_000
    tampered["reviewed_observations"]["diluted"] = _rehash(
        tampered["reviewed_observations"]["diluted"],
        "observation_sha256",
    )
    tampered = _rehash(tampered, "package_sha256")
    with pytest.raises(CaseServiceError, match="projection mismatch"):
        validate_ai_reviewed_historical_dilution_package(tampered)


def test_manual_class_flip_is_not_an_r7_authority_package() -> None:
    _, basic_observation, _, diluted_observation = _pairs()
    basic = copy.deepcopy(basic_observation)
    diluted = copy.deepcopy(diluted_observation)
    basic["class"] = diluted["class"] = "NORMALIZED_FACT"
    basic = _rehash(basic, "observation_sha256")
    diluted = _rehash(diluted, "observation_sha256")

    from valuation_hub.share_dilution import derive_historical_dilution

    legacy = derive_historical_dilution(basic, diluted)
    assert legacy["class"] == "DERIVED_FACT"
    with pytest.raises(CaseServiceError, match="R7 package"):
        validate_ai_reviewed_historical_dilution_package(legacy)


def test_evidence_and_adjudication_validators_lock_lineage() -> None:
    pair = _pairs()
    evidence = _evidence(*pair)
    checked = validate_ai_historical_dilution_evidence(evidence, *pair)
    assert checked["status"] == "PASS_AI_HISTORICAL_DILUTION_EVIDENCE_VALIDATION"

    adjudication = build_ai_historical_dilution_adjudication(
        evidence,
        *pair,
        adjudicated_at="2026-09-29T18:20:00+09:00",
    )
    checked_adjudication = validate_ai_historical_dilution_adjudication(
        adjudication,
        evidence,
        *pair,
    )
    assert (
        checked_adjudication["status"]
        == "PASS_AI_HISTORICAL_DILUTION_ADJUDICATION_VALIDATION"
    )


def test_r7_cli_build_and_prior_delegation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pair = _pairs()
    names = (
        "basic_candidate",
        "basic_observation",
        "diluted_candidate",
        "diluted_observation",
    )
    paths: list[Path] = []
    for name, value in zip(names, pair):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        paths.append(path)

    argv = [
        "--root",
        str(tmp_path),
        "--json",
        "historical-dilution-ai-evidence-build",
        *(str(path) for path in paths),
        "--primary-filing-locator",
        PRIMARY,
        "--evidence-basis",
        "Exact issuer SEC Q2 denominator evidence.",
        "--contradiction-search-summary",
        "No material contrary denominator evidence identified.",
    ]
    for criterion in REQUIRED_CRITERIA:
        argv.extend(["--criterion", criterion])

    assert cli_entry_m30r7.main(argv) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["pair"]["basic_shares"] == 63_300_000
    assert out["pair"]["diluted_shares"] == 63_900_000
    assert all(out["criteria"].values())

    seen: list[list[str]] = []
    monkeypatch.setattr(
        cli_entry_m30r7.prior_cli,
        "main",
        lambda values: seen.append(list(values)) or 29,
    )
    old = ["dilution-assumption-package-validate", "package.json"]
    assert cli_entry_m30r7.main(old) == 29
    assert seen == [old]
