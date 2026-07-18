# AXIMA Curiosity Engine

**File:** `src/python/core/curiosity.py`  
**Lines:** 305  
**Purpose:** Autonomous gap-finding and research task generation

---

## Overview

The Curiosity Engine is AXIMA's autonomous learning system. It operates in the background to identify knowledge gaps, weak theories, disconnected nodes, and generates research tasks automatically—without user prompting.

---

## Core Responsibilities

The engine continuously scans the Reality Graph for:

1. **Weak Knowledge** — Facts/theories with low confidence (<0.4)
2. **Disconnected Nodes** — Facts with no connections
3. **Incomplete Goals** — Goals with no decomposed tasks
4. **Unresolved Contradictions** — Contradictory facts not yet resolved
5. **Stale Knowledge** — Facts not accessed in 7+ days

---

## Architecture

### Data Structures

#### `KnowledgeGap` (dataclass)

```python
@dataclass
class KnowledgeGap:
    description: str           # Human-readable gap description
    gap_type: str              # "unknown", "weak", "disconnected", "incomplete", "stale"
    domain: str                #所属领域
    importance: float          # 0.0-1.0, higher = more urgent
    related_nodes: List[str]   # Node IDs involved
    suggested_action: str      # What to do about it
```

#### `ResearchTask` (dataclass)

```python
@dataclass
class ResearchTask:
    question: str              # Research question
    priority: float            # 0.0-1.0
    domain: str
    gap_type: str              # Which gap generated this
    reason: str                # Why this is worth investigating
    related_to: List[str]      # Related node IDs
```

---

### Main Classes

#### `CuriosityEngine`

Main engine class with methods:

| Method | Purpose |
|--------|---------|
| `find_gaps()` | Returns all detected knowledge gaps |
| `generate_research_tasks(limit=10)` | Converts gaps to research tasks |
| `curiosity_score()` | Overall curiosity level (0.0-1.0) |
| `stats()` | Gap statistics by type |
| `idle_think()` | Background cognition (called when idle) |

---

## Gap Detection Methods

### 1. Weak Knowledge

Scans all `fact` and `theory` nodes:
- Flags nodes with `confidence < 0.4`
- Importance = `0.6 × (1 - confidence)`
- Suggested action: "Verify or find supporting evidence"

### 2. Disconnected Regions

Finds nodes with zero connections:
- Checks all `fact`, `concept`, `theory` nodes
- No neighbors in any direction
- Importance = 0.4
- Suggested action: "Find relationships for: [label]"

### 3. Incomplete Goals

Checks goals with no children:
- Filters to `status == "active"`
- No `contains` relation children
- Importance = 0.8 (high priority)
- Suggested action: "Decompose goal into tasks"

### 4. Unresolved Contradictions

Finds `contradicts` edges not yet resolved:
- Groups contradictions by node pairs
- Skips if either fact has `status == "disputed"`
- Importance = 0.7
- Suggested action: "Resolve which fact is correct"

### 5. Stale Knowledge

Finds unused facts:
- Threshold: 7 days since `last_seen`
- Importance = 0.3 (low priority)
- Suggested action: "Verify if still current"

---

## Research Task Generation

The `_gap_to_task()` method converts each gap type:

| Gap Type | Question Format | Reason |
|----------|----------------|--------|
| `weak` | "What evidence supports: [fact]?" | Low confidence needs verification |
| `disconnected` | "What relates to: [fact]?" | Isolated knowledge should connect |
| `incomplete` | "What tasks are needed for: [goal]?" | Goal needs decomposition |
| `contradiction` | "Which is correct: [conflict]?" | Contradictions need resolution |
| `stale` | "Is this still true: [fact]?" | Knowledge may be outdated |

Tasks are deduplicated and sorted by priority.

---

## Usage Examples

### Basic Gap Finding

```python
from core.curiosity import get_curiosity

curiosity = get_curiosity()

# Find all gaps
gaps = curiosity.find_gaps()
for gap in gaps:
    print(f"[{gap.gap_type}] {gap.description}")
    print(f"  Importance: {gap.importance:.0%}")
    print(f"  Action: {gap.suggested_action}")
```

