"""
Distributed Tracing
===================

Full structured trace per query. Provides parent-child span relationships,
timing, attributes, and events for complete query lifecycle observability.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SpanKind(Enum):
    """Classification of trace span types in the query lifecycle."""

    INPUT = "input"       # Raw input reception
    PARSE = "parse"       # Language parsing and IR compilation
    ROUTE = "route"       # Query routing decisions
    EXECUTE = "execute"   # Engine/plugin execution
    VERIFY = "verify"     # Result verification
    RESPOND = "respond"   # Response assembly and output
    ERROR = "error"       # Error handling


@dataclass
class SpanEvent:
    """A timestamped event within a span."""

    name: str
    timestamp: float = field(default_factory=time.time)
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Span:
    """A single span in a distributed trace.

    Represents a unit of work with timing, hierarchy, and metadata.

    Attributes:
        span_id: Unique identifier for this span.
        parent_id: ID of the parent span (None for root).
        kind: Classification of the span type.
        start_time: Unix timestamp when span started.
        end_time: Unix timestamp when span ended (None if still active).
        attributes: Key-value metadata about this span.
        events: Timestamped events within this span.
    """

    span_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None
    kind: SpanKind = SpanKind.INPUT
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[SpanEvent] = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        """Duration in milliseconds."""
        if self.end_time is None:
            return (time.time() - self.start_time) * 1000.0
        return (self.end_time - self.start_time) * 1000.0

    @property
    def is_active(self) -> bool:
        """Whether this span is still active (not ended)."""
        return self.end_time is None

    def end(self) -> None:
        """Mark this span as ended."""
        if self.end_time is None:
            self.end_time = time.time()

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> SpanEvent:
        """Add a timestamped event to this span."""
        event = SpanEvent(name=name, attributes=attributes or {})
        self.events.append(event)
        return event

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a span attribute."""
        self.attributes[key] = value

    def set_error(self, error: str, error_type: str = "unknown") -> None:
        """Mark this span as having an error."""
        self.attributes["error"] = True
        self.attributes["error.message"] = error
        self.attributes["error.type"] = error_type
        self.add_event("exception", {"message": error, "type": error_type})

    def to_dict(self) -> Dict[str, Any]:
        """Serialize span to dictionary."""
        return {
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "kind": self.kind.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "attributes": self.attributes,
            "events": [
                {"name": e.name, "timestamp": e.timestamp, "attributes": e.attributes}
                for e in self.events
            ],
        }


