"""
AXIMA Knowledge Transfer — Generalize principles across domains.

Example: Binary Search → Database Indexing → Filesystem Lookup → Network Routing.
Transfer learning by structural analogy. Measure transfer quality.
"""

from typing import Optional, List, Dict, Any
from core.reality_graph import get_reality_graph, RealityGraph
from core.analogical_reasoning import get_analogical_reasoning
from core.cognitive_state import get_state, set_state


class KnowledgeTransfer:
    """Transfers learned principles across domains."""

    def __init__(self, graph: Optional[RealityGraph] = None):
        self._graph = graph or get_reality_graph()
        self._analogy = get_analogical_reasoning(self._graph)
        self._transfers: List[Dict[str, Any]] = []

    def transfer_principle(self, principle_id: str, target_domain: str) -> Optional[Dict[str, Any]]:
        """Attempt to transfer a principle to a new domain."""
        node = self._graph.get_node(principle_id)
        if not node:
            return None

        # Find analogous nodes in target domain
        analogies = self._analogy.find_analogies(principle_id, max_results=3)
        target_analogies = [a for a in analogies if a.get("target_domain") == target_domain]

        if not target_analogies:
            # Try finding ANY node in target domain
            domain_nodes = [n for n in self._graph.find_nodes(node_type="concept")
                          if n.properties.get("domain") == target_domain]
            if not domain_nodes:
                return None
            target_analogies = [{"target_id": domain_nodes[0].id, "similarity": 0.3}]

        best_match = target_analogies[0]

        # Create transfer node
        transfer_statement = f"[Transfer] {node.label} applied to {target_domain}"
        transfer_id = self._graph.add_node("theory", transfer_statement[:80], {
            "level": "rule",
            "source_principle": principle_id,
            "target_domain": target_domain,
            "transfer_confidence": best_match["similarity"],
            "confidence": best_match["similarity"] * 0.7,
            "_cs_confidence": best_match["similarity"] * 0.7,
            "_cs_novelty": 0.8,
            "status": "transferred",
            "needs_validation": True,
        })

        # Link
        self._graph.add_edge(principle_id, transfer_id, "extends")
        if best_match.get("target_id"):
            self._graph.add_edge(transfer_id, best_match["target_id"], "relates_to")
        self._graph.save()

        result = {
            "transfer_id": transfer_id,
            "source": node.label,
            "target_domain": target_domain,
            "confidence": round(best_match["similarity"] * 0.7, 3),
            "analogy_strength": best_match["similarity"],
            "needs_validation": True,
        }
        self._transfers.append(result)
        return result

    def validate_transfer(self, transfer_id: str, success: bool) -> Dict[str, Any]:
        """Validate whether a transferred principle worked in new domain."""
        node = self._graph.get_node(transfer_id)
        if not node:
            return {"error": "Not found"}

        conf = node.properties.get("confidence", 0.5)
        if success:
            new_conf = min(0.9, conf + 0.15)
            self._graph.update_node(transfer_id, properties={
                "confidence": new_conf, "_cs_confidence": new_conf,
                "needs_validation": False, "validated": True,
            })
        else:
            new_conf = max(0.1, conf - 0.2)
            self._graph.update_node(transfer_id, properties={
                "confidence": new_conf, "_cs_confidence": new_conf,
                "status": "failed_transfer",
            })
        self._graph.save()
        return {"success": success, "new_confidence": round(new_conf, 3)}

    def transfer_quality(self) -> float:
        """Overall transfer success rate."""
        if not self._transfers:
            return 0.0
        validated = [t for t in self._transfers if self._graph.get_node(t.get("transfer_id", ""))
                    and self._graph.get_node(t["transfer_id"]).properties.get("validated")]
        return len(validated) / max(1, len(self._transfers))

    def stats(self) -> Dict[str, Any]:
        return {"total_transfers": len(self._transfers), "quality": self.transfer_quality()}


_transfer: Optional[KnowledgeTransfer] = None
def get_knowledge_transfer(graph: Optional[RealityGraph] = None) -> KnowledgeTransfer:
    global _transfer
    if _transfer is None:
        _transfer = KnowledgeTransfer(graph=graph)
    return _transfer
