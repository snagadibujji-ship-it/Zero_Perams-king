# ADR-002: Microkernel Architecture

**Status:** Accepted  
**Date:** 2026-07-23  
**Deciders:** Gowtham Sangadi (Ghias)

## Context

The original AXIMA was a monolithic system: `axima.py` directly imported and called all engines with ad-hoc routing. This caused:

- Tight coupling (changing one engine broke others)
- No isolation (a crash in math solver crashed everything)
- No testability (couldn't test engines without the full system)
- No resource control (one engine could starve others)
- Growing complexity (281-line router with regex-based dispatch)

## Decision

**Adopt a microkernel architecture** where:
- A minimal kernel handles lifecycle, scheduling, and contract enforcement
- All domain logic lives in plugins with typed interfaces
- Communication happens exclusively through contracts (no shared mutable state)

## Why Microkernel Over Monolith

| Concern | Monolith | Microkernel |
|---------|----------|-------------|
| Fault isolation | One crash kills all | Plugin failure is contained |
| Testability | Need full system | Test plugins in isolation |
| Evolution | Change everything at once | Evolve plugins independently |
| Resource control | Hope for the best | Enforce budgets per-plugin |
| New capabilities | Edit the monolith | Add a plugin |
| Comprehension | Read 38,000 lines | Read one plugin at a time |

## Plugin Contract Model

Every plugin implements:

```python
class PluginInterface(Protocol):
    @property
    def name(self) -> str:
        """Unique plugin identifier."""

    @property
    def version(self) -> str:
        """Semver version string."""

    @property
    def capabilities(self) -> list[str]:
        """List of capability tokens this plugin requires."""

    def can_handle(self, envelope: QueryEnvelope) -> float:
        """Return 0.0–1.0 confidence that this plugin can handle the query."""

    def execute(self, envelope: QueryEnvelope) -> ExecutionResult:
        """Execute within the resource budget. Must respect deadline."""

    def health_check(self) -> bool:
        """Return True if plugin is operational."""
```

### Contract Guarantees

1. **Input:** Plugin receives a read-only `QueryEnvelope`
2. **Output:** Plugin returns an `ExecutionResult` (never raises to caller)
3. **Budget:** Plugin respects `resource_budget` and `deadline`
4. **Isolation:** Plugin cannot access other plugins' state
5. **Capabilities:** Plugin operates only within granted capabilities

### Plugin Lifecycle

```
REGISTERED → INITIALIZED → HEALTHY → ACTIVE → (UNHEALTHY | UNLOADED)
```

The kernel:
- Discovers plugins at startup
- Initializes them (dependency injection of config)
- Health-checks periodically
- Routes queries only to HEALTHY plugins
- Unloads plugins that fail health checks repeatedly

## Migration Strategy

The migration from monolith to microkernel preserves backward compatibility:

### Phase 1: Legacy Adapter (Complete)

`kernel/legacy_adapter.py` wraps existing engines (prometheus, coder, etc.) in the plugin interface without modifying their internals:

```python
class LegacyMathPlugin:
    """Wraps prometheus.py in the plugin interface."""

    def execute(self, envelope: QueryEnvelope) -> ExecutionResult:
        # Call legacy engine, wrap result in ExecutionResult
        raw = prometheus_solve(envelope.normalized_input)
        return ExecutionResult(answer=raw, engine="prometheus", ...)
```

### Phase 2: Contract Enforcement (Complete)

The kernel validates contracts at all boundaries:
- Input validation before routing
- Output validation after plugin execution
- Budget enforcement via deadline checks

### Phase 3: Plugin Isolation (In Progress)

Moving toward full process isolation for plugins:
- Each plugin runs in its own subprocess (for untrusted plugins)
- Communication via typed message passing
- Resource limits enforced at OS level

### Phase 4: Plugin Evolution (Planned)

- Plugins can be hot-reloaded without restarting the kernel
- Multiple versions of a plugin can coexist (A/B testing)
- Plugin marketplace with verified manifests

## Consequences

### Positive
- Each plugin can be developed, tested, and deployed independently
- Resource exhaustion in one plugin doesn't affect others
- New capabilities added by dropping in a plugin
- Clear ownership boundaries

### Negative
- More boilerplate for simple plugins
- Inter-plugin communication requires going through the kernel
- Slight latency overhead from contract validation
- Legacy adapter adds indirection

### Mitigations
- Fast path mode skips full contract validation for trusted plugins
- Legacy adapter is zero-copy where possible
- Plugin boilerplate reduced by base classes and code generation
