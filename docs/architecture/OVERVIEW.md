# AXIMA Architecture Overview

## Design Philosophy

AXIMA is a **zero-learned-parameter** symbolic intelligence engine. All reasoning emerges from explicit rules, structured knowledge, and compositional patterns — never from trained weights or statistical inference.

The architecture follows a **microkernel** design: a minimal core runtime orchestrates specialized plugins through typed contracts.

## The Four Planes

All query processing flows through four architectural planes, each with a distinct responsibility:

```
    ┌──────────────────────────────────────────────────────┐
    │                 EXPRESSION PLANE                      │
    │  Response formatting • Epistemic annotations          │
    │  Natural language generation • Multi-format output     │
    ├──────────────────────────────────────────────────────┤
    │                  CONTROL PLANE                        │
    │  Routing • Scheduling • Resource budgets              │
    │  Timeout enforcement • Mode selection                  │
    ├──────────────────────────────────────────────────────┤
    │                  EVIDENCE PLANE                       │
    │  Claim verification • Truth level assignment           │
    │  Confidence calibration • Citation tracking            │
    ├──────────────────────────────────────────────────────┤
    │                  MEANING PLANE                        │
    │  Semantic parsing • MeaningIR construction             │
    │  Language detection • Intent classification            │
    └──────────────────────────────────────────────────────┘
```

### Meaning Plane (`src/axima/semantics/`)

Transforms raw user input into a structured semantic representation (MeaningIR):

- Language detection (15 languages, Romanized input)
- Intent classification (math, physics, code, factual, creative, etc.)
- Entity extraction and normalization
- Query decomposition for compound questions

### Control Plane (`src/axima/routing/`, `src/axima/kernel/`)

Decides how to process a query and manages execution:

- Routes queries to appropriate specialist plugins
- Enforces resource budgets (time, memory, depth)
- Schedules multi-step reasoning chains
- Selects between fast path and deep path modes

### Evidence Plane (`src/axima/evidence/`, `src/axima/epistemics/`)

Validates claims and assigns epistemic status:

- Verifies factual claims against knowledge base
- Assigns truth levels: `direct_fact`, `derived`, `heuristic`, `template`, `unsupported`
- Calibrates confidence based on evidence strength
- Tracks derivation chains for explainability

### Expression Plane (`src/axima/responses/`)

Formats verified results for human consumption:

- Structures answers with claims, caveats, and unknowns
- Adds epistemic annotations (what is known vs. inferred)
- Formats for appropriate output mode (CLI, API, etc.)
- Generates explanation chains when requested

## Microkernel Design

The kernel (`src/axima/kernel/`) is intentionally minimal:

```
kernel/
├── runtime.py       → Main execution loop, lifecycle management
├── scheduler.py     → Priority-based task scheduling
├── registry.py      → Plugin discovery, registration, capability grants
├── event_ledger.py  → Immutable event log for tracing
├── trace.py         → Distributed tracing support
└── legacy_adapter.py → Bridge to pre-cosmic engines
```

### Kernel Responsibilities
- Plugin lifecycle (load, initialize, health check, unload)
- Contract enforcement (type validation at boundaries)
- Resource accounting (time, memory, step budgets)
- Event recording (every decision is traceable)

### Kernel Non-Responsibilities
- Domain logic (delegated to plugins)
- Knowledge storage (delegated to knowledge plugin)
- Input parsing (delegated to meaning plane)
- Output formatting (delegated to expression plane)

## Plugin System

Every specialist engine is a plugin that:

1. Declares its capabilities in a manifest
2. Implements the standard plugin interface
3. Receives typed `QueryEnvelope` inputs
4. Returns typed `ExecutionResult` outputs
5. Operates within granted capabilities only

```
plugins/
├── math/        → Symbolic algebra, calculus (prometheus)
├── physics/     → Equation-based physics solving
├── code/        → Algorithm generation, project scaffolding
├── web/         → Website generation (HTML/CSS/JS/React)
├── knowledge/   → 4.8M fact graph, inference rules
├── language/    → Multilingual detection and routing
├── creator/     → Content generation (grammar physics)
├── aces/        → Multi-stage explanation pipeline
├── brain/       → Personal document Q&A
└── cognition/   → Metacognition, planning, memory
```

### Plugin Contract

```python
class PluginInterface(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def capabilities(self) -> list[str]: ...

    def can_handle(self, envelope: QueryEnvelope) -> float:
        """Return confidence 0.0–1.0 that this plugin can handle the query."""
        ...

    def execute(self, envelope: QueryEnvelope) -> ExecutionResult:
        """Execute the query within resource budget."""
        ...

    def health_check(self) -> bool: ...
```

## Two Execution Modes

### Fast Path (< 50ms target)

For queries with high-confidence routing and cached/indexed answers:

1. Meaning plane produces MeaningIR
2. Router identifies single best plugin (confidence > 0.9)
3. Plugin executes with tight budget
4. Response formatted directly (skip full evidence chain)

Use cases: simple factual lookups, basic math, cached code patterns.

### Deep Path (up to 5s)

For complex queries requiring multi-step reasoning:

1. Meaning plane produces MeaningIR with decomposition
2. Planner creates execution graph (may involve multiple plugins)
3. Scheduler executes steps respecting dependencies
4. Evidence plane verifies all claims
5. Expression plane composes final response with full provenance

Use cases: multi-step proofs, complex code generation, compound questions.

## Data Flow

```
User Input
    │
    ▼
QueryEnvelope (raw_input, budget, permissions)
    │
    ▼
┌─ Meaning Plane ─┐
│  → MeaningIR     │
└──────────────────┘
    │
    ▼
┌─ Control Plane ──┐
│  → Route + Plan  │
└──────────────────┘
    │
    ▼
┌─ Plugin(s) ──────┐
│  → ExecutionResult│
└──────────────────┘
    │
    ▼
┌─ Evidence Plane ─┐
│  → Verified claims│
└──────────────────┘
    │
    ▼
┌─ Expression Plane┐
│  → AximaResponseV2│
└──────────────────┘
    │
    ▼
User Response (answer + truth_level + caveats + unknowns)
```

## Key Design Decisions

| Decision | Rationale | ADR |
|----------|-----------|-----|
| Zero learned parameters | Explainability, auditability, determinism | [ADR-001](../decisions/ADR-001-zero-parameter.md) |
| Microkernel over monolith | Isolation, testability, plugin evolution | [ADR-002](../decisions/ADR-002-microkernel.md) |
| No eval() anywhere | Security (code injection prevention) | [ADR-003](../decisions/ADR-003-no-eval.md) |
