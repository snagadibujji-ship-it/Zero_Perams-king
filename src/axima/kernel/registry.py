"""
Capability Registry
===================

Central registry for all engine capabilities (plugins). Provides:
- Registration and unregistration of capabilities
- Query by accepted input types
- Health checking
- Auto-discovery of plugins from the plugins directory
- Selection of the best capability for a given query type
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health state for a registered capability."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class CapabilityDescriptor:
    """Full description of a registered capability (plugin).

    Attributes:
        name: Unique name (e.g., "math_solver", "physics_engine").
        version: Semantic version string.
        accepted_types: Input query types this capability handles.
        produced_types: Output types this capability can produce.
        preconditions: Conditions that must be true before invocation.
        postconditions: Guarantees about the output.
        cost_model: Estimated cost metadata (e.g., {"avg_ms": 50}).
        latency_model: Expected latency characteristics.
        deterministic: Whether same input always yields same output.
        permissions: Required permissions for invocation.
        health: Current health status.
    """

    name: str
    version: str = "1.0.0"
    accepted_types: List[str] = field(default_factory=list)
    produced_types: List[str] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    cost_model: Dict[str, Any] = field(default_factory=dict)
    latency_model: Dict[str, Any] = field(default_factory=dict)
    deterministic: bool = False
    permissions: List[str] = field(default_factory=lambda: ["read"])
    health: HealthStatus = HealthStatus.UNKNOWN

    # The actual callable or engine instance
    handler: Any = None

    # Optional health check function
    health_check_fn: Optional[Callable[[], HealthStatus]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "accepted_types": self.accepted_types,
            "produced_types": self.produced_types,
            "preconditions": self.preconditions,
            "postconditions": self.postconditions,
            "cost_model": self.cost_model,
            "latency_model": self.latency_model,
            "deterministic": self.deterministic,
            "permissions": self.permissions,
            "health": self.health.value,
        }


class CapabilityRegistry:
    """Thread-safe registry for capability plugins.

    Usage::

        registry = CapabilityRegistry()
        registry.register(CapabilityDescriptor(
            name="math_solver",
            accepted_types=["math", "calculate"],
            handler=math_engine,
        ))
        caps = registry.query(accepted_type="math")
        best = registry.get_best_for("math")
    """

    def __init__(self, plugins_dir: Optional[str] = None) -> None:
        self._capabilities: Dict[str, CapabilityDescriptor] = {}
        self._plugins_dir = plugins_dir
        self._lock = __import__("threading").Lock()

    def register(self, descriptor: CapabilityDescriptor) -> None:
        """Register a capability. Overwrites if name already exists."""
        with self._lock:
            self._capabilities[descriptor.name] = descriptor
            logger.info(f"Registered capability: {descriptor.name} v{descriptor.version}")

    def unregister(self, name: str) -> bool:
        """Remove a capability by name. Returns True if found and removed."""
        with self._lock:
            if name in self._capabilities:
                del self._capabilities[name]
                logger.info(f"Unregistered capability: {name}")
                return True
            return False

    def query(
        self,
        accepted_type: Optional[str] = None,
        produced_type: Optional[str] = None,
        healthy_only: bool = False,
    ) -> List[CapabilityDescriptor]:
        """Query capabilities by type or health.

        Args:
            accepted_type: Filter by input type the capability accepts.
            produced_type: Filter by output type the capability produces.
            healthy_only: Only return capabilities with HEALTHY status.

        Returns:
            List of matching CapabilityDescriptor objects.
        """
        with self._lock:
            results = list(self._capabilities.values())

        if accepted_type:
            results = [c for c in results if accepted_type in c.accepted_types]
        if produced_type:
            results = [c for c in results if produced_type in c.produced_types]
        if healthy_only:
            results = [c for c in results if c.health == HealthStatus.HEALTHY]

        return results

    def get(self, name: str) -> Optional[CapabilityDescriptor]:
        """Get a specific capability by name."""
        with self._lock:
            return self._capabilities.get(name)

    def get_best_for(self, query_type: str) -> Optional[CapabilityDescriptor]:
        """Get the best capability for a given query type.

        Selection criteria (in order):
        1. Must accept the query type
        2. Prefer healthy capabilities
        3. Prefer lower latency (from latency_model)
        4. Prefer deterministic
        """
        candidates = self.query(accepted_type=query_type)
        if not candidates:
            return None

        def score(cap: CapabilityDescriptor) -> tuple:
            health_score = 0 if cap.health == HealthStatus.HEALTHY else 1
            latency = cap.latency_model.get("avg_ms", 1000.0)
            deterministic_score = 0 if cap.deterministic else 1
            return (health_score, latency, deterministic_score)

        candidates.sort(key=score)
        return candidates[0]

    def health_check_all(self) -> Dict[str, HealthStatus]:
        """Run health checks on all registered capabilities.

        Returns:
            Dict mapping capability name to its health status.
        """
        results: Dict[str, HealthStatus] = {}
        with self._lock:
            capabilities = list(self._capabilities.values())

        for cap in capabilities:
            if cap.health_check_fn is not None:
                try:
                    cap.health = cap.health_check_fn()
                except Exception:
                    cap.health = HealthStatus.UNHEALTHY
            else:
                # If no health check defined, assume healthy if handler exists
                cap.health = (
                    HealthStatus.HEALTHY if cap.handler is not None
                    else HealthStatus.UNKNOWN
                )
            results[cap.name] = cap.health

        return results

    def list_all(self) -> List[Dict[str, Any]]:
        """List all registered capabilities as dicts."""
        with self._lock:
            return [cap.to_dict() for cap in self._capabilities.values()]

    @property
    def count(self) -> int:
        """Number of registered capabilities."""
        with self._lock:
            return len(self._capabilities)

    def auto_discover(self, plugins_dir: Optional[str] = None) -> int:
        """Auto-discover and register plugins from a directory.

        Looks for Python files with a `register_plugin(registry)` function.

        Args:
            plugins_dir: Directory to scan. Falls back to constructor arg or
                         default path (src/axima/plugins/).

        Returns:
            Number of plugins discovered and registered.
        """
        search_dir = plugins_dir or self._plugins_dir
        if search_dir is None:
            # Default: look for plugins/ relative to this file's package
            search_dir = str(
                Path(__file__).parent.parent / "plugins"
            )

        if not os.path.isdir(search_dir):
            logger.debug(f"Plugins directory does not exist: {search_dir}")
            return 0

        count = 0
        for filename in sorted(os.listdir(search_dir)):
            if not filename.endswith(".py") or filename.startswith("_"):
                continue

            filepath = os.path.join(search_dir, filename)
            module_name = f"axima_plugin_{filename[:-3]}"

            try:
                spec = importlib.util.spec_from_file_location(module_name, filepath)
                if spec is None or spec.loader is None:
                    continue
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                register_fn = getattr(module, "register_plugin", None)
                if callable(register_fn):
                    register_fn(self)
                    count += 1
                    logger.info(f"Auto-discovered plugin: {filename}")
            except Exception as exc:
                logger.warning(f"Failed to load plugin {filename}: {exc}")

        return count
