"""Base abstractions for the verification constellation."""

from __future__ import annotations

import hashlib
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class VerifierResult:
    """Outcome of a single verification check."""

    passed: bool
    check_name: str
    details: str
    counterexamples: List[Any] = field(default_factory=list)
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0,1], got {self.confidence}")


class Verifier(ABC):
    """Abstract base for all verifiers in the constellation."""

    @abstractmethod
    def name(self) -> str:
        """Human-readable verifier identifier."""
        ...

    def version(self) -> str:
        """Semantic version of this verifier."""
        return "0.1.0"

    @abstractmethod
    def verify(
        self,
        claim: Dict[str, Any],
        evidence: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> VerifierResult:
        """Run verification on a claim given supporting evidence."""
        ...

    @abstractmethod
    def applicable(self, claim: Dict[str, Any]) -> bool:
        """Return True if this verifier can meaningfully check the given claim."""
        ...

    def make_receipt(
        self, claim_id: str, result: VerifierResult
    ) -> "VerifierReceipt":
        """Generate an immutable receipt for this verification run."""
        ts = time.time()
        payload = f"{self.name()}:{self.version()}:{claim_id}:{result.passed}:{ts}"
        sig = hashlib.sha256(payload.encode()).hexdigest()
        return VerifierReceipt(
            verifier_name=self.name(),
            verifier_version=self.version(),
            claim_id=claim_id,
            result=result,
            timestamp=ts,
            signature_hash=sig,
        )


@dataclass
class VerifierReceipt:
    """Immutable record that a verifier ran on a specific claim."""

    verifier_name: str
    verifier_version: str
    claim_id: str
    result: VerifierResult
    timestamp: float
    signature_hash: str

    def verify_integrity(self) -> bool:
        """Check that the receipt has not been tampered with."""
        payload = (
            f"{self.verifier_name}:{self.verifier_version}:"
            f"{self.claim_id}:{self.result.passed}:{self.timestamp}"
        )
        expected = hashlib.sha256(payload.encode()).hexdigest()
        return expected == self.signature_hash
