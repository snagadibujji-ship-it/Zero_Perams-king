# AXIMA MULTILINGUAL — Cosmic Level Plan (v2 UPGRADED)

## Weak Points in v1 Plan (FIXED)

```
PROBLEM 1: "Extract vocabulary from Argos" — Argos word tables are contextless.
  A word-pair table gives "cat=పిల్లి" but doesn't know WHEN to use which meaning.
  "bank" = నది ఒడ్డు (river bank) OR బ్యాంకు (money bank)?
  FIX: Extract with CONTEXT TAGS. Each word pair gets a domain label.

PROBLEM 2: SOV→SVO reordering is too simplistic.
  Telugu: "నేను బడికి వెళ్తాను" = "I school-to go" → "I go to school"
  But complex sentences have nested clauses, relative clauses, etc.
  FIX: Use DEPENDENCY STRUCTURE, not just word order swap.

PROBLEM 3: Agglutinative languages (Telugu/Tamil) glue suffixes onto words.
  "పుస్తకాలలో" = పుస్తకం (book) + ల (plural) + లో (inside) = "in the books"
  A word-pair table won't find "పుస్తకాలలో" because it's not a single word.
  FIX: Add MORPHOLOGICAL DECOMPOSITION layer — split suffixes before lookup.

PROBLEM 4: Brain search with translated chunks loses nuance.
  Telugu medical term translated to English might lose the specific meaning.
  FIX: DUAL INDEXING — index BOTH original language AND English.
  Search in BOTH, merge results, rank by combined score.

PROBLEM 5: Formulas have LANGUAGE in them too.
  "వేగం = దూరం / సమయం" (velocity = distance / time)
  User might write formula with Telugu variable names.
  FIX: Variable name translation layer for formulas.

PROBLEM 6: No handling of CODE-SWITCHING.
  Real users mix languages: "gravity అంటే ఏమిటి?" (English word in Telugu sentence)
  FIX: Per-token language detection, not per-sentence.
```

---

## Architecture (UPGRADED)

