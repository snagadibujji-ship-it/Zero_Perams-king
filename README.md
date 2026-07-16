# AXIMA — Offline Symbolic Intelligence Engine

> A rule-based reasoning and generation system. No neural networks, no cloud, no API keys. Runs locally, explains what it knows and what it doesn't.

---

## What This Actually Is

AXIMA is a **symbolic AI stack** — it routes queries to specialized engines (math solver, physics solver, code generator, content generator, web builder) and composes answers from rules, facts, and structural patterns.

**What it is NOT:**
- Not a language model (no transformer, no training)
- Not "zero parameters" (it has rules, patterns, and a 4.8M fact knowledge base)
- Not comparable to GPT/Claude for open-ended conversation
- Not production-ready (prototype quality, needs hardening)

**What it actually does well:**
- Solves math symbolically (algebra, calculus, discrete math)
- Solves physics problems from equations
- Generates code (algorithms in 15 languages, full project scaffolds)
- Generates websites (vanilla/React/Three.js with advanced CSS/JS)
- Answers factual questions from its knowledge base
- Detects 15 languages from Romanized input
- Generates structured creative content (stories, songs, poems)

---

## Architecture

```
axima.py (router)
  ├── inference_engine.py   → factual answers from knowledge graph
  ├── prometheus*.py        → math solving (symbolic)
  ├── prometheus_physics.py → physics solving (equation-based)
  ├── aces_v2/              → multi-stage explanation pipeline
  ├── multilingual/         → language detection + routing
  ├── coder.py              → code generation router
  │   ├── codegen_engine.py → algorithms (pattern-based)
  │   ├── axima_coder.py    → full project generation
  │   └── web_generator.py  → website generation
  ├── creator/engine_v3.py  → content generation (grammar-based)
  └── brain_*.py            → personal document Q&A
```

---

## Honest Capabilities

| System | What It Does | How | Limitations |
|--------|-------------|-----|-------------|
| Math | Symbolic algebra, calculus | Pattern matching + CAS rules | Fails on novel notation |
| Physics | Equation solving | Formula lookup + substitution | Limited to known equations |
| Knowledge | Factual Q&A | 4.8M fact graph + inference rules | Only knows what's indexed |
| Multilingual | Language detection | Grammar pattern matching | Romanized input only, 15 langs |
| Coder | Algorithm generation | Pattern library (100+ algos) | Not context-aware like Copilot |
| Coder | Full projects | Template + pattern composition | Fixed architectural patterns |
| Web Builder | HTML/CSS/JS sites | Component composition + effects | Fixed component library |
| Creator | Stories/songs/poems | Grammar physics (structural) | Repetitive, limited vocabulary |
| ACES | Explanations | Multi-stage pipeline | Template-heavy fallbacks |

---

## Truth Labels

Every response from AXIMA is tagged with its confidence source:

| Label | Meaning |
|-------|---------|
| `direct_fact` | Found verbatim in knowledge base |
| `derived` | Inferred through reasoning rules (may be wrong) |
| `heuristic` | Best guess from pattern matching |
| `template` | Generated from structural patterns |
| `unsupported` | Could not find reliable answer |

---

## Running

```bash
cd hybrid-ai
python3 axima_cli.py
```

---

## Eval Results

See `evals/` folder for reproducible benchmarks with input/expected/actual/score.

---

## Line Counts (actual)

| Module | Lines | Purpose |
|--------|-------|---------|
| prometheus*.py | 15,451 | Math + Physics solvers |
| axima_coder.py | 4,165 | Project generation |
| cosmic_coder.py | 2,830 | Architecture patterns |
| aces_v2/ | 2,118 | Explanation pipeline |
| codegen_engine.py | 2,008 | Algorithm generation |
| brain_*.py | 1,935 | Document ingestion |
| web_generator.py | 1,028 | Website builder |
| knowledge_index.py | 1,405 | Fact indexer |
| multilingual/ | 844 | Language detection |
| web_beyond.py | 792 | Advanced web effects |
| creator/engine_v3.py | 609 | Content generation |
| inference_engine.py | 556 | Reasoning rules |
| axima.py | 281 | Main router |
| **Total** | **~38,000** | |

---

## Known Weaknesses

1. **Silent failures** — some engines return None quietly instead of explaining what broke
2. **Eval gaps** — claimed pass rates (400/400, etc.) not independently reproducible yet
3. **Template dependency** — code/web generation uses fixed patterns, not truly adaptive
4. **No memory** — no session state, no learning from corrections
5. **Regex routing** — query classification is regex-based, brittle on edge cases
6. **eval() in math** — calculator path uses eval (security concern)
7. **No tests** — no automated test suite, evals being built

---

## Roadmap

1. ~~Truth labels on every response~~ ✅
2. ~~Eval harness with reproducible benchmarks~~ ✅
3. Replace silent failures with structured errors
4. Plugin architecture (core + plugins)
5. Shared project schema for all generators
6. Memory system (session + long-term)
7. Safer math execution (no eval)
8. Public benchmark page

---

## Built By

**Gowtham Sangadi (Ghias)** — Architecture & Direction  
**Kiro** — Implementation

*Honest systems beat impressive demos.*
