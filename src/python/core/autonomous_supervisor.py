"""
AXIMA Autonomous Supervisor — Coordinates all background cognition.

Responsibilities:
  - Detect idle periods (no user interaction)
  - Schedule autonomous work by expected cognitive value
  - Enforce CPU, memory, and execution budgets
  - Pause or cancel low-value work
  - Never perform reasoning itself — only coordinate

Usage:
    from core.autonomous_supervisor import AutonomousSupervisor, get_supervisor

    supervisor = get_supervisor()
    supervisor.on_user_idle()      # Start background work
    supervisor.on_user_active()    # Pause background work
    work_done = supervisor.tick()  # One supervised cycle
"""

import time
import tracemalloc
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable

from core.reality_graph import get_reality_graph, RealityGraph
from core.cognitive_scheduler import get_scheduler, CognitiveScheduler


@dataclass
class Budget:
    """Resource budget for autonomous work."""
    max_cpu_ms_per_tick: float = 30.0       # Max milliseconds per tick
    max_memory_mb: float = 25.0             # Hard memory limit
    max_ticks_per_idle: int = 100           # Max ticks before forced pause
    min_idle_seconds: float = 2.0           # Wait before starting autonomous work
    max_work_items_per_tick: int = 3        # Max concurrent work items
    confidence_threshold: float = 0.3       # Min confidence to act on results
    evidence_threshold: int = 2             # Min evidence count to commit changes


@dataclass
class WorkItem:
    """A unit of autonomous work."""
    id: str
    task_type: str          # goal_gen, hypothesis, experiment, maintenance, consolidation
    description: str
    priority: float = 0.5
    expected_value: float = 0.5   # Expected cognitive benefit
    estimated_cost_ms: float = 10.0
    status: str = "pending"       # pending, running, completed, cancelled, paused
    result: Optional[Dict] = None
    started_at: float = 0.0
    completed_at: float = 0.0


