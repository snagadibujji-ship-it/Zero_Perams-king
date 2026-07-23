"""Contradiction detection and resolution court."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional


class Resolution(Enum):
    """Possible outcomes of contradiction resolution."""
    PENDING = "pending"
    A_WINS = "a_wins"
    B_WINS = "b_wins"
    CONTEXT_DEPENDENT = "context_dependent"
    UNRESOLVED = "unresolved"


@dataclass
class ContradictionCase:
    """A case filed when two claims contradict each other."""
    id: str
    claim_a: str
    claim_b: str
    evidence_for_a: List[str] = field(default_factory=list)
    evidence_for_b: List[str] = field(default_factory=list)
    resolution: Resolution = Resolution.PENDING
    reasoning: str = ""
    filed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None


class ContradictionCourt:
    """Adjudicates contradictions between claims.

    Domain rules determine burden of proof:
    - Higher source tier wins by default
    - More independent evidence wins
    - More recent valid_time wins for temporal conflicts
    """

    def __init__(self) -> None:
        self._cases: Dict[str, ContradictionCase] = {}

    def file_case(self, claim_a: str, claim_b: str) -> ContradictionCase:
        """File a new contradiction case between two claims."""
        case = ContradictionCase(
            id=str(uuid.uuid4()),
            claim_a=claim_a,
            claim_b=claim_b,
        )
        self._cases[case.id] = case
        return case

    def present_evidence(
        self, case_id: str, evidence_id: str, supports_claim: str
    ) -> None:
        """Present evidence for one side of the contradiction."""
        if case_id not in self._cases:
            raise KeyError(f"Case {case_id} not found")
        case = self._cases[case_id]
        if supports_claim == case.claim_a:
            case.evidence_for_a.append(evidence_id)
        elif supports_claim == case.claim_b:
            case.evidence_for_b.append(evidence_id)
        else:
            raise ValueError(
                f"Claim {supports_claim} is not part of case {case_id}"
            )

    def resolve(
        self, case_id: str, resolution: Resolution, reasoning: str = ""
    ) -> ContradictionCase:
        """Resolve a contradiction case."""
        if case_id not in self._cases:
            raise KeyError(f"Case {case_id} not found")
        case = self._cases[case_id]
        case.resolution = resolution
        case.reasoning = reasoning
        case.resolved_at = datetime.now(timezone.utc)
        return case

    def get_pending(self) -> List[ContradictionCase]:
        """Return all unresolved contradiction cases."""
        return [c for c in self._cases.values() if c.resolution == Resolution.PENDING]

    def get_case(self, case_id: str) -> Optional[ContradictionCase]:
        """Get a case by ID."""
        return self._cases.get(case_id)

    @property
    def all_cases(self) -> List[ContradictionCase]:
        return list(self._cases.values())
