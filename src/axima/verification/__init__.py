"""Phase R6: Proof and Verification Constellation.

Provides independent verification of claims, code, and derivations
produced by AXIMA's generation engines. No generator may grade itself.
"""

from __future__ import annotations

from .verifier_base import Verifier, VerifierReceipt, VerifierResult
from .constellation import VerificationConstellation, VerificationReport
from .confidence import ConfidenceInterval, UncertaintyConservation

__all__ = [
    "Verifier",
    "VerifierReceipt",
    "VerifierResult",
    "VerificationConstellation",
    "VerificationReport",
    "ConfidenceInterval",
    "UncertaintyConservation",
]
