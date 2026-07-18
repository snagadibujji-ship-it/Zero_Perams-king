# SIGMA_BELIEF_SYSTEM

A persistent belief network that maintains statements with associated confidence levels. Beliefs are distinct from ground-truth facts; they represent the system's current understanding based on available evidence.

## Core Structure

Each belief contains:
- **statement**: The proposition being believed
- **confidence**: Float between 0.0 and 1.0 representing belief strength
- **supporting_evidence**: List of evidence items that reinforce the belief
- **contradicting_evidence**: List of evidence items that challenge the belief
- **observations**: Direct observations that inform the belief
- **dependencies**: Other beliefs this belief relies upon
- **prediction_history**: Past predictions made using this belief
- **revision_history**: Timeline of confidence changes and updates

## Dynamic Confidence

Confidence is never static. It evolves through:
- New evidence weighting by source reliability
- Contradictory evidence from stronger beliefs
- Temporal decay toward neutral (0.5) when unconfirmed
- Propagation through dependency chains

## Non-Monotonic Reasoning

The system supports non-monotonic inference: new evidence can weaken or invalidate previously held beliefs. This enables correction of mistaken assumptions without requiring explicit retraction.

## Integration Point

The belief system serves as the foundation for mental simulation, theory formation, and analogical reasoning. All higher-level modules consult and update beliefs as they operate.
