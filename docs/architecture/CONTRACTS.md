# AXIMA Core Contracts

All data flowing through AXIMA is typed via contracts defined in `src/axima/contracts/`. These are pure Python dataclasses with no external dependencies.

## Contract Types

### QueryEnvelope

The complete specification of a query entering the system. Immutable once created — all transforms produce new envelopes.

```python
@dataclass
class QueryEnvelope:
    raw_input: str                              # Original user input
    query_id: str                               # UUID, auto-generated
    session_id: Optional[str]                   # Session tracking
    normalized_input: Optional[str]             # Cleaned input (auto-set from raw_input)
    language_candidates: List[str]              # Detected languages, default ["en"]
    source_spans: List[Dict[str, Any]]          # Source provenance
    attachments: List[Dict[str, Any]]           # File/data attachments
    user_permissions: List[str]                 # Granted permissions, default ["read"]
    requested_mode: str                         # "fast" or "deep"
    deadline: Optional[float]                   # Unix timestamp (auto-computed from budget)
    resource_budget: ResourceBudgetSpec         # Time/memory/step limits
    created_at: float                           # Creation timestamp
```

### ResourceBudgetSpec

Resource constraints for query execution:

```python
@dataclass
class ResourceBudgetSpec:
    max_time_ms: float = 5000.0     # Maximum wall-clock time
    max_memory_mb: float = 256.0    # Maximum memory allocation
    max_steps: int = 100            # Maximum reasoning steps
    max_depth: int = 10             # Maximum recursion/chain depth
```

### ExecutionResult

Result from a single engine execution step:

```python
@dataclass
class ExecutionResult:
    answer: Optional[str]           # The computed answer (None if failed)
    status: str                     # "success" | "error" | "timeout" | "cancelled"
    claims: List[str]               # Factual claims made in the answer
    evidence: List[str]             # Evidence supporting each claim
    error: Optional[str]            # Error description if status != "success"
    cost_ms: float                  # Wall-clock time consumed
    engine: str                     # Which engine produced this result
```

### AximaResponseV2

The canonical response from the unified cognitive runtime. Self-describing: every response explains what it knows, how it knows it, and what it doesn't know.

```python
@dataclass
class AximaResponseV2:
    answer: str                             # The response text
    meaning_hash: str                       # SHA-256 hash prefix (auto-computed)
    truth_level: TruthLevel                 # Epistemic classification
    calibrated_confidence: float            # 0.0–1.0, calibrated score
    claims: List[str]                       # Individual factual claims
    citations: List[str]                    # Sources supporting claims
    derivation: List[str]                   # Reasoning chain steps
    caveats: List[str]                      # Known limitations of this answer
    unknowns: List[str]                     # What is explicitly not known
    verification: Optional[str]             # Verification result
    trace_id: str                           # Execution trace ID (UUID)
    language: str                           # Response language
    mode: str                               # "fast" or "deep"
    latency_ms: float                       # Total processing time
    engine: str                             # Primary engine used
```

### TruthLevel

Classification of how an answer was derived:

```python
class TruthLevel(Enum):
    DIRECT_FACT = "direct_fact"     # Found verbatim in knowledge base
    DERIVED = "derived"             # Inferred through reasoning rules (may be wrong)
    HEURISTIC = "heuristic"        # Best guess from pattern matching
    TEMPLATE = "template"          # Generated from structural patterns
    UNSUPPORTED = "unsupported"    # Could not find reliable answer
```

## Contract Interactions

```
QueryEnvelope
    │
    │ [Meaning Plane consumes]
    ▼
MeaningIR (internal to semantics module)
    │
    │ [Control Plane routes based on MeaningIR]
    ▼
Plugin.execute(QueryEnvelope) → ExecutionResult
    │
    │ [Evidence Plane verifies ExecutionResult.claims]
    ▼
Verified ExecutionResult + TruthLevel
    │
    │ [Expression Plane assembles]
    ▼
AximaResponseV2
```

### Flow Rules

1. **QueryEnvelope is immutable** — plugins receive it read-only; any transformation creates a new envelope
2. **ExecutionResult is the plugin boundary** — all plugins return this type regardless of internal representation
3. **AximaResponseV2 is the user boundary** — all responses to users use this type
4. **TruthLevel is mandatory** — no response may be returned without an epistemic classification
5. **ResourceBudgetSpec is enforced** — the kernel terminates any execution exceeding its budget

## MeaningIR (Internal)

The Meaning Plane produces an internal representation (MeaningIR) that is not exported outside the semantics module. It captures:

- Intent classification (domain, action, specificity)
- Extracted entities (names, numbers, formulas, code fragments)
- Structural decomposition (for compound queries)
- Language and register

MeaningIR is intentionally internal to allow evolution without breaking the plugin interface.

## Version Policy

### Contract Stability

- **Stable contracts** (QueryEnvelope, AximaResponseV2, ExecutionResult): Additive changes only. New optional fields may be added; existing fields will not be removed or have their types changed.
- **Internal contracts** (MeaningIR, routing decisions): May change between minor versions.
- **Plugin interface**: Follows the same stability as stable contracts.

### Versioning Rules

1. Adding an optional field with a default: **minor** version bump
2. Adding a required field: **major** version bump (breaking)
3. Removing a field: **major** version bump (breaking)
4. Changing a field type: **major** version bump (breaking)
5. Adding an enum variant: **minor** version bump

### Compatibility Guarantees

- All serialized contracts include a schema version
- The kernel validates contract versions at plugin boundaries
- Plugins built against contract v0.1 will work with any v0.1.x runtime
