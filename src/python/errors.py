"""
AXIMA Error Architecture — Structured errors replace silent failures.

Every failure must explain: what failed, why, where, recovery suggestion.

Usage:
    from errors import EngineError, RouteError, ParseError

    try:
        result = engine.process(query)
    except EngineError as e:
        tracer.record_error(e.engine, e.error_type, str(e))
        # Fallback or propagate
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class EngineError(Exception):
    """Base error for all AXIMA engine failures."""
    engine: str              # Which engine failed (math, physics, inference, aces, etc.)
    error_type: str          # Category: parse_error, timeout, no_result, internal, load_error
    message: str             # Human-readable description
    query: str = ""          # The input that caused the failure
    recovery: str = ""       # What to try next

    def __str__(self):
        return f"[{self.engine}:{self.error_type}] {self.message}"

    def to_dict(self):
        return {
            "engine": self.engine,
            "type": self.error_type,
            "message": self.message,
            "query": self.query[:100] if self.query else "",
            "recovery": self.recovery,
        }


class MathError(EngineError):
    """Math engine failure."""
    def __init__(self, message: str, query: str = "", recovery: str = ""):
        super().__init__(
            engine="math",
            error_type="math_error",
            message=message,
            query=query,
            recovery=recovery or "Try rephrasing the expression"
        )


class PhysicsError(EngineError):
    """Physics engine failure."""
    def __init__(self, message: str, query: str = "", recovery: str = ""):
        super().__init__(
            engine="physics",
            error_type="physics_error",
            message=message,
            query=query,
            recovery=recovery or "Specify the physics domain or formula"
        )


class InferenceError(EngineError):
    """Knowledge/inference engine failure."""
    def __init__(self, message: str, query: str = "", recovery: str = ""):
        super().__init__(
            engine="inference",
            error_type="inference_error",
            message=message,
            query=query,
            recovery=recovery or "Topic may not be in knowledge base"
        )


class RouteError(EngineError):
    """Routing failure — could not determine which engine to use."""
    def __init__(self, message: str, query: str = "", recovery: str = ""):
        super().__init__(
            engine="router",
            error_type="route_error",
            message=message,
            query=query,
            recovery=recovery or "Try a more specific query"
        )


class ParseError(EngineError):
    """Input parsing failure."""
    def __init__(self, message: str, query: str = "", engine: str = "parser", recovery: str = ""):
        super().__init__(
            engine=engine,
            error_type="parse_error",
            message=message,
            query=query,
            recovery=recovery or "Check input format"
        )


class LoadError(EngineError):
    """Failed to load data or initialize engine."""
    def __init__(self, message: str, engine: str = "unknown", recovery: str = ""):
        super().__init__(
            engine=engine,
            error_type="load_error",
            message=message,
            query="",
            recovery=recovery or "Check data files exist"
        )
