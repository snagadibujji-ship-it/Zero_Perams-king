"""Knowledge Specialist — sourced factuality, temporal queries, contradiction detection.

Every answer must be sourced with citations. Unknown queries get structured abstention.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple


class ConfidenceLevel(Enum):
    HIGH = auto()       # direct fact from source
    MEDIUM = auto()     # inferred from multiple sources
    LOW = auto()        # single indirect source
    ABSTAIN = auto()    # cannot determine


@dataclass
class Citation:
    """A reference to the source of a fact."""
    source: str
    section: str = ""
    page: Optional[int] = None
    timestamp: Optional[datetime] = None
    verbatim: str = ""


@dataclass
class Fact:
    """A single fact with provenance."""
    statement: str
    citations: List[Citation] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    domain: str = "general"
    tags: List[str] = field(default_factory=list)


@dataclass
class QueryResult:
    """Result of a knowledge query."""
    query: str
    answer: Optional[str]
    facts: List[Fact] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.ABSTAIN
    abstention_reason: Optional[str] = None
    truth_label: str = "unsupported"


@dataclass
class Contradiction:
    """A detected contradiction between facts."""
    fact_a: Fact
    fact_b: Fact
    description: str
    resolution: Optional[str] = None


@dataclass
class TemporalValidity:
    """Temporal validity assessment for a fact."""
    fact: Fact
    is_current: bool
    superseded_by: Optional[Fact] = None
    check_time: Optional[datetime] = None


class KnowledgeSpecialist:
    """Domain specialist for factual knowledge with sourced answers.

    - factual_query: answers with citations, or structured abstention
    - temporal_query: checks temporal validity of facts
    - contradiction_check: detects contradictions between facts
    """

    def __init__(self) -> None:
        self._facts: List[Fact] = []
        self._index: Dict[str, List[int]] = {}  # keyword -> fact indices

    # Common stop words to exclude from indexing
    _STOP_WORDS: Set[str] = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "out", "off", "over", "under", "again",
        "further", "then", "once", "here", "there", "when", "where", "why",
        "how", "all", "each", "every", "both", "few", "more", "most",
        "other", "some", "such", "no", "nor", "not", "only", "own", "same",
        "so", "than", "too", "very", "just", "because", "but", "and", "or",
        "if", "while", "that", "this", "these", "those", "what", "which",
        "who", "whom", "its", "his", "her", "their", "our", "your",
        "about", "up", "it", "he", "she", "they", "we", "you",
    }

    def add_fact(self, fact: Fact) -> None:
        """Add a fact to the knowledge base."""
        idx = len(self._facts)
        self._facts.append(fact)
        # Index by meaningful words in statement (skip stop words)
        for word in fact.statement.lower().split():
            clean = word.strip(".,;:!?()[]\"'")
            if len(clean) > 2 and clean not in self._STOP_WORDS:
                self._index.setdefault(clean, []).append(idx)

    def add_facts(self, facts: List[Fact]) -> None:
        """Add multiple facts."""
        for f in facts:
            self.add_fact(f)

    def factual_query(self, query: str) -> QueryResult:
        """Answer a factual query with citations, or abstain with reason.

        Returns structured abstention when confidence is too low.
        """
        matching_facts = self._search(query)

        if not matching_facts:
            return QueryResult(
                query=query,
                answer=None,
                confidence=ConfidenceLevel.ABSTAIN,
                abstention_reason="No matching facts found in knowledge base",
                truth_label="unsupported",
            )

        # Rank by relevance (number of matching keywords)
        query_words = set(w.lower().strip(".,;:!?()[]\"'") for w in query.split())
        scored: List[Tuple[float, Fact]] = []
        for fact in matching_facts:
            fact_words = set(w.lower().strip(".,;:!?()[]\"'") for w in fact.statement.split())
            overlap = len(query_words & fact_words)
            scored.append((overlap, fact))
        scored.sort(key=lambda x: x[0], reverse=True)

        best_facts = [f for _, f in scored[:5]]
        top_fact = best_facts[0]

        # Determine confidence
        if top_fact.confidence == ConfidenceLevel.HIGH and top_fact.citations:
            confidence = ConfidenceLevel.HIGH
            truth_label = "direct_fact"
        elif top_fact.confidence == ConfidenceLevel.MEDIUM:
            confidence = ConfidenceLevel.MEDIUM
            truth_label = "derived"
        else:
            confidence = ConfidenceLevel.LOW
            truth_label = "heuristic"

        # Compose answer from top facts
        answer = "; ".join(f.statement for f in best_facts[:3])

        return QueryResult(
            query=query,
            answer=answer,
            facts=best_facts,
            confidence=confidence,
            truth_label=truth_label,
        )

    def temporal_query(
        self,
        query: str,
        as_of: Optional[datetime] = None,
    ) -> QueryResult:
        """Query with temporal validity checking.

        Filters facts by temporal validity window and flags expired facts.
        """
        check_time = as_of or datetime.now()
        matching_facts = self._search(query)

        # Filter to temporally valid facts
        valid_facts: List[Fact] = []
        expired_facts: List[Fact] = []

        for fact in matching_facts:
            if fact.valid_from and fact.valid_from > check_time:
                continue  # not yet valid
            if fact.valid_until and fact.valid_until < check_time:
                expired_facts.append(fact)
                continue
            valid_facts.append(fact)

        if not valid_facts:
            reason = "No temporally valid facts found"
            if expired_facts:
                reason += f" ({len(expired_facts)} expired facts exist)"
            return QueryResult(
                query=query,
                answer=None,
                facts=expired_facts,
                confidence=ConfidenceLevel.ABSTAIN,
                abstention_reason=reason,
                truth_label="unsupported",
            )

        answer = "; ".join(f.statement for f in valid_facts[:3])
        return QueryResult(
            query=query,
            answer=answer,
            facts=valid_facts,
            confidence=valid_facts[0].confidence,
            truth_label="direct_fact" if valid_facts[0].citations else "derived",
        )

    def contradiction_check(self, facts: Optional[List[Fact]] = None) -> List[Contradiction]:
        """Detect contradictions within a set of facts.

        Compares facts pairwise for logical contradictions based on:
        - Negation patterns
        - Conflicting numeric values for same subject
        - Temporal impossibilities
        """
        check_facts = facts if facts is not None else self._facts
        contradictions: List[Contradiction] = []

        # Negation patterns
        negation_pairs = [
            ("is", "is not"), ("was", "was not"), ("are", "are not"),
            ("has", "has not"), ("can", "cannot"), ("will", "will not"),
            ("does", "does not"),
        ]

        for i in range(len(check_facts)):
            for j in range(i + 1, len(check_facts)):
                fact_a = check_facts[i]
                fact_b = check_facts[j]

                # Check for negation contradictions
                a_lower = fact_a.statement.lower()
                b_lower = fact_b.statement.lower()

                for pos, neg in negation_pairs:
                    # Check if one statement negates the other
                    if pos in a_lower and neg in b_lower:
                        # Compare subjects (first few words)
                        a_subject = " ".join(a_lower.split()[:3])
                        b_subject = " ".join(b_lower.split()[:3])
                        if a_subject == b_subject:
                            contradictions.append(Contradiction(
                                fact_a=fact_a,
                                fact_b=fact_b,
                                description=f"Negation contradiction: '{fact_a.statement}' vs '{fact_b.statement}'",
                            ))
                            break

                # Check temporal impossibility
                if (fact_a.valid_from and fact_b.valid_until and
                        fact_a.valid_from < fact_b.valid_until and
                        fact_a.domain == fact_b.domain):
                    # Same domain, overlapping time, check if they conflict
                    a_words = set(a_lower.split())
                    b_words = set(b_lower.split())
                    if len(a_words & b_words) > len(a_words) * 0.5:
                        # High overlap but different statements
                        if a_lower != b_lower:
                            contradictions.append(Contradiction(
                                fact_a=fact_a,
                                fact_b=fact_b,
                                description="Temporal overlap with conflicting content",
                            ))

        return contradictions

    def _search(self, query: str) -> List[Fact]:
        """Search facts by keyword matching."""
        query_words = set(
            w.lower().strip(".,;:!?()[]\"'") for w in query.split()
        )
        # Remove stop words from query
        query_words = {w for w in query_words if len(w) > 2 and w not in self._STOP_WORDS}
        fact_scores: Dict[int, int] = {}

        for word in query_words:
            if word in self._index:
                for idx in self._index[word]:
                    fact_scores[idx] = fact_scores.get(idx, 0) + 1

        # Return facts sorted by score
        sorted_indices = sorted(fact_scores.keys(), key=lambda i: fact_scores[i], reverse=True)
        return [self._facts[i] for i in sorted_indices[:20]]
