"""
AXIMA Internal World Model — Causal dynamics, not just stored facts.

Instead of: Bird → flies
Model: Bird → Wing → Lift → Energy → Flight

Represents: causality, dynamics, dependencies, constraints, state transitions.
Supports reasoning without memorized answers.
"""

import time
from typing import Optional, List, Dict, Any, Tuple
from core.reality_graph import get_reality_graph, RealityGraph


class CausalLink:
    """A causal relationship: A causes B under conditions C."""
    def __init__(self, cause_id: str, effect_id: str, mechanism: str = "",
                 conditions: str = "", strength: float = 0.7):
        self.cause_id = cause_id
        self.effect_id = effect_id
        self.mechanism = mechanism
        self.conditions = conditions
        self.strength = strength


class WorldModel:
    """Internal causal model for reasoning about dynamics."""

    def __init__(self, graph: Optional[RealityGraph] = None):
        self._graph = graph or get_reality_graph()

    def add_causal_link(self, cause_id: str, effect_id: str,
                        mechanism: str = "", conditions: str = "",
                        strength: float = 0.7) -> bool:
        """Add a causal relationship: cause → effect."""
        return self._graph.add_edge(cause_id, effect_id, "causes", properties={
            "mechanism": mechanism, "conditions": conditions, "strength": strength,
            "model_type": "causal", "created_at": time.time(),
        })

    def causal_chain(self, start_id: str, max_depth: int = 5) -> List[List[str]]:
        """Trace causal chains from a starting node. Returns paths."""
        chains = []
        self._trace_chain(start_id, [start_id], set(), chains, max_depth)
        return chains

    def predict_effects(self, cause_id: str) -> List[Dict[str, Any]]:
        """Predict what effects a cause will produce."""
        effects = []
        for nid, rel, edge in self._graph.neighbors(cause_id, relation="causes"):
            node = self._graph.get_node(nid)
            if node:
                strength = edge.properties.get("strength", 0.5) if edge else 0.5
                effects.append({
                    "effect_id": nid, "label": node.label,
                    "mechanism": edge.properties.get("mechanism", "") if edge else "",
                    "strength": strength,
                })
        return effects

    def find_causes(self, effect_id: str) -> List[Dict[str, Any]]:
        """Find what causes a given effect."""
        causes = []
        for nid, rel, edge in self._graph.neighbors(effect_id, direction="in"):
            if rel == "causes":
                node = self._graph.get_node(nid)
                if node:
                    causes.append({
                        "cause_id": nid, "label": node.label,
                        "mechanism": edge.properties.get("mechanism", "") if edge else "",
                    })
        return causes

    def simulate_intervention(self, node_id: str, change: str = "remove") -> List[str]:
        """What happens if we intervene on a node? Trace downstream effects."""
        affected = []
        visited = {node_id}
        frontier = [node_id]
        for _ in range(10):
            next_frontier = []
            for nid in frontier:
                for neighbor_id, rel, _ in self._graph.neighbors(nid, relation="causes"):
                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        affected.append(neighbor_id)
                        next_frontier.append(neighbor_id)
            frontier = next_frontier
            if not frontier:
                break
        return affected

    def _trace_chain(self, current: str, path: List[str], visited: set,
                     chains: List, max_depth: int):
        if len(path) > max_depth:
            chains.append(path[:])
            return
        visited.add(current)
        neighbors = self._graph.neighbors(current, relation="causes")
        if not neighbors:
            if len(path) > 1:
                chains.append(path[:])
            return
        for nid, _, _ in neighbors:
            if nid not in visited:
                self._trace_chain(nid, path + [nid], visited, chains, max_depth)

    def stats(self) -> Dict[str, Any]:
        causal_edges = self._graph.find_edges(relation="causes")
        return {"causal_links": len(causal_edges)}


_model: Optional[WorldModel] = None
def get_world_model(graph: Optional[RealityGraph] = None) -> WorldModel:
    global _model
    if _model is None:
        _model = WorldModel(graph=graph)
    return _model
