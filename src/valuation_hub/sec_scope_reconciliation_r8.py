"""M30-R8SCOPE: independent SEC-filed financial-scope reconciliation.

Original cash AS_REPORTED and SEC-debt CFS sources are immutable. This module
creates a noncanonical, source-embedded typed bridge when one Tier-A issuer
10-Q itself supports both amounts within its consolidated statement notes.

The policy adjudicator is RULE_BASED, not a human approval or a conversion
of the source object's financial_scope string.
"""
from __future__ import annotations

import copy
import hashlib
from html.parser import HTMLParser
import json
import re
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.external_source import validate_external_source_snapshot
from valuation_hub.financial_normalization import validate_financial_observation
from valuation_hub.r8_assumption_proof import validate_r6_binding_proof
from valuation_hub.sec_aggregate_debt_authority import validate_sec_aggregate_debt_binding_context

BRIDGE_SCHEMA = "sec-consolidated-scope-reconciliation-v0.1"
BRIDGE_POLICY = "INGR_2026Q2_CONSOLIDATED_STATEMENT_SCOPE_V01"
REVIEW_AUTHORITY = "RULE_BASED_SOURCE_RECONCILIATION"
SOURCE_SHA = "f61f33b0e27403ab56882d8cc1daa3a66571e9452fc5d8012268f39ab098b0f9"
LOCATOR = "https://www.sec.gov/Archives/edgar/data/1046257/000162828026054722/ingr-20260630.htm"
ACCESSION = "0001628280-26-054722"
ENTITY = "SEC_CIK:0001046257"
AS_OF = "2026-09-14"
DATE = "2026-06-30"
CASH_SHA = "c4c7cc9768835cd4ada7129f1ca33d6f7cf9b08a795e08d0085639f90d4551ec"
DEBT_SHA = "1339821cb11c66482cfcbff66838ea6bdd42d32ebabcd32927e6839e6fa1286a"
R8_SHA = "8abc7cf93fd3e2bf93422e915ab4fe5c6ebad2faef34a0a2f7596038eda55cc9"


def _digest(x: Any) -> str:
    return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _without(x: dict[str, Any], field: str) -> dict[str, Any]:
    obj = copy.deepcopy(x)
    obj.pop(field, None)
    return obj


class _Visible(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, text: str) -> None:
        if text:
            self.parts.append(text)


def _visible_html(html: str) -> str:
    parser = _Visible()
    try:
        parser.feed(html)
        parser.close()
    except Exception as exc:
        raise CaseServiceError("SEC 10-Q HTML cannot be normalized") from exc
    return " ".join(" ".join(parser.parts).split())


def _source_checks(snapshot: dict[str, Any]) -> dict[str, Any]:
    checked = validate_external_source_snapshot(snapshot)
    src = snapshot["source"]
    if (checked["snapshot_sha256"] != SOURCE_SHA
        or src["tier"] != "A"
        or src["locator"] != LOCATOR
        or src["publisher"] not in ("SEC", "U.S. Securities and Exchange Commission")
        or not re.search(r"(issuer|filing|10-q)", src["source_type"], re.I)):
        raise CaseServiceError("non-identical SEC Tier-A immutable Q2 source")
    visible = _visible_html(snapshot["raw_text"])
    # Source is a consolidated issuer filing, not a company-level bare API label.
    bal = visible.find("Condensed Consolidated Balance Sheets")
    notes = visible.find("Notes to the Condensed Consolidated Financial Statements")
    finance = visible.find("Financing Arrangements")
    if bal < 0 or notes < 0 or finance < 0:
        raise CaseServiceError("Q2 consolidated statement/notes headings absent")
    if not re.search(r"Cash and cash equivalents\s+\$\s*948\b", visible[bal:], re.I):
        raise CaseServiceError("source-bound consolidated cash USD948m not reproduced")
    if not re.search(r"Total long-term debt\s+1,742\b", visible[finance:], re.I):
        raise CaseServiceError("source-bound Q2 long-term debt USD1742m not reproduced")
    if not re.search(r"Total short-term borrowings\s+41\b", visible[finance:], re.I):
        raise CaseServiceError("source-bound Q2 short-term debt USD41m not reproduced")
    if not re.search(r"Total debt\s+\$\s*1,783\b", visible[finance:], re.I):
        raise CaseServiceError("source-bound Q2 total debt USD1783m not reproduced")
    if "June 30, 2026" not in visible and "June 30, 2026" not in snapshot["raw_text"]:
        raise CaseServiceError("source-bound 2026 Q2 date missing")
    return {"source_snapshot_sha256": checked["snapshot_sha256"],
            "source_body_sha256": checked["body_sha256"],
            "cash_million": 948, "long_term_debt_million": 1742,
            "short_term_debt_million": 41, "total_debt_million": 1783,
            "statement": "Condensed Consolidated Balance Sheets",
            "note": "Notes to the Condensed Consolidated Financial Statements / 6. Financing Arrangements"}


