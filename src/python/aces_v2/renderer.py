"""
ACES v2 — Phase 7+8: Explanation Planner + Renderer
Plans the structure then renders into the requested format.
"""

from typing import List, Dict
from .models import (MeaningGraph, ReasonChain, RouterDecision,
                     ExplanationPlan, ExplanationFrame)


class Planner:
    """Decide how to structure the explanation."""

    def plan(self, chain: ReasonChain, decision: RouterDecision) -> ExplanationPlan:
        """Create an explanation plan from the reason chain."""
        plan = ExplanationPlan()

        # Decide opening strategy
        plan.start_with = self._choose_opening(decision)

        # Decide section order
        plan.section_order = self._order_sections(chain, decision)

        # Decide detail level per section
        plan.detail_level = self._assign_detail(plan.section_order, decision.depth)

        # Choose best analogy
        plan.analogy_choice = chain.analogies[0] if chain.analogies else ""

        # What to hide (too advanced for requested level)
        plan.hidden = self._decide_hidden(chain, decision)

        # Adaptation
        plan.adaptation = self._map_adaptation(decision.format_mode)

        return plan

    def _choose_opening(self, decision: RouterDecision) -> str:
        """How to start the explanation."""
        if decision.format_mode == "simple":
            return "analogy"
        elif decision.format_mode in ("expert", "exam"):
            return "definition"
        elif decision.question_type == "why":
            return "intuition"
        elif decision.question_type == "how":
            return "overview"
        elif decision.question_type == "derivation":
            return "formula"
        return "intuition"

    def _order_sections(self, chain: ReasonChain, decision: RouterDecision) -> List[str]:
        """Decide what order to present information."""
        sections = []

        if decision.format_mode == "teach":
            # Prerequisites → Core → Examples → Implications
            if chain.prerequisites:
                sections.append("prerequisites")
            sections.append("core")
            if chain.analogies:
                sections.append("analogy")
            sections.append("details")
            if chain.enables:
                sections.append("implications")
        elif decision.format_mode == "exam":
            # Definition → Key points → Formula → Warning
            sections.extend(["definition", "key_points", "formula", "common_mistakes"])
        elif decision.format_mode == "simple":
            # Analogy → Core → Summary
            sections.extend(["analogy", "core", "summary"])
        else:
            # Default: Intro → Chain → Insight
            sections.extend(["introduction", "explanation", "insight"])

        return sections

    def _assign_detail(self, sections: List[str], depth: int) -> Dict[str, int]:
        """How much detail per section."""
        detail = {}
        for section in sections:
            if section in ("prerequisites", "summary"):
                detail[section] = min(depth, 2)
            elif section in ("core", "explanation", "details"):
                detail[section] = depth
            else:
                detail[section] = max(1, depth - 1)
        return detail

    def _decide_hidden(self, chain: ReasonChain, decision: RouterDecision) -> List[str]:
        """What to omit based on depth/mode."""
        hidden = []
        if decision.depth <= 2:
            hidden.extend(chain.misconceptions)  # Hide for shallow explanations
        if decision.format_mode == "one-line":
            hidden.extend(chain.prerequisites)
            hidden.extend(chain.analogies)
        return hidden

    def _map_adaptation(self, mode: str) -> str:
        """Map format mode to adaptation style."""
        mapping = {
            "simple": "beginner",
            "expert": "technical",
            "teach": "teacher",
            "exam": "exam",
            "deep": "standard",
        }
        return mapping.get(mode, "standard")


