# AXIMA MULTILINGUAL — Cosmic Level Plan

## The Approach: Hybrid Translation Layer

### One Sentence
"Detect language → translate to English → process → translate back. Extract what we need from models, keep nothing we don't."

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AXIMA LANGUAGE LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  USER INPUT (any language)                                        │
│       ↓                                                           │
│  ┌─── LANGUAGE DETECTOR ────────────────────────────────────┐    │
│  │  • Script detection (Telugu=తెలుగు, Hindi=हिंदी, Tamil=தமிழ்)│    │
│  │  • No model needed — just Unicode range check             │    │
│  │  • Returns: language code (te/hi/ta/en/es/fr/ar/etc)     │    │
│  └───────────────────────────────────────────────────────────┘    │
│       ↓                                                           │
│  ┌─── TRANSLATOR (input → English) ─────────────────────────┐    │
│  │                                                           │    │
│  │  LAYER 1: EXACT TERM DICTIONARY (rule-based, 0 deps)     │    │
│  │    • Math terms: "సమీకరణం" → "equation"                    │    │
│  │    • Physics terms: "గురుత్వాకర్షణ" → "gravity"              │    │
│  │    • Common verbs: "లెక్కించు" → "calculate"                 │    │
│  │    • Numbers: Same in all languages (1,2,3...)            │    │
│  │    • Size: ~500 terms per language (~5KB per language)     │    │
│  │                                                           │    │
│  │  LAYER 2: GRAMMAR TRANSFORMER (rule-based)                │    │
│  │    • Telugu/Hindi/Tamil are SOV (Subject-Object-Verb)     │    │
│  │    • English is SVO (Subject-Verb-Object)                 │    │
│  │    • Rule: detect SOV pattern → reorder to SVO            │    │
│  │    • Handle postpositions → prepositions                  │    │
│  │                                                           │    │
│  │  LAYER 3: EXTRACTED TRANSLATION GENES (from Argos model)  │    │
│  │    • Extract the VOCABULARY MAPPING (word→word table)      │    │
│  │    • Extract PHRASE TEMPLATES (common sentence patterns)   │    │
│  │    • Don't keep the neural model — just the lookup tables │    │
│  │    • Size: ~2-5MB per language (vs 50MB full model)        │    │
│  │                                                           │    │
│  └───────────────────────────────────────────────────────────┘    │
│       ↓                                                           │
│  ┌─── AXIMA CORE (all English) ──────────────────────────────┐    │
│  │    Math → Physics → ACES → BRAIN → Voice                  │    │
│  └───────────────────────────────────────────────────────────┘    │
│       ↓                                                           │
│  ┌─── TRANSLATOR (English → user language) ──────────────────┐    │
│  │    Same 3 layers in reverse:                               │    │
│  │    • Exact terms: "equation" → "సమీకరణం"                    │    │
│  │    • Grammar: SVO → SOV reorder                           │    │
│  │    • Phrase templates for natural output                   │    │
│  └───────────────────────────────────────────────────────────┘    │
│       ↓                                                           │
│  OUTPUT (in user's language)                                      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
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

## BRAIN Module — Multilingual Plan

### Problem
If user uploads a Telugu textbook, searching in English won't find anything.

### Solution

```
BRAIN MULTILINGUAL STRATEGY:

  INGESTION:
    1. User uploads document in ANY language
    2. DETECT language of document
    3. Store ORIGINAL text chunks (for display)
    4. ALSO translate chunks to English (for indexing/search)
    5. Store both: original + English version per chunk

  SEARCH:
    1. User asks question in Telugu
    2. Translate question to English
    3. Search the English index (BM25 works on English)
    4. Get matching chunks
    5. Return the ORIGINAL language chunks (not the English translations)

  QUIZ/FLASHCARD:
    1. Generate quiz from English version of chunks
    2. Translate questions + answers to user's language
    3. Present in user's language

  FORMULA COMPUTATION:
    • Formulas are UNIVERSAL (F=ma works in any language)
    • Just translate the variable descriptions
    • "ద్రవ్యరాశి" → mass, "త్వరణం" → acceleration

  CROSS-BRAIN:
    • Cross-subject connections work on English index
    • Results displayed in user's language

ARCHITECTURE:
  ┌─────────────────────────────────────────────┐
  │ Document (Telugu)                              │
  │    ↓                                          │
  │ Chunk in Telugu → store as original            │
  │    ↓                                          │
  │ Translate chunk → English → store as index     │
  │    ↓                                          │
  │ Index the English version (BM25)               │
  └─────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────┐
  │ User asks (Telugu)                             │
  │    ↓                                          │
  │ Translate question → English                   │
  │    ↓                                          │
  │ Search English index                           │
  │    ↓                                          │
  │ Get matching chunks                            │
  │    ↓                                          │
  │ Return ORIGINAL Telugu chunks to user           │
  └─────────────────────────────────────────────┘
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

## Build Phases

### Phase 1: Language Detector (Zero deps, instant)
- Unicode range detection
- Fallback: character frequency analysis
- Returns ISO language code

### Phase 2: Domain Term Dictionaries
- Build 500-term dictionaries for Telugu, Hindi, Tamil
- Math terms + Physics terms + Common verbs + Question words
- Pure JSON files, ~5KB each

### Phase 3: Grammar Transformer
- SOV → SVO reordering rules
- Postposition → preposition mapping
- Suffix/prefix handling (agglutinative languages)

### Phase 4: Extract Vocabulary from Argos
- Install Argos temporarily
- Dump word-pair tables for te↔en, hi↔en, ta↔en
- Save as compressed lookup files (~2MB each)
- Uninstall Argos

### Phase 5: Translation Engine
- Layer 1: Exact dictionary lookup
- Layer 2: Grammar reorder
- Layer 3: Vocabulary table fallback
- Bidirectional: input→English AND English→output

### Phase 6: Wire into AXIMA
- Wrap ALL existing modules with language layer
- Math/Physics/ACES/Brain all get multilingual input/output
- Single entry point: `axima.process(text)` auto-detects language

### Phase 7: BRAIN Multilingual
- Dual-store: original + English translation per chunk
- Search on English index, return originals
- Quiz/flashcard generation in user's language

### Phase 8: Test Suite
- Test with real Telugu/Hindi/Tamil math questions
- Verify: "2 + 3 ఎంత?" → processes correctly → returns "5" in Telugu
- Verify: BRAIN search works across languages

---

## Size Budget

| Component | Size |
|-----------|------|
| Language detector | 0 KB (built into code) |
| Term dictionaries (3 languages) | 15 KB |
| Grammar rules (3 languages) | 15 KB |
| Extracted vocabulary (3 languages) | 6-9 MB |
| **TOTAL** | **~10 MB for 3 languages** |

Compare: Google Translate app = 50MB per language. Ours = 3MB per language.

---

## What Makes This Cosmic

1. **Truly offline** — No internet for any language
2. **Extract & delete** — Take what we need from models, keep nothing heavy
3. **Universal** — Same approach for ANY new language (just add dictionary + vocabulary)
4. **Brain-aware** — Documents in any language searchable from any language
5. **Formula-universal** — Math works identically regardless of language
6. **Growable** — Community can add new language files (just JSON)
7. **Tiny** — 3MB per language vs 50MB+ for traditional approaches

---

## Success Criteria

- [ ] "2 + 3 ఎంత?" → "5" (Telugu math)
- [ ] "గురుత్వాకర్షణ అంటే ఏమిటి?" → Gravity explanation in Telugu
- [ ] "F=ma ను వివరించు" → Step-by-step in Telugu
- [ ] Brain: Upload Telugu textbook → search in Telugu → get Telugu results
- [ ] Quiz: Generate flashcards in Telugu from Telugu source
- [ ] Works with ZERO internet, ZERO cloud
- [ ] Under 10MB total for 3 languages
