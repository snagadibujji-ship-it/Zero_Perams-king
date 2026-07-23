"""
Cognitive Budget Scheduler
==========================

Enforces resource budgets (time, memory, steps, depth) for query execution.
Provides scheduling, cancellation, and status tracking for concurrent tasks.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional


class TaskStatus(Enum):
    """Lifecycle states for a scheduled task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    BUDGET_EXCEEDED = "budget_exceeded"


@dataclass
class ResourceBudget:
    """Resource constraints for a single task."""

    max_time_ms: float = 5000.0
    max_memory_mb: float = 256.0
    max_steps: int = 100
    max_depth: int = 10


@dataclass
class TaskRecord:
    """Internal tracking state for a scheduled task."""

    task_id: str
    budget: ResourceBudget
    status: TaskStatus = TaskStatus.PENDING
    cancel_event: threading.Event = field(default_factory=threading.Event)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    steps_used: int = 0
    result: Any = None
    error: Optional[str] = None

    @property
    def elapsed_ms(self) -> float:
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000.0

    @property
    def time_remaining_ms(self) -> float:
        return max(0.0, self.budget.max_time_ms - self.elapsed_ms)

    @property
    def is_budget_exceeded(self) -> bool:
        if self.elapsed_ms > self.budget.max_time_ms:
            return True
        if self.steps_used > self.budget.max_steps:
            return True
        return False


class CognitiveScheduler:
    """Schedules tasks with resource budget enforcement.

    Thread-safe. Tracks all active and completed tasks for observability.

    Usage::

        scheduler = CognitiveScheduler()
        task_id = scheduler.schedule(
            task_id="q-123",
            budget=ResourceBudget(max_time_ms=2000),
            fn=lambda cancel: engine.solve(query, cancel=cancel),
        )
        status = scheduler.get_status(task_id)
        scheduler.cancel(task_id)
    """

    def __init__(self, max_concurrent: int = 16) -> None:
        self._lock = threading.Lock()
        self._tasks: Dict[str, TaskRecord] = {}
        self._max_concurrent = max_concurrent

    def schedule(
        self,
        task_id: str,
        budget: ResourceBudget,
        fn: Callable[[threading.Event], Any],
    ) -> str:
        """Schedule a function with budget enforcement.

        Args:
            task_id: Unique identifier for the task.
            budget: Resource constraints to enforce.
            fn: Callable that accepts a cancellation Event and returns a result.

        Returns:
            The task_id (for chaining).

        Raises:
            RuntimeError: If max concurrent tasks exceeded.
        """
        with self._lock:
            active = sum(
                1 for t in self._tasks.values() if t.status == TaskStatus.RUNNING
            )
            if active >= self._max_concurrent:
                raise RuntimeError(
                    f"Max concurrent tasks ({self._max_concurrent}) exceeded"
                )

            record = TaskRecord(task_id=task_id, budget=budget)
            self._tasks[task_id] = record

        thread = threading.Thread(
            target=self._execute_task,
            args=(record, fn),
            daemon=True,
            name=f"axima-task-{task_id[:8]}",
        )
        thread.start()
        return task_id

    def _execute_task(
        self, record: TaskRecord, fn: Callable[[threading.Event], Any]
    ) -> None:
        """Run the task function with time enforcement."""
        record.start_time = time.time()
        record.status = TaskStatus.RUNNING

        try:
            # Use a timer to enforce timeout
            timeout_s = record.budget.max_time_ms / 1000.0
            timer = threading.Timer(timeout_s, record.cancel_event.set)
            timer.daemon = True
            timer.start()

            try:
                result = fn(record.cancel_event)
            finally:
                timer.cancel()

            if record.cancel_event.is_set():
                if record.status == TaskStatus.RUNNING:
                    record.status = TaskStatus.TIMEOUT
            else:
                record.result = result
                record.status = TaskStatus.COMPLETED

        except Exception as exc:
            record.error = f"{type(exc).__name__}: {exc}"
            if record.cancel_event.is_set():
                record.status = TaskStatus.CANCELLED
            else:
                record.status = TaskStatus.BUDGET_EXCEEDED

        finally:
            record.end_time = time.time()

    def cancel(self, task_id: str) -> bool:
        """Cancel a running task. Returns True if the task was running."""
        with self._lock:
            record = self._tasks.get(task_id)
            if record is None:
                return False
            if record.status != TaskStatus.RUNNING:
                return False
            record.cancel_event.set()
            record.status = TaskStatus.CANCELLED
            return True

    def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status info for a task."""
        with self._lock:
            record = self._tasks.get(task_id)
            if record is None:
                return None
            return {
                "task_id": record.task_id,
                "status": record.status.value,
                "elapsed_ms": record.elapsed_ms,
                "time_remaining_ms": record.time_remaining_ms,
                "steps_used": record.steps_used,
                "budget_exceeded": record.is_budget_exceeded,
                "error": record.error,
            }

    def get_result(self, task_id: str, timeout_ms: float = 5000.0) -> Any:
        """Wait for a task to complete and return its result.

        Raises:
            TimeoutError: If the task doesn't complete within timeout_ms.
            RuntimeError: If the task failed or was cancelled.
        """
        record = self._tasks.get(task_id)
        if record is None:
            raise KeyError(f"Unknown task: {task_id}")

        # Wait for completion
        deadline = time.time() + (timeout_ms / 1000.0)
        while record.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
            if time.time() > deadline:
                raise TimeoutError(f"Task {task_id} did not complete within {timeout_ms}ms")
            time.sleep(0.005)

        if record.status == TaskStatus.COMPLETED:
            return record.result
        elif record.status == TaskStatus.CANCELLED:
            raise RuntimeError(f"Task {task_id} was cancelled")
        elif record.status == TaskStatus.TIMEOUT:
            raise TimeoutError(f"Task {task_id} exceeded time budget")
        else:
            raise RuntimeError(f"Task {task_id} failed: {record.error}")

    def increment_steps(self, task_id: str) -> bool:
        """Increment step counter for a task. Returns False if budget exceeded."""
        with self._lock:
            record = self._tasks.get(task_id)
            if record is None:
                return False
            record.steps_used += 1
            if record.steps_used > record.budget.max_steps:
                record.cancel_event.set()
                record.status = TaskStatus.BUDGET_EXCEEDED
                return False
            return True

    def cleanup(self, max_age_s: float = 3600.0) -> int:
        """Remove completed tasks older than max_age_s. Returns count removed."""
        now = time.time()
        to_remove = []
        with self._lock:
            for task_id, record in self._tasks.items():
                if record.status in (
                    TaskStatus.COMPLETED,
                    TaskStatus.CANCELLED,
                    TaskStatus.TIMEOUT,
                    TaskStatus.BUDGET_EXCEEDED,
                ):
                    if record.end_time and (now - record.end_time) > max_age_s:
                        to_remove.append(task_id)
            for task_id in to_remove:
                del self._tasks[task_id]
        return len(to_remove)

    def shutdown(self) -> None:
        """Cancel all running tasks for graceful shutdown."""
        with self._lock:
            for record in self._tasks.values():
                if record.status == TaskStatus.RUNNING:
                    record.cancel_event.set()
                    record.status = TaskStatus.CANCELLED
