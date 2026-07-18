# LAMBDA_AUTONOMY_GOVERNANCE

Ensures all autonomous actions comply with policies. Provides safety constraints and auditability for system changes.

## Governance Policy

### Commit Thresholds
- **Minimum Confidence**: 0.5 (50% confidence required)
- **Minimum Evidence**: 2 independent experimental results

### Operations
- **No Deletion**: Knowledge is never deleted, only marked inactive
- **Rollback Stack**: All changes tracked for undo operations
- **Human Override**: Emergency stop and review capability

## Gate Points

All autonomous actions pass through governance:
- Goal execution approval
- Hypothesis commitment approval
- Graph update approval
- Maintenance operation approval

## Audit Trail

Every governance decision records:
- Action requested
- Evidence reviewed
- Policy criteria applied
- Decision outcome
- Approving entity (human or automated)

## Human Override

Humans can:
- Suspend autonomous operation
- Review pending actions
- Override policy thresholds (with justification)
- Force rollback of recent changes

## Safety Features

- All changes are staged before commitment
- Rollback operations are idempotent
- Policy violations are logged as security events
- Resource budget enforcement (CPU/memory/tick limits)

## Integration

Governance is wired into the IntegratedRuntime and affects all modules. No module can commit changes without passing governance review.
