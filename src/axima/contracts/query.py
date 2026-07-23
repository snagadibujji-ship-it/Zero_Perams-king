"""
AXIMA Core Contract Types
=========================

Defines the canonical data structures for queries, responses, and execution
results flowing through the unified cognitive runtime.

All types are pure dataclasses with no external dependencies.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TruthLevel(Enum):
    """Classification of how an answer was derived.

    Every response from AXIMA carries a truth level indicating the
    epistemic status of the answer.
    """

    DIRECT_FACT = "direct_fact"       # Found verbatim in knowledge base
    DERIVED = "derived"               # Inferred through reasoning rules (may be wrong)
    HEURISTIC = "heuristic"           # Best guess from pattern matching
    TEMPLATE = "template"             # Generated from structural patterns
    UNSUPPORTED = "unsupported"       # Could not find reliable answer


@dataclass
class ResourceBudgetSpec:
    """Resource constraints for query execution."""

    max_time_ms: float = 5000.0
    max_memory_mb: float = 256.0
    max_steps: int = 100
    max_depth: int = 10


@dataclass
class QueryEnvelope:
    """Complete specification of a query entering the system.

    Carries all context needed for routing, execution, and tracing.
    Immutable once created — all transforms produce new envelopes.
    """

    raw_input: str
    query_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[str] = None
    normalized_input: Optional[str] = None
    language_candidates: List[str] = field(default_factory=lambda: ["en"])
    source_spans: List[Dict[str, Any]] = field(default_factory=list)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    user_permissions: List[str] = field(default_factory=lambda: ["read"])
    requested_mode: str = "deep"
    deadline: Optional[float] = None  # Unix timestamp
    resource_budget: ResourceBudgetSpec = field(default_factory=ResourceBudgetSpec)
    created_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.normalized_input is None:
            self.normalized_input = self.raw_input.strip()
        if self.deadline is None:
            self.deadline = self.created_at + (self.resource_budget.max_time_ms / 1000.0)


@dataclass
class ExecutionResult:
    """Result from a single engine execution step."""

    answer: Optional[str] = None
    status: str = "success"  # success | error | timeout | cancelled
    claims: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    error: Optional[str] = None
    cost_ms: float = 0.0
    engine: str = "unknown"


@dataclass
class AximaResponseV2:
    """Canonical response from the unified cognitive runtime.

    Designed to be self-describing: every response explains what it knows,
    how it knows it, and what it doesn't know.
    """

    answer: str
    meaning_hash: str = ""
    truth_level: TruthLevel = TruthLevel.UNSUPPORTED
    calibrated_confidence: float = 0.0
    claims: List[str] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    derivation: List[str] = field(default_factory=list)
    caveats: List[str] = field(default_factory=list)
    unknowns: List[str] = field(default_factory=list)
    verification: Optional[str] = None
    trace_id: str = ""
    language: str = "en"
    mode: str = "deep"
    latency_ms: float = 0.0
    engine: str = "unknown"

    def __post_init__(self) -> None:
        if not self.meaning_hash and self.answer:
            self.meaning_hash = hashlib.sha256(self.answer.encode()).hexdigest()[:16]
        if not self.trace_id:
            self.trace_id = str(uuid.uuid4())
