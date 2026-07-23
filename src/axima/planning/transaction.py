"""Transaction Manager — reversible execution with audit trail.

Provides ACID-like semantics for plan execution:
- Every action is reversible until committed
- Full audit trail of all state transitions
- Preflight validation before execution
- Verification after execution
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .plan_dag import PlanDAG, PlanStep, StepStatus


class TransactionState(Enum):
    """Lifecycle states for a transaction."""

    PLANNING = "planning"
    PREFLIGHT = "preflight"
    AUTHORIZED = "authorized"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"


# Valid state transitions
_VALID_TRANSITIONS: Dict[TransactionState, List[TransactionState]] = {
    TransactionState.PLANNING: [TransactionState.PREFLIGHT, TransactionState.ROLLED_BACK],
    TransactionState.PREFLIGHT: [TransactionState.AUTHORIZED, TransactionState.ROLLED_BACK],
    TransactionState.AUTHORIZED: [TransactionState.EXECUTING, TransactionState.ROLLED_BACK],
    TransactionState.EXECUTING: [TransactionState.VERIFYING, TransactionState.ROLLED_BACK],
    TransactionState.VERIFYING: [TransactionState.COMMITTED, TransactionState.ROLLED_BACK],
    TransactionState.COMMITTED: [],  # Terminal state
    TransactionState.ROLLED_BACK: [],  # Terminal state
}


@dataclass
class AuditEvent:
    """A single audit record for a state transition."""

    timestamp: float
    from_state: TransactionState
    to_state: TransactionState
    step_id: Optional[str] = None
    detail: str = ""
    actor: str = "system"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "step_id": self.step_id,
            "detail": self.detail,
            "actor": self.actor,
        }


@dataclass
class RollbackAction:
    """An action that undoes a previously executed step."""

    step_id: str
    undo_fn: Optional[Callable[[], None]] = None
    description: str = ""
    executed: bool = False

    def execute(self) -> bool:
        """Execute the rollback action. Returns True on success."""
        if self.undo_fn is not None:
            try:
                self.undo_fn()
                self.executed = True
                return True
            except Exception:
                return False
        self.executed = True
        return True


@dataclass
class Transaction:
    """A transaction wrapping a PlanDAG execution.

    Tracks state, audit trail, and rollback actions for full reversibility.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    plan: PlanDAG = field(default_factory=PlanDAG)
    state: TransactionState = TransactionState.PLANNING
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)
    audit_events: List[AuditEvent] = field(default_factory=list)
    rollback_actions: List[RollbackAction] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def transition_to(self, new_state: TransactionState, detail: str = "") -> None:
        """Transition to a new state with validation and audit logging."""
        valid_next = _VALID_TRANSITIONS.get(self.state, [])
        if new_state not in valid_next:
            raise InvalidTransitionError(
                f"Cannot transition from {self.state.value} to {new_state.value}. "
                f"Valid transitions: {[s.value for s in valid_next]}"
            )

        event = AuditEvent(
            timestamp=time.time(),
            from_state=self.state,
            to_state=new_state,
            detail=detail,
        )
        self.audit_events.append(event)
        self.state = new_state
        self.modified_at = time.time()

    def add_rollback_action(self, action: RollbackAction) -> None:
        """Register a rollback action (LIFO order for execution)."""
        self.rollback_actions.append(action)

    @property
    def is_terminal(self) -> bool:
        """Whether the transaction is in a terminal (final) state."""
        return self.state in (TransactionState.COMMITTED, TransactionState.ROLLED_BACK)

    @property
    def duration_ms(self) -> float:
        """Total elapsed time since creation."""
        return (self.modified_at - self.created_at) * 1000

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "state": self.state.value,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "duration_ms": self.duration_ms,
            "audit_events": [e.to_dict() for e in self.audit_events],
            "rollback_actions_count": len(self.rollback_actions),
            "plan": self.plan.to_dict(),
        }


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class TransactionManager:
    """Manages transaction lifecycle with preflight checks and verification.

    Usage::

        mgr = TransactionManager()
        txn = mgr.begin(plan)
        mgr.preflight(txn)
        mgr.authorize(txn)
        mgr.execute(txn, executor_fn)
        mgr.verify(txn, verifier_fn)
        mgr.commit(txn)
    """

    def __init__(self) -> None:
        self._active_transactions: Dict[str, Transaction] = {}
        self._history: List[Transaction] = []

    def begin(self, plan: PlanDAG) -> Transaction:
        """Create a new transaction for the given plan.

        The plan is validated before the transaction is created.
        """
        errors = plan.validate()
        # Allow budget warnings but not structural errors
        structural_errors = [e for e in errors if "cycle" in e or "unknown step" in e]
        if structural_errors:
            raise ValueError(f"Plan validation failed: {structural_errors}")

        txn = Transaction(plan=plan)
        self._active_transactions[txn.id] = txn
        return txn

    def preflight(
        self,
        txn: Transaction,
        checks: Optional[List[Callable[[PlanDAG], Optional[str]]]] = None,
    ) -> List[str]:
        """Run preflight checks on the transaction.

        Args:
            txn: The transaction to check.
            checks: Optional list of check functions. Each returns None (pass)
                    or an error message string (fail).

        Returns:
            List of warning/error messages (empty = all clear).
        """
        txn.transition_to(TransactionState.PREFLIGHT, "Starting preflight checks")

        warnings: List[str] = []
        checks = checks or []

        # Built-in checks
        plan_errors = txn.plan.validate()
        warnings.extend(plan_errors)

        # Custom checks
        for check_fn in checks:
            result = check_fn(txn.plan)
            if result is not None:
                warnings.append(result)

        return warnings

    def authorize(self, txn: Transaction, actor: str = "system") -> None:
        """Authorize the transaction for execution.

        In a real system this would check permissions, quotas, etc.
        """
        event = AuditEvent(
            timestamp=time.time(),
            from_state=txn.state,
            to_state=TransactionState.AUTHORIZED,
            detail=f"Authorized by {actor}",
            actor=actor,
        )
        txn.audit_events.append(event)
        txn.state = TransactionState.AUTHORIZED
        txn.modified_at = time.time()

    def execute(
        self,
        txn: Transaction,
        executor: Optional[Callable[[PlanStep], Any]] = None,
    ) -> Dict[str, Any]:
        """Execute the plan steps in topological order.

        Args:
            txn: The transaction to execute.
            executor: Function that executes a single step. If None, steps are
                      marked complete with no result.

        Returns:
            Dict mapping step_id -> result.
        """
        txn.transition_to(TransactionState.EXECUTING, "Beginning execution")

        results: Dict[str, Any] = {}
        order = txn.plan.topological_sort()

        for step_id in order:
            step = txn.plan.steps[step_id]
            if step.status == StepStatus.SKIPPED:
                continue

            # Check if dependencies are satisfied
            deps = txn.plan.dependencies.get(step_id, [])
            if any(txn.plan.steps[d].status == StepStatus.FAILED for d in deps):
                txn.plan.mark_skipped(step_id)
                continue

            txn.plan.mark_running(step_id)

            try:
                if executor is not None:
                    result = executor(step)
                else:
                    result = {"status": "completed"}

                txn.plan.mark_complete(step_id, result)
                results[step_id] = result

                # Register rollback action
                txn.add_rollback_action(
                    RollbackAction(
                        step_id=step_id,
                        description=f"Undo step: {step.name}",
                    )
                )

            except Exception as exc:
                txn.plan.mark_failed(step_id, str(exc))
                results[step_id] = {"error": str(exc)}

        return results

    def verify(
        self,
        txn: Transaction,
        verifier: Optional[Callable[[Transaction], List[str]]] = None,
    ) -> List[str]:
        """Verify that execution produced correct results.

        Args:
            txn: The transaction to verify.
            verifier: Optional verification function. Returns list of issues.

        Returns:
            List of verification issues (empty = verified).
        """
        txn.transition_to(TransactionState.VERIFYING, "Starting verification")

        issues: List[str] = []

        # Check that all non-skipped steps completed
        for step_id, step in txn.plan.steps.items():
            if step.status == StepStatus.FAILED:
                issues.append(f"Step '{step.name}' ({step_id}) failed")
            elif step.status == StepStatus.RUNNING:
                issues.append(f"Step '{step.name}' ({step_id}) still running")

        # Custom verification
        if verifier is not None:
            issues.extend(verifier(txn))

        return issues

    def commit(self, txn: Transaction) -> None:
        """Commit the transaction — makes results permanent.

        After commit, rollback is no longer possible.
        """
        txn.transition_to(TransactionState.COMMITTED, "Transaction committed")
        # Move from active to history
        self._active_transactions.pop(txn.id, None)
        self._history.append(txn)

    def rollback(self, txn: Transaction, reason: str = "") -> List[str]:
        """Rollback all executed steps in reverse order.

        Returns:
            List of rollback failures (empty = all rolled back successfully).
        """
        if txn.state == TransactionState.COMMITTED:
            raise InvalidTransitionError("Cannot rollback a committed transaction")

        failures: List[str] = []

        # Execute rollback actions in reverse (LIFO)
        for action in reversed(txn.rollback_actions):
            if not action.executed:
                success = action.execute()
                if not success:
                    failures.append(
                        f"Failed to rollback step {action.step_id}: {action.description}"
                    )

        # Reset the plan
        txn.plan.rollback_plan()

        # Transition to rolled back
        detail = f"Rolled back. Reason: {reason}" if reason else "Rolled back"
        event = AuditEvent(
            timestamp=time.time(),
            from_state=txn.state,
            to_state=TransactionState.ROLLED_BACK,
            detail=detail,
        )
        txn.audit_events.append(event)
        txn.state = TransactionState.ROLLED_BACK
        txn.modified_at = time.time()

        # Move from active to history
        self._active_transactions.pop(txn.id, None)
        self._history.append(txn)

        return failures

    @property
    def active_count(self) -> int:
        return len(self._active_transactions)

    @property
    def history(self) -> List[Transaction]:
        return list(self._history)
