# How AXIMA Works

A complete technical explanation of the AXIMA symbolic intelligence engine.

---

## Table of Contents

1. [Overview](#overview)
2. [The Query Pipeline](#the-query-pipeline)
3. [Input Shield](#1-input-shield)
4. [Language Detection](#2-language-detection)
5. [Meaning Compiler](#3-meaning-compiler)
6. [Epistemic Contracts](#4-epistemic-contracts)
7. [Intent Lattice](#5-intent-lattice)
8. [Plugin Execution](#6-plugin-execution)
9. [Verification](#7-verification)
10. [Response Building](#8-response-building)
11. [The Plugin System](#the-plugin-system)
12. [Memory System](#memory-system)
13. [Evidence and Truth](#evidence-and-truth)
14. [Security Model](#security-model)
15. [Knowledge Base](#knowledge-base)
16. [Benchmarks and Testing](#benchmarks-and-testing)

---

## Overview

AXIMA is a **rule-based symbolic reasoning engine**. Every answer it produces comes from explicit rules, pattern matching, algebraic manipulation, or indexed facts — never from statistical prediction or learned weights.

The core insight: for many problems (exact math, factual lookup, code patterns, unit conversion), a deterministic system with clear derivation is more trustworthy than a probabilistic model that can hallucinate.

### What "Zero Learned Parameters" means

- **Allowed**: Source code, algorithms, grammars, indexed facts, inference rules, algebraic manipulation
- **Not allowed**: Neural network weights, embeddings, transformer inference, hidden API calls to LLMs
- **The distinction**: AXIMA has knowledge (facts, rules, patterns) but none of it was learned via gradient descent

### Core Properties

| Property | How it's achieved |
|----------|------------------|
| Deterministic | Same input → same output, always |
| Explainable | Every answer carries a derivation trace |
| Offline | Zero network calls required |
| Verifiable | Independent checkers validate answers |
| Honest | Says "unsupported" rather than guessing |

---

## The Query Pipeline

Every query flows through 8 stages:

```
┌─────────────────────────────────────────────────────────────┐
│  User Query: "solve x^2 - 4 = 0"                           │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  1. INPUT SHIELD                                            │
│     Validate, normalize, check rate limits                  │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  2. LANGUAGE DETECTION                                      │
│     Detect: English (grammar patterns, script analysis)     │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  3. MEANING COMPILER                                        │
│     Extract: quantities=[4], goals=["solve equation"]       │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  4. EPISTEMIC CONTRACT                                      │
│     Determine: answer_kind=DERIVATION, evidence=SOURCED     │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  5. INTENT LATTICE                                          │
│     Route: intent=math (confidence=0.80) → math_solver      │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  6. PLUGIN EXECUTION                                        │
│     math_solver: parse equation → solve → x = ±2           │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  7. VERIFICATION                                            │
│     Check: non-empty, derivation valid, no contradictions   │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  8. RESPONSE                                                │
│     answer="x = ±2", truth=DERIVED, engine="math_solver"    │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Input Shield

**File:** `src/axima/security/input_shield.py`

The first defense layer. Every input passes through validation before any processing.

**What it does:**
- **Length check** — rejects inputs over the configured maximum
- **Encoding normalization** — ensures valid UTF-8
- **Injection detection** — blocks code injection patterns, path traversal, shell metacharacters
- **Rate limiting** — token-bucket rate limiter per source
- **Content policy** — rejects known-malicious patterns

**What it produces:**
```python
@dataclass
class ValidationResult:
    valid: bool
    normalized_input: str
    warnings: list[str]
    blocked_reason: str | None
```

If validation fails, the pipeline stops and returns a SecurityError response immediately.

---

## 2. Language Detection

**File:** `src/axima/api.py` (`_detect_language_builtin`)

Detects the input language using grammar patterns and script analysis. No statistical model — pure rule matching.

**How it works:**

1. **Script detection** — checks for Unicode ranges:
   - Devanagari (0900-097F) → Hindi
   - Bengali (0980-09FF) → Bengali  
   - Japanese (3040-30FF, 4E00-9FFF) → Japanese
   - Arabic (0600-06FF) → Arabic
   - etc.

2. **Romanized grammar patterns** — for languages written in Latin script:
   - Telugu: `ante`, `enti`, `ela`, `enduku`, `gurinchi`, `chemu`
   - Hindi: `kya`, `hai`, `hota`, `kaise`, `kyun`
   - Tamil: `enna`, `eppadi`, `yenna`, `endha`
   - Turkish: `nedir`, `nasil`, `neden`
   - Spanish: `que es`, `como`, `porque`
   - French: `c'est`, `quoi`, `pourquoi`
   - German: `was ist`, `wie`, `warum`
   - Malayalam: `enthu`, `aanu`, `engane`

3. **Default** — English if no other patterns match

**Supported languages:** English, Telugu, Hindi, Tamil, Turkish, Bengali, Japanese, Arabic, Korean, Spanish, French, German, Malayalam, and more.

---

## 3. Meaning Compiler

**File:** `src/axima/semantics/compiler.py`

Parses natural language text into a structured, language-neutral **Meaning IR** (Intermediate Representation).

**What it extracts:**

```python
@dataclass
class MeaningIR:
    entities: list[Entity]          # Named things (people, places, concepts)
    events: list[Event]             # Actions (solve, calculate, write)
    predicates: list[Predicate]     # Subject-relation-object triples
    quantities: list[Quantity]      # Numbers with units
    conditions: list[Condition]     # If-then-else structures
    goals: list[Goal]               # What the user wants
    source_span_map: dict           # Maps back to original text
    language: str                   # Detected language code
```

**Example:** For "solve x^2 - 4 = 0":
- `quantities`: [4, 0] (numeric values found)
- `goals`: [Goal(description="solve x^2 - 4 = 0")]
- `source_span_map`: {"_raw": "solve x^2 - 4 = 0"}

**Key design choice:** The IR preserves multiple parse alternatives when input is ambiguous rather than committing to one interpretation prematurely.

---

## 4. Epistemic Contracts

**File:** `src/axima/epistemics/contracts.py`

Determines what *kind* of answer is required and what *evidence* is needed. This prevents the system from returning a guess when proof is required, or over-computing when a simple lookup suffices.

**Contract fields:**

```python
@dataclass
class EpistemicContract:
    answer_kind: AnswerKind          # FACT, DERIVATION, ESTIMATE, PROOF, PLAN, ACTION
    required_evidence: EvidenceReq   # NONE, HEURISTIC, SOURCED, PROVEN
    confidence_floor: float          # Minimum confidence to return answer
    verification_level: str          # How much checking is required
    abstention_rule: str             # When to say "I don't know"
```

**How it infers contracts from keywords:**
- "prove" / "derive" → `DERIVATION` with `PROVEN` evidence
- "what is" / "who is" → `FACT` with `SOURCED` evidence
- "estimate" / "approximately" → `ESTIMATE` with `HEURISTIC` evidence
- "write" / "create" / "build" → `ACTION` with `NONE` evidence
- "solve" / "calculate" → `DERIVATION` with `SOURCED` evidence

---

## 5. Intent Lattice

**File:** `src/axima/routing/intent_lattice.py`

Replaces simple regex routing with multi-candidate intent detection. Instead of matching the *first* pattern, it scores *all* possible intents and picks the best.

**How it works:**

1. **Pattern matching** — each intent has multiple regex patterns:
   ```python
   "math": [
       r"\b(solve|calculate|compute|integrate|derive)\b",
       r"\b(factorial|gcd|lcm|mod|modulo)\b",
       r"[\d]+\s*[+\-*/^=]\s*[\d]",
       r"\b(sin|cos|tan|log|sqrt)\b",
   ]
   ```

2. **Confidence scoring** — based on pattern match density and structural analysis

3. **Lattice resolution** — picks the highest-confidence candidate, or requests clarification if top candidates are too close

**Intent types:** math, physics, code, web, knowledge, creative, explanation

**Example:** "write fibonacci in python"
- code: 0.87 (matches "write", "python", "fibonacci")
- math: 0.30 (matches "fibonacci" loosely)
- **Winner:** code → routes to `coder` plugin

---

## 6. Plugin Execution

**File:** `src/axima/plugins/`

The actual computation happens in plugins. Each plugin is an independent engine that accepts a MeaningIR and contract, and returns an ExecutionResult.

### Available Plugins

| Plugin | Name | What it does |
|--------|------|-------------|
| `math_solver` | Math | Arithmetic, algebra, calculus, number theory |
| `physics_solver` | Physics | Unit conversion, formula application, dimensional analysis |
| `inference_engine` | Knowledge | Fact lookup from indexed knowledge base |
| `coder` | Code | Algorithm generation from pattern library |
| `creator` | Creative | Structured narrative/poem/song generation |
| `web_builder` | Web | HTML/CSS/JS project scaffolding |
| `brain` | Document | Document Q&A with citations |
| `document_parser` | Documents | Structure extraction from text |
| `multimodal_analyzer` | Multimodal | Image metadata, audio analysis |

### Math Solver Detail

The math plugin is the most developed. It handles:

1. **Direct arithmetic** — `2 + 2`, `sqrt(144)`, `15 * 7`
   - Uses a **safe math AST evaluator** (never `eval()`)
   - Tokenize → parse to AST → evaluate node by node
   - Allowed operations: +, -, *, /, ^, %, //
   - Allowed functions: sin, cos, tan, sqrt, log, ln, exp, factorial, gcd, abs, floor, ceil

2. **Symbolic algebra** — `solve 2x + 6 = 0`, `solve x^2 - 4 = 0`
   - Linear solver: ax + b = c → x = (c-b)/a
   - Quadratic solver: ax² + bx + c = 0 → quadratic formula
   - Returns both roots for quadratic (±)

3. **Calculus** — `derivative of x^3`, `integrate 2x dx`
   - Power rule differentiation: d/dx(axⁿ) = n·a·xⁿ⁻¹
   - Power rule integration: ∫(axⁿ)dx = a/(n+1)·xⁿ⁺¹ + C

4. **Number theory** — `factorial of 5`, `GCD of 12 and 18`, `7 mod 3`
   - Uses Python's math library through safe wrappers

### Coder Plugin Detail

The coder generates code from a pattern library:

- **Pattern matching** — recognizes common algorithms (fibonacci, binary search, quicksort, etc.)
- **Multi-language** — Python, JavaScript, Java, C, Rust, Go, TypeScript
- **Template expansion** — complete, runnable implementations with examples
- **Fallback** — generates a stub with TODO for unrecognized requests

### How Plugins Are Loaded

```python
class PluginLoader:
    def discover(self) -> list[str]:
        # Scan src/axima/plugins/ for subdirectories with plugin.py
    
    def load_all(self) -> dict[str, PluginBase]:
        # Import each, find PluginBase subclass, instantiate
        # Register module in sys.modules before execution (Python 3.14 compat)
```

---

## 7. Verification

**File:** `src/axima/verification/constellation.py`

After a plugin produces an answer, independent verifiers check it. The generator never grades itself.

**Verification checks:**
- Non-empty answer
- Answer is not just the query echoed back
- Math: symbolic equivalence by substitution
- Code: syntax validity (compiles)
- Dimensions: unit consistency for physics
- Provenance: citation to source data

**Quorum decisions:** For high-risk answers, multiple verifiers must agree before the answer is released.

**Confidence intervals:** Confidence cannot be inflated — it's bounded by the weakest link in the derivation chain.

---

## 8. Response Building

**File:** `src/axima/api.py` (`_build_response`)

Assembles the final response with full metadata:

```python
@dataclass
class AximaResponseV2:
    answer: str                      # The actual answer text
    truth_level: TruthLevel          # DIRECT_FACT, DERIVED, HEURISTIC, TEMPLATE, UNSUPPORTED
    calibrated_confidence: float     # 0.0 to 1.0
    claims: list[str]               # What the answer claims
    citations: list[str]            # Source references
    derivation: list[str]           # Steps to arrive at the answer
    caveats: list[str]              # Limitations or assumptions
    unknowns: list[str]             # What we couldn't determine
    engine: str                     # Which plugin produced it
    language: str                   # Detected input language
    trace_id: str                   # For debugging/replay
    latency_ms: float               # How long it took
```

### Truth Levels

| Level | Meaning | Example |
|-------|---------|---------|
| `DIRECT_FACT` | Looked up from knowledge base | "Capital of France = Paris" |
| `DERIVED` | Computed from rules/algebra | "x² - 4 = 0 → x = ±2" |
| `HEURISTIC` | Best guess, lower confidence | Pattern-matched answer |
| `TEMPLATE` | Generated from a template | Code from pattern library |
| `UNSUPPORTED` | Cannot answer | "I don't have enough information" |

---

## The Plugin System

### Plugin Contract

Every plugin implements this interface:

```python
class PluginBase(ABC):
    def name(self) -> str: ...
    def version(self) -> str: ...
    def describe(self) -> CapabilityDescriptor: ...
    def execute(self, ir: MeaningIR, contract: EpistemicContract) -> ExecutionResult: ...
    def health_check(self) -> bool: ...
```

### Capability Descriptors

Each plugin declares what it can do:

```python
@dataclass
class CapabilityDescriptor:
    name: str                    # "math_solver"
    version: str                 # "1.0.0"
    accepted_types: list[str]    # ["equation", "arithmetic", "calculus"]
    produced_types: list[str]    # ["numeric_result", "symbolic_result"]
    preconditions: list[str]     # What must be true
    postconditions: list[str]    # What will be true after
    cost_model: dict             # Expected time/resource cost
    deterministic: bool          # Same input → same output
```

---

## Memory System

**File:** `src/axima/memory/four_plane.py`

AXIMA maintains four separate memory planes:

| Plane | Purpose | Persistence |
|-------|---------|-------------|
| **Working** | Current query context, active plan | Session only |
| **Episodic** | Past interactions, outcomes | Append-only log |
| **Semantic** | Facts, concepts, beliefs | With provenance |
| **Procedural** | Skills, workflows, tool policies | Versioned |

Every memory write requires:
- Schema identifier
- Source attribution
- Retention policy (session, short-term, long-term)
- Sensitivity label (public, internal, private)

Users can export, delete, and inspect all stored memory.

---

## Evidence and Truth

### Claims and Derivation

Every answer is backed by a claim graph:

```python
@dataclass
class Claim:
    statement: str              # "x = 2 satisfies x² - 4 = 0"
    status: ClaimStatus         # PROPOSED, SUPPORTED, VERIFIED
    evidence_ids: list[str]     # Links to evidence records
    derivation_id: str          # Link to derivation steps
```

### Derivation DAGs

For derived answers, the full reasoning chain is recorded:

```python
@dataclass  
class DerivationStep:
    rule: str                   # "quadratic_formula"
    inputs: list[str]           # Previous claim IDs used
    output: str                 # New claim produced
    justification: str          # Why this step is valid
```

### Source Tiers

Evidence is categorized by reliability:

| Tier | Description | Example |
|------|-------------|---------|
| T0 | Formally verified | Mathematical proof |
| T1 | Primary authoritative | Official data source |
| T2 | Reputable secondary | Encyclopedia |
| T3 | User-provided | User's documents |
| T4 | Generated/unverified | Inference output (needs validation) |

---

## Security Model

### Threat Mitigations

| Threat | Mitigation |
|--------|-----------|
| Code injection | Typed math AST evaluator — never `eval()` or `exec()` |
| Path traversal | File operations within allowed directories only |
| Resource exhaustion | Time, memory, recursion depth limits |
| Malicious generated code | Sandbox with process isolation |
| Knowledge poisoning | Source tiers, quarantine for unverified data |
| Secret exposure | Redaction in traces and outputs |

### Safe Math Evaluator

The most critical security component. Instead of `eval("2+2")`, AXIMA:

1. **Tokenizes** — splits "2+2" into tokens: [NUM:2, OP:+, NUM:2]
2. **Parses** — builds an AST: BinOp(left=Num(2), op=ADD, right=Num(2))
3. **Validates** — checks depth, value bounds, allowed operations
4. **Evaluates** — walks the tree: add(2, 2) = 4

Blocked patterns:
- `__import__`, `exec`, `eval`, `compile`
- Attribute access (`.`)
- Subscript access (`[]`)
- Any identifier not in the allowed function list

---

## Knowledge Base

### Data Files

| File | Size | Content |
|------|------|---------|
| `data/axima.cse` | 73 MB | Primary knowledge corpus |
| `data/axima_hot.cse` | 19 MB | Frequently accessed facts |
| `data/axima_cold.cse.gz` | 23 MB | Archive corpus (compressed) |
| `data/all_triples_clean.txt.gz` | 36 MB | Relation triples |
| `src/data/unified_knowledge.triples` | 137 KB | Active inference facts |
| `src/data/causal_knowledge.json` | 89 KB | Cause-effect relations |

### Built-in Knowledge

The API includes a small high-confidence knowledge base for common queries:
- World capitals (15+ countries)
- Physical constants (speed of light, gravity, boiling points)
- Mathematical constants (pi, e)

### Knowledge Index

The full knowledge system supports:
- Subject/object/relation queries
- Temporal validity (facts can expire)
- Source provenance (where each fact came from)
- Incremental updates
- Dependency invalidation (if a source is retracted, derived facts are invalidated)

---

## Benchmarks and Testing

### Test Pyramid

```
┌─────────────────────────────────┐
│  Eval Benchmarks (45 cases)     │  ← End-to-end correctness
├─────────────────────────────────┤
│  Integration Tests              │  ← Full pipeline flow
├─────────────────────────────────┤
│  Contract Tests                 │  ← Interface compliance
├─────────────────────────────────┤
│  Metamorphic Tests              │  ← Meaning preservation
├─────────────────────────────────┤
│  Security Tests                 │  ← Injection/bypass attempts
├─────────────────────────────────┤
│  Unit Tests                     │  ← Individual module behavior
├─────────────────────────────────┤
│  Parse Tests                    │  ← All Python files parse
└─────────────────────────────────┘
```

### Eval Suite (45 cases, 100% pass)

| Category | Cases | What's tested |
|----------|-------|--------------|
| Math | 20 | Arithmetic, algebra, calculus, number theory |
| Multilingual | 15 | Language detection from romanized input |
| Codegen | 10 | Algorithm generation in Python |

### Judge Types

AXIMA never uses substring matching for evaluation:

| Judge | How it scores |
|-------|--------------|
| ExactJudge | Exact string equality (after trim) |
| ToleranceJudge | Numeric within ±tolerance |
| CompilationJudge | Generated code compiles |
| ASTJudge | Structural code equivalence |
| SemanticJudge | Meaning-level comparison via IR |

### Benchmark Immune System

Prevents "teaching to the test":
- Canary questions that shouldn't be answerable
- Semantic mutations of existing cases
- Contamination detection for benchmark-specific code
- Hidden test sets unavailable to developers

---

## Execution Traces

Every query produces a full trace:

```json
{
  "trace_id": "abc-123",
  "events": [
    {"stage": "input", "data": {"raw": "2 + 2"}},
    {"stage": "shield", "data": {"valid": true}},
    {"stage": "language", "data": {"detected": "en"}},
    {"stage": "meaning_ir", "data": {"quantities": 2, "goals": 0}},
    {"stage": "contract", "data": {"answer_kind": "derivation"}},
    {"stage": "intent", "data": {"intent": "math", "confidence": 0.95}},
    {"stage": "route", "data": {"plugin": "math_solver"}},
    {"stage": "execute", "data": {"intent": "math"}},
    {"stage": "verification", "data": {"checks_passed": 2}},
    {"stage": "respond", "data": {"answer_length": 1, "latency_ms": 12}}
  ]
}
```

Traces are available via `ax.get_last_trace()` for debugging and audit.

---

## Performance Characteristics

| Operation | Typical Latency |
|-----------|----------------|
| Simple arithmetic | 5-20 ms |
| Equation solving | 30-100 ms |
| Knowledge lookup | 2-10 ms |
| Code generation | 1-5 ms |
| Language detection | 1-3 ms |
| Cold start (first query) | 500-800 ms |

Memory usage: ~50 MB base + data corpus size

---

## Limitations

AXIMA is honest about what it cannot do:

1. **No open-ended reasoning** — cannot explain concepts, teach, or reason about novel situations
2. **No conversation** — each query is independent (no multi-turn context)
3. **No translation** — detects languages but cannot translate between them
4. **No summarization** — cannot condense documents
5. **Limited knowledge** — only indexed facts, not general world knowledge
6. **Pattern-based code** — generates from templates, cannot write truly novel code
7. **No learning** — doesn't improve from usage (by design — deterministic)

These are fundamental to the zero-parameter architecture. Addressing them would require either neural components (breaking the zero-parameter promise) or years of additional symbolic engineering.

---

## Future Directions

Potential improvements within the zero-parameter constraint:

- Deeper algebra (polynomial division, partial fractions, linear algebra)
- More knowledge corpus coverage
- Better natural language parsing for multi-step problems
- Causal reasoning from structured causal models
- Document ingestion and citation-grounded Q&A
- Richer code generation (project-level, not just functions)
- Improved multilingual response generation (not just detection)
