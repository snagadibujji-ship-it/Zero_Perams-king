"""
Cosmic Microkernel — Unified Cognitive Runtime
===============================================

The single entry point for all AXIMA queries. Manages:
- Feature-flag-based routing (legacy/shadow/canary/cosmic)
- Trace collection for every query
- Budget enforcement via CognitiveScheduler
- Cancellation support via threading.Event
- Graceful shutdown
- Plugin dispatch through CapabilityRegistry

Runtime Mode (AXIMA_RUNTIME_MODE env var):
- 'legacy': Delegates entirely to old axima.py router
- 'shadow': Runs both old and new, compares, returns old result
- 'canary': Routes N% to new pipeline (default 10%)
- 'cosmic': Full new pipeline only
"""

from __future__ import annotations

import hashlib
import logging
import os
import threading
import time
import uuid
from typing import Any, Dict, Optional

from ..contracts.query import (
    AximaResponseV2,
    ExecutionResult,
    QueryEnvelope,
    ResourceBudgetSpec,
    TruthLevel,
)
from .event_ledger import EventLedger
from .legacy_adapter import LegacyAdapter
from .registry import CapabilityRegistry, HealthStatus
from .scheduler import CognitiveScheduler, ResourceBudget
from .trace import QueryTrace

logger = logging.getLogger(__name__)


class RuntimeMode:
    """Valid runtime mode constants."""

    LEGACY = "legacy"
    SHADOW = "shadow"
    CANARY = "canary"
    COSMIC = "cosmic"

    ALL = frozenset({LEGACY, SHADOW, CANARY, COSMIC})


