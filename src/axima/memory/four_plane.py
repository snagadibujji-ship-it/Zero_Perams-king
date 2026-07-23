"""Four-plane memory architecture for AXIMA."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class RetentionPolicy(Enum):
    """How long to retain a memory entry."""
    SESSION = "session"
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    PERMANENT = "permanent"


class SensitivityLabel(Enum):
    """Sensitivity classification for memory entries."""
    PUBLIC = "public"
    INTERNAL = "internal"
    PRIVATE = "private"
    RESTRICTED = "restricted"


@dataclass
class MemoryEntry:
    """A single entry in any memory plane."""
    id: str
    content: Any
    schema: str
    source: str
    retention_policy: RetentionPolicy
    sensitivity_label: SensitivityLabel
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)


class WorkingMemory:
    """Active context: current goals, context, plan, active claims."""

    def __init__(self) -> None:
        self.goals: List[str] = []
        self.context: Dict[str, Any] = {}
        self.plan: List[str] = []
        self.active_claims: List[str] = []

    def set_goal(self, goal: str) -> None:
        if goal not in self.goals:
            self.goals.append(goal)

    def clear_goal(self, goal: str) -> None:
        if goal in self.goals:
            self.goals.remove(goal)

    def set_context(self, key: str, value: Any) -> None:
        self.context[key] = value

    def clear(self) -> None:
        self.goals.clear()
        self.context.clear()
        self.plan.clear()
        self.active_claims.clear()


class EpisodicMemory:
    """Append-only log of interactions, outcomes, and corrections."""

    def __init__(self) -> None:
        self._episodes: List[MemoryEntry] = []

    def append(self, entry: MemoryEntry) -> None:
        self._episodes.append(entry)

    def get_recent(self, n: int = 10) -> List[MemoryEntry]:
        return self._episodes[-n:]

    def search(self, query: str) -> List[MemoryEntry]:
        """Simple keyword search over episodes."""
        results = []
        q_lower = query.lower()
        for ep in self._episodes:
            content_str = str(ep.content).lower()
            if q_lower in content_str:
                results.append(ep)
        return results

    @property
    def count(self) -> int:
        return len(self._episodes)

    @property
    def all_entries(self) -> List[MemoryEntry]:
        return list(self._episodes)


class SemanticMemory:
    """Facts, concepts, and beliefs with provenance."""

    def __init__(self) -> None:
        self._entries: Dict[str, MemoryEntry] = {}

    def store(self, entry: MemoryEntry) -> None:
        self._entries[entry.id] = entry

    def get(self, entry_id: str) -> Optional[MemoryEntry]:
        return self._entries.get(entry_id)

    def search(self, query: str) -> List[MemoryEntry]:
        results = []
        q_lower = query.lower()
        for entry in self._entries.values():
            content_str = str(entry.content).lower()
            if q_lower in content_str:
                results.append(entry)
        return results

    def remove(self, entry_id: str) -> bool:
        if entry_id in self._entries:
            del self._entries[entry_id]
            return True
        return False

    @property
    def count(self) -> int:
        return len(self._entries)


class ProceduralMemory:
    """Verified skills, workflows, and tool policies."""

    def __init__(self) -> None:
        self._procedures: Dict[str, MemoryEntry] = {}

    def store(self, entry: MemoryEntry) -> None:
        self._procedures[entry.id] = entry

    def get(self, entry_id: str) -> Optional[MemoryEntry]:
        return self._procedures.get(entry_id)

    def get_by_tag(self, tag: str) -> List[MemoryEntry]:
        return [e for e in self._procedures.values() if tag in e.tags]

    def remove(self, entry_id: str) -> bool:
        if entry_id in self._procedures:
            del self._procedures[entry_id]
            return True
        return False

    @property
    def count(self) -> int:
        return len(self._procedures)


class FourPlaneMemory:
    """Unified four-plane memory system.

    Every write requires: schema, retention_policy, sensitivity_label, source.
    """

    def __init__(self) -> None:
        self._working = WorkingMemory()
        self._episodic = EpisodicMemory()
        self._semantic = SemanticMemory()
        self._procedural = ProceduralMemory()

    @property
    def working(self) -> WorkingMemory:
        return self._working

    @property
    def episodic(self) -> EpisodicMemory:
        return self._episodic

    @property
    def semantic(self) -> SemanticMemory:
        return self._semantic

    @property
    def procedural(self) -> ProceduralMemory:
        return self._procedural

    def remember(
        self,
        plane: str,
        content: Any,
        schema: str,
        source: str,
        retention_policy: RetentionPolicy = RetentionPolicy.LONG_TERM,
        sensitivity_label: SensitivityLabel = SensitivityLabel.INTERNAL,
        tags: Optional[List[str]] = None,
    ) -> MemoryEntry:
        """Store a memory in the specified plane.

        Args:
            plane: One of 'working', 'episodic', 'semantic', 'procedural'
            content: The data to remember
            schema: Schema identifier for the content
            source: Where this memory came from
            retention_policy: How long to keep it
            sensitivity_label: Access classification
            tags: Optional categorization tags
        """
        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            content=content,
            schema=schema,
            source=source,
            retention_policy=retention_policy,
            sensitivity_label=sensitivity_label,
            tags=tags or [],
        )
        if plane == "episodic":
            self._episodic.append(entry)
        elif plane == "semantic":
            self._semantic.store(entry)
        elif plane == "procedural":
            self._procedural.store(entry)
        elif plane == "working":
            self._working.set_context(entry.id, content)
        else:
            raise ValueError(f"Unknown memory plane: {plane}")
        return entry

    def recall(self, query: str, planes: Optional[List[str]] = None) -> List[MemoryEntry]:
        """Recall memories matching a query across specified planes."""
        if planes is None:
            planes = ["episodic", "semantic", "procedural"]
        results: List[MemoryEntry] = []
        if "episodic" in planes:
            results.extend(self._episodic.search(query))
        if "semantic" in planes:
            results.extend(self._semantic.search(query))
        if "procedural" in planes:
            for entry in self._procedural._procedures.values():
                if query.lower() in str(entry.content).lower():
                    results.append(entry)
        return results

    def forget(self, entry_id: str) -> bool:
        """Remove a memory entry by ID."""
        if self._semantic.remove(entry_id):
            return True
        if self._procedural.remove(entry_id):
            return True
        return False

    def export(self) -> Dict[str, Any]:
        """Export full memory state for persistence."""
        def serialize_entry(e: MemoryEntry) -> Dict[str, Any]:
            return {
                "id": e.id,
                "content": e.content,
                "schema": e.schema,
                "source": e.source,
                "retention_policy": e.retention_policy.value,
                "sensitivity_label": e.sensitivity_label.value,
                "created_at": e.created_at.isoformat(),
                "tags": e.tags,
            }

        return {
            "working": {
                "goals": self._working.goals,
                "context": self._working.context,
                "plan": self._working.plan,
                "active_claims": self._working.active_claims,
            },
            "episodic": [serialize_entry(e) for e in self._episodic.all_entries],
            "semantic": [serialize_entry(e) for e in self._semantic._entries.values()],
            "procedural": [serialize_entry(e) for e in self._procedural._procedures.values()],
        }

    def import_from(self, data: Dict[str, Any]) -> None:
        """Import memory state from exported data."""
        if "working" in data:
            w = data["working"]
            self._working.goals = w.get("goals", [])
            self._working.context = w.get("context", {})
            self._working.plan = w.get("plan", [])
            self._working.active_claims = w.get("active_claims", [])

        for entry_data in data.get("episodic", []):
            entry = MemoryEntry(
                id=entry_data["id"],
                content=entry_data["content"],
                schema=entry_data["schema"],
                source=entry_data["source"],
                retention_policy=RetentionPolicy(entry_data["retention_policy"]),
                sensitivity_label=SensitivityLabel(entry_data["sensitivity_label"]),
                tags=entry_data.get("tags", []),
            )
            self._episodic.append(entry)

        for entry_data in data.get("semantic", []):
            entry = MemoryEntry(
                id=entry_data["id"],
                content=entry_data["content"],
                schema=entry_data["schema"],
                source=entry_data["source"],
                retention_policy=RetentionPolicy(entry_data["retention_policy"]),
                sensitivity_label=SensitivityLabel(entry_data["sensitivity_label"]),
                tags=entry_data.get("tags", []),
            )
            self._semantic.store(entry)

        for entry_data in data.get("procedural", []):
            entry = MemoryEntry(
                id=entry_data["id"],
                content=entry_data["content"],
                schema=entry_data["schema"],
                source=entry_data["source"],
                retention_policy=RetentionPolicy(entry_data["retention_policy"]),
                sensitivity_label=SensitivityLabel(entry_data["sensitivity_label"]),
                tags=entry_data.get("tags", []),
            )
            self._procedural.store(entry)

    def verify_integrity(self) -> List[str]:
        """Verify memory integrity. Returns list of issues."""
        issues: List[str] = []
        # Check for expired entries
        now = datetime.now(timezone.utc)
        for entry in self._semantic._entries.values():
            if entry.expires_at and entry.expires_at < now:
                issues.append(f"Expired semantic entry: {entry.id}")
        for entry in self._procedural._procedures.values():
            if entry.expires_at and entry.expires_at < now:
                issues.append(f"Expired procedural entry: {entry.id}")
        return issues
