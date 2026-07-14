# AXIMA MULTILINGUAL — Cosmic Level Plan (v3 FINAL)

## The Problem Nobody Has Solved

```
Real users DON'T type like textbooks.

They type:
  "gravity ante enti bro formula cheppu"     ← Telugu in English letters
  "force ka formula bata do"                  ← Hindi in English letters
  "gravity enna nu sollu"                     ← Tamil in English letters
  "ela work chestundi explain cheyyi"         ← "How does it work, explain"

This is:
  - NOT pure English (can't parse with English grammar)
  - NOT native script (can't detect by Unicode)
  - NOT transliterable (no 1:1 letter mapping)
  - MIXED English + Native grammar glue

Nobody handles this well. Not Google. Not Siri. Not any offline system.
```

## The AXIMA Approach: STRUCTURAL DETECTION (Not Word Lists)

```
SAME PHILOSOPHY AS ACES:
  "Detect by GRAMMAR STRUCTURE, not by vocabulary matching."

We DON'T store every Romanized word (impossible — infinite spellings).
We detect the SENTENCE STRUCTURE that reveals the language.

KEY INSIGHT:
  Content words (gravity, force, DNA, formula) → Stay English regardless
  Grammar glue (ante, enti, ki, lo, cheppu) → Reveals the language
  
  In ANY language, grammar glue is:
    • Postpositions (ki, lo, meedha, kosam)
    • Question markers (enti, emi, aa, na)
    • Verb endings (-tanu, -tundi, -taru, -andi)
    • Connectors (mariyu, kani, ante, kabatti)
  
  These form CLOSED CLASSES — only ~200 words per language.
  And they follow POSITION RULES in the sentence.
```

## The Architecture: 3-Layer Understanding

```
┌──────────────────────────────────────────────────────────────────────┐
│              AXIMA LANGUAGE INTELLIGENCE                               │
├──────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  INPUT: "gravity ante enti bro formula cheppu"                         │
│       ↓                                                                │
│  ┌─── LAYER 1: STRUCTURAL PATTERN DETECTION ─────────────────────┐    │
│  │                                                                 │    │
│  │  NOT word matching. GRAMMAR PATTERN matching.                   │    │
│  │                                                                 │    │
│  │  PATTERN: [noun] + [postposition/question] + [verb-ending]      │    │
│  │                                                                 │    │
│  │  Telugu patterns:                                               │    │
│  │    • [X] ante enti/emi → "what is [X]?"                        │    │
│  │    • [X] ela [verb] → "how does [X] [verb]?"                   │    │
│  │    • [X] enduku [verb] → "why does [X] [verb]?"                │    │
│  │    • [X] cheppu/cheppandi → "tell me [X]"                      │    │
│  │    • [X] ki [Y] → "[Y] to/for [X]"                            │    │
│  │    • [verb]-tundi/-taru/-tanu → present tense markers           │    │
│  │                                                                 │    │
│  │  Hindi patterns:                                                │    │
│  │    • [X] kya hai → "what is [X]?"                              │    │
│  │    • [X] kaise [verb] → "how does [X] [verb]?"                 │    │
│  │    • [X] kyun [verb] → "why does [X] [verb]?"                  │    │
│  │    • [X] bata/batao → "tell me [X]"                            │    │
│  │    • [X] ka/ki/ke [Y] → "[X]'s [Y]" (possessive)              │    │
│  │                                                                 │    │
│  │  Tamil patterns:                                                │    │
│  │    • [X] enna/enna-nu → "what is [X]?"                         │    │
│  │    • [X] eppadi [verb] → "how does [X] [verb]?"                │    │
│  │    • [X] sollu/sollunga → "tell me [X]"                        │    │
│  │    • [X] -la/-le → locative "in [X]"                           │    │
│  │                                                                 │    │
│  │  HOW: regex on SENTENCE ENDINGS and FUNCTION WORD POSITIONS     │    │
│  │  NOT: looking up every word in a dictionary                     │    │
│  │                                                                 │    │
│  │  Result: detected_language + sentence_type + content_words      │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│       ↓                                                                │
│  ┌─── LAYER 2: INTENT EXTRACTION (language-agnostic) ────────────┐    │
│  │                                                                 │    │
│  │  Once we know the PATTERN, we know the INTENT:                  │    │
│  │                                                                 │    │
│  │  "[X] ante enti" → intent=DEFINE, topic=X                      │    │
│  │  "[X] ela work chestundi" → intent=EXPLAIN_HOW, topic=X        │    │
│  │  "[X] formula cheppu" → intent=GIVE_FORMULA, topic=X           │    │
│  │  "[X] solve cheyyi" → intent=CALCULATE, topic=X                │    │
│  │  "[X] enduku [Y]" → intent=WHY, topic=X+Y                     │    │
│  │  "[X] [Y] compare cheyyi" → intent=COMPARE, topics=X,Y        │    │
│  │                                                                 │    │
│  │  The CONTENT WORDS (gravity, force, DNA) are already English!   │    │
│  │  We just need to understand the INTENT from the grammar glue.   │    │
│  │                                                                 │    │
│  │  Result: clean English query ready for AXIMA core               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│       ↓                                                                │
│  ┌─── AXIMA CORE (processes in English as always) ───────────────┐    │
│  │    Math → Physics → ACES → BRAIN → Voice                       │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│       ↓                                                                │
│  ┌─── LAYER 3: RESPONSE SHAPING (English → User's style) ───────┐    │
│  │                                                                 │    │
│  │  Takes English answer and SHAPES it back to user's style:       │    │
│  │                                                                 │    │
│  │  MODE A: User typed in Romanized Telugu                         │    │
│  │    → Keep technical terms in English                            │    │
│  │    → Add Telugu grammar glue in Roman script                    │    │
│  │    → "Gravity ante: objects ni earth vaipu pull chestundi"      │    │
│  │                                                                 │    │
│  │  MODE B: User typed in native Telugu script                     │    │
│  │    → Full Telugu output with formula in English                 │    │
│  │    → "గురుత్వాకర్షణ: objects ని earth వైపు pull చేస్తుంది. F=mg"  │    │
│  │                                                                 │    │
│  │  MODE C: User typed in pure English                             │    │
│  │    → Pure English response (normal ACES output)                 │    │
│  │                                                                 │    │
│  │  KEY RULE: Match the user's OWN style. If they mix, we mix.     │    │
│  │  If they're formal, we're formal. Mirror their register.        │    │
│  │                                                                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│       ↓                                                                │
│  OUTPUT (in user's OWN style — not forced formal/textbook)            │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
```

