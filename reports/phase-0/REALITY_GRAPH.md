# Reality Graph

## Purpose

The Reality Graph is the persistent knowledge graph that serves as the foundational memory substrate for the AXIMA cognitive system. It maintains a structured representation of all entities, relationships, and knowledge accumulated across sessions, enabling AXIMA to reason over connected information, track goals, and build cumulative understanding of the user's world.

Unlike ephemeral session memory, the Reality Graph persists between interactions, providing continuity of knowledge and enabling long-term reasoning about projects, goals, and concepts.

## Architecture

### Node Types

| Type | Description |
|------|-------------|
| `user` | Represents a human user interacting with the system |
| `project` | A software project, initiative, or body of work |
| `goal` | A high-level objective the user wants to achieve |
| `task` | A concrete, actionable unit of work toward a goal |
| `fact` | A verified piece of information or assertion |
| `concept` | An abstract idea, pattern, or domain concept |
| `theory` | A hypothesis or mental model under evaluation |
| `memory` | A recorded observation, interaction, or event |
| `session` | A bounded interaction period with the system |

Each node carries:
- `id` — unique identifier (UUID)
- `type` — one of the types above
- `label` — human-readable name
- `properties` — arbitrary key-value metadata
- `created_at` — timestamp of creation
- `updated_at` — timestamp of last modification

### Relationship Types

| Relationship | Semantics |
|--------------|-----------|
| `depends_on` | Target must be completed/resolved before source |
| `contains` | Source hierarchically contains target |
| `supports` | Source provides evidence or backing for target |
| `contradicts` | Source conflicts with or negates target |
| `extends` | Source builds upon or elaborates target |
| `owns` | Source has ownership/authority over target |
| `created` | Source produced or authored target |
| `blocked_by` | Source cannot proceed until target is resolved |
| `relates_to` | General semantic association |
| `derived_from` | Source was generated or inferred from target |

Edges are directed and carry optional `properties` metadata.

## API

### Node Operations

```python
add_node(type: str, label: str, properties: dict = None) -> str
```
Creates a new node in the graph. Returns the node ID.

```python
get_node(node_id: str) -> dict | None
```
Retrieves a node by its unique ID. Returns `None` if not found.

```python
update_node(node_id: str, properties: dict) -> bool
```
Merges new properties into an existing node. Updates `updated_at` timestamp.

```python
remove_node(node_id: str) -> bool
```
Removes a node and all edges connected to it.

```python
find_nodes(type: str = None, label: str = None, **properties) -> list[dict]
```
Searches for nodes matching the given criteria. Supports filtering by type, label, and arbitrary property key-value pairs. Uses indexed lookups for efficient retrieval.

### Edge Operations

```python
add_edge(source_id: str, target_id: str, relationship: str, properties: dict = None) -> str
```
Creates a directed edge between two nodes. Returns the edge ID.

```python
remove_edge(edge_id: str) -> bool
```
Removes an edge by its ID.

### Traversal Operations

```python
neighbors(node_id: str, direction: str = "both", relationship: str = None) -> list[dict]
```
Returns all nodes connected to the given node. Optionally filter by direction (`in`, `out`, `both`) and relationship type.

```python
path_between(source_id: str, target_id: str, max_depth: int = 10) -> list[str] | None
```
Finds the shortest path between two nodes using BFS traversal. Returns an ordered list of node IDs forming the path, or `None` if no path exists within `max_depth`.

## Indexing

The Reality Graph maintains three indexes for efficient lookup:

- **Type index** — maps node types to sets of node IDs for fast `find_nodes(type=...)` queries
- **Label index** — maps normalized labels to node IDs for name-based search
- **Property index** — maps `(key, value)` tuples to node IDs for property-based filtering

Indexes are maintained incrementally on every `add_node`, `update_node`, and `remove_node` operation, avoiding full-graph scans.

## Path Finding

The `path_between` operation uses **Breadth-First Search (BFS)** to find the shortest path between any two nodes in the graph:

