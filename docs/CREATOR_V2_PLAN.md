# AXIMA CREATOR v2 — The Real Plan (No Word Lists)

## The Problem With Current Creator

```
CURRENT: Store 100+ adjectives/verbs in pools → pick from them
RESULT:  Every story sounds the same. Generic. Doesn't match topic.
         "A story about cooking" uses same words as "a story about war"
         THIS IS WORD-LIST THINKING. Violates AXIMA philosophy.
```

## The Correct Approach

```
WORDS COME FROM:
  1. The USER'S OWN REQUEST (they give us the vocabulary)
  2. The KNOWLEDGE BASE (facts about the topic provide domain words)
  3. PHONETIC DERIVATION (transform existing words by sound rules)

AXIMA NEVER STORES content words.
AXIMA ONLY STORES grammar rules (sentence structures).

"Write a story about a chef who lost his restaurant"
  → Words available: chef, lost, restaurant, cook, food, fire, kitchen, taste
  → These come FROM the request + knowledge lookup
  → Grammar arranges them: "The chef {verb} the {noun}, {feeling-clause}"
  → Phonetics picks which verb SOUNDS right for the mood
```

## The Architecture

```
┌─────────────────────────────────────────────────────────────┐
│         CREATOR v2: CONTEXT-DRIVEN GENERATION                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  INPUT: "Write a story about a chef who lost his restaurant"  │
│       ↓                                                       │
│  ┌─── WORD HARVESTER ────────────────────────────────────┐   │
│  │                                                        │   │
│  │  SOURCE 1: User's request                             │   │
│  │    Extract ALL nouns, verbs, adjectives from input     │   │
│  │    "chef" "lost" "restaurant"                          │   │
│  │                                                        │   │
│  │  SOURCE 2: Knowledge base lookup                       │   │
│  │    Query: "chef" → "kitchen, cook, fire, taste, knife" │   │
│  │    Query: "restaurant" → "table, guest, menu, door"    │   │
│  │    Query: "lost" → "gone, empty, memory, before"       │   │
│  │    These are RETRIEVED not STORED in Creator            │   │
│  │                                                        │   │
│  │  SOURCE 3: Phonetic expansion                          │   │
│  │    "lost" → words with same dark vowel feel:           │   │
│  │    (compute from phonetics, not a list)                │   │
│  │    soft_o sound → "gone", "long", "song", "wrong"     │   │
│  │    These EMERGE from sound rules                       │   │
│  │                                                        │   │
│  │  RESULT: Word pool is BUILT PER REQUEST                │   │
│  │          Different topic = different words = unique     │   │
│  │                                                        │   │
│  └────────────────────────────────────────────────────────┘   │
│       ↓                                                       │
│  ┌─── GRAMMAR ENGINE (this is what we STORE) ────────────┐   │
│  │                                                        │   │
│  │  Grammar structures (sentence skeletons):              │   │
│  │    High energy: "{noun} {verb}. {fragment}."           │   │
│  │    Low energy: "In the {noun}, {subject} {verb}..."    │   │
│  │                                                        │   │
│  │  These are UNIVERSAL — work for any topic.             │   │
│  │  They're GRAMMAR not VOCABULARY.                       │   │
│  │  Same skeleton + cooking words = cooking story         │   │
│  │  Same skeleton + war words = war story                 │   │
│  │                                                        │   │
│  └────────────────────────────────────────────────────────┘   │
│       ↓                                                       │
│  ┌─── COMBINER ──────────────────────────────────────────┐   │
│  │                                                        │   │
│  │  Takes: harvested words + grammar skeleton + targets   │   │
│  │  Produces: sentences that match the TOPIC naturally    │   │
│  │                                                        │   │
│  │  "The chef stood in the empty kitchen,                 │   │
│  │   the taste of fire still on his tongue."              │   │
│  │                                                        │   │
│  │  ALL words came from topic context.                    │   │
│  │  Grammar provided the shape.                           │   │
│  │  Energy targets chose short vs long structure.         │   │
│  │                                                        │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Word Harvester — How It Works

### Source 1: Extract from user input
```
Input: "Write a story about a chef who lost his restaurant in a fire"

