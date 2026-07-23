# ADR-001: Zero Learned Parameters

**Status:** Accepted  
**Date:** 2026-07-23  
**Deciders:** Gowtham Sangadi (Ghias)

## Context

AXIMA is designed as a symbolic intelligence engine. The core question: should any component use trained/learned parameters (neural networks, statistical models, embeddings)?

## Decision

**AXIMA uses zero learned parameters.** All intelligence emerges from:
- Explicit rules and patterns
- Structured knowledge bases
- Compositional algorithms
- Deterministic transformations

## What Is Allowed

| Technique | Allowed | Rationale |
|-----------|---------|-----------|
| Pattern matching (regex, AST) | ✅ | Explicit, auditable rules |
| Rule-based inference | ✅ | Deterministic, traceable |
| Template composition | ✅ | Structural patterns, no learning |
| Graph traversal (knowledge base) | ✅ | Algorithmic, not statistical |
| Symbolic math (CAS rules) | ✅ | Deterministic algebraic manipulation |
| Grammar-based generation | ✅ | Structural rules, not probabilities |
| Heuristic scoring functions | ✅ | Hand-crafted, auditable weights |
| Lookup tables / dictionaries | ✅ | Explicit mappings |

## What Is NOT Allowed

| Technique | Banned | Rationale |
|-----------|--------|-----------|
| Neural networks (any architecture) | ❌ | Opaque learned parameters |
| Word embeddings (Word2Vec, GloVe) | ❌ | Trained vector representations |
| Statistical classifiers (SVM, NB) | ❌ | Learned decision boundaries |
| Language models (any size) | ❌ | Trained probability distributions |
| Reinforcement learning | ❌ | Learned policies |
| Genetic algorithms with fitness learning | ❌ | Evolved parameters |
| Pre-trained anything | ❌ | External learned weights |

## Rationale

1. **Explainability:** Every AXIMA answer can trace its derivation to explicit rules. No "the model thinks" opacity.
2. **Auditability:** The knowledge base and rules can be inspected, corrected, and versioned.
3. **Determinism:** Same input always produces same output. No temperature, no sampling.
4. **Offline operation:** No API calls, no cloud dependencies, no model downloads.
5. **Honest limitations:** When AXIMA can't answer, it's because a rule or fact is missing — identifiable and fixable.

## Trade-offs

- ❌ Cannot handle truly open-ended generation (creative writing quality limited)
- ❌ Cannot generalize beyond its rules (fails on novel patterns)
- ❌ Requires explicit engineering for each new capability
- ✅ Fully explainable
- ✅ Fully deterministic
- ✅ Runs on any hardware (no GPU, no model loading)
- ✅ Instant startup, predictable latency

## Compliance Gate

Before merging any code:

1. **Static check:** Grep for imports of `torch`, `tensorflow`, `sklearn`, `transformers`, `numpy` (for model operations), `scipy.optimize.minimize` (for learning).
2. **Manifest check:** All capabilities must be listed in `zero_parameter_manifest.json` with their technique classification.
3. **Review check:** PR reviewer confirms no learned parameters are introduced.

### Exceptions

None. If a use case genuinely requires learned parameters, it must be implemented as an external tool called via the sandbox (same isolation as user code), clearly labeled as "external ML" in responses, and excluded from AXIMA's own capability claims.
