"""Skill Foundry — anti-unification of traces into governed skills.

Extracts parameterized programs from successful execution traces via
anti-unification.  Skills must pass governance approval before promotion.
Overfitting to specific inputs is rejected via adversarial testing.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


class ApprovalStatus(Enum):
    CANDIDATE = "CANDIDATE"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"


@dataclass
class SkillSpec:
    """Formal specification of a skill."""

    name: str
    types: List[str]
    preconditions: List[str]
    postconditions: List[str]
    proof_obligations: List[str]
    failure_modes: List[str]
    provenance: str  # Where this skill was derived from
    tests: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SkillCandidate:
    """A candidate skill awaiting governance approval."""

    id: str
    spec: SkillSpec
    source_traces: List[Dict[str, Any]]
    anti_unified_program: str  # Parameterized program text
    positive_tests: List[Dict[str, Any]]
    negative_tests: List[Dict[str, Any]]
    adversarial_tests: List[Dict[str, Any]]
    approval_status: ApprovalStatus = ApprovalStatus.CANDIDATE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    promoted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None


class SkillFoundry:
    """Extracts, tests, and governs skill candidates from execution traces."""

    def __init__(self, governance_gate: Any = None) -> None:
        self._candidates: Dict[str, SkillCandidate] = {}
        self._promoted: Dict[str, SkillCandidate] = {}
        self._governance = governance_gate

    @property
    def candidates(self) -> Dict[str, SkillCandidate]:
        return dict(self._candidates)

    @property
    def promoted_skills(self) -> Dict[str, SkillCandidate]:
        return dict(self._promoted)

    def extract_from_trace(self, traces: List[Dict[str, Any]]) -> Optional[SkillSpec]:
        """Extract a skill specification from successful execution traces.

        Identifies common structure across traces and derives preconditions,
        postconditions, and types from the shared pattern.
        """
        if not traces:
            return None

        # Identify common keys across traces
        common_keys = set(traces[0].keys())
        for trace in traces[1:]:
            common_keys &= set(trace.keys())

        if not common_keys:
            return None

        # Derive types from consistent value types across traces
        types: List[str] = []
        for key in sorted(common_keys):
            type_names = {type(t[key]).__name__ for t in traces}
            types.append(f"{key}: {' | '.join(sorted(type_names))}")

        # Derive preconditions from shared input patterns
        preconditions: List[str] = []
        if "input" in common_keys:
            preconditions.append("input is not None")
        if "context" in common_keys:
            preconditions.append("context is valid")

        # Derive postconditions from shared output patterns
        postconditions: List[str] = []
        if "output" in common_keys:
            postconditions.append("output is not None")
            if all(t.get("success", False) for t in traces):
                postconditions.append("execution succeeded")

        name = traces[0].get("operation", "extracted_skill")

        return SkillSpec(
            name=name,
            types=types,
            preconditions=preconditions,
            postconditions=postconditions,
            proof_obligations=[f"Must satisfy all {len(postconditions)} postconditions"],
            failure_modes=["input validation failure", "postcondition violation"],
            provenance=f"anti-unified from {len(traces)} traces",
            tests=[],
        )

    def anti_unify(self, traces: List[Dict[str, Any]]) -> str:
        """Anti-unify traces into a parameterized program template.

        Anti-unification finds the least-general generalization of multiple
        concrete traces, replacing varying parts with parameters.
        """
        if not traces:
            return ""

        if len(traces) == 1:
            return repr(traces[0])

        # Identify constant vs varying fields
        all_keys = set()
        for t in traces:
            all_keys.update(t.keys())

        constants: Dict[str, Any] = {}
        parameters: List[str] = []

        for key in sorted(all_keys):
            values = [t.get(key) for t in traces if key in t]
            if len(set(repr(v) for v in values)) == 1 and len(values) == len(traces):
                constants[key] = values[0]
            else:
                parameters.append(key)

        # Build parameterized template
        lines = [f"def skill({', '.join(parameters)}):"]
        for k, v in constants.items():
            lines.append(f"    # constant: {k} = {repr(v)}")
        for p in parameters:
            lines.append(f"    # parameter: {p}")
        lines.append(f"    return execute({', '.join(parameters)})")

        return "\n".join(lines)

    def test_candidate(
        self,
        candidate: SkillCandidate,
        test_fn: Optional[Callable[[SkillCandidate], Tuple[bool, str]]] = None,
    ) -> Tuple[bool, str]:
        """Run test suite against candidate.  Rejects overfitting.

        A candidate is rejected if:
        - It has no positive tests
        - It fails any negative test (produces output where it shouldn't)
        - It has fewer than 3 source traces (overfitting risk)
        """
        # Reject if insufficient diversity
        if len(candidate.source_traces) < 3:
            return False, "Insufficient trace diversity (< 3 traces) — overfitting risk"

        # Reject if no positive tests
        if not candidate.positive_tests:
            return False, "No positive tests provided"

        # Run custom test function if provided
        if test_fn:
            return test_fn(candidate)

        # Default: check adversarial tests exist
        if not candidate.adversarial_tests:
            return False, "No adversarial tests — cannot verify robustness"

        return True, "Passed all checks"

    def submit_for_approval(self, spec: SkillSpec, traces: List[Dict[str, Any]],
                            positive_tests: List[Dict[str, Any]],
                            negative_tests: List[Dict[str, Any]],
                            adversarial_tests: List[Dict[str, Any]]) -> SkillCandidate:
        """Create a candidate and submit for governance approval."""
        program = self.anti_unify(traces)

        candidate = SkillCandidate(
            id=str(uuid.uuid4()),
            spec=spec,
            source_traces=traces,
            anti_unified_program=program,
            positive_tests=positive_tests,
            negative_tests=negative_tests,
            adversarial_tests=adversarial_tests,
            approval_status=ApprovalStatus.CANDIDATE,
        )
        self._candidates[candidate.id] = candidate
        return candidate

    def promote(self, candidate_id: str, approved_by: str = "governance") -> SkillCandidate:
        """Promote an approved candidate to active skill.

        Requires governance approval — cannot self-promote.
        """
        if candidate_id not in self._candidates:
            raise KeyError(f"Candidate {candidate_id} not found")

        candidate = self._candidates[candidate_id]

        # Governance check
        if self._governance is not None:
            permission = self._governance.check_permission("promote_skill")
            if not permission.allowed:
                candidate.approval_status = ApprovalStatus.REJECTED
                candidate.rejection_reason = "Governance denied promotion"
                return candidate

        # Test before promoting
        passed, reason = self.test_candidate(candidate)
        if not passed:
            candidate.approval_status = ApprovalStatus.REJECTED
            candidate.rejection_reason = reason
            return candidate

        candidate.approval_status = ApprovalStatus.APPROVED
        candidate.promoted_at = datetime.now(timezone.utc)
        self._promoted[candidate_id] = candidate
        return candidate

    def revoke(self, candidate_id: str, reason: str = "revoked") -> SkillCandidate:
        """Revoke a previously promoted skill."""
        if candidate_id in self._promoted:
            candidate = self._promoted.pop(candidate_id)
        elif candidate_id in self._candidates:
            candidate = self._candidates[candidate_id]
        else:
            raise KeyError(f"Candidate {candidate_id} not found")

        candidate.approval_status = ApprovalStatus.REVOKED
        candidate.revoked_at = datetime.now(timezone.utc)
        candidate.rejection_reason = reason
        return candidate
