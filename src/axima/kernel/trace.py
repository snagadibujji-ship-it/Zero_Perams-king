"""
Execution Tracing
=================

Captures the full lifecycle of a query through the system: input parsing,
routing decisions, engine execution, verification, and response assembly.

Every query gets a QueryTrace that can be serialized for debugging,
auditing, and performance analysis.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TraceEvent:
    """A single event in the query execution timeline."""

    timestamp: float
    stage: str  # input | parse | route | execute | verify | respond | error
    data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "stage": self.stage,
            "data": self.data,
            "duration_ms": self.duration_ms,
        }


class QueryTrace:
    """Collects all trace events for a single query execution.

    Usage::

        trace = QueryTrace(query_id="abc-123")
        trace.add_event("input", {"raw": "solve x^2=4"})
        with trace.timed("execute", {"engine": "math"}):
            result = engine.solve(...)
        trace.add_event("respond", {"answer": "x = ±2"})
    """

    def __init__(self, query_id: str = "", trace_id: str = "") -> None:
        self.query_id = query_id
        self.trace_id = trace_id or query_id
        self.events: List[TraceEvent] = []
        self.start_time: float = time.time()
        self._timer_stack: List[float] = []

    def add_event(
        self,
        stage: str,
        data: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0,
    ) -> TraceEvent:
        """Record a trace event at the current time."""
        event = TraceEvent(
            timestamp=time.time(),
            stage=stage,
            data=data or {},
            duration_ms=duration_ms,
        )
        self.events.append(event)
        return event

    class _TimedContext:
        """Context manager for timed trace sections."""

        def __init__(self, trace: "QueryTrace", stage: str, data: Dict[str, Any]) -> None:
            self._trace = trace
            self._stage = stage
            self._data = data
            self._start: float = 0.0

        def __enter__(self) -> "_TimedContext":
            self._start = time.time()
            return self

        def __exit__(self, *_: Any) -> None:
            elapsed_ms = (time.time() - self._start) * 1000.0
            self._trace.add_event(self._stage, self._data, duration_ms=elapsed_ms)

    def timed(self, stage: str, data: Optional[Dict[str, Any]] = None) -> _TimedContext:
        """Context manager that automatically measures duration."""
        return self._TimedContext(self, stage, data or {})

    def total_duration_ms(self) -> float:
        """Total elapsed time from trace start to now."""
        return (time.time() - self.start_time) * 1000.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the full trace to a dictionary."""
        return {
            "query_id": self.query_id,
            "trace_id": self.trace_id,
            "start_time": self.start_time,
            "total_duration_ms": self.total_duration_ms(),
            "event_count": len(self.events),
            "events": [e.to_dict() for e in self.events],
        }

    def summary(self) -> Dict[str, Any]:
        """Compact summary: stages visited, total time, error count."""
        stages = [e.stage for e in self.events]
        errors = [e for e in self.events if e.stage == "error"]
        engine_events = [e for e in self.events if e.stage == "execute"]
        return {
            "query_id": self.query_id,
            "trace_id": self.trace_id,
            "stages": stages,
            "total_duration_ms": self.total_duration_ms(),
            "event_count": len(self.events),
            "error_count": len(errors),
            "engines_used": [e.data.get("engine", "?") for e in engine_events],
        }
