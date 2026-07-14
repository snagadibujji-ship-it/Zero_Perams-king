"""
ACES v2 — Phase 6: Reason Skeleton Engine
Derives the logical backbone of an explanation from the meaning graph.
This is where ACES stops being a formatter and becomes a REAL explainer.
"""

import re
from typing import List, Optional
from .models import MeaningGraph, MeaningNode, ReasonChain, RouterDecision


class Reasoner:
    """Derive reason skeletons from meaning graphs."""

    def reason(self, graph: MeaningGraph, decision: RouterDecision) -> ReasonChain:
        """Build a complete reason chain from the meaning graph."""
        chain = ReasonChain()

        # 1. Find prerequisites (what must be understood first)
        chain.prerequisites = self._find_prerequisites(graph)

        # 2. Build the main reasoning chain
        chain.chain = self._build_chain(graph, decision)

        # 3. Find analogies (similar concepts that aid understanding)
        chain.analogies = self._find_analogies(graph, decision)

        # 4. Find misconceptions (what people commonly get wrong)
        chain.misconceptions = self._find_misconceptions(graph)

        # 5. What does this enable? (what you can do with this knowledge)
        chain.enables = self._find_enables(graph)

        # 6. What does this rule out?
        chain.rules_out = self._find_rules_out(graph)

        # 7. Shortest path (minimal explanation)
        chain.shortest_path = self._find_shortest(chain)

        return chain

    def _find_prerequisites(self, graph: MeaningGraph) -> List[str]:
        """Find what must be understood before this topic."""
        prereqs = []

        # Nodes that are depended on but not explained
        depended_on = set()
        for edge in graph.edges:
            if edge.relation == "depends_on":
                node = graph.get_node(edge.target)
                if node:
                    depended_on.add(node.label)

        # Nodes with only incoming "enables" edges (they're foundations)
        has_outgoing = set(e.source for e in graph.edges)
        for node in graph.nodes:
            if node.id not in has_outgoing and node.type == "concept":
                if any(e.target == node.id for e in graph.edges):
                    prereqs.append(f"Understand: {node.label}")

        # Add depended-on concepts
        for dep in depended_on:
            prereqs.append(f"Requires: {dep}")

        return prereqs[:5]  # Max 5 prerequisites

    def _build_chain(self, graph: MeaningGraph, decision: RouterDecision) -> List[str]:
        """Build the main reasoning chain based on question type."""
        chain = []

        if decision.question_type == "why":
            chain = self._build_causal_chain(graph)
        elif decision.question_type == "how":
            chain = self._build_process_chain(graph)
        elif decision.question_type == "compare":
            chain = self._build_comparison_chain(graph)
        elif decision.question_type in ("calculation", "derivation"):
            chain = self._build_derivation_chain(graph)
        elif decision.question_type == "teach":
            chain = self._build_teaching_chain(graph)
        else:
            chain = self._build_factual_chain(graph)

        return chain

    def _build_causal_chain(self, graph: MeaningGraph) -> List[str]:
        """Build cause→effect chain for 'why' questions."""
        chain = []
        # Follow causal edges from root
        visited = set()
        current = graph.root_node

        while current and current not in visited:
            visited.add(current)
            node = graph.get_node(current)
            if node:
                chain.append(node.label)

            # Find next in causal chain
            next_id = None
            for edge in graph.edges:
                if edge.source == current and edge.relation in ("causes", "enables", "transforms_into"):
                    next_id = edge.target
                    break
            current = next_id

        if not chain:
            chain = [n.label for n in graph.nodes[:5]]

        return chain

    def _build_process_chain(self, graph: MeaningGraph) -> List[str]:
        """Build sequential steps for 'how' questions."""
        # Find step-type nodes in order
        steps = [n for n in graph.nodes if n.type == "step"]
        if steps:
            return [n.label for n in steps]

        # Otherwise, follow enables edges
        return self._build_causal_chain(graph)

    def _build_comparison_chain(self, graph: MeaningGraph) -> List[str]:
        """Build comparison structure."""
        chain = []
        # Find pairs connected by similar_to or contradicts
        for edge in graph.edges:
            if edge.relation in ("similar_to", "contradicts"):
                n1 = graph.get_node(edge.source)
                n2 = graph.get_node(edge.target)
                if n1 and n2:
                    if edge.relation == "similar_to":
                        chain.append(f"{n1.label} is similar to {n2.label}")
                    else:
                        chain.append(f"{n1.label} differs from {n2.label}")

        if not chain:
            chain = [n.label for n in graph.nodes[:4]]
        return chain

    def _build_derivation_chain(self, graph: MeaningGraph) -> List[str]:
        """Build step-by-step derivation."""
        # Find formula nodes
        formulas = [n for n in graph.nodes if n.type == "formula"]
        steps = [n for n in graph.nodes if n.type == "step"]

        chain = []
        if formulas:
            chain.append(f"Starting from: {formulas[0].label}")
        for step in steps:
            chain.append(step.label)
        if len(formulas) > 1:
            chain.append(f"Result: {formulas[-1].label}")

        if not chain:
            chain = [n.label for n in graph.nodes]
        return chain

    def _build_teaching_chain(self, graph: MeaningGraph) -> List[str]:
        """Build teaching sequence: foundations → core → implications."""
        chain = []

        # Prerequisites first
        prereq_nodes = []
        for edge in graph.edges:
            if edge.relation == "depends_on":
                node = graph.get_node(edge.target)
                if node:
                    prereq_nodes.append(node)

        for n in prereq_nodes:
            chain.append(f"First understand: {n.label}")

        # Core concepts
        for n in graph.nodes:
            if n.type in ("concept", "rule") and n not in prereq_nodes:
                chain.append(n.label)

        # Implications
        for edge in graph.edges:
            if edge.relation == "enables":
                target = graph.get_node(edge.target)
                if target:
                    chain.append(f"This enables: {target.label}")

        return chain or [n.label for n in graph.nodes]

    def _build_factual_chain(self, graph: MeaningGraph) -> List[str]:
        """Build simple factual explanation."""
        return [n.label for n in graph.nodes if n.label]

    def _find_analogies(self, graph: MeaningGraph, decision: RouterDecision) -> List[str]:
        """Generate analogies based on graph structure."""
        analogies = []

        # If there's a transformation, use metaphor
        for edge in graph.edges:
            if edge.relation == "transforms_into":
                src = graph.get_node(edge.source)
                tgt = graph.get_node(edge.target)
                if src and tgt:
                    analogies.append(f"Think of it like {src.label} becoming {tgt.label}")

        # If there's a causal chain, use domino analogy
        causal_count = sum(1 for e in graph.edges if e.relation == "causes")
        if causal_count >= 2:
            analogies.append("Like dominoes: each step triggers the next")

        # If there's dependency, use building analogy
        dep_count = sum(1 for e in graph.edges if e.relation == "depends_on")
        if dep_count >= 1:
            analogies.append("Like building a house: you need the foundation before the walls")

        return analogies[:3]

    def _find_misconceptions(self, graph: MeaningGraph) -> List[str]:
        """Identify common misconceptions."""
        misconceptions = []

        # Contradictions are potential misconception areas
        for edge in graph.edges:
            if edge.relation == "contradicts":
                n1 = graph.get_node(edge.source)
                n2 = graph.get_node(edge.target)
                if n1 and n2:
                    misconceptions.append(f"Don't confuse: {n1.label} ≠ {n2.label}")

        # Limits/constraints often reveal misconceptions
        for edge in graph.edges:
            if edge.relation == "limits":
                node = graph.get_node(edge.target)
                if node:
                    misconceptions.append(f"Common mistake: assuming {node.label} always applies")

        return misconceptions[:3]

    def _find_enables(self, graph: MeaningGraph) -> List[str]:
        """What does this knowledge unlock?"""
        enables = []
        for edge in graph.edges:
            if edge.relation == "enables":
                target = graph.get_node(edge.target)
                if target:
                    enables.append(target.label)
        return enables[:4]

    def _find_rules_out(self, graph: MeaningGraph) -> List[str]:
        """What does this knowledge eliminate?"""
        rules_out = []
        for edge in graph.edges:
            if edge.relation == "contradicts":
                target = graph.get_node(edge.target)
                if target:
                    rules_out.append(target.label)
        return rules_out[:3]

    def _find_shortest(self, chain: ReasonChain) -> List[str]:
        """Find the minimal explanation path."""
        # Take first and last of main chain + key insight
        if len(chain.chain) <= 2:
            return chain.chain
        return [chain.chain[0], chain.chain[-1]]
