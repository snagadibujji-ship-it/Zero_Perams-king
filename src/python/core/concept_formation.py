"""
AXIMA Concept Formation Engine — Discover abstractions automatically.

Example: GPU, CUDA, SIMD, Tensor Core → "Massively Parallel Computing"

Supports: clustering, hierarchy discovery, semantic compression,
concept merging, concept splitting, abstraction scoring.
Concepts emerge from data, not hardcoded.
"""

import time
import re
from typing import Optional, List, Dict, Any, Set
from core.reality_graph import get_reality_graph, RealityGraph
from core.cognitive_state import get_state, set_state, initialize_state


class ConceptFormation:
    """Discovers abstractions by clustering related nodes."""

    def __init__(self, graph: Optional[RealityGraph] = None):
        self._graph = graph or get_reality_graph()

    def discover_concepts(self, min_cluster_size: int = 3, max_new: int = 3) -> List[Dict[str, Any]]:
        """Discover new abstract concepts from existing knowledge.
        
        Clusters nodes that share many connections or similar properties.
        """
        discoveries = []

        # Strategy 1: Nodes sharing many common neighbors
        clusters = self._find_neighbor_clusters(min_cluster_size)
        for cluster_nodes, shared_neighbors in clusters[:max_new]:
            # Generate concept name from common properties
            name = self._name_cluster(cluster_nodes)
            if name and not self._concept_exists(name):
                concept_id = self._create_concept(name, cluster_nodes, "neighbor_clustering")
                discoveries.append({
                    "concept": name, "id": concept_id,
                    "members": len(cluster_nodes), "method": "neighbor_clustering",
                })

        # Strategy 2: Domain co-occurrence clustering
        if len(discoveries) < max_new:
            domain_clusters = self._find_domain_clusters(min_cluster_size)
            for cluster_nodes, domain in domain_clusters[:max_new - len(discoveries)]:
                name = f"{domain} cluster"
                if not self._concept_exists(name):
                    concept_id = self._create_concept(name, cluster_nodes, "domain_clustering")
                    discoveries.append({
                        "concept": name, "id": concept_id,
                        "members": len(cluster_nodes), "method": "domain_clustering",
                    })

        return discoveries

    def merge_concepts(self, concept_ids: List[str], new_name: str) -> Optional[str]:
        """Merge multiple related concepts into one higher-level abstraction."""
        if len(concept_ids) < 2:
            return None
        # Create merged concept
        merged_id = self._graph.add_node("concept", new_name, {
            "abstraction_level": "merged",
            "source_concepts": concept_ids,
            "created_at": time.time(),
            "_cs_confidence": 0.6, "_cs_novelty": 0.7, "_cs_activation": 0.4,
        })
        # Link sources
        for cid in concept_ids:
            self._graph.add_edge(cid, merged_id, "extends")
            self._graph.add_edge(merged_id, cid, "contains")
        initialize_state(self._graph, merged_id, activation=0.4, confidence=0.6, novelty=0.8)
        self._graph.save()
        return merged_id

    def split_concept(self, concept_id: str, sub_names: List[str]) -> List[str]:
        """Split an overly broad concept into sub-concepts."""
        new_ids = []
        for name in sub_names:
            nid = self._graph.add_node("concept", name, {
                "abstraction_level": "split",
                "split_from": concept_id,
                "created_at": time.time(),
            })
            self._graph.add_edge(concept_id, nid, "contains")
            initialize_state(self._graph, nid, activation=0.3, confidence=0.5, novelty=0.6)
            new_ids.append(nid)
        self._graph.save()
        return new_ids

    def abstraction_score(self, concept_id: str) -> float:
        """Score how good an abstraction is (0-1). High = useful, connected, used."""
        node = self._graph.get_node(concept_id)
        if not node:
            return 0.0
        state = get_state(self._graph, concept_id)
        connections = len(self._graph.neighbors(concept_id, direction="both"))
        # Good abstraction: connected, used, confident
        return min(1.0, (connections / 10.0) * 0.4 + state.usage_count / 10.0 * 0.3 + state.confidence * 0.3)

    def _find_neighbor_clusters(self, min_size: int) -> List[tuple]:
        """Find groups of nodes that share many neighbors."""
        facts = self._graph.find_nodes(node_type="fact")
        concepts = self._graph.find_nodes(node_type="concept")
        all_nodes = facts + concepts

        # Build neighbor sets
        neighbor_sets: Dict[str, Set[str]] = {}
        for n in all_nodes:
            neighbors = self._graph.neighbors(n.id, direction="both")
            neighbor_sets[n.id] = {nid for nid, _, _ in neighbors}

        # Find pairs with high overlap
        clusters = []
        seen = set()
        for i, n1 in enumerate(all_nodes):
            if n1.id in seen:
                continue
            cluster = [n1.id]
            for n2 in all_nodes[i+1:]:
                if n2.id in seen:
                    continue
                if not neighbor_sets.get(n1.id) or not neighbor_sets.get(n2.id):
                    continue
                overlap = len(neighbor_sets[n1.id] & neighbor_sets[n2.id])
                if overlap >= 2:
                    cluster.append(n2.id)
            if len(cluster) >= min_size:
                for nid in cluster:
                    seen.add(nid)
                shared = set.intersection(*[neighbor_sets.get(nid, set()) for nid in cluster])
                clusters.append((cluster, list(shared)))

        return clusters[:5]

    def _find_domain_clusters(self, min_size: int) -> List[tuple]:
        """Find clusters by domain property."""
        by_domain: Dict[str, List[str]] = {}
        for node_type in ["fact", "concept"]:
            nodes = self._graph.find_nodes(node_type=node_type)
            for n in nodes:
                domain = n.properties.get("domain", "")
                if domain:
                    by_domain.setdefault(domain, []).append(n.id)
        return [(nids, domain) for domain, nids in by_domain.items() if len(nids) >= min_size][:5]

    def _name_cluster(self, node_ids: List[str]) -> str:
        """Generate a name for a cluster of nodes."""
        labels = []
        for nid in node_ids[:5]:
            n = self._graph.get_node(nid)
            if n:
                labels.append(n.label)
        if not labels:
            return ""
        # Find common words
        word_sets = [set(re.findall(r'\b\w{4,}\b', l.lower())) for l in labels]
        if word_sets:
            common = set.intersection(*word_sets) if len(word_sets) > 1 else word_sets[0]
            if common:
                return f"{'_'.join(sorted(common)[:3])}_concept"
        return f"cluster_of_{len(node_ids)}_nodes"

    def _concept_exists(self, name: str) -> bool:
        existing = self._graph.find_nodes(node_type="concept", label_contains=name[:20])
        return len(existing) > 0

    def _create_concept(self, name: str, member_ids: List[str], method: str) -> str:
        nid = self._graph.add_node("concept", name, {
            "abstraction_level": "discovered",
            "discovery_method": method,
            "member_count": len(member_ids),
            "created_at": time.time(),
            "_cs_confidence": 0.5, "_cs_novelty": 0.9, "_cs_activation": 0.4,
        })
        for mid in member_ids[:10]:
            self._graph.add_edge(mid, nid, "relates_to")
        initialize_state(self._graph, nid, activation=0.4, confidence=0.5, novelty=0.9)
        self._graph.save()
        return nid


_formation: Optional[ConceptFormation] = None
def get_concept_formation(graph: Optional[RealityGraph] = None) -> ConceptFormation:
    global _formation
    if _formation is None:
        _formation = ConceptFormation(graph=graph)
    return _formation
