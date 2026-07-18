# AXIMA SYSTEM AUDIT — Phase 0.1

**Date:** 2026-07-17  
**Auditor:** Kiro (Lead Architect, COSMOS Phase 0)  
**Scope:** Complete architecture analysis of hybrid-ai/src/python/

---

## 1. Architecture Overview

```
                         ┌─────────────┐
                         │ axima_cli.py │  (entry point)
                         └──────┬──────┘
                                │
                         ┌──────▼──────┐
                         │   axima.py   │  (unified router, 281 lines)
                         │ get_axima()  │
                         └──────┬──────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                  │
     ┌────────▼────────┐  ┌────▼────┐    ┌───────▼───────┐
     │ MultilingualEngine│  │ truth.py│    │    ACES v2    │
     │ (lang detection) │  │ (labels)│    │  (fallback)   │
     └────────┬────────┘  └─────────┘    └───────────────┘
              │
    ┌─────────▼──────────┐
    │ _route_and_solve() │
    └─────────┬──────────┘
              │
    ┌─────────┼──────────┬──────────────┬───────────┐
    │         │          │              │           │
┌───▼───┐ ┌──▼──┐  ┌────▼────┐  ┌─────▼─────┐ ┌──▼──┐
│ Math  │ │Phys │  │Inference│  │   Brain   │ │ACES │
│Promet.│ │     │  │ Engine  │  │  (docs)   │ │(v2) │
└───────┘ └─────┘  └─────────┘  └───────────┘ └─────┘
```

### Request Flow (axima.process)

```
1. Input text
2. MultilingualEngine.process(text) → LangResult {language, intent, english_query}
3. IF language == 'en': use original text
   ELSE: use english_query (BUG: misclassification uses garbled text)
4. _route_and_solve(english_query, intent, mode)
   a. IF intent=='calculate' OR _looks_like_math(query): → _try_math()
   b. ELIF _looks_like_physics(query): → _try_physics()
   c. ELSE: → _try_inference() (knowledge base)
   d. ELIF brain loaded: → _try_brain()
   e. DEFAULT: → ACES v2 explanation
5. ResponseShaper (if non-English)
6. TruthLabel tagging
7. Return AximaResponse
```

---

## 2. Engine Inventory

| Engine | File(s) | Lines | Load Strategy | Memory |
|--------|---------|-------|---------------|--------|
| Router | axima.py | 281 | Eager | <1MB |
| Multilingual | multilingual/__init__.py, shaper.py | ~880 | Eager | <1MB |
| Truth | truth.py | 142 | Imported | <1MB |
| Math (Prometheus) | prometheus.py, prometheus_advanced.py, prometheus_mind.py | ~15,451 | Lazy | ~0.5MB |
| Physics | prometheus_physics.py, _math.py, _solve.py | ~9,400 | Lazy | ~0.5MB |
| Inference | inference_engine.py | 556 | Lazy | ~8MB (loads knowledge files) |
| Knowledge Index | knowledge_index.py | 1,405 | Not wired | N/A |
| ACES v2 | aces_v2/ (12 files) | 2,118 | Eager | <1MB |
| Coder | coder.py, codegen_engine.py, axima_coder.py, cosmic_coder.py | ~9,243 | Lazy | <2MB |
| Web Generator | web_generator.py, web_beyond.py | ~1,820 | Lazy | <1MB |
| Creator | creator/ (5 files) | ~2,100 | Lazy | <1MB |
| Brain | brain_*.py (5 files) | ~1,935 | Lazy | Depends on docs |
| hybrid_ai.py | hybrid_ai.py | ~2,500 | Unused legacy? | N/A |

**Total active memory (all engines loaded): ~11MB** ✅ Well under 50MB target.

---

## 3. Dependency Graph

