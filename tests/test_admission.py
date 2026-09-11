"""M11 reviewed-Draft canonical admission tests / 검토 Draft 정식 수용 테스트."""

from __future__ import annotations

import copy
import hashlib
import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

import pytest

from valuation_hub import cli
from valuation_hub.admission import build_admission_bundle, validate_admission_bundle
from valuation_hub.case_service import CaseServiceError, run_case, validate_case
from valuation_hub.draft_service import template
from valuation_hub.interactive import evidence_view, preview_case
from valuation_hub.promotion import build_candidate, validate_candidate
from valuation_hub.promotion_package import build_promotion_package
from valuation_hub.web import case_view
from valuation_hub.web_admission import make_handler, render_admission_lab
from valuation_hub.web_product import render_product_case

ROOT = Path(__file__).resolve().parents[1]


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _draft(model: str) -> dict:
    draft = template(model, ROOT)
    if model == "equity_fcff":
        base = draft["equity"]["scenarios"]["BASE"]
        bear = copy.deepcopy(base)
        bull = copy.deepcopy(base)
        bear["wacc"] = 0.12
        bear["terminal_growth"] = 0.015
        bull["wacc"] = 0.09
        bull["terminal_growth"] = 0.03
        draft["equity"]["scenarios"] = {"BEAR": bear, "BASE": base, "BULL": bull}
    return draft


def _approved_candidate(model: str) -> dict:
    candidate = build_candidate(_draft(model))
    draft = candidate["draft"]
    if model == "equity_fcff":
        observed = {
            "market_price": draft["market_price"],
            "equity.diluted_shares": draft["equity"]["diluted_shares"],
            "equity.debt": draft["equity"]["debt"],
            "equity.cash": draft["equity"]["cash"],
            "equity.minority_interest": draft["equity"]["minority_interest"],
        }
    else:
        observed = {"market_price": draft["market_price"]}

    evidence = []
    for binding in candidate["input_governance"]:
        path = binding["path"]
        if path in observed:
            claim_id = "adm_" + path.replace(".", "_").replace("[", "_").replace("]", "")
            binding.update(
                {
                    "class": "FACT",
                    "claim_ids": [claim_id],
                    "rationale": "Observed value supported by M11 test evidence.",
                }
            )
            evidence.append(
                {
                    "claim_id": claim_id,
                    "class": "FACT",
                    "metric": path,
                    "value": observed[path],
                    "unit": draft["currency"],
                    "as_of": "2026-09-11",
                    "status": "CURRENT",
                    "waiver": None,
                    "source": {
                        "publisher": "M11 test evidence",
                        "locator": f"https://example.invalid/{claim_id}",
                        "tier": "B",
                    },
                }
            )
        else:
            binding.update(
                {
                    "class": "ASSUMPTION",
                    "claim_ids": [],
                    "rationale": "Explicit forward-model assumption reviewed for M11 test.",
                }
            )
    candidate["evidence"] = evidence
    assessment = validate_candidate(candidate)
    candidate["review"] = {
        "decision": "APPROVE",
        "reviewer": "m11-human-reviewer",
        "reviewed_at": "2026-09-11T15:00:00+09:00",
        "rationale": "Reviewed evidence, assumptions, and canonical adapter compatibility.",
        "scope_sha256": assessment["review_scope_sha256"],
    }
    return candidate


def _package(model: str) -> dict:
    if model == "equity_fcff":
        identity = ("KR_TEST_REVIEWED_EQUITY", "Reviewed Equity", "검토 주식", "public_equity")
    else:
        identity = ("US_TEST_REVIEWED_VENTURE", "Reviewed Venture", "검토 벤처", "public_equity_venture")
    return build_promotion_package(
        _approved_candidate(model),
        case_id=identity[0],
        display_name_en=identity[1],
        display_name_ko=identity[2],
        asset_class=identity[3],
        root=ROOT,
    )


def _install_admission(bundle: dict, repo: Path) -> None:
    registry_path = repo / "registry" / "cases.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps({"registry_version": "0.1", "cases": [bundle["registry_entry"]]}, ensure_ascii=False),
        encoding="utf-8",
    )
    target = repo / bundle["target_path"]
    target.mkdir(parents=True, exist_ok=True)
    for name, value in bundle["artifacts"].items():
        path = target / name
        if isinstance(value, str):
            path.write_text(value, encoding="utf-8")
        else:
            path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _post(url: str, payload: dict):
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return urlopen(request, timeout=4)


