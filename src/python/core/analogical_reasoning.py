"""
AXIMA Analogical Reasoning — Structural matching across domains.

Water Flow ≈ Electricity ≈ Traffic ≈ Computer Networks
Reason from structure, not vocabulary.
"""

import re
from typing import Optional, List, Dict, Any, Set, Tuple
from core.reality_graph import get_reality_graph, RealityGraph


class AnalogicalReasoning:
    """Finds structural similarities between different domain subgraphs."""

    def __init__(self, graph: Optional[RealityGraph] = None):
        self._graph = graph or get_reality_graph()

    def find_analogies(self, source_id: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Find nodes structurally analogous to source."""
        source = self._graph.get_node(source_id)
        if not source:
            return []

        # Get source's structural signature (relation types + counts)
        source_sig = self._structural_signature(source_id)
        source_domain = source.properties.get("domain", "")

        # Compare against nodes in OTHER domains
        analogies = []
        for node_type in ["concept", "fact", "theory"]:
            nodes = self._graph.find_nodes(node_type=node_type)
            for n in nodes:
                if n.id == source_id:
                    continue
                n_domain = n.properties.get("domain", "")
                # Cross-domain only
                if n_domain and n_domain == source_domain:
                    continue
                n_sig = self._structural_signature(n.id)
                similarity = self._signature_similarity(source_sig, n_sig)
                if similarity > 0.3:
                    analogies.append({
                        "target_id": n.id,
                        "target_label": n.label,
                        "target_domain": n_domain,
                        "similarity": round(similarity, 3),
                        "shared_structure": list(set(source_sig.keys()) & set(n_sig.keys())),
                    })

        analogies.sort(key=lambda a: -a["similarity"])
        return analogies[:max_results]

    def transfer_structure(self, source_id: str, target_id: str) -> List[str]:
        """Transfer structural relations from source to target (create analogy edges)."""
        created = []
        source_neighbors = self._graph.neighbors(source_id, direction="out")
        target_neighbors = {nid for nid, _, _ in self._graph.neighbors(target_id, direction="out")}

        for nid, rel, _ in source_neighbors:
            if rel in ("causes", "contains", "depends_on"):
                # Check if target already has similar relation
                if nid not in target_neighbors:
                    self._graph.add_edge(target_id, source_id, "relates_to",
                                        properties={"analogy": True, "transferred_relation": rel})
                    created.append(f"{rel} (from {nid})")
                    break  # One transfer per call
        if created:
            self._graph.save()
        return created

    def _structural_signature(self, node_id: str) -> Dict[str, int]:
        """Get structural signature: {relation_type: count}."""
        sig: Dict[str, int] = {}
        for _, rel, _ in self._graph.neighbors(node_id, direction="both"):
            sig[rel] = sig.get(rel, 0) + 1
        return sig

    def _signature_similarity(self, sig1: Dict[str, int], sig2: Dict[str, int]) -> float:
        """Compare two structural signatures (cosine-like)."""
        if not sig1 or not sig2:
            return 0.0
        all_keys = set(sig1.keys()) | set(sig2.keys())
        dot = sum(sig1.get(k, 0) * sig2.get(k, 0) for k in all_keys)
        mag1 = sum(v ** 2 for v in sig1.values()) ** 0.5
        mag2 = sum(v ** 2 for v in sig2.values()) ** 0.5
        if mag1 == 0 or mag2 == 0:
            return 0.0
        return dot / (mag1 * mag2)


_analogical: Optional[AnalogicalReasoning] = None
def get_analogical_reasoning(graph: Optional[RealityGraph] = None) -> AnalogicalReasoning:
    global _analogical
    if _analogical is None:
        _analogical = AnalogicalReasoning(graph=graph)
    return _analogical
