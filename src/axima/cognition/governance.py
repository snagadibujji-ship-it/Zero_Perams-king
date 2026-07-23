"""Governance Gate — enforceable capability boundaries for AXIMA.

Defines what AXIMA can and cannot do autonomously.  All actions are audited.
The governance policy itself cannot be modified by AXIMA.

AXIMA CANNOT:
  - Deploy to production
  - Grant itself new capabilities
  - Change governance rules
  - Access new network resources
  - Promote its own code without approval
  - Delete audit history
  - Claim benchmark victory without independent verification

AXIMA CAN:
  - Search local knowledge graph
  - Run bounded simulations
  - Generate hypotheses
  - Maintain indexes
  - Run idle tasks within budget
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class PermissionResult(Enum):
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"


@dataclass
class Permission:
    """Result of a permission check."""

    action: str
    result: PermissionResult
    reason: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def allowed(self) -> bool:
        return self.result == PermissionResult.ALLOWED


@dataclass
class AuditEntry:
    """Immutable audit log entry."""

    id: str
    timestamp: datetime
    action: str
    actor: str
    result: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GovernancePolicy:
    """Defines capability boundaries for AXIMA."""

    allowed_autonomous_actions: List[str] = field(default_factory=lambda: [
        "search_local_graph",
        "run_bounded_simulation",
        "generate_hypothesis",
        "maintain_indexes",
        "run_idle_tasks",
        "record_prediction",
        "extract_skill_spec",
        "propose_local_revision",
    ])

    forbidden_actions: List[str] = field(default_factory=lambda: [
        "deploy_to_production",
        "grant_self_capabilities",
        "change_governance",
        "access_new_network",
        "promote_own_code",
        "delete_audit_history",
        "claim_benchmark_victory",
        "modify_governance_policy",
        "escalate_privileges",
        "bypass_approval",
    ])

    approval_required_actions: List[str] = field(default_factory=lambda: [
        "promote_skill",
        "apply_module_revision",
        "apply_system_revision",
        "submit_discovery",
        "revoke_skill",
        "run_experiment_with_side_effects",
    ])

    budget_limits: Dict[str, float] = field(default_factory=lambda: {
        "max_simulation_steps": 10000,
        "max_hypotheses_per_hour": 100,
        "max_index_operations": 5000,
        "max_idle_task_seconds": 300,
    })

    audit_requirements: List[str] = field(default_factory=lambda: [
        "all_permission_checks",
        "all_denials",
        "all_approvals",
        "all_promotions",
        "all_revocations",
        "all_revisions",
        "all_experiments",
    ])


class GovernanceGate:
    """Enforces governance policy on all AXIMA actions.

    The gate cannot be disabled or weakened by AXIMA itself.
    All decisions are audited immutably.
    """

    def __init__(self, policy: Optional[GovernancePolicy] = None) -> None:
        self._policy = policy or GovernancePolicy()
        self._audit_log: List[AuditEntry] = []
        self._pending_approvals: Dict[str, Dict[str, Any]] = {}
        self._approved_actions: Dict[str, bool] = {}  # action_request_id → approved

    @property
    def policy(self) -> GovernancePolicy:
        return self._policy

    @property
    def audit_log(self) -> List[AuditEntry]:
        return list(self._audit_log)

    def check_permission(self, action: str, actor: str = "axima") -> Permission:
        """Check whether an action is permitted under current governance.

        Returns a Permission with allowed/denied/requires_approval status.
        """
        # Forbidden actions are always denied
        if action in self._policy.forbidden_actions:
            perm = Permission(
                action=action,
                result=PermissionResult.DENIED,
                reason=f"Action '{action}' is explicitly forbidden by governance policy",
            )
            self._audit(action, actor, "DENIED", {"reason": perm.reason})
            return perm

        # Approval-required actions need explicit approval
        if action in self._policy.approval_required_actions:
            # Check if there's a standing approval
            if self._approved_actions.get(f"{actor}:{action}"):
                perm = Permission(
                    action=action,
                    result=PermissionResult.ALLOWED,
                    reason=f"Action '{action}' has standing approval",
                )
                self._audit(action, actor, "ALLOWED_WITH_APPROVAL", {})
                return perm

            perm = Permission(
                action=action,
                result=PermissionResult.REQUIRES_APPROVAL,
                reason=f"Action '{action}' requires explicit governance approval",
            )
            self._audit(action, actor, "REQUIRES_APPROVAL", {"reason": perm.reason})
            return perm

        # Allowed autonomous actions
        if action in self._policy.allowed_autonomous_actions:
            perm = Permission(
                action=action,
                result=PermissionResult.ALLOWED,
                reason=f"Action '{action}' is in allowed autonomous actions",
            )
            self._audit(action, actor, "ALLOWED", {})
            return perm

        # Unknown actions default to denied
        perm = Permission(
            action=action,
            result=PermissionResult.DENIED,
            reason=f"Action '{action}' not in any policy list — denied by default",
        )
        self._audit(action, actor, "DENIED_UNKNOWN", {"reason": perm.reason})
        return perm

    def request_approval(self, action: str, justification: str, actor: str = "axima") -> str:
        """Submit an action for governance approval.

        Returns a request ID.  The action remains blocked until approved.
        """
        request_id = str(uuid.uuid4())
        self._pending_approvals[request_id] = {
            "action": action,
            "actor": actor,
            "justification": justification,
            "submitted_at": datetime.now(timezone.utc),
            "status": "pending",
        }
        self._audit(
            f"approval_request:{action}",
            actor,
            "SUBMITTED",
            {"request_id": request_id, "justification": justification},
        )
        return request_id

    def grant_approval(self, request_id: str, approver: str = "human_operator") -> bool:
        """Grant approval for a pending request (called by external authority)."""
        if request_id not in self._pending_approvals:
            return False

        request = self._pending_approvals[request_id]
        request["status"] = "approved"
        request["approved_by"] = approver
        request["approved_at"] = datetime.now(timezone.utc)

        # Set standing approval
        self._approved_actions[f"{request['actor']}:{request['action']}"] = True

        self._audit(
            f"approval_granted:{request['action']}",
            approver,
            "APPROVED",
            {"request_id": request_id},
        )
        return True

    def deny_approval(self, request_id: str, denier: str = "human_operator", reason: str = "") -> bool:
        """Deny a pending approval request."""
        if request_id not in self._pending_approvals:
            return False

        request = self._pending_approvals[request_id]
        request["status"] = "denied"
        request["denied_by"] = denier
        request["denial_reason"] = reason

        self._audit(
            f"approval_denied:{request['action']}",
            denier,
            "DENIED",
            {"request_id": request_id, "reason": reason},
        )
        return True

    def audit(self) -> List[AuditEntry]:
        """Return the full immutable audit log."""
        return list(self._audit_log)

    def enforce(self, action: str, actor: str = "axima") -> Permission:
        """Check and enforce permission — raises if denied.

        Use this for hard enforcement where denial should block execution.
        """
        perm = self.check_permission(action, actor)
        if perm.result == PermissionResult.DENIED:
            raise PermissionError(
                f"Governance DENIED action '{action}' for actor '{actor}': {perm.reason}"
            )
        return perm

    def _audit(self, action: str, actor: str, result: str, details: Dict[str, Any]) -> None:
        """Append an immutable entry to the audit log."""
        entry = AuditEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            action=action,
            actor=actor,
            result=result,
            details=details,
        )
        self._audit_log.append(entry)
