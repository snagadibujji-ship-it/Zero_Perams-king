# LAMBDA_INTEGRATION

IntegratedRuntime wires all 4 autonomous phases into a cohesive system. Manages execution context and coordinates scheduler decisions.

## Architecture

The runtime implements:
- **process_interaction()**: Handles user-initiated interactions
- **autonomous_cycle()**: Executes background cognition during idle
- **Scheduler**: Decides what runs and when based on policies

## Phase Wiring

All 9 modules (3 per phase) are instantiated and wired:
- Phase 1: Autonomy (Supervisor, Goals, Governance)
- Phase 2: Discovery (Hypothesis, Experiment, Pipeline)
- Phase 3: Maintenance (Knowledge, Self-Assessment)

## Execution Modes

### User Mode
- Waits for user input
- Prioritizes user requests
- Brief autonomous work between inputs

### Idle Mode
- Triggers autonomous cycle
- Supervisor evaluates budget availability
- Scheduler picks highest-priority work

## Scheduler Logic

Scheduler considers:
- User activity state
- Resource budget status
- Goal priority ranking
- Hypothesis freshness
- Maintenance urgency

## Commit Gate

All modules must pass through governance before committing:
- Results staged
- Governance review
- Confirmed commits
- Rollback stack updated

## Metrics Collection

Runtime tracks:
- Session duration
- User vs. autonomous time ratio
- Commit rate and success rate
- Resource usage per mode
