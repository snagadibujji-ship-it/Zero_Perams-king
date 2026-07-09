"""Multi-path reasoning: generates 3 approaches, scores each, picks the best."""

import re
from dataclasses import dataclass, field


@dataclass
class ReasoningPath:
    name: str
    approach: str
    answer: str
    scores: dict = field(default_factory=dict)

    @property
    def total_score(self) -> float:
        return sum(self.scores.values())


class MultiPathReasoner:
    """Generates 3 reasoning paths for a question and selects the best."""

    def reason(self, question: str, knowledge_answer: str) -> ReasoningPath:
        """Generate 3 paths, score each, return the best."""
        paths = self._generate_paths(question, knowledge_answer)
        for path in paths:
            path.scores = self._score(path, question, knowledge_answer)
        paths.sort(key=lambda p: p.total_score, reverse=True)
        return paths[0]

    def _generate_paths(self, question: str, knowledge_answer: str) -> list:
        path_a = ReasoningPath(
            name="Factual",
            approach="Direct knowledge graph answer",
            answer=knowledge_answer.strip(),
        )
        path_b = ReasoningPath(
            name="Causal",
            approach="Cause-effect explanation",
            answer=self._causal(question, knowledge_answer),
        )
        path_c = ReasoningPath(
            name="Analogical",
            approach="Explanation by comparison",
            answer=self._analogical(question, knowledge_answer),
        )
        return [path_a, path_b, path_c]

    def _causal(self, question: str, knowledge: str) -> str:
        q_lower = question.lower()
        if any(w in q_lower for w in ("why", "how", "cause", "reason")):
            return f"This occurs because: {knowledge} — the underlying cause relates to the mechanisms described."
        return f"The reason is: {knowledge} — this follows from cause-effect relationships in the domain."

    def _analogical(self, question: str, knowledge: str) -> str:
        return f"Think of it like this: just as related systems behave predictably, {knowledge.lower()} Similarly, this pattern applies here."

    def _score(self, path: ReasoningPath, question: str, knowledge: str) -> dict:
        answer = path.answer
        specificity = 0.2 if re.search(r'\d+|[A-Z][a-z]+(?:\s[A-Z][a-z]+)', answer) else 0.0
        q_words = set(question.lower().split())
        a_words = set(answer.lower().split())
        overlap = len(q_words & a_words) / max(len(q_words), 1)
        completeness = min(0.3, overlap * 0.6 + (0.15 if len(answer) > 20 else 0.0))
        k_words = set(knowledge.lower().split())
        k_overlap = len(k_words & a_words) / max(len(k_words), 1)
        confidence = min(0.3, k_overlap * 0.4)
        extra_words = a_words - k_words - q_words
        novelty = min(0.2, len(extra_words) * 0.02)
        return {
            "specificity": round(specificity, 3),
            "completeness": round(completeness, 3),
            "confidence": round(confidence, 3),
            "novelty": round(novelty, 3),
        }

    def combine_paths(self, paths: list) -> str:
        """Take best elements from all 3 paths into one combined answer."""
        paths_sorted = sorted(paths, key=lambda p: p.total_score, reverse=True)
        best = paths_sorted[0]
        additions = []
        for p in paths_sorted[1:]:
            extra = set(p.answer.lower().split()) - set(best.answer.lower().split())
            if extra and p.scores.get("novelty", 0) > 0.05:
                # Extract a short novel snippet
                words = p.answer.split()
                snippet = " ".join(words[:12]) + ("..." if len(words) > 12 else "")
                additions.append(snippet)
        combined = best.answer
        if additions:
            combined += " Additionally: " + "; ".join(additions)
        return combined

    def explain_reasoning(self, question: str, paths: list) -> str:
        """Show which path was chosen and why (for /debug command)."""
        paths_sorted = sorted(paths, key=lambda p: p.total_score, reverse=True)
        lines = [f"Question: {question}", f"Winner: PATH {paths_sorted[0].name} (score={paths_sorted[0].total_score:.3f})", ""]
        for i, p in enumerate(paths_sorted):
            marker = "→ " if i == 0 else "  "
            lines.append(f"{marker}[{p.name}] score={p.total_score:.3f} | {p.scores}")
            lines.append(f"   {p.answer[:80]}{'...' if len(p.answer) > 80 else ''}")
        lines.append(f"\nRationale: {paths_sorted[0].name} path scored highest due to "
                     f"{max(paths_sorted[0].scores, key=paths_sorted[0].scores.get)} strength.")
        return "\n".join(lines)


# ─── Standalone Test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    reasoner = MultiPathReasoner()

    question = "Why does Python use GIL?"
    knowledge = "Python's GIL (Global Interpreter Lock) ensures only 1 thread executes bytecode at a time, simplifying memory management."

    # Test reason()
    best = reasoner.reason(question, knowledge)
    assert best.total_score > 0, "Best path should have positive score"
    assert best.name in ("Factual", "Causal", "Analogical")
    print(f"✓ reason() → Best path: {best.name} (score={best.total_score:.3f})")
    print(f"  Answer: {best.answer[:100]}")

    # Test all paths generation and scoring
    paths = reasoner._generate_paths(question, knowledge)
    for p in paths:
        p.scores = reasoner._score(p, question, knowledge)
    assert len(paths) == 3, "Should generate exactly 3 paths"
    print(f"✓ Generated 3 paths: {[p.name for p in paths]}")

    # Test combine_paths()
    combined = reasoner.combine_paths(paths)
    assert len(combined) > len(knowledge) * 0.5, "Combined should have substance"
    print(f"✓ combine_paths() → {combined[:100]}...")

    # Test explain_reasoning()
    explanation = reasoner.explain_reasoning(question, paths)
    assert "Winner:" in explanation
    assert "Rationale:" in explanation
    print(f"✓ explain_reasoning() output:\n{explanation}")

    print("\n✅ All tests passed!")
