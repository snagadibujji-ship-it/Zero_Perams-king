"""
AXIMA Meta Cognition — Reason about own reasoning.

Why was I wrong? Why was confidence inaccurate? Which strategy worked?
Which failed? Which cognitive law should change?
Generate internal explanations. Self-awareness without anthropomorphism.
"""

import time
from typing import Optional, List, Dict, Any
from core.reality_graph import get_reality_graph, RealityGraph
from core.cognitive_state import get_state
from core.belief_system import get_belief_system
from core.self_metrics import get_self_metrics


class MetaCognition:
    """Reasons about AXIMA's own reasoning processes."""

    def __init__(self, graph: Optional[RealityGraph] = None):
        self._graph = graph or get_reality_graph()
        self._beliefs = get_belief_system(self._graph)
        self._metrics = get_self_metrics(self._graph)
        self._insights: List[Dict[str, Any]] = []

    def why_was_i_wrong(self, belief_id: str) -> Dict[str, Any]:
        """Analyze why a belief turned out incorrect."""
        belief = self._beliefs.get_belief(belief_id)
        if not belief:
            return {"error": "Belief not found"}
        
        reasons = []
        # Check evidence quality
        if len(belief.supporting_evidence) < 2:
            reasons.append("Insufficient supporting evidence")
        if belief.is_contested:
            reasons.append("Had contradicting evidence but didn't weigh it enough")
        # Check prediction history
        if belief.prediction_accuracy < 0.4:
            reasons.append(f"Prediction accuracy was low ({belief.prediction_accuracy:.0%})")
        # Check dependencies
        for dep_id in belief.dependencies:
            dep = self._beliefs.get_belief(dep_id)
            if dep and dep.confidence < 0.4:
                reasons.append(f"Depended on weak belief: '{dep.statement[:40]}'")

        insight = {
            "belief": belief.statement[:60],
            "confidence_was": belief.confidence,
            "reasons_wrong": reasons or ["No clear explanation — may need more data"],
            "recommendation": self._recommend_fix(reasons),
        }
        self._insights.append(insight)
        return insight

    def confidence_calibration(self) -> Dict[str, Any]:
        """Analyze how well-calibrated AXIMA's confidence scores are."""
        beliefs = self._beliefs.all_beliefs()
        if not beliefs:
            return {"calibration": "no_data"}

        # Group by confidence bucket and check prediction accuracy
        buckets = {"high": [], "medium": [], "low": []}
        for b in beliefs:
            if b.prediction_history:
                actual_acc = b.prediction_accuracy
                if b.confidence > 0.7:
                    buckets["high"].append(actual_acc)
                elif b.confidence > 0.4:
                    buckets["medium"].append(actual_acc)
                else:
                    buckets["low"].append(actual_acc)

        result = {}
        for bucket, accs in buckets.items():
            if accs:
                result[bucket] = {
                    "count": len(accs),
                    "avg_accuracy": round(sum(accs) / len(accs), 3),
                    "calibrated": bucket == "high" and sum(accs)/len(accs) > 0.6,
                }
        return result

    def strategy_analysis(self) -> Dict[str, Any]:
        """Which cognitive strategies have been working?"""
        # Analyze nodes by source/method
        facts = self._graph.find_nodes(node_type="fact")
        by_source = {}
        for f in facts:
            source = f.properties.get("source", "unknown")
            conf = f.properties.get("_cs_confidence", 0.5)
            by_source.setdefault(source, []).append(conf)

        strategies = {}
        for source, confs in by_source.items():
            strategies[source] = {
                "count": len(confs),
                "avg_confidence": round(sum(confs) / len(confs), 3),
                "effective": sum(confs) / len(confs) > 0.5,
            }
        return {"strategies": strategies}

    def suggest_cognitive_changes(self) -> List[str]:
        """Suggest changes to cognitive parameters based on performance."""
        suggestions = []
        metrics = self._metrics.compute_all()

        if metrics.get("prediction_accuracy", 1) < 0.5:
            suggestions.append("Increase min_confidence_to_commit threshold")
        if metrics.get("contradiction_rate", 0) > 0.2:
            suggestions.append("Run contradiction resolution more frequently")
        if metrics.get("learning_velocity", 0) < 0.01:
            suggestions.append("Lower novelty decay rate to retain new knowledge longer")
        if metrics.get("goal_completion_rate", 0) < 0.3:
            suggestions.append("Reduce goal complexity or increase task decomposition")

        return suggestions

    def _recommend_fix(self, reasons: List[str]) -> str:
        if "Insufficient supporting evidence" in reasons:
            return "Require more evidence before forming strong beliefs"
        if any("contradicting" in r for r in reasons):
            return "Weight contradicting evidence more heavily"
        if any("weak belief" in r for r in reasons):
            return "Validate dependency beliefs before building on them"
        return "Gather more data and re-evaluate"

    def stats(self) -> Dict[str, Any]:
        return {"total_insights": len(self._insights)}


_meta_cog: Optional[MetaCognition] = None
def get_meta_cognition(graph: Optional[RealityGraph] = None) -> MetaCognition:
    global _meta_cog
    if _meta_cog is None:
        _meta_cog = MetaCognition(graph=graph)
    return _meta_cog
