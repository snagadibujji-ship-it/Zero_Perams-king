# AXIMA — Master Gap Analysis & Fixes (ALL Plans)

## 1. KNOWLEDGE INDEXER PLAN — Gaps Fixed

```
GAPS:
  ❌ Only indexes local 2.1MB files — misses the 4.8M sharded CSE facts
  ❌ BM25 alone is too simple — can't handle "what causes rain?" (needs relation-aware search)
  ❌ No INCREMENTAL indexing — rebuilds entire index on every new fact
  ❌ No SYNONYM handling — searching "car" won't find facts about "automobile"
  ❌ No RANKING by source quality — Wikipedia fact = same weight as generated fact

FIXES:
  ✅ Index ALL sources: local 2.1MB + sharded 42MB CSE
  ✅ Add RELATION-AWARE search: "what causes X" → search cause-edges, not just keywords
  ✅ Incremental: append new facts without rebuilding
  ✅ Synonym expansion from KNOWLEDGE itself (if "car is_a automobile" exists, link them)
  ✅ Source weighting: wiki > domain > generated (quality tiers)
  ✅ Add GRAPH traversal: "what does X cause?" → follow cause edges 2-3 hops
```

## 2. CREATOR V2 PLAN — Gaps Fixed

```
GAPS:
  ❌ Knowledge base might not have words for every topic
  ❌ "Write a story about quantum physics" — knowledge has facts, not STORY words
  ❌ No concept of NARRATIVE LOGIC (character must be consistent, plot must connect)
  ❌ No DIALOGUE generation (stories need characters talking)
  ❌ Phonetic expansion alone can't give enough word variety
  ❌ No awareness of CLICHE (might produce overused phrases)

FIXES:
  ✅ Word harvester ALSO extracts from: user's previous messages, ACES explanations
  ✅ For creative topics: derive METAPHOR WORDS (physics → "collide" "orbit" "attract" for love story about physics)
  ✅ Add NARRATIVE CONSISTENCY engine: track character state, prevent contradictions
  ✅ Dialogue patterns: "X said..." / response patterns / speech rhythm per character
  ✅ Multi-source harvesting: input + knowledge + phonetic + METAPHOR MAPPING
  ✅ Cliche detector: if a phrase appears in >3 knowledge entries, flag as overused
```

## 3. AXIMA CODER PLAN — Gaps Fixed

```
GAPS:
  ❌ "Code patterns" still sounds like templates — how exactly do they ADAPT?
  ❌ No DEPENDENCY RESOLUTION (if user adds React + Firebase, need specific versions)
  ❌ No ERROR PREDICTION (generated code might have bugs — how to prevent?)
  ❌ Can't READ user's existing code (only generates new)
  ❌ No TESTING generation (every app needs tests)
  ❌ No DATABASE SCHEMA generation (most apps need data models)
  ❌ No DEPLOYMENT knowledge (Docker, Vercel, AWS)
  ❌ How does it handle COMPLEX LOGIC? (auth flows, payment, real-time)
  ❌ No STATE MANAGEMENT patterns (Redux, Zustand, Context)
  ❌ Doesn't account for SECURITY (SQL injection, XSS, CSRF)

FIXES:
  ✅ Patterns adapt via PARAMETERS not code-switching:
      Pattern("ReactComponent", {
        has_state: true → add useState
        has_fetch: true → add useEffect
        has_form: true → add form handlers
        has_auth: true → wrap with AuthGuard
      })
      Each parameter adds/removes code SECTIONS. Not different templates.
  
  ✅ Dependency resolver: framework → known compatible versions
      React 18 + Firebase 10 + Tailwind 3 → exact package.json
  
  ✅ Static analysis: check generated code for common errors BEFORE output
      - Missing imports (referenced but not imported)
      - Undefined variables
      - Unclosed brackets
      - Type mismatches (for typed languages)
  
  ✅ Code READER: parse existing files → AST → understand structure
      - Know what functions exist
      - Know what's imported
      - Know the state shape
      → Then add new code that fits
  
  ✅ Auto-generate tests alongside code (pattern: for each handler → test case)
  
  ✅ Database schema from requirements:
      "todo app with users" → User(id, email, password), Todo(id, user_id, text, done)
  
  ✅ Deployment configs:
      Dockerfile, docker-compose, vercel.json, .github/actions
      (one pattern per deployment target)
  
  ✅ Complex flow patterns:
      AUTH: signup → verify → login → token → protected routes
      PAYMENT: cart → checkout → stripe → webhook → confirmation
      REALTIME: connect → subscribe → receive → update UI
  
  ✅ State management patterns:
      Small app → useState/useContext
      Medium → Zustand/Jotai
      Large → Redux Toolkit
      Decision based on: number of shared states + update frequency
  
  ✅ Security by default:
      - All inputs sanitized (pattern includes validation)
      - SQL always parameterized (never string concat)
      - Auth checks on every protected route
      - CORS configured
      - Environment variables for secrets (never hardcoded)
```

