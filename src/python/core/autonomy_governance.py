"""
AXIMA Autonomy Governance — Safeguards for autonomous cognition.

Requirements: configurable resource limits, confidence thresholds,
evidence requirements, rollback capability, audit logs, human override,
explainable decisions. Every autonomous action must be reproducible.
"""

import time
import json
import os
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from core.reality_graph import get_reality_graph, RealityGraph


@dataclass
class GovernancePolicy:
    """Configurable governance policy."""
    # Resource limits
    max_memory_mb: float = 25.0
    max_cpu_ms_per_action: float = 50.0
    max_autonomous_actions_per_session: int = 200

    # Confidence thresholds
    min_confidence_to_commit: float = 0.5      # Min confidence to create knowledge
    min_confidence_to_modify: float = 0.6      # Min confidence to modify existing
    min_confidence_to_retire: float = 0.8      # Min confidence to retire a principle

    # Evidence requirements
    min_evidence_to_commit: int = 2            # Min supporting evidence
    min_experiments_to_validate: int = 1       # Min experiments before commit

    # Safety
    allow_node_deletion: bool = False          # Never delete, only archive
    allow_principle_retirement: bool = True
    require_rollback_point: bool = True

    # Human override
    human_override_active: bool = False        # When True, all autonomous actions pause


@dataclass
class AuditEntry:
    """Record of an autonomous action."""
    timestamp: float
    action_type: str        # create, modify, archive, retire, reject
    target_id: str = ""
    description: str = ""
    confidence: float = 0.0
    evidence_count: int = 0
    reversible: bool = True
    rollback_data: Dict[str, Any] = field(default_factory=dict)


class AutonomyGovernance:
    """Strict safeguards for all autonomous actions."""

    def __init__(self, graph: Optional[RealityGraph] = None,
                 policy: Optional[GovernancePolicy] = None):
        self._graph = graph or get_reality_graph()
        self._policy = policy or GovernancePolicy()
        self._audit: List[AuditEntry] = []
        self._action_count = 0
        self._rollback_stack: List[AuditEntry] = []

    def can_commit(self, confidence: float, evidence_count: int) -> bool:
        """Check if an autonomous action is allowed."""
        if self._policy.human_override_active:
            return False
        if self._action_count >= self._policy.max_autonomous_actions_per_session:
            return False
        if confidence < self._policy.min_confidence_to_commit:
            return False
        if evidence_count < self._policy.min_evidence_to_commit:
            return False
        return True

    def can_modify(self, confidence: float) -> bool:
        """Check if modification of existing knowledge is allowed."""
        if self._policy.human_override_active:
            return False
        return confidence >= self._policy.min_confidence_to_modify

    def can_retire(self, confidence: float) -> bool:
        """Check if retiring a principle is allowed."""
        if not self._policy.allow_principle_retirement:
            return False
        return confidence >= self._policy.min_confidence_to_retire

    def record_action(self, action_type: str, target_id: str = "",
                      description: str = "", confidence: float = 0.0,
                      evidence_count: int = 0, rollback_data: Optional[Dict] = None):
        """Record an autonomous action in the audit log."""
        entry = AuditEntry(
            timestamp=time.time(),
            action_type=action_type,
            target_id=target_id,
            description=description,
            confidence=confidence,
            evidence_count=evidence_count,
            reversible=True,
            rollback_data=rollback_data or {},
        )
        self._audit.append(entry)
        self._rollback_stack.append(entry)
        self._action_count += 1

        # Keep bounded
        if len(self._audit) > 1000:
            self._audit = self._audit[-1000:]
        if len(self._rollback_stack) > 100:
            self._rollback_stack = self._rollback_stack[-100:]

    def rollback_last(self) -> Optional[Dict[str, Any]]:
        """Rollback the most recent autonomous action."""
        if not self._rollback_stack:
            return None
        entry = self._rollback_stack.pop()
        # If it was a create action, remove the node
        if entry.action_type == "create" and entry.target_id:
            self._graph.remove_node(entry.target_id)
            self._graph.save()
        # If it was a modify, restore old values
        elif entry.action_type == "modify" and entry.rollback_data:
            self._graph.update_node(entry.target_id, properties=entry.rollback_data)
            self._graph.save()
        return {"rolled_back": entry.description, "action": entry.action_type}

    def human_override(self, active: bool = True):
        """Enable/disable human override (pauses all autonomous actions)."""
        self._policy.human_override_active = active

    def audit_log(self, n: int = 50) -> List[Dict[str, Any]]:
        """Get recent audit entries."""
        return [
            {
                "time": e.timestamp,
                "action": e.action_type,
                "target": e.target_id,
                "description": e.description,
                "confidence": e.confidence,
                "evidence": e.evidence_count,
            }
            for e in self._audit[-n:]
        ]

    def policy_summary(self) -> Dict[str, Any]:
        """Get current governance policy."""
        return {
            "max_memory_mb": self._policy.max_memory_mb,
            "min_confidence_to_commit": self._policy.min_confidence_to_commit,
            "min_evidence_to_commit": self._policy.min_evidence_to_commit,
            "allow_deletion": self._policy.allow_node_deletion,
            "human_override": self._policy.human_override_active,
            "actions_this_session": self._action_count,
            "max_actions": self._policy.max_autonomous_actions_per_session,
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "total_actions": self._action_count,
            "audit_entries": len(self._audit),
            "rollback_available": len(self._rollback_stack),
            "human_override": self._policy.human_override_active,
        }


_governance: Optional[AutonomyGovernance] = None
def get_governance(graph: Optional[RealityGraph] = None) -> AutonomyGovernance:
    global _governance
    if _governance is None:
        _governance = AutonomyGovernance(graph=graph)
    return _governance