## Why This Is Cosmic (What Nobody Else Does)

```
GOOGLE TRANSLATE: Needs you to pick a language. Can't handle mixed input.
SIRI: Supports ONE language at a time. Fails on Romanized.
CHATGPT: Often responds in wrong language or forced formal.

AXIMA:
  1. Detects language from GRAMMAR PATTERNS (not script, not word lookup)
  2. Handles MIXED input naturally (English content + native grammar)
  3. Responds in the SAME STYLE user typed (mirror their register)
  4. Works for Romanized input (the way people ACTUALLY type)
  5. Only needs ~200 grammar patterns per language (not 50K words)
  6. ZERO ML model, ZERO internet, ZERO heavy data
```

## The Grammar Pattern Database (per language)

```
NOT a word list. A STRUCTURE list.

Each entry is: [pattern_regex, intent, extraction_rule]

Telugu (~200 patterns):
  ("[X] ante enti", WHAT_IS, extract X)
  ("[X] ante em", WHAT_IS, extract X)
  ("[X] gurinchi cheppu", EXPLAIN, extract X)
  ("[X] ela [V]", HOW, extract X + V)
  ("[X] enduku [V]", WHY, extract X + V)
  ("[X] formula enti", GIVE_FORMULA, extract X)
  ("[X] solve cheyyi", CALCULATE, extract X)
  ("[X] [Y] difference enti", COMPARE, extract X, Y)
  ("[X] valla [Y]", BECAUSE_OF, X causes Y)
  ("[X] ki [Y] kavali", X needs Y)
  ("[V]-tundi", PRESENT_TENSE, verb=V)
  ("[V]-taru", PLURAL_PRESENT, verb=V)
  ("[V]-andi", POLITE_REQUEST, verb=V)
  ...

Hindi (~200 patterns):
  ("[X] kya hai", WHAT_IS, extract X)
  ("[X] ke baare mein bata", EXPLAIN, extract X)
  ("[X] kaise [V]", HOW, extract X + V)
  ("[X] kyun [V]", WHY, extract X + V)
  ("[X] ka formula", GIVE_FORMULA, extract X)
  ("[X] solve karo", CALCULATE, extract X)
  ...

Tamil (~200 patterns):
  ("[X] enna", WHAT_IS, extract X)
  ("[X] pathi sollu", EXPLAIN, extract X)
  ("[X] eppadi [V]", HOW, extract X + V)
  ("[X] en [V]", WHY, extract X + V)
  ...

SIZE: ~200 patterns × ~50 bytes = ~10KB per language
TOTAL FOR 3 LANGUAGES: ~30KB

Compare: Google's language model = 50MB per language
We need: 30KB for 3 languages. That's 5000x smaller.
```

## Handling Spelling Variations (Smart, Not Exhaustive)

```
PROBLEM: Romanized Telugu has NO standard spelling.
  "enti" / "enti" / "emiti" / "enti" / "yenti" all mean "what"
  "cheppu" / "cheppu" / "cheppu" / "cheppandi" all mean "tell"

SOLUTION: Fuzzy pattern matching with PHONETIC NORMALIZATION

Step 1: Normalize double letters → single
  "cheppandi" → "chepandi"
  "antte" → "ante"

Step 2: Normalize vowel endings (they vary most)
  Strip trailing vowels for matching:
  "enti" / "enta" / "ento" → root "ent"
  
Step 3: Consonant skeleton matching
  Extract just consonants: "cheppu" → "CHPP"
  Match against known roots: "CHPP" → "tell/say" family

This handles ALL spelling variations with ~50 consonant skeletons per language.
Not 10,000 word variants. Just 50 patterns.
```

