# AXIMA Attention System — Cognitive Focus Engine

## Purpose

The Attention System implements dynamic cognitive focus by scoring all nodes in the Reality Graph and maintaining a subset as "active" cognitive foreground. Only high-scoring nodes consume reasoning resources; others remain stored but dormant.

Attention is computed from six weighted components that determine what AXIMA is "thinking about" at any moment.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Attention System                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │   Input: Reality Graph nodes                          │  │
│  │   Output: Active nodes (cognitive foreground)         │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  AttentionScore = Σ(weight × component)               │  │
│  │                                                         │  │
│  │  importance:  0.30 — Critical to active goals         │  │
│  │  urgency:     0.25 — Time pressure                    │  │
│  │  novelty:     0.15 — How recently discovered          │  │
│  │  confidence:  0.10 — Information reliability          │  │
│  │  recency:     0.10 — Recent access/update             │  │
│  │  energy:      0.10 — Processing invested              │  │
│  └───────────────────────────────────────────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌───────────────────────────┐  │
│  │  Update  │ │  Active  │ │    Boost/Decay Control    │  │
│  │  Scores  │ │  Selection│ │   (manual reinforcement)  │  │
│  └──────────┘ └──────────┘ └───────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### AttentionScore Data Class
Per-node attention computation.

| Field | Type | Range |
|-------|------|-------|
| `total` | float | 0.0–1.0 (weighted composite) |
| `importance` | float | 0.0–1.0 |
| `urgency` | float | 0.0–1.0 |
| `novelty` | float | 0.0–1.0 |
| `confidence` | float | 0.0–1.0 |
| `recency` | float | 0.0–1.0 |
| `energy` | float | 0.0–1.0 |

## Key APIs

### AttentionSystem.update_scores()
Recompute attention scores for all nodes.

```python
attention = get_attention()
attention.update_scores()
```

### AttentionSystem.active_nodes(limit=None) → List[AttentionScore]
Get the highest-scoring nodes (cognitive foreground).

```python
active = attention.active_nodes(limit=10)
# Returns top 10 nodes by attention score
```

### AttentionSystem.current_focus() → Optional[AttentionScore]
Get the single highest-scoring node.

```python
focus = attention.current_focus()
if focus:
    print(f"Currently thinking about: {focus.label}")
```

### AttentionSystem.boost(node_id, component, amount=0.2)
Manually boost a component (used to draw attention).

```python
attention.boost(node_id, "urgency", 0.3)  # Increase urgency by 30%
```

### AttentionSystem.decay(rate=0.05)
Apply time-based decay to let attention fade naturally.

```python
attention.decay(rate=0.05)  # Reduce urgency, novelty, energy
```

### AttentionSystem.stats() → Dict
System statistics for monitoring.

```python
{
    "nodes_scored": 127,
    "active_nodes": 14,
    "top_focus": "fix math router",
    "avg_attention": 0.42,
    "max_attention": 0.89
}
```

## Integration Points

| Module | Integration |
|--------|-------------|
| `core/reality_graph.py` | Reads all nodes to compute attention scores |
| `core/reality_sync.py` | New nodes automatically score and may become active |
| `core/prediction.py` | Active goals are prediction targets |
| `core/cognitive_runtime.py` | Uses `current_focus()` to determine next processing step |

## Implementation Reference

**File**: `core/attention.py`  
**Lines**: 285

### Component Calculators

| Method | Logic |
|--------|-------|
| `_compute_importance()` | Goal priority × 0.1, blocked tasks get 0.8 |
| `_compute_urgency()` | Node urgency prop, blocked tasks get 0.7 |
| `_compute_novelty()` | Exponential decay: new=1.0, 1hr=0.6, 24hr=0.1 |
| `_compute_confidence()` | Node confidence property |
| `_compute_recency()` | Exponential decay on last access/update |
| `_compute_energy()` | (mentions + used_count) / 10, capped at 1.0 |

### Default Weights
```python
{
    'importance': 0.30,
    'urgency': 0.25,
    'novelty': 0.15,
    'confidence': 0.10,
    'recency': 0.10,
    'energy': 0.10,
}
```

Weights can be adjusted dynamically via `set_weights()` to shift focus (e.g., prioritize urgency during crises).

## Status

✅ **Production Ready**  
- Fully implemented with dynamic scoring
- Boost/decay controls active
- Used by cognitive runtime to determine focus
