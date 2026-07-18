# AXIMA Execution Coordinator - Documentation

## Purpose

The Execution Coordinator replaces isolated routing logic with a cooperative, discovery-based execution system. Instead of hardcoded if/elif routing that ties specific queries to specific plugins, the Coordinator asks all plugins "can you handle this?" and builds a dynamic execution plan.

The Coordinator handles:
- Plugin discovery and routing via PluginRegistry
- Execution order decisions (primary vs cooperative)
- Cooperative multi-plugin execution for complex queries
- Fallback chains when primary execution fails
- Result merging from multiple contributing engines

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Execution Coordinator                            │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Plugin Registry (discovery-based)                           │  │
│  │  - Registers all available plugins                           │  │
│  │  - Provides health checks and capabilities                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Execution Plan Builder                                      │  │
│  │  - Scores all plugins for given context                      │  │
│  │  - Identifies primary and cooperative candidates             │  │
│  │  - Builds fallback chain                                     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Safe Execution Layer                                        │  │
│  │  - Wraps plugin calls in try/except                          │  │
│  │  - Catches exceptions and converts to Result status          │  │
│  │  - Tracks latency per plugin                                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

**Key components:**
- `ExecutionCoordinator` class - Main orchestration engine
- `ExecutionStep` dataclass - Single step in execution plan (primary/cooperative/fallback)
- `ExecutionResult` dataclass - Combined result with all contributing engines

**Design patterns:**
- Registry pattern (PluginRegistry for discovery)
- Chain of Responsibility (fallback chain)
- Strategy pattern (different execution strategies)
- Guard clause pattern (safe execution wrapping)

## Key APIs

### `execute(context: Context) -> ExecutionResult`
Primary execution method. Takes a Context and returns an ExecutionResult with:
- `primary_result` - Result from the primary plugin
- `supplementary_results` - Results from cooperative plugins
- `execution_plan` - Detailed plan of which plugins were used and why
- `cooperating_engines` - List of engine names that contributed

**Execution flow:**
1. Score all plugins via PluginRegistry
2. Build execution plan (primary + cooperative + fallback)
3. Execute primary plugin
4. Execute cooperative plugins if primary succeeded
5. Execute fallback plugins if primary failed
6. Merge results and return

### `execute_specific(plugin_name: str, context: Context) -> Result`
Execute a specific plugin by name, bypassing routing. Returns a Result directly (not wrapped in ExecutionResult).

### `available_plugins() -> List[Dict[str, Any]]`
List all registered plugins with their current health status including:
- Name and version
- Capabilities list
- Health status (healthy/unhealthy)

### `register_plugin(plugin: Plugin)`
Register a new plugin for execution. Adds to the PluginRegistry for future routing decisions.

### `get_executor(registry: Optional[PluginRegistry] = None) -> ExecutionCoordinator`
Get the global ExecutionCoordinator singleton. Optionally pass a custom registry.

## Integration Points

### Input Dependencies

| Component | Purpose |
|-----------|---------|
| `PluginRegistry` | Plugin discovery, health checks, capability matching |
| `Context` | Input data including query, topic, session info |
| `Plugin` (interface) | All plugins must implement process(context) -> Result |

### Output Consumers

| Component | Uses |
|-----------|------|
| `Router` (legacy) | Replaced by ExecutionCoordinator |
| `Observer` | Records execution outcomes |
| `ReflectionEngine` | Analyzes plugin performance over time |

### Data Flow

```
Context → PluginRegistry.route() → Scored Plugins
                 ↓
    Execution Plan (primary/cooperative/fallback)
                 ↓
    Primary Plugin Execution
                 ↓
    Cooperative Plugins (if primary succeeded)
                 ↓
    Fallback Chain (if primary failed)
                 ↓
    ExecutionResult (merged results)
```

## Implementation Reference

**File:** `core/executor.py`  
**Lines:** 237  
**Primary Class:** `ExecutionCoordinator`

### Core Methods

```python
def execute(self, context: Context) -> ExecutionResult:
    start = time.time()
    # Score all plugins
    scored = self._registry.route(context)
    # Build execution plan
    plan = self._build_plan(scored)
    # Execute primary
    # Execute cooperative
    # Execute fallback if needed
    return ExecutionResult(...)

def _build_plan(self, scored: List[tuple]) -> List[ExecutionStep]:
    plan = []
    primary_set = False
    for plugin, confidence in scored:
        step = ExecutionStep(plugin_name=plugin.name, confidence=confidence)
        if not primary_set and confidence >= self._fallback_threshold:
            step.is_primary = True
            primary_set = True
        elif confidence >= self._cooperation_threshold:
            step.is_cooperative = True
        else:
            step.reason = "Fallback option"
        plan.append(step)
    return plan
```

### Configuration Thresholds

```python
self._cooperation_threshold = 0.6   # Min confidence for cooperative execution
self._fallback_threshold = 0.3      # Min confidence for fallback attempt
```

### Output Structures

```python
@dataclass
class ExecutionStep:
    plugin_name: str
    confidence: float = 0.0
    reason: str = ""
    is_primary: bool = False
    is_cooperative: bool = False

@dataclass
class ExecutionResult:
    primary_result: Optional[Result] = None
    supplementary_results: List[Result] = field(default_factory=list)
    execution_plan: List[ExecutionStep] = field(default_factory=list)
    total_latency_ms: float = 0.0
    cooperating_engines: List[str] = field(default_factory=list)

    def merged_answer(self) -> str:
        """Merge primary and supplementary results, avoiding duplicates."""
```

### Safe Execution Wrapper

```python
def _safe_execute(self, plugin: Plugin, context: Context) -> Result:
    try:
        start = time.time()
        result = plugin.process(context)
        result.latency_ms = (time.time() - start) * 1000
        result.engine = plugin.name
        return result
    except Exception as e:
        return Result(
            status=ResultStatus.ERROR,
            engine=plugin.name,
            error_type=type(e).__name__,
            error_message=str(e),
            recovery_hint="Plugin raised an exception",
        )
```

## Status

✅ **Production Ready**  
- 237 lines of code  
- PluginRegistry-based discovery routing (no hardcoded routing)  
- Cooperative execution for multi-plugin queries  
- Fallback chains for reliability  
- Safe execution wrapping with error recovery  
- Latency tracking per plugin  
- Health status reporting  

---

*Generated for AXIMA v6.0 - July 17, 2026*
