# SIGMA_WORLD_MODEL

A causal graph representing how events and states influence one another, distinct from statistical correlations.

## Causal Representation

- **Nodes**: Events, states, or conditions
- **Edges**: Causal relationships with direction and strength
- **Edge weights**: Measure of effect size and certainty
- **Edge types**: Necessary, sufficient, contributory, inhibitory

## Core Operations

**add_causal_link(source, target, strength, certainty)**
- Creates or updates causal edge between nodes
- Validates causality before adding (temporal precedence, mechanism)

**causal_chain(start_node, max_depth)**
- Traces forward through causal graph
- Returns list of reachable effects with accumulated uncertainty
- Detects cycles to prevent infinite recursion

**predict_effects(action, time Horizon)**
- Simulates causal consequences of hypothetical actions
- Returns probabilistic outcomes at each time step
- Quantifies uncertainty in predictions

**find_causes(effect, max_depth)**
- Traces backward through causal graph
- Identifies potential root causes
- Ranks by causal strength and temporal proximity

**simulate_intervention(action, baseline)**
- Compares baseline world state vs. intervention scenario
- Calculates difference in expected outcomes
- Evaluates counterfactual scenarios

## Temporal Causality

Causal links maintain temporal ordering. Effects cannot precede causes, enabling consistent time-based reasoning and scenario generation.