Extract by GRAMMAR ROLE (not word type):
  Nouns (things):      chef, restaurant, fire
  Verbs (actions):     lost, write
  Adjectives (traits): (none given)
  Relations:           chef→lost→restaurant, restaurant→in→fire
  
These become the PRIMARY word pool for this story.
```

### Source 2: Knowledge base association
```
For each extracted noun, query knowledge:
  "chef" → cooking, kitchen, knife, taste, recipe, heat, passion
  "restaurant" → table, door, guest, night, menu, candle, plate
  "fire" → flame, smoke, ash, red, burn, destroy, heat, light

For each verb, query knowledge:
  "lost" → gone, empty, before, memory, once, never again

These ASSOCIATED words become the SECONDARY pool.
No storage in Creator — pulled from knowledge at runtime.
```

### Source 3: Phonetic expansion (the AXIMA way)
```
For the CORE EMOTION WORD, expand by sound physics:

"lost" has: dark vowel (o), soft ending (st), one syllable
  → Same SOUND FEEL words (computed, not stored):
    Rule: words ending in -ost/-ost/-ong/-one have similar darkness
    "cost", "frost", "gone", "long", "song", "wrong", "stone", "alone"
    
These are DERIVED from phonetic rules — not a thesaurus.
The rules: match vowel darkness + consonant softness + syllable count.
```

## What We Store (ONLY grammar)

```
STORED (structure — universal):
  • 30 sentence grammar skeletons (varied by energy level)
  • 6 arc patterns (story/song/poem/essay/rap/script)
  • 8 style parameters (Style DNA)
  • Growth rules (tension must rise before falling)
  • Coherence rules (thread, callback, variation)
  • Rhyme computation rules (phonetic matching logic)
  
  SIZE: ~10KB of pure grammar/rules

NOT STORED:
  • No adjectives
  • No verbs
  • No nouns
  • No phrases
  • No feelings
  • No descriptions
  
  ALL content words come from: user input + knowledge lookup + phonetic derivation
```

## Why This Is Better

```
CURRENT CREATOR:
  "Write a story about cooking" → uses same "shattered/drifted/hollow"
  "Write a story about war" → uses same "shattered/drifted/hollow"
  EVERYTHING sounds the same.

NEW CREATOR:
  "Write a story about cooking" → harvests: kitchen, flame, taste, simmer, spice
    → "The kitchen simmered with memory, each spice a story untold"
  
  "Write a story about war" → harvests: soldier, march, blood, silence, ground
    → "The soldier marched into silence, blood soaking the ground"
  
  EACH topic produces UNIQUE vocabulary from its own context.
```

## Build Steps

1. **Word Harvester** — extract nouns/verbs/adj from user input via grammar parsing
2. **Knowledge Connector** — query knowledge base for associated words per noun
3. **Phonetic Expander** — derive similar-sounding words from core emotion word
4. **Remove all stored word pools** from current physics.py
5. **Combiner** — grammar skeletons + harvested words → sentences
6. **Test** — same grammar, different topics → different-sounding output

## Dependencies

- ACES v2 parser (for extracting grammar roles from input) ← already built!
- Knowledge Index (for associated word lookup) ← next to build
- Phonetic rules from Voice module (vowel/consonant classification) ← already built!

## Success Criteria

- [ ] "Story about cooking" sounds DIFFERENT from "story about war"
- [ ] ALL content words traceable to user input or knowledge base
- [ ] Zero stored adjectives/verbs/nouns in the Creator module
- [ ] Grammar structures are the ONLY stored data (~10KB)
- [ ] Works for ANY topic (even ones never seen before)
- [ ] Each generation is UNIQUE (time-seeded selection from harvested pool)