def test_admission_bundle_is_deterministic_and_declares_versioned_adapter() -> None:
    package = _package("equity_fcff")
    left = build_admission_bundle(copy.deepcopy(package), ROOT)
    right = build_admission_bundle(copy.deepcopy(package), ROOT)
    assert left == right
    assert left["canonical"] is False
    assert left["status"] == "CANONICAL_ADMISSION_PROPOSED"
    assert left["registry_entry"]["adapter"] == "reviewed-draft-equity-fcff-v0.1"
    assert left["artifacts"]["case_inputs.json"]["reviewed_draft"] == package["artifacts"]["reviewed_candidate.json"]["draft"]
    result = validate_admission_bundle(left, ROOT)
    assert result["valid"] is True
    assert result["valuation_as_of"] == "2026-09-11"


def test_venture_admission_uses_versioned_venture_adapter_losslessly() -> None:
    package = _package("venture_probability")
    bundle = build_admission_bundle(package, ROOT)
    assert bundle["registry_entry"]["adapter"] == "reviewed-draft-venture-probability-v0.1"
    staged = package["artifacts"]["staged_valuation_result.json"]["valuation"]["runtime"]
    admitted = bundle["artifacts"]["valuation_result.json"]["runtime"]
    assert admitted == staged
    assert validate_admission_bundle(bundle, ROOT)["valid"] is True


def test_generic_draft_can_stage_but_incompatible_canonical_profile_fails_closed() -> None:
    candidate = build_candidate(template("equity_fcff", ROOT))
    draft = candidate["draft"]
    observed = {
        "market_price": draft["market_price"],
        "equity.diluted_shares": draft["equity"]["diluted_shares"],
        "equity.debt": draft["equity"]["debt"],
        "equity.cash": draft["equity"]["cash"],
        "equity.minority_interest": draft["equity"]["minority_interest"],
    }
    evidence = []
    for binding in candidate["input_governance"]:
        if binding["path"] in observed:
            claim_id = "profile_" + binding["path"].replace(".", "_")
            binding.update({"class": "FACT", "claim_ids": [claim_id], "rationale": "Observed."})
            evidence.append(
                {
                    "claim_id": claim_id,
                    "class": "FACT",
                    "metric": binding["path"],
                    "value": observed[binding["path"]],
                    "as_of": "2026-09-11",
                    "status": "CURRENT",
                    "source": {"publisher": "Profile test", "locator": "https://example.invalid/profile", "tier": "B"},
                }
            )
        else:
            binding.update({"class": "ASSUMPTION", "claim_ids": [], "rationale": "Forward assumption."})
    candidate["evidence"] = evidence
    assessment = validate_candidate(candidate)
    candidate["review"] = {
        "decision": "APPROVE",
        "reviewer": "profile-reviewer",
        "reviewed_at": "2026-09-11T15:05:00+09:00",
        "rationale": "Generic Draft review.",
        "scope_sha256": assessment["review_scope_sha256"],
    }
    package = build_promotion_package(
        candidate,
        case_id="KR_TEST_BASE_ONLY_DRAFT",
        display_name_en="Base Only Draft",
        display_name_ko="단일 시나리오 Draft",
        asset_class="public_equity",
        root=ROOT,
    )
    with pytest.raises(CaseServiceError, match="BEAR/BASE/BULL"):
        build_admission_bundle(package, ROOT)


def test_market_price_evidence_date_is_required_for_canonical_valuation_date() -> None:
    package = _package("venture_probability")
    candidate = package["artifacts"]["reviewed_candidate.json"]
    market_claim = next(item for item in candidate["evidence"] if item["metric"] == "market_price")
    # Rebuilding a package from a candidate with invalid date keeps M10 semantics valid;
    # M11 must be the layer that rejects it as a canonical valuation date.
    market_claim["as_of"] = "2026/09/11"
    from valuation_hub.promotion import validate_candidate

    candidate["review"]["scope_sha256"] = validate_candidate(candidate)["review_scope_sha256"]
    rebuilt = build_promotion_package(
        candidate,
        case_id="US_TEST_BAD_DATE_VENTURE",
        display_name_en="Bad Date Venture",
        display_name_ko="잘못된 날짜 벤처",
        asset_class="public_equity_venture",
        root=ROOT,
    )
    with pytest.raises(CaseServiceError, match="YYYY-MM-DD"):
        build_admission_bundle(rebuilt, ROOT)


