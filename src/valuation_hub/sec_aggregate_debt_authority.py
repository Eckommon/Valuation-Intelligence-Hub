"""Authority-aware successor for reviewed SEC aggregate debt.

The historical M30-P1 implementation remains the validator of numeric, filing,
semantic-boundary, freshness, and lineage semantics. This successor corrects only
review-authority provenance for AI-adjudicated compatibility assertions.

Legacy explicit-human profiles remain byte-for-byte compatible. AI-adjudicated
profiles must identify their binding eligibility as AI reviewed rather than human
reviewed. Mislabeled AI profiles fail closed.
"""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from valuation_hub import sec_aggregate_debt as legacy
from valuation_hub.case_service import CaseServiceError

AI_REVIEWER_ID = "AI_EVIDENCE_ADJUDICATOR_V01"
AI_REASON = "AI_REVIEWED_EXACT_SEC_AGGREGATE_DEBT"
HUMAN_REASON = "HUMAN_REVIEWED_EXACT_SEC_AGGREGATE_DEBT"


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    out = copy.deepcopy(value)
    out.pop(key, None)
    return out


def _assertion(profile: dict[str, Any]) -> dict[str, Any]:
    assertion = profile.get("review_assertion")
    if not isinstance(assertion, dict):
        raise CaseServiceError("reviewed SEC aggregate-debt assertion missing / 검토 SEC aggregate debt assertion 누락")
    return assertion


def _is_ai_assertion(assertion: dict[str, Any]) -> bool:
    return assertion.get("reviewer") == AI_REVIEWER_ID


def expected_binding_reason(assertion: dict[str, Any]) -> str:
    return AI_REASON if _is_ai_assertion(assertion) else HUMAN_REASON


def legacy_profile_view(profile: dict[str, Any]) -> dict[str, Any]:
    """Return a hash-consistent human-reason view solely for legacy validation reuse."""
    out = copy.deepcopy(profile)
    out["binding_eligibility"] = {"eligible": True, "reason": HUMAN_REASON}
    out["profile_sha256"] = _sha(_without(out, "profile_sha256"))
    return out


def finalize_reviewed_sec_aggregate_debt(
    observation: dict[str, Any], assertion: dict[str, Any]
) -> dict[str, Any]:
    profile = legacy.finalize_reviewed_sec_aggregate_debt(observation, assertion)
    if not _is_ai_assertion(assertion):
        return profile
    profile = copy.deepcopy(profile)
    profile["binding_eligibility"] = {"eligible": True, "reason": AI_REASON}
    profile["profile_sha256"] = _sha(_without(profile, "profile_sha256"))
    validate_reviewed_sec_aggregate_debt(profile)
    return profile


def validate_reviewed_sec_aggregate_debt(profile: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(profile, dict):
        raise CaseServiceError("reviewed SEC aggregate-debt profile object required / 검토 SEC aggregate debt profile 객체 필요")
    assertion = _assertion(profile)
    expected_reason = expected_binding_reason(assertion)
    expected_eligibility = {"eligible": True, "reason": expected_reason}
    if profile.get("binding_eligibility") != expected_eligibility:
        raise CaseServiceError("reviewed SEC aggregate-debt reviewer-type eligibility mismatch / 검토 SEC aggregate debt 검토주체 적격사유 불일치")

    if _is_ai_assertion(assertion):
        # Reuse all historical semantic checks without allowing the historical
        # hard-coded human reason to mislabel the actual artifact.
        legacy.validate_reviewed_sec_aggregate_debt(legacy_profile_view(profile))
    else:
        legacy.validate_reviewed_sec_aggregate_debt(profile)

    expected = _sha(_without(profile, "profile_sha256"))
    if profile.get("profile_sha256") != expected:
        raise CaseServiceError("reviewed SEC aggregate-debt profile SHA mismatch / 검토 SEC aggregate debt profile SHA 불일치")
    return {
        "status": "PASS_REVIEWED_SEC_AGGREGATE_DEBT_AUTHORITY_VALIDATION",
        "eligible": True,
        "review_authority": "AI" if _is_ai_assertion(assertion) else "HUMAN",
        "profile_sha256": expected,
    }


def legacy_context_view(context: dict[str, Any]) -> dict[str, Any]:
    """Return a hash-consistent legacy context view for historical validator reuse."""
    profile = context.get("reviewed_profile")
    if not isinstance(profile, dict):
        raise CaseServiceError("SEC aggregate debt reviewed profile missing / SEC aggregate debt reviewed profile 누락")
    legacy_profile = legacy_profile_view(profile)
    out = copy.deepcopy(context)
    out["reviewed_profile"] = legacy_profile
    out["source_debt_sha256"] = legacy_profile["profile_sha256"]
    out["source_debt_profile_sha256"] = legacy_profile["profile_sha256"]
    out["context_sha256"] = _sha(_without(out, "context_sha256"))
    return out


def build_sec_aggregate_debt_binding_context(
    profile: dict[str, Any], *, as_of: str, max_age_days: int = 550
) -> dict[str, Any]:
    checked = validate_reviewed_sec_aggregate_debt(profile)
    if checked["review_authority"] == "HUMAN":
        return legacy.build_sec_aggregate_debt_binding_context(profile, as_of=as_of, max_age_days=max_age_days)

    legacy_context = legacy.build_sec_aggregate_debt_binding_context(
        legacy_profile_view(profile), as_of=as_of, max_age_days=max_age_days
    )
    context = copy.deepcopy(legacy_context)
    context["reviewed_profile"] = copy.deepcopy(profile)
    context["source_debt_sha256"] = profile["profile_sha256"]
    context["source_debt_profile_sha256"] = profile["profile_sha256"]
    context["context_sha256"] = _sha(_without(context, "context_sha256"))
    validate_sec_aggregate_debt_binding_context(context)
    return context


def validate_sec_aggregate_debt_binding_context(context: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(context, dict):
        raise CaseServiceError("SEC aggregate-debt context object required / SEC aggregate debt context 객체 필요")
    profile = context.get("reviewed_profile")
    if not isinstance(profile, dict):
        raise CaseServiceError("SEC aggregate debt reviewed profile missing / SEC aggregate debt reviewed profile 누락")
    checked_profile = validate_reviewed_sec_aggregate_debt(profile)

    if checked_profile["review_authority"] == "AI":
        legacy_checked = legacy.validate_sec_aggregate_debt_binding_context(legacy_context_view(context))
        if context.get("source_debt_sha256") != profile.get("profile_sha256") or context.get("source_debt_profile_sha256") != profile.get("profile_sha256"):
            raise CaseServiceError("SEC aggregate debt authority profile lineage mismatch / SEC aggregate debt 검토주체 profile lineage 불일치")
    else:
        legacy_checked = legacy.validate_sec_aggregate_debt_binding_context(context)

    expected = _sha(_without(context, "context_sha256"))
    if context.get("context_sha256") != expected:
        raise CaseServiceError("SEC aggregate debt context SHA mismatch / SEC aggregate debt context SHA 불일치")
    return {
        "status": "PASS_SEC_AGGREGATE_DEBT_AUTHORITY_CONTEXT_VALIDATION",
        "eligible": legacy_checked["eligible"],
        "review_authority": checked_profile["review_authority"],
        "context_sha256": expected,
    }
