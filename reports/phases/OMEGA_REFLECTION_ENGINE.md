# AXIMA Reflection Engine - Documentation

## Purpose

The Reflection Engine performs post-execution analysis to turn every interaction into permanent knowledge. It asks after every execution:

- What happened?
- Was the prediction correct?
- What failed? What succeeded?
- What surprised us?
- What should change?

Reflection is the core mechanism that ensures AXIMA doesn't just accumulate data—it learns and improves. Every lesson is stored in the Reality Graph as permanent knowledge that persists across sessions.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Reflection Engine                               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Observation     │  │  Prediction      │  │  Result          │  │
│  │  (input)         │  │  (comparison)    │  │  (outcome)       │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Reflection Analysis                                           │ │
│  │  - Prediction accuracy check                                   │ │
│  │  - Success/failure detection                                   │ │
│  │  - Surprise detection                                          │ │
│  │  - Lesson extraction                                           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Knowledge Storage (Reality Graph)                            │ │
│  │  - Store lessons as permanent nodes                           │ │
│  │  - Link to source interactions                                │ │
│  │  - Track lesson type and confidence                           │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

**Key components:**
- `ReflectionEngine` class - Main orchestration engine
- `Reflection` dataclass - Complete analysis of one interaction
- `Lesson` dataclass - Extracted reusable lesson with type and domain

**Design patterns:**
- Singleton pattern (`get_reflection()`) for global access
- Observer pattern (reflects on execution results)
- Knowledge compilation (transforming raw experience into structured knowledge)

## Key APIs

### `reflect(observation: Observation, prediction: Optional[Prediction], result_status: str, result_engine: str, result_answer: str) -> Reflection`
Main reflection method. Called after every execution to analyze what happened and return a complete Reflection including:
- Prediction accuracy analysis
- Success/failure detection
- Surprise detection
- Extracted lessons
- Change recommendations

**Stores reflections in Reality Graph** as permanent knowledge (not just in-memory).

### `recent_lessons(n: int = 10) -> List[Lesson]`
Get the most recent lessons learned across all reflections. Returns up to `n` lessons.

### `prediction_accuracy() -> float`
Calculate overall prediction accuracy from reflection history. Compares predictions against actual outcomes.

### `common_failures() -> Dict[str, int]`
Return a frequency dictionary of the most common failure patterns, sorted by occurrence count (top 10).

### `stats() -> Dict[str, Any]`
Return comprehensive reflection statistics:
- Total reflections
- Success rate
- Prediction accuracy
- Total lessons learned
- Total surprises detected

### `get_reflection(graph: Optional[RealityGraph] = None) -> ReflectionEngine`
Get the global ReflectionEngine singleton.

## Integration Points

### Input Dependencies

| Component | Purpose |
|-----------|---------|
| `Observation` | Raw input: query, topic, session context |
| `Prediction` | Prediction engine output for comparison |
| `RealityGraph` | Storage for permanent knowledge |

### Output Consumers

| Component | Uses |
|-----------|------|
| `Evolution` | Learns from lessons for principle refinement |
| `Planner` | Avoids known failure patterns when planning |
| `Executor` | Adjusts plugin selection based on failure history |

### Data Flow

```
Execution → Observation + Prediction + Result
                  ↓
          Reflection Analysis
                  ↓
    ┌─────────────┴─────────────┐
    ↓                           ↓
Lessons (stored in Graph)   Statistics (for monitoring)
```

## Implementation Reference

**File:** `core/reflection.py`  
**Lines:** 300  
**Primary Class:** `ReflectionEngine`

### Core Methods

```python
def reflect(self, observation: Observation,
            prediction: Optional[Prediction],
            result_status: str,
            result_engine: str,
            result_answer: str) -> Reflection:
    ref = Reflection(...)
    ref.prediction_was_correct = self._check_prediction(prediction, result_status)
    ref.prediction_error = self._prediction_error(prediction, result_status)
    ref.successes = self._detect_successes(result_status, result_answer)
    ref.failures = self._detect_failures(result_status, result_answer, observation)
    ref.surprises = self._detect_surprises(prediction, result_status, result_engine)
    ref.lessons = self._extract_lessons(ref, observation)
    ref.should_change = self._recommend_changes(ref)
    self._persist_reflection(ref)
    return ref
```

### Prediction Analysis

```python
def _check_prediction(self, prediction: Prediction, outcome: str) -> bool:
    """Was the prediction correct?"""
    if outcome == "success" and prediction.success_probability > 0.5:
        return True
    if outcome in ("failure", "error") and prediction.success_probability < 0.5:
        return True
    return False

def _prediction_error(self, prediction: Prediction, outcome: str) -> float:
    """Absolute error between predicted probability and actual outcome."""
    actual = 1.0 if outcome == "success" else 0.0
    return abs(prediction.success_probability - actual)
```

### Knowledge Persistence

```python
def _persist_reflection(self, ref: Reflection):
    """Store key lessons in the Reality Graph as permanent nodes."""
    for lesson in ref.lessons:
        if lesson.confidence >= 0.6:
            self._graph.add_node("memory", lesson.content[:80], {
                "memory_type": "lesson",
                "lesson_type": lesson.lesson_type,  # observation, correction, insight, warning
                "domain": lesson.domain,
                "confidence": lesson.confidence,
                "source": ref.action_taken[:100],
                "created_at": time.time(),
            })
    self._graph.save()
```

### Output Structures

```python
@dataclass
class Lesson:
    content: str
    lesson_type: str = "observation"  # observation, correction, insight, warning
    domain: str = ""                  # Topic domain
    confidence: float = 0.7           # How confident we are in this lesson
    source_interaction: str = ""      # Reference to original interaction

@dataclass
class Reflection:
    timestamp: float
    action_taken: str
    outcome: str          # success, partial, failure
    engine_used: str
    had_prediction: bool
    prediction_was_correct: bool
    prediction_error: float
    lessons: List[Lesson]
    surprises: List[str]
    failures: List[str]
    successes: List[str]
    should_change: List[str]  # Recommendations
```

## Status

✅ **Production Ready**  
- 300 lines of code  
- Permanent knowledge storage in Reality Graph  
- Prediction accuracy tracking  
- Surprise detection (unexpected successes/failures)  
- Lesson extraction with type classification (observation/correction/insight/warning)  
- Statistics and metrics for monitoring improvement over time  
- Singleton pattern for global access  

---

*Generated for AXIMA v6.0 - July 17, 2026*
