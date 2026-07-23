"""Semantic Entropy Gauge — measures unresolved ambiguity in meaning representations."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import List

from ..semantics.meaning_ir import MeaningIR


class EntropyRecommendation(Enum):
    """Recommended action based on entropy level."""
    PROCEED = "proceed"
    CONTINUE_REASONING = "continue_reasoning"
    ASK_CLARIFICATION = "ask_clarification"


@dataclass
class EntropyResult:
    """Result of entropy computation."""
    entropy: float
    recommendation: EntropyRecommendation
    rationale: str


class SemanticEntropy:
    """Measures the unresolved ambiguity across multiple meaning interpretations.

    Low entropy = clear, unambiguous meaning
    High entropy = multiple conflicting interpretations
    """

    # Thresholds for recommendations
    PROCEED_THRESHOLD = 0.3
    REASONING_THRESHOLD = 0.7

    def compute(self, alternatives: List[MeaningIR]) -> float:
        """Compute semantic entropy across alternative interpretations.

        Returns a value between 0.0 (no ambiguity) and 1.0 (maximum ambiguity).

        The entropy is based on:
        1. Number of distinct semantic hashes (more = more ambiguous)
        2. Structural divergence between alternatives
        3. Predicate disagreements
        """
        if not alternatives:
            return 0.0

        if len(alternatives) == 1:
            # Single interpretation: check internal ambiguity
            return self._internal_entropy(alternatives[0])

        # Multiple alternatives: measure divergence
        hashes = [alt.semantic_hash() for alt in alternatives]
        unique_hashes = set(hashes)

        # Hash diversity component
        n = len(alternatives)
        k = len(unique_hashes)
        hash_entropy = (k - 1) / max(n - 1, 1) if n > 1 else 0.0

        # Structural divergence component
        struct_entropy = self._structural_divergence(alternatives)

        # Predicate conflict component
        pred_entropy = self._predicate_conflicts(alternatives)

        # Weighted combination
        entropy = 0.4 * hash_entropy + 0.35 * struct_entropy + 0.25 * pred_entropy
        return min(1.0, max(0.0, entropy))

    def recommend(self, alternatives: List[MeaningIR]) -> EntropyResult:
        """Compute entropy and return a recommendation."""
        entropy = self.compute(alternatives)

        if entropy <= self.PROCEED_THRESHOLD:
            return EntropyResult(
                entropy=entropy,
                recommendation=EntropyRecommendation.PROCEED,
                rationale="Low ambiguity — safe to proceed with primary interpretation.",
            )
        elif entropy <= self.REASONING_THRESHOLD:
            return EntropyResult(
                entropy=entropy,
                recommendation=EntropyRecommendation.CONTINUE_REASONING,
                rationale="Moderate ambiguity — additional reasoning may resolve it.",
            )
        else:
            return EntropyResult(
                entropy=entropy,
                recommendation=EntropyRecommendation.ASK_CLARIFICATION,
                rationale="High ambiguity — clarification needed from user.",
            )

    def _internal_entropy(self, ir: MeaningIR) -> float:
        """Measure ambiguity within a single IR (from its alternatives field)."""
        if not ir.ambiguity_alternatives:
            return 0.0

        # The more alternatives, the more ambiguous
        n_alts = len(ir.ambiguity_alternatives)
        return min(1.0, math.log2(n_alts + 1) / 3.0)

    def _structural_divergence(self, alternatives: List[MeaningIR]) -> float:
        """Measure structural differences between alternatives."""
        if len(alternatives) < 2:
            return 0.0

        # Compare entity counts, predicate counts, etc.
        entity_counts = [len(a.entities) for a in alternatives]
        pred_counts = [len(a.predicates) for a in alternatives]
        qty_counts = [len(a.quantities) for a in alternatives]

        def _variance(values: List[int]) -> float:
            if not values:
                return 0.0
            mean = sum(values) / len(values)
            if mean == 0:
                return 0.0
            var = sum((v - mean) ** 2 for v in values) / len(values)
            # Normalize by mean to get coefficient of variation
            return min(1.0, math.sqrt(var) / max(mean, 1))

        e_var = _variance(entity_counts)
        p_var = _variance(pred_counts)
        q_var = _variance(qty_counts)

        return (e_var + p_var + q_var) / 3.0

    def _predicate_conflicts(self, alternatives: List[MeaningIR]) -> float:
        """Detect contradictory predicates across alternatives."""
        if len(alternatives) < 2:
            return 0.0

        # Collect all predicate keys and their negation status
        all_pred_keys: dict = {}
        for alt in alternatives:
            for pred in alt.predicates:
                key = (pred.subject, pred.relation, pred.object)
                if key not in all_pred_keys:
                    all_pred_keys[key] = set()
                all_pred_keys[key].add(pred.negated)

        # Count conflicts (same predicate both negated and not negated)
        conflicts = sum(1 for negs in all_pred_keys.values() if len(negs) > 1)
        total = len(all_pred_keys) if all_pred_keys else 1

        return min(1.0, conflicts / total)
