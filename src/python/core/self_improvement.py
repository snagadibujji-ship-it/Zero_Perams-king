"""
AXIMA Self Improvement — Evidence-based cognitive optimization.

Evaluate performance, identify bottlenecks, generate proposals,
run experiments, adopt successes, reject failures.
Every improvement must be evidence-based.
"""

import time
from typing import Optional, List, Dict, Any
from core.reality_graph import get_reality_graph, RealityGraph
from core.self_assessment import get_self_assessment
from core.autonomy_governance import get_governance


class SelfImprovement:
    """Evidence-based cognitive self-improvement."""

    def __init__(self, graph: Optional[RealityGraph] = None):
        self._graph = graph or get_reality_graph()
        self._assessment = get_self_assessment(self._graph)
        self._governance = get_governance(self._graph)
        self._proposals: List[Dict[str, Any]] = []
        self._experiments: List[Dict[str, Any]] = []

    def identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify cognitive performance bottlenecks."""
        metrics = self._assessment.assess()
        bottlenecks = []
        
        thresholds = {
            "prediction_accuracy": 0.5,
            "planning_success": 0.4,
            "hypothesis_success_rate": 0.3,
            "graph_health": 0.5,
            "reasoning_confidence": 0.5,
        }
        for metric, threshold in thresholds.items():
            value = metrics.get(metric, 1.0)
            if value < threshold:
                bottlenecks.append({
                    "metric": metric, "value": round(value, 3),
                    "threshold": threshold,
                    "severity": round((threshold - value) / threshold, 2),
                })
        bottlenecks.sort(key=lambda b: -b["severity"])
        return bottlenecks

    def generate_proposal(self, bottleneck: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an improvement proposal for a bottleneck."""
        metric = bottleneck["metric"]
        proposals_map = {
            "prediction_accuracy": "Increase evidence requirements before forming beliefs",
            "planning_success": "Prioritize goals with higher confidence tasks",
            "hypothesis_success_rate": "Require stronger evidence before hypothesis generation",
            "graph_health": "Run knowledge maintenance more frequently",
            "reasoning_confidence": "Consolidate weak knowledge or archive low-value nodes",
        }
        proposal = {
            "target_metric": metric,
            "action": proposals_map.get(metric, "Investigate root cause"),
            "expected_improvement": 0.1,
            "confidence": 0.5,
            "status": "proposed",
            "created_at": time.time(),
        }
        self._proposals.append(proposal)
        return proposal

    def run_improvement_cycle(self) -> Dict[str, Any]:
        """Full cycle: identify → propose → (future: experiment → adopt/reject)."""
        bottlenecks = self.identify_bottlenecks()
        proposals = []
        for b in bottlenecks[:3]:
            if self._governance.can_commit(0.5, 1):
                p = self.generate_proposal(b)
                proposals.append(p)
        return {"bottlenecks": len(bottlenecks), "proposals": len(proposals), "details": proposals}

    def stats(self) -> Dict[str, Any]:
        return {"proposals": len(self._proposals), "experiments": len(self._experiments)}


_improvement: Optional[SelfImprovement] = None
def get_self_improvement(graph: Optional[RealityGraph] = None) -> SelfImprovement:
    global _improvement
    if _improvement is None:
        _improvement = SelfImprovement(graph=graph)
    return _improvement
