"""Intent Lattice — multi-candidate intent detection replacing regex routing."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class IntentCandidate:
    """A candidate intent with confidence and metadata."""
    intent: str
    confidence: float
    engine: str
    cost: float = 1.0
    information_gain: float = 0.0


class IntentLattice:
    """A lattice of intent candidates ranked by confidence.

    Supports adding candidates, resolving the best match,
    and determining when clarification is needed.
    """

    def __init__(self) -> None:
        self._candidates: List[IntentCandidate] = []

    @property
    def candidates(self) -> List[IntentCandidate]:
        return sorted(self._candidates, key=lambda c: c.confidence, reverse=True)

    def add_candidate(self, candidate: IntentCandidate) -> None:
        """Add a candidate intent to the lattice."""
        self._candidates.append(candidate)

    def resolve(self) -> Optional[IntentCandidate]:
        """Resolve to the highest-confidence candidate.

        Returns None if clarification is needed.
        """
        if not self._candidates:
            return None
        if self.needs_clarification():
            return None
        return self.candidates[0]

    def get_top_k(self, k: int = 3) -> List[IntentCandidate]:
        """Get the top-k candidates by confidence."""
        return self.candidates[:k]

    def needs_clarification(self, threshold: float = 0.15) -> bool:
        """Determine if the top candidates are too close to distinguish.

        Returns True if the gap between #1 and #2 is less than threshold,
        indicating ambiguity that requires user clarification.
        """
        sorted_candidates = self.candidates
        if len(sorted_candidates) < 2:
            return False
        gap = sorted_candidates[0].confidence - sorted_candidates[1].confidence
        return gap < threshold


# Intent detection patterns (preserves and extends AXIMA's regex routing)
_INTENT_PATTERNS = {
    "math": {
        "patterns": [
            re.compile(r"\b(solve|calculate|compute|evaluate|simplify|factor|integrate|derive|differentiate)\b", re.I),
            re.compile(r"\b(equation|formula|expression|polynomial|matrix|vector)\b", re.I),
            re.compile(r"[\d]+\s*[+\-*/^=]\s*[\d]", re.I),
            re.compile(r"\b(sin|cos|tan|log|ln|sqrt|lim|sum|product)\b", re.I),
            re.compile(r"\b(factorial|gcd|lcm|prime|mod|modulo|remainder)\b", re.I),
            re.compile(r"\b(derivative|integral|calculus|limit|series|convergence)\b", re.I),
            re.compile(r"\b(algebra|arithmetic|geometry|trigonometry)\b", re.I),
            re.compile(r"\b(\d+\s*(factorial|!)|\d+\s*mod\s*\d+)\b", re.I),
        ],
        "engine": "prometheus_math",
        "cost": 1.0,
    },
    "physics": {
        "patterns": [
            re.compile(r"\b(force|velocity|acceleration|momentum|energy|gravity|mass)\b", re.I),
            re.compile(r"\b(newton|joule|watt|pascal|hertz|ohm|volt|ampere)\b", re.I),
            re.compile(r"\b(thermodynamics|quantum|relativity|optics|mechanics)\b", re.I),
        ],
        "engine": "prometheus_physics",
        "cost": 1.5,
    },
    "code": {
        "patterns": [
            re.compile(r"\b(write|code|implement|program|function|class|algorithm)\b", re.I),
            re.compile(r"\b(python|java|javascript|rust|cpp|go|typescript)\b", re.I),
            re.compile(r"\b(sort|search|tree|graph|linked list|hash|stack|queue)\b", re.I),
        ],
        "engine": "coder",
        "cost": 2.0,
    },
    "web": {
        "patterns": [
            re.compile(r"\b(website|web page|html|css|react|frontend|landing page)\b", re.I),
            re.compile(r"\b(responsive|animation|component|layout|navbar|footer)\b", re.I),
        ],
        "engine": "web_generator",
        "cost": 2.5,
    },
    "knowledge": {
        "patterns": [
            re.compile(r"\b(what is|who is|when did|where is|define|explain)\b", re.I),
            re.compile(r"\b(tell me about|describe|history of|meaning of)\b", re.I),
        ],
        "engine": "inference_engine",
        "cost": 0.5,
    },
    "creative": {
        "patterns": [
            re.compile(r"\b(write a (story|poem|song|essay)|compose|create a)\b", re.I),
            re.compile(r"\b(creative|fiction|narrative|lyrics|haiku)\b", re.I),
        ],
        "engine": "creator",
        "cost": 1.5,
    },
    "explanation": {
        "patterns": [
            re.compile(r"\b(explain|how does|why does|what causes|describe how)\b", re.I),
            re.compile(r"\b(step by step|breakdown|walkthrough)\b", re.I),
        ],
        "engine": "aces_v2",
        "cost": 1.0,
    },
}

# Structural patterns (query shape analysis)
_QUESTION_RE = re.compile(r"^(what|who|when|where|why|how|which|is|are|can|does|do)\b", re.I)
_COMMAND_RE = re.compile(r"^(write|create|build|make|generate|solve|calculate|find)\b", re.I)


class IntentDetector:
    """Detects intent from a query using regex patterns, keywords, and structure.

    Returns an IntentLattice with multiple ranked candidates,
    supporting mixed-intent queries and ambiguity detection.
    """

    def detect(self, query: str) -> IntentLattice:
        """Detect intents from a query string."""
        lattice = IntentLattice()
        query_lower = query.lower().strip()

        for intent_name, config in _INTENT_PATTERNS.items():
            confidence = self._compute_confidence(query_lower, config["patterns"])
            if confidence > 0.0:
                # Boost based on structural analysis
                confidence = self._apply_structural_boost(query, intent_name, confidence)
                lattice.add_candidate(IntentCandidate(
                    intent=intent_name,
                    confidence=min(1.0, confidence),
                    engine=config["engine"],
                    cost=config["cost"],
                    information_gain=self._estimate_info_gain(intent_name, confidence),
                ))

        # If no patterns matched, default to knowledge
        if not lattice.candidates:
            lattice.add_candidate(IntentCandidate(
                intent="knowledge",
                confidence=0.3,
                engine="inference_engine",
                cost=0.5,
                information_gain=0.5,
            ))

        return lattice

    def _compute_confidence(self, query: str, patterns: List[re.Pattern]) -> float:
        """Compute confidence from pattern matches."""
        matches = sum(1 for p in patterns if p.search(query))
        if matches == 0:
            return 0.0
        # Confidence scales with number of matching patterns
        return min(1.0, 0.3 + (matches / len(patterns)) * 0.7)

    def _apply_structural_boost(self, query: str, intent: str, base: float) -> float:
        """Apply confidence boost based on query structure."""
        boost = 0.0

        # Command-style queries boost action intents
        if _COMMAND_RE.match(query):
            if intent in ("code", "web", "creative", "math"):
                boost += 0.1

        # Question-style queries boost knowledge/explanation intents
        if _QUESTION_RE.match(query):
            if intent in ("knowledge", "explanation"):
                boost += 0.1

        # Numeric content boosts math/physics
        if re.search(r"\d", query):
            if intent in ("math", "physics"):
                boost += 0.05

        return base + boost

    def _estimate_info_gain(self, intent: str, confidence: float) -> float:
        """Estimate information gain from routing to this engine."""
        # Higher confidence = higher expected info gain
        base_gain = {
            "math": 0.9,
            "physics": 0.85,
            "code": 0.8,
            "web": 0.75,
            "knowledge": 0.7,
            "creative": 0.6,
            "explanation": 0.75,
        }
        return base_gain.get(intent, 0.5) * confidence
