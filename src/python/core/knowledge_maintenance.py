"""
AXIMA Knowledge Maintenance — Continuous Reality Graph upkeep.

Responsibilities: merge duplicates, archive inactive, strengthen valuable links,
weaken obsolete links, reorganize concept clusters, preserve historical lineage.
Incremental and event-driven.
"""

import time
from typing import Optional, List, Dict, Any
from core.reality_graph import get_reality_graph, RealityGraph
from core.cognitive_state import get_state, set_state


class KnowledgeMaintenance:
    """Incremental maintenance of the Reality Graph."""

    def __init__(self, graph: Optional[RealityGraph] = None):
        self._graph = graph or get_reality_graph()
        self._maintenance_count = 0

    def maintain_step(self, max_work: int = 5) -> Dict[str, int]:
        """One incremental maintenance step."""
        self._maintenance_count += 1
        result = {"duplicates_merged": 0, "archived": 0, "links_strengthened": 0, "links_weakened": 0}
        work = 0

        if work < max_work:
            result["duplicates_merged"] = self._merge_duplicates(max_work - work)
            work += result["duplicates_merged"]

        if work < max_work:
            result["archived"] = self._archive_inactive(max_work - work)
            work += result["archived"]

        if work < max_work:
            result["links_strengthened"] = self._strengthen_valuable_links(max_work - work)
            work += result["links_strengthened"]

        if work < max_work:
            result["links_weakened"] = self._weaken_obsolete_links(max_work - work)

        self._graph.save()
        return result

    def _merge_duplicates(self, limit: int) -> int:
        """Find and merge duplicate nodes."""
        merged = 0
        facts = self._graph.find_nodes(node_type="fact")
        seen_labels = {}
        for f in facts:
            key = f.label.lower().strip()[:40]
            if key in seen_labels:
                # Duplicate found — merge into existing
                existing_id = seen_labels[key]
                # Transfer edges
                for nid, rel, _ in self._graph.neighbors(f.id, direction="both"):
                    self._graph.add_edge(existing_id, nid, rel)
                # Boost existing confidence
                state = get_state(self._graph, existing_id)
                state.confidence = min(1.0, state.confidence + 0.05)
                set_state(self._graph, existing_id, state)
                # Remove duplicate
                self._graph.remove_node(f.id)
                merged += 1
                if merged >= limit:
                    break
            else:
                seen_labels[key] = f.id
        return merged

    def _archive_inactive(self, limit: int) -> int:
        """Archive long-dormant nodes (mark, don't delete)."""
        archived = 0
        now = time.time()
        for node_type in ["fact", "memory"]:
            nodes = self._graph.find_nodes(node_type=node_type)
            for n in nodes:
                if archived >= limit:
                    return archived
                state = get_state(self._graph, n.id)
                if state.is_dormant and state.age > 30 * 86400:  # 30 days dormant
                    self._graph.update_node(n.id, properties={"status": "archived", "archived_at": now})
                    archived += 1
        return archived

    def _strengthen_valuable_links(self, limit: int) -> int:
        """Strengthen edges between high-confidence, frequently-used nodes."""
        strengthened = 0
        edges = self._graph.find_edges(relation="supports")
        for edge in edges:
            if strengthened >= limit:
                break
            src_state = get_state(self._graph, edge.source_id)
            tgt_state = get_state(self._graph, edge.target_id)
            if src_state.confidence > 0.7 and tgt_state.confidence > 0.7:
                if edge.weight < 1.5:
                    # Can't modify edge weight directly, but we can boost target
                    tgt_state.stability = min(1.0, tgt_state.stability + 0.01)
                    set_state(self._graph, edge.target_id, tgt_state)
                    strengthened += 1
        return strengthened

    def _weaken_obsolete_links(self, limit: int) -> int:
        """Weaken edges involving low-confidence or dormant nodes."""
        weakened = 0
        edges = self._graph.find_edges(relation="supports")
        for edge in edges:
            if weakened >= limit:
                break
            src_state = get_state(self._graph, edge.source_id)
            if src_state.confidence < 0.2 and src_state.is_dormant:
                # Remove weak support link
                self._graph.remove_edge(edge.source_id, edge.target_id, "supports")
                weakened += 1
        return weakened

    def stats(self) -> Dict[str, Any]:
        return {"maintenance_cycles": self._maintenance_count}


_maintenance: Optional[KnowledgeMaintenance] = None
def get_maintenance(graph: Optional[RealityGraph] = None) -> KnowledgeMaintenance:
    global _maintenance
    if _maintenance is None:
        _maintenance = KnowledgeMaintenance(graph=graph)
    return _maintenance
