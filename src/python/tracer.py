"""
AXIMA Tracer — Structured Query Tracing
Every query records its full journey: detection → routing → engine → result.

Usage:
    from tracer import Tracer, get_tracer

    tracer = get_tracer()
    with tracer.trace("solve x^2=4") as t:
        t.record_detection(language="en", confidence=1.0)
        t.record_routing(engine="math", reason="regex match")
        t.record_result(answer="x=2", status="success")

    # Get last trace as JSON
    print(tracer.last_trace_json())
"""

import time
import json
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


@dataclass
class TraceRecord:
    """Complete trace of a single query through AXIMA."""
    query: str = ""
    timestamp: float = 0.0

    # Language detection
    detected_language: str = ""
    language_confidence: float = 0.0
    english_query: str = ""

    # Routing
    router_decision: str = ""        # Which engine was chosen
    routing_reason: str = ""         # Why (regex match, intent, etc.)
    fallback_chain: List[str] = field(default_factory=list)

    # Execution
    engine: str = ""                 # Final engine that answered
    latency_ms: float = 0.0
    confidence: float = 0.0

    # Result
    result: str = ""                 # Answer (truncated to 200 chars)
    result_source: str = ""          # truth label source
    status: str = "pending"          # success | fallback | error | no_answer

    # Errors
    errors: List[Dict[str, str]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict, excluding empty fields."""
        d = asdict(self)
        return {k: v for k, v in d.items() if v or v == 0}

    def to_json(self) -> str:
        """Convert to compact JSON."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class TraceContext:
    """Context manager for building a trace record."""

    def __init__(self, query: str):
        self.record = TraceRecord(query=query, timestamp=time.time())
        self._start_time = time.time()

    def record_detection(self, language: str, confidence: float,
                        english_query: str = "", intent: str = ""):
        """Record language detection result."""
        self.record.detected_language = language
        self.record.language_confidence = confidence
        self.record.english_query = english_query
        if intent:
            self.record.routing_reason = f"intent={intent}"

    def record_routing(self, engine: str, reason: str = ""):
        """Record which engine was selected and why."""
        self.record.router_decision = engine
        if reason:
            self.record.routing_reason = reason
        self.record.fallback_chain.append(engine)

    def record_fallback(self, from_engine: str, to_engine: str, reason: str = ""):
        """Record a fallback from one engine to another."""
        self.record.fallback_chain.append(f"{from_engine}→{to_engine}")
        if reason:
            self.record.warnings.append(f"Fallback: {reason}")

    def record_result(self, answer: str, status: str = "success",
                     source: str = "", confidence: float = 0.0):
        """Record the final result."""
        self.record.result = answer[:200] if answer else ""
        self.record.status = status
        self.record.result_source = source
        self.record.confidence = confidence
        self.record.engine = self.record.router_decision

    def record_error(self, engine: str, error_type: str, message: str):
        """Record an error that occurred during processing."""
        self.record.errors.append({
            "engine": engine,
            "type": error_type,
            "message": message[:200]
        })

    def finalize(self):
        """Calculate latency and finalize the trace."""
        self.record.latency_ms = round((time.time() - self._start_time) * 1000, 1)
        if not self.record.result and self.record.status == "pending":
            self.record.status = "no_answer"


class Tracer:
    """AXIMA Query Tracer. Stores trace history and provides access."""

    def __init__(self, max_history: int = 1000, enabled: bool = True):
        self.enabled = enabled
        self.max_history = max_history
        self._history: List[TraceRecord] = []
        self._current: Optional[TraceContext] = None

    @contextmanager
    def trace(self, query: str):
        """Context manager for tracing a query.
        
        Usage:
            with tracer.trace("solve x^2=4") as t:
                t.record_detection(...)
                t.record_routing(...)
                t.record_result(...)
        """
        if not self.enabled:
            yield _NullTrace()
            return

        ctx = TraceContext(query)
        self._current = ctx
        try:
            yield ctx
        finally:
            ctx.finalize()
            self._history.append(ctx.record)
            if len(self._history) > self.max_history:
                self._history = self._history[-self.max_history:]
            self._current = None

    @property
    def current(self) -> Optional[TraceContext]:
        """Get the current active trace context (if any)."""
        return self._current

    def last_trace(self) -> Optional[TraceRecord]:
        """Get the most recent trace record."""
        return self._history[-1] if self._history else None

    def last_trace_json(self) -> str:
        """Get last trace as JSON string."""
        rec = self.last_trace()
        return rec.to_json() if rec else "{}"

    def history(self, n: int = 10) -> List[TraceRecord]:
        """Get last N trace records."""
        return self._history[-n:]

    def failures(self, n: int = 10) -> List[TraceRecord]:
        """Get last N failed traces."""
        return [r for r in self._history if r.status in ("error", "no_answer")][-n:]

    def stats(self) -> Dict[str, Any]:
        """Get trace statistics."""
        if not self._history:
            return {"total": 0}

        total = len(self._history)
        statuses = {}
        engines = {}
        total_latency = 0.0

        for r in self._history:
            statuses[r.status] = statuses.get(r.status, 0) + 1
            engines[r.engine] = engines.get(r.engine, 0) + 1
            total_latency += r.latency_ms

        return {
            "total": total,
            "statuses": statuses,
            "engines": engines,
            "avg_latency_ms": round(total_latency / total, 1),
            "error_rate": round(statuses.get("error", 0) / total * 100, 1),
        }

    def clear(self):
        """Clear trace history."""
        self._history.clear()


class _NullTrace:
    """No-op trace context when tracing is disabled."""
    def record_detection(self, **kwargs): pass
    def record_routing(self, **kwargs): pass
    def record_fallback(self, **kwargs): pass
    def record_result(self, **kwargs): pass
    def record_error(self, **kwargs): pass


# ═══════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════

_tracer: Optional[Tracer] = None


def get_tracer(enabled: bool = True) -> Tracer:
    """Get the global tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = Tracer(enabled=enabled)
    return _tracer
