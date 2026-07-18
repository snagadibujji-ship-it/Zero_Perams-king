"""
AXIMA Belief System — Persistent belief network.

A belief is NOT a fact. A fact is observed. A belief is held.
Beliefs evolve continuously. Confidence is never static.

Each belief: statement, confidence, supporting_evidence, contradicting_evidence,
originating_observations, dependencies, prediction_history, revision_history.
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from core.reality_graph import get_reality_graph, RealityGraph


@dataclass
class BeliefRevision:
    """A single revision event in a belief's history."""
    timestamp: float = 0.0
    old_confidence: float = 0.0
    new_confidence: float = 0.0
    reason: str = ""
    evidence_id: str = ""


@dataclass 
class Belief:
    """A belief held by AXIMA. Not a fact — an interpretation."""
    id: str = ""
    statement: str = ""
    confidence: float = 0.5
    domain: str = ""
    
    # Evidence
    supporting_evidence: List[str] = field(default_factory=list)   # Node IDs
    contradicting_evidence: List[str] = field(default_factory=list)
    originating_observations: List[str] = field(default_factory=list)
    
    # Dependencies (beliefs this depends on)
    dependencies: List[str] = field(default_factory=list)
    
    # History
    prediction_history: List[Dict[str, Any]] = field(default_factory=list)  # [{predicted, actual, correct}]
    revision_history: List[BeliefRevision] = field(default_factory=list)
    
    # Metadata
    created_at: float = 0.0
    updated_at: float = 0.0
    status: str = "active"  # active, suspended, retired

    def __post_init__(self):
        if not self.id:
            self.id = f"B_{uuid.uuid4().hex[:8]}"
        if not self.created_at:
            self.created_at = time.time()

    @property
    def evidence_ratio(self) -> float:
        """Ratio of supporting to total evidence."""
        total = len(self.supporting_evidence) + len(self.contradicting_evidence)
        return len(self.supporting_evidence) / max(1, total)

    @property
    def prediction_accuracy(self) -> float:
        """How accurate predictions based on this belief have been."""
        if not self.prediction_history:
            return 0.5
        correct = sum(1 for p in self.prediction_history if p.get("correct"))
        return correct / len(self.prediction_history)

    @property
    def is_well_supported(self) -> bool:
        return len(self.supporting_evidence) >= 3 and self.confidence > 0.6

    @property
    def is_contested(self) -> bool:
        return len(self.contradicting_evidence) > 0 and self.evidence_ratio < 0.7


