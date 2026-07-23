"""Reality Ledger — bitemporal, append-only event log for fact lifecycle."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import uuid


SCHEMA_VERSION = 1


class EventType(Enum):
    """Types of ledger events."""
    ASSERT = "assert"
    RETRACT = "retract"
    CORRECT = "correct"
    QUERY = "query"


@dataclass
class LedgerEvent:
    """A single immutable event in the reality ledger."""
    event_id: str
    timestamp: datetime
    event_type: EventType
    claim_id: str
    old_value: Optional[str]
    new_value: Optional[str]
    source: str
    transaction_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    valid_time: Tuple[Optional[datetime], Optional[datetime]] = (None, None)
    schema_version: int = SCHEMA_VERSION


class RealityLedger:
    """Bitemporal, append-only event log with deterministic rebuild.

    Tracks both valid_time (when a fact was true in reality) and
    transaction_time (when we recorded it).
    """

    def __init__(self) -> None:
        self._events: List[LedgerEvent] = []
        # Current state: claim_id -> latest value (None means retracted)
        self._current_state: Dict[str, Optional[str]] = {}
        self._schema_version: int = SCHEMA_VERSION

    @property
    def schema_version(self) -> int:
        return self._schema_version

    @property
    def events(self) -> List[LedgerEvent]:
        return list(self._events)

    def _append(self, event: LedgerEvent) -> LedgerEvent:
        """Append an event (internal, enforces append-only)."""
        self._events.append(event)
        return event

    def assert_fact(
        self,
        claim_id: str,
        value: str,
        source: str,
        valid_time: Tuple[Optional[datetime], Optional[datetime]] = (None, None),
    ) -> LedgerEvent:
        """Assert a new fact."""
        now = datetime.now(timezone.utc)
        event = LedgerEvent(
            event_id=str(uuid.uuid4()),
            timestamp=now,
            event_type=EventType.ASSERT,
            claim_id=claim_id,
            old_value=self._current_state.get(claim_id),
            new_value=value,
            source=source,
            transaction_time=now,
            valid_time=valid_time,
        )
        self._append(event)
        self._current_state[claim_id] = value
        return event

    def retract(
        self,
        claim_id: str,
        source: str,
        valid_time: Tuple[Optional[datetime], Optional[datetime]] = (None, None),
    ) -> LedgerEvent:
        """Retract a fact."""
        now = datetime.now(timezone.utc)
        old_value = self._current_state.get(claim_id)
        event = LedgerEvent(
            event_id=str(uuid.uuid4()),
            timestamp=now,
            event_type=EventType.RETRACT,
            claim_id=claim_id,
            old_value=old_value,
            new_value=None,
            source=source,
            transaction_time=now,
            valid_time=valid_time,
        )
        self._append(event)
        self._current_state[claim_id] = None
        return event

    def correct(
        self,
        claim_id: str,
        new_value: str,
        source: str,
        valid_time: Tuple[Optional[datetime], Optional[datetime]] = (None, None),
    ) -> LedgerEvent:
        """Correct a fact (supersedes previous value)."""
        now = datetime.now(timezone.utc)
        old_value = self._current_state.get(claim_id)
        event = LedgerEvent(
            event_id=str(uuid.uuid4()),
            timestamp=now,
            event_type=EventType.CORRECT,
            claim_id=claim_id,
            old_value=old_value,
            new_value=new_value,
            source=source,
            transaction_time=now,
            valid_time=valid_time,
        )
        self._append(event)
        self._current_state[claim_id] = new_value
        return event

    def query_as_of(
        self,
        claim_id: str,
        transaction_time: Optional[datetime] = None,
        valid_time: Optional[datetime] = None,
    ) -> Optional[str]:
        """Query the value of a claim as of a given transaction_time and/or valid_time.

        If transaction_time is None, uses current state.
        If valid_time is provided, finds the latest event whose valid_time range includes it.
        """
        if transaction_time is None and valid_time is None:
            return self._current_state.get(claim_id)

        # Filter events for this claim up to transaction_time
        relevant_events = [
            e for e in self._events
            if e.claim_id == claim_id and e.event_type != EventType.QUERY
        ]
        if transaction_time is not None:
            relevant_events = [
                e for e in relevant_events if e.transaction_time <= transaction_time
            ]
        if valid_time is not None:
            # Filter to events whose valid_time range includes the query time
            filtered = []
            for e in relevant_events:
                vt_start, vt_end = e.valid_time
                start_ok = vt_start is None or vt_start <= valid_time
                end_ok = vt_end is None or valid_time <= vt_end
                if start_ok and end_ok:
                    filtered.append(e)
            relevant_events = filtered

        if not relevant_events:
            return None

        # Take the latest event by transaction_time
        latest = max(relevant_events, key=lambda e: e.transaction_time)
        if latest.event_type == EventType.RETRACT:
            return None
        return latest.new_value

    def history(self, claim_id: str) -> List[LedgerEvent]:
        """Get full event history for a claim."""
        return [e for e in self._events if e.claim_id == claim_id]

    def rebuild_from_events(self, events: List[LedgerEvent]) -> None:
        """Deterministically rebuild ledger state from an event log."""
        self._events = []
        self._current_state = {}
        for event in sorted(events, key=lambda e: e.transaction_time):
            self._events.append(event)
            if event.event_type == EventType.RETRACT:
                self._current_state[event.claim_id] = None
            elif event.event_type in (EventType.ASSERT, EventType.CORRECT):
                self._current_state[event.claim_id] = event.new_value
            # QUERY events don't modify state

    def get_current(self, claim_id: str) -> Optional[str]:
        """Get the current value of a claim."""
        return self._current_state.get(claim_id)