@pytest.mark.parametrize("model", ["equity_fcff", "venture_probability"])
def test_temporary_repository_admission_executes_through_full_read_path(model: str, tmp_path: Path) -> None:
    package = _package(model)
    bundle = build_admission_bundle(package, ROOT)
    repo = tmp_path / "repo"
    _install_admission(bundle, repo)
    case_id = bundle["case_id"]

    validation = validate_case(case_id, repo)
    assert validation["valid"] is True
    assert validation["adapter"] == bundle["registry_entry"]["adapter"]

    run = run_case(case_id, repo)
    assert run["runtime"] == bundle["artifacts"]["valuation_result.json"]["runtime"]
    assert run["market_price"] == bundle["artifacts"]["case_inputs.json"]["reviewed_draft"]["market_price"]

    evidence = evidence_view(case_id, repo)
    assert evidence["read_only"] is True
    assert evidence["bundles"][0]["file"] == "evidence_reviewed.json"
    assert evidence["claims"] == package["artifacts"]["reviewed_candidate.json"]["evidence"]

    preview = preview_case(case_id, {}, repo)
    assert preview["status"] == "PREVIEW_NOT_CANONICAL"
    if model == "equity_fcff":
        assert preview["preview"]["input_mode"] == "reviewed_absolute_draft"
        assert preview["preview"]["value_per_share"] == run["runtime"]["BASE"]["value_per_share"]
    else:
        assert preview["preview"]["expected_present_value_per_share"] == run["runtime"]["expected_present_value_per_share"]

    view = case_view(case_id, repo)
    assert view["runtime"] == run["runtime"]
    page = render_product_case(case_id, repo)
    assert "Canonical valuation / 정식 가치평가" in page
    assert bundle["registry_entry"]["display_name_en"] in page


def test_canonical_evidence_file_tamper_is_detected_after_admission(tmp_path: Path) -> None:
    bundle = build_admission_bundle(_package("equity_fcff"), ROOT)
    repo = tmp_path / "repo"
    _install_admission(bundle, repo)
    evidence_path = repo / bundle["target_path"] / "evidence_reviewed.json"
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    payload["claims"][0]["value"] = float(payload["claims"][0]["value"]) + 1
    evidence_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(CaseServiceError, match="approved package"):
        validate_case(bundle["case_id"], repo)


def test_legacy_reference_cases_remain_executable() -> None:
    for case_id in ("KR_010120_LS_ELECTRIC", "KR_229640_LS_ECO_ENERGY", "US_JTAI_JET_AI"):
        assert validate_case(case_id, ROOT)["adapter"] is None
        assert run_case(case_id, ROOT)["grounded"] is True


def test_admission_cli_and_web_use_shared_service(tmp_path: Path, capsys) -> None:
    package = _package("venture_probability")
    package_path = tmp_path / "package.json"
    package_path.write_text(json.dumps(package, ensure_ascii=False), encoding="utf-8")

    rc = cli.main(["--root", str(ROOT), "admission-build", str(package_path)])
    assert rc == 0
    cli_bundle = json.loads(capsys.readouterr().out)
    expected = build_admission_bundle(package, ROOT)
    assert cli_bundle == expected

    bundle_path = tmp_path / "admission.json"
    bundle_path.write_text(json.dumps(cli_bundle, ensure_ascii=False), encoding="utf-8")
    rc = cli.main(["--root", str(ROOT), "--json", "admission-validate", str(bundle_path)])
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["valid"] is True

    page = render_admission_lab()
    assert "Canonical Admission Lab / 정식 수용 랩" in page
    assert "Review-only boundary / 검토 전용 경계" in page

    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ROOT))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        with _post(base + "/api/admission/build", package) as response:
            web_bundle = json.loads(response.read())
        assert web_bundle == expected
        with _post(base + "/api/admission/validate", web_bundle) as response:
            validated = json.loads(response.read())
        assert validated["valid"] is True
        with urlopen(base + "/", timeout=4) as response:
            dashboard = response.read().decode("utf-8")
        assert "Open Canonical Admission Lab / 정식 수용 랩 열기" in dashboard
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=4)


def test_admission_builders_never_mutate_current_canonical_repository() -> None:
    protected = [
        ROOT / "registry" / "cases.json",
        ROOT / "analyses" / "equities" / "KR_010120_LS_ELECTRIC" / "case_inputs.json",
        ROOT / "analyses" / "equities" / "KR_010120_LS_ELECTRIC" / "evidence_manifest.json",
        ROOT / "analyses" / "equities" / "KR_010120_LS_ELECTRIC" / "valuation_result.json",
    ]
    before = {path: _digest(path) for path in protected}
    for model in ("equity_fcff", "venture_probability"):
        bundle = build_admission_bundle(_package(model), ROOT)
        validate_admission_bundle(bundle, ROOT)
    after = {path: _digest(path) for path in protected}
    assert before == after
