# SIGMA_BELIEF_REVISION

Bayesian confidence updates that maintain belief coherence amid incoming evidence.

## Evidence Weighting

Evidence is weighted by source reliability:
- Direct observation: base weight (1.0)
- Trusted informant: adjusted based on historical accuracy
- Statistical data: weighted by sample size and confidence interval
- Anecdotal reports: reduced weight, flagged for verification

## Contradiction Resolution

When conflicting evidence arrives:
1. Compare evidence reliability scores
2. Apply Bayes' theorem to compute posterior confidence
3. Stronger evidence dominates unless combined weight of weaker evidence exceeds threshold
4. Record contradiction in revision_history for future analysis

## Uncertainty Propagation

When a belief's confidence changes:
1. Identify all dependent beliefs through dependency graph
2. Compute new confidence values using conditional probability
3. Propagate changes recursively through dependency chains
4. Log propagation path in revision_history

## Confidence Decay

Unverified beliefs decay toward 0.5 confidence over time:
- Decay rate: configurable parameter (default: 0.01 per time unit)
- Decay pauses when new supporting evidence arrives
- Decay accelerates when contradicted evidence accumulates
- Prevents stale beliefs from persisting indefinitely

## Evidence Tracking

Every revision maintains:
- Timestamp and source of new evidence
- Previous confidence value
- Computed posterior confidence
- Rationale for change (mathematical or logical justification)
