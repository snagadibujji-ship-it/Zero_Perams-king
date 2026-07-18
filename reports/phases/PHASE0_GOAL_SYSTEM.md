# Goal System Foundation

## Purpose

The Goal System provides AXIMA with persistent awareness of what it is working toward. At any moment, AXIMA knows:

- The **current goal** and why it matters
- Active **subgoals** decomposing the goal into manageable pieces
- **Blocked tasks** and what is blocking them
- **Completed tasks** and the progress they represent

This eliminates the "amnesia problem" where an AI loses track of objectives across context boundaries. The Goal System is the motivational backbone of AXIMA — it drives focus, prioritization, and progress tracking.

## Hierarchy

The Goal System uses a three-level hierarchy:

```
Goal
├── Subgoal
│   ├── Task
│   ├── Task
│   └── Task
├── Subgoal
│   ├── Task
│   └── Task
└── Subgoal
    └── Task
```

| Level   | Description                                      | Example                              |
|---------|--------------------------------------------------|--------------------------------------|
| Goal    | Top-level objective with clear success criteria   | "Deploy v2.0 to production"          |
| Subgoal | A logical grouping of related work               | "Complete database migration"        |
| Task    | An atomic unit of work that can be completed     | "Write migration script for users table" |

Goals own subgoals. Subgoals own tasks. Progress flows upward automatically.

## Status Transitions

Every node in the hierarchy has a status that follows defined transitions:

```
         ┌──────────┐
         │  active  │
         └────┬─────┘
              │
    ┌─────────┼─────────┐
    │         │         │
    ▼         ▼         ▼
┌────────┐ ┌─────────┐ ┌──────────┐
│blocked │ │completed│ │abandoned │
└────┬───┘ └─────────┘ └──────────┘
     │
     ▼
┌────────┐
│ active │  (via unblock)
└────────┘
```

| Transition           | Trigger                          | Constraint                        |
|----------------------|----------------------------------|-----------------------------------|
| active → blocked     | External dependency or blocker   | Must specify blocker reason       |
| active → completed   | Work finished successfully       | All children must be completed    |
| active → abandoned   | Goal no longer relevant          | Cascades to all children          |
| blocked → active     | Blocker resolved                 | Blocker reason cleared            |

**Rules:**
- A goal cannot be completed until all its subgoals are completed
- A subgoal cannot be completed until all its tasks are completed
- Abandoning a goal cascades abandonment to all subgoals and tasks
- Blocking does **not** cascade — children remain independently trackable

## API

### Mutation Operations

| Function         | Parameters                              | Returns     | Description                          |
|------------------|----------------------------------------|-------------|--------------------------------------|
| `create_goal`    | `name, description, success_criteria`  | `goal_id`   | Create a new top-level goal          |
| `create_subgoal` | `goal_id, name, description`           | `subgoal_id`| Add a subgoal under a goal           |
| `create_task`    | `subgoal_id, name, description`        | `task_id`   | Add a task under a subgoal           |
| `complete_task`  | `task_id, result_summary`              | `bool`      | Mark task as completed               |
| `block_task`     | `task_id, blocker_reason`              | `bool`      | Mark task as blocked                 |
| `unblock_task`   | `task_id`                              | `bool`      | Remove blocker, reactivate task      |
| `complete_goal`  | `goal_id`                              | `bool`      | Mark goal as completed (validates)   |
| `abandon_goal`   | `goal_id, reason`                      | `bool`      | Abandon goal and cascade to children |

### Query Operations

| Function            | Parameters       | Returns                  | Description                              |
|---------------------|-----------------|--------------------------|------------------------------------------|
| `active_goals()`    | —               | `List[Goal]`             | All goals with status "active"           |
| `blocked_tasks()`   | `goal_id=None`  | `List[Task]`             | All blocked tasks, optionally filtered   |
| `completed_tasks()` | `goal_id=None`  | `List[Task]`             | All completed tasks, optionally filtered |
| `goal_progress()`   | `goal_id`       | `ProgressReport`         | Completion percentage and breakdown      |
| `goal_tree()`       | `goal_id`       | `TreeNode`               | Full hierarchy with statuses             |
| `current_focus()`   | —               | `Task`                   | The next actionable task to work on      |

## Storage

All goal system data is stored as **nodes and edges in the Reality Graph**:

- **Nodes**: Goal, Subgoal, and Task entities with status, timestamps, and metadata
- **Edges**: `has_subgoal`, `has_task`, `blocked_by`, `completed_by` relationships
- **Persistence**: Survives restarts — goals persist across sessions
- **Indexing**: Status-based indexes for fast query resolution