class CosmicMicrokernel:
    """Unified cognitive runtime for AXIMA.

    Orchestrates query processing through configurable pipelines with
    full observability and resource management.

    Usage::

        kernel = CosmicMicrokernel()
        response = kernel.process_query("solve x^2 = 4")
        print(response.answer)
        print(response.truth_level)

        # Graceful shutdown
        kernel.shutdown()
    """

    def __init__(
        self,
        mode: Optional[str] = None,
        ledger_path: Optional[str] = None,
        canary_percent: float = 10.0,
        max_concurrent: int = 16,
    ) -> None:
        """Initialize the microkernel.

        Args:
            mode: Runtime mode override. If None, reads AXIMA_RUNTIME_MODE env.
            ledger_path: Path for event ledger persistence.
            canary_percent: Percentage of queries routed to new pipeline in canary mode.
            max_concurrent: Maximum concurrent query executions.
        """
        # Determine runtime mode
        self._mode = self._resolve_mode(mode)
        self._canary_percent = canary_percent
        self._canary_counter = 0
        self._canary_lock = threading.Lock()

        # Core subsystems
        self._registry = CapabilityRegistry()
        self._scheduler = CognitiveScheduler(max_concurrent=max_concurrent)
        self._ledger = EventLedger(path=ledger_path)
        self._legacy_adapter = LegacyAdapter()

        # State
        self._shutdown_event = threading.Event()
        self._query_count = 0
        self._query_lock = threading.Lock()

        # Auto-discover plugins
        self._registry.auto_discover()

        logger.info(f"CosmicMicrokernel initialized in '{self._mode}' mode")

    @staticmethod
    def _resolve_mode(mode: Optional[str]) -> str:
        """Resolve the runtime mode from argument or environment."""
        if mode is not None:
            resolved = mode.lower().strip()
        else:
            resolved = os.environ.get("AXIMA_RUNTIME_MODE", "legacy").lower().strip()

        if resolved not in RuntimeMode.ALL:
            logger.warning(
                f"Unknown runtime mode '{resolved}', falling back to 'legacy'"
            )
            resolved = RuntimeMode.LEGACY

        return resolved

    @property
    def mode(self) -> str:
        """Current runtime mode."""
        return self._mode

    @property
    def registry(self) -> CapabilityRegistry:
        """Access the capability registry."""
        return self._registry

    @property
    def scheduler(self) -> CognitiveScheduler:
        """Access the cognitive scheduler."""
        return self._scheduler

    @property
    def ledger(self) -> EventLedger:
        """Access the event ledger."""
        return self._ledger

    def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        mode: str = "deep",
        cancel_event: Optional[threading.Event] = None,
        resource_budget: Optional[ResourceBudgetSpec] = None,
        **kwargs: Any,
    ) -> AximaResponseV2:
        """Process a query through the configured pipeline.

        Args:
            query: The user's input query.
            session_id: Optional session identifier for continuity.
            mode: Explanation mode (deep, simple, bullets, etc.).
            cancel_event: Optional external cancellation signal.
            resource_budget: Optional resource constraints override.
            **kwargs: Additional context passed to engines.

        Returns:
            AximaResponseV2 with the answer and full metadata.
        """
        if self._shutdown_event.is_set():
            return self._error_response(
                "System is shutting down", query=query, mode=mode
            )

        # Create query envelope
        query_id = str(uuid.uuid4())
        budget = resource_budget or ResourceBudgetSpec()
        envelope = QueryEnvelope(
            raw_input=query,
            query_id=query_id,
            session_id=session_id,
            requested_mode=mode,
            resource_budget=budget,
        )

        # Create trace
        trace = QueryTrace(query_id=query_id)
        trace.add_event("input", {"raw": query, "mode": mode, "session_id": session_id})

        # Merge cancellation
        effective_cancel = cancel_event or threading.Event()

        # Track query count
        with self._query_lock:
            self._query_count += 1

        # Record in ledger
        self._ledger.append(
            "query_start",
            {"query": query, "mode": mode, "runtime_mode": self._mode},
            query_id=query_id,
            session_id=session_id,
        )

        start_time = time.time()

        try:
            # Route based on runtime mode
            if self._mode == RuntimeMode.LEGACY:
                response = self._run_legacy(envelope, trace, effective_cancel)
            elif self._mode == RuntimeMode.SHADOW:
                response = self._run_shadow(envelope, trace, effective_cancel)
            elif self._mode == RuntimeMode.CANARY:
                response = self._run_canary(envelope, trace, effective_cancel)
            elif self._mode == RuntimeMode.COSMIC:
                response = self._run_cosmic(envelope, trace, effective_cancel)
            else:
                response = self._run_legacy(envelope, trace, effective_cancel)

        except Exception as exc:
            trace.add_event("error", {"type": type(exc).__name__, "msg": str(exc)})
            response = self._error_response(str(exc), query=query, mode=mode)

        # Finalize
        elapsed_ms = (time.time() - start_time) * 1000.0
        response.latency_ms = elapsed_ms
        response.trace_id = trace.trace_id

        trace.add_event("respond", {
            "answer_length": len(response.answer) if response.answer else 0,
            "engine": response.engine,
            "truth_level": response.truth_level.value,
            "latency_ms": elapsed_ms,
        })

        # Record completion in ledger
        self._ledger.append(
            "query_complete",
            {
                "engine": response.engine,
                "truth_level": response.truth_level.value,
                "latency_ms": elapsed_ms,
                "status": "success" if response.answer else "no_answer",
            },
            query_id=query_id,
            session_id=session_id,
        )

        return response

    def _run_legacy(
        self,
        envelope: QueryEnvelope,
        trace: QueryTrace,
        cancel: threading.Event,
    ) -> AximaResponseV2:
        """Execute using the legacy adapter only."""
        trace.add_event("route", {"target": "legacy", "reason": "legacy mode"})

        with trace.timed("execute", {"engine": "legacy"}):
            result = self._legacy_adapter.execute(
                envelope.raw_input,
                mode=envelope.requested_mode,
                cancel_event=cancel,
            )

        return self._result_to_response(result, envelope)

    def _run_shadow(
        self,
        envelope: QueryEnvelope,
        trace: QueryTrace,
        cancel: threading.Event,
    ) -> AximaResponseV2:
        """Run both legacy and cosmic, compare, return legacy result.

        The cosmic result is logged for comparison but never returned to the user.
        """
        trace.add_event("route", {"target": "shadow", "reason": "shadow mode"})

        # Run legacy (authoritative)
        with trace.timed("execute", {"engine": "legacy", "role": "authoritative"}):
            legacy_result = self._legacy_adapter.execute(
                envelope.raw_input,
                mode=envelope.requested_mode,
                cancel_event=cancel,
            )

        # Run cosmic (shadow, non-blocking)
        cosmic_result: Optional[ExecutionResult] = None
        try:
            with trace.timed("execute", {"engine": "cosmic", "role": "shadow"}):
                cosmic_result = self._execute_cosmic_pipeline(envelope, trace, cancel)
        except Exception as exc:
            trace.add_event("error", {
                "source": "shadow_cosmic",
                "type": type(exc).__name__,
                "msg": str(exc),
            })

        # Compare and log divergence
        if cosmic_result and legacy_result:
            self._log_shadow_comparison(
                envelope, legacy_result, cosmic_result, trace
            )

        # Always return legacy result
        return self._result_to_response(legacy_result, envelope)

    def _run_canary(
        self,
        envelope: QueryEnvelope,
        trace: QueryTrace,
        cancel: threading.Event,
    ) -> AximaResponseV2:
        """Route a percentage of queries to cosmic, rest to legacy."""
        use_cosmic = self._should_canary()
        target = "cosmic" if use_cosmic else "legacy"
        trace.add_event("route", {
            "target": target,
            "reason": f"canary mode ({self._canary_percent}%)",
        })

        if use_cosmic:
            return self._run_cosmic(envelope, trace, cancel)
        else:
            return self._run_legacy(envelope, trace, cancel)

    def _run_cosmic(
        self,
        envelope: QueryEnvelope,
        trace: QueryTrace,
        cancel: threading.Event,
    ) -> AximaResponseV2:
        """Full new pipeline execution."""
        trace.add_event("route", {"target": "cosmic", "reason": "cosmic mode"})

        with trace.timed("execute", {"engine": "cosmic"}):
            result = self._execute_cosmic_pipeline(envelope, trace, cancel)

        return self._result_to_response(result, envelope)

    def _execute_cosmic_pipeline(
        self,
        envelope: QueryEnvelope,
        trace: QueryTrace,
        cancel: threading.Event,
    ) -> ExecutionResult:
        """Execute the new cognitive pipeline.

        Currently delegates to registered capabilities via the registry.
        Falls back to legacy if no suitable capability is found.
        """
        # Determine query type (simple heuristic for now)
        query_type = self._classify_query(envelope.normalized_input or envelope.raw_input)
        trace.add_event("parse", {"classified_type": query_type})

        # Find best capability
        cap = self._registry.get_best_for(query_type)

        if cap and cap.handler:
            try:
                # Execute through the registered capability
                handler = cap.handler
                if callable(handler):
                    answer = handler(envelope.raw_input)
                    return ExecutionResult(
                        answer=str(answer) if answer else None,
                        status="success" if answer else "no_answer",
                        engine=f"cosmic/{cap.name}",
                        cost_ms=0.0,
                    )
            except Exception as exc:
                trace.add_event("error", {
                    "source": f"capability/{cap.name}",
                    "type": type(exc).__name__,
                    "msg": str(exc),
                })

        # Fallback: delegate to legacy adapter
        trace.add_event("fallback", {"from": "cosmic", "to": "legacy", "reason": "no capability"})
        return self._legacy_adapter.execute(
            envelope.raw_input,
            mode=envelope.requested_mode,
            cancel_event=cancel,
        )

    def _classify_query(self, query: str) -> str:
        """Simple query classification (placeholder for future NLU)."""
        lower = query.lower()
        if any(kw in lower for kw in ("solve", "calculate", "compute", "integral", "derivative", "x^", "x =")):
            return "math"
        if any(kw in lower for kw in ("force", "velocity", "energy", "momentum", "gravity", "newton")):
            return "physics"
        if any(kw in lower for kw in ("code", "function", "algorithm", "implement", "program")):
            return "code"
        if any(kw in lower for kw in ("what is", "who is", "define", "explain")):
            return "knowledge"
        return "general"

    def _should_canary(self) -> bool:
        """Determine if this query should use the canary (cosmic) pipeline."""
        with self._canary_lock:
            self._canary_counter += 1
            # Every N queries, route to cosmic (where N = 100/percent)
            interval = max(1, int(100.0 / self._canary_percent))
            return (self._canary_counter % interval) == 0

    def _log_shadow_comparison(
        self,
        envelope: QueryEnvelope,
        legacy: ExecutionResult,
        cosmic: ExecutionResult,
        trace: QueryTrace,
    ) -> None:
        """Log comparison between legacy and cosmic results."""
        legacy_hash = hashlib.sha256(
            (legacy.answer or "").encode()
        ).hexdigest()[:16]
        cosmic_hash = hashlib.sha256(
            (cosmic.answer or "").encode()
        ).hexdigest()[:16]

        diverged = legacy_hash != cosmic_hash

        trace.add_event("shadow_compare", {
            "diverged": diverged,
            "legacy_hash": legacy_hash,
            "cosmic_hash": cosmic_hash,
            "legacy_engine": legacy.engine,
            "cosmic_engine": cosmic.engine,
            "legacy_status": legacy.status,
            "cosmic_status": cosmic.status,
        })

        if diverged:
            self._ledger.append(
                "shadow_divergence",
                {
                    "query": envelope.raw_input[:200],
                    "legacy_hash": legacy_hash,
                    "cosmic_hash": cosmic_hash,
                    "legacy_engine": legacy.engine,
                    "cosmic_engine": cosmic.engine,
                },
                query_id=envelope.query_id,
                session_id=envelope.session_id,
            )

    def _result_to_response(
        self,
        result: ExecutionResult,
        envelope: QueryEnvelope,
    ) -> AximaResponseV2:
        """Convert an ExecutionResult to the canonical AximaResponseV2."""
        answer = result.answer or ""

        # Determine truth level from engine
        truth_level = self._legacy_adapter.get_truth_level(result.engine)

        # Confidence heuristic
        confidence = 0.0
        if result.status == "success" and answer:
            confidence = 0.8
            if truth_level == TruthLevel.DIRECT_FACT:
                confidence = 0.95
            elif truth_level == TruthLevel.DERIVED:
                confidence = 0.85
            elif truth_level == TruthLevel.TEMPLATE:
                confidence = 0.7
        elif result.status == "no_answer":
            truth_level = TruthLevel.UNSUPPORTED
            confidence = 0.0

        return AximaResponseV2(
            answer=answer,
            truth_level=truth_level,
            calibrated_confidence=confidence,
            claims=result.claims,
            citations=[],
            derivation=[],
            caveats=[f"Error: {result.error}"] if result.error else [],
            unknowns=[],
            verification=None,
            language="en",
            mode=envelope.requested_mode,
            latency_ms=result.cost_ms,
            engine=result.engine,
        )

    @staticmethod
    def _error_response(
        error_msg: str,
        query: str = "",
        mode: str = "deep",
    ) -> AximaResponseV2:
        """Create an error response."""
        return AximaResponseV2(
            answer="",
            truth_level=TruthLevel.UNSUPPORTED,
            calibrated_confidence=0.0,
            caveats=[f"Error: {error_msg}"],
            mode=mode,
            engine="error",
        )

    def shutdown(self) -> None:
        """Graceful shutdown: cancel running tasks, close ledger."""
        logger.info("CosmicMicrokernel shutting down...")
        self._shutdown_event.set()
        self._scheduler.shutdown()
        self._ledger.close()
        logger.info("CosmicMicrokernel shutdown complete")

    @property
    def is_shutdown(self) -> bool:
        """Whether shutdown has been initiated."""
        return self._shutdown_event.is_set()

    @property
    def query_count(self) -> int:
        """Total queries processed since startup."""
        with self._query_lock:
            return self._query_count

    def health(self) -> Dict[str, Any]:
        """System health summary."""
        cap_health = self._registry.health_check_all()
        healthy = sum(1 for h in cap_health.values() if h == HealthStatus.HEALTHY)
        return {
            "mode": self._mode,
            "shutdown": self._shutdown_event.is_set(),
            "query_count": self.query_count,
            "capabilities_registered": self._registry.count,
            "capabilities_healthy": healthy,
            "ledger_events": self._ledger.count,
        }
