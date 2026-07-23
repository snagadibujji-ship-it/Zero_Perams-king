"""Agency Transactions — capability tokens and transactional execution.

Every action requires a short-lived CapabilityToken scoped by path, operation,
network destination, data class, and budget. Every action produces an AuditEvent.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set


class TransactionState(Enum):
    PENDING = auto()
    DRY_RUN = auto()
    AUTHORIZED = auto()
    EXECUTING = auto()
    COMMITTED = auto()
    ROLLED_BACK = auto()
    FAILED = auto()


class OperationType(Enum):
    READ = auto()
    WRITE = auto()
    DELETE = auto()
    EXECUTE = auto()
    NETWORK = auto()


@dataclass
class CapabilityScope:
    """Defines what a capability token allows."""
    paths: List[str] = field(default_factory=list)           # allowed path prefixes
    operations: List[OperationType] = field(default_factory=list)
    network_destinations: List[str] = field(default_factory=list)  # allowed hosts/URLs
    data_classes: List[str] = field(default_factory=list)    # e.g. ["public", "internal"]


@dataclass
class CapabilityToken:
    """Short-lived, scoped capability token.

    Grants permission to perform specific operations within defined boundaries.
    """
    token_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    scope: CapabilityScope = field(default_factory=CapabilityScope)
    budget: float = 0.0          # max cost/resource units allowed
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(minutes=5))
    issued_at: datetime = field(default_factory=datetime.now)
    issuer: str = ""
    revoked: bool = False
    spent: float = 0.0

    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.revoked and not self.is_expired and self.spent <= self.budget

    @property
    def remaining_budget(self) -> float:
        return max(0.0, self.budget - self.spent)

    def check_path(self, path: str) -> bool:
        """Check if path is within allowed scope."""
        if not self.scope.paths:
            return True  # no path restrictions
        return any(path.startswith(allowed) for allowed in self.scope.paths)

    def check_operation(self, op: OperationType) -> bool:
        """Check if operation type is allowed."""
        if not self.scope.operations:
            return True
        return op in self.scope.operations

    def check_network(self, destination: str) -> bool:
        """Check if network destination is allowed."""
        if not self.scope.network_destinations:
            return False  # default deny for network
        return any(destination.startswith(allowed) for allowed in self.scope.network_destinations)

    def check_data_class(self, data_class: str) -> bool:
        """Check if data class is allowed."""
        if not self.scope.data_classes:
            return True
        return data_class in self.scope.data_classes

    def spend(self, amount: float) -> bool:
        """Deduct from budget. Returns False if insufficient."""
        if self.spent + amount > self.budget:
            return False
        self.spent += amount
        return True

    def revoke(self) -> None:
        """Revoke this token immediately."""
        self.revoked = True


@dataclass
class AuditEvent:
    """Immutable audit record of an action."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    token_id: str = ""
    operation: str = ""
    target: str = ""
    result: str = ""
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AuthorizationError(Exception):
    """Raised when an operation is not authorized."""


class BudgetExceededError(Exception):
    """Raised when budget is exceeded."""