```
axima.py
├── multilingual/ (eager)
│   ├── __init__.py (MultilingualEngine)
│   └── shaper.py (ResponseShaper)
├── aces_v2/ (eager)
│   ├── engine.py (ACESV2 — orchestrator)
│   ├── shield.py, router.py, parser.py
│   ├── graph_builder.py, reasoner.py, renderer.py
│   ├── auditor.py, memory.py, bridges.py
│   └── models.py
├── truth.py (imported on response)
├── prometheus.py (lazy: _try_math)
│   └── prometheus_advanced.py (imported by prometheus)
│   └── prometheus_mind.py (imported by prometheus)
├── prometheus_physics.py (lazy: _try_physics)
│   ├── prometheus_physics_math.py
│   └── prometheus_physics_solve.py
├── inference_engine.py (lazy: _try_inference)
│   └── Loads: src/data/*.triples, *.cse, *.txt, *.json
├── brain_*.py (lazy: load_brain)
│   ├── brain_ingest.py, brain_study.py
│   ├── brain_reason.py, brain_compute.py
│   ├── brain_cross.py, brain_tracker.py
├── coder.py (lazy: ax.code())
│   ├── codegen_engine.py (algorithms)
│   ├── axima_coder.py (projects)
│   ├── cosmic_coder.py (architectures)
│   └── web_generator.py / web_beyond.py (web)
└── creator/ (lazy: ax.create())
    ├── engine_v3.py (grammar physics)
    ├── engine.py, narrative_intelligence.py
    └── physics.py
```

**No circular dependencies detected.** ✅
**No external pip dependencies.** ✅ (Pure Python stdlib)

---

## 4. Critical Bugs Found

### Bug #1: Multilingual False Positives (ROOT CAUSE of 7 math failures)

The multilingual engine misclassifies English math queries as other languages:

| Query | Misdetected As | Why | Effect |
|-------|----------------|-----|--------|
| `what is 15 * 7` | Arabic | `'7'` is in ARABIC_MARKERS (Franco-Arabic digit) | Query truncated to `"what is 15 *"` |
| `what is the derivative of x^3` | Hindi | `'the'` matches Hindi marker; pattern `(.+?)\s+(?:the)\s*\??` fires | Topic becomes `"what is"` |
| `what is the factorial of 5` | Hindi | Same `'the'` match | Same garbling |
| `what is pi to 2 decimal places` | Arabic | `'2'` in ARABIC_MARKERS (counted twice: words + norm_words) | `'2'` stripped from query |
| `what is e to 2 decimal places` | Arabic | `'2'` in ARABIC_MARKERS | `'2'` stripped |
| `what is sqrt(144)` | English | But `english_query` becomes `"What is sqrt(14)?"` | Digits stripped |

**Root Cause:**
1. ARABIC_MARKERS contains `'2', '3', '5', '7'` (Franco-Arabic number-letter substitutes)
2. HINDI_MARKERS contains `'the'` (Hindi past tense verb form)
3. Score counting checks same word list TWICE (words + norm_words = identical for English)
4. Hindi pattern `(.+?)\s+(?:hai|hain|tha|the|hota|hoti)\s*\??` matches English `"the"`
5. The `_extract_topic_by_removal` function strips digits thinking they're Franco-Arabic

**Fix:** Add English detection priority. If text matches common English patterns (starts with "what is", "solve", "calculate"), bypass multilingual detection.

### Bug #2: _try_math regex extracts garbage for "pi/e to N decimal places"

Even when correctly routed, `_try_math` regex produces `"2decimal"` for `"pi to 2 decimal places"`.

### Bug #3: Validation in _try_math drops valid results

The validation `if first_line and first_line != expr.split()[0]:` may falsely reject some results.

---

## 5. Silent Failures (37 bare except blocks)

| File | Count | Risk |
|------|-------|------|
| prometheus.py | 6 | HIGH — hides math errors |
| prometheus_advanced.py | 8 | HIGH |
| prometheus_mind.py | 6 | MEDIUM |
| prometheus_physics_solve.py | 2 | MEDIUM |
| axima.py | 3 | CRITICAL — _try_math, _try_physics, _try_inference all swallow |
| inference_engine.py | 2 | HIGH — CSE load failures hidden |
| brain_*.py | 3 | LOW |
| aces_v2/ | 4 | LOW |
| codegen_engine.py | 1 | LOW |
| hybrid_ai.py | 1 | N/A (unused?) |
| **TOTAL** | **37** | |

The **3 in axima.py** are the most critical — they hide WHY math/physics/inference fail.

---

## 6. Duplicated Logic

| Duplication | Where | Impact |
|-------------|-------|--------|
| Web generation | web_generator.py + axima_coder.py (HTML path) | Divergent features |
| Knowledge loading | inference_engine.py + knowledge_index.py | Two indexers for same data |
| Math detection | axima.py `_looks_like_math` + multilingual patterns | Conflicting classification |
| Code detection | coder.py `_classify` + axima_cli.py routing | Minor |
| Physics solver | prometheus_physics.py + prometheus_physics_solve.py + prometheus_physics_math.py | Unclear boundaries |

---

## 7. Memory Usage Estimates

