# SIGMA_MENTAL_SIMULATION

Evaluation of possible futures using the world model without altering reality.

## Scenario Generation

Simulates alternative futures based on:
- **Optimistic**: Best-case outcomes assuming favorable conditions
- **Pessimistic**: Worst-case scenarios assuming adverse conditions
- **Neutral**: Expected outcomes based on current belief confidence

## Core Operations

**simulate_causal_chain(action, scenarios)**
- Traces causal effects of actions across scenario paths
- Quantifies outcome distributions
- Identifies critical decision points and feedback loops

**compare_options(actions)**
- Ranks action alternatives by expected utility
- Considers multiple scenario perspectives
- Outputs probability distribution over outcomes

**evaluate_risk(action)**
- Computes worst-case, best-case, and expected values
- Identifies high-impact low-probability events
- Assesses robustness across scenarios

## Constraints

- Reality remains unaltered; simulations are hypothetical
- World model uncertainty propagates through simulations
- Temporal consistency maintained throughout simulation

## Output Format

Each simulation produces:
- Timeline of expected states
- Probability distribution at each time step
- Key divergences from baseline trajectory
- Confidence bands around predictions

## Use Cases

- Decision support with uncertainty quantification
- Policy impact assessment
- Strategy evaluation before implementation
- Training data for belief system (prediction history)
