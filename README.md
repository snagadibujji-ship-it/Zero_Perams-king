# AXIMA

**Offline Symbolic Intelligence Engine — Zero Learned Parameters**

AXIMA is a rule-based reasoning and generation system that runs entirely offline. No neural networks, no cloud APIs, no training data. It routes queries to specialized symbolic engines and produces answers with full derivation traces.

---

## What AXIMA Does

| Domain | Capability | Example |
|--------|-----------|---------|
| **Mathematics** | Symbolic algebra, calculus, arithmetic | `solve x^2 - 4 = 0` → `x = ±2` |
| **Physics** | Equation solving, unit analysis | Dimensional analysis, formula lookup |
| **Knowledge** | Factual Q&A from indexed knowledge base | `capital of France` → `Paris` |
| **Code Generation** | Algorithms in multiple languages | Fibonacci, binary search, sorting |
| **Language Detection** | 15 languages from romanized input | `gravity kya hai` → Hindi detected |
| **Web Building** | HTML/CSS/JS site generation | Component-based page scaffolding |
| **Creative Content** | Stories, poems, songs (structural) | Grammar-based narrative generation |

## What AXIMA Is Not

- Not a language model — no transformer, no training, no learned weights
- Not comparable to ChatGPT/Claude for open-ended conversation
- Not a general-purpose AI — it handles structured, well-defined problems
- "Zero parameters" means zero *learned* parameters — it has rules, patterns, and a knowledge base

---

## Architecture

AXIMA uses a **microkernel architecture** with specialized plugins:

```
Input → Shield → Language Detection → Meaning IR → Contract → Intent Routing
    → Plugin Execution → Verification → Proof-Carrying Response
```

**Core components:**

- **Input Shield** — validates, normalizes, rate-limits all input
- **Meaning Compiler** — parses text into a language-neutral semantic representation
- **Epistemic Contracts** — determines what kind of answer is required and what evidence is needed
- **Intent Lattice** — routes to the best engine using multi-candidate detection
- **9 Plugins** — math, physics, inference, coder, creator, web, brain, document, multimodal
- **Verification Constellation** — independent checkers validate answers
- **Proof-Carrying Responses** — every answer includes derivation, confidence, and truth level

**Two execution modes:**
- **Fast path** (<50ms) — direct computation for arithmetic, cached facts
- **Deep path** (up to 5s) — multi-step reasoning with full verification

Every response carries a truth label: `direct_fact`, `derived`, `heuristic`, `template`, or `unsupported`.

---

## Quick Start

### Requirements

- Python 3.11+
- No external runtime dependencies

### Install

```bash
git clone <repo-url> hybrid-ai
cd hybrid-ai
pip install -e ".[dev]"
```

### Usage

```python
from axima.api import Axima

ax = Axima()

# Math
result = ax.query("solve x^2 - 4 = 0")
print(result.answer)        # "x = ±2"
print(result.truth_level)   # TruthLevel.DERIVED
print(result.engine)        # "math_solver"

# Knowledge
result = ax.query("what is the capital of France?")
print(result.answer)        # "Paris"
print(result.truth_level)   # TruthLevel.DIRECT_FACT

# Code generation
result = ax.query("write fibonacci in python")
print(result.answer)        # Complete fibonacci implementation

# Language detection
result = ax.query("gravity ante enti")
print(result.language)      # "te" (Telugu)
```

### CLI

```bash
# Interactive mode
axima

# Single query
axima "solve 2x + 6 = 0"

# Legacy CLI
python3 axima_cli.py
```

---

## Running Tests

```bash
# Full test suite (873 tests)
pytest

# By category
pytest tests/unit/
pytest tests/integration/
pytest tests/security/
pytest tests/contracts/
pytest tests/metamorphic/
pytest tests/regression/

# Eval benchmarks (45 cases, 100% pass)
python evals/run_cosmic_evals.py

# Type checking
mypy src/

# Linting
ruff check src/ tests/
```

---

## Project Structure

```
hybrid-ai/
├── src/axima/              # New architecture (119 modules)
│   ├── api.py              # Public API — sole entry point
│   ├── cli.py              # CLI interface
│   ├── kernel/             # Microkernel, registry, scheduler, traces
│   ├── semantics/          # Meaning IR, compiler, transforms
│   ├── epistemics/         # Contracts, entropy, unknowns
│   ├── routing/            # Intent lattice
│   ├── planning/           # PlanDAG, transactions
│   ├── plugins/            # 9 capability plugins
│   ├── evidence/           # Claims, derivation, provenance, reality ledger
│   ├── knowledge/          # Corpus, indexes, crystals
│   ├── memory/             # Four-plane memory system
│   ├── verification/       # Verifier constellation
│   ├── security/           # Safe math, sandbox, input shield
│   ├── language/           # Parsers, realizers
│   ├── cognition/          # Teaching, narrative, governance
│   ├── agency/             # Transactional tool execution
│   ├── specialist/         # Math, physics, causal specialists
│   ├── benchmarks/         # Judges, runner, immune system
│   └── production/         # API, lifecycle, backup
├── src/python/             # Legacy engines (math, physics, knowledge)
├── tests/                  # 873 automated tests
├── evals/                  # Benchmark suite (45 cases, 100%)
├── data/                   # Knowledge corpus files
└── docs/                   # Architecture documentation
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [How It Works](docs/HOW_IT_WORKS.md) | Complete explanation of AXIMA's architecture and pipeline |
| [Architecture Overview](docs/architecture/OVERVIEW.md) | Four planes, microkernel, plugin system |
| [Core Contracts](docs/architecture/CONTRACTS.md) | QueryEnvelope, MeaningIR, Response types |
| [Benchmark Methodology](docs/benchmarks/METHODOLOGY.md) | Test layers, judges, claim format |
| [Threat Model](docs/threat-model/THREATS.md) | Security threats and mitigations |
| [ADR-001: Zero Parameters](docs/decisions/ADR-001-zero-parameter.md) | Why no learned parameters |
| [ADR-002: Microkernel](docs/decisions/ADR-002-microkernel.md) | Why microkernel over monolith |
| [ADR-003: No eval()](docs/decisions/ADR-003-no-eval.md) | Safe math alternative |

---

## Design Principles

1. **No silent failures** — every answer explains its confidence and source
2. **Abstention over hallucination** — says "I don't know" when it doesn't know
3. **Verifiable** — every derived answer has a replayable derivation chain
4. **Offline-first** — no network calls, no API keys, no cloud dependencies
5. **Deterministic** — same input always produces the same output
6. **Safe** — no eval(), sandboxed code execution, input validation

---

## Built By

**Gowtham Sangadi (Ghias)** — Architecture & Direction
**Kiro** — Implementation

---

## License

See repository license file.
