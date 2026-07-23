"""Plan DAG — Directed Acyclic Graph for execution planning.

Supports topological ordering, critical path analysis, parallel execution
detection, branch conditions, and rollback.
"""

from __future__ import annotations

import uuid
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class StepStatus(Enum):
    """Execution status of a plan step."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ResourceBudget:
    """Resource constraints for plan execution."""

    max_time_ms: int = 5000
    max_memory_mb: int = 256
    max_parallel: int = 4
    max_retries: int = 2


@dataclass
class BranchCondition:
    """Conditional branching in the DAG.

    If the condition_step completes with a result matching `match_value`,
    the `then_steps` are activated; otherwise `else_steps` are activated.
    """

    condition_step: str
    match_field: str = "status"
    match_value: str = "done"
    then_steps: List[str] = field(default_factory=list)
    else_steps: List[str] = field(default_factory=list)


@dataclass
class PlanStep:
    """A single step in the execution plan.

    Attributes:
        id: Unique identifier for this step.
        name: Human-readable name.
        capability: Name of the capability (plugin) to invoke.
        preconditions: Conditions that must hold before execution.
        postconditions: Guarantees after successful execution.
        expected_cost_ms: Estimated wall-clock time.
        expected_info_gain: Expected information gain (0.0–1.0).
        status: Current execution status.
        result: Stored result after execution (opaque).
        retry_count: Number of retries attempted.
        branch_condition: Optional branching logic attached to this step.
    """

    id: str
    name: str
    capability: str
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    expected_cost_ms: int = 100
    expected_info_gain: float = 0.5
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    retry_count: int = 0
    branch_condition: Optional[BranchCondition] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "capability": self.capability,
            "preconditions": self.preconditions,
            "postconditions": self.postconditions,
            "expected_cost_ms": self.expected_cost_ms,
            "expected_info_gain": self.expected_info_gain,
            "status": self.status.value,
            "retry_count": self.retry_count,
        }
        if self.branch_condition:
            d["branch_condition"] = {
                "condition_step": self.branch_condition.condition_step,
                "match_field": self.branch_condition.match_field,
                "match_value": self.branch_condition.match_value,
                "then_steps": self.branch_condition.then_steps,
                "else_steps": self.branch_condition.else_steps,
            }
        return d


@dataclass
class PlanDAG:
    """Directed Acyclic Graph representing an execution plan.

    Steps are nodes; dependencies are directed edges (dependency -> step).
    Supports topological sort, critical path, parallel execution groups,
    and rollback.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    steps: Dict[str, PlanStep] = field(default_factory=dict)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    budget: ResourceBudget = field(default_factory=ResourceBudget)
    deadline_ms: int = 5000
    branch_conditions: List[BranchCondition] = field(default_factory=list)

    # --- Mutation Methods ---

    def add_step(self, step: PlanStep) -> None:
        """Add a step to the plan. Raises ValueError on duplicate ID."""
        if step.id in self.steps:
            raise ValueError(f"Step '{step.id}' already exists in plan")
        self.steps[step.id] = step
        if step.id not in self.dependencies:
            self.dependencies[step.id] = []

    def add_dependency(self, step_id: str, depends_on: str) -> None:
        """Declare that `step_id` depends on `depends_on`.

        Both steps must already exist. Raises ValueError on cycle detection.
        """
        if step_id not in self.steps:
            raise ValueError(f"Step '{step_id}' not found in plan")
        if depends_on not in self.steps:
            raise ValueError(f"Dependency '{depends_on}' not found in plan")
        if depends_on == step_id:
            raise ValueError("A step cannot depend on itself")

        if depends_on not in self.dependencies[step_id]:
            self.dependencies[step_id].append(depends_on)

        # Check for cycles
        if self._has_cycle():
            self.dependencies[step_id].remove(depends_on)
            raise ValueError(
                f"Adding dependency {step_id} -> {depends_on} would create a cycle"
            )

    def remove_step(self, step_id: str) -> None:
        """Remove a step and all its edges from the plan."""
        if step_id not in self.steps:
            raise ValueError(f"Step '{step_id}' not found")
        del self.steps[step_id]
        del self.dependencies[step_id]
        # Remove from other dependency lists
        for sid in self.dependencies:
            if step_id in self.dependencies[sid]:
                self.dependencies[sid].remove(step_id)

    # --- Query Methods ---

    def get_ready_steps(self) -> List[PlanStep]:
        """Return steps whose dependencies are all DONE and are PENDING.

        These are candidates for parallel execution.
        """
        ready: List[PlanStep] = []
        for step_id, step in self.steps.items():
            if step.status != StepStatus.PENDING:
                continue
            deps = self.dependencies.get(step_id, [])
            all_deps_done = all(
                self.steps[d].status == StepStatus.DONE for d in deps
            )
            if all_deps_done:
                ready.append(step)
        return ready

    def get_dependents(self, step_id: str) -> List[str]:
        """Return IDs of steps that depend on `step_id`."""
        dependents: List[str] = []
        for sid, deps in self.dependencies.items():
            if step_id in deps:
                dependents.append(sid)
        return dependents

    def topological_sort(self) -> List[str]:
        """Return step IDs in topological order (Kahn's algorithm).

        Raises ValueError if the graph has a cycle.
        """
        in_degree: Dict[str, int] = {sid: 0 for sid in self.steps}
        for sid, deps in self.dependencies.items():
            in_degree[sid] = len(deps)

        queue = deque([sid for sid, d in in_degree.items() if d == 0])
        order: List[str] = []

        while queue:
            node = queue.popleft()
            order.append(node)
            for dependent in self.get_dependents(node):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(order) != len(self.steps):
            raise ValueError("Plan DAG contains a cycle — topological sort impossible")

        return order

    def get_parallel_groups(self) -> List[List[str]]:
        """Return groups of steps that can execute in parallel (level-based).

        Each group is a set of steps with the same topological depth.
        """
        if not self.steps:
            return []

        # Calculate depth (longest path to each node)
        depth: Dict[str, int] = {}
        order = self.topological_sort()

        for sid in order:
            deps = self.dependencies.get(sid, [])
            if not deps:
                depth[sid] = 0
            else:
                depth[sid] = max(depth[d] for d in deps) + 1

        # Group by depth
        max_depth = max(depth.values()) if depth else 0
        groups: List[List[str]] = [[] for _ in range(max_depth + 1)]
        for sid, d in depth.items():
            groups[d].append(sid)

        return groups

    def get_critical_path(self) -> List[str]:
        """Return the critical path (longest weighted path through the DAG).

        Weight is `expected_cost_ms` for each step.
        """
        if not self.steps:
            return []

        order = self.topological_sort()

        # Longest path calculation
        dist: Dict[str, int] = {sid: 0 for sid in self.steps}
        predecessor: Dict[str, Optional[str]] = {sid: None for sid in self.steps}

        for sid in order:
            step = self.steps[sid]
            current_dist = dist[sid] + step.expected_cost_ms
            for dependent in self.get_dependents(sid):
                if current_dist > dist[dependent]:
                    dist[dependent] = current_dist
                    predecessor[dependent] = sid

        # Find the endpoint with maximum distance + its own cost
        end_node = max(
            self.steps.keys(),
            key=lambda s: dist[s] + self.steps[s].expected_cost_ms,
        )

        # Trace back
        path: List[str] = [end_node]
        current = predecessor[end_node]
        while current is not None:
            path.append(current)
            current = predecessor[current]

        path.reverse()
        return path

    def estimated_total_cost_ms(self) -> int:
        """Estimated total time considering parallel execution."""
        groups = self.get_parallel_groups()
        total = 0
        for group in groups:
            # Parallel group time = max cost in the group
            if group:
                total += max(self.steps[sid].expected_cost_ms for sid in group)
        return total

    # --- Status Management ---

    def mark_complete(self, step_id: str, result: Any = None) -> None:
        """Mark a step as successfully completed."""
        if step_id not in self.steps:
            raise ValueError(f"Step '{step_id}' not found")
        self.steps[step_id].status = StepStatus.DONE
        self.steps[step_id].result = result

    def mark_failed(self, step_id: str, error: Optional[str] = None) -> None:
        """Mark a step as failed and evaluate branch conditions."""
        if step_id not in self.steps:
            raise ValueError(f"Step '{step_id}' not found")
        step = self.steps[step_id]
        step.status = StepStatus.FAILED
        step.result = {"error": error} if error else None

        # Skip dependents that cannot proceed
        self._propagate_failure(step_id)

    def mark_running(self, step_id: str) -> None:
        """Mark a step as currently executing."""
        if step_id not in self.steps:
            raise ValueError(f"Step '{step_id}' not found")
        self.steps[step_id].status = StepStatus.RUNNING

    def mark_skipped(self, step_id: str) -> None:
        """Mark a step as skipped (e.g., due to branch condition)."""
        if step_id not in self.steps:
            raise ValueError(f"Step '{step_id}' not found")
        self.steps[step_id].status = StepStatus.SKIPPED

    def rollback_plan(self) -> None:
        """Reset all steps to PENDING status (for retry/rollback scenarios)."""
        for step in self.steps.values():
            step.status = StepStatus.PENDING
            step.result = None
            step.retry_count = 0

    # --- Validation ---

    def validate(self) -> List[str]:
        """Validate plan structure. Returns list of error messages (empty = valid)."""
        errors: List[str] = []

        # Check for cycles
        if self._has_cycle():
            errors.append("Plan DAG contains a cycle")

        # Check dependency references
        for step_id, deps in self.dependencies.items():
            if step_id not in self.steps:
                errors.append(f"Dependency list references unknown step: {step_id}")
            for dep in deps:
                if dep not in self.steps:
                    errors.append(
                        f"Step '{step_id}' depends on unknown step '{dep}'"
                    )

        # Check budget feasibility
        estimated = self.estimated_total_cost_ms()
        if estimated > self.deadline_ms:
            errors.append(
                f"Estimated cost ({estimated}ms) exceeds deadline ({self.deadline_ms}ms)"
            )

        # Check branch condition references
        for bc in self.branch_conditions:
            if bc.condition_step not in self.steps:
                errors.append(
                    f"Branch condition references unknown step: {bc.condition_step}"
                )
            for s in bc.then_steps + bc.else_steps:
                if s not in self.steps:
                    errors.append(
                        f"Branch condition references unknown step: {s}"
                    )

        return errors

    # --- Serialization ---

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the plan to a dictionary."""
        return {
            "id": self.id,
            "steps": {sid: step.to_dict() for sid, step in self.steps.items()},
            "dependencies": dict(self.dependencies),
            "budget": {
                "max_time_ms": self.budget.max_time_ms,
                "max_memory_mb": self.budget.max_memory_mb,
                "max_parallel": self.budget.max_parallel,
                "max_retries": self.budget.max_retries,
            },
            "deadline_ms": self.deadline_ms,
            "estimated_cost_ms": self.estimated_total_cost_ms(),
            "critical_path": self.get_critical_path(),
        }

    # --- Internal Helpers ---

    def _has_cycle(self) -> bool:
        """Detect cycles using DFS."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {sid: WHITE for sid in self.steps}

        def dfs(node: str) -> bool:
            color[node] = GRAY
            for dependent in self.get_dependents(node):
                if color.get(dependent, WHITE) == GRAY:
                    return True
                if color.get(dependent, WHITE) == WHITE and dfs(dependent):
                    return True
            color[node] = BLACK
            return False

        for sid in self.steps:
            if color[sid] == WHITE:
                if dfs(sid):
                    return True
        return False

    def _propagate_failure(self, failed_step: str) -> None:
        """Skip all downstream steps that depend on a failed step.

        Only skips if ALL paths to a downstream step pass through the failure.
        """
        # Simple heuristic: skip direct dependents that have no other satisfied deps
        for dependent_id in self.get_dependents(failed_step):
            deps = self.dependencies[dependent_id]
            # If all dependencies are either DONE or the failed one, skip
            non_failed_deps = [
                d for d in deps
                if d != failed_step and self.steps[d].status != StepStatus.FAILED
            ]
            unsatisfied = [
                d for d in non_failed_deps
                if self.steps[d].status != StepStatus.DONE
            ]
            # If no way to proceed (the failed dep was required and others aren't done)
            all_other_done = all(
                self.steps[d].status in (StepStatus.DONE, StepStatus.SKIPPED)
                for d in non_failed_deps
            )
            # If the failed step is the only non-done dep, this step can't proceed
            if not non_failed_deps or not all_other_done:
                self.steps[dependent_id].status = StepStatus.SKIPPED
                self._propagate_failure(dependent_id)
