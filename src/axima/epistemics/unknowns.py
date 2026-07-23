"""Unknown Boundary Mapper — maps what is known, derivable, and unknown."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from .contracts import EpistemicContract, AnswerKind, EvidenceRequirement


@dataclass
class UnknownBoundary:
    """Maps the boundary between known and unknown for a given query.

    Attributes:
        known_claims: Facts directly available in evidence.
        derivable_claims: Claims that can be inferred from known facts.
        assumptions: Claims assumed but not verified.
        unresolved: Questions that cannot be answered from available evidence.
        missing_evidence: Specific evidence that would resolve unknowns.
        cheapest_next_observation: The lowest-cost action to expand knowledge.
    """
    known_claims: List[str] = field(default_factory=list)
    derivable_claims: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    unresolved: List[str] = field(default_factory=list)
    missing_evidence: List[str] = field(default_factory=list)
    cheapest_next_observation: Optional[str] = None


class BoundaryMapper:
    """Maps the epistemic boundary for a query given a contract and evidence.

    Determines what can be answered directly, what requires inference,
    what assumptions are being made, and what cannot be answered.
    """

    def map(
        self,
        contract: EpistemicContract,
        available_evidence: List[Any],
    ) -> UnknownBoundary:
        """Map the unknown boundary for a contract given available evidence.

        Args:
            contract: The epistemic contract specifying answer requirements.
            available_evidence: List of evidence items (strings, dicts, or objects
                with a 'claim' attribute).

        Returns:
            UnknownBoundary describing what is known and unknown.
        """
        known_claims: List[str] = []
        derivable_claims: List[str] = []
        assumptions: List[str] = []
        unresolved: List[str] = []
        missing_evidence: List[str] = []

        # Extract claim strings from evidence
        evidence_claims = self._extract_claims(available_evidence)

        # Classify based on evidence level
        if not evidence_claims:
            # No evidence at all
            unresolved.append(f"No evidence available for {contract.answer_kind.value} query")
            missing_evidence.append("Any relevant factual evidence")
        else:
            # Classify each piece of evidence
            for claim in evidence_claims:
                known_claims.append(claim)

        # Determine what's derivable based on allowed inference types
        if "deduction" in contract.allowed_inference_types and known_claims:
            derivable_claims.append(
                f"Deductive conclusions from {len(known_claims)} known facts "
                f"(max {contract.maximum_hops} hops)"
            )

        if "induction" in contract.allowed_inference_types and known_claims:
            derivable_claims.append("Inductive generalizations from known patterns")
            assumptions.append("Inductive reasoning assumes pattern continues")

        if "analogy" in contract.allowed_inference_types:
            derivable_claims.append("Analogical inferences from similar cases")
            assumptions.append("Analogical reasoning assumes structural similarity")

        if "abduction" in contract.allowed_inference_types:
            derivable_claims.append("Abductive explanations (best guess)")
            assumptions.append("Abductive reasoning may select wrong explanation")

        # Check evidence sufficiency against contract requirements
        sufficiency_gaps = self._check_sufficiency(contract, evidence_claims)
        missing_evidence.extend(sufficiency_gaps)
        if sufficiency_gaps:
            unresolved.append(
                f"Contract requires {contract.required_evidence.value} evidence; "
                f"gaps remain"
            )

        # Determine cheapest next observation
        cheapest = self._find_cheapest_observation(contract, missing_evidence)

        return UnknownBoundary(
            known_claims=known_claims,
            derivable_claims=derivable_claims,
            assumptions=assumptions,
            unresolved=unresolved,
            missing_evidence=missing_evidence,
            cheapest_next_observation=cheapest,
        )

    def _extract_claims(self, evidence: List[Any]) -> List[str]:
        """Extract string claims from various evidence formats."""
        claims: List[str] = []
        for item in evidence:
            if isinstance(item, str):
                claims.append(item)
            elif isinstance(item, dict):
                if "claim" in item:
                    claims.append(str(item["claim"]))
                elif "fact" in item:
                    claims.append(str(item["fact"]))
                else:
                    claims.append(str(item))
            elif hasattr(item, "claim"):
                claims.append(str(item.claim))
            else:
                claims.append(str(item))
        return claims

    def _check_sufficiency(
        self,
        contract: EpistemicContract,
        claims: List[str],
    ) -> List[str]:
        """Check if available evidence meets contract requirements."""
        gaps: List[str] = []

        if contract.required_evidence == EvidenceRequirement.PROVEN:
            if not claims:
                gaps.append("Formal proof required but no proof steps available")
            else:
                gaps.append("Proof verification: each step needs validation")

        elif contract.required_evidence == EvidenceRequirement.SOURCED:
            if not claims:
                gaps.append("Sourced evidence required but none available")

        elif contract.required_evidence == EvidenceRequirement.WITNESSED:
            gaps.append("Witnessed evidence required (direct observation)")

        if contract.freshness_requirement:
            gaps.append(f"Freshness check needed: data must be within {contract.freshness_requirement}")

        if contract.unit_requirement:
            gaps.append(f"Unit conversion/verification needed: result in {contract.unit_requirement}")

        return gaps

    def _find_cheapest_observation(
        self,
        contract: EpistemicContract,
        missing: List[str],
    ) -> Optional[str]:
        """Determine the lowest-cost action to expand knowledge."""
        if not missing:
            return None

        # Heuristic: prioritize by cost
        cost_priorities = {
            "lookup": 1,
            "calculation": 2,
            "deduction": 3,
            "pattern_matching": 2,
            "induction": 4,
            "analogy": 4,
            "abduction": 5,
            "generation": 3,
        }

        cheapest_inference = min(
            contract.allowed_inference_types,
            key=lambda t: cost_priorities.get(t, 10),
            default=None,
        )

        if cheapest_inference:
            return f"Apply {cheapest_inference} to available evidence"

        return "Gather additional evidence from knowledge base"
