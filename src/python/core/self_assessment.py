"""
AXIMA Self-Assessment — Evaluate cognitive performance continuously.

Extends SelfMetrics with hypothesis success rate, reflection effectiveness,
principle stability, and graph health. Uses metrics to improve prioritization.
"""

import time
from typing import Optional, Dict, Any, List
from core.reality_graph import get_reality_graph, RealityGraph
from core.self_metrics import get_self_metrics, SelfMetrics
from core.cognitive_state import get_state


class SelfAssessment:
    """Continuous cognitive performance evaluation."""

    def __init__(self, graph: Optional[RealityGraph] = None):
        self._graph = graph or get_reality_graph()
        self._base_metrics = get_self_metrics(self._graph)
        self._assessments: List[Dict[str, Any]] = []

    def assess(self) -> Dict[str, Any]:
        """Full self-assessment combining all metrics."""
        base = self._base_metrics.compute_all()
        extended = {
            **base,
            "hypothesis_success_rate": self._hypothesis_success_rate(),
            "principle_stability": self._principle_stability(),
            "graph_health": self._graph_health(),
            "autonomy_efficiency": self._autonomy_efficiency(),
        }
        self._assessments.append({**extended, "time": time.time()})
        if len(self._assessments) > 50:
            self._assessments = self._assessments[-50:]
        return extended

    def improvement_areas(self) -> List[str]:
        """Identify areas needing improvement."""
        if not self._assessments:
            self.assess()
        latest = self._assessments[-1]
        areas = []
        if latest.get("prediction_accuracy", 1) < 0.5:
            areas.append("prediction_accuracy: Below 50% — recalibrate models")
        if latest.get("contradiction_rate", 0) > 0.2:
            areas.append("contradiction_rate: High — resolve conflicts")
        if latest.get("graph_health", 1) < 0.5:
            areas.append("graph_health: Poor — run maintenance")
        if latest.get("hypothesis_success_rate", 1) < 0.3:
            areas.append("hypothesis_success_rate: Low — improve generation")
        return areas

    def _hypothesis_success_rate(self) -> float:
        memories = self._graph.find_nodes(node_type="memory")
        rejections = sum(1 for m in memories if m.properties.get("memory_type") == "rejection")
        discoveries = self._graph.find_nodes(node_type="fact")
        pipeline_discoveries = sum(1 for d in discoveries if d.properties.get("source") == "discovery_pipeline")
        total = rejections + pipeline_discoveries
        return pipeline_discoveries / max(1, total)

    def _principle_stability(self) -> float:
        theories = self._graph.find_nodes(node_type="theory")
        principles = [t for t in theories if t.properties.get("level") == "principle"
                     and t.properties.get("status") not in ("retired", "merged")]
        if not principles:
            return 1.0
        stabilities = [get_state(self._graph, p.id).stability for p in principles]
        return sum(stabilities) / len(stabilities)

    def _graph_health(self) -> float:
        """Composite graph health metric."""
        stats = self._graph.stats()
        nodes = stats.get("nodes", 0)
        edges = stats.get("edges", 0)
        if nodes == 0:
            return 0.0
        # Healthy graph: edges/nodes ratio between 1-3
        ratio = edges / max(1, nodes)
        health = min(1.0, ratio / 2.0)
        # Penalize for archived/retired nodes
        all_nodes = []
        for t in ["fact", "concept", "theory", "memory"]:
            all_nodes.extend(self._graph.find_nodes(node_type=t))
        archived = sum(1 for n in all_nodes if n.properties.get("status") in ("archived", "retired"))
        if all_nodes:
            health *= (1.0 - archived / len(all_nodes) * 0.5)
        return health

    def _autonomy_efficiency(self) -> float:
        """How efficiently is autonomous work improving the system?"""
        discoveries = self._graph.find_nodes(node_type="fact")
        auto_discoveries = [d for d in discoveries if d.properties.get("source") == "discovery_pipeline"]
        if not auto_discoveries:
            return 0.0
        # Measure confidence of autonomous discoveries
        confs = [d.properties.get("confidence", 0.5) for d in auto_discoveries]
        return sum(confs) / len(confs)


_assessment: Optional[SelfAssessment] = None
def get_self_assessment(graph: Optional[RealityGraph] = None) -> SelfAssessment:
    global _assessment
    if _assessment is None:
        _assessment = SelfAssessment(graph=graph)
    return _assessment
