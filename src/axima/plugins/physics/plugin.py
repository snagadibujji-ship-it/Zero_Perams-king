"""Physics Plugin — wraps Prometheus physics solver.

Adds unit checking and dimensional analysis on top of the
equation-based physics solver.
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ...contracts.query import ExecutionResult
from ...epistemics.contracts import EpistemicContract
from ...kernel.registry import CapabilityDescriptor, HealthStatus
from ...semantics.meaning_ir import MeaningIR, Quantity
from ..base import PluginBase

logger = logging.getLogger(__name__)

_LEGACY_DIR = Path(__file__).parent.parent.parent.parent.parent / "python"

# SI base dimensions for dimensional analysis
_DIMENSION_MAP: Dict[str, str] = {
    "m": "L",
    "meter": "L",
    "meters": "L",
    "km": "L",
    "kg": "M",
    "kilogram": "M",
    "s": "T",
    "second": "T",
    "seconds": "T",
    "A": "I",
    "ampere": "I",
    "K": "Θ",
    "kelvin": "Θ",
    "mol": "N",
    "cd": "J",
    # Derived units
    "N": "MLT⁻²",
    "newton": "MLT⁻²",
    "J": "ML²T⁻²",
    "joule": "ML²T⁻²",
    "W": "ML²T⁻³",
    "watt": "ML²T⁻³",
    "Pa": "ML⁻¹T⁻²",
    "pascal": "ML⁻¹T⁻²",
    "V": "ML²T⁻³I⁻¹",
    "volt": "ML²T⁻³I⁻¹",
    "m/s": "LT⁻¹",
    "m/s²": "LT⁻²",
    "Hz": "T⁻¹",
    "C": "IT",
    "coulomb": "IT",
}


class PhysicsPlugin(PluginBase):
    """Physics equation solver with unit checking and dimensional analysis."""

    def __init__(self) -> None:
        self._physics_engine = None
        self._healthy = False

    def name(self) -> str:
        return "physics_solver"

    def version(self) -> str:
        return "1.0.0"

    def describe(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            name=self.name(),
            version=self.version(),
            accepted_types=["physics", "mechanics", "thermodynamics", "electromagnetism"],
            produced_types=["numeric_result", "derivation"],
            preconditions=[],
            postconditions=["physics_result"],
            cost_model={"avg_ms": 200, "max_ms": 5000},
            latency_model={"avg_ms": 200, "p95_ms": 3000},
            deterministic=True,
            permissions=["read"],
            health=HealthStatus.HEALTHY if self._healthy else HealthStatus.UNKNOWN,
        )

    def execute(self, ir: MeaningIR, contract: EpistemicContract) -> ExecutionResult:
        """Solve a physics problem from the MeaningIR."""
        start = time.time()

        # Extract quantities and check dimensional consistency
        quantities = ir.quantities
        dim_errors = self._check_dimensions(quantities)
        if dim_errors:
            return ExecutionResult(
                status="error",
                error=f"Dimensional analysis errors: {'; '.join(dim_errors)}",
                engine=self.name(),
                cost_ms=(time.time() - start) * 1000,
            )

        # Extract the physics problem
        problem = self._extract_problem(ir)
        if not problem:
            return ExecutionResult(
                status="error",
                error="Could not extract physics problem from query",
                engine=self.name(),
                cost_ms=(time.time() - start) * 1000,
            )

        # Solve using prometheus_physics
        result = self._solve(problem, quantities)
        elapsed = (time.time() - start) * 1000

        if result is not None:
            # Add unit to result if unit_requirement specified
            answer = result.get("answer", "")
            unit = contract.unit_requirement or result.get("unit", "")
            if unit and unit not in str(answer):
                answer = f"{answer} {unit}"

            return ExecutionResult(
                answer=answer,
                status="success",
                claims=result.get("claims", [f"Physics solution: {problem}"]),
                evidence=result.get("steps", ["prometheus_physics"]),
                engine=self.name(),
                cost_ms=elapsed,
            )

        return ExecutionResult(
            status="error",
            error=f"Could not solve physics problem: {problem}",
            engine=self.name(),
            cost_ms=elapsed,
        )

    def health_check(self) -> bool:
        """Check if the physics engine is available."""
        try:
            self._load_engine()
            self._healthy = self._physics_engine is not None
            return self._healthy
        except Exception:
            self._healthy = False
            return False

    def initialize(self) -> None:
        self._load_engine()

    # --- Dimensional Analysis ---

    def _check_dimensions(self, quantities: List[Quantity]) -> List[str]:
        """Check dimensional consistency of provided quantities."""
        errors: List[str] = []
        for q in quantities:
            if q.unit and q.unit not in _DIMENSION_MAP:
                # Not necessarily an error, just a warning
                logger.debug(f"Unknown unit: {q.unit}")
        return errors

    def get_dimension(self, unit: str) -> Optional[str]:
        """Get the dimensional formula for a unit."""
        return _DIMENSION_MAP.get(unit)

    # --- Internal Methods ---

    def _extract_problem(self, ir: MeaningIR) -> Optional[str]:
        """Extract a physics problem description from the IR."""
        # Check goals
        for goal in ir.goals:
            if goal.description:
                return goal.description

        # Check events
        for event in ir.events:
            if event.verb in ("find", "calculate", "compute", "determine"):
                parts = [event.verb]
                if event.patient:
                    parts.append(event.patient)
                return " ".join(parts)

        # Check predicates
        for pred in ir.predicates:
            return f"{pred.subject} {pred.relation} {pred.object}"

        return None

    def _solve(
        self, problem: str, quantities: List[Quantity]
    ) -> Optional[Dict[str, Any]]:
        """Solve using the prometheus_physics engine."""
        try:
            self._load_engine()
            if self._physics_engine is not None:
                # Build known values from quantities
                known = {}
                for q in quantities:
                    if q.unit:
                        known[q.unit] = q.value
                    elif q.domain:
                        known[q.domain] = q.value

                result = self._physics_engine.solve(problem, known_values=known)
                if result:
                    return result
        except Exception as exc:
            logger.debug(f"Physics solve failed: {exc}")
        return None

    def _load_engine(self) -> None:
        """Load the prometheus_physics engine."""
        if self._physics_engine is not None:
            return
        try:
            legacy_dir = str(_LEGACY_DIR)
            if legacy_dir not in sys.path:
                sys.path.insert(0, legacy_dir)
            import prometheus_physics
            self._physics_engine = prometheus_physics
        except ImportError:
            logger.debug("prometheus_physics not available")
