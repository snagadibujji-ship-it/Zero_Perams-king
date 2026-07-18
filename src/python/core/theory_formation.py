"""
AXIMA Theory Formation — Competing explanations pipeline.

Pipeline: Observation → Question → Hypothesis A/B/C → Evidence → Selection →
Prediction → Validation → Revision.
Never assume first explanation is correct. Maintain multiple simultaneous theories.
"""

import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from core.reality_graph import get_reality_graph, RealityGraph
from core.belief_system import get_belief_system
from core.experiment_engine import get_experiment_engine
from core.hypothesis_generation import Hypothesis


@dataclass
class Theory:
    """A competing explanation for an observed phenomenon."""
    id: str = ""
    question: str = ""
    explanation: str = ""
    confidence: float = 0.3
    evidence_for: List[str] = field(default_factory=list)
    evidence_against: List[str] = field(default_factory=list)
    predictions: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "candidate"  # candidate, leading, rejected, validated


class TheoryFormation:
    """Maintains competing theories for observed phenomena."""

    def __init__(self, graph: Optional[RealityGraph] = None):
        self._graph = graph or get_reality_graph()
        self._beliefs = get_belief_system(self._graph)
        self._experiments = get_experiment_engine(self._graph)
        self._active_competitions: Dict[str, List[str]] = {}  # question → [theory_ids]

    def pose_question(self, question: str, candidate_explanations: List[str]) -> Dict[str, Any]:
        """Create competing theories for a question."""
        theory_ids = []
        for explanation in candidate_explanations:
            tid = self._beliefs.add_belief(
                statement=explanation, confidence=0.3,
                domain="theory_formation",
            )
            self._graph.update_node(tid, properties={
                "theory_question": question,
                "theory_status": "candidate",
            })
            theory_ids.append(tid)
        self._active_competitions[question] = theory_ids
        return {"question": question, "theories": len(theory_ids), "ids": theory_ids}

    def add_evidence(self, question: str, evidence_id: str, supports_theory_id: str):
        """Add evidence supporting one theory in a competition."""
        self._beliefs.add_evidence(supports_theory_id, evidence_id, supporting=True)
        # Weaken competing theories slightly
        for tid in self._active_competitions.get(question, []):
            if tid != supports_theory_id:
                node = self._graph.get_node(tid)
                if node:
                    conf = node.properties.get("confidence", 0.5)
                    self._beliefs.revise_confidence(tid, max(0.05, conf - 0.02), "Competing theory gained evidence")

    def evaluate_theories(self, question: str) -> Optional[Dict[str, Any]]:
        """Evaluate which theory is currently leading."""
        theory_ids = self._active_competitions.get(question, [])
        if not theory_ids:
            return None
        scored = []
        for tid in theory_ids:
            belief = self._beliefs.get_belief(tid)
            if belief:
                scored.append({"id": tid, "statement": belief.statement, "confidence": belief.confidence})
        scored.sort(key=lambda t: -t["confidence"])
        if scored:
            # Mark leading theory
            self._graph.update_node(scored[0]["id"], properties={"theory_status": "leading"})
        return {"question": question, "theories": scored, "leading": scored[0] if scored else None}

    def validate_leading(self, question: str) -> Dict[str, Any]:
        """Promote leading theory to validated if confidence > 0.7."""
        result = self.evaluate_theories(question)
        if not result or not result["leading"]:
            return {"status": "no_leading_theory"}
        leading = result["leading"]
        if leading["confidence"] > 0.7:
            self._graph.update_node(leading["id"], properties={"theory_status": "validated"})
            return {"status": "validated", "theory": leading["statement"]}
        return {"status": "insufficient_confidence", "confidence": leading["confidence"]}


_theory: Optional[TheoryFormation] = None
def get_theory_formation(graph: Optional[RealityGraph] = None) -> TheoryFormation:
    global _theory
    if _theory is None:
        _theory = TheoryFormation(graph=graph)
    return _theory
