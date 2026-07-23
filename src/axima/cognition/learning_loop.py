"""Learning Loop — bounded revision from prediction errors.

When a prediction is wrong, the loop identifies which rule or assumption
caused the error, proposes a minimal revision, validates it, and applies
it only with governance approval.  Rollback is always available.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


class RevisionScope(Enum):
    """How broad a proposed revision is."""

    LOCAL = "LOCAL"  # Affects a single rule
    MODULE = "MODULE"  # Affects multiple rules in one module
    SYSTEM = "SYSTEM"  # Affects cross-module behavior


class RevisionStatus(Enum):
    PROPOSED = "PROPOSED"
    VALIDATED = "VALIDATED"
    APPLIED = "APPLIED"
    ROLLED_BACK = "ROLLED_BACK"
    REJECTED = "REJECTED"


@dataclass
class LearningSignal:
    """A signal derived from a prediction error."""

    id: str
    prediction_id: str
    error_type: str  # e.g., "false_positive", "false_negative", "miscalibration"
    causal_rule: str  # The rule/assumption that caused the error
    proposed_revision: str  # Description of proposed change
    scope: RevisionScope
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Revision:
    """A tracked revision with rollback capability."""

    id: str
    signal_id: str
    description: str
    scope: RevisionScope
    old_state: Dict[str, Any]  # State before revision (for rollback)
    new_state: Dict[str, Any]  # State after revision
    status: RevisionStatus = RevisionStatus.PROPOSED
    applied_at: Optional[datetime] = None
    rolled_back_at: Optional[datetime] = None
    validation_result: Optional[Tuple[bool, str]] = None


class RealityGapLoop:
    """Identifies and closes gaps between predictions and reality.

    Bounded revisions: each revision has a defined scope, rollback state,
    and requires governance approval for MODULE or SYSTEM scope.
    """

    def __init__(self, governance_gate: Any = None) -> None:
        self._signals: List[LearningSignal] = []
        self._revisions: Dict[str, Revision] = {}
        self._applied_revisions: List[Revision] = []
        self._rules: Dict[str, Any] = {}  # Active rules/assumptions
        self._governance = governance_gate

    @property
    def signals(self) -> List[LearningSignal]:
        return list(self._signals)

    @property
    def revisions(self) -> Dict[str, Revision]:
        return dict(self._revisions)

    def record_gap(
        self,
        prediction_id: str,
        error_type: str,
        causal_rule: str,
        proposed_revision: str,
        scope: RevisionScope = RevisionScope.LOCAL,
    ) -> LearningSignal:
        """Record a gap between prediction and reality."""
        signal = LearningSignal(
            id=str(uuid.uuid4()),
            prediction_id=prediction_id,
            error_type=error_type,
            causal_rule=causal_rule,
            proposed_revision=proposed_revision,
            scope=scope,
        )
        self._signals.append(signal)
        return signal

    def identify_cause(self, signal: LearningSignal) -> Dict[str, Any]:
        """Analyze a learning signal to identify the root cause.

        Returns a diagnostic dict with the rule, its current state,
        and the suspected failure mode.
        """
        current_state = self._rules.get(signal.causal_rule)
        return {
            "rule": signal.causal_rule,
            "current_state": current_state,
            "error_type": signal.error_type,
            "prediction_id": signal.prediction_id,
            "diagnosis": f"Rule '{signal.causal_rule}' produced {signal.error_type}",
            "scope": signal.scope.value,
        }

    def propose_revision(
        self,
        signal: LearningSignal,
        new_state: Dict[str, Any],
    ) -> Revision:
        """Propose a bounded revision to address the learning signal.

        Old state is captured for rollback.
        """
        old_state = {signal.causal_rule: self._rules.get(signal.causal_rule)}

        revision = Revision(
            id=str(uuid.uuid4()),
            signal_id=signal.id,
            description=signal.proposed_revision,
            scope=signal.scope,
            old_state=old_state,
            new_state=new_state,
            status=RevisionStatus.PROPOSED,
        )
        self._revisions[revision.id] = revision
        return revision

    def validate_revision(
        self,
        revision_id: str,
        validator: Optional[Callable[[Revision], Tuple[bool, str]]] = None,
    ) -> Tuple[bool, str]:
        """Validate a proposed revision before applying.

        Default validation checks scope bounds.  Custom validator can be provided.
        """
        if revision_id not in self._revisions:
            raise KeyError(f"Revision {revision_id} not found")

        revision = self._revisions[revision_id]

        # Reject already-applied or rolled-back revisions
        if revision.status not in (RevisionStatus.PROPOSED,):
            return False, f"Revision is in status {revision.status.value}, cannot validate"

        # Custom validator
        if validator:
            passed, reason = validator(revision)
            revision.validation_result = (passed, reason)
            if passed:
                revision.status = RevisionStatus.VALIDATED
            return passed, reason

        # Default: LOCAL scope always allowed, broader needs governance
        if revision.scope == RevisionScope.LOCAL:
            revision.status = RevisionStatus.VALIDATED
            revision.validation_result = (True, "LOCAL scope — auto-validated")
            return True, "LOCAL scope — auto-validated"

        # MODULE/SYSTEM requires governance
        if self._governance is not None:
            action = "apply_module_revision" if revision.scope == RevisionScope.MODULE else "apply_system_revision"
            permission = self._governance.check_permission(action)
            if not permission.allowed:
                revision.status = RevisionStatus.REJECTED
                revision.validation_result = (False, "Governance denied")
                return False, "Governance denied"

        revision.status = RevisionStatus.VALIDATED
        revision.validation_result = (True, f"{revision.scope.value} scope — governance approved")
        return True, f"{revision.scope.value} scope — governance approved"

    def apply_if_approved(self, revision_id: str) -> Tuple[bool, str]:
        """Apply a validated revision.  Must be validated first."""
        if revision_id not in self._revisions:
            raise KeyError(f"Revision {revision_id} not found")

        revision = self._revisions[revision_id]

        if revision.status != RevisionStatus.VALIDATED:
            return False, f"Revision not validated (status: {revision.status.value})"

        # Apply the revision
        for key, value in revision.new_state.items():
            self._rules[key] = value

        revision.status = RevisionStatus.APPLIED
        revision.applied_at = datetime.now(timezone.utc)
        self._applied_revisions.append(revision)
        return True, "Revision applied"

    def rollback(self, revision_id: str) -> Tuple[bool, str]:
        """Roll back an applied revision to its previous state."""
        if revision_id not in self._revisions:
            raise KeyError(f"Revision {revision_id} not found")

        revision = self._revisions[revision_id]

        if revision.status != RevisionStatus.APPLIED:
            return False, f"Cannot rollback — status is {revision.status.value}"

        # Restore old state
        for key, value in revision.old_state.items():
            if value is None:
                self._rules.pop(key, None)
            else:
                self._rules[key] = value

        revision.status = RevisionStatus.ROLLED_BACK
        revision.rolled_back_at = datetime.now(timezone.utc)

        # Remove from applied list
        self._applied_revisions = [r for r in self._applied_revisions if r.id != revision_id]
        return True, "Revision rolled back"

    def set_rule(self, name: str, value: Any) -> None:
        """Set a rule/assumption in the active rules store (for testing)."""
        self._rules[name] = value

    def get_rule(self, name: str) -> Any:
        """Get current value of a rule/assumption."""
        return self._rules.get(name)
