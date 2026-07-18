# AXIMA Planner - Documentation

## Purpose

The Planner component converts predictions and graph state into actionable plans. It bridges the gap between what AXIMA expects to happen and what it should actually do next. Planning emerges dynamically from the current state of the Reality Graph, Attention System, and Prediction Engine rather than following hardcoded workflows.

The Planner is responsible for:
- Creating tasks from goal analysis and decomposition
- Prioritizing tasks using attention scores
- Detecting blockers from graph relationships
- Recommending the next best action
- Generating planning observations and insights

## Architecture

The Planner operates at the intersection of three core systems:

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Planner                                    │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Reality Graph   │  │  Attention       │  │  Prediction      │  │
│  │  (state)         │  │  System          │  │  Engine          │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Plan Generation (plan_next, plan_for_goal)                    │ │
│  │  - Blocker detection                                           │ │
│  │  - Task prioritization                                         │ │
│  │  - Action recommendation                                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

**Key components:**
- `Planner` class - Main orchestration engine
- `Plan` dataclass - Output structure containing recommended actions, priorities, blockers
- `Action` dataclass - Individual recommended action with type, target, priority, reason

**Design patterns:**
- Singleton pattern (`get_planner()`) for global access
- Graph-driven planning (emergent from state rather than hardcoded)
- Attention-based prioritization (scores determine task order)

## Key APIs

### `plan_next() -> Plan`
Generate a comprehensive plan based on current global state. Returns a Plan with:
- `recommended_action` - Single best action to take next
- `priority_tasks` - Ordered list of actionable tasks
- `blockers` - All currently blocked tasks with reasons
- `observations` - Planning notes and insights

### `plan_for_goal(goal_id: str) -> Plan`
Generate a targeted plan for a specific goal. Analyzes the goal's children (tasks) and:
- Identifies active vs blocked subtasks
- Recommends appropriate next action
- Includes prediction-based success estimates
- Returns detailed task breakdown

### `create_tasks_for_goal(goal_id: str, task_descriptions: List[str]) -> List[str]`
Decompose a goal into individual tasks. Creates task nodes in the graph with:
- Status set to "active"
- Detection timestamp
- Initial confidence score
- "contains" edge linking to parent goal

### `detect_completed_goals() -> List[str]`
Identify goals where all child tasks have been completed. Automatically:
- Marks goal status as "completed"
- Sets progress to 1.0
- Records completion timestamp
- Returns list of completed goal IDs

### `get_planner(graph: Optional[RealityGraph] = None) -> Planner`
Get the global Planner singleton instance. Optionally pass a custom graph for testing.

## Integration Points

### Input Dependencies

| Component | Purpose |
|-----------|---------|
| `RealityGraph` | Provides current state: nodes (goals, tasks), edges (contains, blocks) |
| `AttentionSystem` | Supplies attention scores for task prioritization |
| `PredictionEngine` | Provides success probability and risk estimates |

### Output Consumers

| Component | Uses |
|-----------|------|
| `Executor` | Receives recommended actions for execution |
| `ReflectionEngine` | Analyzes planning outcomes for lessons |
| `Evolution` | Updates understanding based on planning effectiveness |

### Data Flow

```
Goal →分解 → Tasks → Attention Scores → Prioritized Plan
                         ↓
                    Predictions → Success Estimates
                         ↓
                    Graph State → Blocker Detection
```

## Implementation Reference

**File:** `core/planner.py`  
**Lines:** 308  
**Primary Class:** `Planner`

### Core Methods

```python
def plan_next(self) -> Plan:
    # Refresh state from all systems
    # Find all blockers
    # Generate priority tasks list
    # Determine recommended action
    # Generate observations
    return plan

def _find_all_blockers(self) -> List[Dict[str, str]]:
    # Query graph for blocked tasks
    # Extract block reasons
    # Return structured list

def _prioritize_tasks(self) -> List[Action]:
    # Get active nodes from attention system
    # Filter to tasks/goals
    # Sort by attention score (priority)
    # Return top 10 actions

def _recommend_action(self, plan: Plan) -> Optional[Action]:
    # Priority: unblock > execute high-priority > investigate
    # Return single best action or None
```

### Output Structures

```python
@dataclass
class Action:
    description: str
    action_type: str  # execute, investigate, unblock, create, wait
    target_id: str    # Node ID
    priority: float   # 0=low, 1=critical
    reason: str       # Justification

@dataclass
class Plan:
    recommended_action: Optional[Action] = None
    priority_tasks: List[Action] = field(default_factory=list)
    blockers: List[Dict[str, str]] = field(default_factory=list)
    observations: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
```

## Status

✅ **Production Ready**  
- 308 lines of code  
- Singleton pattern for global access  
- Graph-driven planning with attention-based prioritization  
- Comprehensive blocker detection and action recommendation  
- Integration with Reality Graph, Attention System, and Prediction Engine  
- Unit tested for common planning scenarios

---

*Generated for AXIMA v6.0 - July 17, 2026*
