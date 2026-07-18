"""
AXIMA Hypothesis Generation — Candidate explanations for observed gaps.

Generates hypotheses about: possible relationships, hidden causes,
missing concepts, overgeneralized principles, conflicting evidence.

Hypotheses are temporary and require validation. Every hypothesis preserves provenance.
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from core.reality_graph import get_reality_graph, RealityGraph
from core.cognitive_state import get_state


@dataclass
class Hypothesis:
    """A candidate explanation requiring validation."""
    id: str = ""
    statement: str = ""
    hypothesis_type: str = ""  # relationship, cause, missing_concept, overgeneralization, conflict
    source_nodes: List[str] = field(default_factory=list)  # What provoked this hypothesis
    confidence: float = 0.3         # Prior confidence (low — unvalidated)
    evidence_for: List[str] = field(default_factory=list)
    evidence_against: List[str] = field(default_factory=list)
    status: str = "pending"         # pending, testing, validated, rejected, inconclusive
    created_at: float = 0.0

    def __post_init__(self):
        if not self.id:
            self.id = f"H_{uuid.uuid4().hex[:8]}"
        if not self.created_at:
            self.created_at = time.time()


class HypothesisGenerator:
    """Generates candidate explanations for observed gaps."""

    def __init__(self, graph: Optional[RealityGraph] = None):
        self._graph = graph or get_reality_graph()

    def generate(self, max_hypotheses: int = 5) -> List[Hypothesis]:
        """Generate hypotheses from current graph state."""
        hypotheses = []
        hypotheses.extend(self._hypothesize_relationships())
        hypotheses.extend(self._hypothesize_causes())
        hypotheses.extend(self._hypothesize_overgeneralizations())
        hypotheses.sort(key=lambda h: -h.confidence)
        return hypotheses[:max_hypotheses]

    def generate_for_node(self, node_id: str) -> List[Hypothesis]:
        """Generate hypotheses about a specific node."""
        node = self._graph.get_node(node_id)
        if not node:
            return []
        hypotheses = []
        state = get_state(self._graph, node_id)

        # If low confidence — hypothesize why
        if state.confidence < 0.4:
            hypotheses.append(Hypothesis(
                statement=f"'{node.label}' may lack supporting evidence",
                hypothesis_type="missing_concept",
                source_nodes=[node_id],
                confidence=0.4,
            ))

        # If contradictions — hypothesize resolution
        neighbors = self._graph.neighbors(node_id, direction="both")
        contradictions = [(nid, r) for nid, r, _ in neighbors if r == "contradicts"]
        for contra_id, _ in contradictions:
            contra = self._graph.get_node(contra_id)
            if contra:
                hypotheses.append(Hypothesis(
                    statement=f"Contradiction may be due to different contexts: '{node.label}' vs '{contra.label}'",
                    hypothesis_type="conflict",
                    source_nodes=[node_id, contra_id],
                    confidence=0.35,
                ))

        return hypotheses

    def _hypothesize_relationships(self) -> List[Hypothesis]:
        """Hypothesize hidden relationships between disconnected nodes."""
        hypotheses = []
        concepts = self._graph.find_nodes(node_type="concept")
        isolated = [c for c in concepts if len(self._graph.neighbors(c.id, direction="both")) == 0]
        for c in isolated[:3]:
            hypotheses.append(Hypothesis(
                statement=f"'{c.label}' may relate to active goals",
                hypothesis_type="relationship",
                source_nodes=[c.id],
                confidence=0.3,
            ))
        return hypotheses

    def _hypothesize_causes(self) -> List[Hypothesis]:
        """Hypothesize causes for prediction failures."""
        hypotheses = []
        for node_type in ["theory"]:
            nodes = self._graph.find_nodes(node_type=node_type)
            for n in nodes:
                acc = n.properties.get("_cs_prediction_accuracy", 0.5)
                if acc < 0.35 and n.properties.get("_cs_usage_count", 0) > 2:
                    hypotheses.append(Hypothesis(
                        statement=f"'{n.label}' may have hidden preconditions not captured",
                        hypothesis_type="cause",
                        source_nodes=[n.id],
                        confidence=0.4,
                    ))
        return hypotheses[:3]

    def _hypothesize_overgeneralizations(self) -> List[Hypothesis]:
        """Hypothesize principles that may be overgeneralized."""
        hypotheses = []
        theories = self._graph.find_nodes(node_type="theory")
        for t in theories:
            if t.properties.get("level") != "principle":
                continue
            contradictions = len([n for n, r, _ in self._graph.neighbors(t.id, direction="in") if r == "contradicts"])
            if contradictions > 0:
                hypotheses.append(Hypothesis(
                    statement=f"Principle '{t.label}' may be overgeneralized — has {contradictions} exception(s)",
                    hypothesis_type="overgeneralization",
                    source_nodes=[t.id],
                    confidence=0.5,
                ))
        return hypotheses[:2]


_gen: Optional[HypothesisGenerator] = None
def get_hypothesis_generator(graph: Optional[RealityGraph] = None) -> HypothesisGenerator:
    global _gen
    if _gen is None:
        _gen = HypothesisGenerator(graph=graph)
    return _gen