```
Reality Graph Structure:

[Goal Node] --has_subgoal--> [Subgoal Node] --has_task--> [Task Node]
                                                              |
                                                    --blocked_by--> [Blocker Node]
```

This means goal state is never stored in ephemeral memory. It lives in the same persistent graph that holds all of AXIMA's knowledge about reality.

## Progress Calculation

Progress is calculated **automatically** from children completion:

```python
def goal_progress(goal_id: str) -> ProgressReport:
    """
    Progress rolls up from tasks → subgoals → goals.
    
    Task progress: 0% (active/blocked) or 100% (completed)
    Subgoal progress: average of its tasks' progress
    Goal progress: average of its subgoals' progress
    """
    goal = get_node(goal_id)
    subgoals = get_children(goal_id, "has_subgoal")
    
    subgoal_progress = []
    for subgoal in subgoals:
        tasks = get_children(subgoal.id, "has_task")
        completed = sum(1 for t in tasks if t.status == "completed")
        subgoal_progress.append(completed / len(tasks) if tasks else 0.0)
    
    overall = sum(subgoal_progress) / len(subgoal_progress) if subgoal_progress else 0.0
    
    return ProgressReport(
        goal_id=goal_id,
        overall_progress=overall,
        subgoal_breakdown=subgoal_progress,
        blocked_count=len([t for t in all_tasks if t.status == "blocked"]),
        completed_count=len([t for t in all_tasks if t.status == "completed"]),
        total_count=len(all_tasks)
    )
```

## Implementation

**File:** `/root/hybrid-ai/src/python/core/goal_system.py` (324 lines)

The implementation includes:

- `GoalSystem` class with full CRUD and query operations
- Integration with the Reality Graph storage layer
- Status validation and transition enforcement
- Cascade logic for abandonment
- Progress calculation with caching
- `current_focus()` heuristic: selects the highest-priority active task from the most progressed subgoal

## Usage Examples

### Creating and tracking a goal

```python
from core.goal_system import GoalSystem

gs = GoalSystem(reality_graph)

# Create a goal
goal_id = gs.create_goal(
    name="Deploy v2.0",
    description="Ship version 2.0 to production",
    success_criteria="All services running v2.0, no P0 incidents for 24h"
)

# Decompose into subgoals
sg_migrate = gs.create_subgoal(goal_id, "Database Migration", "Migrate schema to v2")
sg_deploy = gs.create_subgoal(goal_id, "Service Deployment", "Roll out new containers")

# Add tasks
t1 = gs.create_task(sg_migrate, "Write migration script", "ALTER TABLE statements for users")
t2 = gs.create_task(sg_migrate, "Test migration on staging", "Run against staging DB copy")
t3 = gs.create_task(sg_deploy, "Update Kubernetes manifests", "New image tags and env vars")

# Work through tasks
gs.complete_task(t1, "Migration script written and reviewed")
gs.block_task(t2, "Staging DB is currently unavailable — ops ticket #4521")

# Check progress
progress = gs.goal_progress(goal_id)
# ProgressReport(overall_progress=0.25, blocked_count=1, completed_count=1, total_count=3)

# Check what to work on next
focus = gs.current_focus()
# Returns t3 (next actionable task since t2 is blocked)
```

### Querying goal state

```python
# What are we working on?
active = gs.active_goals()

# What's stuck?
blocked = gs.blocked_tasks(goal_id)
for task in blocked:
    print(f"  {task.name}: blocked by {task.blocker_reason}")

# Full picture
tree = gs.goal_tree(goal_id)
print(tree)
# Deploy v2.0 [active] (25%)
# ├── Database Migration [active] (50%)
# │   ├── Write migration script [completed] ✓
# │   └── Test migration on staging [blocked] ⚠
# └── Service Deployment [active] (0%)
#     └── Update Kubernetes manifests [active]
```

### Unblocking and completing

```python
# Blocker resolved
gs.unblock_task(t2)
gs.complete_task(t2, "Migration tested successfully on staging")
gs.complete_task(t3, "Manifests updated, PR merged")

# Now we can complete the goal
gs.complete_goal(goal_id)
# Returns True — all children completed
```

## Status

**Implemented and tested.** The Goal System is fully operational and integrated with the Reality Graph persistence layer. Unit tests cover all status transitions, cascade behavior, progress calculation, and edge cases (empty goals, re-blocking, abandonment mid-progress).
