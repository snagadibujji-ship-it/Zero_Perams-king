#!/usr/bin/env python3
"""
AXIMA QueryBrain — Universal Question Understanding Engine

Understands ANY question format. No hardcoded patterns for specific questions.
Instead, uses STRUCTURE to understand what the user wants.

Capabilities:
1. INTENT DETECTION — What does the user want? (definition, inventor, location, cause, comparison...)
2. ENTITY EXTRACTION — What's the core topic? Works with any phrasing.
3. MULTI-QUESTION SPLIT — Handles "what is X and who invented it and where is it from"
4. SPELLING CORRECTION — Uses QIR for misspellings before searching
5. SEARCH QUERY CONSTRUCTION — Builds optimal search queries per intent

Design principles:
- ZERO hardcoded answers
- Works for questions that don't exist yet (new inventions, new topics)
- Handles slang, typos, minimal input ("hmm book?"), multi-questions
- Extracts STRUCTURE not content — so it works for ANY topic

Owner: Ghias / Gowtham Sangadi
"""

import re
from typing import List, Dict, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
# INTENT TYPES — What the user wants to know
# ═══════════════════════════════════════════════════════════════

INTENT_DEFINITION = 'definition'      # what is X
INTENT_INVENTOR = 'inventor'          # who invented/created X
INTENT_DISCOVERER = 'discoverer'      # who discovered X
INTENT_LOCATION = 'location'          # where is X
INTENT_TIME = 'time'                  # when did X happen
INTENT_CAUSE = 'cause'                # why does X happen / what causes X
INTENT_EFFECT = 'effect'              # what happens if X
INTENT_HOW = 'how'                    # how does X work
INTENT_QUANTITY = 'quantity'          # how many/much X
INTENT_COMPARISON = 'comparison'      # X vs Y / which is bigger
INTENT_SUPERLATIVE = 'superlative'    # biggest/fastest/tallest X
INTENT_PERSON = 'person'             # who is X
INTENT_AUTHOR = 'author'             # who wrote/painted X
INTENT_BOOLEAN = 'boolean'           # is X true? can X do Y?
INTENT_LIST = 'list'                 # what are types of X
INTENT_UNKNOWN = 'unknown'


# ═══════════════════════════════════════════════════════════════
# QUERY BRAIN
# ═══════════════════════════════════════════════════════════════

