"""
AXIMA Goal System — Persistent goal/subgoal/task tracking.

AXIMA must know:
  - Current Goal
  - Subgoals
  - Blocked Tasks
  - Completed Tasks

All stored in the Reality Graph. No planning engine yet — only persistence.

Usage:
    from core.goal_system import get_goal_system

    gs = get_goal_system()
    
    # Create a goal hierarchy
    goal_id = gs.create_goal("Fix math router", priority=1)
    sub_id = gs.create_subgoal(goal_id, "Fix multilingual false positives")
    task_id = gs.create_task(sub_id, "Add English priority bypass")
    
    # Track progress
    gs.complete_task(task_id)
    gs.block_task(other_task, reason="Waiting for data")
    
    # Query state
    active = gs.active_goals()
    blocked = gs.blocked_tasks()
    progress = gs.goal_progress(goal_id)
"""

import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from core.reality_graph import get_reality_graph, RealityGraph


# ═══════════════════════════════════════════════════════════════
# GOAL STATUS
# ═══════════════════════════════════════════════════════════════

class Status:
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


# ═══════════════════════════════════════════════════════════════
# GOAL SYSTEM
# ═══════════════════════════════════════════════════════════════

class GoalSystem:
    """Persistent goal/subgoal/task tracking.
    
    Hierarchy: Goal → Subgoal → Task
    All stored as nodes in the Reality Graph.
    """

    def __init__(self, graph: Optional[RealityGraph] = None):
        self._graph = graph or get_reality_graph()

    # ─── CREATE ───

    def create_goal(self, title: str, priority: int = 0,
                    description: str = "", owner: str = "") -> str:
        """Create a top-level goal. Returns goal node ID."""
        props = {
            "status": Status.ACTIVE,
            "priority": priority,
            "description": description,
            "progress": 0.0,
            "owner": owner,
        }
        goal_id = self._graph.add_node("goal", title, props)

        # Link to owner if specified
        if owner:
            users = self._graph.find_nodes(node_type="user", label_contains=owner)
            if users:
                self._graph.add_edge(users[0].id, goal_id, "owns")

        self._graph.save()
        return goal_id

    def create_subgoal(self, parent_id: str, title: str,
                       priority: int = 0, description: str = "") -> str:
        """Create a subgoal under a parent goal. Returns subgoal node ID."""
        props = {
            "status": Status.ACTIVE,
            "priority": priority,
            "description": description,
            "progress": 0.0,
            "level": "subgoal",
        }
        sub_id = self._graph.add_node("goal", title, props)
        self._graph.add_edge(parent_id, sub_id, "contains")
        self._graph.save()
        return sub_id

    def create_task(self, parent_id: str, title: str,
                    description: str = "", depends_on: Optional[List[str]] = None) -> str:
        """Create a task under a goal or subgoal. Returns task node ID."""
        props = {
            "status": Status.ACTIVE,
            "description": description,
            "completed_at": None,
        }
        task_id = self._graph.add_node("task", title, props)
        self._graph.add_edge(parent_id, task_id, "contains")

        # Add dependencies
        if depends_on:
            for dep_id in depends_on:
                self._graph.add_edge(task_id, dep_id, "depends_on")

        self._graph.save()
        return task_id

    # ─── STATUS TRANSITIONS ───

    def complete_task(self, task_id: str) -> bool:
        """Mark a task as completed. Updates parent progress."""
        success = self._graph.update_node(task_id, properties={
            "status": Status.COMPLETED,
            "completed_at": time.time(),
        })
        if success:
            self._update_parent_progress(task_id)
            self._graph.save()
        return success

    def block_task(self, task_id: str, reason: str = "",
                   blocked_by: Optional[str] = None) -> bool:
        """Mark a task as blocked."""
        props = {"status": Status.BLOCKED, "block_reason": reason}
        success = self._graph.update_node(task_id, properties=props)
        if success and blocked_by:
            self._graph.add_edge(task_id, blocked_by, "blocked_by")
        if success:
            self._graph.save()
        return success

    def unblock_task(self, task_id: str) -> bool:
        """Unblock a task (set back to active)."""
        success = self._graph.update_node(task_id, properties={
            "status": Status.ACTIVE,
            "block_reason": "",
        })
        if success:
            self._graph.save()
        return success

    def complete_goal(self, goal_id: str) -> bool:
        """Mark a goal as completed."""
        success = self._graph.update_node(goal_id, properties={
            "status": Status.COMPLETED,
            "progress": 1.0,
            "completed_at": time.time(),
        })
        if success:
            self._graph.save()
        return success

    def abandon_goal(self, goal_id: str, reason: str = "") -> bool:
        """Abandon a goal."""
        success = self._graph.update_node(goal_id, properties={
            "status": Status.ABANDONED,
            "abandon_reason": reason,
        })
        if success:
            self._graph.save()
        return success

    # ─── QUERIES ───

    def active_goals(self) -> List[Dict[str, Any]]:
        """Get all active top-level goals."""
        goals = self._graph.find_nodes(node_type="goal", status=Status.ACTIVE)
        # Filter to top-level only (not subgoals — those have incoming 'contains' edges)
        top_level = []
        for goal in goals:
            incoming = self._graph.neighbors(goal.id, direction="in")
            is_subgoal = any(rel == "contains" for _, rel, _ in incoming)
            if not is_subgoal:
                top_level.append(self._goal_summary(goal))
        return sorted(top_level, key=lambda g: -g.get("priority", 0))

    def blocked_tasks(self) -> List[Dict[str, Any]]:
        """Get all blocked tasks."""
        tasks = self._graph.find_nodes(node_type="task", status=Status.BLOCKED)
        return [self._task_summary(t) for t in tasks]

    def completed_tasks(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recently completed tasks."""
        tasks = self._graph.find_nodes(node_type="task", status=Status.COMPLETED)
        tasks.sort(key=lambda t: t.properties.get("completed_at", 0), reverse=True)
        return [self._task_summary(t) for t in tasks[:limit]]

    def goal_progress(self, goal_id: str) -> float:
        """Calculate progress of a goal (0.0 to 1.0) based on child completion."""
        children = self._get_children(goal_id)
        if not children:
            node = self._graph.get_node(goal_id)
            if node:
                return node.properties.get("progress", 0.0)
            return 0.0

        completed = sum(1 for c in children
                       if c.properties.get("status") == Status.COMPLETED)
        return completed / len(children)

    def goal_tree(self, goal_id: str) -> Dict[str, Any]:
        """Get full goal tree (goal → subgoals → tasks)."""
        node = self._graph.get_node(goal_id)
        if not node:
            return {}

        tree = self._goal_summary(node)
        tree["children"] = []

        for child_id, rel, _ in self._graph.neighbors(goal_id, relation="contains"):
            child = self._graph.get_node(child_id)
            if child:
                if child.node_type == "goal":
                    tree["children"].append(self.goal_tree(child_id))
                else:
                    tree["children"].append(self._task_summary(child))

        return tree

    def current_focus(self) -> Optional[Dict[str, Any]]:
        """What should AXIMA be working on right now?
        
        Returns the highest-priority active goal with active tasks.
        """
        goals = self.active_goals()
        for goal in goals:
            children = self._get_children(goal["id"])
            active_children = [c for c in children
                             if c.properties.get("status") == Status.ACTIVE]
            if active_children:
                return {
                    "goal": goal,
                    "next_task": self._task_summary(active_children[0]),
                    "total_tasks": len(children),
                    "completed": sum(1 for c in children
                                    if c.properties.get("status") == Status.COMPLETED),
                }
        return None

    # ─── HELPERS ───

    def _get_children(self, node_id: str) -> List:
        """Get all direct children (via 'contains' edges)."""
        children = []
        for child_id, rel, _ in self._graph.neighbors(node_id, relation="contains"):
            child = self._graph.get_node(child_id)
            if child:
                children.append(child)
        return children

    def _update_parent_progress(self, child_id: str):
        """Update parent goal's progress when a child changes status."""
        incoming = self._graph.neighbors(child_id, direction="in")
        for parent_id, rel, _ in incoming:
            if rel == "contains":
                progress = self.goal_progress(parent_id)
                self._graph.update_node(parent_id, properties={"progress": progress})
                # Recurse up
                self._update_parent_progress(parent_id)

    def _goal_summary(self, node) -> Dict[str, Any]:
        """Convert a goal node to a summary dict."""
        return {
            "id": node.id,
            "title": node.label,
            "status": node.properties.get("status", Status.ACTIVE),
            "priority": node.properties.get("priority", 0),
            "progress": node.properties.get("progress", 0.0),
            "description": node.properties.get("description", ""),
        }

    def _task_summary(self, node) -> Dict[str, Any]:
        """Convert a task node to a summary dict."""
        return {
            "id": node.id,
            "title": node.label,
            "status": node.properties.get("status", Status.ACTIVE),
            "description": node.properties.get("description", ""),
            "block_reason": node.properties.get("block_reason", ""),
        }

    # ─── STATS ───

    def stats(self) -> Dict[str, Any]:
        """Goal system statistics."""
        all_goals = self._graph.find_nodes(node_type="goal")
        all_tasks = self._graph.find_nodes(node_type="task")
        return {
            "total_goals": len(all_goals),
            "active_goals": sum(1 for g in all_goals if g.properties.get("status") == Status.ACTIVE),
            "completed_goals": sum(1 for g in all_goals if g.properties.get("status") == Status.COMPLETED),
            "total_tasks": len(all_tasks),
            "active_tasks": sum(1 for t in all_tasks if t.properties.get("status") == Status.ACTIVE),
            "blocked_tasks": sum(1 for t in all_tasks if t.properties.get("status") == Status.BLOCKED),
            "completed_tasks": sum(1 for t in all_tasks if t.properties.get("status") == Status.COMPLETED),
        }


# ═══════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════

_goal_system: Optional[GoalSystem] = None


def get_goal_system(graph: Optional[RealityGraph] = None) -> GoalSystem:
    """Get the global goal system instance."""
    global _goal_system
    if _goal_system is None:
        _goal_system = GoalSystem(graph=graph)
    return _goal_system
