"""
Event Ledger
============

Append-only persistent event storage using JSON Lines format.
Provides querying, replay, and export for audit trails and debugging.

Schema versioning ensures forward compatibility as the event format evolves.
"""

from __future__ import annotations

import json
import os
import time
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional


SCHEMA_VERSION = 1


@dataclass
class LedgerEntry:
    """A single entry in the event ledger."""

    event_type: str
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    schema_version: int = SCHEMA_VERSION
    query_id: Optional[str] = None
    session_id: Optional[str] = None

    def to_json_line(self) -> str:
        """Serialize to a JSON line (no newlines in output)."""
        record = {
            "v": self.schema_version,
            "ts": self.timestamp,
            "type": self.event_type,
            "query_id": self.query_id,
            "session_id": self.session_id,
            "data": self.data,
        }
        return json.dumps(record, separators=(",", ":"), default=str)

    @classmethod
    def from_json_line(cls, line: str) -> "LedgerEntry":
        """Deserialize from a JSON line."""
        record = json.loads(line)
        return cls(
            event_type=record.get("type", "unknown"),
            data=record.get("data", {}),
            timestamp=record.get("ts", 0.0),
            schema_version=record.get("v", 1),
            query_id=record.get("query_id"),
            session_id=record.get("session_id"),
        )


class EventLedger:
    """Append-only event ledger with JSON Lines persistence.

    Thread-safe. Supports querying, replay, and export.

    Usage::

        ledger = EventLedger("/tmp/axima_events.jsonl")
        ledger.append("query_start", {"query": "solve x^2=4"}, query_id="q-1")
        ledger.append("query_complete", {"answer": "x=±2"}, query_id="q-1")

        # Query events
        events = ledger.query(event_type="query_start")

        # Replay
        for entry in ledger.replay():
            process(entry)

        # Export
        ledger.export("/tmp/export.jsonl")
    """

    def __init__(self, path: Optional[str] = None) -> None:
        """Initialize the event ledger.

        Args:
            path: File path for persistent storage. If None, operates in
                  memory-only mode (events are not persisted to disk).
        """
        self._path = path
        self._lock = threading.Lock()
        self._entries: List[LedgerEntry] = []
        self._closed = False

        # Create parent directories if needed
        if self._path:
            parent = Path(self._path).parent
            parent.mkdir(parents=True, exist_ok=True)

            # Load existing entries
            if os.path.isfile(self._path):
                self._load_existing()

    def _load_existing(self) -> None:
        """Load existing entries from the file."""
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entry = LedgerEntry.from_json_line(line)
                            self._entries.append(entry)
                        except (json.JSONDecodeError, KeyError):
                            # Skip malformed lines
                            pass
        except OSError:
            pass

    def append(
        self,
        event_type: str,
        data: Optional[Dict[str, Any]] = None,
        query_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> LedgerEntry:
        """Append an event to the ledger.

        Args:
            event_type: Classification of the event (e.g., "query_start").
            data: Arbitrary event payload.
            query_id: Associated query ID.
            session_id: Associated session ID.

        Returns:
            The created LedgerEntry.

        Raises:
            RuntimeError: If the ledger has been closed.
        """
        if self._closed:
            raise RuntimeError("EventLedger is closed")

        entry = LedgerEntry(
            event_type=event_type,
            data=data or {},
            query_id=query_id,
            session_id=session_id,
        )

        with self._lock:
            self._entries.append(entry)
            if self._path:
                self._persist_entry(entry)

        return entry

    def _persist_entry(self, entry: LedgerEntry) -> None:
        """Write a single entry to the file."""
        try:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(entry.to_json_line() + "\n")
        except OSError as exc:
            # Log but don't crash — memory copy is authoritative
            import logging
            logging.getLogger(__name__).warning(f"Failed to persist event: {exc}")

    def query(
        self,
        event_type: Optional[str] = None,
        query_id: Optional[str] = None,
        session_id: Optional[str] = None,
        since: Optional[float] = None,
        until: Optional[float] = None,
        limit: int = 0,
    ) -> List[LedgerEntry]:
        """Query events with optional filters.

        Args:
            event_type: Filter by event type.
            query_id: Filter by query ID.
            session_id: Filter by session ID.
            since: Only events after this timestamp.
            until: Only events before this timestamp.
            limit: Maximum number of results (0 = unlimited).

        Returns:
            List of matching LedgerEntry objects (newest last).
        """
        with self._lock:
            results = list(self._entries)

        if event_type:
            results = [e for e in results if e.event_type == event_type]
        if query_id:
            results = [e for e in results if e.query_id == query_id]
        if session_id:
            results = [e for e in results if e.session_id == session_id]
        if since is not None:
            results = [e for e in results if e.timestamp >= since]
        if until is not None:
            results = [e for e in results if e.timestamp <= until]

        if limit > 0:
            results = results[-limit:]

        return results

    def replay(
        self,
        since: Optional[float] = None,
        callback: Optional[Callable[[LedgerEntry], None]] = None,
    ) -> Iterator[LedgerEntry]:
        """Replay events in chronological order.

        Args:
            since: Only replay events after this timestamp.
            callback: Optional function called for each event during replay.

        Yields:
            LedgerEntry objects in order.
        """
        with self._lock:
            entries = list(self._entries)

        for entry in entries:
            if since and entry.timestamp < since:
                continue
            if callback:
                callback(entry)
            yield entry

    def export(self, output_path: str) -> int:
        """Export all events to a new JSON Lines file.

        Args:
            output_path: Destination file path.

        Returns:
            Number of events exported.
        """
        with self._lock:
            entries = list(self._entries)

        parent = Path(output_path).parent
        parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(entry.to_json_line() + "\n")

        return len(entries)

    @property
    def count(self) -> int:
        """Total number of events in the ledger."""
        with self._lock:
            return len(self._entries)

    def close(self) -> None:
        """Mark the ledger as closed. No further appends allowed."""
        self._closed = True

    def clear(self) -> None:
        """Clear all in-memory entries and truncate the file.

        WARNING: This is destructive and irreversible.
        """
        with self._lock:
            self._entries.clear()
            if self._path and os.path.isfile(self._path):
                with open(self._path, "w", encoding="utf-8") as f:
                    pass  # Truncate
