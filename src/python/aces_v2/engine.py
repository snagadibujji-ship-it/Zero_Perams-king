"""
ACES v2 — Main Orchestrator
Runs the full pipeline: Input → Shield → Router → Parser → Graph → Skeleton → Planner → Renderer → Auditor
"""

from typing import Optional
from .models import (
    NormalizedInput, RouterDecision, MeaningGraph, ReasonChain,
    ExplanationPlan, ExplanationFrame, AuditReport, MemoryRecord
)


class ACESV2:
    """The ACES v2 Explanation Engine.
    
    Compiles meaning into a graph, derives a reason skeleton,
    and renders explanations in any human shape.
    """

    def __init__(self):
        # Pipeline stages — all wired up
        from .shield import InputShield
        from .router import Router
        from .parser import MeaningParser
        from .graph_builder import GraphBuilder
        from .reasoner import Reasoner
        from .renderer import Planner, Renderer
        from .auditor import Auditor
        from .memory import Memory

        self.shield = InputShield()
        self.router = Router()
        self.parser = MeaningParser()
        self.graph_builder = GraphBuilder()
        self.reasoner = Reasoner()
        self.planner = Planner()
        self.renderer = Renderer()
        self.auditor = Auditor()
        self.memory = Memory()
        self.solver_bridge = None   # Phase 11
        self.search_bridge = None   # Phase 12

    def explain(self, question: str, mode: str = "deep",
                context: Optional[str] = None) -> ExplanationFrame:
        """Main entry point: explain anything in any shape.
        
        Args:
            question: What to explain
            mode: Explanation format (one-line/bullets/steps/deep/expert/simple/teach/exam)
            context: Optional additional context
            
        Returns:
            ExplanationFrame with the rendered explanation
        """
        # Stage 1: Shield — normalize input
        normalized = self._shield(question)

        # Stage 2: Route — decide what kind of explanation
        decision = self._route(normalized, mode)

        # Stage 3: Parse — extract meaning structure
        graph = self._parse(normalized, decision)

        # Stage 4: Reason — derive the explanation skeleton
        chain = self._reason(graph, decision)

        # Stage 5: Plan — decide how to present
        plan = self._plan(chain, decision)

        # Stage 6: Render — produce the output
        frame = self._render(plan, chain, graph, decision)

        # Stage 7: Audit — check quality
        report = self._audit(frame, graph)

        # Stage 8: Memory — store for future use
        self._remember(normalized.clean, graph, chain, frame)

        return frame

    def _shield(self, raw: str) -> NormalizedInput:
        """Stage 1: Normalize input."""
        if self.shield:
            return self.shield.process(raw)
        # Fallback: minimal normalization
        clean = raw.strip()
        return NormalizedInput(raw=raw, clean=clean, tokens=clean.split())

    def _route(self, inp: NormalizedInput, requested_mode: str) -> RouterDecision:
        """Stage 2: Decide explanation type."""
        if self.router:
            return self.router.route(inp, requested_mode)
        # Fallback: use requested mode
        return RouterDecision(format_mode=requested_mode)

    def _parse(self, inp: NormalizedInput, decision: RouterDecision) -> MeaningGraph:
        """Stage 3: Extract meaning graph."""
        graph = self.parser.parse(inp, decision)
        # Enrich with graph builder
        graph = self.graph_builder.build(graph, decision)
        return graph

    def _reason(self, graph: MeaningGraph, decision: RouterDecision) -> ReasonChain:
        """Stage 4: Derive reason skeleton."""
        return self.reasoner.reason(graph, decision)

    def _plan(self, chain: ReasonChain, decision: RouterDecision) -> ExplanationPlan:
        """Stage 5: Plan the explanation structure."""
        return self.planner.plan(chain, decision)

    def _render(self, plan: ExplanationPlan, chain: ReasonChain,
                graph: MeaningGraph, decision: RouterDecision) -> ExplanationFrame:
        """Stage 6: Render into requested format."""
        return self.renderer.render(plan, chain, graph, decision)

    def _audit(self, frame: ExplanationFrame, graph: MeaningGraph) -> AuditReport:
        """Stage 7: Check quality."""
        return self.auditor.audit(frame, graph)

    def _remember(self, topic: str, graph: MeaningGraph,
                  chain: ReasonChain, frame: ExplanationFrame):
        """Stage 8: Store in memory."""
        self.memory.store(topic, graph, chain, frame)
