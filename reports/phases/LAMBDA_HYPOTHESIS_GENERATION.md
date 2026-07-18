# LAMBDA_HYPOTHESIS_GENERATION

Proactively generates testable hypotheses from gaps and patterns in the knowledge base. Drives scientific discovery within the reasoning system.

## Hypothesis Types

- **Hidden Relationships**: Suspected connections between known entities not yet linked
- **Causal Patterns**: Belief that factor A influences outcome B, not yet verified
- **Missing Concepts**: Anticipation of a category or construct that should exist
- **Overgeneralizations**: Suspicion that a rule applies more broadly than currently encoded
- **Conflicts**: Inconsistencies suggesting an underlying principle is wrong

## Generation Strategy

Hypotheses are generated when:
- Graph analysis reveals disconnected but semantically related nodes
- Prediction failures occur with consistent patterns
- Reasoning chains hit unexpected contradictions
- Knowledge maintenance flags stale or low-confidence concepts

## Hypothesis Metadata

Each hypothesis preserves:
- **Provenance**: Which trigger(s) generated it
- **Type**: Category of hypothesis (see above)
- **Supporting Evidence**: Initial observations motivating the hypothesis
- **Expected Evidence**: What would confirm or refute it
- **Test Strategy**: Suggested experimental approach

## Temporary Nature

Hypotheses are temporary structures. They expire if not tested within a session or if superseded by stronger hypotheses. No commitments are made until evidence validates a hypothesis.

## Integration

Hypotheses are submitted to the Experiment Engine for validation. The Discovery Pipeline orchestrates the full lifecycle from hypothesis generation to graph update.
