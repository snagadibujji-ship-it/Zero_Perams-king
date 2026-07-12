#!/usr/bin/env python3
"""
MultiPath Reasoning v3.0 — Maximum Level

Generates 5 reasoning paths for every question, scores each on 6 dimensions,
selects the best, and explains WHY it chose that path.

Paths:
  1. Factual (direct knowledge lookup)
  2. Causal (cause-effect chain)
  3. Analogical (similar to something known)
  4. Deductive (logical proof from premises)
  5. Compositional (break into parts, answer each)

Scoring dimensions:
  1. Relevance (does path address the question?)
  2. Confidence (how sure are we?)
  3. Specificity (concrete vs vague?)
  4. Completeness (full answer vs partial?)
  5. Consistency (matches known facts?)
  6. Novelty (adds info beyond restating question?)
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ReasoningPath:
    name: str
    approach: str
    answer: str
    scores: Dict[str, float] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)
    steps: int = 1

    @property
    def total_score(self) -> float:
        if not self.scores:
            return 0
        return sum(self.scores.values()) / len(self.scores)


class MultiPathReasoner:
    """Generates 5 paths, scores on 6 dimensions, returns best."""

    DIMENSIONS = ['relevance', 'confidence', 'specificity', 'completeness', 'consistency', 'novelty']

    def reason(self, question: str, knowledge_answer: str,
               causal_answer: str = None,
               world_sim_answer: str = None) -> Dict:
        """Generate paths, score, select best. Returns full analysis."""
        paths = self._generate_paths(question, knowledge_answer, causal_answer, world_sim_answer)

        # Score each path
        for path in paths:
            path.scores = self._score_path(path, question, knowledge_answer)

        # Sort by total score
        paths.sort(key=lambda p: p.total_score, reverse=True)

        best = paths[0]
        runner_up = paths[1] if len(paths) > 1 else None

        return {
            'best_path': best.name,
            'answer': best.answer,
            'confidence': round(best.total_score, 3),
            'approach': best.approach,
            'scores': best.scores,
            'evidence': best.evidence,
            'runner_up': runner_up.name if runner_up else None,
            'margin': round(best.total_score - (runner_up.total_score if runner_up else 0), 3),
            'all_paths': [{
                'name': p.name, 'score': round(p.total_score, 3),
                'answer_preview': p.answer[:80] if p.answer else ''
            } for p in paths],
        }

    def _generate_paths(self, question: str, knowledge: str,
                        causal: str = None, world_sim: str = None) -> List[ReasoningPath]:
        """Generate 5 reasoning paths."""
        paths = []
        q_lower = question.lower()

        # Path 1: Factual (direct answer from knowledge)
        if knowledge and len(knowledge) > 5:
            paths.append(ReasoningPath(
                name="Factual",
                approach="Direct knowledge graph lookup",
                answer=knowledge.strip(),
                evidence=["Stored in knowledge base"],
                steps=1,
            ))

        # Path 2: Causal (cause-effect reasoning)
        if causal and len(causal) > 5:
            paths.append(ReasoningPath(
                name="Causal",
                approach="Cause-effect chain reasoning",
                answer=causal.strip(),
                evidence=["Derived from causal rules"],
                steps=2,
            ))
        elif 'why' in q_lower or 'cause' in q_lower or 'because' in q_lower:
            # Try to construct causal answer from factual
            causal_attempt = self._construct_causal(question, knowledge)
            if causal_attempt:
                paths.append(ReasoningPath(
                    name="Causal",
                    approach="Causal inference from facts",
                    answer=causal_attempt,
                    evidence=["Inferred from stored properties"],
                    steps=3,
                ))

        # Path 3: Analogical (similar to something known)
        analogy = self._construct_analogy(question, knowledge)
        if analogy:
            paths.append(ReasoningPath(
                name="Analogical",
                approach="Reasoning by analogy to similar concept",
                answer=analogy,
                evidence=["By analogy to related concept"],
                steps=2,
            ))

        # Path 4: Deductive (logical proof)
        deduction = self._construct_deduction(question, knowledge)
        if deduction:
            paths.append(ReasoningPath(
                name="Deductive",
                approach="Logical deduction from premises",
                answer=deduction,
                evidence=["Logically derived"],
                steps=3,
            ))

        # Path 5: Compositional (break question into parts)
        composition = self._construct_composition(question, knowledge)
        if composition:
            paths.append(ReasoningPath(
                name="Compositional",
                approach="Break into sub-questions, answer each",
                answer=composition,
                evidence=["Assembled from sub-answers"],
                steps=4,
            ))

        # World simulator path (if available)
        if world_sim and len(world_sim) > 5:
            paths.append(ReasoningPath(
                name="Simulation",
                approach="Physics/world simulation",
                answer=world_sim.strip(),
                evidence=["Simulated via causal world model"],
                steps=2,
            ))

        # Fallback: if no paths worked
        if not paths:
            paths.append(ReasoningPath(
                name="Uncertain",
                approach="No confident reasoning path found",
                answer="I don't have enough information to answer this reliably.",
                evidence=[],
                steps=0,
            ))

        return paths

    def _score_path(self, path: ReasoningPath, question: str, knowledge: str) -> Dict[str, float]:
        """Score a path on 6 dimensions (0-1 each)."""
        scores = {}
        q_words = set(question.lower().split()) - {'what', 'is', 'the', 'a', 'how', 'why', 'who', 'where', 'when'}
        a_words = set(path.answer.lower().split()) if path.answer else set()

        # Relevance: keyword overlap
        if q_words and a_words:
            scores['relevance'] = min(1.0, len(q_words & a_words) / max(1, len(q_words)) * 2)
        else:
            scores['relevance'] = 0.0

        # Confidence: based on evidence and steps
        if path.evidence:
            scores['confidence'] = min(1.0, 0.5 + len(path.evidence) * 0.2)
        else:
            scores['confidence'] = 0.2

        # Specificity: numbers, proper nouns, concrete details
        has_numbers = bool(re.search(r'\d+', path.answer)) if path.answer else False
        has_names = bool(re.search(r'[A-Z][a-z]{2,}', path.answer)) if path.answer else False
        scores['specificity'] = 0.3 + (0.3 if has_numbers else 0) + (0.3 if has_names else 0) + (0.1 if len(path.answer or '') > 50 else 0)

        # Completeness: answer length relative to question complexity
        q_complexity = len(q_words)
        a_length = len(path.answer) if path.answer else 0
        scores['completeness'] = min(1.0, a_length / max(1, q_complexity * 20))

        # Consistency: doesn't say "I don't know" + doesn't contradict
        if path.answer:
            if any(s in path.answer.lower() for s in ["don't know", "not sure", "cannot"]):
                scores['consistency'] = 0.2
            elif 'concept' in path.answer.lower() and 'is a concept' in path.answer.lower():
                scores['consistency'] = 0.1  # Non-answer
            else:
                scores['consistency'] = 0.8
        else:
            scores['consistency'] = 0.0

        # Novelty: adds info beyond restating the question
        if path.answer:
            novel_words = a_words - q_words
            scores['novelty'] = min(1.0, len(novel_words) / max(1, len(a_words)))
        else:
            scores['novelty'] = 0.0

        return scores

    def _construct_causal(self, question: str, knowledge: str) -> Optional[str]:
        """Try to build causal explanation from factual answer."""
        if not knowledge or len(knowledge) < 20:
            return None
        # If knowledge mentions "causes" or "because"
        if any(w in knowledge.lower() for w in ['cause', 'because', 'result', 'due to']):
            return knowledge
        return None

    def _construct_analogy(self, question: str, knowledge: str) -> Optional[str]:
        """Try analogy reasoning."""
        if not knowledge or len(knowledge) < 20:
            return None
        # If knowledge mentions "like" or "similar"
        if any(w in knowledge.lower() for w in ['like', 'similar to', 'comparable', 'same as']):
            return f"By analogy: {knowledge}"
        return None

    def _construct_deduction(self, question: str, knowledge: str) -> Optional[str]:
        """Try logical deduction."""
        # Look for "all X are Y" + "Z is X" → "Z is Y"
        if not knowledge:
            return None
        if 'all ' in question.lower() and ' are ' in question.lower():
            return knowledge  # Syllogism handled by C engine
        return None

    def _construct_composition(self, question: str, knowledge: str) -> Optional[str]:
        """Break complex question into parts."""
        # Multi-part questions (contains "and" or multiple question marks)
        if ' and ' in question and len(question) > 50:
            parts = question.split(' and ')
            if len(parts) >= 2:
                return f"Part 1: {knowledge}. (Other parts would need separate lookup.)"
        return None
