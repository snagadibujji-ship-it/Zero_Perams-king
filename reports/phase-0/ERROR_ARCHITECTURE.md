# AXIMA Error Architecture — Phase 0.3

**Date:** 2026-07-17  
**Status:** Critical path fixed (axima.py + inference_engine.py). Remaining 31 in non-critical engines.

---

## Design Principle

Every failure must explain:
1. **What** failed (engine name, operation)
2. **Why** (error type + message)
3. **Where** (query that triggered it)
4. **Recovery** (what to try next)

---

## Error Type Hierarchy

```
EngineError (base)
├── MathError        — math expression parsing/solving failures
├── PhysicsError     — physics identification/solving failures
├── InferenceError   — knowledge lookup/reasoning failures
├── RouteError       — could not determine target engine
├── ParseError       — input format issues
└── LoadError        — data file or engine initialization failures
```

---

## Implementation: src/python/errors.py

```python
@dataclass
class EngineError(Exception):
    engine: str        # "math", "physics", "inference", etc.
    error_type: str    # "parse_error", "no_result", "timeout", "internal", "load_error"
    message: str       # Human-readable description
    query: str = ""    # Input that caused failure
    recovery: str = "" # Suggested next action
```

---

## Fixed Locations (Phase 0.3)

| File | Line | Before | After | Risk Level |
|------|------|--------|-------|------------|
| axima.py | _try_math | `except: pass` | `except Exception as e: tracer.record_error(...)` | CRITICAL |
| axima.py | _try_physics | `except: pass` | `except Exception as e: tracer.record_error(...)` | CRITICAL |
| axima.py | _try_brain | `except: pass` | `except Exception as e: tracer.record_error(...)` | CRITICAL |
| axima.py | _try_inference | `except: pass` | `except Exception as e: tracer.record_error(...)` | CRITICAL |
| inference_engine.py | _load_cse | `except: pass` | `except (UnicodeDecodeError, IOError): pass` | HIGH |
| inference_engine.py | _load_causal_json | `except: pass` | `except (json.JSONDecodeError, IOError, KeyError): pass` | HIGH |

---

## Remaining Bare Excepts (31 — lower priority)

| File | Count | Recommended Fix |
|------|-------|-----------------|
| prometheus.py | 6 | Catch `(ValueError, ZeroDivisionError, TypeError)` |
| prometheus_advanced.py | 8 | Catch `(ValueError, ZeroDivisionError, OverflowError)` |
| prometheus_mind.py | 6 | Catch `(ValueError, KeyError, IndexError)` |
| prometheus_physics_solve.py | 2 | Catch `(ValueError, ZeroDivisionError)` |
| brain_compute.py | 2 | Catch `(ValueError, TypeError)` |
| brain_ingest.py | 1 | Catch `(IOError, UnicodeDecodeError)` |
| brain_tracker.py | 1 | Catch `(IOError, json.JSONDecodeError)` |
| aces_v2/bridges.py | 3 | Catch `(ImportError, AttributeError)` |
| aces_v2/memory.py | 2 | Catch `(IOError, json.JSONDecodeError)` |
| codegen_engine.py | 1 | Catch `(ValueError, KeyError)` |
| hybrid_ai.py | 1 | Likely dead code — skip |

**Strategy:** Fix remaining in future phases as engines are touched. The critical path (axima.py router) is now fully traced.

---

## Integration with Tracer

All errors in the critical path now feed into the tracer:

```json
{
  "query": "what is 15 * 7",
  "errors": [
    {
      "engine": "math",
      "type": "ValueError",
      "message": "Could not parse expression"
    }
  ]
}
```

---

## Recovery Strategy Per Engine

| Engine | On Failure | Recovery |
|--------|-----------|----------|
| Math | Falls through to inference | "Try rephrasing the expression" |
| Physics | Falls through to inference | "Specify the physics domain or formula" |
| Inference | Falls through to brain/ACES | "Topic may not be in knowledge base" |
| Brain | Falls through to ACES | "Document may not contain relevant info" |
| ACES | Returns template explanation | Always succeeds (last resort) |
