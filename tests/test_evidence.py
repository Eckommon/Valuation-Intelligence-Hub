import pytest

from valuation_hub.evidence import (
    ClaimClass,
    EvidenceRecord,
    EvidenceStatus,
    SourceTier,
    evaluate_canonical_promotion,
    require_canonical_promotion,
)


def test_empty_evidence_fails_closed() -> None:
    decision = evaluate_canonical_promotion([])
    assert decision.allowed is False
    assert "NO_MATERIAL_EVIDENCE" in decision.reasons


def test_tier_a_current_fact_can_promote() -> None:
    record = EvidenceRecord(
        claim_id="revenue_2026q2",
        claim_class=ClaimClass.FACT,
        metric="revenue",
        source_tier=SourceTier.A,
    )
    assert evaluate_canonical_promotion([record]).allowed is True


def test_unknown_conflict_blocks_promotion() -> None:
    record = EvidenceRecord(
        claim_id="shares_current",
        claim_class=ClaimClass.FACT,
        metric="diluted_shares",
        source_tier=SourceTier.A,
        status=EvidenceStatus.UNKNOWN_CONFLICT,
    )
    decision = evaluate_canonical_promotion([record])
    assert decision.allowed is False
    assert any(reason.startswith("CONFLICT:") for reason in decision.reasons)


def test_stale_material_fact_blocks_promotion() -> None:
    record = EvidenceRecord(
        claim_id="risk_free_rate",
        claim_class=ClaimClass.FACT,
        metric="risk_free_rate",
        source_tier=SourceTier.B,
        status=EvidenceStatus.STALE,
    )
    with pytest.raises(ValueError):
        require_canonical_promotion([record])


def test_tier_d_cannot_independently_support_canonical_fact() -> None:
    record = EvidenceRecord(
        claim_id="forum_revenue",
        claim_class=ClaimClass.FACT,
        metric="revenue",
        source_tier=SourceTier.D,
    )
    assert evaluate_canonical_promotion([record]).allowed is False


def test_waiver_requires_rationale() -> None:
    record = EvidenceRecord(
        claim_id="beta",
        claim_class=ClaimClass.FACT,
        metric="beta",
        source_tier=SourceTier.B,
        status=EvidenceStatus.WAIVED,
    )
    assert evaluate_canonical_promotion([record]).allowed is False


def test_explicit_waiver_can_pass_gate() -> None:
    record = EvidenceRecord(
        claim_id="beta",
        claim_class=ClaimClass.FACT,
        metric="beta",
        source_tier=SourceTier.B,
        status=EvidenceStatus.WAIVED,
        waiver="No newer comparable beta source; accepted for exploratory v0.1 run.",
    )
    assert evaluate_canonical_promotion([record]).allowed is True