```
┌─────────────────────────────────────────────────────────────────────┐
│                 AXIMA LANGUAGE LAYER (UPGRADED)                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  USER INPUT (any language, possibly mixed)                            │
│       ↓                                                               │
│  ┌─── TOKEN-LEVEL LANGUAGE DETECTOR ─────────────────────────────┐   │
│  │  • Per-CHARACTER script detection (not per-sentence)           │   │
│  │  • Handles code-switching: "gravity అంటే ఏమిటి?"              │   │
│  │  • Tags each token: [gravity:EN] [అంటే:TE] [ఏమిటి:TE]        │   │
│  │  • Returns: dominant language + per-token tags                 │   │
│  │  • Zero deps — pure Unicode range check                       │   │
│  └────────────────────────────────────────────────────────────────┘   │
│       ↓                                                               │
│  ┌─── MORPHOLOGICAL DECOMPOSER ──────────────────────────────────┐   │
│  │  • Splits agglutinated words into root + suffixes              │   │
│  │  • "పుస్తకాలలో" → ["పుస్తకం", "+plural", "+locative"]           │   │
│  │  • "படிக்கிறேன்" → ["படி", "+present", "+1st person"]           │   │
│  │  • Rule-based suffix stripping (not ML)                        │   │
│  │  • ~100 suffix rules per language (~2KB each)                  │   │
│  └────────────────────────────────────────────────────────────────┘   │
│       ↓                                                               │
│  ┌─── HYBRID TRANSLATOR (Input → English) ───────────────────────┐   │
│  │                                                                 │   │
│  │  LAYER 1: EXACT DOMAIN DICTIONARY (highest priority)            │   │
│  │    • Math: 500 terms with DOMAIN TAGS                          │   │
│  │    • Physics: 500 terms with domain tags                       │   │
│  │    • Biology/Chemistry/CS: 300 terms each                      │   │
│  │    • Common words: 2000 most frequent                          │   │
│  │    • Each entry: {word, english, domain, pos, example}         │   │
│  │                                                                 │   │
│  │  LAYER 2: MORPHEME-AWARE LOOKUP                                │   │
│  │    • After decomposition: look up ROOT word                    │   │
│  │    • Re-attach English equivalents of suffixes                 │   │
│  │    • "books" = lookup("పుస్తకం") + apply("+plural")             │   │
│  │                                                                 │   │
│  │  LAYER 3: DEPENDENCY-BASED REORDERING                          │   │
│  │    • NOT just SOV→SVO swap                                     │   │
│  │    • Parse: Subject / Object / Verb / Modifier / Postposition  │   │
│  │    • Reorder based on ROLE, not position                       │   │
│  │    • Handle: relative clauses, nested structures               │   │
│  │    • Rule-based dependency parser (~200 rules per language)    │   │
│  │                                                                 │   │
│  │  LAYER 4: CONTEXT-AWARE DISAMBIGUATION                         │   │
│  │    • "bank" → if domain=physics → "ఒడ్డు" (river bank)          │   │
│  │    •        → if domain=finance → "బ్యాంకు" (money bank)        │   │
│  │    • Uses: RouterDecision.domain from ACES shield              │   │
│  │    • Falls back to most common meaning if no domain detected   │   │
│  │                                                                 │   │
│  │  LAYER 5: EXTRACTED N-GRAM PATTERNS (from Argos, one-time)     │   │
│  │    • Common 2-3 word phrases with translations                 │   │
│  │    • Handles idioms and fixed expressions                      │   │
│  │    • ~10,000 n-gram pairs per language (~500KB)                │   │
│  │                                                                 │   │
│  │  LAYER 6: SUBWORD FALLBACK (for unknown words)                 │   │
│  │    • Transliteration: unknown Telugu → phonetic English        │   │
│  │    • "రామ్" → "Ram" (proper noun, just transliterate)          │   │
│  │    • Uses character mapping tables                             │   │
│  │                                                                 │   │
│  └────────────────────────────────────────────────────────────────┘   │
│       ↓                                                               │
│  ┌─── FORMULA TRANSLATOR ────────────────────────────────────────┐   │
│  │  • Detects formulas in any language                            │   │
│  │  • "వేగం = దూరం / సమయం" → "velocity = distance / time"         │   │
│  │  • Translates variable NAMES, keeps operators/numbers          │   │
│  │  • Bidirectional: en↔te, en↔hi, en↔ta                        │   │
│  └────────────────────────────────────────────────────────────────┘   │
│       ↓                                                               │
│  ┌─── AXIMA CORE (English internal) ────────────────────────────┐    │
│  │    Math → Physics → ACES → BRAIN → Voice                      │    │
│  └────────────────────────────────────────────────────────────────┘   │
│       ↓                                                               │
│  ┌─── OUTPUT TRANSLATOR (English → User Language) ───────────────┐   │
│  │    Same layers in reverse + NATURAL LANGUAGE POLISHER:          │   │
│  │    • Reorder SVO → SOV                                         │   │
│  │    • Re-attach suffixes (agglutination)                        │   │
│  │    • Apply honorifics/formality level                          │   │
│  │    • Preserve formulas in original + translated form           │   │
│  │    • Output: natural-sounding target language                  │   │
│  └────────────────────────────────────────────────────────────────┘   │
│       ↓                                                               │
│  OUTPUT (user's language, natural, with formulas preserved)           │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## What We Extract From Argos (One Time)

```
EXTRACTION PROCESS:
  1. pip install argostranslate (temporarily)
  2. Download language packs (te-en, hi-en, ta-en)
  3. Run extraction script:
     - Dump the vocabulary table (word→word mappings)
     - Dump the phrase alignment table
     - Dump the subword tokenizer vocabulary
     - Save as compressed JSON/binary files
  4. pip uninstall argostranslate
  5. Delete the model files

WHAT WE KEEP (per language):
  vocabulary.json    — ~50,000 word pairs (~1MB compressed)
  phrases.json       — ~5,000 common phrase templates (~200KB)
  subwords.json      — Subword units for unknown words (~500KB)
  grammar_rules.py   — SOV↔SVO conversion rules (~5KB)
  terms_dict.json    — Domain-specific exact translations (~20KB)