class Renderer:
    """Render explanation plans into final text output."""

    def render(self, plan: ExplanationPlan, chain: ReasonChain,
               graph: MeaningGraph, decision: RouterDecision) -> ExplanationFrame:
        """Render the explanation in the requested format."""
        mode = decision.format_mode

        if mode == "one-line":
            return self._render_oneline(chain, graph)
        elif mode == "bullets":
            return self._render_bullets(chain, graph)
        elif mode == "steps":
            return self._render_steps(chain, graph)
        elif mode == "simple":
            return self._render_simple(chain, graph, plan)
        elif mode == "expert":
            return self._render_expert(chain, graph, plan)
        elif mode == "teach":
            return self._render_teach(chain, graph, plan)
        elif mode == "exam":
            return self._render_exam(chain, graph, plan)
        else:  # "deep" default
            return self._render_deep(chain, graph, plan)

    def _render_oneline(self, chain: ReasonChain, graph: MeaningGraph) -> ExplanationFrame:
        """Single sentence answer."""
        if chain.shortest_path:
            text = " → ".join(chain.shortest_path)
        elif chain.chain:
            text = chain.chain[0]
        else:
            text = graph.nodes[0].label if graph.nodes else ""
        return ExplanationFrame(mode="one-line", text=text)

    def _render_bullets(self, chain: ReasonChain, graph: MeaningGraph) -> ExplanationFrame:
        """Key points as bullet list."""
        lines = []
        for item in chain.chain:
            lines.append(f"• {item}")
        if chain.analogies:
            lines.append(f"\n💡 {chain.analogies[0]}")
        text = "\n".join(lines)
        return ExplanationFrame(mode="bullets", text=text)

    def _render_steps(self, chain: ReasonChain, graph: MeaningGraph) -> ExplanationFrame:
        """Ordered step-by-step."""
        lines = []
        for i, step in enumerate(chain.chain, 1):
            lines.append(f"{i}. {step}")
        text = "\n".join(lines)
        return ExplanationFrame(mode="steps", text=text)

    def _render_simple(self, chain: ReasonChain, graph: MeaningGraph,
                      plan: ExplanationPlan) -> ExplanationFrame:
        """Simple explanation (5th grader level)."""
        parts = []

        # Start with analogy if available
        if plan.analogy_choice:
            parts.append(plan.analogy_choice)

        # Core in simple terms
        if chain.chain:
            parts.append(chain.chain[0])
            if len(chain.chain) > 1:
                parts.append("So basically: " + chain.chain[-1])

        text = "\n\n".join(parts)
        return ExplanationFrame(mode="simple", text=text)

    def _render_expert(self, chain: ReasonChain, graph: MeaningGraph,
                      plan: ExplanationPlan) -> ExplanationFrame:
        """Technical expert explanation."""
        parts = []

        # Prerequisites (brief)
        if chain.prerequisites:
            parts.append("Prerequisites: " + ", ".join(chain.prerequisites))

        # Main chain (formal)
        for item in chain.chain:
            parts.append(item)

        # Formulas
        formulas = [n.label for n in graph.nodes if n.type == "formula"]
        if formulas:
            parts.append("\nFormulae: " + " ; ".join(formulas))

        # What it rules out
        if chain.rules_out:
            parts.append("Excludes: " + ", ".join(chain.rules_out))

        text = "\n".join(parts)
        return ExplanationFrame(mode="expert", text=text, formulas=formulas)

    def _render_teach(self, chain: ReasonChain, graph: MeaningGraph,
                     plan: ExplanationPlan) -> ExplanationFrame:
        """Teaching mode: build from foundations."""
        parts = []

        # Prerequisites
        if chain.prerequisites:
            parts.append("📚 Before we start:")
            for p in chain.prerequisites:
                parts.append(f"   • {p}")
            parts.append("")

        # Main explanation
        parts.append("📖 The explanation:")
        for i, item in enumerate(chain.chain, 1):
            parts.append(f"   {i}. {item}")
        parts.append("")

        # Analogy
        if chain.analogies:
            parts.append(f"💡 Think of it this way: {chain.analogies[0]}")
            parts.append("")

        # Common mistakes
        if chain.misconceptions:
            parts.append("⚠️ Watch out:")
            for m in chain.misconceptions:
                parts.append(f"   • {m}")
            parts.append("")

        # What you can now do
        if chain.enables:
            parts.append("✅ Now you can:")
            for e in chain.enables:
                parts.append(f"   • {e}")

        text = "\n".join(parts)
        return ExplanationFrame(mode="teach", text=text)

    def _render_exam(self, chain: ReasonChain, graph: MeaningGraph,
                    plan: ExplanationPlan) -> ExplanationFrame:
        """Exam preparation format."""
        parts = []

        # Definition
        if graph.nodes:
            parts.append(f"DEFINITION: {graph.nodes[0].label}")
            if graph.nodes[0].content != graph.nodes[0].label:
                parts.append(f"  = {graph.nodes[0].content}")
            parts.append("")

        # Key points
        parts.append("KEY POINTS:")
        for item in chain.chain[:5]:
            parts.append(f"  • {item}")
        parts.append("")

        # Formulas
        formulas = [n.label for n in graph.nodes if n.type == "formula"]
        if formulas:
            parts.append("FORMULAS:")
            for f in formulas:
                parts.append(f"  {f}")
            parts.append("")

        # Common mistakes
        if chain.misconceptions:
            parts.append("COMMON MISTAKES:")
            for m in chain.misconceptions:
                parts.append(f"  ✗ {m}")

        text = "\n".join(parts)
        return ExplanationFrame(mode="exam", text=text, formulas=formulas)

    def _render_deep(self, chain: ReasonChain, graph: MeaningGraph,
                    plan: ExplanationPlan) -> ExplanationFrame:
        """Full detailed explanation (default)."""
        parts = []

        # Opening
        if chain.chain:
            parts.append(chain.chain[0])
            parts.append("")

        # Full chain
        if len(chain.chain) > 1:
            for item in chain.chain[1:]:
                parts.append(f"→ {item}")
            parts.append("")

        # Analogy
        if chain.analogies:
            parts.append(f"Analogy: {chain.analogies[0]}")
            parts.append("")

        # Implications
        if chain.enables:
            parts.append("This means: " + "; ".join(chain.enables))

        # Misconceptions
        if chain.misconceptions:
            parts.append("\nNote: " + chain.misconceptions[0])

        text = "\n".join(parts)
        return ExplanationFrame(mode="deep", text=text, source_graph=graph)
