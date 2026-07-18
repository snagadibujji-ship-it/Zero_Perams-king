# AXIMA Prediction Engine — Goal Outcome Forecasting

## Purpose

The Prediction Engine maintains forecasts for active goals in the Reality Graph. Every active goal has associated predictions that evolve as reality changes — no static projections.

Predictions inform decision-making by estimating:
- Probability of success
- Estimated completion time (in interactions)
- Risk level and specific risk factors
- Confidence in the prediction
- Historical trends

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Prediction Engine                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │   Input: Active goals from Reality Graph              │  │
│  │   Output: Prediction objects with forecasts           │  │
│  └───────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Prediction = f(progress, tasks, blockers, facts)     │ │
│  │                                                         │ │
│  │  success_probability: 0.0–1.0                         │ │
│  │  estimated_turns: integer                             │ │
│  │  risk_level: 0.0–1.0                                  │ │
│  │  confidence: 0.0–1.0                                  │ │
│  │  trend: "improving" | "declining" | "stable"          │ │
│  └───────────────────────────────────────────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌───────────────────────────┐  │
│  │  Update  │ │  Report  │ │   Accuracy Tracking       │  │
│  │  All     │ │  High    │ │   (completed goals)       │  │
│  └──────────┘ └──────────┘ └───────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Prediction Data Class
Complete forecast for a goal.

| Field | Type | Description |
|-------|------|-------------|
| `success_probability` | float | Estimated 0.0–1.0 |
| `estimated_turns` | int | Interactions to complete |
| `risk_level` | float | 0=safe, 1=high risk |
| `confidence` | float | How confident in prediction |
| `blockers` | List[str] | What's blocking success |
| `risks` | List[str] | Identified risk factors |
| `history` | List[Dict] | Previous snapshots [time, prob, conf] |
| `trend` | str | "improving" / "declining" / "stable" |

## Key APIs

### PredictionEngine.update_all()
Update predictions for all active goals.

```python
engine = get_predictions()
engine.update_all()
```

### PredictionEngine.predict_goal(goal_id) → Optional[Prediction]
Get prediction for specific goal.

```python
pred = engine.predict_goal(goal_id)
print(f"Success: {pred.success_probability:.0%}")
print(f"Risk: {pred.risk_level:.0%}")
print(f"Trend: {pred.trend}")
print(f"Blockers: {pred.blockers}")
```

### PredictionEngine.high_risk() → List[Prediction]
Get predictions with risk > 60%.

```python
for pred in engine.high_risk():
    print(f"WARNING: {pred.target_label} has {pred.risk_level:.0%} risk")
```

### PredictionEngine.accuracy_report() → Dict
Track historical prediction accuracy.

```python
{
    "total_predictions": 47,
    "completed_goals": 12,
    "tracked_completions": 12,
    "correct_predictions": 9,
    "accuracy": 0.75
}
```

## Integration Points

| Module | Integration |
|--------|-------------|
| `core/reality_graph.py` | Reads active goals and their children (tasks) |
| `core/attention.py` | High-risk predictions may boost attention scores |
| `core/reality_sync.py` | Contradictions trigger prediction recalculation |
| `core/cognitive_runtime.py` | Uses predictions to decide goal commitment |

## Implementation Reference

**File**: `core/prediction.py`  
**Lines**: 295

### Prediction Components

| Method | Logic |
|--------|-------|
| `_estimate_success()` | Base on progress (50%) + task completion ratio (40%) - block ratio (20%) |
| `_estimate_risk()` | Blocked tasks (+30%), many active tasks (+20%), low confidence (+20%), contradictions (+20%) |
| `_estimate_completion()` | Active tasks × 2 turns + blocked tasks × 4 turns |
| `_estimate_confidence()` | Base 0.4 + (child count × 0.05), capped at 0.9 |
| `_find_blockers()` | Collect tasks with status="blocked" |
| `_identify_risks()` | Check for contradictions and high blocker counts |

### History Recording
Each prediction maintains a history of 50 snapshots for trend analysis.

```python
pred.record_snapshot()
# Appends {time, success_probability, confidence, risk_level}
```

### Trend Calculation
Compares recent 3 snapshots to earlier history:
- `improving`: avg recent > avg past + 0.1
- `declining`: avg recent < avg past - 0.1
- `stable`: otherwise

## Status

✅ **Production Ready**  
- Fully implemented with all components
- History tracking active
- Accuracy tracking enabled
