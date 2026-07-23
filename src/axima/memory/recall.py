"""Memory recall system — evidence-based retrieval across memory planes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .four_plane import FourPlaneMemory, MemoryEntry


@dataclass
class RecallRequest:
    """A structured request to recall from memory."""
    query: str
    memory_planes: List[str] = field(default_factory=lambda: ["episodic", "semantic", "procedural"])
    max_results: int = 10
    min_relevance: float = 0.0
    max_age: Optional[timedelta] = None


@dataclass
class RecallResult:
    """Result of a memory recall operation."""
    items: List[MemoryEntry] = field(default_factory=list)
    relevance_scores: List[float] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    staleness: List[float] = field(default_factory=list)


class MemoryRecaller:
    """Recalls memories with evidence and relevance scoring.

    Returns evidence and relevance, not just text similarity.
    """

    def __init__(self, memory: FourPlaneMemory) -> None:
        self._memory = memory

    def _compute_relevance(self, query: str, entry: MemoryEntry) -> float:
        """Compute relevance score for an entry against a query."""
        content_str = str(entry.content).lower()
        query_lower = query.lower()
        query_terms = query_lower.split()

        if not query_terms:
            return 0.0

        # Term overlap scoring
        matches = sum(1 for term in query_terms if term in content_str)
        score = matches / len(query_terms)

        # Exact match bonus
        if query_lower in content_str:
            score = min(1.0, score + 0.3)

        # Tag bonus
        for tag in entry.tags:
            if any(term in tag.lower() for term in query_terms):
                score = min(1.0, score + 0.1)

        return score

    def _compute_staleness(self, entry: MemoryEntry) -> float:
        """Compute staleness (0.0 = fresh, 1.0 = very stale)."""
        now = datetime.now(timezone.utc)
        age = now - entry.created_at
        # Staleness grows over 30 days to 1.0
        days = age.total_seconds() / 86400
        return min(1.0, days / 30.0)

    def recall(self, request: RecallRequest) -> RecallResult:
        """Execute a recall request across memory planes."""
        candidates: List[MemoryEntry] = []

        # Gather candidates from requested planes
        candidates = self._memory.recall(request.query, request.memory_planes)

        # Filter by max_age
        if request.max_age is not None:
            cutoff = datetime.now(timezone.utc) - request.max_age
            candidates = [e for e in candidates if e.created_at >= cutoff]

        # Score and sort
        scored: List[tuple] = []
        for entry in candidates:
            relevance = self._compute_relevance(request.query, entry)
            if relevance >= request.min_relevance:
                staleness = self._compute_staleness(entry)
                scored.append((entry, relevance, staleness))

        # Sort by relevance descending
        scored.sort(key=lambda x: x[1], reverse=True)

        # Limit results
        scored = scored[: request.max_results]

        # Build result
        result = RecallResult(
            items=[s[0] for s in scored],
            relevance_scores=[s[1] for s in scored],
            evidence=[f"matched query '{request.query}' in {s[0].schema}" for s in scored],
            staleness=[s[2] for s in scored],
        )
        return result