def _source_filings(cash: dict[str, Any], debt: dict[str, Any]) -> None:
    cash_filing = cash.get("lineage", {}).get("filing_identity")
    debt_filing = debt.get("reviewed_profile", {}).get("filing")
    if (not isinstance(cash_filing, dict)
        or cash_filing.get("accession") != ACCESSION
        or not isinstance(debt_filing, dict)
        or debt_filing.get("accession") != ACCESSION
        or debt_filing.get("form") not in ("10-Q", "10-Q/A")):
        raise CaseServiceError("cash/debt accession does not independently tie to exact 2026 Q2 filing")


def _check_inputs(cash: dict[str, Any], debt: dict[str, Any],
                  proof: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    validate_financial_observation(cash)
    authority = validate_sec_aggregate_debt_binding_context(debt)
    validate_r6_binding_proof(proof)
    if (cash.get("observation_sha256") != CASH_SHA
        or debt.get("context_sha256") != DEBT_SHA
        or proof.get("proof_sha256") != R8_SHA
        or authority.get("review_authority") != "AI"
        or cash.get("metric") != "cash" or cash.get("class") != "NORMALIZED_FACT"
        or cash.get("value") != 948_000_000 or cash.get("unit") != "USD"
        or cash.get("period", {}).get("kind") != "INSTANT"
        or cash.get("period", {}).get("end") != DATE
        or debt.get("value") != 1_783_000_000
        or debt.get("resolved_period_end") != DATE
        or debt.get("unit") != "USD"
        or debt.get("policy", {}).get("as_of") != AS_OF
        or proof["package"].get("as_of") != AS_OF
        or proof["package"].get("class") != "ASSUMPTION"
        or proof["package"].get("value") != 63_900_000):
        raise CaseServiceError("source authority/period/quantity/SHA mismatch")
    entities = [cash.get("entity"), debt.get("entity"), proof["package"].get("entity")]
    if (any(not isinstance(e, dict) or e.get("id") != ENTITY for e in entities)
        or [e.get("financial_scope") for e in entities] != ["AS_REPORTED", "CFS", "AS_REPORTED"]):
        raise CaseServiceError("unexpected source financial_scope; no implicit conversion")
    _source_filings(cash, debt)
    return _source_checks(snapshot)


def _projection(cash: dict[str, Any], debt: dict[str, Any],
                proof: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    source = _check_inputs(cash, debt, proof, snapshot)
    out = {
        "schema_version": BRIDGE_SCHEMA,
        "status": "SOURCE_BOUND_SCOPE_RECONCILED",
        "canonical": False,
        "authority": REVIEW_AUTHORITY,
        "policy": BRIDGE_POLICY,
        "decision": "RECONCILE_FOR_INGR_2026Q2_VALUATION_ONLY",
        "entity_id": ENTITY,
        "as_of": AS_OF,
        "source_scopes": {"cash": "AS_REPORTED", "debt": "CFS", "r6_shares": "AS_REPORTED"},
        "target_scope": "AS_REPORTED",
        "source_evidence": source,
        "cash": copy.deepcopy(cash),
        "debt_context": copy.deepcopy(debt),
        "r8_proof": copy.deepcopy(proof),
        "source_snapshot": copy.deepcopy(snapshot),
        "source_cash_sha256": CASH_SHA,
        "source_debt_context_sha256": DEBT_SHA,
        "source_r8_proof_sha256": R8_SHA,
        "source_snapshot_sha256": SOURCE_SHA,
        "bridge_sha256": "",
    }
    out["bridge_sha256"] = _digest(_without(out, "bridge_sha256"))
    return out


def build_scope_bridge(cash: dict[str, Any], debt: dict[str, Any],
                       proof: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    bridge = _projection(cash, debt, proof, snapshot)
    validate_scope_bridge(bridge)
    return bridge


def validate_scope_bridge(bridge: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(bridge, dict) or bridge.get("schema_version") != BRIDGE_SCHEMA:
        raise CaseServiceError("scope bridge schema invalid")
    for field in ("cash", "debt_context", "r8_proof", "source_snapshot"):
        if not isinstance(bridge.get(field), dict):
            raise CaseServiceError("scope bridge requires full source-embedded object")
    expected = _projection(bridge["cash"], bridge["debt_context"],
                           bridge["r8_proof"], bridge["source_snapshot"])
    if bridge != expected:
        raise CaseServiceError("scope evidence, authority, source or hash differs from revalidated bridge")
    return {"status": "PASS_INGR_2026Q2_SCOPE_BRIDGE", "bridge_sha256": bridge["bridge_sha256"],
            "source_class_cash": "NORMALIZED_FACT", "source_class_debt": "DERIVED_FACT",
            "source_class_shares": "ASSUMPTION", "canonical": False}