class AgencyTransaction:
    """Transactional execution with capability enforcement.

    Lifecycle: begin() -> dry_run() -> authorize() -> execute() -> commit()/rollback()
    Every state transition produces an AuditEvent.
    """

    def __init__(self, token: CapabilityToken) -> None:
        self._token = token
        self._state = TransactionState.PENDING
        self._audit_log: List[AuditEvent] = []
        self._actions: List[Dict[str, Any]] = []
        self._results: List[Any] = []
        self._rollback_actions: List[Callable[[], None]] = []
        self._tx_id = str(uuid.uuid4())

    @property
    def state(self) -> TransactionState:
        return self._state

    @property
    def audit_log(self) -> List[AuditEvent]:
        return list(self._audit_log)

    @property
    def transaction_id(self) -> str:
        return self._tx_id

    def begin(self) -> "AgencyTransaction":
        """Begin the transaction."""
        if not self._token.is_valid:
            self._state = TransactionState.FAILED
            self._audit("begin", "transaction", "failed", success=False, error="Invalid token")
            raise AuthorizationError("Token is invalid (expired or revoked)")

        self._state = TransactionState.PENDING
        self._audit("begin", "transaction", "started")
        return self

    def dry_run(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Preview what would happen without executing.

        Returns list of planned effects for each action.
        """
        previews: List[Dict[str, Any]] = []
        for action in actions:
            op = action.get("operation", "")
            target = action.get("target", "")
            preview: Dict[str, Any] = {
                "operation": op,
                "target": target,
                "authorized": self._check_authorization(action),
                "within_budget": self._token.remaining_budget >= action.get("cost", 0),
                "effects": action.get("effects", []),
            }
            previews.append(preview)

        self._state = TransactionState.DRY_RUN
        self._actions = actions
        self._audit("dry_run", "transaction", f"previewed {len(actions)} actions")
        return previews

    def authorize(self, actions: Optional[List[Dict[str, Any]]] = None) -> bool:
        """Authorize all pending actions against the capability token.

        Returns True if all actions are authorized.
        """
        check_actions = actions or self._actions
        if not check_actions:
            self._audit("authorize", "transaction", "no actions", success=False)
            return False

        for action in check_actions:
            if not self._check_authorization(action):
                self._state = TransactionState.FAILED
                self._audit(
                    "authorize", action.get("target", ""),
                    "denied", success=False,
                    error=f"Operation not authorized: {action}",
                )
                return False

        self._actions = check_actions
        self._state = TransactionState.AUTHORIZED
        self._audit("authorize", "transaction", f"authorized {len(check_actions)} actions")
        return True

    def execute(self, executor: Optional[Callable[[Dict[str, Any]], Any]] = None) -> List[Any]:
        """Execute authorized actions.

        Optionally provide an executor function. Default stores actions as-is.
        """
        if self._state != TransactionState.AUTHORIZED:
            raise AuthorizationError(
                f"Cannot execute: transaction in state {self._state.name}, expected AUTHORIZED"
            )

        if not self._token.is_valid:
            self._state = TransactionState.FAILED
            self._audit("execute", "transaction", "failed", success=False, error="Token expired during execution")
            raise AuthorizationError("Token expired during execution")

        self._state = TransactionState.EXECUTING
        self._results = []

        for action in self._actions:
            cost = action.get("cost", 0.0)
            if not self._token.spend(cost):
                self._state = TransactionState.FAILED
                self._audit("execute", action.get("target", ""), "budget_exceeded", success=False)
                raise BudgetExceededError(f"Budget exceeded: remaining={self._token.remaining_budget}")

            try:
                if executor:
                    result = executor(action)
                else:
                    result = {"action": action, "status": "executed"}
                self._results.append(result)
                self._audit("execute", action.get("target", ""), "success")
            except Exception as exc:
                self._state = TransactionState.FAILED
                self._audit("execute", action.get("target", ""), "failed", success=False, error=str(exc))
                raise

        return self._results

    def inspect(self) -> Dict[str, Any]:
        """Inspect current transaction state."""
        return {
            "transaction_id": self._tx_id,
            "state": self._state.name,
            "token_valid": self._token.is_valid,
            "token_remaining_budget": self._token.remaining_budget,
            "actions_count": len(self._actions),
            "results_count": len(self._results),
            "audit_events": len(self._audit_log),
        }

    def commit(self) -> bool:
        """Commit the transaction (mark as final)."""
        if self._state not in (TransactionState.EXECUTING, TransactionState.AUTHORIZED):
            self._audit("commit", "transaction", "invalid_state", success=False)
            return False

        self._state = TransactionState.COMMITTED
        self._audit("commit", "transaction", "committed")
        return True

    def rollback(self) -> bool:
        """Rollback the transaction, executing undo actions."""
        if self._state == TransactionState.COMMITTED:
            self._audit("rollback", "transaction", "cannot_rollback_committed", success=False)
            return False

        for undo_fn in reversed(self._rollback_actions):
            try:
                undo_fn()
            except Exception:
                pass  # best-effort rollback

        self._state = TransactionState.ROLLED_BACK
        self._results = []
        self._audit("rollback", "transaction", "rolled_back")
        return True

    def add_rollback_action(self, fn: Callable[[], None]) -> None:
        """Register a rollback/undo action."""
        self._rollback_actions.append(fn)

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _check_authorization(self, action: Dict[str, Any]) -> bool:
        """Check if an action is authorized by the token."""
        if not self._token.is_valid:
            return False

        op_str = action.get("operation", "")
        target = action.get("target", "")

        # Map string operation to OperationType
        op_map = {
            "read": OperationType.READ,
            "write": OperationType.WRITE,
            "delete": OperationType.DELETE,
            "execute": OperationType.EXECUTE,
            "network": OperationType.NETWORK,
        }
        op_type = op_map.get(op_str.lower())
        if op_type and not self._token.check_operation(op_type):
            return False

        if target and not self._token.check_path(target):
            return False

        data_class = action.get("data_class", "")
        if data_class and not self._token.check_data_class(data_class):
            return False

        destination = action.get("destination", "")
        if destination and not self._token.check_network(destination):
            return False

        return True

    def _audit(
        self, operation: str, target: str, result: str,
        success: bool = True, error: Optional[str] = None,
    ) -> None:
        """Record an audit event."""
        event = AuditEvent(
            token_id=self._token.token_id,
            operation=operation,
            target=target,
            result=result,
            success=success,
            error=error,
            metadata={"transaction_id": self._tx_id, "state": self._state.name},
        )
        self._audit_log.append(event)
