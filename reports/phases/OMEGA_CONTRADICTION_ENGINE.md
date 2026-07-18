# AXIMA Contradiction Engine

**File:** `src/python/core/contradiction.py`  
**Lines:** 302  
**Purpose:** Auto-detects duplicates, support, contradictions, and extensions when knowledge enters the Reality Graph

---

## Overview

The Contradiction Engine is the knowledge integrity system of AXIMA. It ensures that no knowledge is ever silently overwritten—every new fact is analyzed against existing knowledge to detect relationships and create explicit conflict edges.

---

## Core Responsibilities

### 1. Relationship Detection

When knowledge enters the system, the engine automatically detects:

| Relationship Type | Description |
|-------------------|-------------|
| `DUPLICATE` | Same fact expressed with different wording (>85% similarity) |
| `SUPPORTS` | New fact strengthens or reinforces existing knowledge |
| `CONTRADICTS` | New fact conflicts with existing knowledge (same subject, different object) |
| `EXTENDS` | New fact adds information to existing knowledge |
| `OBSOLETES` | New fact supersedes older information |

### 2. Never Silent Overwrites

The engine **never** silently replaces existing knowledge. It always creates relationship edges in the Reality Graph:
- `contradicts` edges for conflicts
- `supports` edges for reinforcement
- `extends` edges for additions

### 3. Confidence-Based Analysis

All relationship detections include confidence scores based on:
- Text similarity (Jaccard word overlap)
- Subject matching
- Object divergence
- Negation detection

---

## Architecture

### Main Classes

#### `Relationship` (class)

Constants for relationship types:
```python
DUPLICATE = "duplicate"
SUPPORTS = "supports"
CONTRADICTS = "contradicts"
EXTENDS = "extends"
OBSOLETES = "obsoletes"
```

#### `ConflictAnalysis` (dataclass)

Result container with computed properties:
- `has_contradictions`: Boolean
- `has_duplicates`: Boolean
- `contradicts`: List of conflict records
- `supports`: List of support records
- `duplicates`: List of duplicate records
- `extensions`: List of extension records
- `summary()`: Returns {type: count} dict

#### `ContradictionEngine` (class)

Main engine with methods:

| Method | Purpose |
|--------|---------|
| `analyze_new_fact(content, subject, predicate, obj)` | Analyze new knowledge against all existing |
| `record_relationships(new_node_id, analysis)` | Store relationship edges in graph |
| `scan_all()` | Find contradictions between existing facts |
| `resolve_contradiction(keep_id, discard_id, reason)` | Manual resolution |

---

## Detection Algorithms

### Text Similarity

Word-level Jaccard similarity:
- Extracts words ≥3 characters
- Computes intersection / union
- Thresholds:
  - >0.85 = duplicate
  - 0.4-0.85 = potential support
  - <0.3 (with same subject) = contradiction

### Negation Detection

Regex pattern:
```python
\b(?:not|n't|never|no|cannot|can't|won't|doesn't|isn't)\b
```

Used to detect when two similar facts have opposite truth values.

### Subject-Object Conflict Detection

1. Compare subject similarity (>0.7 threshold)
2. If subjects match, compare objects
3. Object similarity <0.3 = contradiction
4. Object similarity 0.3-0.7 = extends
5. If negation differs = stronger contradiction signal

---

## Usage Examples

### Analyzing New Knowledge

```python
from core.contradiction import get_contradiction_engine

engine = get_contradiction_engine()

# Analyze a new fact
analysis = engine.analyze_new_fact(
    "Water boils at 90°C at sea level"
)

# Check relationships
if analysis.has_contradictions:
    print(f"Contradicts: {analysis.contradicts}")
if analysis.has_duplicates:
    print(f"Duplicates: {analysis.duplicates}")

# Record relationships in the graph
# (Assume we have a new_node_id from adding the fact)
# engine.record_relationships(new_node_id, analysis)
```

### Scanning for Existing Contradictions

```python
# Scan entire graph for contradictions
contradictions = engine.scan_all()
for conflict in contradictions:
    print(f"Conflict: {conflict.new_content}")
    print(f"  {conflict.summary()}")
```

### Resolving Contradictions

```python
# Manually resolve by keeping one, discarding another
success = engine.resolve_contradiction(
    keep_id="fact_123",
    discard_id="fact_456",
    reason="New experimental data supersedes older measurement"
)

# This:
# - Boosts confidence of kept fact (+0.2)
# - Marks discarded fact as disputed (confidence 0.1)
```

---

## Integration Points

### Reality Graph

The engine works with `RealityGraph` via:
- `find_nodes(node_type="fact")` / `find_nodes(node_type="theory")`
- `add_edge(src_id, tgt_id, relation, properties={})`
- `get_node(node_id)`
- `update_node(node_id, properties={})`
- `save()`

### Singleton Pattern

```python
# Global singleton access
engine = get_contradiction_engine(graph=None)  # Uses default graph
```

---

## Output Example

```json
{
  "new_content": "Water boils at 90°C at sea level",
  "relationships": [
    {
      "type": "contradicts",
      "existing_id": "fact_789",
      "existing_label": "Water boils at 100°C at sea level",
      "confidence": 0.85,
      "reason": "Same subject 'Water' but conflicting assertions"
    }
  ],
  "summary": {
    "contradicts": 1
  }
}
```

---

## Design Principles

1. **Explicit is better than implicit** — All conflicts are edges, not hidden flags
2. **Never silent overwrites** — New knowledge always creates relationship metadata
3. **Confidence-aware** — All detections include numerical confidence scores
4. **Extensible** — New relationship types can be added without breaking existing code
5. **Graph-native** — Works with Reality Graph as the single source of truth

---

## Performance Characteristics

- Linear scan of facts for each new input
- Jaccard similarity is O(n) in word count
- Real-time analysis suitable for ≤10K facts
- For large graphs, consider indexing by subject/predicate

---

## Future Enhancements

- [ ] Fuzzy matching with embedding vectors
- [ ] Temporal reasoning (newer facts may override older)
- [ ] Domain-specific conflict rules
- [ ] Confidence weighting based on source reliability