TOTAL PER LANGUAGE: ~2-3MB
TOTAL FOR 5 LANGUAGES (te/hi/ta/es/fr): ~12-15MB
```

---

## BRAIN Module — Multilingual Plan (UPGRADED)

### Problem
If user uploads a Telugu textbook, searching in English won't find anything.
v1 plan said "translate chunks to English for indexing" — but this LOSES nuance.

### Solution: DUAL-INDEX ARCHITECTURE

```
INGESTION (upgraded):
  1. User uploads document in ANY language
  2. DETECT language per paragraph (could be mixed!)
  3. MORPHOLOGICAL DECOMPOSITION of each chunk
     → Extract root words for indexing
  4. Store THREE versions per chunk:
     a) ORIGINAL text (for display)
     b) ROOT WORDS in original language (for same-language search)
     c) TRANSLATED ROOT WORDS in English (for cross-language search)
  5. Index ALL THREE in BM25

SEARCH (upgraded):
  1. User asks question in Telugu
  2. Decompose + extract roots from query
  3. Search SIMULTANEOUSLY:
     a) Telugu root index (exact language match — highest relevance)
     b) English index (cross-language — catches translated content)
  4. MERGE results by score (Telugu match scores 1.5x boost)
  5. Return ORIGINAL language chunks
  6. If explanation needed → pass through ACES → translate output

QUIZ GENERATION (upgraded):
  1. Generate quiz from meaning graph (ACES v2)
  2. Questions generated in English internally
  3. Translate questions to user's language
  4. But KEEP technical terms in both languages:
     "గురుత్వాకర్షణ (Gravity) అంటే ఏమిటి?"
     Shows both so student learns the English term too

FORMULA HANDLING:
  • Formulas stored as SYMBOLIC: F=m*a
  • Variable descriptions stored per language:
    {F: {en: "Force", te: "బలం"}, m: {en: "mass", te: "ద్రవ్యరాశి"}}
  • Computation always on symbolic form
  • Display in user's preferred language

STUDY TRACKER:
  • Tracks concepts in CANONICAL (English) form internally
  • Displays progress in user's language
  • "You're weak on గురుత్వాకర్షణ (gravity) — review suggested"

CROSS-BRAIN CONNECTIONS:
  • Find connections between docs in DIFFERENT languages!
  • Telugu physics textbook ↔ English chemistry textbook
  • Connected by shared concepts in English index
  • "ఈ Telugu physics concept relates to this English chemistry concept"
```

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    BRAIN MULTILINGUAL                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  INDEX LAYER (per chunk):                                     │
│  ┌─────────┐ ┌──────────────┐ ┌──────────────────┐          │
│  │ ORIGINAL │ │ NATIVE ROOTS │ │ ENGLISH ROOTS    │          │
│  │ (display)│ │ (same-lang)  │ │ (cross-lang)     │          │
│  └─────────┘ └──────────────┘ └──────────────────┘          │
│       ↑              ↑                  ↑                     │
│       │              │                  │                     │
│  ┌────┴──────────────┴──────────────────┴───────────┐        │
│  │         UNIFIED SEARCH (merge + rank)             │        │
│  └───────────────────────────────────────────────────┘        │
│       ↑                                                       │
│  User query (any language) → decompose → search both indexes │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Language Detection (Zero Dependencies)

```python
# Unicode script ranges — no model needed, instant detection
SCRIPTS = {
    'te': (0x0C00, 0x0C7F),   # Telugu
    'hi': (0x0900, 0x097F),   # Devanagari (Hindi)
    'ta': (0x0B80, 0x0BFF),   # Tamil
    'ar': (0x0600, 0x06FF),   # Arabic
    'zh': (0x4E00, 0x9FFF),   # Chinese
    'ja': (0x3040, 0x30FF),   # Japanese (Hiragana/Katakana)
    'ko': (0xAC00, 0xD7AF),   # Korean
    'th': (0x0E00, 0x0E7F),   # Thai
    'ru': (0x0400, 0x04FF),   # Cyrillic (Russian)
}

