"""
ACES Adaptive Teaching
======================

Adaptive explanation system that builds teaching plans based on a learner model.
Tracks known concepts, misconceptions, and prerequisites.
Uses verified claims and derivations — never invents content.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set


@dataclass
class LearnerModel:
    """Represents the current state of a learner's understanding.

    Attributes:
        known_concepts: Concepts the learner has demonstrated understanding of.
        misconceptions: Known misconceptions (concept -> incorrect belief).
        preferred_examples: Types of examples that resonate (e.g., 'visual', 'code').
        learning_style: Preferred style (e.g., 'deductive', 'inductive', 'analogical').
        completed_prerequisites: Prerequisites already satisfied.
    """

    known_concepts: Set[str] = field(default_factory=set)
    misconceptions: Dict[str, str] = field(default_factory=dict)
    preferred_examples: List[str] = field(default_factory=list)
    learning_style: str = "deductive"
    completed_prerequisites: Set[str] = field(default_factory=set)

    def knows(self, concept: str) -> bool:
        """Check if the learner knows a concept."""
        return concept in self.known_concepts

    def has_misconception(self, concept: str) -> bool:
        """Check if the learner has a misconception about a concept."""
        return concept in self.misconceptions

    def mark_learned(self, concept: str) -> None:
        """Mark a concept as learned."""
        self.known_concepts.add(concept)
        self.completed_prerequisites.add(concept)

    def add_misconception(self, concept: str, belief: str) -> None:
        """Record a misconception."""
        self.misconceptions[concept] = belief

    def clear_misconception(self, concept: str) -> None:
        """Clear a misconception once corrected."""
        self.misconceptions.pop(concept, None)


@dataclass
class TeachingPlan:
    """A plan for explaining a concept to a learner.

    Attributes:
        target_concept: The concept to teach.
        bridge_from: Known concepts to bridge from.
        explanation_depth: How deep the explanation should go (1-5).
        examples: Concrete examples to use.
        transfer_tasks: Tasks to verify transfer of understanding.
    """

    target_concept: str
    bridge_from: List[str] = field(default_factory=list)
    explanation_depth: int = 2
    examples: List[str] = field(default_factory=list)
    transfer_tasks: List[str] = field(default_factory=list)
    prerequisite_chain: List[str] = field(default_factory=list)
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# Knowledge graph for prerequisite tracking
# ---------------------------------------------------------------------------

@dataclass
class ConceptNode:
    """A concept in the knowledge graph."""

    name: str
    prerequisites: List[str] = field(default_factory=list)
    related: List[str] = field(default_factory=list)
    explanations: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    transfer_tasks: List[str] = field(default_factory=list)
    difficulty: int = 1  # 1-5


class AdaptiveTeacher:
    """Generates adaptive teaching plans based on learner state.

    Uses a concept graph for prerequisite tracking and generates
    explanations that bridge from known to unknown concepts.

    All explanations are based on verified claims — the teacher
    never invents content that isn't grounded in the concept graph.
    """

    def __init__(self) -> None:
        self._concepts: Dict[str, ConceptNode] = {}
        self._learner: Optional[LearnerModel] = None

    def set_learner(self, learner: LearnerModel) -> None:
        """Set the current learner model."""
        self._learner = learner

    def register_concept(self, node: ConceptNode) -> None:
        """Register a concept in the knowledge graph."""
        self._concepts[node.name] = node

    def register_concepts(self, nodes: List[ConceptNode]) -> None:
        """Register multiple concepts."""
        for node in nodes:
            self._concepts[node.name] = node

    def get_concept(self, name: str) -> Optional[ConceptNode]:
        """Retrieve a concept by name."""
        return self._concepts.get(name)

    def plan_explanation(
        self,
        target_concept: str,
        learner: Optional[LearnerModel] = None,
    ) -> TeachingPlan:
        """Create a teaching plan for a target concept.

        Determines:
        1. What prerequisites are missing
        2. What known concepts can serve as bridges
        3. What depth is appropriate for the learner
        4. What examples match the learner's style

        Args:
            target_concept: The concept to explain.
            learner: Optional learner model (uses self._learner if None).

        Returns:
            A TeachingPlan with bridge concepts, depth, examples, and tasks.
        """
        learner = learner or self._learner or LearnerModel()
        concept = self._concepts.get(target_concept)

        # Find bridge concepts (known concepts related to target)
        bridges: List[str] = []
        if concept:
            for prereq in concept.prerequisites:
                if learner.knows(prereq):
                    bridges.append(prereq)
            for rel in concept.related:
                if learner.knows(rel):
                    bridges.append(rel)

        # Determine prerequisite chain (what needs to be taught first)
        prereq_chain = self._compute_prerequisite_chain(target_concept, learner)

        # Select depth based on learning style and concept difficulty
        depth = self._select_depth(target_concept, learner)

        # Select examples matching learner preference
        examples = self._select_examples(target_concept, learner)

        # Generate transfer tasks
        tasks = self._select_transfer_tasks(target_concept, learner)

        return TeachingPlan(
            target_concept=target_concept,
            bridge_from=bridges,
            explanation_depth=depth,
            examples=examples,
            transfer_tasks=tasks,
            prerequisite_chain=prereq_chain,
        )

    def expand_depth(self, plan: TeachingPlan, levels: int = 1) -> TeachingPlan:
        """Increase explanation depth of an existing plan.

        Used when the learner signals they need more detail.

        Args:
            plan: Existing teaching plan.
            levels: How many depth levels to add.

        Returns:
            Updated TeachingPlan with increased depth.
        """
        new_depth = min(plan.explanation_depth + levels, 5)

        # Add more detailed examples at deeper depth
        concept = self._concepts.get(plan.target_concept)
        additional_examples: List[str] = []
        if concept and len(concept.examples) > len(plan.examples):
            additional_examples = concept.examples[len(plan.examples):]

        return TeachingPlan(
            target_concept=plan.target_concept,
            bridge_from=plan.bridge_from,
            explanation_depth=new_depth,
            examples=plan.examples + additional_examples,
            transfer_tasks=plan.transfer_tasks,
            prerequisite_chain=plan.prerequisite_chain,
            plan_id=plan.plan_id,
        )

    def change_anchors(
        self,
        plan: TeachingPlan,
        new_bridges: List[str],
    ) -> TeachingPlan:
        """Change the bridge concepts in a plan.

        Used when current analogies aren't working for the learner.

        Args:
            plan: Existing teaching plan.
            new_bridges: New concepts to bridge from.

        Returns:
            Updated TeachingPlan with new bridges.
        """
        return TeachingPlan(
            target_concept=plan.target_concept,
            bridge_from=new_bridges,
            explanation_depth=plan.explanation_depth,
            examples=plan.examples,
            transfer_tasks=plan.transfer_tasks,
            prerequisite_chain=plan.prerequisite_chain,
            plan_id=plan.plan_id,
        )

    def check_transfer(
        self,
        target_concept: str,
        learner_response: str,
        learner: Optional[LearnerModel] = None,
    ) -> Dict[str, Any]:
        """Check if the learner demonstrates understanding transfer.

        Evaluates a learner's response against known correct patterns
        for the target concept.

        Args:
            target_concept: Concept being checked.
            learner_response: The learner's answer or explanation.
            learner: Optional learner model.

        Returns:
            Dict with 'passed', 'feedback', and 'misconceptions_detected'.
        """
        learner = learner or self._learner or LearnerModel()
        concept = self._concepts.get(target_concept)

        result: Dict[str, Any] = {
            "passed": False,
            "feedback": "",
            "misconceptions_detected": [],
            "confidence": 0.0,
        }

        if concept is None:
            result["feedback"] = f"Unknown concept: {target_concept}"
            return result

        # Check if response mentions key terms from the concept
        response_lower = learner_response.lower()
        concept_terms = set()
        concept_terms.add(target_concept.lower())
        for prereq in concept.prerequisites:
            concept_terms.add(prereq.lower())
        for rel in concept.related:
            concept_terms.add(rel.lower())

        terms_found = sum(1 for t in concept_terms if t in response_lower)
        coverage = terms_found / max(len(concept_terms), 1)

        # Check for known misconceptions
        misconceptions: List[str] = []
        for mc_concept, mc_belief in learner.misconceptions.items():
            if mc_belief.lower() in response_lower:
                misconceptions.append(f"Misconception about {mc_concept}: {mc_belief}")

        result["misconceptions_detected"] = misconceptions
        result["confidence"] = coverage

        if misconceptions:
            result["passed"] = False
            result["feedback"] = (
                f"Some misconceptions detected: {'; '.join(misconceptions)}. "
                f"Let's revisit the foundations."
            )
        elif coverage >= 0.5:
            result["passed"] = True
            result["feedback"] = "Good understanding demonstrated."
            learner.mark_learned(target_concept)
        else:
            result["passed"] = False
            result["feedback"] = (
                f"Response covers {coverage:.0%} of expected concepts. "
                f"Consider reviewing: {', '.join(concept_terms - {t for t in concept_terms if t in response_lower})}"
            )

        return result

    # ------------------------------------------------------------------
    # Internal methods
    # ------------------------------------------------------------------

    def _compute_prerequisite_chain(
        self,
        target: str,
        learner: LearnerModel,
    ) -> List[str]:
        """Compute ordered list of prerequisites that need to be taught first."""
        chain: List[str] = []
        visited: Set[str] = set()

        def _dfs(concept_name: str) -> None:
            if concept_name in visited:
                return
            visited.add(concept_name)

            concept = self._concepts.get(concept_name)
            if concept is None:
                return

            for prereq in concept.prerequisites:
                if not learner.knows(prereq):
                    _dfs(prereq)

            # Only add if not already known and not the final target
            if not learner.knows(concept_name) and concept_name != target:
                chain.append(concept_name)

        concept = self._concepts.get(target)
        if concept:
            for prereq in concept.prerequisites:
                if not learner.knows(prereq):
                    _dfs(prereq)

        return chain

    def _select_depth(self, target: str, learner: LearnerModel) -> int:
        """Select explanation depth based on learner and concept."""
        concept = self._concepts.get(target)
        base_depth = 2

        if concept:
            base_depth = min(concept.difficulty, 5)

        # Reduce depth for experienced learners
        if len(learner.known_concepts) > 10:
            base_depth = max(base_depth - 1, 1)

        # Increase depth if learner has misconceptions about this topic
        if learner.has_misconception(target):
            base_depth = min(base_depth + 1, 5)

        return base_depth

    def _select_examples(self, target: str, learner: LearnerModel) -> List[str]:
        """Select examples matching learner preferences."""
        concept = self._concepts.get(target)
        if concept is None:
            return []

        examples = list(concept.examples)

        # Filter by preferred example types if specified
        if learner.preferred_examples:
            preferred = [
                ex for ex in examples
                if any(pref.lower() in ex.lower() for pref in learner.preferred_examples)
            ]
            if preferred:
                return preferred[:3]

        return examples[:3]

    def _select_transfer_tasks(self, target: str, learner: LearnerModel) -> List[str]:
        """Select transfer tasks appropriate for the learner."""
        concept = self._concepts.get(target)
        if concept is None:
            return [f"Explain {target} in your own words"]

        tasks = list(concept.transfer_tasks)
        if not tasks:
            tasks = [
                f"Explain {target} in your own words",
                f"Give an example of {target}",
                f"How does {target} relate to {concept.prerequisites[0] if concept.prerequisites else 'what you already know'}?",
            ]

        return tasks[:3]
