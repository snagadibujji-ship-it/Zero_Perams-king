"""AXIMA Evidence subsystem — claims, derivations, provenance, and contradiction resolution."""

from .claims import Claim, ClaimStatus, ClaimGraph
from .derivation import DerivationStep, DerivationDAG
from .provenance import SourceTier, EvidenceRecord, ProvenanceStore
from .reality_ledger import LedgerEvent, EventType, RealityLedger
from .contradiction import ContradictionCase, Resolution, ContradictionCourt

__all__ = [
    "Claim", "ClaimStatus", "ClaimGraph",
    "DerivationStep", "DerivationDAG",
    "SourceTier", "EvidenceRecord", "ProvenanceStore",
    "LedgerEvent", "EventType", "RealityLedger",
    "ContradictionCase", "Resolution", "ContradictionCourt",
]
