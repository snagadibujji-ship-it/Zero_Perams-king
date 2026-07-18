"""
AXIMA Experiment Engine — Evaluate hypotheses with safe experiments.

Supported types: graph_reasoning, historical_replay, prediction_comparison,
consistency_analysis, controlled_simulation.

Each experiment records: hypothesis, evidence_examined, outcome, confidence_update, lesson.
No permanent knowledge changes without evidence.
"""

import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from core.reality_graph import get_reality_graph, RealityGraph
from core.cognitive_state import get_state
from core.hypothesis_generation import Hypothesis


@dataclass
class ExperimentResult:
    """Result of running an experiment."""
    hypothesis_id: str
    experiment_type: str
    outcome: str = "inconclusive"   # confirmed, refuted, inconclusive
    evidence_examined: List[str] = field(default_factory=list)
    confidence_delta: float = 0.0   # How much to adjust hypothesis confidence
    lesson: str = ""
    duration_ms: float = 0.0
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()


class ExperimentEngine:
    """Evaluates hypotheses through safe, reversible experiments."""

    def __init__(self, graph: Optional[RealityGraph] = None):
        self._graph = graph or get_reality_graph()
        self._results: List[ExperimentResult] = []

    def run_experiment(self, hypothesis: Hypothesis) -> ExperimentResult:
        """Run the most appropriate experiment for a hypothesis."""
        start = time.time()

        if hypothesis.hypothesis_type == "relationship":
            result = self._experiment_graph_reasoning(hypothesis)
        elif hypothesis.hypothesis_type == "cause":
            result = self._experiment_consistency_analysis(hypothesis)
        elif hypothesis.hypothesis_type == "overgeneralization":
            result = self._experiment_prediction_comparison(hypothesis)
        elif hypothesis.hypothesis_type == "conflict":
            result = self._experiment_consistency_analysis(hypothesis)
        else:
            result = self._experiment_graph_reasoning(hypothesis)

        result.duration_ms = (time.time() - start) * 1000
        self._results.append(result)
        return result

    def _experiment_graph_reasoning(self, h: Hypothesis) -> ExperimentResult:
        """Test by examining graph structure for supporting evidence."""
        evidence = []
        support_count = 0
        contra_count = 0

        for nid in h.source_nodes:
            neighbors = self._graph.neighbors(nid, direction="both")
            for neighbor_id, rel, _ in neighbors:
                n = self._graph.get_node(neighbor_id)
                if n:
                    evidence.append(neighbor_id)
                    if rel == "supports":
                        support_count += 1
                    elif rel == "contradicts":
                        contra_count += 1

        if support_count > contra_count and support_count >= 2:
            outcome = "confirmed"
            delta = 0.2
            lesson = f"Graph evidence supports hypothesis ({support_count} supporting, {contra_count} contradicting)"
        elif contra_count > support_count:
            outcome = "refuted"
            delta = -0.2
            lesson = f"Graph evidence contradicts hypothesis ({contra_count} contradicting)"
        else:
            outcome = "inconclusive"
            delta = 0.0
            lesson = "Insufficient graph evidence"

        return ExperimentResult(
            hypothesis_id=h.id,
            experiment_type="graph_reasoning",
            outcome=outcome,
            evidence_examined=evidence[:10],
            confidence_delta=delta,
            lesson=lesson,
        )

    def _experiment_consistency_analysis(self, h: Hypothesis) -> ExperimentResult:
        """Test by checking consistency of related facts."""
        evidence = []
        consistent = 0
        inconsistent = 0

        for nid in h.source_nodes:
            node = self._graph.get_node(nid)
            if not node:
                continue
            state = get_state(self._graph, nid)
            evidence.append(nid)

            if state.confidence > 0.6:
                consistent += 1
            elif state.entropy > 0.6:
                inconsistent += 1

            # Check if neighbors agree
            for neighbor_id, rel, _ in self._graph.neighbors(nid, relation="supports"):
                n_state = get_state(self._graph, neighbor_id)
                if n_state.confidence > 0.5:
                    consistent += 1
                evidence.append(neighbor_id)

        if consistent > inconsistent + 1:
            return ExperimentResult(
                hypothesis_id=h.id, experiment_type="consistency_analysis",
                outcome="confirmed", evidence_examined=evidence[:10],
                confidence_delta=0.15, lesson=f"Consistent evidence ({consistent} vs {inconsistent})"
            )
        elif inconsistent > consistent:
            return ExperimentResult(
                hypothesis_id=h.id, experiment_type="consistency_analysis",
                outcome="refuted", evidence_examined=evidence[:10],
                confidence_delta=-0.15, lesson=f"Inconsistent evidence ({inconsistent} vs {consistent})"
            )
        return ExperimentResult(
            hypothesis_id=h.id, experiment_type="consistency_analysis",
            outcome="inconclusive", evidence_examined=evidence[:10],
            confidence_delta=0.0, lesson="Mixed evidence — inconclusive"
        )

    def _experiment_prediction_comparison(self, h: Hypothesis) -> ExperimentResult:
        """Test by comparing prediction accuracies of related nodes."""
        evidence = []
        accuracies = []

        for nid in h.source_nodes:
            state = get_state(self._graph, nid)
            if state.usage_count > 0:
                accuracies.append(state.prediction_accuracy)
                evidence.append(nid)

        if not accuracies:
            return ExperimentResult(
                hypothesis_id=h.id, experiment_type="prediction_comparison",
                outcome="inconclusive", lesson="No prediction data available"
            )

        avg_acc = sum(accuracies) / len(accuracies)
        if avg_acc < 0.4:
            return ExperimentResult(
                hypothesis_id=h.id, experiment_type="prediction_comparison",
                outcome="confirmed", evidence_examined=evidence,
                confidence_delta=0.2, lesson=f"Low prediction accuracy ({avg_acc:.0%}) supports hypothesis"
            )
        return ExperimentResult(
            hypothesis_id=h.id, experiment_type="prediction_comparison",
            outcome="refuted", evidence_examined=evidence,
            confidence_delta=-0.1, lesson=f"Prediction accuracy ({avg_acc:.0%}) doesn't support hypothesis"
        )

    def stats(self) -> Dict[str, Any]:
        """Experiment statistics."""
        if not self._results:
            return {"total": 0}
        outcomes = {}
        for r in self._results:
            outcomes[r.outcome] = outcomes.get(r.outcome, 0) + 1
        return {"total": len(self._results), "outcomes": outcomes}


_engine: Optional[ExperimentEngine] = None
def get_experiment_engine(graph: Optional[RealityGraph] = None) -> ExperimentEngine:
    global _engine
    if _engine is None:
        _engine = ExperimentEngine(graph=graph)
    return _engine
