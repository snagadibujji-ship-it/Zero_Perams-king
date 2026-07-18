"""
AXIMA Autonomous Goal Generation — Generate internal goals from evidence.

Sources: unresolved contradictions, prediction failures, low-confidence principles,
weakly connected concepts, unfinished reflections, stale knowledge, curiosity gaps.

Each goal includes: objective, rationale, expected_benefit, estimated_effort,
confidence, dependencies. Integrates with existing Goal System.
"""

import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from core.reality_graph import get_reality_graph, RealityGraph
from core.cognitive_state import get_state
from core.goal_system import get_goal_system


@dataclass
class AutonomousGoal:
    """An internally generated goal."""
    objective: str
    rationale: str
    source: str             # contradiction, prediction_failure, weak_principle, etc.
    expected_benefit: float = 0.5   # 0-1
    estimated_effort: int = 1       # Estimated ticks
    confidence: float = 0.5
    dependencies: List[str] = field(default_factory=list)
    related_nodes: List[str] = field(default_factory=list)


class AutonomousGoalGenerator:
    """Generates internal goals from evidence in the Reality Graph."""

    def __init__(self, graph: Optional[RealityGraph] = None):
        self._graph = graph or get_reality_graph()
        self._goal_system = get_goal_system(self._graph)

    def generate(self, max_goals: int = 5) -> List[AutonomousGoal]:
        """Generate autonomous goals from current graph state."""
        candidates = []
        candidates.extend(self._from_contradictions())
        candidates.extend(self._from_prediction_failures())
        candidates.extend(self._from_weak_principles())
        candidates.extend(self._from_disconnected_concepts())
        candidates.extend(self._from_stale_knowledge())

        # Sort by expected value (benefit * confidence / effort)
        candidates.sort(key=lambda g: -(g.expected_benefit * g.confidence / max(1, g.estimated_effort)))
        return candidates[:max_goals]

    def commit_goal(self, goal: AutonomousGoal) -> str:
        """Commit an autonomous goal to the Goal System. Returns goal ID."""
        goal_id = self._goal_system.create_goal(
            title=goal.objective,
            priority=int(goal.expected_benefit * 5),
            description=f"[AUTO] {goal.rationale}",
        )
        # Tag as autonomous
        self._graph.update_node(goal_id, properties={
            "source": "autonomous",
            "goal_source": goal.source,
            "expected_benefit": goal.expected_benefit,
            "estimated_effort": goal.estimated_effort,
        })
        self._graph.save()
        return goal_id

    def _from_contradictions(self) -> List[AutonomousGoal]:
        """Goals from unresolved contradictions."""
        goals = []
        edges = self._graph.find_edges(relation="contradicts")
        seen = set()
        for edge in edges:
            pair = tuple(sorted([edge.source_id, edge.target_id]))
            if pair in seen:
                continue
            seen.add(pair)
            src = self._graph.get_node(edge.source_id)
            tgt = self._graph.get_node(edge.target_id)
            if src and tgt:
                # Check if resolved
                if src.properties.get("status") == "disputed" or tgt.properties.get("status") == "disputed":
                    continue
                goals.append(AutonomousGoal(
                    objective=f"Resolve contradiction: {src.label[:40]} vs {tgt.label[:40]}",
                    rationale="Unresolved contradictions reduce knowledge reliability",
                    source="contradiction",
                    expected_benefit=0.7,
                    estimated_effort=3,
                    confidence=0.8,
                    related_nodes=[edge.source_id, edge.target_id],
                ))
        return goals[:3]

    def _from_prediction_failures(self) -> List[AutonomousGoal]:
        """Goals from nodes with low prediction accuracy."""
        goals = []
        for node_type in ["theory", "concept"]:
            nodes = self._graph.find_nodes(node_type=node_type)
            for n in nodes:
                acc = n.properties.get("_cs_prediction_accuracy", 0.5)
                usage = n.properties.get("_cs_usage_count", 0)
                if acc < 0.35 and usage > 3:
                    goals.append(AutonomousGoal(
                        objective=f"Investigate poor predictions for: {n.label[:50]}",
                        rationale=f"Prediction accuracy {acc:.0%} after {usage} uses",
                        source="prediction_failure",
                        expected_benefit=0.6,
                        estimated_effort=2,
                        confidence=0.7,
                        related_nodes=[n.id],
                    ))
        return goals[:3]

    def _from_weak_principles(self) -> List[AutonomousGoal]:
        """Goals from low-confidence principles."""
        goals = []
        theories = self._graph.find_nodes(node_type="theory")
        for t in theories:
            if t.properties.get("level") != "principle":
                continue
            if t.properties.get("status") in ("retired", "merged"):
                continue
            conf = t.properties.get("_cs_confidence", t.properties.get("confidence", 0.5))
            if conf < 0.4:
                goals.append(AutonomousGoal(
                    objective=f"Strengthen or retire weak principle: {t.label[:50]}",
                    rationale=f"Confidence {conf:.0%} — needs evidence or retirement",
                    source="weak_principle",
                    expected_benefit=0.5,
                    estimated_effort=2,
                    confidence=0.6,
                    related_nodes=[t.id],
                ))
        return goals[:2]

    def _from_disconnected_concepts(self) -> List[AutonomousGoal]:
        """Goals from isolated nodes with no connections."""
        goals = []
        for node_type in ["fact", "concept"]:
            nodes = self._graph.find_nodes(node_type=node_type)
            for n in nodes:
                neighbors = self._graph.neighbors(n.id, direction="both")
                if len(neighbors) == 0:
                    goals.append(AutonomousGoal(
                        objective=f"Find connections for isolated knowledge: {n.label[:50]}",
                        rationale="Disconnected knowledge cannot participate in reasoning",
                        source="disconnected",
                        expected_benefit=0.4,
                        estimated_effort=1,
                        confidence=0.5,
                        related_nodes=[n.id],
                    ))
        return goals[:2]

    def _from_stale_knowledge(self) -> List[AutonomousGoal]:
        """Goals from knowledge that hasn't been verified recently."""
        goals = []
        now = time.time()
        stale_threshold = 7 * 86400  # 7 days
        for node_type in ["fact"]:
            nodes = self._graph.find_nodes(node_type=node_type)
            for n in nodes:
                last_seen = n.properties.get("last_seen", n.updated_at)
                conf = n.properties.get("_cs_confidence", 0.5)
                if last_seen and (now - last_seen) > stale_threshold and conf > 0.5:
                    goals.append(AutonomousGoal(
                        objective=f"Verify stale knowledge: {n.label[:50]}",
                        rationale=f"Not accessed in {(now - last_seen) / 86400:.0f} days",
                        source="stale",
                        expected_benefit=0.3,
                        estimated_effort=1,
                        confidence=0.4,
                        related_nodes=[n.id],
                    ))
        return goals[:2]


_generator: Optional[AutonomousGoalGenerator] = None
def get_goal_generator(graph: Optional[RealityGraph] = None) -> AutonomousGoalGenerator:
    global _generator
    if _generator is None:
        _generator = AutonomousGoalGenerator(graph=graph)
    return _generator
