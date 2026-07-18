# AXIMA — Problems & Issues (July 17, 2026)

## EVAL RESULTS: 38/45 (84%)

### Math: 13/20 (65%) — 7 FAILURES

| # | Input | Expected | Got | Root Cause |
|---|-------|----------|-----|-----------|
| 1 | what is 15 * 7 | 105 | 0 | Stale cache — prometheus returns 105 directly but axima returns 0 |
| 2 | what is sqrt(144) | 12 | 3.74166 | Same cache/flow issue |
| 3 | what is the derivative of x^3 | 3x^2 | knowledge fallback | Regex extracts "derivative of x^3" but _try_math doesn't return it |
| 4 | integrate 2x dx | x^2 | knowledge fallback | Falls through to knowledge base |
| 5 | what is the factorial of 5 | 120 | knowledge fallback | Same as #3 |
| 6 | what is pi to 2 decimal places | 3.14 | error msg | Prometheus can't parse "pi to decimal places" |
| 7 | what is e to 2 decimal places | 2.71 | knowledge fallback | Same — needs special handling |

**Root cause:** The `_try_math` function extracts the math expression correctly via regex, prometheus solves it correctly when called directly, but somewhere in the axima.process() pipeline flow the correct result isn't being returned. Likely a variable scope issue or the fallback path executing.

### Multilingual: 15/15 (100%) ✅ FIXED

### Codegen: 10/10 (100%) ✅

---

## ARCHITECTURE ISSUES (from friend's review)

### 1. Silent Failures (Phase 4 — NOT DONE)
- Multiple `bare except:` blocks in axima.py hide errors
- Engines return None silently instead of explaining what broke
- Need structured error returns

### 2. Plugin Architecture (Phase 5 — NOT DONE)
- All engines are in one flat `src/python/` folder
- Should be: core/ + plugins/ (math, physics, code, web, etc.)
- Would make it easier to grow without becoming a "giant script pile"

### 3. eval() in Math (Security)
- Calculator path in prometheus uses `eval()` — unsafe
- Should use restricted interpreter or parser

### 4. No Memory System
- No session state
- No learning from corrections
- No "I saw this before" capability

### 5. Shared Project Schema Missing
- web_generator.py and axima_coder.py do similar things differently
- Should share: name, stack, components, routes, files, dependencies

### 6. Regex Routing is Brittle
- Query classification is all regex-based
- Edge cases break easily
- Works 84% of the time, fails 16%

---

## KNOWN BUGS

1. Math router: results don't propagate correctly through axima.process() flow
2. Creator v3: some sentence repetition within beats
3. Creator v3: "the hands" should be "his hands" (possessive missing)
4. Web builder: edit system doesn't persist across sessions
5. Inference engine: returns random geographic facts for creative topics

---

## WHAT'S WORKING WELL

- Codegen: 100% — algorithms in 15 languages ✅
- Multilingual: 100% — 16 languages (added Turkish) ✅
- Web Builder: generates 34K chars with physics/shaders/3D ✅
- Creator v3: produces coherent narratives (not garbage anymore) ✅
- Truth labels: every response tagged with confidence source ✅
- Eval harness: reproducible benchmarks ✅
- Project structure: clean, modular, 38K lines ✅

---

## PRIORITY FIX ORDER

1. Fix math router flow issue (7 failures)
2. Replace bare except blocks with structured errors
3. Plugin architecture split
4. Safer math execution (no eval)
5. Memory system
6. Shared project schema

---

## FILES STATUS

| File | Lines | Status |
|------|-------|--------|
| axima.py | 281 | Router works, math has flow bug |
| truth.py | 142 | ✅ Working |
| coder.py | 240 | ✅ Working |
| web_generator.py | 1,028 | ✅ Working |
| web_beyond.py | 792 | ✅ Working |
| creator/engine_v3.py | 609 | Working, minor quality issues |
| inference_engine.py | 556 | ✅ Working |
| multilingual/__init__.py | ~880 | ✅ Fixed (16 langs) |
| codegen_engine.py | 2,008 | ✅ Working |
| axima_coder.py | 4,165 | ✅ Working |
| cosmic_coder.py | 2,830 | ✅ Working |
| prometheus*.py | 15,451 | Works directly, routing issue |
