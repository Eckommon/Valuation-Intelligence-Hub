"""Evidence governance primitives / 근거 거버넌스 원시 함수."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ClaimClass(str, Enum):
    FACT = "FACT"
    NORMALIZED_FACT = "NORMALIZED_FACT"
    ASSUMPTION = "ASSUMPTION"
    DERIVED = "DERIVED"
    INTERPRETATION = "INTERPRETATION"
    UNKNOWN = "UNKNOWN"


class EvidenceStatus(str, Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    UNKNOWN_CONFLICT = "UNKNOWN_CONFLICT"
    WAIVED = "WAIVED"


class SourceTier(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


@dataclass(frozen=True)
class EvidenceRecord:
    claim_id: str
    claim_class: ClaimClass
    metric: str
    source_tier: SourceTier
    status: EvidenceStatus = EvidenceStatus.CURRENT
    waiver: str | None = None


@dataclass(frozen=True)
class PromotionDecision:
    allowed: bool
    reasons: tuple[str, ...]


def evaluate_canonical_promotion(records: list[EvidenceRecord]) -> PromotionDecision:
    """Fail closed unless all material records satisfy the evidence contract.

    모든 중요 레코드가 근거 계약을 만족하지 않으면 정식 승격을 차단한다.
    """
    reasons: list[str] = []
    if not records:
        return PromotionDecision(False, ("NO_MATERIAL_EVIDENCE",))

    for record in records:
        if not record.claim_id.strip() or not record.metric.strip():
            reasons.append("MISSING_ID_OR_METRIC")

        if record.claim_class is ClaimClass.UNKNOWN:
            reasons.append(f"UNKNOWN:{record.claim_id}")

        if record.status is EvidenceStatus.UNKNOWN_CONFLICT:
            reasons.append(f"CONFLICT:{record.claim_id}")

        if record.status is EvidenceStatus.STALE:
            reasons.append(f"STALE:{record.claim_id}")

        if record.status is EvidenceStatus.WAIVED and not (record.waiver or "").strip():
            reasons.append(f"WAIVER_WITHOUT_RATIONALE:{record.claim_id}")

        if (
            record.claim_class in {ClaimClass.FACT, ClaimClass.NORMALIZED_FACT}
            and record.source_tier is SourceTier.D
        ):
            reasons.append(f"TIER_D_CANNOT_CANONICALIZE_FACT:{record.claim_id}")

    return PromotionDecision(not reasons, tuple(dict.fromkeys(reasons)))


def require_canonical_promotion(records: list[EvidenceRecord]) -> None:
    """Raise when promotion gate fails / 승격 게이트 실패 시 예외."""
    decision = evaluate_canonical_promotion(records)
    if not decision.allowed:
        raise ValueError("canonical promotion blocked: " + ", ".join(decision.reasons))
