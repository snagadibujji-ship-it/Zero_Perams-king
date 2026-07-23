"""
Legacy Adapter
==============

Wraps the existing src/python/axima.py router (Axima class with _route_and_solve)
as a capability that can be invoked through the new unified runtime.

Catches all exceptions, wraps results in ExecutionResult, and adds
basic tracing for observability during the migration period.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Optional

from ..contracts.query import ExecutionResult, TruthLevel

logger = logging.getLogger(__name__)

# Path to the old src/python directory
_LEGACY_DIR = Path(__file__).parent.parent.parent.parent / "python"


class LegacyAdapter:
    """Adapter that bridges the old Axima router to the new contract.

    Lazily imports the old Axima class from src/python/axima.py and
    delegates queries through the existing process() pipeline.

    Usage::

        adapter = LegacyAdapter()
        result = adapter.execute("solve x^2 = 4", mode="deep")
        # result is an ExecutionResult
    """

    def __init__(self) -> None:
        self._axima_instance: Any = None
        self._init_lock = threading.Lock()
        self._initialized = False
        self._init_error: Optional[str] = None

    def _ensure_initialized(self) -> bool:
        """Lazy-init the legacy Axima instance. Thread-safe."""
        if self._initialized:
            return self._init_error is None

        with self._init_lock:
            if self._initialized:
                return self._init_error is None

            try:
                legacy_path = str(_LEGACY_DIR.resolve())
                if not os.path.isdir(legacy_path):
                    self._init_error = f"Legacy directory not found: {legacy_path}"
                    self._initialized = True
                    return False

                # Add legacy path to sys.path
                if legacy_path not in sys.path:
                    sys.path.insert(0, legacy_path)

                # Import the old Axima class
                # The old module is at src/python/axima.py which exports get_axima()
                import importlib
                axima_mod = importlib.import_module("axima")

                # get_axima() returns a singleton Axima instance
                get_axima_fn = getattr(axima_mod, "get_axima", None)
                if get_axima_fn and callable(get_axima_fn):
                    self._axima_instance = get_axima_fn()
                else:
                    # Try direct instantiation
                    axima_cls = getattr(axima_mod, "Axima", None)
                    if axima_cls:
                        self._axima_instance = axima_cls()
                    else:
                        self._init_error = "Could not find Axima class or get_axima() in legacy module"
                        self._initialized = True
                        return False

                self._initialized = True
                logger.info("Legacy adapter initialized successfully")
                return True

            except ImportError as exc:
                self._init_error = f"ImportError: {exc}"
                self._initialized = True
                logger.warning(f"Legacy adapter init failed: {exc}")
                return False
            except Exception as exc:
                self._init_error = f"{type(exc).__name__}: {exc}"
                self._initialized = True
                logger.warning(f"Legacy adapter init failed: {exc}")
                return False

    def execute(
        self,
        query: str,
        mode: str = "deep",
        cancel_event: Optional[threading.Event] = None,
    ) -> ExecutionResult:
        """Execute a query through the legacy pipeline.

        Args:
            query: The user's query string.
            mode: Explanation mode (deep, simple, bullets, etc.).
            cancel_event: Optional cancellation signal.

        Returns:
            ExecutionResult wrapping the legacy response.
        """
        start = time.time()

        # Check cancellation before starting
        if cancel_event and cancel_event.is_set():
            return ExecutionResult(
                status="cancelled",
                error="Cancelled before execution",
                engine="legacy",
                cost_ms=0.0,
            )

        # Initialize
        if not self._ensure_initialized():
            return ExecutionResult(
                status="error",
                error=f"Legacy init failed: {self._init_error}",
                engine="legacy",
                cost_ms=(time.time() - start) * 1000.0,
            )

        # Execute
        try:
            response = self._axima_instance.process(query, mode=mode)
            elapsed_ms = (time.time() - start) * 1000.0

            # Check cancellation after execution
            if cancel_event and cancel_event.is_set():
                return ExecutionResult(
                    status="cancelled",
                    error="Cancelled during execution",
                    engine="legacy",
                    cost_ms=elapsed_ms,
                )

            # Extract fields from old AximaResponse
            answer = getattr(response, "answer", None)
            source = getattr(response, "source", "unknown")
            confidence = getattr(response, "confidence", 0.5)

            return ExecutionResult(
                answer=answer if answer else None,
                status="success" if answer else "no_answer",
                claims=[],
                evidence=[f"legacy/{source}"],
                error=None,
                cost_ms=elapsed_ms,
                engine=f"legacy/{source}",
            )

        except Exception as exc:
            elapsed_ms = (time.time() - start) * 1000.0
            return ExecutionResult(
                status="error",
                error=f"{type(exc).__name__}: {exc}",
                engine="legacy",
                cost_ms=elapsed_ms,
            )

    def get_truth_level(self, engine_source: str) -> TruthLevel:
        """Map legacy source labels to TruthLevel enum."""
        mapping = {
            "knowledge": TruthLevel.DIRECT_FACT,
            "math": TruthLevel.DERIVED,
            "physics": TruthLevel.DERIVED,
            "aces": TruthLevel.HEURISTIC,
            "brain": TruthLevel.HEURISTIC,
            "coder": TruthLevel.TEMPLATE,
            "web": TruthLevel.TEMPLATE,
            "creator": TruthLevel.TEMPLATE,
        }
        # Extract the engine name from "legacy/engine" format
        engine = engine_source.replace("legacy/", "")
        return mapping.get(engine, TruthLevel.UNSUPPORTED)

    @property
    def is_available(self) -> bool:
        """Check if the legacy system can be initialized."""
        return self._ensure_initialized()

    @property
    def initialization_error(self) -> Optional[str]:
        """Get the initialization error, if any."""
        return self._init_error
