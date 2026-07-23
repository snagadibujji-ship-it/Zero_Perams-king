"""Semantic checksums — content-addressed hashing with canonical normalization."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from .meaning_ir import MeaningIR


def _normalize_string(s: str) -> str:
    """Normalize a string for canonical comparison."""
    return s.strip().lower()


def _canonical_form(ir: MeaningIR) -> Dict[str, Any]:
    """Produce a fully normalized canonical form for hashing.

    Goes beyond MeaningIR._canonical_dict() by also normalizing:
    - String case (lowercase)
    - Whitespace (stripped)
    - Floating point precision (6 decimal places)
    """
    base = ir._canonical_dict()

    def _normalize_value(v: Any) -> Any:
        if isinstance(v, str):
            return _normalize_string(v)
        if isinstance(v, float):
            return round(v, 6)
        if isinstance(v, dict):
            return {_normalize_string(k) if isinstance(k, str) else k: _normalize_value(val) for k, val in sorted(v.items())}
        if isinstance(v, list):
            return [_normalize_value(item) for item in v]
        return v

    return _normalize_value(base)


def semantic_hash(ir: MeaningIR) -> str:
    """Compute a content-addressed semantic hash of a MeaningIR.

    Uses canonical form normalization to ensure that semantically
    equivalent IRs produce the same hash regardless of surface
    differences in representation.
    """
    canonical = _canonical_form(ir)
    serialized = json.dumps(canonical, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def verify_checksum(ir: MeaningIR, expected: str) -> bool:
    """Verify that a MeaningIR matches an expected semantic hash.

    Returns True if the canonical hash matches the expected value.
    """
    actual = semantic_hash(ir)
    return actual == expected