# If text has characters in a script range → that's the language
# If all ASCII → English
# Takes: 0.001ms, 0 dependencies
```

---

## Domain Term Dictionaries (What We Build)

### Telugu (తెలుగు) — Math Terms

| Telugu | English | Category |
|--------|---------|----------|
| సమీకరణం | equation | math |
| లెక్కించు | calculate | math |
| సమాధానం | answer/solution | math |
| సంఖ్య | number | math |
| భిన్నం | fraction | math |
| వర్గం | square | math |
| వర్గమూలం | square root | math |
| కూడిక | addition | math |
| తీసివేత | subtraction | math |
| గుణకారం | multiplication | math |
| భాగహారం | division | math |
| కోణం | angle | math |
| త్రిభుజం | triangle | math |
| వృత్తం | circle | math |
| సూత్రం | formula | math |

### Telugu — Physics Terms

| Telugu | English | Category |
|--------|---------|----------|
| గురుత్వాకర్షణ | gravity | physics |
| బలం | force | physics |
| ద్రవ్యరాశి | mass | physics |
| వేగం | velocity | physics |
| త్వరణం | acceleration | physics |
| శక్తి | energy | physics |
| పని | work | physics |
| తరంగం | wave | physics |
| కాంతి | light | physics |
| ధ్వని | sound | physics |
| ఉష్ణోగ్రత | temperature | physics |
| పీడనం | pressure | physics |
| విద్యుత్ | electricity | physics |

### Telugu — Common Verbs/Question Words

| Telugu | English |
|--------|---------|
| ఏమిటి | what |
| ఎందుకు | why |
| ఎలా | how |
| లెక్కించు | calculate |
| వివరించు | explain |
| పోల్చు | compare |
| నిరూపించు | prove |
| చూపించు | show |
| కనుగొను | find |

(Same tables would be built for Hindi and Tamil)

---

## Build Phases (UPGRADED — 12 phases)

### Phase 1: Token-Level Language Detector
- Per-character Unicode script detection
- Handle mixed-language input (code-switching)
- Return: dominant language + per-token language tags
- Size: 0 KB (pure code, no data)

### Phase 2: Morphological Decomposer
- Suffix stripping rules for Telugu, Hindi, Tamil
- Handles: plurals, case markers, tense markers, honorifics
- ~100 rules per language
- Output: root word + suffix list
- Size: ~2KB per language

### Phase 3: Domain Term Dictionaries (with context tags)
- 500+ terms per language per domain (math/physics/bio/chem/cs)
- Each entry: {native, english, domain, part_of_speech, example_sentence}
- Handles ambiguity: same word, different meaning per domain
- Size: ~30KB per language

### Phase 4: Dependency-Based Reordering
- NOT simple SOV→SVO swap
- Parse sentence into: Subject / Object / Verb / Modifier / Clause
- Reorder based on grammatical ROLE
- Handle: relative clauses ("which", "that"), nested structures
- ~200 grammar rules per language
- Size: ~10KB per language

### Phase 5: N-gram Pattern Extraction (from Argos)
- Install Argos temporarily
- Extract: phrase pairs, idiom translations, fixed expressions
- Extract: subword tokenizer vocabulary (for unknown words)
- Save as compressed lookup tables
- Uninstall Argos
- Size: ~2MB per language

### Phase 6: Transliteration Engine
- For proper nouns and unknown words
- Telugu→Latin: "రామ్" → "Ram"
- Latin→Telugu: "Newton" → "న్యూటన్"
- Character-by-character mapping tables
- Size: ~5KB per language

### Phase 7: Formula Translator
- Detect formulas in any language
- Translate variable NAMES, keep operators/numbers
- "వేగం = దూరం / సమయం" → "velocity = distance / time"
- Bidirectional (for output too)
- Preserve original + translated in output

### Phase 8: Output Language Polisher
- SVO → SOV reordering for output
- Re-agglutinate suffixes
- Apply honorifics (formal/informal based on context)
- Ensure grammatical correctness in target language
- Show bilingual terms: "గురుత్వాకర్షణ (Gravity)"

### Phase 9: BRAIN Multilingual Wiring
- Triple-index per chunk (original + native roots + English roots)
- Unified search across all indexes
- Cross-language document connections
- Quiz generation in user's language with bilingual terms

### Phase 10: Voice Multilingual
- Telugu/Hindi/Tamil G2P rules (phoneme sets)
- Map to area functions in the tube model
- Same physics engine, different phoneme→area mappings
- Emotional prosody rules per language (intonation patterns differ)

### Phase 11: Integration + Single Entry Point
- `axima.process(text)` auto-detects language, routes everything
- Works transparently — user never thinks about language
- Math in Telugu → answer in Telugu
- ACES explanation in Hindi → formatted in Hindi

### Phase 12: Test Suite (Multilingual Benchmark)
- 50 test questions per language (te/hi/ta)
- Mix of: math, physics, general knowledge, brain search
- Verify: correct translation + correct answer + natural output
- Score: translation accuracy + answer accuracy + naturalness

---

## NEW: Smart Features (Cosmic Level)

### Bilingual Learning Mode
```
When user is LEARNING English through their native language:
  • Show answer in BOTH languages side by side
  • Technical terms always shown as: "నేటివ్ (English)"
  • Build vocabulary: track which English terms user has learned
  • Gradually increase English content as user improves
