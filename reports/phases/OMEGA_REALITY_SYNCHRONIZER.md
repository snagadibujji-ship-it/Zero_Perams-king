# AXIMA Reality Synchronizer — Graph Update Engine

## Purpose

The Reality Synchronizer automatically updates the Reality Graph from Observer observations. It is the bridge between perception and memory, ensuring the graph always reflects current reality without manual intervention.

Key responsibilities:
- Create/update nodes for goals, facts, entities, concepts, tasks
- Detect and flag contradictions between new and existing facts
- Create cross-references between related items
- Track duplicates to avoid redundancy
- Record session events

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Reality Synchronizer                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │   Input: Observation dataclass                        │  │
│  │   Output: SyncResult with changes                     │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │   Entity │ │   Goal   │ │   Task   │ │    Fact      │ │
│  │   Sync   │ │   Sync   │ │   Sync   │ │    Sync      │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘ │
│  ┌──────────┐ ┌─────────────────────────────────────────┐ │
│  │ Concept  │ │ Contradiction Detection & Flagging      │ │
│  │  Sync    │ │ Duplicate Merging                       │ │
│  └──────────┘ │ Cross-Reference Creation                │ │
│                └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### SyncResult Data Class
Tracks all changes made during synchronization.

| Field | Type | Description |
|-------|------|-------------|
| `created_nodes` | List[Dict] | New nodes added [{id, type, label}] |
| `updated_nodes` | List[Dict] | Existing nodes updated [{id, field, old, new}] |
| `created_edges` | List[Dict] | New relationships [{source, target, relation}] |
| `contradictions` | List[Dict] | Conflicting information [{existing, new, issue}] |
| `duplicates_merged` | int | Number of duplicates skipped |
| `timestamp` | float | Sync completion time |

## Key APIs

### RealitySynchronizer.synchronize(observation: Observation) → SyncResult
Primary synchronization function. Processes all extracted elements.

```python
sync = get_reality_sync()
result = sync.synchronize(observation)

result.created_nodes      # 5 nodes added
result.updated_nodes      # 2 nodes updated
result.created_edges      # 3 relationships created
result.contradictions     # 1 conflict detected
result.has_contradictions # True
```

### get_reality_sync(graph=None) → RealitySynchronizer
Get the global singleton synchronizer.

## Integration Points

| Module | Integration |
|--------|-------------|
| `core/observer.py` | Consumes `Observation` output from Observer |
| `core/reality_graph.py` | Operates on `RealityGraph`, adds/updates nodes and edges |
| `core/attention.py` | New nodes become candidates for attention scoring |
| `core/prediction.py` | New goals trigger prediction updates |
| `core/reflection.py` | Contradictions detected here feed into self-correction |

## Implementation Reference

**File**: `core/reality_sync.py`  
**Lines**: 347

### Sync Methods

| Method | Purpose |
|--------|---------|
| `_record_session()` | Record interaction as session node with metadata |
| `_sync_entity()` | Create/update entity nodes, merge with concepts if similar |
| `_sync_goal()` | Create/update goal nodes with urgency/priority |
| `_sync_task()` | Create task nodes, link to parent goal |
| `_sync_fact()` | Create fact nodes with contradiction detection |
| `_sync_concept()` | Create/update abstract concept nodes |
| `_create_cross_references()` | Link co-occurring items (e.g., related concepts) |

### Contradiction Detection
When syncing a fact, the system checks if:
1. Same subject exists in graph
2. Different object/predicate is claimed
3. Same fact type (assertion vs relationship)

If contradictory facts exist, both are stored with a `contradicts` edge, and the conflict is recorded in `SyncResult.contradictions`.

### Similarity Matching
Uses word overlap ratio (≥70%) to determine if entities/goals/facts are similar enough to merge/update rather than create new nodes.

## Status

✅ **Production Ready**  
- Fully implemented and tested
- Handles all node types (goal, task, fact, concept, entity)
- Contradiction detection active
- Auto-merging duplicates reduces graph bloat