1. Start from the source node
2. Expand outward level by level through connected edges (both directions)
3. Track visited nodes to avoid cycles
4. Return the first path found (guaranteed shortest by BFS property)
5. Respect `max_depth` to bound search in large graphs

This enables queries like "how is this task related to that goal?" or "what chain of dependencies blocks this work?"

## Persistence

The graph is persisted as a JSON file at:

```
~/.axima/reality_graph.json
```

The file structure:

```json
{
  "nodes": {
    "<node_id>": {
      "id": "<uuid>",
      "type": "goal",
      "label": "Ship v2.0",
      "properties": {"priority": "high"},
      "created_at": "2026-07-17T10:00:00Z",
      "updated_at": "2026-07-17T12:30:00Z"
    }
  },
  "edges": {
    "<edge_id>": {
      "id": "<uuid>",
      "source": "<node_id>",
      "target": "<node_id>",
      "relationship": "depends_on",
      "properties": {}
    }
  }
}
```

Persistence is triggered on every mutation (write-through) with an optional batch mode for bulk operations. The file is atomically written to prevent corruption.

## Memory Footprint

- **Space complexity**: O(N + E) where N = number of nodes, E = number of edges
- **Index overhead**: O(N) additional for type, label, and property indexes
- **Persistence**: Full JSON serialization; file size scales linearly with graph contents
- **Load time**: Full graph loaded into memory on initialization for O(1) node/edge access

## Usage Examples

### Tracking a project and its goals

```python
from core.reality_graph import RealityGraph

graph = RealityGraph()

# Create project structure
project_id = graph.add_node("project", "AXIMA v6.0", {"status": "active"})
goal_id = graph.add_node("goal", "Implement Reality Graph", {"priority": "high"})
task_id = graph.add_node("task", "Add BFS path finding", {"status": "done"})

# Connect them
graph.add_edge(project_id, goal_id, "contains")
graph.add_edge(goal_id, task_id, "contains")
graph.add_edge(task_id, goal_id, "depends_on")
```

### Finding related concepts

```python
# Find all active goals
active_goals = graph.find_nodes(type="goal", status="active")

# Get everything connected to a goal
related = graph.neighbors(goal_id, direction="out")

# Find how two nodes are connected
path = graph.path_between(task_id, project_id)
# Returns: [task_id, goal_id, project_id]
```

### Recording facts and theories

```python
fact_id = graph.add_node("fact", "Python GIL limits CPU parallelism", {
    "source": "documentation",
    "confidence": 1.0
})
theory_id = graph.add_node("theory", "Async IO approach will be faster", {
    "confidence": 0.7,
    "status": "untested"
})

graph.add_edge(theory_id, fact_id, "derived_from")
graph.add_edge(theory_id, fact_id, "supports")
```

## Integration

### Goal System

The Reality Graph is the backing store for the AXIMA goal system:
- Goals and tasks are nodes in the graph
- Dependencies between tasks are `depends_on` edges
- Completion status is tracked in node properties
- The goal system queries `neighbors` and `path_between` to determine execution order and blockers

### Understanding Pipeline

The understanding pipeline feeds into the Reality Graph:
- New concepts discovered during analysis become `concept` nodes
- Facts extracted from code or documentation become `fact` nodes
- Relationships identified between entities become edges
- The pipeline uses `find_nodes` to check for existing knowledge before creating duplicates
- Contradictions between new and existing facts are captured via `contradicts` edges

### Session Continuity

Each interaction session is recorded as a `session` node:
- Links to all nodes created or modified during that session via `created` edges
- Enables "what did we work on last time?" queries
- Provides temporal context for knowledge evolution

## Implementation

- **Source**: `/root/hybrid-ai/src/python/core/reality_graph.py`
- **Size**: 428 lines
- **Language**: Python
- **Dependencies**: Standard library only (json, uuid, collections, pathlib, datetime)
- **Thread safety**: Single-writer model with atomic file persistence

## Status

**Implemented and tested.** The Reality Graph is fully operational as the persistent knowledge substrate for the AXIMA cognitive system.