```

### Context Memory Across Languages
```
If user asked about "gravity" in English yesterday,
and asks about "గురుత్వాకర్షణ" in Telugu today,
the system KNOWS it's the same topic and says:
"You asked about this before. Here's what's new..."
```

### Script Auto-Complete
```
If user types "grav" in Telugu input mode:
  → Suggest: "gravity" (EN) or "గురుత్వాకర్షణ" (TE)
User can type in ANY script and get suggestions in their preferred one.
```

### Language Confidence Score
```
Each translation gets a confidence:
  • Dictionary exact match: 0.95
  • N-gram pattern match: 0.80
  • Morpheme-based construction: 0.70
  • Transliteration fallback: 0.50

If confidence < 0.6:
  Show user: "I translated this as X — is that correct?"
  User corrects → system LEARNS (adds to dictionary)
```

---

## Size Budget (UPGRADED)

| Component | Per Language | 3 Languages |
|-----------|-------------|-------------|
| Language detector | 0 KB | 0 KB |
| Morphological rules | 2 KB | 6 KB |
| Domain term dictionaries | 30 KB | 90 KB |
| Grammar/reorder rules | 10 KB | 30 KB |
| N-gram patterns (from Argos) | 2 MB | 6 MB |
| Transliteration tables | 5 KB | 15 KB |
| Formula term mappings | 10 KB | 30 KB |
| **TOTAL** | **~2.1 MB** | **~6.2 MB** |

Compare:
- Google Translate offline: 50MB per language
- AXIMA: 2.1MB per language (24x smaller)

---

## Success Criteria (UPGRADED)

### Must Pass (Core)
- [ ] "2 + 3 ఎంత?" → "5"
- [ ] "గురుత్వాకర్షణ అంటే ఏమిటి?" → Correct explanation in Telugu
- [ ] "F=ma ను వివరించు" → Step-by-step in Telugu with formula
- [ ] Mixed: "gravity force ఎంత if mass=10?" → Handles code-switching
- [ ] Brain: Telugu textbook → search in Telugu → Telugu results
- [ ] Quiz: Telugu flashcards from Telugu source material

### Must Pass (Quality)
- [ ] Morphology: "పుస్తకాలలో" correctly decomposed and translated
- [ ] Ambiguity: "bank" resolves correctly per domain context
- [ ] Formulas: "వేగం = దూరం/సమయం" → correct symbolic computation
- [ ] Output: Natural Telugu (not word-by-word translation garbage)
- [ ] Bilingual: Technical terms shown in both languages

### Must Pass (System)
- [ ] ZERO internet required
- [ ] Under 2.5MB per language
- [ ] Translation < 50ms per sentence
- [ ] Works on phone CPU
- [ ] New language addable by community (just JSON files)

---

## The Philosophy

```
"Every other system translates the WORDS.
AXIMA translates the MEANING.

We decompose → understand structure → translate structure → reconstruct.
This is why our 2MB beats their 50MB.
They memorize phrases. We understand grammar.

Same philosophy as everything in AXIMA:
  DERIVE from principles. Never memorize."
```
