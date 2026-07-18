"""
AXIMA Belief Revision Engine — Bayesian-style evidence-driven updating.

Supports: Bayesian confidence updates, contradiction handling, uncertainty
propagation, confidence decay, evidence weighting, source reliability.

Old beliefs are never deleted — they become historical states.
The system explains why beliefs changed.
"""

import math
import time
from typing import Optional, List, Dict, Any

from core.reality_graph import get_reality_graph, RealityGraph
from core.belief_system import get_belief_system, BeliefSystem, Belief
from core.cognitive_state import get_state, set_state


class BeliefRevisionEngine:
    """Bayesian-style belief updating with full traceability."""

    def __init__(self, graph: Optional[RealityGraph] = None):
        self._graph = graph or get_reality_graph()
        self._beliefs = get_belief_system(self._graph)
        self._source_reliability: Dict[str, float] = {}  # source → reliability (0-1)

    def update_on_evidence(self, belief_id: str, evidence_id: str,
                           supports: bool = True, strength: float = 0.5,
                           source: str = "") -> Dict[str, Any]:
        """Update belief confidence based on new evidence (Bayesian-style).
        
        Returns explanation of what changed and why.
        """
        belief = self._beliefs.get_belief(belief_id)
        if not belief:
            return {"error": "Belief not found"}

        # Source reliability weighting
        reliability = self._source_reliability.get(source, 0.7) if source else 0.7
        effective_strength = strength * reliability

        # Bayesian-style update
        prior = belief.confidence
        if supports:
            # P(H|E) = P(E|H) * P(H) / P(E)
            # Simplified: shift toward 1.0 proportional to strength
            likelihood = 0.5 + effective_strength * 0.4
            posterior = prior * likelihood / (prior * likelihood + (1 - prior) * (1 - likelihood))
        else:
            # Evidence against: shift toward 0.0
            likelihood = 0.5 - effective_strength * 0.4
            posterior = prior * likelihood / (prior * likelihood + (1 - prior) * (1 - likelihood))

        # Clamp
        posterior = max(0.01, min(0.99, posterior))

        # Apply revision
        reason = f"{'Supporting' if supports else 'Contradicting'} evidence (strength={strength:.2f}, source_reliability={reliability:.2f})"
        self._beliefs.revise_confidence(belief_id, posterior, reason)
        self._beliefs.add_evidence(belief_id, evidence_id, supporting=supports)

        # Propagate to dependent beliefs
        propagation = self._propagate_uncertainty(belief_id, prior, posterior)

        return {
            "belief": belief.statement[:60],
            "prior": round(prior, 3),
            "posterior": round(posterior, 3),
            "delta": round(posterior - prior, 3),
            "reason": reason,
            "propagated_to": propagation,
        }

    def update_on_prediction_result(self, belief_id: str, correct: bool) -> Dict[str, Any]:
        """Update belief based on whether a prediction it generated was correct."""
        belief = self._beliefs.get_belief(belief_id)
        if not belief:
            return {"error": "Belief not found"}

        prior = belief.confidence
        # Correct prediction strengthens belief
        if correct:
            delta = 0.03 * (1 - prior)  # Diminishing returns
        else:
            delta = -0.05 * prior  # Failures hurt more

        posterior = max(0.01, min(0.99, prior + delta))
        self._beliefs.revise_confidence(belief_id, posterior,
                                        f"Prediction {'correct' if correct else 'incorrect'}")
        self._beliefs.record_prediction(belief_id, "based_on_belief", "outcome", correct)

        return {"prior": round(prior, 3), "posterior": round(posterior, 3), "correct": correct}

    def resolve_contradiction(self, belief_a_id: str, belief_b_id: str) -> Dict[str, Any]:
        """Resolve contradiction between two beliefs. Stronger survives."""
        a = self._beliefs.get_belief(belief_a_id)
        b = self._beliefs.get_belief(belief_b_id)
        if not a or not b:
            return {"error": "Belief not found"}

        # Score by evidence ratio + prediction accuracy + confidence
        score_a = a.evidence_ratio * 0.4 + a.prediction_accuracy * 0.3 + a.confidence * 0.3
        score_b = b.evidence_ratio * 0.4 + b.prediction_accuracy * 0.3 + b.confidence * 0.3

        if score_a > score_b:
            winner_id, loser_id = belief_a_id, belief_b_id
            winner, loser = a, b
        else:
            winner_id, loser_id = belief_b_id, belief_a_id
            winner, loser = b, a

        # Boost winner, weaken loser
        self._beliefs.revise_confidence(winner_id, min(0.95, winner.confidence + 0.1),
                                        f"Won contradiction against '{loser.statement[:30]}'")
        self._beliefs.revise_confidence(loser_id, max(0.1, loser.confidence - 0.2),
                                        f"Lost contradiction against '{winner.statement[:30]}'")

        # Suspend loser if very weak
        loser_node = self._graph.get_node(loser_id)
        if loser_node and loser.confidence - 0.2 < 0.15:
            self._graph.update_node(loser_id, properties={"status": "suspended"})

        return {
            "winner": winner.statement[:50],
            "loser": loser.statement[:50],
            "scores": {"a": round(score_a, 3), "b": round(score_b, 3)},
        }

    def decay_all(self, rate: float = 0.005):
        """Apply small confidence decay to all beliefs (entropy increases)."""
        beliefs = self._beliefs.all_beliefs()
        for b_node in self._graph.find_nodes(node_type="theory"):
            if b_node.properties.get("belief_type") != "belief":
                continue
            if b_node.properties.get("status") != "active":
                continue
            conf = b_node.properties.get("confidence", 0.5)
            # Decay toward 0.5 (maximum uncertainty)
            new_conf = conf + (0.5 - conf) * rate
            self._graph.update_node(b_node.id, properties={"confidence": new_conf, "_cs_confidence": new_conf})

    def set_source_reliability(self, source: str, reliability: float):
        """Set how much to trust a particular evidence source."""
        self._source_reliability[source] = max(0.0, min(1.0, reliability))

    def _propagate_uncertainty(self, belief_id: str, old_conf: float, new_conf: float) -> int:
        """Propagate confidence changes to dependent beliefs."""
        dependents = self._beliefs.dependent_beliefs(belief_id)
        propagated = 0
        delta = new_conf - old_conf
        for dep_id in dependents:
            dep_node = self._graph.get_node(dep_id)
            if dep_node:
                dep_conf = dep_node.properties.get("confidence", 0.5)
                # Proportional propagation (30% of delta)
                new_dep_conf = max(0.01, min(0.99, dep_conf + delta * 0.3))
                self._beliefs.revise_confidence(dep_id, new_dep_conf,
                                                f"Propagated from dependency (delta={delta:.3f})")
                propagated += 1
        return propagated

    def explain_belief(self, belief_id: str) -> Dict[str, Any]:
        """Explain current state of a belief and why it has its confidence."""
        belief = self._beliefs.get_belief(belief_id)
        if not belief:
            return {"error": "Not found"}
        return {
            "statement": belief.statement,
            "confidence": belief.confidence,
            "evidence_ratio": round(belief.evidence_ratio, 2),
            "prediction_accuracy": round(belief.prediction_accuracy, 2),
            "supporting": len(belief.supporting_evidence),
            "contradicting": len(belief.contradicting_evidence),
            "revisions": len(belief.revision_history),
            "status": belief.status,
            "is_contested": belief.is_contested,
        }


_revision: Optional[BeliefRevisionEngine] = None
def get_belief_revision(graph: Optional[RealityGraph] = None) -> BeliefRevisionEngine:
    global _revision
    if _revision is None:
        _revision = BeliefRevisionEngine(graph=graph)
    return _revision