class AutonomousSupervisor:
    """Coordinates autonomous background cognition.
    
    The supervisor decides WHAT runs and WHEN, but never performs
    reasoning itself. It delegates to existing subsystems.
    """

    def __init__(self, graph: Optional[RealityGraph] = None,
                 budget: Optional[Budget] = None):
        self._graph = graph or get_reality_graph()
        self._budget = budget or Budget()
        self._scheduler = get_scheduler(self._graph)

        # State
        self._idle_since: Optional[float] = None
        self._is_active = True  # User active by default
        self._tick_count = 0
        self._ticks_this_idle = 0
        self._work_queue: List[WorkItem] = []
        self._completed_work: List[WorkItem] = []
        self._paused = False

        # Audit log
        self._audit_log: List[Dict[str, Any]] = []

    def on_user_idle(self):
        """Signal that user is no longer interacting."""
        if self._is_active:
            self._idle_since = time.time()
            self._is_active = False
            self._ticks_this_idle = 0
            self._log("state_change", "User went idle")

    def on_user_active(self):
        """Signal that user is interacting again."""
        if not self._is_active:
            self._is_active = True
            self._idle_since = None
            self._paused = True  # Pause background work
            self._log("state_change", "User became active — pausing autonomous work")

    def tick(self) -> Dict[str, Any]:
        """One supervised autonomous cycle.
        
        Returns summary of what was done (or why nothing was done).
        """
        self._tick_count += 1
        result = {"tick": self._tick_count, "actions": [], "skipped_reason": None}

        # Check if we should work
        if not self._should_work():
            result["skipped_reason"] = self._skip_reason()
            return result

        # Check memory budget
        if not self._within_memory_budget():
            result["skipped_reason"] = "memory_budget_exceeded"
            self._log("budget_exceeded", "Memory limit reached")
            return result

        # Increment idle tick counter
        self._ticks_this_idle += 1

        # Get scheduled tasks from cognitive scheduler
        scheduled = self._scheduler.what_runs_now()

        # Execute within CPU budget
        start = time.time()
        for task_type in scheduled[:self._budget.max_work_items_per_tick]:
            elapsed_ms = (time.time() - start) * 1000
            if elapsed_ms >= self._budget.max_cpu_ms_per_tick:
                break

            action = self._execute_task(task_type)
            if action:
                result["actions"].append(action)
                self._scheduler.mark_completed(task_type, actual_ms=(time.time() - start) * 1000)

        return result

    def queue_work(self, task_type: str, description: str,
                   priority: float = 0.5, expected_value: float = 0.5):
        """Add work to the autonomous queue."""
        item = WorkItem(
            id=f"W{self._tick_count}_{len(self._work_queue)}",
            task_type=task_type,
            description=description,
            priority=priority,
            expected_value=expected_value,
        )
        self._work_queue.append(item)
        self._work_queue.sort(key=lambda w: -w.priority * w.expected_value)

    def cancel_work(self, work_id: str) -> bool:
        """Cancel a queued work item."""
        for item in self._work_queue:
            if item.id == work_id:
                item.status = "cancelled"
                self._log("work_cancelled", f"Cancelled: {item.description}")
                return True
        return False

    def pause(self):
        """Pause all autonomous work."""
        self._paused = True
        self._log("paused", "Autonomous work paused")

    def resume(self):
        """Resume autonomous work."""
        self._paused = False
        self._log("resumed", "Autonomous work resumed")

    @property
    def is_working(self) -> bool:
        """Is the supervisor currently doing autonomous work?"""
        return not self._is_active and not self._paused and self._should_work()

    def stats(self) -> Dict[str, Any]:
        """Supervisor statistics."""
        return {
            "total_ticks": self._tick_count,
            "ticks_this_idle": self._ticks_this_idle,
            "is_active": self._is_active,
            "is_paused": self._paused,
            "queue_size": len([w for w in self._work_queue if w.status == "pending"]),
            "completed_work": len(self._completed_work),
            "idle_seconds": (time.time() - self._idle_since) if self._idle_since else 0,
        }

    def audit_log(self, n: int = 20) -> List[Dict[str, Any]]:
        """Get recent audit entries."""
        return self._audit_log[-n:]

    # ─── Internal ───

    def _should_work(self) -> bool:
        """Should the supervisor execute work right now?"""
        if self._is_active:
            return False
        if self._paused:
            return False
        if self._ticks_this_idle >= self._budget.max_ticks_per_idle:
            return False
        if self._idle_since:
            idle_duration = time.time() - self._idle_since
            if idle_duration < self._budget.min_idle_seconds:
                return False
        return True

    def _skip_reason(self) -> str:
        if self._is_active:
            return "user_active"
        if self._paused:
            return "paused"
        if self._ticks_this_idle >= self._budget.max_ticks_per_idle:
            return "max_ticks_reached"
        if self._idle_since and (time.time() - self._idle_since) < self._budget.min_idle_seconds:
            return "waiting_for_idle_threshold"
        return "unknown"

    def _within_memory_budget(self) -> bool:
        """Check if within memory budget."""
        try:
            import resource
            usage_bytes = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
            usage_mb = usage_bytes / (1024 * 1024)
            return usage_mb < self._budget.max_memory_mb
        except (ImportError, AttributeError):
            return True  # Can't measure, assume OK

    def _execute_task(self, task_type: str) -> Optional[Dict]:
        """Execute a single autonomous task. Returns action record."""
        self._log("execute", f"Running: {task_type}")
        return {"task": task_type, "status": "executed", "time": time.time()}

    def _log(self, event_type: str, message: str):
        """Add to audit log."""
        self._audit_log.append({
            "time": time.time(),
            "event": event_type,
            "message": message,
            "tick": self._tick_count,
        })
        if len(self._audit_log) > 500:
            self._audit_log = self._audit_log[-500:]


_supervisor: Optional[AutonomousSupervisor] = None
def get_supervisor(graph: Optional[RealityGraph] = None) -> AutonomousSupervisor:
    global _supervisor
    if _supervisor is None:
        _supervisor = AutonomousSupervisor(graph=graph)
    return _supervisor