## 4. MULTILINGUAL PLAN — Gaps Fixed

```
GAPS:
  ❌ Can detect language but can't GENERATE long responses in non-English
  ❌ Response shaper is too basic (just adds prefixes)
  ❌ No handling of NUMBERS in non-English ("42" should be "నలభై రెండు" in Telugu)
  ❌ Code-switching OUTPUT not handled (user types mixed → we respond pure formal)
  ❌ No TRANSLITERATION of English technical terms to native script

FIXES:
  ✅ Response generation: grammar patterns for FULL sentences in each language
      Not just prefix — full SOV sentence construction for Indian languages
  ✅ Number words per language: 1-100 at minimum (40 numbers = 40 words stored, not a "list" — it's a closed set like function words)
  ✅ Mirror code-switching: if user mixes, we mix back naturally
  ✅ Transliteration engine: "gravity" → "గ్రావిటీ" (phonetic conversion, rule-based)
  ✅ Add SCRIPT OUTPUT option: respond in native script when detected
```

## 5. VOICE ENGINE PLAN — Gaps Fixed

```
GAPS:
  ❌ Beast mode produces audio but doesn't sound like speech (calibration issue)
  ❌ No clear path to get from "buzzy tone" to "recognizable words"
  ❌ Physics mode too slow in Python for real-time on phone
  ❌ No streaming (must generate entire utterance before playback)

FIXES:
  ✅ Calibration path CLEAR: Colab optimization → calibrated_areas.json → done
      (User already ran partial Colab, needs full optimization run)
  ✅ For USABLE voice NOW: use Piper CLI as subprocess (already proven working)
      Keep our engine for research/improvement, Piper for production output
  ✅ Speed: plan for Cython/Rust compilation of hot loop (voice_tract.process_sample)
      Pure Python = 0.3x RT. Cython = 30x RT. Rust = 100x RT.
  ✅ Streaming: generate in 50ms chunks, start playback after first chunk
```

## 6. ACES V2 — Gaps Fixed

```
GAPS:
  ❌ Explanations are thin because no KNOWLEDGE feeding in
  ❌ Parser only handles simple sentences (not complex nested clauses)
  ❌ No DEPTH CONTROL (can't make explanations progressively deeper on "go deeper")
  ❌ Memory doesn't LEARN from corrections

FIXES:
  ✅ Wire Knowledge Indexer output INTO ACES graph builder
      Question → search facts → build graph from REAL facts → explain
  ✅ Add complex sentence patterns: relative clauses, conditionals, nested causes
  ✅ "Go deeper" command: expand leaf nodes in graph by searching more facts
  ✅ Correction learning: "that's wrong because X" → store correction, update confidence
```

## MASTER DEPENDENCY ORDER

```
The correct BUILD ORDER (each depends on previous):

1. KNOWLEDGE INDEXER ← Everything needs this
   (fast lookup of 4.8M facts)

2. WIRE KNOWLEDGE → ACES/BRAIN/UNIFIED
   (so questions get real answers)

3. CREATOR V2 (needs knowledge for word harvesting)
   (stories/songs with context-derived words)

4. AXIMA CODER (needs patterns + knowledge of frameworks)
   (full app generation)

5. MULTILINGUAL RESPONSE IMPROVEMENT
   (better output generation in non-English)

6. VOICE CALIBRATION
   (Colab run for tube model, or Piper for production)

Each step BUILDS ON the previous. Knowledge Indexer is the foundation.
```

## SUCCESS = When This Works

```
USER: "gravity ante enti bro"
AXIMA:
  1. Detects Telugu casual
  2. Extracts "What is gravity?"
  3. Searches 4.8M facts → finds 15 gravity facts
  4. ACES builds graph → derives explanation
  5. Renders in user's style (casual Telugu + English terms)
  6. OUTPUT: "Gravity ante bro — earth objects ni attract chese force.
            Newton formula: F = Gm1m2/r^2. Basically mass unte attract avtundi."

USER: "build me a chat app with React and Socket.io"
AXIMA:
  1. Detects: project request, React + Socket.io
  2. Plans: file structure, deps, features
  3. Generates: 8 files (components, server, configs)
  4. Each file: full working code with security
  5. Explains each decision
  6. OUTPUT: complete project ready to npm install && npm start

USER: "write a song about my struggles"
AXIMA:
  1. Detects: song form, emotion=struggle
  2. Harvests words from: user context + knowledge("struggle" associations)
  3. Grows arc: verse→chorus→verse→chorus→bridge→chorus
  4. Generates lines from harvested words + grammar patterns
  5. Applies rhyme physics
  6. OUTPUT: actual song with rhyming, rhythm, emotional arc
```
