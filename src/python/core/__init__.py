"""
AXIMA Core Contracts — Interfaces that define the cognitive operating system.

Every engine, every result, every context must conform to these contracts.
No engine-specific hacks. One protocol for all.

Contracts:
    Plugin      — Any engine that can process queries
    Result      — Standard response from any engine
    Context     — Query context (session, history, user state)
    MemoryRef   — Reference to stored knowledge
    GoalRef     — Reference to active goal/task
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set
from enum import Enum, auto
import time


# ═══════════════════════════════════════════════════════════════
# RESULT CONTRACT — Every engine returns this
# ═══════════════════════════════════════════════════════════════

class ResultStatus(Enum):
    """Outcome of processing a query."""
    SUCCESS = "success"           # Engine produced a valid answer
    PARTIAL = "partial"           # Engine produced incomplete answer
    NO_ANSWER = "no_answer"       # Engine could not answer (not an error)
    ERROR = "error"               # Engine encountered an error
    UNSUPPORTED = "unsupported"   # Query type not supported by this engine


class TruthLevel(Enum):
    """How much to trust this result."""
    DIRECT_FACT = "direct_fact"   # Verbatim from knowledge base
    DERIVED = "derived"           # Computed/inferred (may be wrong)
    HEURISTIC = "heuristic"       # Best guess from patterns
    TEMPLATE = "template"         # Generated from fixed patterns
    UNSUPPORTED = "unsupported"   # No reliable answer possible


@dataclass
class Result:
    """Standard result from any AXIMA engine.
    
    Every engine must return a Result. No more Optional[str].
    """
    # Core
    status: ResultStatus = ResultStatus.NO_ANSWER
    answer: str = ""                    # The main answer text
    confidence: float = 0.0             # 0.0 to 1.0

    # Provenance
    engine: str = ""                    # Which engine produced this
    truth_level: TruthLevel = TruthLevel.HEURISTIC
    source_facts: List[str] = field(default_factory=list)  # What data backed this answer

    # Metadata
    latency_ms: float = 0.0
    steps: List[str] = field(default_factory=list)  # Reasoning/computation steps
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Error info (if status == ERROR)
    error_type: str = ""
    error_message: str = ""
    recovery_hint: str = ""

    @property
    def succeeded(self) -> bool:
        return self.status in (ResultStatus.SUCCESS, ResultStatus.PARTIAL)

    @property
    def has_answer(self) -> bool:
        return bool(self.answer.strip())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "answer": self.answer[:200],
            "confidence": self.confidence,
            "engine": self.engine,
            "truth_level": self.truth_level.value,
            "latency_ms": self.latency_ms,
        }


# ═══════════════════════════════════════════════════════════════
# CONTEXT CONTRACT — What the engine knows about the query
# ═══════════════════════════════════════════════════════════════

@dataclass
class Context:
    """Query context passed to every engine.
    
    Contains everything an engine might need to make decisions:
    session state, user preferences, history, active goals.
    """
    # Query
    query: str = ""                     # Original user input
    normalized_query: str = ""          # Cleaned/English version
    intent: str = "general"             # Detected intent
    language: str = "en"                # Detected language

    # Session
    session_id: str = ""                # Current session identifier
    turn_number: int = 0                # Which turn in this session
    history: List[str] = field(default_factory=list)  # Recent queries

    # User
    user_id: str = "default"
    preferences: Dict[str, Any] = field(default_factory=dict)

    # Goals (references to active goals)
    active_goals: List[str] = field(default_factory=list)  # GoalRef IDs

    # Memory (references to relevant memories)
    relevant_memories: List[str] = field(default_factory=list)  # MemoryRef IDs

    # Mode
    mode: str = "deep"                  # Explanation mode
    max_latency_ms: float = 5000.0      # Timeout budget

    def elapsed_budget(self, start_time: float) -> float:
        """How much of the latency budget has been used."""
        elapsed = (time.time() - start_time) * 1000
        return elapsed / max(self.max_latency_ms, 1)


# ═══════════════════════════════════════════════════════════════
# PLUGIN CONTRACT — Every engine implements this
# ═══════════════════════════════════════════════════════════════

class Plugin(ABC):
    """Base contract for all AXIMA engines (plugins).
    
    Every engine must implement:
      - name: unique identifier
      - can_handle: whether it can process this query
      - process: actually process the query
    
    Optional:
      - initialize: startup logic
      - shutdown: cleanup
      - health: self-diagnostic
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique engine identifier (e.g., 'math', 'physics', 'inference')."""
        ...

    @property
    def version(self) -> str:
        """Engine version string."""
        return "1.0.0"

    @property
    def capabilities(self) -> Set[str]:
        """What this engine can do (e.g., {'solve_equation', 'differentiate', 'integrate'})."""
        return set()

    @abstractmethod
    def can_handle(self, context: Context) -> float:
        """Return confidence (0.0-1.0) that this engine can handle the query.
        
        This replaces brittle regex routing. Each engine scores itself.
        Router picks the highest-confidence engine.
        
        Returns:
            0.0 = definitely cannot handle
            0.5 = might be able to handle
            1.0 = definitely can handle
        """
        ...

    @abstractmethod
    def process(self, context: Context) -> Result:
        """Process the query and return a Result.
        
        Must never raise exceptions to the caller.
        All errors should be caught and returned as Result(status=ERROR).
        """
        ...

    def initialize(self) -> bool:
        """Optional: Run startup logic (load data, warm caches).
        
        Returns True if initialization succeeded.
        """
        return True

    def shutdown(self):
        """Optional: Cleanup resources."""
        pass

    def health(self) -> Dict[str, Any]:
        """Optional: Self-diagnostic check.
        
        Returns dict with at minimum:
            {"healthy": True/False, "message": "..."}
        """
        return {"healthy": True, "engine": self.name}


# ═══════════════════════════════════════════════════════════════
# MEMORY REFERENCE — Pointer to stored knowledge
# ═══════════════════════════════════════════════════════════════

@dataclass
class MemoryReference:
    """Reference to a stored piece of knowledge in the reality graph.
    
    Memories are: facts learned, corrections received, patterns observed.
    """
    id: str                             # Unique identifier
    content: str                        # The memory content (text)
    memory_type: str = "fact"           # fact | correction | observation | learned
    source: str = ""                    # Where it came from
    confidence: float = 1.0             # How reliable
    created_at: float = 0.0             # Timestamp
    accessed_count: int = 0             # How often referenced
    tags: List[str] = field(default_factory=list)

    @property
    def is_stale(self) -> bool:
        """Memory older than 30 days with low access."""
        age_days = (time.time() - self.created_at) / 86400
        return age_days > 30 and self.accessed_count < 3


# ═══════════════════════════════════════════════════════════════
# GOAL REFERENCE — Pointer to active goal/task
# ═══════════════════════════════════════════════════════════════

class GoalStatus(Enum):
    """Status of a goal or task."""
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass
class GoalReference:
    """Reference to a goal or task in the goal system.
    
    Goals are hierarchical: Goal → Subgoal → Task.
    """
    id: str                             # Unique identifier
    title: str                          # What this goal is
    status: GoalStatus = GoalStatus.ACTIVE
    parent_id: Optional[str] = None     # Parent goal (None = top-level)
    priority: int = 0                   # Higher = more important
    progress: float = 0.0              # 0.0 to 1.0
    blockers: List[str] = field(default_factory=list)   # What's blocking
    children: List[str] = field(default_factory=list)   # Sub-goal/task IDs
    created_at: float = 0.0
    completed_at: float = 0.0

    @property
    def is_leaf(self) -> bool:
        """Is this a leaf task (no children)?"""
        return len(self.children) == 0


# ═══════════════════════════════════════════════════════════════
# PLUGIN REGISTRY — Discovery and management
# ═══════════════════════════════════════════════════════════════

class PluginRegistry:
    """Registry for all AXIMA plugins. Enables discovery-based routing."""

    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}

    def register(self, plugin: Plugin):
        """Register a plugin."""
        self._plugins[plugin.name] = plugin

    def unregister(self, name: str):
        """Remove a plugin."""
        self._plugins.pop(name, None)

    def get(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        return self._plugins.get(name)

    def all(self) -> List[Plugin]:
        """Get all registered plugins."""
        return list(self._plugins.values())

    def route(self, context: Context) -> List[tuple]:
        """Score all plugins and return sorted by confidence.
        
        Returns: [(plugin, confidence), ...] sorted highest first.
        """
        scored = []
        for plugin in self._plugins.values():
            try:
                confidence = plugin.can_handle(context)
                if confidence > 0:
                    scored.append((plugin, confidence))
            except Exception:
                continue
        scored.sort(key=lambda x: -x[1])
        return scored

    def health_check(self) -> Dict[str, Any]:
        """Run health check on all plugins."""
        results = {}
        for name, plugin in self._plugins.items():
            try:
                results[name] = plugin.health()
            except Exception as e:
                results[name] = {"healthy": False, "error": str(e)}
        return results
