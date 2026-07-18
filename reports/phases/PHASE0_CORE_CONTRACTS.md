# AXIMA Core Contracts — Phase 0.5

**Date:** 2026-07-17  
**Implementation:** `src/python/core/__init__.py`

---

## Philosophy

Every engine is a **Plugin**. Every answer is a **Result**. Every query has a **Context**.

No engine-specific hacks. One protocol for all. The router doesn't know what engines exist — it asks each one "can you handle this?" and picks the best.

---

## Contract 1: Plugin

```python
class Plugin(ABC):
    @property
    def name(self) -> str: ...          # "math", "physics", etc.
    @property
    def version(self) -> str: ...       # "1.0.0"
    @property
    def capabilities(self) -> Set[str]: ...  # {"solve_equation", "differentiate"}

    def can_handle(self, context: Context) -> float:
        """0.0 = cannot, 1.0 = definitely can."""

    def process(self, context: Context) -> Result:
        """Process query. Never raises to caller."""

    def initialize(self) -> bool: ...   # Optional startup
    def shutdown(self): ...             # Optional cleanup
    def health(self) -> Dict: ...       # Optional self-diagnostic
```

### Migration Path

Current engines return `Optional[str]`. Migration to Plugin contract:

1. Wrap existing engine in a Plugin adapter class
2. `can_handle` = current regex logic (from `_looks_like_math`, etc.)
3. `process` = current `_try_*` method, returning Result instead of str
4. Register in PluginRegistry
5. Router calls `registry.route(context)` instead of hardcoded if/elif

---

## Contract 2: Result

```python
@dataclass
class Result:
    status: ResultStatus    # success | partial | no_answer | error | unsupported
    answer: str             # The answer text
    confidence: float       # 0.0 to 1.0
    engine: str             # Which engine produced this
    truth_level: TruthLevel # direct_fact | derived | heuristic | template
    source_facts: List[str] # What data backed the answer
    latency_ms: float
    steps: List[str]        # Reasoning steps
    error_type: str         # If error
    error_message: str
    recovery_hint: str
```

Replaces the current `Optional[str]` returns. An engine that can't answer returns `Result(status=NO_ANSWER)` instead of `None`. An engine that errors returns `Result(status=ERROR, error_message="...")` instead of silently passing.

---

## Contract 3: Context

```python
@dataclass
class Context:
    query: str              # Original input
    normalized_query: str   # English version
    intent: str             # "calculate", "explain", etc.
    language: str           # "en", "te", "hi", etc.
    session_id: str
    turn_number: int
    history: List[str]      # Recent queries
    active_goals: List[str] # GoalRef IDs
    relevant_memories: List[str]  # MemoryRef IDs
    mode: str               # "deep", "one-line", etc.
    max_latency_ms: float   # Budget
```

Context flows through the entire pipeline. Each engine can read it to make better decisions. History enables continuity. Goals enable priority. Memory enables learning.

---

## Contract 4: MemoryReference

```python
@dataclass
class MemoryReference:
    id: str
    content: str
    memory_type: str    # fact | correction | observation | learned
    source: str
    confidence: float
    created_at: float
    accessed_count: int
    tags: List[str]
```

Points to knowledge stored in the reality graph. Used by engines to recall past interactions, corrections, and learned facts.

---

## Contract 5: GoalReference

```python
@dataclass
class GoalReference:
    id: str
    title: str
    status: GoalStatus  # active | blocked | completed | abandoned
    parent_id: str      # None = top-level goal
    priority: int
    progress: float     # 0.0 to 1.0
    blockers: List[str]
    children: List[str]
```

Points to goals in the goal system. Enables AXIMA to know what it's working on, what's blocked, and what's done.

---

## Contract 6: PluginRegistry

```python
class PluginRegistry:
    def register(plugin: Plugin): ...
    def route(context: Context) -> [(Plugin, confidence)]: ...
    def health_check() -> Dict: ...
```

Discovery-based routing. No hardcoded engine selection. The router asks all registered plugins "can you handle this?" and picks the most confident.

---

## Routing: Current vs Future

### Current (Phase 0.4)
```
if _looks_like_math(query):    → try math
elif _looks_like_physics(query): → try physics
else:                           → try inference → aces
```

### Future (Post-migration)
```
for plugin, confidence in registry.route(context):
    result = plugin.process(context)
    if result.succeeded:
        return result
# All plugins failed → ACES fallback
```

---

## Status

| Contract | Implemented | In Use |
|----------|-------------|--------|
| Plugin | ✅ | Not yet (engines not migrated) |
| Result | ✅ | Not yet (axima.py still uses str) |
| Context | ✅ | Not yet |
| MemoryReference | ✅ | Pending reality graph |
| GoalReference | ✅ | Pending goal system |
| PluginRegistry | ✅ | Not yet |

**Next:** Migrate one engine (math) as proof of concept in Phase 1.
