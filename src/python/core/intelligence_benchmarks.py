"""
AXIMA Intelligence Benchmarks — Measurable intelligence tests.

Evaluates: learning_speed, retention, belief_accuracy, prediction_accuracy,
concept_quality, transfer_learning, theory_accuracy, reasoning_efficiency,
self_improvement_success, simulation_accuracy.

Benchmarks run continuously. Tracks improvement over time.
"""

import time
from typing import Optional, List, Dict, Any
from core.reality_graph import get_reality_graph, RealityGraph
from core.cognitive_state import get_state
from core.belief_system import get_belief_system
from core.self_metrics import get_self_metrics


class IntelligenceBenchmarks:
    """Measurable intelligence tests for AXIMA."""

    def __init__(self, graph: Optional[RealityGraph] = None):
        self._graph = graph or get_reality_graph()
        self._beliefs = get_belief_system(self._graph)
        self._metrics = get_self_metrics(self._graph)
        self._history: List[Dict[str, float]] = []

    def run_all(self) -> Dict[str, float]:
        """Run all intelligence benchmarks. Returns scores (0-1)."""
        scores = {
            "learning_speed": self._benchmark_learning_speed(),
            "knowledge_retention": self._benchmark_retention(),
            "belief_accuracy": self._benchmark_belief_accuracy(),
            "prediction_accuracy": self._benchmark_prediction_accuracy(),
            "concept_quality": self._benchmark_concept_quality(),
            "transfer_learning": self._benchmark_transfer(),
            "theory_accuracy": self._benchmark_theory_accuracy(),
            "reasoning_efficiency": self._benchmark_reasoning_efficiency(),
            "self_improvement": self._benchmark_self_improvement(),
            "simulation_accuracy": self._benchmark_simulation(),
        }
        scores["composite"] = sum(scores.values()) / len(scores)
        scores["timestamp"] = time.time()
        self._history.append(scores)
        if len(self._history) > 100:
            self._history = self._history[-100:]
        return {k: round(v, 3) for k, v in scores.items()}

    def improvement_over_time(self) -> Dict[str, Any]:
        """Track how scores have changed."""
        if len(self._history) < 2:
            return {"status": "insufficient_data"}
        first = self._history[0]
        latest = self._history[-1]
        changes = {}
        for key in first:
            if key == "timestamp":
                continue
            changes[key] = round(latest.get(key, 0) - first.get(key, 0), 3)
        return {
            "measurements": len(self._history),
            "timespan_hours": (latest["timestamp"] - first["timestamp"]) / 3600,
            "changes": changes,
            "improving": sum(1 for v in changes.values() if v > 0) > sum(1 for v in changes.values() if v < 0),
        }

    def _benchmark_learning_speed(self) -> float:
        """How quickly does new knowledge get integrated?"""
        facts = self._graph.find_nodes(node_type="fact")
        if not facts:
            return 0.0
        # Measure: facts with high confidence relative to age
        fast_learners = 0
        for f in facts:
            state = get_state(self._graph, f.id)
            age_hours = state.age / 3600
            if age_hours < 24 and state.confidence > 0.6:
                fast_learners += 1
        return min(1.0, fast_learners / max(1, len(facts)) * 5)

    def _benchmark_retention(self) -> float:
        """Does knowledge stay accessible over time?"""
        facts = self._graph.find_nodes(node_type="fact")
        if not facts:
            return 0.0
        active = sum(1 for f in facts if f.properties.get("_cs_activation", 0) > 0.05)
        return active / max(1, len(facts))

    def _benchmark_belief_accuracy(self) -> float:
        """Are beliefs well-calibrated?"""
        beliefs = self._beliefs.all_beliefs()
        if not beliefs:
            return 0.5
        # Beliefs with predictions: how accurate?
        with_preds = [b for b in beliefs if b.prediction_history]
        if not with_preds:
            return 0.5
        return sum(b.prediction_accuracy for b in with_preds) / len(with_preds)

    def _benchmark_prediction_accuracy(self) -> float:
        """Overall prediction accuracy from metrics."""
        metrics = self._metrics.compute_all()
        return metrics.get("prediction_accuracy", 0.5)

    def _benchmark_concept_quality(self) -> float:
        """How useful are formed concepts? (connected, used)"""
        concepts = self._graph.find_nodes(node_type="concept")
        if not concepts:
            return 0.0
        useful = 0
        for c in concepts:
            connections = len(self._graph.neighbors(c.id, direction="both"))
            usage = c.properties.get("_cs_usage_count", 0)
            if connections >= 2 or usage >= 2:
                useful += 1
        return useful / max(1, len(concepts))

    def _benchmark_transfer(self) -> float:
        """How successful is knowledge transfer?"""
        theories = self._graph.find_nodes(node_type="theory")
        transfers = [t for t in theories if t.properties.get("status") == "transferred"]
        validated = [t for t in transfers if t.properties.get("validated")]
        if not transfers:
            return 0.5  # No transfers attempted
        return len(validated) / max(1, len(transfers))

    def _benchmark_theory_accuracy(self) -> float:
        """How often are theories validated?"""
        theories = self._graph.find_nodes(node_type="theory")
        with_status = [t for t in theories if t.properties.get("theory_status")]
        if not with_status:
            return 0.5
        validated = sum(1 for t in with_status if t.properties.get("theory_status") == "validated")
        return validated / max(1, len(with_status))

    def _benchmark_reasoning_efficiency(self) -> float:
        """How efficient is reasoning? (results per energy spent)"""
        all_nodes = []
        for t in ["fact", "concept", "theory"]:
            all_nodes.extend(self._graph.find_nodes(node_type=t))
        if not all_nodes:
            return 0.0
        # Efficiency = confidence gained per energy spent
        efficiencies = []
        for n in all_nodes:
            state = get_state(self._graph, n.id)
            if state.energy > 0:
                efficiencies.append(state.confidence / max(0.01, state.energy))
        if not efficiencies:
            return 0.5
        avg = sum(efficiencies) / len(efficiencies)
        return min(1.0, avg / 2.0)  # Normalize

    def _benchmark_self_improvement(self) -> float:
        """Is the system getting better over time?"""
        if len(self._history) < 3:
            return 0.5
        recent = self._history[-3:]
        older = self._history[:3]
        recent_avg = sum(h.get("composite", 0) for h in recent) / len(recent)
        older_avg = sum(h.get("composite", 0) for h in older) / len(older)
        if recent_avg > older_avg:
            return min(1.0, 0.5 + (recent_avg - older_avg) * 5)
        return max(0.0, 0.5 - (older_avg - recent_avg) * 5)

    def _benchmark_simulation(self) -> float:
        """Placeholder: simulation accuracy (needs real predictions to measure)."""
        return 0.5  # Neutral until we have simulation prediction data


_benchmarks: Optional[IntelligenceBenchmarks] = None
def get_benchmarks(graph: Optional[RealityGraph] = None) -> IntelligenceBenchmarks:
    global _benchmarks
    if _benchmarks is None:
        _benchmarks = IntelligenceBenchmarks(graph=graph)
    return _benchmarks
