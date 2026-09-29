"""M30-R6 bounded dilution envelope."""
from __future__ import annotations

import copy
import hashlib
import json
from math import isfinite
from typing import Any

from valuation_hub.case_service import CaseServiceError
from valuation_hub.valuation_shares import ADJUSTMENT_CATEGORIES, FRESH, validate_valuation_share_base_context

SCHEMA = "bounded-dilution-envelope-v0.1"
STATUS = "BOUNDED_DILUTION_ENVELOPE_EVALUATED"
POLICY_ID = "BOUNDED_DILUTION_PUBLIC_DATA_V01"
RANGE_READY = "RANGE_READY_FOR_VALUATION_SCENARIOS"
HOLD_MATERIAL = "HOLD_MATERIAL_DILUTION_UNCERTAINTY"
EXACT = "EXACT"
BOUNDED = "BOUNDED"

def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")

def _sha(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()

def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    out = copy.deepcopy(value)
    out.pop(key, None)
    return out

def _num(value: Any, field: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
        raise CaseServiceError(f"{field} finite numeric required")
    number = float(value)
    if (positive and number <= 0) or (not positive and number < 0):
        raise CaseServiceError(f"{field} numeric range invalid")
    return number