## BRAIN Multilingual (UPGRADED for Romanized)

```
INGESTION:
  • User uploads document — could be in ANY format:
    - Pure Telugu script ✓
    - Romanized Telugu ✓
    - English ✓
    - Mixed ✓
  • Detect language per PARAGRAPH using grammar patterns
  • Index in the language it was written in
  • ALSO create English equivalent index

SEARCH:
  • User types "gravity ante enti" (Romanized Telugu)
  • Layer 1 detects: Telugu, intent=WHAT_IS, topic=gravity
  • Searches: English index for "gravity"
  • Returns results shaped in user's Romanized style

QUIZ:
  • Generates in user's detected style
  • If user types Romanized → quiz in Romanized
  • "Gravity ante enti?" rather than "గురుత్వాకర్షణ అంటే ఏమిటి?"
  • MATCHES how the user actually communicates
```

## Build Phases (Final — 10 phases)

### Phase 1: Grammar Pattern Engine
- Regex-based pattern matching for Telugu/Hindi/Tamil
- ~200 patterns per language
- Handles: questions, commands, explanations, comparisons
- Size: ~10KB per language

### Phase 2: Phonetic Normalizer
- Handles spelling variations in Romanized text
- Double letter collapse + vowel normalization + consonant skeleton
- Size: ~2KB per language

### Phase 3: Intent Extractor
- Maps detected patterns → clean English intent
- "[X] ante enti" → "What is X?"
- Preserves English content words, translates only grammar glue
- Size: ~5KB per language

### Phase 4: Script Detector (for native script input)
- Unicode ranges for when users DO type in native script
- Per-character detection for mixed scripts
- Size: 0KB (pure code)

### Phase 5: Response Shaper
- Mirror user's input style in output
- If Romanized → respond Romanized with English terms
- If native script → respond in native script
- If pure English → respond in English

### Phase 6: Morphological Lite
- Handle verb endings (-tundi, -taru, -andi)
- Handle postpositions (ki, lo, meedha, valla)
- NOT full decomposition — just enough for pattern matching
- Size: ~3KB per language

### Phase 7: BRAIN Wiring
- Per-paragraph language detection
- Dual indexing (native + English)
- Quiz generation in user's style

### Phase 8: Voice Adaptation
- Phoneme mapping for Telugu/Hindi/Tamil sounds
- Same tube model, different area targets for native phonemes
- Prosody rules (Telugu has different intonation patterns)

### Phase 9: Learning Mode
- Track what language user prefers
- Adapt over time (if they switch styles, follow)
- Remember per-user language preference

### Phase 10: Benchmark
- 50 Romanized Telugu questions
- 50 Romanized Hindi questions
- Mixed input tests
- Spelling variation tests

---

## Size Budget (FINAL)

| Component | Per Language | 3 Languages |
|-----------|-------------|-------------|
| Grammar patterns | 10 KB | 30 KB |
| Phonetic normalizer | 2 KB | 6 KB |
| Intent mapper | 5 KB | 15 KB |
| Response templates | 5 KB | 15 KB |
| Morphological lite | 3 KB | 9 KB |
| **TOTAL** | **25 KB** | **75 KB** |

**75 KILOBYTES for 3 languages.**
Not megabytes. KILOBYTES.
Because we use STRUCTURE, not VOCABULARY.

---

## Success Criteria

### Romanized Input (THE REAL TEST)
- [ ] "gravity ante enti" → explains gravity
- [ ] "force formula cheppu" → gives F=ma
- [ ] "DNA ela work chestundi" → explains how DNA works
- [ ] "2+3 enti" → "5"
- [ ] "photosynthesis gurinchi cheppu" → full explanation
- [ ] "mass and weight difference enti" → comparison

### Spelling Variations (MUST handle all)
- [ ] "enti" = "emiti" = "yenti" = "enti" → all understood
- [ ] "cheppu" = "cheppandi" = "chepu" → all understood
- [ ] "ela" = "yela" = "elaa" → all understood

### Mixed (Code-switching)
- [ ] "gravity force enti and ela calculate chestaru" → understood
- [ ] "F=ma lo m ante mass andi" → "In F=ma, m means mass"

### Style Mirroring
- [ ] If user types casual Romanized → respond casual Romanized
- [ ] If user types formal Telugu script → respond formal Telugu
- [ ] If user types English → respond English

---

## The Philosophy (FINAL)

```
"Don't translate words. Understand INTENT from grammar patterns.
 
Real people don't type in textbook language.
They mix, they abbreviate, they misspell, they code-switch.

AXIMA doesn't fight this. AXIMA EMBRACES it.
Detect the pattern. Extract the intent. Respond in their style.

75 kilobytes. No internet. No model. Just grammar intelligence.

Same principle as everything in AXIMA:
  Structure over vocabulary.
  Patterns over memorization.
  Derive, don't store."
```

```
┌─────────────────────────────────────────────────────────────────────┐
