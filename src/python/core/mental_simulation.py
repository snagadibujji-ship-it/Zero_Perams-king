"""
AXIMA Mental Simulation — Generate and evaluate possible futures.

Before decisions: generate multiple scenarios, estimate outcomes,
evaluate consequences, choose best path.
The simulator NEVER alters reality. It only evaluates possibilities.
"""

import time
import copy
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from core.reality_graph import get_reality_graph, RealityGraph
from core.cognitive_state import get_state


@dataclass
class Scenario:
    """A simulated possible future."""
    id: str = ""
    description: str = ""
    actions: List[str] = field(default_factory=list)
    predicted_outcomes: List[str] = field(default_factory=list)
    confidence: float = 0.5
    risk: float = 0.0
    benefit: float = 0.0
    score: float = 0.0  # benefit * confidence - risk

    def compute_score(self):
        self.score = self.benefit * self.confidence - self.risk * 0.5


class MentalSimulation:
    """Internal simulator for evaluating possibilities without altering reality."""

    def __init__(self, graph: Optional[RealityGraph] = None):
        self._graph = graph or get_reality_graph()

    def simulate_action(self, action: str, context_nodes: List[str] = None) -> List[Scenario]:
        """Simulate possible outcomes of an action."""
        scenarios = []
        context = context_nodes or []

        # Generate optimistic scenario
        scenarios.append(self._generate_scenario(action, context, "optimistic"))
        # Generate pessimistic scenario
        scenarios.append(self._generate_scenario(action, context, "pessimistic"))
        # Generate neutral scenario
        scenarios.append(self._generate_scenario(action, context, "neutral"))

        for s in scenarios:
            s.compute_score()
        scenarios.sort(key=lambda s: -s.score)
        return scenarios

    def compare_options(self, options: List[str], context_nodes: List[str] = None) -> Dict[str, Any]:
        """Compare multiple action options by simulating each."""
        results = {}
        for option in options:
            scenarios = self.simulate_action(option, context_nodes)
            best = scenarios[0] if scenarios else Scenario()
            results[option] = {
                "best_score": round(best.score, 3),
                "confidence": round(best.confidence, 3),
                "risk": round(best.risk, 3),
                "scenarios_generated": len(scenarios),
            }
        # Rank
        ranked = sorted(results.items(), key=lambda x: -x[1]["best_score"])
        return {"ranked_options": [r[0] for r in ranked], "details": results}

    def simulate_causal_chain(self, trigger_id: str, depth: int = 3) -> List[Dict[str, Any]]:
        """Simulate a causal chain from a trigger node."""
        chain = []
        current = trigger_id
        visited = {current}
        for _ in range(depth):
            effects = self._graph.neighbors(current, relation="causes")
            if not effects:
                break
            for nid, _, edge in effects:
                if nid in visited:
                    continue
                visited.add(nid)
                node = self._graph.get_node(nid)
                strength = edge.properties.get("strength", 0.5) if edge else 0.5
                chain.append({
                    "node_id": nid,
                    "label": node.label if node else "",
                    "causal_strength": strength,
                })
                current = nid
                break
        return chain

    def _generate_scenario(self, action: str, context: List[str], mood: str) -> Scenario:
        """Generate one scenario based on graph structure."""
        # Use context nodes to estimate outcomes
        confidence_base = 0.5
        risk_base = 0.3
        benefit_base = 0.5

        for nid in context[:5]:
            state = get_state(self._graph, nid)
            confidence_base = (confidence_base + state.confidence) / 2
            if state.entropy > 0.5:
                risk_base += 0.1

        if mood == "optimistic":
            return Scenario(id=f"sim_opt_{int(time.time())}", description=f"Best case: {action}",
                           actions=[action], confidence=min(0.9, confidence_base + 0.2),
                           risk=max(0.05, risk_base - 0.2), benefit=0.8)
        elif mood == "pessimistic":
            return Scenario(id=f"sim_pes_{int(time.time())}", description=f"Worst case: {action}",
                           actions=[action], confidence=max(0.2, confidence_base - 0.2),
                           risk=min(0.9, risk_base + 0.3), benefit=0.3)
        else:
            return Scenario(id=f"sim_neu_{int(time.time())}", description=f"Expected: {action}",
                           actions=[action], confidence=confidence_base,
                           risk=risk_base, benefit=benefit_base)


_sim: Optional[MentalSimulation] = None
def get_mental_simulation(graph: Optional[RealityGraph] = None) -> MentalSimulation:
    global _sim
    if _sim is None:
        _sim = MentalSimulation(graph=graph)
    return _sim