### Generating Research Tasks

```python
# Generate up to 5 research tasks
tasks = curiosity.generate_research_tasks(limit=5)
for task in tasks:
    print(f"Task: {task.question}")
    print(f"  Priority: {task.priority:.0%}")
    print(f"  Reason: {task.reason}")
```

### Background Cognition

```python
# Called when system is idle
results = curiosity.idle_think()
print(f"Gaps found: {results['gaps_found']}")
print(f"Tasks created: {results['research_tasks']}")
```

### Checking Curiosity Level

```python
# Overall curiosity score
score = curiosity.curiosity_score()
# High = many gaps, system should explore
# Low = knowledge is well-connected
print(f"Curiosity score: {score:.0%}")
```

### Statistics

```python
stats = curiosity.stats()
print(f"Total gaps: {stats['total_gaps']}")
print(f"By type: {stats['gap_types']}")
print(f"Avg importance: {stats['avg_importance']:.2f}")
```

---

## Integration with Cognitive Runtime

The Cognitive Runtime calls the Curiosity Engine during `idle_think()`:

```python
def idle_think(self) -> Dict[str, Any]:
    results = {
        "gaps_found": 0,
        "research_tasks": 0,
        "weak_retired": 0,
        "cross_links": 0,
    }
    
    # 1. Find gaps
    gaps = self._curiosity.find_gaps()
    results["gaps_found"] = len(gaps)
    
    # 2. Generate tasks and create them as goals
    tasks = self._curiosity.generate_research_tasks(limit=3)
    for task in tasks:
        if not self._graph.find_nodes(node_type="task", label_contains=task.question[:30]):
            self._graph.add_node("task", task.question[:80], {
                "status": "active",
                "source": "curiosity",
                "priority": int(task.priority * 5),
            })
    
    # 3. Find weak principles to retire
    retired = self._evolution.retire_weak_principles(threshold=0.15)
    results["weak_retired"] = len(retired)
    
    # ... more background thinking ...
    
    return results
```

---

## Curiosity Score Formula

```
curiosity_score = min(1.0, total_importance / num_nodes)
```

Where `total_importance` is the sum of all gap importances.

This normalizes curiosity against graph size:
- Small graph with many gaps = high score
- Large graph with few gaps = low score

---

## Output Example

```json
{
  "total_gaps": 12,
  "gap_types": {
    "weak": 5,
    "disconnected": 3,
    "incomplete": 2,
    "contradiction": 1,
    "stale": 1
  },
  "curiosity_score": 0.42,
  "avg_importance": 0.58
}
```

Research tasks generated:
```json
[
  {
    "question": "What evidence supports: Water boils at 90°C at sea level?",
    "priority": 0.6,
    "domain": "physics",
    "gap_type": "weak",
    "reason": "Low confidence knowledge needs verification"
  },
  {
    "question": "What relates to: Quantum Entanglement?",
    "priority": 0.4,
    "domain": "physics",
    "gap_type": "disconnected",
    "reason": "Isolated knowledge should be connected"
  }
]
```

---

## Design Principles

1. **Autonomous** — Runs without user prompting
2. **Actionable** — Every gap has a suggested action
3. **Priority-aware** — Higher importance gaps get priority
4. **Persistent** — Research tasks are created as graph nodes
5. **Background capable** — `idle_think()` for non-blocking operation

---

## Performance Characteristics

- Scans entire graph for each operation
- Capped stale findings at 20 items
- Capped research task generation at `limit * 2` candidates
- Suitable for graphs up to ~100K nodes with optimization

---

## Future Enhancements

- [ ] Weight gaps by domain importance
- [ ] Learn which gaps lead to useful discoveries
- [ ] Prioritize cross-domain gaps
- [ ] Predict which gap-filling will most improve predictions
- [ ] Collaborative curiosity (shared gaps across instances)
