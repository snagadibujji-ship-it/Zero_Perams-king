"""
AXIMA BRAIN — Module 4: Knowledge Tracker
Built by: Ghias + Kiro

Tracks what user knows vs doesn't know.
Implements scientific spaced repetition (forgetting curve).
Suggests what to study next.
"""

import json
import os
import time
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ConceptState:
    """Tracks user's knowledge of a single concept."""
    concept: str
    strength: float = 0.0         # 0-1 how well user knows this
    last_reviewed: float = 0.0    # timestamp of last review
    times_correct: int = 0        # total correct answers
    times_wrong: int = 0          # total wrong answers
    tau: float = 86400.0          # forgetting time constant (seconds) — starts at 1 day
    next_review: float = 0.0      # when to review next


class KnowledgeTracker:
    """Track what user knows, implement spaced repetition."""

    def __init__(self, filepath: str = "user_data/brain/tracker.json"):
        self.filepath = filepath
        self.concepts: Dict[str, ConceptState] = {}
        self._load()

    # ──────────────────────────────────────────────────────────────
    # PUBLIC API
    # ──────────────────────────────────────────────────────────────

    def record_correct(self, concept: str):
        """User answered correctly about this concept."""
        state = self._get_or_create(concept)
        state.times_correct += 1
        state.strength = min(1.0, state.strength + 0.2)
        state.last_reviewed = time.time()
        # Strengthen: slower forgetting next time
        state.tau *= 2.0  # double the retention time
        state.next_review = time.time() + state.tau
        self._save()

    def record_wrong(self, concept: str):
        """User answered incorrectly — needs more practice."""
        state = self._get_or_create(concept)
        state.times_wrong += 1
        state.strength = max(0.0, state.strength - 0.3)
        state.last_reviewed = time.time()
        # Weaken: faster review needed
        state.tau = max(3600.0, state.tau / 3)  # min 1 hour
        state.next_review = time.time() + state.tau
        self._save()

    def record_asked(self, concept: str):
        """User asked about this concept (shows interest)."""
        state = self._get_or_create(concept)
        state.last_reviewed = time.time()
        if state.strength == 0:
            state.strength = 0.1  # first exposure
        self._save()

    def get_strength(self, concept: str) -> float:
        """Get current knowledge strength (accounts for forgetting)."""
        state = self.concepts.get(concept.lower())
        if not state:
            return 0.0
        # Apply forgetting curve: S(t) = S₀ × e^(-t/τ)
        elapsed = time.time() - state.last_reviewed
        current = state.strength * math.exp(-elapsed / state.tau)
        return current

    def get_weak_concepts(self, threshold: float = 0.3) -> List[Tuple[str, float]]:
        """Find concepts user is weakest on (below threshold)."""
        weak = []
        for concept, state in self.concepts.items():
            current_strength = self.get_strength(concept)
            if current_strength < threshold and state.times_correct + state.times_wrong > 0:
                weak.append((concept, current_strength))
        return sorted(weak, key=lambda x: x[1])

    def get_due_for_review(self) -> List[str]:
        """Get concepts due for spaced repetition review NOW."""
        due = []
        now = time.time()
        for concept, state in self.concepts.items():
            if state.next_review > 0 and state.next_review <= now:
                due.append(concept)
        return due

    def get_never_studied(self, all_concepts: List[str]) -> List[str]:
        """Find concepts in material that user has never been tested on."""
        studied = set(self.concepts.keys())
        return [c for c in all_concepts if c.lower() not in studied]

    def get_study_plan(self, all_concepts: List[str], sessions: int = 5) -> List[List[str]]:
        """Generate a study plan prioritized by weakness + forgetting curve."""
        # Priority 1: Due for review (about to forget)
        due = self.get_due_for_review()
        # Priority 2: Weak concepts (got wrong before)
        weak = [c for c, _ in self.get_weak_concepts()]
        # Priority 3: Never studied
        never = self.get_never_studied(all_concepts)

        all_to_study = []
        seen = set()
        for c in due + weak + never:
            if c.lower() not in seen:
                seen.add(c.lower())
                all_to_study.append(c)

        # Split into sessions
        per_session = max(1, len(all_to_study) // sessions)
        plan = []
        for i in range(0, len(all_to_study), per_session):
            plan.append(all_to_study[i:i+per_session])

        return plan[:sessions]

    def get_stats(self) -> Dict:
        """Return user's learning statistics."""
        total = len(self.concepts)
        if total == 0:
            return {"total_concepts": 0}

        strengths = [self.get_strength(c) for c in self.concepts]
        strong = sum(1 for s in strengths if s > 0.7)
        medium = sum(1 for s in strengths if 0.3 <= s <= 0.7)
        weak = sum(1 for s in strengths if s < 0.3)

        total_correct = sum(s.times_correct for s in self.concepts.values())
        total_wrong = sum(s.times_wrong for s in self.concepts.values())

        return {
            "total_concepts": total,
            "strong": strong,
            "medium": medium,
            "weak": weak,
            "accuracy": total_correct / max(1, total_correct + total_wrong),
            "due_for_review": len(self.get_due_for_review()),
            "total_reviews": total_correct + total_wrong,
        }

    # ──────────────────────────────────────────────────────────────
    # INTERNAL
    # ──────────────────────────────────────────────────────────────

    def _get_or_create(self, concept: str) -> ConceptState:
        key = concept.lower()
        if key not in self.concepts:
            self.concepts[key] = ConceptState(concept=key)
        return self.concepts[key]

    def _save(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        data = {}
        for key, state in self.concepts.items():
            data[key] = {
                "strength": state.strength,
                "last_reviewed": state.last_reviewed,
                "times_correct": state.times_correct,
                "times_wrong": state.times_wrong,
                "tau": state.tau,
                "next_review": state.next_review,
            }
        with open(self.filepath, 'w') as f:
            json.dump(data, f)

    def _load(self):
        if not os.path.exists(self.filepath):
            return
        try:
            with open(self.filepath) as f:
                data = json.load(f)
            for key, d in data.items():
                self.concepts[key] = ConceptState(
                    concept=key,
                    strength=d.get("strength", 0),
                    last_reviewed=d.get("last_reviewed", 0),
                    times_correct=d.get("times_correct", 0),
                    times_wrong=d.get("times_wrong", 0),
                    tau=d.get("tau", 86400),
                    next_review=d.get("next_review", 0),
                )
        except:
            pass