class BeliefSystem:
    """Persistent belief network stored in Reality Graph."""

    def __init__(self, graph: Optional[RealityGraph] = None):
        self._graph = graph or get_reality_graph()

    def add_belief(self, statement: str, confidence: float = 0.5,
                   domain: str = "", evidence: Optional[List[str]] = None,
                   observations: Optional[List[str]] = None) -> str:
        """Create a new belief. Returns belief node ID."""
        belief = Belief(
            statement=statement, confidence=confidence, domain=domain,
            supporting_evidence=evidence or [],
            originating_observations=observations or [],
        )
        nid = self._graph.add_node("theory", statement[:80], {
            "belief_type": "belief",
            "confidence": confidence,
            "domain": domain,
            "supporting_evidence": belief.supporting_evidence,
            "contradicting_evidence": [],
            "originating_observations": belief.originating_observations,
            "dependencies": [],
            "prediction_history": [],
            "revision_history": [],
            "status": "active",
            "belief_id": belief.id,
            "_cs_confidence": confidence,
            "_cs_novelty": 0.8,
            "_cs_activation": 0.5,
        })
        # Link evidence
        for eid in (evidence or []):
            self._graph.add_edge(eid, nid, "supports")
        self._graph.save()
        return nid

    def get_belief(self, node_id: str) -> Optional[Belief]:
        """Reconstruct a Belief from graph node."""
        node = self._graph.get_node(node_id)
        if not node or node.properties.get("belief_type") != "belief":
            return None
        return Belief(
            id=node.properties.get("belief_id", node_id),
            statement=node.label,
            confidence=node.properties.get("confidence", 0.5),
            domain=node.properties.get("domain", ""),
            supporting_evidence=node.properties.get("supporting_evidence", []),
            contradicting_evidence=node.properties.get("contradicting_evidence", []),
            originating_observations=node.properties.get("originating_observations", []),
            dependencies=node.properties.get("dependencies", []),
            prediction_history=node.properties.get("prediction_history", []),
            revision_history=[],
            created_at=node.created_at,
            updated_at=node.updated_at,
            status=node.properties.get("status", "active"),
        )

    def all_beliefs(self, domain: Optional[str] = None) -> List[Belief]:
        """Get all active beliefs, optionally filtered by domain."""
        theories = self._graph.find_nodes(node_type="theory")
        beliefs = []
        for t in theories:
            if t.properties.get("belief_type") != "belief":
                continue
            if t.properties.get("status") != "active":
                continue
            if domain and t.properties.get("domain") != domain:
                continue
            b = self.get_belief(t.id)
            if b:
                beliefs.append(b)
        return beliefs

    def add_evidence(self, belief_id: str, evidence_id: str, supporting: bool = True):
        """Add evidence to a belief."""
        node = self._graph.get_node(belief_id)
        if not node:
            return
        key = "supporting_evidence" if supporting else "contradicting_evidence"
        evidence_list = node.properties.get(key, [])
        if evidence_id not in evidence_list:
            evidence_list.append(evidence_id)
            self._graph.update_node(belief_id, properties={key: evidence_list})
            rel = "supports" if supporting else "contradicts"
            self._graph.add_edge(evidence_id, belief_id, rel)
            self._graph.save()

    def record_prediction(self, belief_id: str, predicted: Any, actual: Any, correct: bool):
        """Record a prediction made based on this belief."""
        node = self._graph.get_node(belief_id)
        if not node:
            return
        history = node.properties.get("prediction_history", [])
        history.append({"predicted": str(predicted)[:50], "actual": str(actual)[:50],
                       "correct": correct, "time": time.time()})
        if len(history) > 50:
            history = history[-50:]
        self._graph.update_node(belief_id, properties={"prediction_history": history})

    def revise_confidence(self, belief_id: str, new_confidence: float, reason: str = ""):
        """Revise a belief's confidence (records history)."""
        node = self._graph.get_node(belief_id)
        if not node:
            return
        old_conf = node.properties.get("confidence", 0.5)
        revision = {"old": old_conf, "new": new_confidence, "reason": reason, "time": time.time()}
        rev_history = node.properties.get("revision_history", [])
        rev_history.append(revision)
        if len(rev_history) > 30:
            rev_history = rev_history[-30:]
        self._graph.update_node(belief_id, properties={
            "confidence": new_confidence,
            "_cs_confidence": new_confidence,
            "revision_history": rev_history,
        })
        self._graph.save()

    def dependent_beliefs(self, belief_id: str) -> List[str]:
        """Get beliefs that depend on this one."""
        dependents = []
        neighbors = self._graph.neighbors(belief_id, direction="in")
        for nid, rel, _ in neighbors:
            n = self._graph.get_node(nid)
            if n and n.properties.get("belief_type") == "belief" and rel == "depends_on":
                dependents.append(nid)
        return dependents

    def stats(self) -> Dict[str, Any]:
        beliefs = self.all_beliefs()
        return {
            "total_beliefs": len(beliefs),
            "avg_confidence": sum(b.confidence for b in beliefs) / max(1, len(beliefs)),
            "contested": sum(1 for b in beliefs if b.is_contested),
            "well_supported": sum(1 for b in beliefs if b.is_well_supported),
        }


_system: Optional[BeliefSystem] = None
def get_belief_system(graph: Optional[RealityGraph] = None) -> BeliefSystem:
    global _system
    if _system is None:
        _system = BeliefSystem(graph=graph)
    return _system
