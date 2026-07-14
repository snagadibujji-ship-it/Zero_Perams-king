"""
ACES v2 — Phases 11-13: Bridges + Multi-step
Connects ACES to the math/physics solvers and external knowledge.
"""

import re
from typing import Optional, List, Dict
from .models import MeaningGraph, MeaningNode, MeaningEdge, RouterDecision, NormalizedInput


class SolverBridge:
    """Feed math/physics solver output into ACES as structured data.
    
    Converts solver results (formulas, steps, values) into MeaningGraph nodes
    with high trust scores.
    """

    def enrich(self, graph: MeaningGraph, inp: NormalizedInput,
               decision: RouterDecision) -> MeaningGraph:
        """Add solver results to the meaning graph."""
        if not decision.needs_solver:
            return graph

        # Try math solver
        if decision.domain == "math":
            self._add_math_solution(graph, inp.clean)

        # Try physics solver
        elif decision.domain == "physics":
            self._add_physics_solution(graph, inp.clean)

        return graph

    def _add_math_solution(self, graph: MeaningGraph, text: str):
        """Route to PROMETHEUS math solver and add results."""
        try:
            import sys
            sys.path.insert(0, 'src/python')
            from prometheus import get_prometheus
            P = get_prometheus()
            result = P.solve(text)
            if result:
                # Add formula node with high confidence
                node = MeaningNode(
                    id="solver_result",
                    type="formula",
                    label=str(result.get('answer', result)),
                    content=str(result),
                    evidence="PROMETHEUS math solver",
                    confidence=1.0,
                    metadata={"source": "solver", "trust": "high"}
                )
                graph.add_node(node)

                # Add steps if available
                steps = result.get('steps', []) if isinstance(result, dict) else []
                prev_id = None
                for i, step in enumerate(steps):
                    step_node = MeaningNode(
                        id=f"step_{i}",
                        type="step",
                        label=str(step),
                        confidence=1.0,
                        metadata={"source": "solver"}
                    )
                    graph.add_node(step_node)
                    if prev_id:
                        graph.add_edge(MeaningEdge(source=prev_id, target=step_node.id, relation="enables"))
                    prev_id = step_node.id
        except:
            pass  # Solver not available

    def _add_physics_solution(self, graph: MeaningGraph, text: str):
        """Route to physics solver and add results."""
        try:
            import sys
            sys.path.insert(0, 'src/python')
            from prometheus_physics import PhysicsIdentifier
            pi = PhysicsIdentifier()
            result = pi.identify(text)
            if result:
                node = MeaningNode(
                    id="physics_result",
                    type="rule",
                    label=result.get('law', str(result)),
                    content=str(result),
                    evidence="Physics Engine",
                    confidence=1.0,
                    metadata={"source": "solver", "trust": "high"}
                )
                graph.add_node(node)
        except:
            pass


class SearchBridge:
    """Fallback deeper context when ACES doesn't have enough information.
    
    Uses AXIMA BRAIN (if available) or basic knowledge lookup
    to add more context to the explanation.
    """

    def enrich(self, graph: MeaningGraph, inp: NormalizedInput,
               decision: RouterDecision) -> MeaningGraph:
        """Add external knowledge to the graph."""
        if not decision.needs_search:
            return graph

        # Try AXIMA BRAIN
        self._search_brain(graph, inp.clean)

        return graph

    def _search_brain(self, graph: MeaningGraph, query: str):
        """Search AXIMA BRAIN for relevant knowledge."""
        try:
            import sys
            sys.path.insert(0, 'src/python')
            from brain_ingest import DocumentBrain

            brain = DocumentBrain()
            results = brain.search(query, top_k=3)

            for i, chunk in enumerate(results):
                node = MeaningNode(
                    id=f"search_{i}",
                    type="concept",
                    label=chunk.text[:80],
                    content=chunk.text,
                    evidence=f"Source: {chunk.source}",
                    confidence=0.7,
                    metadata={"source": "brain_search"}
                )
                graph.add_node(node)
        except:
            pass  # Brain not available


class MultiStepProcessor:
    """Process multi-sentence answers into chained explanations.
    
    Splits complex text into individual claims,
    detects relationships between them, and builds a teaching chain.
    """

    def process(self, text: str, graph: MeaningGraph) -> MeaningGraph:
        """Split complex text into a multi-step explanation graph."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

        if len(sentences) <= 1:
            return graph

        prev_id = None
        for i, sent in enumerate(sentences):
            # Detect role of this sentence
            role = self._detect_role(sent)

            node = MeaningNode(
                id=f"multi_{i}",
                type="step" if role == "step" else "concept",
                label=sent[:80],
                content=sent,
                metadata={"role": role, "position": i}
            )
            graph.add_node(node)

            # Connect to previous
            if prev_id:
                relation = self._infer_relation(role)
                graph.add_edge(MeaningEdge(
                    source=prev_id, target=node.id, relation=relation
                ))

            prev_id = node.id

        return graph

    def _detect_role(self, sent: str) -> str:
        """Detect the role of a sentence in the explanation."""
        sl = sent.lower()

        if re.search(r'\b(?:first|begin|start|initially)\b', sl):
            return "opening"
        elif re.search(r'\b(?:then|next|after|subsequently)\b', sl):
            return "step"
        elif re.search(r'\b(?:because|since|due to|reason)\b', sl):
            return "cause"
        elif re.search(r'\b(?:therefore|so|thus|result|consequence)\b', sl):
            return "effect"
        elif re.search(r'\b(?:finally|conclude|summary|overall)\b', sl):
            return "conclusion"
        elif re.search(r'\b(?:however|but|although|despite)\b', sl):
            return "contrast"
        elif re.search(r'\b(?:for example|such as|like|instance)\b', sl):
            return "example"
        return "step"

    def _infer_relation(self, role: str) -> str:
        """Map sentence role to edge relation."""
        mapping = {
            "opening": "enables",
            "step": "enables",
            "cause": "causes",
            "effect": "causes",
            "conclusion": "enables",
            "contrast": "contradicts",
            "example": "part_of",
        }
        return mapping.get(role, "enables")