class QueryBrain:
    """Universal question understanding. No hardcoded question-answer pairs.
    Understands STRUCTURE to work with ANY topic — past, present, or future."""

    def __init__(self, qir=None, knowledge=None):
        """
        qir: QIR instance for spelling correction
        knowledge: CSEKnowledge for entity validation
        """
        self._qir = qir
        self._knowledge = knowledge

    # ─────────────────────────────────────────────────────────
    # MAIN API
    # ─────────────────────────────────────────────────────────

    def understand(self, raw_input: str) -> List[Dict]:
        """
        Understand ANY user input. Returns list of parsed queries.
        Each query has: {intent, entity, search_query, original}
        
        Handles:
        - Single question: "what is a book" → [{intent: definition, entity: book}]
        - Multi question: "what is a book and who invented it" → [{...}, {...}]
        - Minimal: "book?" → [{intent: definition, entity: book}]
        - Misspelled: "wat is a boook" → [{intent: definition, entity: book}]
        - Slang: "do u know about books" → [{intent: definition, entity: books}]
        """
        if not raw_input or not raw_input.strip():
            return []

        # Step 1: Clean input
        text = raw_input.strip()

        # Step 2: Spelling correction (via QIR if available)
        corrected = self._correct_spelling(text)

        # Step 3: Split multi-questions
        sub_questions = self._split_questions(corrected)

        # Step 4: For each sub-question, extract intent + entity
        results = []
        prev_entity = None
        for sq in sub_questions:
            parsed = self._parse_single(sq, prev_entity)
            if parsed:
                results.append(parsed)
                prev_entity = parsed.get('entity')  # for pronoun resolution

        return results

    # ─────────────────────────────────────────────────────────
    # STEP 2: SPELLING CORRECTION
    # ─────────────────────────────────────────────────────────

    def _correct_spelling(self, text: str) -> str:
        """Use QIR to fix misspellings. Non-destructive — only fixes obvious typos."""
        if not self._qir:
            return text

        try:
            interps = self._qir.resolve(text, 'general')
            if interps and interps[0].total_confidence > 0.85:
                best = interps[0].text
                # Only accept if it's a minor change (≤ 2 words different)
                orig_words = text.lower().split()
                best_words = best.split()
                if len(orig_words) == len(best_words):
                    changes = sum(1 for a, b in zip(orig_words, best_words) if a != b)
                    if changes <= 2:
                        return best
        except Exception:
            pass
        return text

    # ─────────────────────────────────────────────────────────
    # STEP 3: MULTI-QUESTION SPLITTING
    # ─────────────────────────────────────────────────────────

    def _split_questions(self, text: str) -> List[str]:
        """Split compound questions into individual ones.
        'what is a book and who invented it and where was it made'
        → ['what is a book', 'who invented it', 'where was it made']
        """
        # Split on conjunctions that start a new question
        # Pattern: "and/but/also" followed by a question word or new clause
        parts = re.split(
            r'\s+(?:and|but|also)\s+(?=who |what |where |when |why |how |is |can |does |do )',
            text, flags=re.IGNORECASE
        )

        # Also split on question marks (multiple questions in one line)
        expanded = []
        for part in parts:
            if '?' in part and part.count('?') > 1:
                sub = [s.strip() for s in part.split('?') if s.strip()]
                expanded.extend(sub)
            else:
                expanded.append(part.strip().rstrip('?').strip())

        # Also split on periods that separate questions
        final = []
        for part in expanded:
            if '. ' in part:
                subs = [s.strip() for s in part.split('. ') if s.strip() and len(s.strip()) > 3]
                if len(subs) > 1 and all(len(s) > 5 for s in subs):
                    final.extend(subs)
                else:
                    final.append(part)
            else:
                final.append(part)

        return [f for f in final if f and len(f) > 1]

    # ─────────────────────────────────────────────────────────
    # STEP 4: PARSE SINGLE QUESTION
    # ─────────────────────────────────────────────────────────

    def _parse_single(self, text: str, prev_entity: Optional[str] = None) -> Optional[Dict]:
        """Parse a single question into intent + entity."""
        if not text or len(text) < 2:
            return None

        low = text.lower().strip().rstrip('?.!').strip()

        # Resolve pronouns ("who invented it" → use prev_entity)
        if prev_entity:
            low = re.sub(r'\b(it|that|this|them|those)\b', prev_entity, low)
            text = re.sub(r'\b(it|that|this|them|those)\b', prev_entity, text, flags=re.IGNORECASE)

        # Detect intent and extract entity
        intent, entity = self._detect_intent_entity(low)

        # If no entity found, use the whole text as entity
        if not entity:
            entity = self._extract_fallback_entity(low)

        # Build optimal search query based on intent + entity
        search_query = self._build_search_query(intent, entity)

        return {
            'intent': intent,
            'entity': entity,
            'search_query': search_query,
            'original': text,
        }

    def _detect_intent_entity(self, q: str) -> Tuple[str, str]:
        """Detect intent and extract entity from question.
        Uses STRUCTURAL patterns, not content matching.
        Works for any topic — known or unknown."""

        # ── SUPERLATIVE: largest/smallest/fastest/tallest X ──
        m = re.search(r'(?:what|which|whats|what\'s)\s*(?:is\s+)?(?:the\s+)?(largest|biggest|smallest|tallest|highest|fastest|slowest|longest|shortest|deepest|heaviest|lightest|oldest|newest|hottest|coldest|richest|poorest|most \w+)\s+(.+)', q)
        if m:
            return INTENT_SUPERLATIVE, f"{m.group(1)} {m.group(2).strip()}"

        # ── INVENTOR: who invented/created/made/built X ──
        m = re.search(r'who\s+(?:invented|created|made|built|designed|developed|started|founded)\s+(?:the\s+|a\s+)?(.+)', q)
        if m:
            return INTENT_INVENTOR, m.group(1).strip()

        # ── DISCOVERER: who discovered/found X ──
        m = re.search(r'who\s+(?:discovered|found|identified|detected)\s+(?:the\s+|a\s+)?(.+)', q)
        if m:
            return INTENT_DISCOVERER, m.group(1).strip()

        # ── AUTHOR: who wrote/painted/composed/directed X ──
        m = re.search(r'who\s+(?:wrote|painted|composed|directed|sang|produced)\s+(?:the\s+|a\s+)?(.+)', q)
        if m:
            return INTENT_AUTHOR, m.group(1).strip()

        # ── PERSON: who is/was X ──
        m = re.search(r'who\s+(?:is|was|are|were)\s+(.+)', q)
        if m:
            return INTENT_PERSON, m.group(1).strip()

        # ── LOCATION: where is/was X ──
        m = re.search(r'where\s+(?:is|was|are|were|does|do|can)\s+(.+)', q)
        if m:
            return INTENT_LOCATION, m.group(1).strip()

        # ── TIME: when did/was/is X ──
        m = re.search(r'when\s+(?:did|was|is|were|does|do)\s+(.+)', q)
        if m:
            return INTENT_TIME, m.group(1).strip()

        # ── CAUSE: why does/is/do X ──
        m = re.search(r'why\s+(?:does|do|is|are|was|were|did|can|would)\s+(.+)', q)
        if m:
            return INTENT_CAUSE, m.group(1).strip()

        # ── EFFECT: what happens if/when X ──
        m = re.search(r'what\s+(?:happens|would happen|will happen)\s+(?:if|when)\s+(.+)', q)
        if m:
            return INTENT_EFFECT, m.group(1).strip()

        # ── HOW: how does/do/is/to X ──
        m = re.search(r'how\s+(?:does|do|is|are|was|were|can|to|would)\s+(.+)', q)
        if m:
            return INTENT_HOW, m.group(1).strip()

        # ── QUANTITY: how many/much X ──
        m = re.search(r'how\s+(?:many|much|long|far|big|tall|old|fast|heavy)\s+(.+)', q)
        if m:
            return INTENT_QUANTITY, m.group(1).strip()

        # ── BOOLEAN: is/can/does X Y ──
        # But first check it's not "do you know" (which is definition)
        if re.match(r'(?:do|does)\s+(?:you|u|ya)\s+know', q):
            m = re.search(r'(?:do|does)\s+(?:you|u|ya)\s+know\s+(?:about\s+)?(?:a\s+|an\s+|the\s+)?(.+)', q)
            if m:
                return INTENT_DEFINITION, m.group(1).strip()
        m = re.match(r'(?:is|can|does|do|was|were|has|have|will|would|should)\s+(.+)', q)
        if m:
            return INTENT_BOOLEAN, m.group(1).strip()

        # ── COMPARISON: X vs Y / X or Y / which is better ──
        if ' vs ' in q or ' versus ' in q or re.search(r'which\s+(?:is|are)\s+(?:better|bigger|faster)', q):
            return INTENT_COMPARISON, q

        # ── DEFINITION: what is/are X (most common, check last) ──
        m = re.search(r'(?:what|wat|wut|whats|what\'s)\s+(?:is|are|r)\s+(?:a\s+|an\s+|the\s+)?(.+)', q)
        if m:
            return INTENT_DEFINITION, m.group(1).strip()

        # ── DEFINITION (informal): "do you know X", "tell me about X", "X?" ──
        m = re.search(r'(?:do\s+(?:you|u|ya)\s+know|tell\s+me\s+about|explain|describe|define)\s+(?:about\s+|what\s+)?(?:a\s+|an\s+|the\s+)?(.+)', q)
        if m:
            return INTENT_DEFINITION, m.group(1).strip()

        # ── DEFINITION (minimal): just a word/phrase with ? or alone ──
        # "book?" or "hmm book" or just "quantum mechanics"
        clean = re.sub(r'^(?:hmm|hm|um|uh|ok|so|hey|well|like)\s+', '', q).strip()
        if clean and len(clean) < 50 and not any(w in clean for w in ['and', 'but', 'or', 'because']):
            return INTENT_DEFINITION, clean

        return INTENT_UNKNOWN, ''

    def _extract_fallback_entity(self, q: str) -> str:
        """Last resort entity extraction — get the meaningful words."""
        # Remove all question/stop words, keep content
        stops = {'what', 'is', 'are', 'the', 'a', 'an', 'who', 'where', 'when',
                 'why', 'how', 'does', 'do', 'did', 'can', 'could', 'would',
                 'should', 'will', 'was', 'were', 'been', 'be', 'have', 'has',
                 'had', 'it', 'its', 'this', 'that', 'these', 'those', 'i',
                 'you', 'u', 'we', 'they', 'me', 'my', 'your', 'tell', 'about',
                 'know', 'please', 'hmm', 'hm', 'um', 'ok', 'hey', 'well'}
        words = [w for w in q.split() if w.lower() not in stops and len(w) > 1]
        return ' '.join(words) if words else q

    # ─────────────────────────────────────────────────────────
    # STEP 5: BUILD SEARCH QUERY
    # ─────────────────────────────────────────────────────────

    def _build_search_query(self, intent: str, entity: str) -> str:
        """Build the optimal search query based on intent + entity.
        This is what gets sent to Wikipedia/DDG/Wikidata."""

        if not entity:
            return ''

        # Strategy per intent — construct the query that gets the RIGHT answer
        if intent == INTENT_DEFINITION:
            return entity  # Wikipedia handles "book", "quantum mechanics" etc.

        elif intent == INTENT_INVENTOR:
            # "radio" → search "radio" on Wikipedia, the article mentions inventor
            # But also try "invention of radio" as backup
            return entity

        elif intent == INTENT_DISCOVERER:
            return entity

        elif intent == INTENT_AUTHOR:
            return entity

        elif intent == INTENT_PERSON:
            return entity

        elif intent == INTENT_LOCATION:
            return entity

        elif intent == INTENT_TIME:
            return entity

        elif intent == INTENT_CAUSE:
            return entity

        elif intent == INTENT_EFFECT:
            return entity

        elif intent == INTENT_HOW:
            return entity

        elif intent == INTENT_SUPERLATIVE:
            # "largest desert" → search as-is, Wikipedia has "list of" articles
            return entity

        elif intent == INTENT_QUANTITY:
            return entity

        elif intent == INTENT_COMPARISON:
            return entity

        elif intent == INTENT_BOOLEAN:
            return entity

        return entity

    # ─────────────────────────────────────────────────────────
    # UTILITY: Get search variants for retry
    # ─────────────────────────────────────────────────────────

    def get_search_variants(self, parsed: Dict) -> List[str]:
        """Generate alternative search queries if first one fails.
        Based on intent, construct different angles to find the answer."""
        intent = parsed['intent']
        entity = parsed['entity']
        variants = []

        if intent == INTENT_INVENTOR:
            variants.append(f"invention of {entity}")
            variants.append(f"{entity} history")
            variants.append(f"{entity} inventor")

        elif intent == INTENT_DISCOVERER:
            variants.append(f"discovery of {entity}")
            variants.append(f"{entity} discovery history")

        elif intent == INTENT_AUTHOR:
            variants.append(f"{entity} author")
            variants.append(f"{entity} written by")

        elif intent == INTENT_SUPERLATIVE:
            variants.append(f"list of {entity}")
            variants.append(f"world {entity}")
            # Extract just the noun (e.g., "largest desert" → "desert")
            words = entity.split()
            noun = ' '.join(w for w in words if w not in ('largest', 'biggest', 'smallest', 'tallest', 'highest', 'fastest', 'longest', 'deepest', 'in', 'the', 'world', 'on', 'earth'))
            if noun:
                variants.append(f"{noun}")  # Search for just the category

        elif intent == INTENT_LOCATION:
            variants.append(f"{entity} location")
            variants.append(f"{entity} geography")

        elif intent == INTENT_TIME:
            variants.append(f"{entity} date")
            variants.append(f"{entity} timeline")

        elif intent == INTENT_CAUSE:
            variants.append(f"why {entity}")
            variants.append(f"{entity} cause explanation")

        elif intent == INTENT_HOW:
            variants.append(f"{entity} how it works")
            variants.append(f"{entity} mechanism")

        # Generic fallback
        if not variants:
            words = entity.split()
            if len(words) > 1:
                variants.append(words[-1])  # just the last word
                variants.append(' '.join(reversed(words)))

        return variants

    # ─────────────────────────────────────────────────────────
    # UTILITY: Check if answer matches intent
    # ─────────────────────────────────────────────────────────

    def answer_matches_intent(self, parsed: Dict, answer: str) -> bool:
        """Check if the answer actually answers the question.
        Used to decide if we need to search again with variants."""
        if not answer or len(answer) < 10:
            return False

        intent = parsed['intent']
        entity = parsed['entity']
        a_low = answer.lower()

        if intent == INTENT_INVENTOR:
            # Answer should mention a person name (capitalized words) or "invented"
            if re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+', answer):
                return True
            if any(w in a_low for w in ['invented', 'created', 'developed', 'designed', 'built']):
                return True
            return False

        elif intent == INTENT_DISCOVERER:
            if re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+', answer):
                return True
            if any(w in a_low for w in ['discovered', 'found', 'identified']):
                return True
            return False

        elif intent == INTENT_AUTHOR:
            if re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+', answer):
                return True
            if any(w in a_low for w in ['wrote', 'written', 'author', 'painted', 'composed']):
                return True
            return False

        elif intent == INTENT_SUPERLATIVE:
            # Answer should contain a proper noun AND relate to the entity type
            entity_words = [w for w in entity.split() if len(w) > 3 and w not in ('largest', 'biggest', 'smallest', 'tallest', 'highest', 'fastest', 'longest', 'deepest')]
            # Reject answers that are clearly wrong domain (album, song, book, film for geography)
            wrong_domain = ['album', 'song', 'film', 'movie', 'novel', 'book', 'band', 'game']
            if any(wd in a_low for wd in wrong_domain):
                return False
            # Must mention the category (desert, mountain, continent, etc.)
            if entity_words and any(ew in a_low for ew in entity_words):
                return True
            # Or contain clear superlative confirmation
            if any(w in a_low for w in ['largest', 'biggest', 'tallest', 'highest', 'fastest', 'longest', 'deepest', 'smallest']):
                return True
            return False

        elif intent == INTENT_DEFINITION:
            # Should have some substance (> 30 chars, not just "X is a concept")
            if len(answer) > 30 and 'is a concept' not in a_low:
                return True
            return False

        elif intent == INTENT_LOCATION:
            if any(w in a_low for w in ['located', 'found in', 'situated', 'in the']):
                return True
            return len(answer) > 20

        # Default: if answer is > 20 chars and mentions the entity, accept
        if entity and entity.split()[0].lower() in a_low and len(answer) > 20:
            return True

        return len(answer) > 30


# ═══════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════

_brain = None

def get_query_brain(qir=None, knowledge=None):
    global _brain
    if _brain is None:
        _brain = QueryBrain(qir=qir, knowledge=knowledge)
    return _brain


# ═══════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    brain = QueryBrain()

    print("═══ QUERY BRAIN TEST ═══\n")

    tests = [
        # Normal questions
        "what is a book",
        "who invented the radio",
        "what is the largest desert in the world",
        # Informal / slang
        "do u know about quantum physics",
        "hmm book?",
        "tell me about einstein",
        # Misspelled
        "wat is a commputer",
        "who invnted the telphone",
        # Multi-question
        "what is a book and who invented it and where was it first made",
        "what is gold? who discovered it? where is it found?",
        # Minimal
        "python",
        "mars",
        # Complex
        "what happens if you heat ice and what is the boiling point of water",
        "is the earth flat",
        "how does a computer work",
        "why is the sky blue",
        "how many planets are in the solar system",
    ]

    for t in tests:
        results = brain.understand(t)
        print(f"  Input: \"{t}\"")
        for r in results:
            print(f"    → intent={r['intent']:12s} entity=\"{r['entity']}\"  search=\"{r['search_query']}\"")
        print()
