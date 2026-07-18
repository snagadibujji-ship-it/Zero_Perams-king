"""
AXIMA Discovery Pipeline — Convert validated hypotheses into durable knowledge.

Lifecycle: Observation → Hypothesis → Experiment → Evidence → Decision →
           Reality Graph Update → Principle Evolution → Reflection

Every knowledge update remains traceable.
"""

import time
from typing import Optional, List, Dict, Any

from core.reality_graph import get_reality_graph, RealityGraph
from core.cognitive_state import get_state, set_state, initialize_state
from core.hypothesis_generation import Hypothesis, get_hypothesis_generator
from core.experiment_engine import ExperimentResult, get_experiment_engine
from core.cognitive_physics import get_physics


class DiscoveryPipeline:
    """Converts validated hypotheses into durable knowledge."""

    def __init__(self, graph: Optional[RealityGraph] = None):
        self._graph = graph or get_reality_graph()
        self._hypothesis_gen = get_hypothesis_generator(self._graph)
        self._experiments = get_experiment_engine(self._graph)
        self._physics = get_physics(self._graph)
        self._discoveries: List[Dict[str, Any]] = []

    def discover_step(self, max_hypotheses: int = 3) -> Dict[str, Any]:
        """One step of the discovery pipeline.
        
        1. Generate hypotheses
        2. Run experiments
        3. Commit confirmed findings
        4. Record reflections
        """
        result = {"hypotheses": 0, "experiments": 0, "discoveries": 0, "rejections": 0}

        # Generate
        hypotheses = self._hypothesis_gen.generate(max_hypotheses=max_hypotheses)
        result["hypotheses"] = len(hypotheses)

        # Experiment + Commit
        for h in hypotheses:
            exp_result = self._experiments.run_experiment(h)
            result["experiments"] += 1

            if exp_result.outcome == "confirmed" and exp_result.confidence_delta > 0.1:
                self._commit_discovery(h, exp_result)
                result["discoveries"] += 1
            elif exp_result.outcome == "refuted":
                self._record_rejection(h, exp_result)
                result["rejections"] += 1

        return result

    def _commit_discovery(self, hypothesis: Hypothesis, evidence: ExperimentResult):
        """Commit a validated hypothesis as new knowledge."""
        # Create fact node for the discovery
        nid = self._graph.add_node("fact", hypothesis.statement[:80], {
            "source": "discovery_pipeline",
            "hypothesis_id": hypothesis.id,
            "experiment_type": evidence.experiment_type,
            "confidence": min(0.7, hypothesis.confidence + evidence.confidence_delta),
            "lesson": evidence.lesson,
            "discovered_at": time.time(),
        })
        initialize_state(self._graph, nid, activation=0.5, confidence=0.6, novelty=0.8)

        # Link to source nodes
        for src in hypothesis.source_nodes:
            self._graph.add_edge(nid, src, "derived_from")

        # Activate physics on new node
        self._physics.mark_new(nid)

        self._discoveries.append({
            "node_id": nid,
            "statement": hypothesis.statement,
            "evidence": evidence.lesson,
            "time": time.time(),
        })
        self._graph.save()

    def _record_rejection(self, hypothesis: Hypothesis, evidence: ExperimentResult):
        """Record that a hypothesis was rejected (without creating knowledge)."""
        # Store as memory/lesson
        self._graph.add_node("memory", f"Rejected: {hypothesis.statement[:60]}", {
            "memory_type": "rejection",
            "hypothesis_type": hypothesis.hypothesis_type,
            "reason": evidence.lesson,
            "created_at": time.time(),
        })

    def stats(self) -> Dict[str, Any]:
        return {
            "total_discoveries": len(self._discoveries),
            "experiment_stats": self._experiments.stats(),
        }


_pipeline: Optional[DiscoveryPipeline] = None
def get_discovery_pipeline(graph: Optional[RealityGraph] = None) -> DiscoveryPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = DiscoveryPipeline(graph=graph)
    return _pipeline
