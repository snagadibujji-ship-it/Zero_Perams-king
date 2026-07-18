# AXIMA Observer — Cognitive Perception Layer

## Purpose

The Observer is the cognitive perception layer of AXIMA. It extracts structured understanding from unstructured input without attempting to answer questions or solve problems. Its sole responsibility is **perception** — identifying entities, goals, tasks, facts, concepts, and unknowns from any input text.

Key principles:
- **Never answers questions** — only perceives and understands
- Produces an `Observation` dataclass with extracted elements
- Estimates confidence for each extraction
- Detects intent, mood, topic, and complexity

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Observer                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │   Input: raw text                                     │  │
│  │   Output: Observation dataclass                       │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │  Intent  │ │  Entities│ │   Goals  │ │    Facts     │ │
│  │ Detection│ │ Extraction││ Detection│ │ Detection    │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │  Tasks   │ │ Concepts │ │ Unknowns │                    │
│  │ Detection│ │ Detection│ │ Detection│                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

### Data Structures

| Class | Purpose |
|-------|---------|
| `Entity` | A thing that exists (people, systems, concepts, places) |
| `DetectedGoal` | A desired outcome with urgency and target |
| `DetectedTask` | A specific actionable item |
| `DetectedFact` | An assertion about reality with subject/predicate/object |
| `DetectedConcept` | Abstract ideas being discussed |
| `DetectedUnknown` | Something unknown that needs resolution |
| `Observation` | Complete structured understanding from input |

## Key APIs

### Observer.observe(text: str) → Observation
Primary perception function. Extracts everything meaningful from input.

```python
observer = Observer()
obs = observer.observe("I need to fix the math router because it's dropping results")

obs.entities    # [Entity("math router")]
obs.goals       # [DetectedGoal("fix the math router")]
obs.facts       # [DetectedFact("math router is dropping results")]
obs.tasks       # []
obs.concepts    # []
obs.unknowns    # [DetectedUnknown("why results are dropped")]
```

### Observation.summary() → Dict
Quick overview of extraction results.

```python
{
    "intent": "command",
    "topic": "math router",
    "entities": 1,
    "goals": 1,
    "tasks": 0,
    "facts": 1,
    "concepts": 0,
    "unknowns": 1,
    "confidence": 0.73
}
```

## Integration Points

| Module | Integration |
|--------|-------------|
| `core/reality_sync.py` | Observer output feeds Reality Synchronizer to update the Reality Graph |
| `core/cognitive_runtime.py` | Observer is invoked on every user input as the first perception step |
| `core/attention.py` | Extracted goals/facts become candidates for attention scoring |
| `core/prediction.py` | Detected goals become targets for prediction |

## Implementation Reference

**File**: `core/observer.py`  
**Lines**: 477

### Intent Detection Patterns
- Commands: verbs like fix, build, create, deploy
- Questions: what, why, how, is/are, question mark
- Requests: please, can you, I need, help me
- Statements: normal declarative sentences

### Extraction heuristics
- **Entities**: Capitalized words, quoted strings, code paths (file extensions), technical compound terms
- **Goals**: Goal verbs (fix, build, implement, improve), "I need/want" patterns
- **Tasks**: Numbered/bulleted items, imperative sentences starting with action verbs
- **Facts**: X is Y, X has Y, X causes Y patterns with negation detection
- **Concepts**: Domain-specific keywords (math, physics, programming, architecture, language)
- **Unknowns**: Direct questions, "I don't know" patterns, unexplained problems

### Confidence Scoring
Each extraction has a confidence score (0.0-1.0) based on pattern match strength and contextual evidence.

## Status

✅ **Production Ready**  
- Fully implemented and tested
- Integrates with Reality Synchronizer
- Active use in cognitive runtime pipeline