class DistributedTrace:
    """A complete distributed trace for a single query.

    Collects all spans for a query's lifecycle, maintaining parent-child
    relationships for hierarchical timing analysis.

    Usage::

        trace = DistributedTrace(trace_id="q-123")
        root = trace.start_span(SpanKind.INPUT, attributes={"raw": "solve x=2"})
        parse_span = trace.start_span(SpanKind.PARSE, parent_id=root.span_id)
        # ... do parsing ...
        parse_span.end()
        root.end()
        print(trace.to_dict())
    """

    def __init__(self, trace_id: Optional[str] = None) -> None:
        self.trace_id: str = trace_id or str(uuid.uuid4())
        self._spans: Dict[str, Span] = {}
        self._root_id: Optional[str] = None
        self.created_at: float = time.time()

    @property
    def span_count(self) -> int:
        """Number of spans in this trace."""
        return len(self._spans)

    def add_span(self, span: Span) -> Span:
        """Add an existing span to this trace.

        Args:
            span: The span to add.

        Returns:
            The added span (same reference).
        """
        self._spans[span.span_id] = span
        if span.parent_id is None and self._root_id is None:
            self._root_id = span.span_id
        return span

    def start_span(
        self,
        kind: SpanKind,
        parent_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Span:
        """Create and start a new span.

        Args:
            kind: The span kind.
            parent_id: Parent span ID (None for root span).
            attributes: Initial attributes.

        Returns:
            The new active Span.
        """
        span = Span(
            parent_id=parent_id,
            kind=kind,
            attributes=attributes or {},
        )
        self._spans[span.span_id] = span

        if parent_id is None and self._root_id is None:
            self._root_id = span.span_id

        return span

    def end_span(self, span_id: str) -> Optional[Span]:
        """End a span by ID.

        Args:
            span_id: The span to end.

        Returns:
            The ended span, or None if not found.
        """
        span = self._spans.get(span_id)
        if span:
            span.end()
        return span

    def get_root(self) -> Optional[Span]:
        """Get the root span of this trace."""
        if self._root_id:
            return self._spans.get(self._root_id)
        return None

    def get_span(self, span_id: str) -> Optional[Span]:
        """Get a span by ID."""
        return self._spans.get(span_id)

    def get_children(self, span_id: str) -> List[Span]:
        """Get all direct children of a span.

        Args:
            span_id: Parent span ID.

        Returns:
            List of child spans.
        """
        return [
            span for span in self._spans.values()
            if span.parent_id == span_id
        ]

    def get_descendants(self, span_id: str) -> List[Span]:
        """Get all descendants (children, grandchildren, etc.) of a span."""
        descendants: List[Span] = []
        to_visit = [span_id]

        while to_visit:
            current = to_visit.pop(0)
            children = self.get_children(current)
            descendants.extend(children)
            to_visit.extend(c.span_id for c in children)

        return descendants

    def duration(self) -> float:
        """Total trace duration in milliseconds.

        Computed from root span if available, otherwise from
        earliest start to latest end.
        """
        root = self.get_root()
        if root:
            return root.duration_ms

        if not self._spans:
            return 0.0

        earliest = min(s.start_time for s in self._spans.values())
        latest_end = max(
            s.end_time if s.end_time else time.time()
            for s in self._spans.values()
        )
        return (latest_end - earliest) * 1000.0

    def get_spans_by_kind(self, kind: SpanKind) -> List[Span]:
        """Get all spans of a specific kind."""
        return [s for s in self._spans.values() if s.kind == kind]

    def get_error_spans(self) -> List[Span]:
        """Get all spans that have errors."""
        return [
            s for s in self._spans.values()
            if s.attributes.get("error") or s.kind == SpanKind.ERROR
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the full trace to a dictionary."""
        return {
            "trace_id": self.trace_id,
            "created_at": self.created_at,
            "duration_ms": self.duration(),
            "span_count": self.span_count,
            "root_span_id": self._root_id,
            "spans": [span.to_dict() for span in self._spans.values()],
        }

    def summary(self) -> Dict[str, Any]:
        """Compact summary of the trace."""
        kinds_used = list({s.kind.value for s in self._spans.values()})
        errors = self.get_error_spans()

        return {
            "trace_id": self.trace_id,
            "duration_ms": self.duration(),
            "span_count": self.span_count,
            "kinds_used": kinds_used,
            "error_count": len(errors),
            "has_root": self._root_id is not None,
        }


class SpanContext:
    """Context manager for automatic span lifecycle management.

    Usage::

        trace = DistributedTrace()
        with SpanContext(trace, SpanKind.EXECUTE, attributes={"engine": "math"}) as span:
            result = engine.solve(...)
            span.set_attribute("result_status", "success")
    """

    def __init__(
        self,
        trace: DistributedTrace,
        kind: SpanKind,
        parent_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._trace = trace
        self._kind = kind
        self._parent_id = parent_id
        self._attributes = attributes or {}
        self._span: Optional[Span] = None

    def __enter__(self) -> Span:
        self._span = self._trace.start_span(
            self._kind,
            parent_id=self._parent_id,
            attributes=self._attributes,
        )
        return self._span

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._span:
            if exc_type is not None:
                self._span.set_error(
                    str(exc_val) if exc_val else "Unknown error",
                    error_type=exc_type.__name__ if exc_type else "unknown",
                )
            self._span.end()
