"""
ACES v2 — Phase 5: Graph Builder
Enriches the raw parsed graph with proper node types, edge confidence,
duplicate merging, and evidence preservation.
"""

import re
from typing import List, Set
from .models import MeaningGraph, MeaningNode, MeaningEdge, RouterDecision


class GraphBuilder:
    """Build a rich, typed meaning graph from parser output."""

    def build(self, graph: MeaningGraph, decision: RouterDecision) -> MeaningGraph:
        """Enrich and clean the meaning graph."""
        # Step 1: Classify node types more precisely
        self._classify_nodes(graph, decision)

        # Step 2: Merge duplicate/near-duplicate nodes
        self._merge_duplicates(graph)

        # Step 3: Add confidence scores to edges
        self._score_edges(graph)

        # Step 4: Infer missing edges (if A→B and B→C, maybe A→C)
        self._infer_transitive(graph)

        # Step 5: Set root node
        self._determine_root(graph)

        return graph

    def _classify_nodes(self, graph: MeaningGraph, decision: RouterDecision):
        """Reclassify nodes based on content analysis."""
        for node in graph.nodes:
            content = node.content or node.label
            cl = content.lower()

            # Formula detection
            if re.search(r'[a-zA-Z]\s*=\s*[a-zA-Z0-9+\-*/^]', content):
                node.type = "formula"
            # Rule/law detection
            elif re.search(r'\b(?:law|rule|principle|theorem|always|never|must)\b', cl):
                node.type = "rule"
            # Warning/exception
            elif re.search(r'\b(?:warning|caution|exception|but not|however|unless)\b', cl):
                node.type = "warning"
            # Example
            elif re.search(r'\b(?:for example|such as|like|e\.g\.|instance)\b', cl):
                node.type = "example"
            # Insight/key point
            elif re.search(r'\b(?:key|important|critical|essential|insight|note)\b', cl):
                node.type = "insight"
            # Step (already classified by parser, keep it)
            elif node.type == "step":
                pass
            # Default: concept (already set)

    def _merge_duplicates(self, graph: MeaningGraph):
        """Merge nodes that refer to the same concept."""
        merged: Set[str] = set()
        for i, n1 in enumerate(graph.nodes):
            if n1.id in merged:
                continue
            for j, n2 in enumerate(graph.nodes):
                if j <= i or n2.id in merged:
                    continue
                if self._is_duplicate(n1, n2):
                    # Merge n2 into n1
                    self._merge_nodes(graph, n1, n2)
                    merged.add(n2.id)

        # Remove merged nodes
        graph.nodes = [n for n in graph.nodes if n.id not in merged]

    def _is_duplicate(self, n1: MeaningNode, n2: MeaningNode) -> bool:
        """Check if two nodes refer to the same concept."""
        l1 = n1.label.lower().strip()
        l2 = n2.label.lower().strip()

        # Exact match
        if l1 == l2:
            return True

        # One contains the other
        if l1 in l2 or l2 in l1:
            if len(l1) > 3 and len(l2) > 3:
                return True

        return False

    def _merge_nodes(self, graph: MeaningGraph, keep: MeaningNode, remove: MeaningNode):
        """Merge 'remove' into 'keep', redirecting all edges."""
        # Combine content
        if remove.content and remove.content not in keep.content:
            keep.content += "; " + remove.content

        # Combine evidence
        if remove.evidence and remove.evidence not in keep.evidence:
            keep.evidence += " | " + remove.evidence

        # Redirect edges
        for edge in graph.edges:
            if edge.source == remove.id:
                edge.source = keep.id
            if edge.target == remove.id:
                edge.target = keep.id

    def _score_edges(self, graph: MeaningGraph):
        """Assign confidence scores to edges."""
        for edge in graph.edges:
            # Edges with explicit evidence get high confidence
            if edge.evidence:
                edge.confidence = 0.9
            else:
                edge.confidence = 0.6

            # Certain relations are stronger
            if edge.relation in ("is", "causes", "depends_on"):
                edge.confidence = min(1.0, edge.confidence + 0.1)
            elif edge.relation in ("similar_to", "contradicts"):
                edge.confidence = min(1.0, edge.confidence - 0.1)

    def _infer_transitive(self, graph: MeaningGraph):
        """Infer transitive relationships: if A causes B and B causes C, then A causes C."""
        new_edges = []
        causal_rels = {"causes", "enables", "transforms_into"}

        for e1 in graph.edges:
            if e1.relation in causal_rels:
                for e2 in graph.edges:
                    if e2.relation in causal_rels and e2.source == e1.target:
                        # A→B→C: add A→C
                        if e1.source != e2.target:  # No self-loops
                            exists = any(e.source == e1.source and e.target == e2.target
                                        for e in graph.edges)
                            if not exists:
                                new_edges.append(MeaningEdge(
                                    source=e1.source,
                                    target=e2.target,
                                    relation="enables",
                                    confidence=0.5,
                                    evidence="(inferred transitive)"
                                ))

        graph.edges.extend(new_edges[:5])  # Limit to prevent explosion

    def _determine_root(self, graph: MeaningGraph):
        """Determine the root/main topic node."""
        if graph.root_node:
            return

        # Root = node with most outgoing edges
        out_counts = {}
        for edge in graph.edges:
            out_counts[edge.source] = out_counts.get(edge.source, 0) + 1

        if out_counts:
            graph.root_node = max(out_counts, key=out_counts.get)
        elif graph.nodes:
            graph.root_node = graph.nodes[0].id
