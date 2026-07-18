# AXIMA Understanding Evolution - Documentation

## Purpose

The Understanding Evolution system ensures AXIMA's knowledge graph doesn't just accumulate—it actively improves over time. It implements mechanisms for:

- **Confidence updates** - Weights strengthen or weaken based on new evidence
- **Principle refinement** - Statements sharpen as understanding deepens
- **Principle merging** - Related concepts combine into stronger unified principles
- **Principle retirement** - Disproven or weak knowledge is marked inactive
- **Cross-domain links** - Analogies between different domains emerge automatically

Evolution makes knowledge not just persistent, but *adaptive*.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                   Understanding Evolution                           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Reality Graph   │  │  Understanding   │  │  Abstraction     │  │
│  │  (knowledge base)│  │  Pipeline        │  │  Levels          │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Confidence Updates                                            │ │
│  │  - Evidence accumulation                                       │ │
│  │  - Diminishing returns (1.0 ceiling)                           │ │
│  │  - Proportional decay (0.0 floor)                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Principle Management                                          │ │
│  │  - Refinement (sharpen statements)                             │ │
│  │  - Merging (combine related principles)                        │ │
│  │  - Retirement (mark weak principles inactive)                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Cross-Domain Analysis                                         │ │
│  │  - Structural similarity detection                             │ │
│  │  - Analogy discovery across domains                            │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

**Key components:**
- `UnderstandingEvolution` class - Main orchestration engine
- Abstraction level tracking (fact/principle/theory)
- Structural similarity metrics for cross-domain analysis

**Design patterns:**
- Builder pattern (gradual principle refinement)
- Graph analytics (structural similarity)
- Knowledge lifecycle management (birth → refinement → retirement)

## Key APIs

### `update_confidence(node_id: str, supporting: bool = True, amount: float = 0.1) -> float`
Update confidence based on new evidence. Implements diminishing returns:

- `supporting=True`: `new = min(1.0, current + amount * (1 - current))`
- `supporting=False`: `new = max(0.0, current - amount * current)`

Returns the new confidence value.

### `refine_principle(principle_id: str, new_statement: str, reason: str) -> bool`
Refine a principle's statement. Stores refinement history:
- Old statement preserved
- New statement applied
- Reason logged
- Timestamp recorded
- History capped at last 10 refinements

### `merge_principles(principle_ids: List[str], merged_statement: str) -> Optional[str]`
Merge multiple related principles into one stronger principle.

**Returns:** New merged principle's node ID

**Actions:**
- Collects all supporting rules from merged principles
- Creates new principle with higher confidence (avg + 0.1, max 0.95)
- Links old principles as "derived_from"
- Marks old principles as "merged"

### `retire_weak_principles(threshold: float = 0.2) -> List[str]`
Retire principles below confidence threshold.

**Returns:** List of retired principle IDs

**Actions:**
- Marks principles as "retired"
- Records retirement timestamp and reason
- Does NOT delete (preserves historical knowledge)

### `find_cross_domain_links() -> List[Dict[str, Any]]`
Find potential analogies between different domains.

**Returns:** List of structural similarity matches with similarity scores

**Method:**
1. Groups concepts by domain
2. Compares concepts across domains
3. Uses structural similarity (neighborhood relation types)
4. Filters out existing connections
5. Returns top 20 potential links

### `evolution_report() -> Dict[str, Any]`
Comprehensive report on knowledge evolution:
- Total facts, theories, concepts
- Average confidence per type
- Retired/merged/refined counts
- Cross-domain edge count

### `get_evolution(graph: Optional[RealityGraph] = None) -> UnderstandingEvolution`
Get the global UnderstandingEvolution instance.

## Integration Points

### Input Dependencies

| Component | Purpose |
|-----------|---------|
| `RealityGraph` | Knowledge base with confidence scores and relationships |
| `UnderstandingPipeline` | Abstraction level context (fact/principle/theory) |

### Output Consumers

| Component | Uses |
|-----------|------|
| `ReflectionEngine` | Applies lessons via confidence updates |
| `Planner` | Uses refined principles for better planning |
| `Evolution` (self) | Continuously improves understanding |

### Data Flow

```
New Evidence → update_confidence() → Strength Adjustment
                 ↓
      Refinement / Merging / Retirement
                 ↓
      Cross-Domain Link Discovery
                 ↓
      Evolution Report (monitoring)
```

## Implementation Reference

**File:** `core/evolution.py`  
**Lines:** 286  
**Primary Class:** `UnderstandingEvolution`

### Confidence Update Logic

```python
def update_confidence(self, node_id: str, supporting: bool = True,
                      amount: float = 0.1) -> float:
    node = self._graph.get_node(node_id)
    current = node.properties.get("confidence", 0.5)
    
    if supporting:
        # Diminishing returns: closer to 1.0, slower updates
        new_conf = min(1.0, current + amount * (1 - current))
    else:
        # Proportional decay: closer to 0.0, faster decay
        new_conf = max(0.0, current - amount * current)
    
    self._graph.update_node(node_id, properties={
        "confidence": new_conf,
        "last_evidence_at": time.time(),
        "evidence_count": node.properties.get("evidence_count", 0) + 1,
    })
    return new_conf
```

### Principle Merging

```python
def merge_principles(self, principle_ids: List[str],
                     merged_statement: str) -> Optional[str]:
    if len(principle_ids) < 2:
        return None
    
    # Collect all supporting rules
    all_supports = []
    avg_confidence = 0.0
    
    for pid in principle_ids:
        node = self._graph.get_node(pid)
        if node:
            avg_confidence += node.properties.get("confidence", 0.5)
            for nid, rel, _ in self._graph.neighbors(pid, direction="in"):
                if rel == "supports":
                    all_supports.append(nid)
    
    avg_confidence /= len(principle_ids)
    
    # Create merged principle
    merged_id = self._graph.add_node("theory", merged_statement, {
        "confidence": min(0.95, avg_confidence + 0.1),
        "merged_from": principle_ids,
        "created_at": time.time(),
    })
    
    # Link and mark old as merged
    for pid in principle_ids:
        self._graph.add_edge(merged_id, pid, "derived_from")
        self._graph.update_node(pid, properties={"status": "merged"})
    
    return merged_id
```

### Structural Similarity

```python
def _structural_similarity(self, node1, node2) -> float:
    """Compare relation types in neighborhood."""
    n1_rels = set(rel for _, rel, _ in self._graph.neighbors(node1.id, direction="both"))
    n2_rels = set(rel for _, rel, _ in self._graph.neighbors(node2.id, direction="both"))
    
    if not n1_rels or not n2_rels:
        return 0.0
    
    overlap = len(n1_rels & n2_rels)
    union = len(n1_rels | n2_rels)
    return overlap / max(union, 1)  # Jaccard-like similarity
```

### Output Structures

```python
# Evolution report dictionary
{
    "total_facts": int,
    "total_theories": int,
    "total_concepts": int,
    "avg_fact_confidence": float,
    "avg_theory_confidence": float,
    "retired_theories": int,
    "merged_theories": int,
    "refined_theories": int,
    "cross_domain_edges": int,
}
```

## Status

✅ **Production Ready**  
- 286 lines of code  
- Confidence updates with diminishing returns/proportional decay  
- Principle refinement with full history tracking  
- Principle merging with support inheritance  
- Principle retirement (mark inactive, not delete)  
- Cross-domain structural similarity analysis  
- Evolution metrics and reporting  

---

*Generated for AXIMA v6.0 - July 17, 2026*