| State | Memory | Notes |
|-------|--------|-------|
| CLI startup (eager modules) | 2.5 MB | Multilingual + ACES |
| + Math engine loaded | 3.0 MB | Prometheus lazy init |
| + Inference engine loaded | 10.8 MB | src/data/ text files (~2MB on disk) |
| + All engines loaded | ~15 MB | Estimated |
| data/axima.cse (full KB) | ~70 MB | NOT loaded by default (knowledge_index.py) |
| data/axima_cold.cse.gz | ~23 MB compressed | NOT loaded |

**Current default: 10.8 MB** ✅ Under 50 MB target.
**Risk:** If knowledge_index.py (full 70MB CSE) is wired in, would exceed target.

---

## 8. Startup Sequence

```
1. axima_cli.py → sys.path.insert → import axima
2. get_axima() → Axima.__init__()
   a. MultilingualEngine() — grammar patterns compiled (eager)
   b. ResponseShaper() — templates loaded (eager)
   c. ACESV2() — full pipeline wired (eager, but lightweight)
   d. Math, Physics, Brain, Inference → set to None (lazy)
3. First math query → prometheus imported (one-time cost ~300ms)
4. First knowledge query → inference_engine loads src/data/ files (~500ms)
```

**Startup time: <500ms** for CLI ready. ✅

---

## 9. Routing Paths (Complete)

| Path | Trigger | Engine | Fallback |
|------|---------|--------|----------|
| Math | intent=='calculate' OR regex match | prometheus.py | Falls through to inference |
| Physics | regex match on physics keywords | prometheus_physics.py | Falls through to inference |
| Knowledge | Always tried (3rd priority) | inference_engine.py | Falls through to brain |
| Brain | Only if documents loaded | brain_*.py | Falls through to ACES |
| ACES | Default (always catches) | aces_v2/ | Never fails (template fallback) |
| Code | ax.code() direct call | coder.py → engines | Always produces something |
| Create | ax.create() direct call | creator/engine_v3.py | Always produces something |
| Web | Via coder.py classification | web_generator.py | Always produces HTML |

---

## 10. Bottlenecks

| Bottleneck | Severity | Impact |
|------------|----------|--------|
| Multilingual runs BEFORE math check | CRITICAL | Garbles math queries |
| Inference engine has no relevance threshold | MEDIUM | Returns random facts for any query |
| No caching between process() calls | LOW | Repeated singleton init checks |
| Regex-based routing | MEDIUM | Brittle, no confidence scoring |
| ACES always catches (hides routing failures) | HIGH | Masks problems with a plausible-looking answer |

---

## 11. Hidden Technical Debt

1. **hybrid_ai.py (96KB, 2500+ lines)** — Appears to be a legacy monolith. Not imported by axima.py. Possibly dead code.
2. **knowledge_index.py** — Full CSE indexer, not wired into axima.py. Inference engine has its own loader.
3. **Franco-Arabic digit markers** — The digits `'2','3','5','7'` in Arabic markers cause false positives on ANY text containing those digits.
4. **Hindi `'the'` marker** — Triggers on every English sentence containing "the".
5. **Double-counting in language detection** — `words` and `norm_words` are identical for English, doubling scores artificially.
6. **eval() in prometheus.py** — Calculator path uses `eval()` on user input. Security vulnerability.
7. **No structured error type** — All engines return Optional[str]. No way to distinguish "no answer" from "error".
8. **Singleton pattern without cleanup** — All `get_*()` functions use module-level globals with no reset mechanism.
9. **No logging anywhere** — Zero structured logging in 38K lines.
10. **IntentExtractor.to_english()** — Produces garbled English from extracted topics (e.g., `"What is what is?"`)

---

## 12. Recommendations (Priority Order)

1. **Fix multilingual false positives** — Add math/English priority bypass (fixes 5-7 of 7 math failures)
2. **Fix _try_math for pi/e decimal queries** — Special-case constant lookups
3. **Add tracing** — Every route decision logged as structured JSON
4. **Replace bare excepts** — At minimum in axima.py (3 locations)
5. **Define Result contract** — Replace Optional[str] returns with typed Result
6. **Wire reality graph** — Lightweight JSON persistence for goals/facts

---

## Conclusion

AXIMA is architecturally sound at the macro level: clean routing, lazy loading, modular engines, no circular deps, low memory. The critical failures are all in the **multilingual → router interface** — a 5-line fix would resolve 5 of 7 math failures. The remaining issues (bare excepts, no tracing, no contracts) are systematic hardening work.

The system is ready for Phase 0.2+.
