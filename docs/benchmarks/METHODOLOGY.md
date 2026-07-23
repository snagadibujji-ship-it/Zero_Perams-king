# Benchmark Methodology

## Benchmark Constitution

AXIMA's evaluation system follows a strict constitution to prevent inflated or misleading claims.

### Core Principles

1. **Reproducibility above all.** Every benchmark must be independently reproducible from the published test cases, judge code, and scoring rules.
2. **No self-grading.** The system under test never judges its own output.
3. **Deterministic judges.** Judge functions are pure functions: same input always produces same score.
4. **Published failures.** Every benchmark run publishes both passes AND failures with full traces.
5. **Honest framing.** Claims state what was tested, on what inputs, with what judge — never extrapolate.

## Test Layers

Benchmarks operate at multiple layers, from unit correctness to system-level capability:

### Layer 1: Component Correctness

Tests individual engines in isolation with known-answer pairs.

| Suite | Engine | Cases | Judge |
|-------|--------|-------|-------|
| `evals/math/` | Prometheus (math) | Algebraic/calculus | Numeric equivalence |
| `evals/codegen/` | Code generator | Algorithm output | Execution + output match |
| `evals/multilingual/` | Language detector | Labeled samples | Exact language match |
| `evals/web/` | Web generator | Component specs | Structure validation |
| `evals/explanation/` | ACES pipeline | Explanation prompts | Rubric coverage |

### Layer 2: Contract Compliance

Tests that all components honor typed contracts:

- QueryEnvelope fields are preserved through the pipeline
- ExecutionResult always has a valid status
- AximaResponseV2 always carries a TruthLevel
- Resource budgets are never exceeded

Located in: `tests/contracts/`

### Layer 3: System Integration

End-to-end tests from raw input to final response:

- Query → correct engine routing
- Multi-step queries → correct decomposition
- Error cases → structured error responses (not None/crash)
- Budget exhaustion → graceful timeout with partial results

Located in: `tests/integration/`

### Layer 4: Metamorphic Properties

Tests that semantic equivalences are preserved:

- Paraphrased inputs produce equivalent answers
- Unit conversions preserve meaning
- Language-equivalent inputs route to same engine
- Order-independent inputs produce order-independent results

Located in: `tests/metamorphic/`

## Correct Judges

Judges are deterministic functions that score outputs. Each judge is:

- A pure Python function in `evals/judges/`
- Fully tested with its own unit tests
- Documented with its scoring criteria

### Available Judges

#### Numeric Judge (`evals/judges/numeric.py`)

For math and physics outputs:
- Parses numeric answers from varied formats
- Applies configurable tolerance (default: 1e-6 relative, 1e-9 absolute)
- Handles special cases: infinity, NaN, complex numbers
- Scores: 1.0 (correct), 0.0 (incorrect), with partial credit for close answers

#### Exact Judge (`evals/judges/exact.py`)

For classification and detection outputs:
- Case-insensitive string comparison
- Normalization (whitespace, punctuation)
- Set-based comparison for multi-value outputs
- Scores: 1.0 (exact match), 0.0 (no match)

### Judge Requirements

New judges must:
1. Be deterministic (same input → same output, always)
2. Accept `(expected: str, actual: str) -> float` signature
3. Return scores in [0.0, 1.0]
4. Include documentation of scoring criteria
5. Have their own test suite proving correctness

## Frontier Comparison Protocol

When comparing AXIMA against other systems (LLMs, CAS tools, etc.):

### Rules

1. **Same inputs.** All systems receive identical test cases.
2. **Same judge.** The same judge function scores all outputs.
3. **Published config.** System configurations (model version, temperature, etc.) are recorded.
4. **Time-bounded.** All systems get the same time budget per query.
5. **No cherry-picking.** Report all results, not just favorable subsets.
6. **Version-pinned.** Record exact versions of all compared systems.

### Protocol

```
1. Select test suite (must be published in evals/)
2. Run AXIMA on all cases, record outputs
3. Run comparison system on same cases, record outputs
4. Apply judge to both output sets
5. Publish: inputs, both outputs, scores, system versions, judge version
```

## Required Claim Format

Any performance claim about AXIMA must follow this format:

```
CLAIM: [specific capability statement]
SUITE: [path to test suite, e.g., evals/math/cases.json]
CASES: [number of test cases]
JUDGE: [judge function, e.g., evals/judges/numeric.py::NumericJudge]
SCORE: [pass/total, e.g., 47/50]
DATE: [ISO date of run]
COMMIT: [git commit hash]
REPRODUCE: [exact command to reproduce]
```

### Example

```
CLAIM: AXIMA solves basic algebra with 94% accuracy
SUITE: evals/math/cases.json
CASES: 50
JUDGE: evals/judges/numeric.py::NumericJudge(tolerance=1e-6)
SCORE: 47/50
DATE: 2026-07-23
COMMIT: abc123f
REPRODUCE: python evals/run_evals.py --suite math --judge numeric
```

### Prohibited Claim Formats

- ❌ "AXIMA achieves 400/400 on math" (no suite reference)
- ❌ "Better than GPT-4" (no comparison protocol)
- ❌ "99% accuracy" (no judge or test set specified)
- ❌ "Passes all tests" (unfalsifiable without published failures)

## Running Benchmarks

```bash
# Run all evaluation suites
python evals/run_evals.py

# Run specific suite
python evals/run_evals.py --suite math

# Generate public manifest (published results)
python evals/run_evals.py --publish
```

Results are written to `evals/public/manifest.json` with full provenance.
