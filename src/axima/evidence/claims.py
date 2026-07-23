"""Claim lifecycle management and claim dependency graph."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple


class ClaimStatus(Enum):
    """Lifecycle status of a claim."""
    PROPOSED = "proposed"
    SUPPORTED = "supported"
    VERIFIED = "verified"
    CONTRADICTED = "contradicted"
    RETRACTED = "retracted"


@dataclass
class Claim:
    """A single epistemic claim tracked by the system."""
    id: str
    statement: str
    status: ClaimStatus
    source_engine: str
    confidence_interval: Tuple[float, float]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    valid_time: Tuple[Optional[datetime], Optional[datetime]] = (None, None)
    evidence_ids: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    derivation_id: Optional[str] = None


class ClaimGraph:
    """Directed graph of claims and their support/contradiction relationships."""

    def __init__(self) -> None:
        self._claims: Dict[str, Claim] = {}
        # edges: claim_id -> list of (target_claim_id, relation)
        self._supports: Dict[str, List[str]] = {}  # supporter -> supported
        self._contradicts: Dict[str, List[str]] = {}  # contradictor -> contradicted

    def add_claim(self, claim: Claim) -> Claim:
        """Register a new claim in the graph."""
        if claim.id in self._claims:
            raise ValueError(f"Claim {claim.id} already exists")
        self._claims[claim.id] = claim
        return claim

    def get_claim(self, claim_id: str) -> Optional[Claim]:
        """Retrieve a claim by id."""
        return self._claims.get(claim_id)

    def support(self, supporter_id: str, supported_id: str) -> None:
        """Record that supporter_id provides evidence for supported_id."""
        if supporter_id not in self._claims:
            raise KeyError(f"Supporter claim {supporter_id} not found")
        if supported_id not in self._claims:
            raise KeyError(f"Supported claim {supported_id} not found")
        self._supports.setdefault(supporter_id, []).append(supported_id)
        supported = self._claims[supported_id]
        if supported.status == ClaimStatus.PROPOSED:
            supported.status = ClaimStatus.SUPPORTED

    def contradict(self, contradictor_id: str, contradicted_id: str) -> None:
        """Record that contradictor_id contradicts contradicted_id."""
        if contradictor_id not in self._claims:
            raise KeyError(f"Contradictor claim {contradictor_id} not found")
        if contradicted_id not in self._claims:
            raise KeyError(f"Contradicted claim {contradicted_id} not found")
        self._contradicts.setdefault(contradictor_id, []).append(contradicted_id)
        self._claims[contradicted_id].status = ClaimStatus.CONTRADICTED

    def retract(self, claim_id: str) -> None:
        """Retract a claim, marking it and downstream dependents."""
        if claim_id not in self._claims:
            raise KeyError(f"Claim {claim_id} not found")
        self._claims[claim_id].status = ClaimStatus.RETRACTED

    def get_chain(self, claim_id: str) -> List[str]:
        """Get the chain of supporting claims (BFS from claim backwards through support edges)."""
        if claim_id not in self._claims:
            raise KeyError(f"Claim {claim_id} not found")
        chain: List[str] = []
        visited: set = set()
        queue = [claim_id]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            chain.append(current)
            # Find all claims that support this one
            for supporter, supported_list in self._supports.items():
                if current in supported_list and supporter not in visited:
                    queue.append(supporter)
        return chain

    def get_unsupported(self) -> List[Claim]:
        """Return all claims that have PROPOSED status (no supporting evidence)."""
        return [c for c in self._claims.values() if c.status == ClaimStatus.PROPOSED]

    @property
    def claims(self) -> Dict[str, Claim]:
        return dict(self._claims)
